# Context Budget Guard

![Less noise. Keep the clues. A tool-result stack preserves its failure diagnostic and a path to recover detail. Experimental operating skill and benchmark kit; runtime not shipped; activation blocked.](docs/assets/hero.svg)

[![CI](https://github.com/seatrunk/context-budget-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/seatrunk/context-budget-guard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**[The idea](#the-idea) · [How it should work](#how-it-should-work) · [The plan](#the-plan) · [Evaluation](#how-we-plan-to-evaluate-it) · [Try the toolkit](#try-the-toolkit)**

> **Experimental · activation BLOCKED.** This repository ships an operating skill, specifications and benchmark tools—not runtime enforcement or an installer. The combined local candidate **fails acceptance**, and separate delivery-support code was **REJECTED** in review. Read the [latest findings and reviewer handoff](docs/reviews/2026-11-04-combined-assessment.md). These graphics explain the intended design, not a working release or measured savings.

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

**We are between “review rejected” and “repair + re-review,” not between “tests passed” and “ship it.”**

Individual repairs for [#6](https://github.com/seatrunk/context-budget-guard/issues/6), [#7](https://github.com/seatrunk/context-budget-guard/issues/7), [#8](https://github.com/seatrunk/context-budget-guard/issues/8) and [#9](https://github.com/seatrunk/context-budget-guard/issues/9) reached scoped independent approvals, then the **combined gate failed: 649 passed, 13 failed, one existing Windows-only skip**. These are local runtime observations, not public CI results or proof of a shipped fix.

| Current blocker | Observed result | Next review question |
| --- | --- | --- |
| Session rotation | Two approved-read rows remain above 16,384 bytes | Reconcile re-budgeting with old-scope notice ownership |
| Fallback ownership | A bounded media marker disagrees with the owned original suffix | Define ownership of the actual displayed notice |
| Persistent failure | Four SECOND-settlement cases lose a notice | Reconcile owner retirement with repeated finalization |
| Delivery-support integrity | Independent review rejected two verifier gaps despite 37 existing tests passing | Verify actual executing source and managed dependencies |

Six additional synthetic read/media probes fail before budget commit at an existing result-type guardrail; they are separately unsupported/unverified, not established new budget regressions. The parent independently reproduced all seven product-acceptance failures. The delivery-support implementation and its tests remain separate and are **not shipped on this documentation branch**.

Read the [latest findings and reviewer brief](docs/reviews/2026-11-04-combined-assessment.md), [sanitized evidence JSON](docs/reviews/2026-11-04-combined-assessment.json), and [current status](docs/project-status.md). The [earlier protected-note rejection](docs/reviews/2026-11-03-protected-notes.md) remains historical evidence. Native patches, full probes and the rejected support code are not distributed here; fingerprints are local snapshot identifiers, not a self-contained reproduction package. Issues remain open and activation remains blocked.

## How we plan to evaluate it

![Proposed evaluation: synthetic Python, TypeScript/JavaScript, Rust and SQL/config/log workloads enter paired unbudgeted, historical-spill and candidate-runtime arms. Independent correctness oracles veto broken results before bytes, recovery calls, latency or available token/cost data are compared. Protocol only; no benchmark scores are shown.](docs/assets/evaluation.svg)

### Fidelity first. Efficiency second.

- **Same workload, different arms:** freeze the inputs, call order, budgets and runtime fingerprints. Compare an unbudgeted reference, historical spilling and the actual isolated candidate—not a toy replacement.
- **Check what survives:** diagnostic facts, note placement, failure status, media order, receipt lifetime, artifact recovery and no repeated tool execution.
- **Then measure the whole cost:** output bytes, recovery/tool calls, timing, and actual provider/tokenizer usage when available. Count retries and follow-up reads; report unknown costs as unknown.
- **Only later, with separate approval:** real coding tasks and tests, followed by deliberate conversation-compaction interaction experiments. A benchmark cannot authorize production activation.

The [evaluation protocol](docs/multi-codebase-evaluation.md) is published; the replay harness and execution are **not implemented** by that document. [#11](https://github.com/seatrunk/context-budget-guard/issues/11) tracks the actual benchmark work.

The historical [November 2 baseline](benchmarks/results/2026-11-02-off-baseline.json) remains **guard off, one observation per case**. There is no published on-mode comparison, measured savings, or verified live-backend enforcement. The [benchmark guide](docs/benchmarking.md) explains the evidence limits.

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
| [Project status](docs/project-status.md) | Exact candidate fingerprint and remaining blockers |
| [Latest assessment / reviewer handoff](docs/reviews/2026-11-04-combined-assessment.md) | Scoped progress, combined failures, verifier findings and decisions for the next reviewer |
| [Prior protected-note cycle](docs/reviews/2026-11-03-protected-notes.md) | Historical rejection and original defect evidence |
| [Evaluation protocol](docs/multi-codebase-evaluation.md) | Proposed corpus, comparison arms, metrics and promotion gates |
| [Rollout](docs/rollout.md) | Separate approval and rollback requirements |
| [Governance](docs/repository-governance.md) | Required review and branch protections |
| [Visual guide](docs/visual-guide.html) · [artwork sources](docs/assets/README.md) | Self-contained offline gallery and editable SVG/PNG graphics |

Contributions are welcome, especially small adversarial reproductions. Start with [CONTRIBUTING.md](CONTRIBUTING.md). Keep sensitive reports private under [SECURITY.md](SECURITY.md), follow the [code of conduct](CODE_OF_CONDUCT.md), and preserve the existing [MIT license](LICENSE) attribution.
