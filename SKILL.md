---
name: context-budget-guard
description: "Use when reviewing output-budget evidence or rollout gates."
version: 0.3.0
author: Ricardo Margalho (seatrunk), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [context, tool-output, benchmarking, review]
    related_skills: []
---

# Context budget guard operating procedure

Use this skill to review proposed output budgeting and reproduce repository checks. It is an operating procedure, not runtime enforcement: loading it changes no configuration. The optional Hermes installer lives in `adapters/hermes/` and must be run explicitly.

## When to use

- Reviewing output truncation, artifact handling, or benchmark claims.
- Preparing a synthetic regression case or assessing rollout readiness.
- Do not use it to authorize activation or claim an upstream Hermes feature.

## Prerequisites

Read [project status](docs/project-status.md) and [design](docs/design.md) with `read_file`. Use Python 3.11+ from the repository root. No dependency installation, credentials, or live profile access is required.

## Núcleo executável (0.3.0)

- Testes e invariantes: `python3 -m unittest discover -s tests -v`.
- Replay offline: `python3 benchmarks/replay/replay.py` (0 chamadas de modelo; sai 1 se o candidato falhar um oráculo).
- Hermes: [adapters/hermes/README.md](adapters/hermes/README.md). Comece em `CBG_MODE=shadow` e leia `receipts.jsonl` antes de qualquer `enforce`.

## Procedure

1. Record the proposed scope and candidate fingerprint. Match any prototype evidence to its exact base revision and patch SHA-256; a changed candidate needs new review. Completion: evidence and candidate identity agree.
2. Check the known missing-note failure before optimizing size. Build a synthetic plugin/LSP note that fits individually, trigger aggregate spill, and inspect what the model receives. Completion: necessary notes remain visible, or the candidate stays blocked.
3. Review complete/partial reads, UTF-8 boundaries, mandatory control content, media, error/exit metadata, artifact privacy, and cached policy behavior against the design. Completion: every invariant has evidence or an explicit gap.
   - Inspect actual assertions, not test names or green totals. A receipt-bearing result must traverse admission, dispatch, commit **and finalization**; compare the no-note control after the one-use allowance is consumed.
   - Measure complete rendered multimodal bytes after corrective compaction, including escaped status fields, JSON/text-part overhead, separators and appended notes. Aggregate characters alone are not a per-result byte check.
   - Put a literal wrapper delimiter in the **queued note itself** when testing note sanitization; a delimiter in the opaque body tests a different boundary.
   - Check repeated/control-only batches and missing segments for exactly-once delivery and a documented ownership lifetime. Do not drop pending notes just to clear state.
4. Run repository checks through `terminal`:
   - `terminal(command="python3 -m unittest discover -s tests -v")`
   - `terminal(command="python3 scripts/check_repo.py")`
   - `terminal(command="python3 scripts/validate_benchmark.py benchmarks/results/2026-11-02-off-baseline.json")`
   Completion: retain actual command outcomes, including failures; do not substitute prototype test counts.
5. For new data, follow [benchmarking](docs/benchmarking.md) and the proposed [multi-codebase evaluation protocol](docs/multi-codebase-evaluation.md). Use the actual isolated runtime, matched inputs and independent correctness oracles; do not evaluate a substitute implementation. Separate tool-output guard behavior from conversation-summary compaction. Publish only synthetic, privacy-reviewed evidence. Completion: modes, units, sample counts, cost unknowns, cache accounting and all failures are explicit; proposed experiments are not reported as completed.
6. Report approval separately from tests. Apply [rollout gates](docs/rollout.md); never activate, restart, or modify profiles merely because checks passed. Honor the explicit implementation/review allowance: resume an interrupted cycle without resetting it, and stop on rejection when no further cycle is authorized. Completion: unresolved issues and required human approval are stated.

## Pitfalls

A stored artifact does not prove the model saw a necessary note. UTF-8 bytes are not tokens. An off-only baseline cannot establish savings. Repository CI cannot certify a runtime that is absent from this repository. Same-UID compromise is outside the intended authorization boundary.

The [November 3 review](docs/reviews/2026-11-03-protected-notes.md) demonstrates why a large passing suite is not acceptance: its tests missed receipt finalization, escaped multimodal corrective overhead, and a delimiter originating in a note. Overlapping worker/parent/reviewer totals must not be added as unique coverage.

## Verification

Return changed files, real check results, candidate identity when relevant, and remaining blockers. Keep private paths, session identifiers, credentials, and transcripts out of the report. Current activation status remains **BLOCKED**.
