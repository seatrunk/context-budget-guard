"""Source-checkout shim for the Spillway MCP stdio proxy.

The implementation lives in ``spillway.mcp_proxy`` (installed as ``spillway mcp``). This file keeps
``python3 adapters/mcp_proxy/proxy.py [options] -- CMD [ARGS...]`` working without installation.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from spillway.mcp_proxy import *  # noqa: E402,F401,F403
from spillway.mcp_proxy import Proxy, main  # noqa: E402,F401

if __name__ == "__main__":
    raise SystemExit(main())
