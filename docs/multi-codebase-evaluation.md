# Multi-codebase evaluation protocol

**Proposal only. No replay harness or new benchmark results are delivered by this document.** Design: [#10](https://github.com/seatrunk/context-budget-guard/issues/10). Implementation/execution: [#11](https://github.com/seatrunk/context-budget-guard/issues/11).

## What is being evaluated?

Evaluate the separate runtime guard's admission, output previews, artifact recovery, and final model-visible tool messages. Do not call a smaller output a successful result if it loses the diagnostic, grant, note, media, or trust boundary needed by the task.

Conversation compaction is a separate layer: Hermes documents independent history-compression mechanisms.[1] A later experiment can study their interaction, but must not attribute summary quality, provider compression, or prompt-cache behavior solely to this operating skill. The skill is procedure; the runtime performs enforcement.

## Stage 0 — Correctness characterization now

Run only in an isolated, explicitly fingerprinted checkout. A rejected candidate may be measured to expose failures, never to promote it. Carry the three [reproduced blockers](reviews/2026-11-03-protected-notes.md) as mandatory failing oracles until actually fixed. Do not mask them with skips, expected-failure labels, or favorable averages.

### Proposed corpus

| Family | Workloads and information that must survive |
| --- | --- |
| Python | Tracebacks, import chains, parameterized tests, a diagnosis at the beginning/middle/end |
| TypeScript/JavaScript | Compiler diagnostics, nested JSON, diffs, test failures, cross-file symbol references |
| Rust | Compiler/cargo diagnostics, UTF-8 source and byte boundaries, multiline error context |
| SQL/configuration/logs | Migration failures, YAML/JSON, escaped status fields, long lines, repeated low-value progress |

Add string and multimodal representations, mandatory controls, ordinary calls, short/oversized plugin and LSP notices, valid/invalid receipts, and cached-policy changes. These are proposed workload families, **not** a claim that four real repositories have been benchmarked.

Start with deterministic synthetic fixtures. For later real source snapshots, record repository, commit, license/attribution, fixture-generation command and SHA-256. Do not copy private application code or transcripts without explicit authorization and privacy review. Source excerpts alone are not representative end-to-end tasks.

### Paired comparison arms

1. Unbudgeted reference output, retained only inside the controlled replay.
2. Historical spill behavior on its pinned revision and configuration.
3. Exact candidate guard on a pinned revision and configuration.

Use identical input bytes, call order, tool outcomes, budgets and fixture seeds. Invoke the actual runtime through an explicitly supplied isolated adapter; do not copy its logic into a toy compressor. No production configuration changes or model calls are needed for deterministic replay.

### Independent oracles

- Necessary error, exit code, file/symbol reference and short note remain visible or receive the explicitly permitted bounded marker.
- Exactly-once notice delivery occurs outside the genuine untrusted wrapper, including a literal delimiter **in the note**.
- Media and order survive; corrective multimodal results count escaped JSON and separators in the complete rendered byte measurement.
- An approved receipt survives actual admission → dispatch → commit → finalization without becoming reusable. Compare note/no-note controls.
- Complete/partial read limits and ordinary final ceilings hold. Keep explicitly defined irreducible aggregate-overhead conditions separate from per-result violations.
- Private/redacted artifacts are recoverable; an artifact alone is not a substitute for model-visible required metadata.
- Tool dispatch count remains one even when persistence or policy fails; cached historical prefixes are unchanged.
- Repeated batches, control-only rows, missing segments and session rotation obey a documented ownership lifetime.

Use ground-truth fixture labels and assertions independent of the guard's own helper functions where possible. Perturb the retained fact's position and output size; do not rely only on the cases used to write the fix.

## Metrics and promotion rules

| Dimension | Record |
| --- | --- |
| Correctness | Per-oracle pass/fail, missing required facts, duplicate/misplaced notes, status/media corruption, receipt regressions |
| Budget | Actual final UTF-8 bytes using the runtime representation; aggregate characters and any explicit unsatisfiable condition separately |
| Recovery | Artifact read attempts, recovered required facts, follow-up tool calls, no-redispatch failures |
| Overhead | Guard-only elapsed time separately from fixture generation, artifact I/O and whole-process time |
| Context | Provider/tokenizer identity when used; actual input/output/cached tokens only when available, otherwise unknown |
| Cost | All measured model/tool/recovery calls; billed-usage provenance or unknown, not bytes converted into money |

Correctness is a veto, not an average: a ceiling violation, necessary-note loss, changed failure semantics or unauthorized receipt reuse blocks readiness even if output shrinks. Publish every failed case. A summary may group results by family and representation, but cannot hide them in one compression-ratio score.

For deterministic replay, repeat to check output stability; repeated identical runs do not create independent semantic evidence. For timing, predeclare repetitions, warm-up policy, run order and machine/runtime versions; publish individual samples and dispersion. Keep cold and warm/cache conditions separate. No percentage-savings target is asserted before data exists.

## Stage 1 — Task-based evaluation after correctness passes

With separate explicit model/provider, repository and spending approval, pair real coding tasks and their tests across baseline/candidate sessions. Freeze tool/model versions, initial context and cache conditions; count artifact recovery and retries in total usage. Score resolved tasks and new regressions, not only smaller prompts or an LLM judge's opinion.

SWE-bench is a methodological reference: its harness evaluates generated patches using repository tests.[2] This proposal has **not** run SWE-bench, does not inherit its scores, and is not a substitute for the rejected guard's own regression gate. Choose or author appropriately licensed tasks before budgeting a model-based experiment.

## Stage 2 — Compaction interaction and rollout are separate gates

Only after a reviewed guard candidate and task-based evidence should an approved experiment compare guard off/on with conversation compaction held constant, then vary compaction deliberately. Record each layer's version, trigger and outcome. Do not mutate cached past messages to manufacture a comparison.

No benchmark authorizes a shared-backend restart, profile enablement or production canary. Follow [rollout](rollout.md); resolve the current [status blockers](project-status.md). The historical [off-only data](../benchmarks/results/2026-11-02-off-baseline.json) remains off-only.

## Proposed result record

A future replay schema should include corpus/fixture hashes, runtime and configuration fingerprints, comparison arm, expected facts, final measured units, per-oracle outcomes, recovery/call counts, timing samples and limitations. It needs its own validator and harness tests. The existing provider-baseline validator does not validate this proposed schema.

## Sources

[1] https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching — Hermes context compression and caching
[2] https://www.swebench.com/SWE-bench/guides/evaluation — SWE-bench evaluation guide
