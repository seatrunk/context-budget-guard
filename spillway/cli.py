"""Unified CLI for Spillway: MCP stdio proxy, receipt telemetry summary, and artifact pruning.

Examples:
    spillway mcp --mode shadow -- npx -y @modelcontextprotocol/server-filesystem .
    spillway --mode enforce --cap 16384 -- my-mcp-server
    spillway stats ~/.cache/spillway/receipts.jsonl
    spillway prune --log-dir ~/.cache/spillway --max-artifacts 100
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import statistics
import sys
from typing import List, Optional

from . import __version__
from .artifacts import ArtifactStore, DEFAULT_MAX_ARTIFACTS, DEFAULT_MAX_ARTIFACT_BYTES

# Top-level proxy flags accepted without the explicit ``mcp`` subcommand (``spillway --mode enforce -- CMD``).
_PROXY_FLAGS = {"--mode", "--cap", "--log-dir", "--wrap-untrusted", "--max-artifacts", "--max-artifact-bytes"}


def _default_log_dir() -> Path:
    for var in ("SPILLWAY_LOG_DIR", "CBG_LOG_DIR"):
        val = os.environ.get(var)
        if val:
            return Path(val).expanduser()
    return Path.home() / ".cache" / "spillway"


def _cmd_stats(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(prog="spillway stats", description="Summarize a receipts.jsonl file.")
    ap.add_argument("receipts", nargs="?", type=Path, default=_default_log_dir() / "receipts.jsonl")
    ap.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON summary")
    args = ap.parse_args(argv)
    path = args.receipts.expanduser()
    if not path.is_file():
        print(f"spillway stats: file not found: {path}", file=sys.stderr)
        return 2
    rows = []
    skipped = 0
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except ValueError:  # truncated/corrupt line (e.g. crash mid-write): count, do not abort
                skipped += 1
                continue
            if isinstance(obj, dict) and "mode" in obj and "original_bytes" in obj:
                rows.append(obj)
    by_mode = {}
    for r in rows:
        by_mode[r["mode"]] = by_mode.get(r["mode"], 0) + 1
    lat = sorted(r["elapsed_us"] for r in rows if isinstance(r.get("elapsed_us"), (int, float)))
    summary = {
        "total_results": len(rows),
        "would_change": sum(1 for r in rows if r.get("would_change")),
        "bytes_before": sum(r.get("original_bytes", 0) for r in rows),
        "bytes_after": sum(r.get("rendered_bytes", 0) for r in rows),
        "not_verified": sum(1 for r in rows if not r.get("verified", True) or r.get("mode") == "failclosed"),
        "by_mode": by_mode,
        "skipped_lines": skipped,
        "latency_us": (
            {
                "n": len(lat),
                "p50": statistics.median(lat),
                "p95": lat[min(len(lat) - 1, int(len(lat) * 0.95))],
                "max": lat[-1],
            }
            if lat
            else None
        ),
    }
    if args.as_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            f"results: {summary['total_results']}  would_change: {summary['would_change']}  "
            f"not_verified: {summary['not_verified']}"
        )
        print(f"bytes:   before={summary['bytes_before']}  after={summary['bytes_after']}  modes={summary['by_mode']}")
        if summary["latency_us"]:
            lu = summary["latency_us"]
            print(f"latency: n={lu['n']}  p50={lu['p50']}us  p95={lu['p95']}us  max={lu['max']}us")
    return 0


def _cmd_prune(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(prog="spillway prune", description="Prune stored artifacts to configured bounds.")
    ap.add_argument("--log-dir", type=Path, default=_default_log_dir())
    ap.add_argument("--max-artifacts", type=int, default=DEFAULT_MAX_ARTIFACTS)
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_ARTIFACT_BYTES)
    args = ap.parse_args(argv)
    store = ArtifactStore(args.log_dir, max_artifacts=args.max_artifacts, max_bytes=args.max_bytes)
    result = store.prune()
    print(json.dumps(result, sort_keys=True))
    return 0


def _cmd_replay(argv: List[str]) -> int:
    replay_path = Path(__file__).resolve().parents[1] / "benchmarks" / "replay" / "replay.py"
    if not replay_path.is_file():
        print("spillway replay: benchmark suite is only available in a source checkout", file=sys.stderr)
        return 2
    import importlib.util
    spec = importlib.util.spec_from_file_location("spillway_replay", replay_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.main(argv))


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(
            "usage: spillway <command> [options]\n\n"
            "commands:\n"
            "  mcp     Run MCP stdio proxy around a child server (or pass '-- <cmd>' directly)\n"
            "  stats   Summarize receipts.jsonl metrics\n"
            "  prune   Enforce retention limits on artifacts/\n"
            "  replay  Run deterministic offline benchmark replay (source checkout)\n"
            "  --version  Show Spillway version"
        )
        return 0
    if argv[0] in ("-V", "--version"):
        print(f"spillway {__version__}")
        return 0
    if argv[0] == "stats":
        return _cmd_stats(argv[1:])
    if argv[0] == "prune":
        return _cmd_prune(argv[1:])
    if argv[0] == "replay":
        return _cmd_replay(argv[1:])
    if argv[0] == "mcp":
        from .mcp_proxy import main as mcp_main
        return mcp_main(argv[1:])
    if argv[0] == "--" or argv[0].split("=", 1)[0] in _PROXY_FLAGS:
        from .mcp_proxy import main as mcp_main
        return mcp_main(argv)
    print(f"spillway: unknown command {argv[0]!r}; try 'spillway --help'", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
