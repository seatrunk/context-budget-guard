# Rollout gates

Activation is currently **BLOCKED**. This page is a future approval checklist, not activation instructions. This repository has no runtime to enable.

Before any separate runtime trial:

- Resolve the missing short plugin/LSP note after aggregate spill. Add a synthetic regression and inspect model-visible output.
- Verify every [design invariant](design.md), including mandatory exceptions, valid media, failure metadata, artifact privacy, and cached profile/session behavior.
- Record the exact base revision and patch SHA-256. Obtain independent review of that exact candidate; test totals alone cannot grant approval.
- Agree on explicit human authorization, isolated synthetic trial scope, stop conditions, and a tested rollback to the prior configuration. Do not use private live transcripts as fixtures.
- Re-run applicable integration checks on the candidate. Distinguish those checks from this repository's CI and record unresolved limitations.

Stop if necessary notes disappear, artifacts expose private content, media/control content breaks, failure semantics change, or the reviewed fingerprint differs. Revert the trial through the agreed rollback and verify the resulting state. A fresh patch requires fresh review.

Do not restart services, enable profiles, or claim deployment from this checklist. See [project status](project-status.md) for the rejected candidate and [benchmarking](benchmarking.md) for what the off-only evidence can establish.
