# MCP stdio proxy

Sits between an MCP client and a real MCP server and budgets `tools/call` responses. Standard library only. The implementation is [`spillway/mcp_proxy.py`](../../spillway/mcp_proxy.py); this directory keeps a source-checkout shim.

```sh
spillway mcp --mode shadow -- <MCP server command> [args]                   # installed
python3 adapters/mcp_proxy/proxy.py --mode shadow -- <MCP server command>   # from a checkout
```

In the client configuration, replace the server command with one of these.

| Option | Env | Default | Effect |
| --- | --- | --- | --- |
| `--mode` | `SPILLWAY_MODE` | `shadow` | `shadow` passes responses through byte for byte and writes receipts only. `enforce` caps results. `off` is plain passthrough |
| `--log-dir` | `SPILLWAY_LOG_DIR` | `~/.cache/spillway` | Receipts and artifacts |
| `--cap` | `SPILLWAY_RESULT_CAP` | `16384` | Per-result cap in bytes (floor 256) |
| `--wrap-untrusted` | `SPILLWAY_WRAP_UNTRUSTED=1` | off | Keep the `<untrusted_tool_result>` wrapper in enforced text |
| `--max-artifacts`, `--max-artifact-bytes` | `SPILLWAY_MAX_ARTIFACTS`, `SPILLWAY_MAX_ARTIFACT_BYTES` | `200`, 100 MiB | Artifact retention |

In `enforce`:

- Oversized results become previews. `isError` and media parts are kept, and `structuredContent` is removed from cut responses because it would bypass the cap.
- The original is written to `artifacts/<sha256>.txt` (0600).
- `tools/list` gains **`spillway_read_artifact`** (`sha256`, `offset`, `limit`). The proxy answers it directly with a UTF-8-safe, neutralized slice that always fits within the cap, plus `next_offset` and `eof`, so clients can recover output without filesystem access. The SHA-256 is case-insensitive, and invalid names or symlinks return `isError: true`.

Any internal error while processing a message fails open and forwards the original line. Unchanged messages, including invalid UTF-8, are forwarded as their original bytes.

Known limit: JSON-RPC batch arrays (removed from MCP in 2025-06-18) are passed through without budgeting.

Tests: [`tests/adapters/test_mcp_proxy.py`](../../tests/adapters/test_mcp_proxy.py), with a fake server in [`tests/adapters/fake_mcp_server.py`](../../tests/adapters/fake_mcp_server.py).
