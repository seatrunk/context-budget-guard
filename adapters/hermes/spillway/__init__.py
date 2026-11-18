"""Hermes Agent adapter for Spillway (``transform_tool_result`` hook).

Reads configuration from environment variables (with ``CBG_*`` legacy fallbacks), invokes the
pure ``spillway`` core, and persists receipts/artifacts through ``ArtifactStore``.

Environment variables:
  SPILLWAY_MODE             off | shadow (default) | enforce   (fallback: CBG_MODE)
  SPILLWAY_LOG_DIR          default: $HERMES_HOME/spillway     (fallback: CBG_LOG_DIR)
  SPILLWAY_RESULT_CAP       default 16384 UTF-8 bytes          (fallback: CBG_RESULT_CAP)
  SPILLWAY_FRAMING_RESERVE  default 512 bytes                  (fallback: CBG_FRAMING_RESERVE)
  SPILLWAY_MAX_ARTIFACTS    default 200                        (max retained files in artifacts/)
  SPILLWAY_MAX_ARTIFACT_BYTES default 104857600                (max retained bytes in artifacts/)

In ``shadow`` mode the hook returns ``None`` (Hermes keeps the original result) and logs a
content-free receipt. In ``enforce`` mode oversized results become bounded previews while the
complete original is saved to ``artifacts/<sha256>.txt`` (0600). Internal errors fail open.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Optional

_HERE = Path(__file__).resolve().parent
if str(_HERE / "vendor") not in sys.path:  # install.sh copies core to vendor/spillway
    sys.path.insert(0, str(_HERE / "vendor"))

import spillway  # noqa: E402
from spillway import facts as _facts  # noqa: E402
from spillway.artifacts import (  # noqa: E402
    ArtifactStore,
    DEFAULT_MAX_ARTIFACTS,
    DEFAULT_MAX_ARTIFACT_BYTES,
)

log = logging.getLogger("spillway")


def _env(primary: str, legacy: str, default: str) -> str:
    """``primary`` if set and non-empty, else ``legacy`` if set and non-empty, else ``default``."""
    return os.environ.get(primary) or os.environ.get(legacy) or default


def _mode() -> str:
    mode = _env("SPILLWAY_MODE", "CBG_MODE", "shadow").strip().lower()
    return mode if mode in ("off", "shadow", "enforce") else "shadow"


def _log_dir() -> Path:
    explicit = os.environ.get("SPILLWAY_LOG_DIR") or os.environ.get("CBG_LOG_DIR")
    if explicit:
        return Path(explicit).expanduser()
    home = os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes")
    return Path(home).expanduser() / "spillway"


def _store(logdir: Path) -> ArtifactStore:
    max_files = int(os.environ.get("SPILLWAY_MAX_ARTIFACTS") or DEFAULT_MAX_ARTIFACTS)
    max_bytes = int(os.environ.get("SPILLWAY_MAX_ARTIFACT_BYTES") or DEFAULT_MAX_ARTIFACT_BYTES)
    return ArtifactStore(logdir, max_artifacts=max_files, max_bytes=max_bytes)


def _policy() -> spillway.Policy:
    cap = int(_env("SPILLWAY_RESULT_CAP", "CBG_RESULT_CAP", "16384"))
    reserve = int(_env("SPILLWAY_FRAMING_RESERVE", "CBG_FRAMING_RESERVE", "512"))
    return spillway.Policy(result_cap=max(spillway.MIN_RESULT_CAP, cap - reserve))


def _exit_code(result: str) -> Optional[int]:
    try:
        parsed = json.loads(result)
    except (ValueError, TypeError, RecursionError):
        return None
    return _facts.exit_code_of(parsed) if isinstance(parsed, dict) else None


def process(
    tool_name: str,
    result: Any,
    tool_call_id: str = "",
    session_id: str = "",
    mode: Optional[str] = None,
) -> Optional[str]:
    mode = mode or _mode()
    if mode == "off" or not isinstance(result, str):
        return None
    logdir = _log_dir()
    store = _store(logdir)
    # Escape braces in the directory so str.format() in the core only substitutes {sha256}.
    safe_dir = str(store.artifacts_dir).replace("{", "{{").replace("}", "}}")
    hint = (
        "artifact path=" + safe_dir + "/{sha256}.txt (read with offset/limit)"
        if mode == "enforce"
        else None
    )
    started = time.perf_counter()
    out = spillway.apply_budget(
        tool_call_id or "unknown",
        result,
        policy=_policy(),
        exit_code=_exit_code(result),
        session_id=session_id,
        artifact_hint=hint,
    )
    record = dict(
        out.receipt,
        ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        tool=tool_name,
        session_id=session_id,
        adapter="hermes",
        adapter_mode=mode,
        elapsed_us=int((time.perf_counter() - started) * 1e6),
    )
    changed = out.mode not in ("full", "control")
    record["would_change"] = changed
    if mode == "enforce" and changed and out.artifact is not None:
        store.write_artifact(out.receipt["artifact_sha256"], out.artifact)
    store.append_jsonl("receipts.jsonl", json.dumps(record, ensure_ascii=False))
    if mode != "enforce" or not changed:
        return None
    return out.rendered.unwrapped_payload()


def _on_transform_tool_result(
    tool_name: str = "",
    args: Any = None,
    result: Any = None,
    tool_call_id: str = "",
    session_id: str = "",
    **_: Any,
) -> Optional[str]:
    try:
        return process(tool_name, result, tool_call_id, session_id)
    except Exception as exc:  # fail-open: never break host tool execution
        log.warning("spillway: internal error (%s); original result kept", type(exc).__name__)
        try:
            # Plain ArtifactStore: a bad retention env var must not break error logging either.
            ArtifactStore(_log_dir()).append_jsonl(
                "errors.jsonl",
                json.dumps({"tool": tool_name, "error": type(exc).__name__}),
            )
        except Exception:  # never let the fail-open path itself raise into the host
            pass
        return None


def register(ctx) -> None:
    ctx.register_hook("transform_tool_result", _on_transform_tool_result)
