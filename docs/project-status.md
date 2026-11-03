# Project status

**November 3, 2026: experimental; activation BLOCKED. Latest independent verdict: REJECT.**

This repository contains operating guidance, specifications, and benchmark tooling. The separate local runtime prototype is absent here and is not upstream Hermes. There is no runtime installer here.

## Latest cycle

The protected-note implementation preserves the primary short plugin/LSP note in its targeted aggregate-spill regression, but the exact candidate still fails the full acceptance contract. Independent review reproduced:

- [#6: corrective multimodal byte overflow](https://github.com/seatrunk/context-budget-guard/issues/6): 17,108 measured bytes against the ordinary 16,384-byte ceiling.
- [#7: receipt regression at finalization](https://github.com/seatrunk/context-budget-guard/issues/7): a note-bearing approved read loses its larger allowance after commit consumes the one-use receipt.
- [#8: literal delimiters in notes](https://github.com/seatrunk/context-budget-guard/issues/8): a queued literal closing tag remains unsanitized in string and multimodal results.

[#9](https://github.com/seatrunk/context-budget-guard/issues/9) separately tracks the lifetime of already-delivered control-note ownership. It is an observed lifecycle concern, not an additional proven violation of the plan's deliberate pending-control choice.

Original issues [#1](https://github.com/seatrunk/context-budget-guard/issues/1), [#3](https://github.com/seatrunk/context-budget-guard/issues/3), [#4](https://github.com/seatrunk/context-budget-guard/issues/4), and [#5](https://github.com/seatrunk/context-budget-guard/issues/5) remain unresolved: targeted successes do not override the rejected exact candidate.

## Evidence identity and limits

```text
base revision: bf0203a794a07aac3ff764972ab9087baa4e4f4e
predecessor patch SHA-256: 8cef70e609a26d9460a08e3d01f9349e4a3903f92a474189ffd7853f36987f30
latest patch SHA-256: af23cfed60b6e85e88ed4e2f63ec89872c6fb598f63f2e9bde879bc9262ac2f6
latest index tree: eed6890e06d0eaee9c3b26dad17ed7b5f182a373
```

The implementer recorded 641 passes and one existing Windows-only skip across 17 files, plus 12 staged checks. The parent independently reproduced 274 affected passes and one skip. These sets overlap: **do not add them together**. The reviewer reran 21 permanent contracts successfully, then retained an eight-case adversarial probe with three passes and five failures. Four failing cases substantiate three blockers; the fifth audits ownership retention.

Read the [cycle report](reviews/2026-11-03-protected-notes.md) and its [sanitized machine-readable record](reviews/2026-11-03-protected-notes.json). Native patches, private logs, and probes are not distributed here; this summary is not a self-contained reproduction package. Public repository CI checks tooling and documentation, not those native integration claims.

The agreed implementation/review allowance was exhausted. Work stopped after rejection, without a repair loop, live application, profile change, or service restart. Another runtime repair cycle needs explicit authorization and fresh review.

## Evaluation next

The [multi-codebase evaluation protocol](multi-codebase-evaluation.md) is a proposal, not an implemented replay harness or measured comparison. [#10](https://github.com/seatrunk/context-budget-guard/issues/10) tracks that specification; [#11](https://github.com/seatrunk/context-budget-guard/issues/11) tracks future implementation and execution. Offline characterization can expose known failures; it cannot grant approval to a failing candidate.

The historical [off-only baseline](../benchmarks/results/2026-11-02-off-baseline.json) remains unchanged. There is still no published on-mode comparison, measured savings, production rollout, or verified live-backend enforcement. See [benchmarking](benchmarking.md) and [rollout](rollout.md).
