"""MCP stdio proxy that budgets tool results. Stdlib only.

    python3 adapters/mcp_proxy/proxy.py [--mode shadow|enforce|off] [--log-dir DIR] [--cap N] -- CMD [ARGS...]

Sits between the MCP client (this process's stdin/stdout) and the real server (CMD, a child).
Forwards every JSON-RPC message unchanged, except responses to ``tools/call``: ``result.content``
goes through the ``cbg`` core. Default ``shadow``: only writes receipts to DIR/receipts.jsonl (no
content). In ``enforce`` the original goes to DIR/artifacts/<sha256>.txt (0600).
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import cbg  # noqa: E402


class Proxy:
    def __init__(self, mode: str, log_dir: Path, cap: int):
        self.mode, self.log_dir, self.policy = mode, log_dir, cbg.Policy(result_cap=cap)
        self.pending = {}  # JSON-RPC id -> tool name
        self.lock = threading.Lock()

    def _write(self, rel: str, text: str) -> None:
        path = self.log_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as fh:
            fh.write(text)

    def from_client(self, line: str) -> str:
        try:
            msg = json.loads(line)
        except ValueError:
            return line
        if isinstance(msg, dict) and msg.get("method") == "tools/call" and "id" in msg:
            with self.lock:
                self.pending[json.dumps(msg["id"])] = (msg.get("params") or {}).get("name", "")
        return line

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
            tool = self.pending.pop(json.dumps(msg["id"]), None)
        result = msg.get("result")
        if tool is None or not isinstance(result, dict) or not isinstance(result.get("content"), list):
            return line
        content = result["content"]
        texts = [p for p in content if isinstance(p, dict) and p.get("type") == "text"]
        media = [p for p in content if not (isinstance(p, dict) and p.get("type") == "text")]
        body = {"_multimodal": True, "content": content} if media else "\n".join(str(p.get("text", "")) for p in texts)
        call_id = "mcp-" + json.dumps(msg["id"])
        out = cbg.apply_budget(call_id, body, policy=self.policy)
        changed = out.mode not in ("full", "control")
        rec = dict(out.receipt, ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"), tool=tool, adapter="mcp_proxy",
                   adapter_mode=self.mode, is_error=bool(result.get("isError")), would_change=changed)
        if self.mode == "enforce" and changed and out.artifact is not None:
            self._write("artifacts/" + out.receipt["artifact_sha256"] + ".txt", out.artifact)
        self._write("receipts.jsonl", json.dumps(rec, ensure_ascii=False) + "\n")
        if self.mode != "enforce" or not changed:
            return line
        r = out.rendered
        new_content = [{"type": "text", "text": r.payload}] if r.kind == "text" else r.payload
        new_result = dict(result, content=new_content)
        if "structuredContent" in new_result:  # would bypass the budget
            new_result.pop("structuredContent")
            rec_note = {"call_id": call_id, "structured_content_dropped": True}
            self._write("receipts.jsonl", json.dumps(rec_note) + "\n")
        return json.dumps(dict(msg, result=new_result), ensure_ascii=False) + "\n"


def _pump(src, dst, fn):
    for raw in iter(src.readline, b""):
        line = raw.decode("utf-8", errors="replace")
        try:
            line = fn(line)
        except Exception:  # fail-open to the original message
            pass
        dst.write(line.encode("utf-8") if line.endswith("\n") else (line + "\n").encode("utf-8"))
        dst.flush()


def _pump_and_close(src, dst, fn):
    try:
        _pump(src, dst, fn)
    finally:
        dst.close()  # client EOF becomes server EOF


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", default=os.environ.get("CBG_MODE", "shadow"), choices=["off", "shadow", "enforce"])
    ap.add_argument("--log-dir", default=os.environ.get("CBG_LOG_DIR", str(Path.home() / ".cache/context-budget-guard")))
    ap.add_argument("--cap", type=int, default=int(os.environ.get("CBG_RESULT_CAP", "16384")))
    ap.add_argument("command", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    cmd = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not cmd:
        ap.error("pass the real MCP server command after --")
    proxy = Proxy(args.mode, Path(args.log_dir).expanduser(), args.cap)
    child = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    up = threading.Thread(target=_pump_and_close, args=(sys.stdin.buffer, child.stdin, proxy.from_client), daemon=True)
    up.start()
    _pump(child.stdout, sys.stdout.buffer, proxy.from_server)
    return child.wait()


if __name__ == "__main__":
    raise SystemExit(main())
