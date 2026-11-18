# Hermes Agent adapter

A user plugin that registers Hermes's public `transform_tool_result` hook and calls the `spillway` core. It does not modify Hermes code.

## Install and enable

```sh
sh adapters/hermes/install.sh      # copies to ${HERMES_HOME:-~/.hermes}/plugins/spillway, with the core in vendor/spillway
hermes plugins enable spillway     # or plugins.enabled: [spillway] in ~/.hermes/config.yaml
# restart Hermes (the gateway discovers plugins once per process)
```

The installer enables nothing. It refuses an empty destination, or one that does not end in `/plugins/spillway`, before it runs `rm -rf`. `SPILLWAY_INSTALL_DEST` overrides the destination for tests. Upgrading from 0.3.x? Run `hermes plugins disable context-budget-guard`, then delete `~/.hermes/plugins/context-budget-guard`.

## Configuration

Set these in the environment of the Hermes process. The legacy `CBG_*` names are read when the `SPILLWAY_*` name is unset.

| Variable | Default | Effect |
| --- | --- | --- |
| `SPILLWAY_MODE` | `shadow` | `shadow` measures and writes receipts, and the model sees the original. `enforce` replaces oversized results with the preview and saves the original. `off` does nothing. An invalid value becomes `shadow` |
| `SPILLWAY_LOG_DIR` | `$HERMES_HOME/spillway` | Holds `receipts.jsonl`, `errors.jsonl` and `artifacts/` |
| `SPILLWAY_RESULT_CAP` | `16384` | Cap in UTF-8 bytes |
| `SPILLWAY_FRAMING_RESERVE` | `512` | Bytes reserved for the wrapper Hermes adds; the core cap is `max(256, CAP - RESERVE)` |
| `SPILLWAY_MAX_ARTIFACTS` / `SPILLWAY_MAX_ARTIFACT_BYTES` | `200` / `104857600` | Artifact retention |

## What changes in `enforce`

An oversized result becomes a `[spillway preview] …` header followed by a head and a tail. The header names the artifact's absolute path, for example `artifact path=<HERMES_HOME>/spillway/artifacts/<sha256>.txt (read with offset/limit)` with `<HERMES_HOME>` expanded, so the agent can page through it with `read_file`. The exit code is taken from JSON results (`{"output": …, "exit_code": N}`). Tracebacks inside JSON strings are found as well.

## Where to see the results

- `receipts.jsonl`: one content-free line per text tool result. Field reference: [docs/design.md](../../docs/design.md#receipt-fields).
- `spillway stats ~/.hermes/spillway/receipts.jsonl` (installed CLI), or `python3 -m spillway.cli stats …` from a checkout.
- `artifacts/<sha256>.txt` (0600): the complete original, written only in `enforce`.

## Turning it off

`hermes plugins disable spillway` and restart, or set `SPILLWAY_MODE=off`. To remove it, delete `~/.hermes/plugins/spillway`.

## Known limits

- The public hook only sees string results. Multimodal results pass through unchanged.
- Plugin and LSP notes do not reach the public hook, so the note ledger is not used here.
- Hermes still wraps the result in its own `untrusted_tool_result` outside the plugin's output, which is why the framing reserve exists. The receipt measures Spillway's render, not the final text Hermes assembles.
- Any internal error fails open: the original result goes through, and the exception type name goes to `errors.jsonl`.
