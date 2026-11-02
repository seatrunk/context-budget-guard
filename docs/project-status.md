# Project status

**November 2, 2026: experimental; activation BLOCKED.**

This repository contains operating guidance, specifications, and benchmark tooling. The local runtime prototype is separate, absent from this repository, and not upstream Hermes. There is no runtime installer here.

## Why blocked

Short necessary plugin/LSP notes may disappear from the model-visible result after aggregate spill even when they fit individually. Recoverability from an artifact does not satisfy visibility. The final static review rejected the candidate after two fix cycles; no activation, restart, or commit of that prototype followed. Track the remaining interaction in [issue #1](https://github.com/seatrunk/context-budget-guard/issues/1).

The separate integration reported 208 focused tests across 10 files plus 12 passing gates. Those tests are not this repository's CI and did not override the rejection. No security findings are claimed.

## Evidence identity

The rejected native-patch candidate was reviewed against:

```text
base revision: bf0203a794a07aac3ff764972ab9087baa4e4f4e
patch SHA-256: 8cef70e609a26d9460a08e3d01f9349e4a3903f92a474189ffd7853f36987f30
```

These identifiers describe separate local evidence, not a shipped artifact or a revision promised to exist in this repository. Any changed candidate requires fresh fingerprinting and independent review.

## Public evidence

The [baseline JSON](../benchmarks/results/2026-11-02-off-baseline.json) contains actual synthetic CLI observations with the guard off. There is no on-mode evidence and no measured savings claim. Read [benchmarking](benchmarking.md) for limitations and [rollout](rollout.md) for approval requirements.
