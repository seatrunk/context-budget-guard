# Protected-note cycle: passing suites, rejecting review

**Review date: November 3, 2026. Verdict: REJECT. Activation remains BLOCKED.**

This report summarizes a separate, isolated native candidate. This repository does not include or install that runtime. It publishes a privacy-reviewed evidence summary, not the native patch, complete probe source, or private logs. Those omissions limit independent reproduction from this repository alone.

## What changed in the isolated candidate

The cycle introduced call-ID-owned note suffixes across commit and aggregate finalization; full rendered-suffix reservation; commit/finalization inline caps; a shared private/redacted note archive; filtered-row identity handling; and a corrective aggregate pass. It added permanent tests and native developer documentation.

Targeted coverage supports recovery of the original short plugin/LSP aggregate-spill case, ordinary note placement outside wrappers, media preservation, disabled behavior, archive privacy, and cached-prefix preservation. This is **partial evidence**, not acceptance of every boundary or a claim that the implementation is ready.

## Fingerprint

| Identifier | Value |
| --- | --- |
| Base commit | `bf0203a794a07aac3ff764972ab9087baa4e4f4e` |
| Predecessor patch SHA-256 | `8cef70e609a26d9460a08e3d01f9349e4a3903f92a474189ffd7853f36987f30` |
| Reviewed patch SHA-256 | `af23cfed60b6e85e88ed4e2f63ec89872c6fb598f63f2e9bde879bc9262ac2f6` |
| Reviewed index tree | `eed6890e06d0eaee9c3b26dad17ed7b5f182a373` |
| Staged files | 21 |

The parent verified the patch and all manifest entries. The reviewer reverified the unchanged fingerprint at review completion. The live predecessor and unrelated edits were preserved.

## Verification, separated by source

| Evidence owner | Scope | Actual recorded outcome |
| --- | --- | --- |
| Implementer | Required 11 files | 253 passed, 1 existing Windows-only skip |
| Implementer | Additional note-contract file | 21 passed |
| Implementer | Adjacent 5 files | 367 passed |
| Implementer | Staged repository gates | 12 passed |
| Parent | Independent affected 12-file run | 274 passed, 1 existing skip |
| Independent reviewer | Permanent note contracts | 21 passed |
| Independent reviewer | Final retained adversarial probe | 3 passed, 5 failed |

The implementer's total is 641 passes across 17 files. Parent and reviewer reruns overlap those tests; they are not extra unique coverage to add to that total. Exploratory probes with corrected preconditions are not substituted for the final retained result. Public repository CI is a different suite and cannot reproduce these native results without the absent runtime.

## Reproduced blockers

### F1 — Corrective multimodal compaction exceeds the ceiling (P1)

Separate-candidate path: `agent/context_budget_finalization.py`, corrective compaction and finalization.

The fallback wraps the body with the full 16,384-byte allowance, then appends the note without remeasuring complete rendered bytes. A bounded 4,015-byte note, an image, exit code 7, and eight admitted status fields containing 255 escaped control characters each produced **17,108 measured bytes**. A deliberately non-progressing aggregate implementation exercises the intended corrective fallback; the aggregate budget itself is feasible. The string control passed.

The permanent corrective test used ASCII status values and missed multimodal JSON-escaping overhead. Track the fix in [#6](https://github.com/seatrunk/context-budget-guard/issues/6). This also prevents closing the ceiling-related acceptance criteria in #1, #3, and #4.

### F2 — Finalization loses an approved read ceiling (P2)

Separate-candidate paths: `agent/context_budget_note_policy.py` and `agent/context_budget_notes.py`.

A real sequential read with a **65,536-byte receipt** committed its complete synthetic 351-line output plus note at **21,448 characters**. Finalization under a nonbinding **200,000-character aggregate budget** replaced it with a **1,494-character archive notice**. The otherwise identical no-note control retained the complete body. The one-use receipt had already been consumed at commit, but note preparation re-limited the unchanged row.

The permanent receipt-with-note test exercised limiter consumption without finalization. Track the full-lifecycle regression and fix in [#7](https://github.com/seatrunk/context-budget-guard/issues/7).

### F3 — Delimiters inside actual notes remain literal (P2)

Separate-candidate path: `agent/context_budget_note_policy.py`, note redaction/normalization.

A queued note containing `</untrusted_tool_result>` remained literal after real commit/finalization, producing two closing delimiters for both strings and multimodal content. The permanent XML test put the literal in the **tool body**, not in the **note**. It therefore tested a different input boundary.

Track sanitization and correctly sourced fixtures in [#8](https://github.com/seatrunk/context-budget-guard/issues/8). This is a framing/acceptance defect, not a demonstrated operating-system boundary escape or a security advisory.

## Nonblocking observation and ruled-out suspicion

Ten separately finalized control-only rows retained ten delivered ownership entries. [#9](https://github.com/seatrunk/context-budget-guard/issues/9) requests a bounded lifecycle decision without dropping genuinely pending segmented notes. Review did not classify this deliberate ownership choice as another proven plan violation.

A separate suspicion that a shortened fallback marker exceeded the cap was not reproduced with the sampled legal archive paths. It is not counted as a blocker. The confirmed F1 corrective path is distinct.

## Self-improvement adopted

The [operating skill](../../SKILL.md) now requires evidence from complete lifecycles, full rendered corrective output, and the exact input origin named by an acceptance criterion. Test names and a large green total are not coverage proofs. The local review workflow also records these reusable lessons; no native runtime self-repair or rollout is implied.

The agreed single implementation cycle and fresh review ended in rejection. No further repair, commit of native code, live application, runtime enablement, service restart, or model/provider change followed. Original correctness issues stay open. The [evaluation protocol](../multi-codebase-evaluation.md) can guide isolated characterization, not bypass this rejection.
