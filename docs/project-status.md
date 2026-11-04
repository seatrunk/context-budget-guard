# Project status

**November 4, 2026 UTC snapshot: combined native acceptance BLOCKED; separate delivery-support review REJECTED; activation BLOCKED.**

This repository contains operating guidance, specifications, and benchmark tooling. The separate local runtime prototype is absent here and is not upstream Hermes. There is no runtime installer here.

## Current combined assessment and review handoff

The [full findings and reviewer brief](reviews/2026-11-04-combined-assessment.md) and [sanitized JSON](reviews/2026-11-04-combined-assessment.json) supersede the historical cycle below as the current progress snapshot. #6–#9 each reached independent scoped approval in separate frozen checkpoints, but the combined candidate does not pass acceptance. Issues remain open for actual delivery.

- **Composite gate:** 649 passed, 13 failed, one existing Windows-only skip across 30 files; all 12 staged checks passed. Seven failures concern rotated-session byte ceilings, withheld-note ownership, and SECOND settlement under persistent dependency failure. Six synthetic read/media probes stop at an existing result-type guardrail before budget commit and are separately unsupported/unverified, not established new budget regressions.
- **Parent reproduction:** one control passed and all seven product-acceptance failures reproduced in two files. These overlap the full gate and are not an extra unique total.
- **Separate delivery support:** implemented in a local worktree, then **REJECTED** by scoped independent review. Its 37 existing tests passed, but two RED integrity assertions show untracked Python import shadowing and index-flag-hidden inherited changes. Those 37 tests and the six-file support implementation are not included in this documentation-only publication.
- **Exact composite:** tree `e35b5b0fd06cdaaa36bf5ac5adfa24b757f4be84`; full patch SHA-256 `a154f4438caece252141b4a1698abb7a2e0800139e8e9ae41e6fca3f372685f2`. The report records predecessor/support identities and all attribution limits.
- **Stopped:** no new ownership/delivery contract selected, repair round started, composite approval, runtime payload export, actual native CI, installation or activation. Bundle review-driven repairs remain 0 of 2 used. This handoff asks another reviewer to propose bounded modifications; it is not permission to implement or enable them.

The separately retained source, full patches, probes and raw logs are absent from this public repository. Fingerprints identify local snapshots, not remotely fetchable objects. Public CI validates the unchanged public tooling and published documentation; it cannot reproduce the absent runtime or delivery-support candidate.

## Historical protected-note cycle — November 3

The protected-note implementation preserves the primary short plugin/LSP note in its targeted aggregate-spill regression, but the exact candidate still fails the full acceptance contract. Independent review reproduced:

- [#6: corrective multimodal byte overflow](https://github.com/seatrunk/context-budget-guard/issues/6): the intended corrective-fallback probe, with deliberately non-progressing aggregate enforcement and a feasible 200,000-character aggregate budget, returned 17,108 measured bytes against the ordinary 16,384-byte ceiling. The string control passed; see the [F1 reproduction scope](reviews/2026-11-03-protected-notes.md#f1--corrective-multimodal-compaction-exceeds-the-ceiling-p1).
- [#7: unnecessary read re-limit at finalization](https://github.com/seatrunk/context-budget-guard/issues/7): finalization re-limits an already-approved note-bearing read after its one-use receipt was consumed. The approved output should survive; the receipt must not be retained or replayed.
- [#8: literal delimiters in notes](https://github.com/seatrunk/context-budget-guard/issues/8): a queued literal closing tag remains unsanitized in string and multimodal results.

[#9](https://github.com/seatrunk/context-budget-guard/issues/9) separately tracks the lifetime of already-delivered control-note ownership. It is an observed lifecycle concern, not an additional proven violation of the plan's deliberate pending-control choice.

Original issues [#1](https://github.com/seatrunk/context-budget-guard/issues/1), [#3](https://github.com/seatrunk/context-budget-guard/issues/3), [#4](https://github.com/seatrunk/context-budget-guard/issues/4), and [#5](https://github.com/seatrunk/context-budget-guard/issues/5) remain unresolved: targeted successes do not override the rejected exact candidate.

## Historical evidence identity and limits

```text
base revision: bf0203a794a07aac3ff764972ab9087baa4e4f4e
predecessor patch SHA-256: 8cef70e609a26d9460a08e3d01f9349e4a3903f92a474189ffd7853f36987f30
latest patch SHA-256: af23cfed60b6e85e88ed4e2f63ec89872c6fb598f63f2e9bde879bc9262ac2f6
latest index tree: eed6890e06d0eaee9c3b26dad17ed7b5f182a373
```

The implementer recorded 641 passes and one existing Windows-only skip across 17 files, plus 12 staged checks. The parent independently reproduced 274 affected passes and one skip. These sets overlap: **do not add them together**. The reviewer reran 21 permanent contracts successfully, then retained an eight-case adversarial probe with three passes and five failures. Four failing cases substantiate three blockers; the fifth audits ownership retention.

Read the [cycle report](reviews/2026-11-03-protected-notes.md) and its [sanitized machine-readable record](reviews/2026-11-03-protected-notes.json). Native patches, private logs, and probes are not distributed here; this summary is not a self-contained reproduction package. Public repository CI checks tooling and documentation, not those native integration claims.

That historical cycle's agreed implementation/review allowance was exhausted and it stopped after rejection. Subsequently authorized #6–#9 repairs reached scoped approvals, but the current combined assessment remains blocked as documented above. Neither the historical rejection nor later approvals authorize live application, profile changes or service restarts.

## Evaluation next

The [multi-codebase evaluation protocol](multi-codebase-evaluation.md) is a proposal, not an implemented replay harness or measured comparison. [#10](https://github.com/seatrunk/context-budget-guard/issues/10) tracks that specification; [#11](https://github.com/seatrunk/context-budget-guard/issues/11) tracks future implementation and execution. Offline characterization can expose known failures; it cannot grant approval to a failing candidate.

The historical [off-only baseline](../benchmarks/results/2026-11-02-off-baseline.json) remains unchanged. There is still no published on-mode comparison, measured savings, production rollout, or verified live-backend enforcement. See [benchmarking](benchmarking.md) and [rollout](rollout.md).
