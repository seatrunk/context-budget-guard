# MCP stdio proxy

Sits between the MCP client and a real MCP server and applies the budget to `tools/call` responses. Stdlib only.

```sh
python3 adapters/mcp_proxy/proxy.py --mode shadow --log-dir ~/.cache/context-budget-guard -- <MCP server command> [args]
```

In the client, replace the server command with the command above. Default `shadow` (byte-for-byte identical response, receipts only). `--mode enforce` cuts to `--cap` bytes (default 16384), writes the original to `artifacts/` (0600) and removes `structuredContent` from cut responses, because it would bypass the cap. `isError` and media are kept. An internal error while processing a message is fail-open.

Tests: `tests/adapters/test_mcp_proxy.py`, with a fake server in `tests/adapters/fake_mcp_server.py`.
