# Rollout gates

Production activation is currently **BLOCKED**. Since PR #14 this repository ships the `cbg/` core plus a Hermes plugin and an MCP proxy that default to `shadow` (receipts only, output unchanged). Installing them in shadow mode is observation, not activation. Their `enforce` mode and the private native patch both stay behind the gates below.

Before any `enforce` trial or native runtime trial:

- Run the real-task benchmark from the README: shadow receipts first, then paired A/B enforce runs, with no fidelity-oracle regressions.
- Pass the Etapa 2 native combined gate on the exact native candidate, then independent review. Etapa 1 core tests and the offline replay (candidate 39/39) do not replace it.

- Resolve the missing short plugin/LSP note after aggregate spill. Add a synthetic regression and inspect model-visible output.
- Resolve the latest [combined assessment blockers](reviews/2026-11-04-combined-assessment.md): rotated-session re-budgeting, exact ownership of withheld notice presentations, and repeated settlement while dependencies remain failed. Individual #6–#9 approvals do not establish compatibility.
- Repair and independently re-review the separate delivery-support verifier: untracked import shadowing and index-flag-hidden inherited changes currently defeat its intended candidate-identity checks. Validate the actual exported payload, public-pin materialization, managed PM setup and native CI; none is established by documentation/tooling CI.
- Verify every [design invariant](design.md), including mandatory exceptions, valid media, failure metadata, artifact privacy, and cached profile/session behavior.
- Record the exact base revision and patch SHA-256. Obtain independent review of that exact candidate; test totals alone cannot grant approval.
- Agree on explicit human authorization, isolated synthetic trial scope, stop conditions, and a tested rollback to the prior configuration. Do not use private live transcripts as fixtures.
- Re-run applicable integration checks on the candidate. Distinguish those checks from this repository's CI and record unresolved limitations.

Stop if necessary notes disappear, artifacts expose private content, media/control content breaks, failure semantics change, or the reviewed fingerprint differs. Revert the trial through the agreed rollback and verify the resulting state. A fresh patch requires fresh review.

Offline, no-provider replay in an approved isolated checkout may characterize a rejected candidate's failures. It is not a live trial or readiness approval. Task-based model experiments, conversation-compaction interactions, paid usage, and any production canary require separate scope and authorization. See the proposed [evaluation protocol](multi-codebase-evaluation.md).

Do not restart services, enable profiles, or claim deployment from this checklist. See [project status](project-status.md) for Etapa 1 and the rejected native candidate and [benchmarking](benchmarking.md) for what the off-only evidence can establish.
