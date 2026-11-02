---
name: context-budget-guard
description: Review output-budget evidence before any rollout.
version: 0.1.0
author: Ricardo Margalho (seatrunk), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [context, tool-output, benchmarking, review]
    related_skills: []
---

# Context budget guard operating procedure

Use this skill to review proposed output budgeting and reproduce repository checks. It is an operating procedure, not runtime enforcement: loading it changes no configuration and supplies no installer.

## When to use

- Reviewing output truncation, artifact handling, or benchmark claims.
- Preparing a synthetic regression case or assessing rollout readiness.
- Do not use it to authorize activation or claim an upstream Hermes feature.

## Prerequisites

Read [project status](docs/project-status.md) and [design](docs/design.md) with `read_file`. Use Python 3.11+ from the repository root. No dependency installation, credentials, or live profile access is required.

## Procedure

1. Record the proposed scope and candidate fingerprint. Match any prototype evidence to its exact base revision and patch SHA-256; a changed candidate needs new review. Completion: evidence and candidate identity agree.
2. Check the known missing-note failure before optimizing size. Build a synthetic plugin/LSP note that fits individually, trigger aggregate spill, and inspect what the model receives. Completion: necessary notes remain visible, or the candidate stays blocked.
3. Review complete/partial reads, UTF-8 boundaries, mandatory control content, media, error/exit metadata, artifact privacy, and cached policy behavior against the design. Completion: every invariant has evidence or an explicit gap.
4. Run repository checks through `terminal`:
   - `terminal(command="python3 -m unittest discover -s tests -v")`
   - `terminal(command="python3 scripts/check_repo.py")`
   - `terminal(command="python3 scripts/validate_benchmark.py benchmarks/results/2026-11-02-off-baseline.json")`
   Completion: retain actual command outcomes, including failures; do not substitute prototype test counts.
5. For new data, follow [benchmarking](docs/benchmarking.md). Publish only synthetic, privacy-reviewed evidence. Completion: modes, units, sample counts, cost unknowns, and cache accounting are explicit.
6. Report approval separately from tests. Apply [rollout gates](docs/rollout.md); never activate, restart, or modify profiles merely because checks passed. Completion: unresolved issues and required human approval are stated.

## Pitfalls

A stored artifact does not prove the model saw a necessary note. UTF-8 bytes are not tokens. An off-only baseline cannot establish savings. Repository CI cannot certify a runtime that is absent from this repository. Same-UID compromise is outside the intended authorization boundary.

## Verification

Return changed files, real check results, candidate identity when relevant, and remaining blockers. Keep private paths, session identifiers, credentials, and transcripts out of the report. Current activation status remains **BLOCKED**.
