# Combined #6–#9 assessment and delivery-support review

**Status: BLOCKED — review handoff, not a runtime release.** Snapshot through November 4, 2026 at 02:25 UTC (November 3 in UTC−03). This report publishes progress and retained failures for another reviewer to propose modifications. It does not select a new ownership contract, authorize repairs, close issues, or approve activation.

The [machine-readable summary](2026-11-04-combined-assessment.json) contains the corresponding fingerprints and attributed outcomes. The [earlier protected-note rejection](2026-11-03-protected-notes.md) remains historical evidence; it is not the latest candidate.

## What is and is not available here

This publication is **documentation only**. The rejected native composite and rejected delivery-support code, full patches, executable probes, raw logs and local evidence package are **not included**. Candidate-relative source/test names below are references into those separate worktrees, not links to files shipped by this repository.

Git trees and patch hashes identify retained local snapshots. They are not promises that those objects can be fetched from this public remote. A reviewer without the local evidence needs a separately authorized, sanitized exact-fingerprint source/probe export before claiming independent reproduction or proposing a verified code patch. Do not reconstruct missing code from these summaries and call it the assessed candidate.

No private paths, credentials, profiles, transcripts or raw runtime logs are published. These are correctness and reproducibility findings, not claimed OS/same-UID security-boundary violations.

## Progress before the combined gate

All four issues reached independent **scoped approval** in isolated checkpoints. That progress is real, but their approvals do not compose into combined readiness. Issues remain open for actual delivery.

| Issue | Scoped progress | Frozen tree | Boundary |
| --- | --- | --- | --- |
| [#6](https://github.com/seatrunk/context-budget-guard/issues/6) | Corrective rendered-byte accounting and status serialization; permanent boundary tests | `f8183457faa4ba8404ebef5aa07d02bcbd5bde03` | Approval covers the narrow correction, not every inherited fallback |
| [#7](https://github.com/seatrunk/context-budget-guard/issues/7) | Preserve committed approved-read presentation without reusing the receipt; repair proof consumption to check row identity first | `219341fb26c4a262afb2e6c145e6194974048352` | Separate sibling of #8; still needed compatibility with #9 |
| [#8](https://github.com/seatrunk/context-budget-guard/issues/8) | Encode actual queued notice delimiters; recover exact emitted JSON archive pointers, including literal/entity path distinctions | `7399d18b675b621c216fceb624ac3e5c9becea6e` | Scoped framing/recovery approval; inherited fallback risks retained |
| [#9](https://github.com/seatrunk/context-budget-guard/issues/9) | Bind the actual operation owner through policy, redaction, writers and downstream budgeting; distinguish pending/delivered ownership and preserve grant rotation | `089e068a528b6f018ed9c3356ec9e11c9d75f139` | Inherits #8, not #7; pending-state and repeated-failure limits disclosed |

The composite began from frozen #9 and integrated #7 without modifying the frozen predecessors. It retained all 34 inherited feature paths. Three production modules changed during integration: `agent/context_budget_guard.py`, `agent/context_budget_notes.py`, and `agent/context_budget_note_policy.py`. Both approved #7 test files were copied byte-for-byte; two composite test files were added. The sealed composite has 38 changed paths in total.

## Exact composite identity

```text
native upstream base: bf0203a794a07aac3ff764972ab9087baa4e4f4e
starting approved #9 tree: 089e068a528b6f018ed9c3356ec9e11c9d75f139
initial composite tree: e35b5b0fd06cdaaa36bf5ac5adfa24b757f4be84
full patch SHA-256: a154f4438caece252141b4a1698abb7a2e0800139e8e9ae41e6fca3f372685f2
integration delta SHA-256: 557beb0a42440d138f5b11443ca099fc87382d3e039f32a15aa1977ce8529442
candidate manifest SHA-256: 351816cb19ffe78d6f1ead1abcba2934af9e11b61301acb8110dab212184ca06
```

Parent verification checked all 38 source files and their source/patch exports, both full exports, 101 frozen source/evidence hashes, and seven gate log/receipt pairs. Hash consistency is not semantic approval. Frozen checkpoints were preserved and no live-source edit was made.

## Executed native gates

| Run owner / scope | Passed | Failed | Skipped | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Implementer, unchanged #7 tracer before integration | 24 | 47 | 0 | Establishes missing compatibility; some failures were missing proof-cache attributes, not lost bodies |
| Implementer, original #7 tests after integration | 69 | 2 | 0 | All nine same-ID ownership cases pass; rotated-session cases remain red |
| Implementer, frozen #9 26-file subset | 562 | 0 | 1 | Preserved inherited gates; not overall approval |
| Implementer, two new composite files | 18 | 11 | 0 | Includes six pre-commit result-type probes, separated below |
| Implementer, final deduplicated 30-file gate | **649** | **13** | **1** | **Combined acceptance failed** |
| Parent, targeted product-blocker reproduction in two files | 1 | 7 | 0 | Independently reproduces all seven product-acceptance failures |

The single skip is an existing Windows-only case on Linux. All 12 staged checks and both diff checks passed. The added-line scan reported only synthetic fixture matches; it is not a comprehensive secret scan or independent approval. Runs and subsets overlap: **do not add these counts into a unique total**. The root-cause explanations below follow the implementer's trace; the parent independently reproduced the seven product failures. Independent contract/code review is still needed. No independent composite approval was requested or obtained for this failing candidate.

### B1 — rotated-session results retain the larger ceiling (2 failures)

The unchanged #7 rotation tests retain results of **21,407 and 21,823 bytes**, above the ordinary 16,384-byte limit. Old presentation proofs and one-use grants are correctly cleared, but #9's new-owner eligibility excludes the old-scope owned note, and the resulting row escapes the necessary re-budgeting.

Reproduction identifiers in the separate candidate:

- `tests/agent/test_context_budget_approved_reads.py::test_approval_cannot_escape_admission_or_changed_output_budgets[string-rotated-session]`
- `tests/agent/test_context_budget_approved_reads.py::test_approval_cannot_escape_admission_or_changed_output_budgets[status-rotated-session]`

**Decision needed:** reconcile old-row re-budgeting with ownership isolation. Do not revive an allowance, archive into another profile, consume another scope's genuine pending notice, or edit cached past messages merely to satisfy a byte assertion.

### B2 — withheld media presentation and owned suffix disagree (1 failure)

Under unavailable policy, a control-heavy note has 3,043 source bytes but its original JSON text-block presentation occupies **18,073 bytes**. The fallback displays a bounded withheld marker and the final output is small, but ownership still names the original suffix. An independent detachment oracle therefore fails. The string control passes.

Reproduction identifier: `tests/agent/test_context_budget_composite_fallbacks.py::test_control_heavy_unavailable_policy_matches_owned_presentation[True]`.

**Decision needed:** define truthful, idempotent ownership of the actual bounded presentation without pretending a marker preserves the original notice. Small output alone is insufficient evidence of note preservation. Related behavior was already disclosed on predecessor candidates; this is not established as newly introduced by the merge.

### B3 — persistent failure loses a notice at SECOND settlement (4 failures)

Policy/aggregate failure × string/media yields four failing cases. First settlement retains the notice and retires its ownership. The dependency remains unavailable; the second settlement rewrites the already-delivered content and loses the trusted notice. Result sizes satisfy the byte cap, but preservation fails. Restoring the dependency before the second call does not test this condition.

Reproduction: `tests/agent/test_context_budget_composite_fallbacks.py::test_second_settlement_preserves_notice_with_dependency_still_unavailable`, covering all four `policy`/`aggregate` and `False`/`True` parameter combinations.

**Decision needed:** reconcile delivered-owner retirement with idempotent repeated finalization under persistent failure, while retaining genuine pending exact-ID owners and not creating a global unbounded delivery ledger by accident.

### P1 — six pre-commit read/media probes are unsupported or unverified

Six cases in `tests/agent/test_context_budget_composite.py::test_receipt_encoded_notice_and_rendered_settlement` encounter the existing `tool_guardrails._result_hash` `dict.encode` assumption before budget commit. Their supplied result shape does not reach the lifecycle under test.

These six red probes are retained separately from the seven product failures. They are **neither newly demonstrated budget regressions nor passing media-read lifecycle coverage**. Investigate whether the probe uses supported real-adapter normalization before proposing unrelated native API expansion. Existing external-tool multimodal controls and altered-media rejection remained green. No guardrail bypass or new result-type API was implemented.

### Native reproduction command template

Only use this after obtaining the exact separate candidate and preparing an isolated interpreter via the upstream-managed workflow. The placeholder is not an installed interpreter path; these files do not exist in this documentation-only repository.

```sh
env -u __HERMES_ACTIVATED HERMES_PYTHON='<managed-test-python>' \
  scripts/run_tests.sh \
  tests/agent/test_context_budget_approved_reads.py \
  tests/agent/test_context_budget_composite_fallbacks.py \
  --file-retries 0 -j 1 \
  -k 'rotated-session or control_heavy or second_settlement' \
  -q --tb=short --show-capture=no
```

Recorded parent result: exit 1, one passed and seven failed. Keep these expectations red until a reviewed correction changes the behavior; do not replace them with permissive markers or xfails.

## Separate public-delivery support: implemented, then REJECTED

A separate worktree implemented stdlib manifest/materialization support, deterministic real-Git fixtures, payload hygiene checks, documentation and proposed native CI. None of these six changed files is delivered by this documentation-only handoff:

- `scripts/runtime_delivery.py`
- `tests/test_runtime_delivery.py`
- `scripts/check_repo.py`
- `.github/workflows/ci.yml`
- `docs/runtime-delivery.md`
- `README.md`

The materializer is intended to copy a clean, explicit pinned base into a new isolated output, validate allowlisted file hashes/modes and the full candidate tree, and never install or activate a profile. The production pin is the native base above; synthetic Git tests use a distinct fixture schema. Exact identity:

```text
support base: d0894d0e6aadb4dc8ff5501a97c63988a3adcdee
support tree: 5a7ecb87ee81925f767430f300bc878fea6f0247
support patch SHA-256: e79ff0b00a25507cc5462f14f1729fa6dc82ef1666edc8607944e8d215d2958e
scoped review verdict: REJECT — delivery support only
verdict SHA-256: 2b583cd53e41cc7aecb5ae95bd1439b79a399b34e515694b363933130d3e669a
```

The separate support worktree's **37 public tests passed**, including 23 delivery tests; the parent reran them. The independent reviewer ran **18 real-Git observation/control probes**, including successful demonstrations of the defects below, and retained **two failing required-integrity assertions**. Observation-test passes are not acceptance approval. The 37-test count does not describe the unchanged public code on this documentation branch.

### DS-1 — untracked Python can spoof the pytest preflight (medium, blocking)

Candidate-relative locations: `scripts/runtime_delivery.py:193–215,229–238`.

After materializing a real synthetic Git fixture, add an untracked `pytest.py`. Verification accepts the expected receipt/index/tree, but Python run from the checkout imports the added file. A subprocess control using an interpreter wrapper with `-S` initially cannot import pytest and rejects execution; the fake module makes preflight succeed and permits a harmless tracked fixture runner to execute and return success. The fixture writes its observation outside the checkout; it does not invoke real PM, native CI or a provider.

**Required integrity question:** establish the managed interpreter's actual dependency and execution identity, and define allowed generated artifacts. Do not confuse successful import from a mutable checkout with a dependency installed in the managed environment.

### DS-2 — skip-worktree hides changed inherited source (medium, blocking)

Candidate-relative location: `scripts/runtime_delivery.py:207–214`.

Materialize a fixture containing a base-tracked, nonexported Python file. Apply `git update-index --skip-worktree` to that file, then change its contents. Git diff checks still exit zero and the verifier returns the expected tree, while Python imports the changed value. The exported-file tampering control is rejected by its explicit byte comparison.

**Required integrity question:** verify inherited executing bytes or reject the unsupported index state; tree/index equality and diff alone are insufficient. This probe explicitly mutates local Git metadata. It is a functional exact-checkout integrity gap, **not a same-UID sandbox escape**.

### Support review limits

Safety controls confirmed unchanged base bytes/modes on success and failure, isolated objects, existing-output preservation, rejection of wrong trees without success receipts, and path/symlink/FIFO/collision rejection. Those controls do not override DS-1/DS-2.

Repository hygiene and historical benchmark validation passed. Three proposed CI Bash blocks passed syntax checks only: no full workflow execution, PM provisioning, real native tests or actual public-pin materialization occurred. A reviewer-only exception-class identity error was corrected in the probe harness with its original evidence retained; product code and required-integrity assertions were not changed. The parent verified all six source hashes, the exact tree/patch and 23 review artifact hashes; it did not re-execute those independent probes.

## What the next reviewer should propose

1. A bounded reconciliation of B1–B3, with a precise owner/presentation/delivery lifetime contract and real RED→GREEN regressions. Preserve one-use admission, aggregate accounting, failure metadata, media order, privacy, mandatory controls and cached prefixes.
2. A separate, narrow DS-1/DS-2 verification correction: candidate execution identity, index-state handling, dependency preflight and explicitly permitted generated artifacts. Do not turn this into an OS sandbox claim.
3. A validity assessment for P1's adapter/result shape before deciding whether any native API work belongs in scope.
4. Required additional evidence and exact source/probe exports needed for an independent review. The local evidence bundle is labeled `bundle-20261103-195301`; it is not a public repository directory.
5. A concrete test matrix and stop conditions before any repair implementation. Bundle review-driven repairs remain **0 of 2 used**; no new repair round or contract was selected by this report.

Strong row/content references, genuine pending queues/bundles and on-disk artifacts are not globally memory/disk-bounded. Native SQL session-history routing is outside the budget-local ownership guarantee. No global session lease, durable replay ledger or exactly-once external-consumption guarantee is established.

**Still not done:** actual runtime/source delivery, public-pin materialization, delivery-path PM provisioning/native CI, composite approval, final payload/privacy review, paired multi-codebase evaluation, measured savings, installation, loaded-backend verification or activation. See [current status](../project-status.md), [rollout gates](../rollout.md), and the [evaluation proposal](../multi-codebase-evaluation.md). The historical off-only benchmark and earlier rejecting records remain unchanged.
