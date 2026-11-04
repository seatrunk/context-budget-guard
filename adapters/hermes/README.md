# Hermes Agent adapter

A user plugin that registers Hermes's public `transform_tool_result` hook and calls the `cbg` core. It does not modify Hermes code.

## Install and enable

```sh
sh adapters/hermes/install.sh            # copies to ~/.hermes/plugins/context-budget-guard (or $HERMES_HOME)
hermes plugins enable context-budget-guard
# restart Hermes (the gateway discovers plugins once per process)
```

Manual equivalent: in `~/.hermes/config.yaml`, `plugins.enabled: [context-budget-guard]`.

Mode, via environment variables of the Hermes process:

| Variable | Default | Effect |
| --- | --- | --- |
| `CBG_MODE` | `shadow` | `shadow` only measures and writes receipts; `enforce` replaces the result with the preview; `off` does nothing |
| `CBG_LOG_DIR` | `$HERMES_HOME/context-budget-guard` | where `receipts.jsonl`, `errors.jsonl` and `artifacts/` live |
| `CBG_RESULT_CAP` | `16384` | cap in UTF-8 bytes |
| `CBG_FRAMING_RESERVE` | `512` | bytes reserved for the wrapper Hermes applies itself |

## Where to see the results

- `~/.hermes/context-budget-guard/receipts.jsonl`: one line per text tool result, with no content. Useful fields: `tool`, `mode` (full, preview, marker, failclosed), `would_change`, `original_bytes`, `rendered_bytes`, `cap`, `exit_code`, `error_locations`, `verified`, `elapsed_us`.
- `artifacts/<sha256>.txt` (0600): complete original, only in `enforce`.
- Quick summary: `python3 -c "import json,sys;r=[json.loads(l) for l in open(sys.argv[1])];print(len(r),'results',sum(x['would_change'] for x in r),'would be cut',sum(x['original_bytes']-x['rendered_bytes'] for x in r if x['would_change']),'bytes saved')" ~/.hermes/context-budget-guard/receipts.jsonl`

## Turning it off

`hermes plugins disable context-budget-guard` and restart, or `CBG_MODE=off`. To remove it: delete `~/.hermes/plugins/context-budget-guard`.

## Known limits

- The public hook only sees string results. Multimodal results pass unchanged.
- Hermes plugin/LSP notes do not reach the public hook, so the core's note ledger is not used here. The MCP proxy and the native patch can use it.
- In `enforce`, Hermes still applies its own `untrusted_tool_result` wrapper outside; that is why the framing reserve exists.
- Any internal error is fail-open: the original result goes through and the error goes to `errors.jsonl`.
