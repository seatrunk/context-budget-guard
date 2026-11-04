"""Hermes Agent adapter for context-budget-guard (``transform_tool_result`` hook).

Thin on purpose: reads config from the environment, calls the ``cbg`` core and writes JSONL receipts.

Variables:
  CBG_MODE           off | shadow (default) | enforce
  CBG_LOG_DIR        default: $HERMES_HOME/context-budget-guard  (receipts in receipts.jsonl)
  CBG_RESULT_CAP     default 16384 (UTF-8 bytes of the final text)
  CBG_FRAMING_RESERVE default 512 (bytes reserved for the wrapper Hermes applies itself)

In shadow the hook returns None (Hermes keeps the original result) and only records what it would do.
Receipts hold no tool-result content: only sizes, hashes, mode and facts (exit code, locations).
In enforce the original goes to artifacts/<sha256>.txt (0600) and the model receives the preview.
Any internal exception is fail-open to the original result and is recorded as an error.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve().parent
if str(_HERE / "vendor") not in sys.path:  # install.sh copies the core to vendor/cbg
    sys.path.insert(0, str(_HERE / "vendor"))

import cbg  # noqa: E402
from cbg.sanitize import CLOSE, OPEN  # noqa: E402

log = logging.getLogger("context_budget_guard")


def _mode() -> str:
    mode = os.environ.get("CBG_MODE", "shadow").strip().lower()
    return mode if mode in ("off", "shadow", "enforce") else "shadow"


def _log_dir() -> Path:
    explicit = os.environ.get("CBG_LOG_DIR")
    if explicit:
        return Path(explicit).expanduser()
    home = os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes")
    return Path(home).expanduser() / "context-budget-guard"


def _policy() -> cbg.Policy:
    cap = int(os.environ.get("CBG_RESULT_CAP", "16384"))
    reserve = int(os.environ.get("CBG_FRAMING_RESERVE", "512"))
    return cbg.Policy(result_cap=max(256, cap - reserve))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as fh:
        fh.write(text)


def _exit_code(result: str) -> Optional[int]:
    try:
        parsed = json.loads(result)
    except (ValueError, TypeError):
        return None
    return cbg.facts.exit_code_of(parsed) if isinstance(parsed, dict) else None


def _inner(rendered_text: str) -> str:
    """Hermes applies its own wrapper; we return only the body (without our framing)."""
    body = rendered_text
    if body.startswith(OPEN + "\n"):
        body = body[len(OPEN) + 1:]
        end = body.rfind("\n" + CLOSE)
        body = body[:end] + body[end + len(CLOSE) + 1:]
    return body


def process(tool_name: str, result: Any, tool_call_id: str = "", session_id: str = "",
            mode: Optional[str] = None) -> Optional[str]:
    mode = mode or _mode()
    if mode == "off" or not isinstance(result, str):
        return None
    started = time.perf_counter()
    out = cbg.apply_budget(tool_call_id or "unknown", result, policy=_policy(), exit_code=_exit_code(result),
                           session_id=session_id)
    record = dict(out.receipt, ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"), tool=tool_name, session_id=session_id,
                  adapter="hermes", adapter_mode=mode, elapsed_us=int((time.perf_counter() - started) * 1e6))
    changed = out.mode not in ("full", "control")
    record["would_change"] = changed
    logdir = _log_dir()
    if mode == "enforce" and changed and out.artifact is not None:
        _write(logdir / "artifacts" / (out.receipt["artifact_sha256"] + ".txt"), out.artifact)
    _write(logdir / "receipts.jsonl", json.dumps(record, ensure_ascii=False) + "\n")
    if mode != "enforce" or not changed:
        return None
    return _inner(out.rendered.model_text())


def _on_transform_tool_result(tool_name: str = "", args: Any = None, result: Any = None,
                              tool_call_id: str = "", session_id: str = "", **_: Any) -> Optional[str]:
    try:
        return process(tool_name, result, tool_call_id, session_id)
    except Exception as exc:  # fail-open: never breaks the call
        log.warning("context-budget-guard: internal error (%s); original result kept", type(exc).__name__)
        try:
            _write(_log_dir() / "errors.jsonl", json.dumps({"tool": tool_name, "error": type(exc).__name__}) + "\n")
        except OSError:
            pass
        return None


def register(ctx) -> None:
    ctx.register_hook("transform_tool_result", _on_transform_tool_result)
