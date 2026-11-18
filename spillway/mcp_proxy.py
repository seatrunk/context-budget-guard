"""MCP stdio proxy that budgets tool results and serves paginated artifact recovery. Stdlib only.

    spillway mcp [--mode shadow|enforce|off] [--log-dir DIR] [--cap N] [--wrap-untrusted] -- CMD [ARGS...]
    python3 adapters/mcp_proxy/proxy.py [same options] -- CMD [ARGS...]   # source-checkout shim

Sits between an MCP client (stdin/stdout) and a real MCP server (CMD child process).
- ``shadow`` (default): byte-for-byte identical passthrough; records receipts in ``DIR/receipts.jsonl``.
- ``enforce``: caps ``tools/call`` outputs, persists full originals in ``DIR/artifacts/<sha256>.txt`` (0600),
  strips ``structuredContent`` on cut responses, and exposes ``spillway_read_artifact`` so any MCP client
  can recover paginated slices by SHA-256 without host filesystem access.
- ``off``: passthrough with no receipts or artifacts.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from typing import Any, Dict, Optional, Tuple

from . import facts as _facts
from .artifacts import ArtifactStore, DEFAULT_MAX_ARTIFACTS, DEFAULT_MAX_ARTIFACT_BYTES
from .budget import MIN_RESULT_CAP, Policy, apply_budget
from .render import render
from .sanitize import neutralize_body

RECOVERY_TOOL_NAME = "spillway_read_artifact"
RECOVERY_TOOL_SPEC = {
    "name": RECOVERY_TOOL_NAME,
    "description": (
        "Read a UTF-8-safe paginated slice of a spilled tool output stored by Spillway. "
        "Pass the 64-character hex sha256 shown in the [spillway preview] header."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "sha256": {"type": "string", "description": "64-char lowercase hex artifact SHA-256"},
            "offset": {"type": "integer", "minimum": 0, "default": 0, "description": "Byte offset"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 65536, "default": 8192, "description": "Max bytes"},
        },
        "required": ["sha256"],
    },
}
MCP_ARTIFACT_HINT = (
    "artifact sha256={sha256} "
    "(recover via tool spillway_read_artifact with offset/limit)"
)


def _env(primary: str, legacy: str, default: str) -> str:
    """``primary`` if set and non-empty, else ``legacy`` if set and non-empty, else ``default``."""
    return os.environ.get(primary) or os.environ.get(legacy) or default


class Proxy:
    def __init__(
        self,
        mode: str,
        log_dir: Path,
        cap: int,
        *,
        wrap_untrusted: bool = False,
        max_artifacts: int = DEFAULT_MAX_ARTIFACTS,
        max_artifact_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
    ):
        self.mode = mode
        self.wrap_untrusted = wrap_untrusted
        effective_cap = max(MIN_RESULT_CAP, int(cap))
        self.policy = Policy(result_cap=effective_cap)
        self.store = ArtifactStore(
            log_dir,
            max_artifacts=max_artifacts,
            max_bytes=max_artifact_bytes,
        )
        self.pending: Dict[str, Tuple[str, str]] = {}  # JSON-RPC id -> (method, tool_name)
        self.lock = threading.Lock()
        self.out_lock = threading.Lock()

    def _handle_recovery_call(self, msg_id: Any, arguments: Any) -> str:
        args = arguments if isinstance(arguments, dict) else {}
        sha256 = str(args.get("sha256", "")).strip().lower()
        cap = self.policy.result_cap
        max_slice = max(128, cap // 2)
        try:
            offset = int(args.get("offset", 0))
            limit = max(1, min(int(args.get("limit", min(8192, max_slice))), max_slice))
            while True:
                slice_info = self.store.read_slice(sha256, offset=offset, limit=limit)
                meta = (
                    f"[spillway artifact {slice_info['sha256'][:16]}...] "
                    f"bytes {slice_info['offset']}..{slice_info['next_offset']} of {slice_info['total_bytes']} "
                    f"(eof={str(slice_info['eof']).lower()})\n"
                )
                # The artifact is the raw, untrusted tool output: neutralize wrapper delimiters and
                # reserved header tags so a stored payload cannot forge a [spillway ...] header or escape.
                text = meta + neutralize_body(slice_info["text"])
                if self.wrap_untrusted:
                    text = render(text, "text").model_text()
                # Neutralization can grow text (``[cbg`` -> ``[untrusted-cbg``): shrink until it fits.
                if len(text.encode("utf-8")) <= cap or limit <= 1:
                    break
                limit //= 2
        except (ValueError, TypeError, OverflowError, OSError) as exc:
            err_text = f"[spillway recovery error] cannot read artifact: {type(exc).__name__}"
            res = {"content": [{"type": "text", "text": err_text}], "isError": True}
            return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": res}, ensure_ascii=False) + "\n"
        res = {"content": [{"type": "text", "text": text}], "isError": False}
        return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": res}, ensure_ascii=False) + "\n"

    def from_client(self, line: str) -> Tuple[Optional[str], Optional[str]]:
        """Processes a client JSON-RPC line; returns ``(forward_to_server, immediate_reply_to_client)``."""
        try:
            msg = json.loads(line)
        except ValueError:
            return line, None
        if not isinstance(msg, dict) or "id" not in msg:
            return line, None
        method = msg.get("method")
        if method == "tools/call":
            params = msg.get("params") or {}
            tool_name = params.get("name", "") if isinstance(params, dict) else ""
            if self.mode == "enforce" and tool_name == RECOVERY_TOOL_NAME:
                reply = self._handle_recovery_call(msg["id"], params.get("arguments") if isinstance(params, dict) else {})
                return None, reply
            with self.lock:
                self.pending[json.dumps(msg["id"])] = ("tools/call", str(tool_name))
        elif method == "tools/list" and self.mode == "enforce":
            with self.lock:
                self.pending[json.dumps(msg["id"])] = ("tools/list", "")
        return line, None

    def from_server(self, line: str) -> str:
        if self.mode == "off":
            return line
        try:
            msg = json.loads(line)
        except ValueError:
            return line
        if not isinstance(msg, dict) or "id" not in msg or "method" in msg:
            return line
        with self.lock:
            entry = self.pending.pop(json.dumps(msg["id"]), None)
        if entry is None:
            return line
        req_method, tool = entry
        result = msg.get("result")
        if not isinstance(result, dict):
            return line

        if req_method == "tools/list":
            if self.mode == "enforce" and isinstance(result.get("tools"), list):
                existing = {t.get("name") for t in result["tools"] if isinstance(t, dict)}
                if RECOVERY_TOOL_NAME not in existing:
                    new_tools = list(result["tools"]) + [RECOVERY_TOOL_SPEC]
                    return json.dumps(dict(msg, result=dict(result, tools=new_tools)), ensure_ascii=False) + "\n"
            return line

        if not isinstance(result.get("content"), list):
            return line
        content = result["content"]
        texts = [p for p in content if isinstance(p, dict) and p.get("type") == "text"]
        media = [p for p in content if not (isinstance(p, dict) and p.get("type") == "text")]
        body: Any = (
            {"_multimodal": True, "content": content}
            if media
            else "\n".join(str(p.get("text", "")) for p in texts)
        )
        explicit_exit = _facts.exit_code_of(result.get("structuredContent"))
        call_id = "mcp-" + json.dumps(msg["id"])
        started = time.perf_counter()
        out = apply_budget(
            call_id,
            body,
            policy=self.policy,
            exit_code=explicit_exit,
            artifact_hint=MCP_ARTIFACT_HINT if self.mode == "enforce" else None,
        )
        changed = out.mode not in ("full", "control")
        rec = dict(
            out.receipt,
            ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            tool=tool,
            adapter="mcp_proxy",
            adapter_mode=self.mode,
            is_error=bool(result.get("isError")),
            elapsed_us=int((time.perf_counter() - started) * 1e6),
            would_change=changed,
        )
        if self.mode == "enforce" and changed and out.artifact is not None:
            self.store.write_artifact(out.receipt["artifact_sha256"], out.artifact)
        self.store.append_jsonl("receipts.jsonl", json.dumps(rec, ensure_ascii=False))
        if self.mode != "enforce" or not changed:
            return line
        r = out.rendered
        payload = r.payload if self.wrap_untrusted else r.unwrapped_payload()
        new_content = [{"type": "text", "text": payload}] if r.kind == "text" else payload
        new_result = dict(result, content=new_content)
        if "structuredContent" in new_result:  # would bypass the budget cap
            new_result.pop("structuredContent")
            rec_note = {"call_id": call_id, "structured_content_dropped": True}
            self.store.append_jsonl("receipts.jsonl", json.dumps(rec_note))
        return json.dumps(dict(msg, result=new_result), ensure_ascii=False) + "\n"


def _write_raw(dst, raw: bytes, lock: Optional[threading.Lock] = None) -> None:
    if lock is not None:
        with lock:
            dst.write(raw)
            dst.flush()
    else:
        dst.write(raw)
        dst.flush()


def _write_line(dst, text: str, lock: Optional[threading.Lock] = None) -> None:
    _write_raw(dst, text.encode("utf-8") if text.endswith("\n") else (text + "\n").encode("utf-8"), lock)


def _decode(raw: bytes) -> Optional[str]:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:  # not valid JSON-RPC text: forward the bytes untouched
        return None


def _pump_client(src, server_dst, client_dst, proxy: Proxy) -> None:
    try:
        for raw in iter(src.readline, b""):
            line = _decode(raw)
            forward, reply = line, None
            if line is not None:
                try:
                    forward, reply = proxy.from_client(line)
                except Exception:  # fail-open to original message
                    forward, reply = line, None
            if reply is not None:
                _write_line(client_dst, reply, proxy.out_lock)
            if forward is line:  # unchanged (or undecodable): original bytes, byte for byte
                _write_raw(server_dst, raw)
            elif forward is not None:
                _write_line(server_dst, forward)
    finally:
        server_dst.close()  # client EOF becomes server EOF


def _pump_server(src, client_dst, proxy: Proxy) -> None:
    for raw in iter(src.readline, b""):
        line = _decode(raw)
        out = line
        if line is not None:
            try:
                out = proxy.from_server(line)
            except Exception:  # fail-open to original message
                out = line
        if out is line:
            _write_raw(client_dst, raw, proxy.out_lock)
        else:
            _write_line(client_dst, out, proxy.out_lock)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="spillway mcp", description=__doc__.splitlines()[0])
    ap.add_argument(
        "--mode",
        default=_env("SPILLWAY_MODE", "CBG_MODE", "shadow"),
        choices=["off", "shadow", "enforce"],
    )
    ap.add_argument(
        "--log-dir",
        default=_env("SPILLWAY_LOG_DIR", "CBG_LOG_DIR", str(Path.home() / ".cache/spillway")),
    )
    ap.add_argument(
        "--cap",
        type=int,
        default=int(_env("SPILLWAY_RESULT_CAP", "CBG_RESULT_CAP", "16384")),
    )
    ap.add_argument(
        "--wrap-untrusted",
        action="store_true",
        default=os.environ.get("SPILLWAY_WRAP_UNTRUSTED", "").strip().lower() in ("1", "true", "yes"),
        help="Include <untrusted_tool_result> XML wrapper inside enforced MCP tool text",
    )
    ap.add_argument(
        "--max-artifacts",
        type=int,
        default=int(os.environ.get("SPILLWAY_MAX_ARTIFACTS") or DEFAULT_MAX_ARTIFACTS),
    )
    ap.add_argument(
        "--max-artifact-bytes",
        type=int,
        default=int(os.environ.get("SPILLWAY_MAX_ARTIFACT_BYTES") or DEFAULT_MAX_ARTIFACT_BYTES),
    )
    ap.add_argument("command", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    cmd = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not cmd:
        ap.error("pass the real MCP server command after --")
    proxy = Proxy(
        args.mode,
        Path(args.log_dir).expanduser(),
        args.cap,
        wrap_untrusted=args.wrap_untrusted,
        max_artifacts=args.max_artifacts,
        max_artifact_bytes=args.max_artifact_bytes,
    )
    child = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    up = threading.Thread(
        target=_pump_client,
        args=(sys.stdin.buffer, child.stdin, sys.stdout.buffer, proxy),
        daemon=True,
    )
    up.start()
    _pump_server(child.stdout, sys.stdout.buffer, proxy)
    return child.wait()


if __name__ == "__main__":
    raise SystemExit(main())
