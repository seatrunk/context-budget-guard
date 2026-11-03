# context-budget-guard

### Less tool-output confetti. Keep the clues.

[![CI](https://github.com/seatrunk/context-budget-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/seatrunk/context-budget-guard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **Experimental · activation BLOCKED.** This repository contains an operating skill, design notes, and benchmark tooling. It does **not** ship runtime enforcement or an installer. The separate local prototype is not included here and is not upstream Hermes.

```text
mountain of tool output  -->  useful preview + recoverable artifact
                              ^ intended behavior, not a shipped guard
```

The goal is to bound tool output without dropping the diagnostic that explains what broke. A small error message matters more than another thousand lines of progress bars.

The November 3 protected-note candidate passes its primary aggregate-note regression, but independent review still rejected it: corrective multimodal output can exceed the byte ceiling, finalization loses a note-bearing read's approved receipt allowance, and literal wrapper delimiters remain unsanitized in notes. **Passing suites did not make this candidate ready.** Read the [cycle report](docs/reviews/2026-11-03-protected-notes.md) and [current status](docs/project-status.md).

## What you can use today

- Follow the root [operating skill](SKILL.md) to review evidence and run repository checks.
- Inspect the proposed [design and invariants](docs/design.md).
- Generate synthetic fixtures and validate published data using the [benchmark guide](docs/benchmarking.md).
- Help reproduce the [open correctness gaps](docs/project-status.md) with tiny synthetic cases. Read [CONTRIBUTING.md](CONTRIBUTING.md) first.
- Review the proposed [multi-codebase evaluation protocol](docs/multi-codebase-evaluation.md): correctness first, smaller output second. It is not an implemented harness or a completed benchmark.

You do not need to install dependencies to run the repository tooling. From the repository root with Python 3.11 or newer:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_repo.py
python3 scripts/validate_benchmark.py benchmarks/results/2026-11-02-off-baseline.json
```

These commands check this repository; they do not enable a guard or run the separate prototype's integration suite.

## Evidence, without the victory lap

The [published baseline](benchmarks/results/2026-11-02-off-baseline.json) records actual synthetic CLI runs on November 2, 2026 with the guard **off**. There is one observation per case, no on-mode comparison, and no demonstrated savings. Actual USD cost is unknown; subscription inclusion is not a measured zero-dollar cost. See [measurement limits](docs/benchmarking.md) before comparing numbers.

This cycle's separate native integration recorded 641 passing tests and one existing platform skip; a parent rerun passed 274 overlapping tests. Independent adversarial probes then exposed three blockers. These are **correctness results, not compression or cost benchmarks**, and public CI does not run the absent native implementation. The [sanitized review record](docs/reviews/2026-11-03-protected-notes.json) keeps those evidence sources separate.

## Project map

| Read | For |
| --- | --- |
| [Project status](docs/project-status.md) | Blocker, prototype fingerprint, evidence boundaries |
| [Benchmarking](docs/benchmarking.md) | Reproduction, metrics, reporting rules |
| [Evaluation protocol](docs/multi-codebase-evaluation.md) | Proposed paired offline replay and later task-based evaluation |
| [Latest cycle](docs/reviews/2026-11-03-protected-notes.md) | Rejected candidate, reproduced gaps, lessons learned |
| [Rollout](docs/rollout.md) | Approval gates and rollback discipline |
| [Repository governance](docs/repository-governance.md) | Desired review and branch protections |
| [Security policy](SECURITY.md) | Private reporting and threat boundary |
| [Code of conduct](CODE_OF_CONDUCT.md) | Working together |

Contributions are welcome, especially boring regression tests. Please keep private transcripts out of public issues. The project uses the [MIT license](LICENSE); existing copyright attribution remains unchanged.
