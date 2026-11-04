# Context Budget Guard

![Less noise. Keep the clues. A tool-result stack preserves its failure diagnostic and a path to recover detail. Experimental operating skill and benchmark kit; native runtime not shipped; activation blocked.](docs/assets/hero.svg)

[![CI](https://github.com/seatrunk/context-budget-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/seatrunk/context-budget-guard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**[The idea](#the-idea) · [How it should work](#how-it-should-work) · [The plan](#the-plan) · [Evaluation](#how-we-plan-to-evaluate-it) · [Try the toolkit](#try-the-toolkit)**

> **Experimental · production activation BLOCKED.** Since Stage 1 (PR #14) this repository ships a pure, dependency-free core (`cbg/`), a Hermes plugin and an MCP stdio proxy that default to `shadow`, and an offline replay where the candidate passes 39/39 oracles. See [Core and adapters](#core-and-adapters-v030). The private native patch is still not shipped: its combined local candidate **failed acceptance** and separate delivery-support code was **REJECTED**, as recorded in the [November 4 assessment](docs/reviews/2026-11-04-combined-assessment.md). Still pending: the Stage 2 native gate, a real-task benchmark and independent review. The graphics explain the design, not measured savings.

## The idea

An agent can drown in tool output: a compiler dump, a long file, a giant JSON response. The important part may be just one exit code, one source location, or a short runtime notice.

**The goal is not to delete more text. It is to keep the information the next decision needs—and make the rest recoverable.**

| Keep in view | Keep recoverable | Never trade away |
| --- | --- | --- |
| Useful preview, failure status, necessary notices | Additional detail in a private/redacted artifact | Trust boundaries, valid media, mandatory controls, approved read semantics |

The [operating skill](SKILL.md) describes how to review that behavior. The runtime would enforce it. **Loading a skill is not installing a guard.** Conversation-summary compaction is another layer, not a different name for this tool-output policy.

## How it should work

![Design target: tool data passes through per-result and aggregate budgeting into a model-visible preview. Additional detail goes to a private/redacted artifact. A trusted runtime notice remains exactly once outside the genuine untrusted wrapper, and targeted reads recover extra detail.](docs/assets/output-flow.svg)

### One output, two destinations

1. **For the model:** a useful bounded preview, original error/exit semantics, valid media and any necessary notice.
2. **For recovery:** additional output in a private/redacted artifact, read with targeted `offset` / `limit` when the task actually needs it.
3. **Across both:** track notice ownership by call ID, reserve its complete rendered footprint before spilling, and never restore an unbounded note after the final cap.

A note sitting in a file is not the same as a note the model received. A small preview is not successful if it hides the reason a command failed.

### The proposed defaults

| Surface | Intended ordinary limit | Important boundary |
| --- | --- | --- |
| Complete file selection | 350 effective LF lines **and** 16,384 formatted UTF-8 bytes | Both limits apply; define empty/trailing-line behavior |
| Partial file selection | 150 effective LF lines **and** 16,384 formatted UTF-8 bytes | Paginate instead of silently presenting an incomplete read as complete |
| Final ordinary tool text | 16,384 UTF-8 bytes | Count the final representation, including framing and escaped metadata |
| Inline notice bundles | Up to 4,096 bytes per bundle; 8,192 per batch | Active policy/tiny-budget decisions still apply; archive or use a bounded marker |

Mandatory controls and valid one-use read receipts retain their defined exceptions. Aggregate turn accounting is separate from per-result bytes; irreducible-overhead reporting must not become a byte-limit escape hatch. None of these proposed limits is a total token, money, filesystem or same-UID security boundary. See the [full design](docs/design.md).

## The plan

![Six-stage promotion roadmap: define invariants is documented; the isolated build and review is rejected; repair and re-review is next; multi-code replay is proposed; real-task and compaction evaluation is not run; controlled rollout is locked. Offline characterization may expose failures earlier but cannot override a failing oracle.](docs/assets/roadmap.svg)

**Status after Stage 1:** the published core closes B1–B3 and the core parts of #1 and #3–#9 in its own tests and offline replay. The native runtime is a separate matter: its Stage 2 combined gate, a real-task benchmark and independent review are still pending, so this is not “ship it.”

### Historical record: native combined assessment (November 4, before Stage 1)

Individual repairs for [#6](https://github.com/seatrunk/context-budget-guard/issues/6), [#7](https://github.com/seatrunk/context-budget-guard/issues/7), [#8](https://github.com/seatrunk/context-budget-guard/issues/8) and [#9](https://github.com/seatrunk/context-budget-guard/issues/9) reached scoped independent approvals, then the **combined gate failed: 649 passed, 13 failed, one existing Windows-only skip**. These are local runtime observations, not public CI results or proof of a shipped fix.

| Native blocker (recorded) | Observed result | Addressed in the published core by |
| --- | --- | --- |
| Session rotation | Two approved-read rows remain above 16,384 bytes | `test_B1_*` (re-measured final render; rotated-session receipt rejected) |
| Fallback ownership | A bounded media marker disagrees with the owned original suffix | `test_B2_*` (owner bound to the rendered SHA-256) |
| Persistent failure | Four SECOND-settlement cases lose a notice | `test_B3_*` (retirement only after the last settlement) |
| Delivery-support integrity | Independent review rejected two verifier gaps despite 37 existing tests passing | Not addressed: native delivery support is not published |

Six additional synthetic read/media probes fail before budget commit at an existing result-type guardrail; they are separately unsupported/unverified, not established new budget regressions. The parent independently reproduced all seven product-acceptance failures. The delivery-support implementation and its tests remain separate and are **not shipped on this documentation branch**.

Read the [latest findings and reviewer brief](docs/reviews/2026-11-04-combined-assessment.md), [sanitized evidence JSON](docs/reviews/2026-11-04-combined-assessment.json), and [current status](docs/project-status.md). The [earlier protected-note rejection](docs/reviews/2026-11-03-protected-notes.md) remains historical evidence. Native patches, full probes and the rejected support code are not distributed here; fingerprints are local snapshot identifiers, not a self-contained reproduction package. Issues remain open until the native gate and independent review pass; production activation remains blocked.

## How we plan to evaluate it

![Proposed evaluation: synthetic Python, TypeScript/JavaScript, Rust and SQL/config/log workloads enter paired unbudgeted, historical-spill and candidate-runtime arms. Independent correctness oracles veto broken results before bytes, recovery calls, latency or available token/cost data are compared. Protocol only; no benchmark scores are shown.](docs/assets/evaluation.svg)

### Fidelity first. Efficiency second.

- **Same workload, different arms:** freeze the inputs, call order, budgets and runtime fingerprints. Compare an unbudgeted reference, historical spilling and the actual isolated candidate—not a toy replacement.
- **Check what survives:** diagnostic facts, note placement, failure status, media order, receipt lifetime, artifact recovery and no repeated tool execution.
- **Then measure the whole cost:** output bytes, recovery/tool calls, timing, and actual provider/tokenizer usage when available. Count retries and follow-up reads; report unknown costs as unknown.
- **Only later, with separate approval:** real coding tasks and tests, followed by deliberate conversation-compaction interaction experiments. A benchmark cannot authorize production activation.

The [evaluation protocol](docs/multi-codebase-evaluation.md) is published; the replay harness and execution are **not implemented** by that document. [#11](https://github.com/seatrunk/context-budget-guard/issues/11) tracks the actual benchmark work.

The historical [November 2 baseline](benchmarks/results/2026-11-02-off-baseline.json) remains **guard off, one observation per case**. There is no published on-mode comparison, measured savings, or verified live-backend enforcement. The [benchmark guide](docs/benchmarking.md) explains the evidence limits.

## Core and adapters (v0.3.0)

Since Stage 1 the repo publishes the pure core, with no I/O and no dependencies (Python 3.11+ stdlib):

| Path | What it is |
| --- | --- |
| [`cbg/`](cbg/) | `limits` (effective LF lines, UTF-8 cut), `render` (final bytes with framing, multimodal JSON escaping and note suffix), `notes` (ownership by call ID), `sanitize` (delimiters), `facts` (exit code and `file:line`), `budget` (limiter and batch) and `verify` (independent receipt verifier) |
| [`adapters/hermes/`](adapters/hermes/README.md) | Hermes Agent plugin via the `transform_tool_result` hook |
| [`adapters/mcp_proxy/`](adapters/mcp_proxy/README.md) | MCP stdio proxy |
| [`benchmarks/replay/`](benchmarks/replay/README.md) | offline replay with three arms and fidelity oracles |
| [`docs/model/notes.md`](docs/model/notes.md) | note state machine |

The verifier rereads the final output and, if the receipt does not match, delivers a bounded marker (fail closed). The private native patch stays outside the repo. Production activation remains blocked by the [rollout](docs/rollout.md).

### Installing in Hermes

```sh
sh adapters/hermes/install.sh
```

The script copies `adapters/hermes/context_budget_guard/__init__.py` and `plugin.yaml` to `${HERMES_HOME:-~/.hermes}/plugins/context-budget-guard/`, and the whole `cbg/` core to `vendor/cbg` inside that directory, deleting `__pycache__`. It activates nothing: Hermes only loads plugins listed in `plugins.enabled`.

### Turning it on and off

```sh
hermes plugins enable context-budget-guard     # or plugins.enabled: [context-budget-guard] in ~/.hermes/config.yaml
# restart Hermes: the gateway discovers plugins once per process
hermes plugins disable context-budget-guard    # turns it off; restart again
```

To remove it for good: delete `~/.hermes/plugins/context-budget-guard`.

### Modes and variables (Hermes adapter)

| Variable | Default | Effect |
| --- | --- | --- |
| `CBG_MODE` | `shadow` | `shadow` (observation): measures and writes a receipt; the model receives the original. `enforce`: replaces results above the cap with the preview and writes the original to `artifacts/`. `off`: does nothing and writes nothing. An invalid value becomes `shadow` |
| `CBG_LOG_DIR` | `$HERMES_HOME/context-budget-guard` (or `~/.hermes/context-budget-guard`) | directory for `receipts.jsonl`, `errors.jsonl` and `artifacts/` |
| `CBG_RESULT_CAP` | `16384` | cap in UTF-8 bytes |
| `CBG_FRAMING_RESERVE` | `512` | bytes subtracted from the cap for the `untrusted_tool_result` wrapper that Hermes applies afterwards; the core uses `max(256, CBG_RESULT_CAP - CBG_FRAMING_RESERVE)` |

An internal plugin error is fail-open: the original result goes through and `errors.jsonl` receives `{"tool", "error"}` (only the exception name).

### MCP proxy

```sh
python3 adapters/mcp_proxy/proxy.py [--mode shadow|enforce|off] [--log-dir DIR] [--cap N] -- <real server command> [args]
```

In the MCP client, replace the server command with that line. The real server runs as a child process. Every message passes unchanged, except responses to `tools/call`. Defaults: `--mode` comes from `CBG_MODE` (otherwise `shadow`), `--log-dir` from `CBG_LOG_DIR` (otherwise `~/.cache/context-budget-guard`), `--cap` from `CBG_RESULT_CAP` (otherwise `16384`, with no framing reserve). In `shadow` the response is byte-for-byte identical. In `enforce`, a response above the cap becomes a preview, `isError` and media are kept, the original goes to `artifacts/` and `structuredContent` is removed (it would bypass the cap). `off` passes everything through and writes no receipt.

### Warning: `artifacts/` holds the complete output

With `CBG_MODE=enforce` (Hermes) or `--mode enforce` (MCP proxy), `artifacts/<sha256>.txt` holds the **complete, unredacted** output of every cut tool result. It can contain secrets (tokens, keys, `.env` files read by the agent), PII and private code. The guard redacts nothing.

- The adapter creates directories with 0700 and files with 0600. That only protects against other users on the system, not against processes running under the same UID.
- Do not commit or share `artifacts/`, `receipts.jsonl` or `errors.jsonl`. The repo `.gitignore` already ignores `artifacts/` and `*.jsonl`, but the default `CBG_LOG_DIR` lives outside the repo on purpose; do not point that directory inside a repository.
- Cleanup: `rm -rf ~/.hermes/context-budget-guard/artifacts` (Hermes) or `rm -rf ~/.cache/context-budget-guard/artifacts` (proxy), or the `CBG_LOG_DIR` you configured. Receipts hold no content, but they do hold tool names and error locations (`file:line`); delete `receipts.jsonl` too if that is sensitive.
- In `shadow` no artifact is written.

`install.sh` refuses an empty destination, or one that does not end in `/plugins/context-budget-guard` (it accepts `CBG_INSTALL_DEST` for tests), before any `rm -rf`.

### Receipts

One JSON line per tool result in `receipts.jsonl`. It contains no result content. In `enforce`, `artifacts/<artifact_sha256>.txt` holds the complete original (files 0600, directories 0700).

Core fields (`cbg/budget.py`, `apply_budget`):

| Field | Meaning |
| --- | --- |
| `call_id` | tool call ID (in the proxy, `mcp-<JSON-RPC id>`) |
| `mode` | `full` (fit entirely), `preview` (head and tail with a facts header), `marker` (header only), `withheld` (policy or aggregate failure), `failclosed` (verifier rejected), `control` (mandatory control, no cap) |
| `kind` | `text` or `multimodal` |
| `cap` | cap applied in bytes (`null` for control) |
| `rendered_bytes` / `rendered_sha256` | size and hash of the measured final render |
| `original_bytes` / `original_lines` | size in UTF-8 bytes and effective LF lines of the original |
| `exit_code` | detected exit code (`null` if none) |
| `error_locations` | up to 5 extracted `file:line` locations |
| `notes_shown` / `notes_marked` | IDs of notes that are visible / represented only by a marker (empty in the Hermes adapter) |
| `media_parts` | number of preserved media parts |
| `artifact_sha256` / `artifact_bytes` | hash and size of the original |
| `receipt_used` | whether an approved-read receipt (#7) was applied |
| `verified` | the verifier accepted the final render |
| `violations_before_failclose` | violations found before failing closed (empty list in the normal case) |
| `policy_error`, `aggregate_bytes`, `aggregate_unsatisfiable` | only in `finalize_batch` (batch); they do not appear in the adapters |

Fields added by the Hermes adapter: `ts`, `tool`, `session_id`, `adapter` (`hermes`), `adapter_mode`, `elapsed_us`, `would_change` (the mode is neither `full` nor `control`, so enforce would change the result). By the proxy: `ts`, `tool`, `adapter` (`mcp_proxy`), `adapter_mode`, `is_error`, `would_change`. In `enforce` the proxy also writes a `{"call_id", "structured_content_dropped": true}` line when it removes `structuredContent`.

### Known risks and limits

- The private native patch has not been proven. B1–B3 are closed in the published core, not in the private runtime; the native combined gate is still pending.
- The public Hermes hook only sees text results. Multimodal passes unchanged, and the runtime's plugin/LSP notes do not reach the hook.
- We reserve 512 bytes for the Hermes wrapper. In `enforce` the receipt measures our render, not the final text assembled by Hermes.
- The offline replay is synthetic: it does not measure tokens or cost, and the historical-spill arm is an emulation, not the old runtime.

### Real-task benchmark plan

1. Observation (`CBG_MODE=shadow`, one week or a fixed batch of tasks). Measure: bytes before and after (`original_bytes` and `rendered_bytes`), how many results would exceed the cap (`would_change`), oracle violations (`verified=false`, `mode=failclosed`, non-empty `violations_before_failclose`) and latency (`elapsed_us`, Hermes only).
2. Enforce: the same tasks, in A/B pairs (same prompt, repository at the same commit, same model; one arm `shadow`, the other `enforce`, alternating order). Compare task success (tests pass, criterion defined beforehand), tokens and cost from the invoice or provider logs, recovery reads in `artifacts/`, and fidelity regressions (the model lost the exit code, error location or note). At least 5 pairs per task; report median and IQR.

Aggregation with jq:

```sh
R=~/.hermes/context-budget-guard/receipts.jsonl
jq -s 'map(select(.mode)) | {total: length, would_exceed_cap: map(select(.would_change)) | length,
        bytes_before: (map(.original_bytes) | add), bytes_after: (map(.rendered_bytes) | add),
        not_verified: map(select(.verified == false or .mode == "failclosed")) | length,
        by_mode: (group_by(.mode) | map({(.[0].mode): length}) | add)}' "$R"
jq -s 'map(.elapsed_us // empty) | sort | {n: length, p50: .[length/2|floor], p95: .[length*0.95|floor], max: .[-1]}' "$R"
jq -r 'select(.would_change) | [.tool, .original_bytes, .rendered_bytes] | @tsv' "$R" | sort | uniq -c | sort -rn | head
```

The same with Python stdlib only:

```sh
python3 - ~/.hermes/context-budget-guard/receipts.jsonl <<'PY'
import json, statistics, sys
r = [json.loads(l) for l in open(sys.argv[1]) if l.strip() and '"mode"' in l]
cut = [x for x in r if x.get("would_change")]
lat = sorted(x["elapsed_us"] for x in r if "elapsed_us" in x)
print("results", len(r), "would exceed cap", len(cut))
print("bytes before", sum(x["original_bytes"] for x in r), "after", sum(x["rendered_bytes"] for x in r))
print("not verified", sum(1 for x in r if not x.get("verified") or x["mode"] == "failclosed"))
if lat:
    print("latency us p50", statistics.median(lat), "p95", lat[int(len(lat) * 0.95)], "max", lat[-1])
PY
```

Reproduce the offline replay (0 model calls):

```sh
python3 benchmarks/replay/replay.py --out /tmp/offline-replay.json
cmp /tmp/offline-replay.json benchmarks/replay/results/offline-replay.json && echo identical
```

The command exits with 1 if the candidate arm fails any oracle. `cmp` should stay silent and the line should print `identical`; CI does the same.

## Try the toolkit

Python 3.11+, no dependency installation, credentials or live profile required:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_repo.py
python3 scripts/validate_benchmark.py benchmarks/results/2026-11-02-off-baseline.json
```

These check the **public tooling**, not the separate runtime. To create synthetic fixtures, choose a new output directory:

```sh
python3 scripts/generate_fixtures.py --output benchmark-fixtures
```

The generator refuses existing paths. Generating fixtures does not run a model, recreate measured timing, or complete the proposed multi-codebase benchmark.

## Go deeper

| Start here | What you get |
| --- | --- |
| [Operating skill](SKILL.md) | Repeatable evidence and review procedure |
| [Design](docs/design.md) | Invariants, exceptions and protected-note contract |
| [Project status](docs/project-status.md) | Stage 1 delivery, native fingerprints and remaining gates |
| [Latest assessment / reviewer handoff](docs/reviews/2026-11-04-combined-assessment.md) | Scoped progress, combined failures, verifier findings and decisions for the next reviewer |
| [Prior protected-note cycle](docs/reviews/2026-11-03-protected-notes.md) | Historical rejection and original defect evidence |
| [Evaluation protocol](docs/multi-codebase-evaluation.md) | Proposed corpus, comparison arms, metrics and promotion gates |
| [Rollout](docs/rollout.md) | Separate approval and rollback requirements |
| [Governance](docs/repository-governance.md) | Required review and branch protections |
| [Visual guide](docs/visual-guide.html) · [artwork sources](docs/assets/README.md) | Self-contained offline gallery and editable SVG/PNG graphics |

Contributions are welcome, especially small adversarial reproductions. Start with [CONTRIBUTING.md](CONTRIBUTING.md). Keep sensitive reports private under [SECURITY.md](SECURITY.md), follow the [code of conduct](CODE_OF_CONDUCT.md), and preserve the existing [MIT license](LICENSE) attribution.
