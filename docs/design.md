# Proposed design

These are intended properties of a separate experimental prototype, not guarantees implemented by this repository.

## Output policy

| Surface | Intended default |
| --- | --- |
| Complete file read | 350 effective LF lines |
| Partial file read | 150 effective LF lines |
| Final text | 16,384 UTF-8 bytes |

Tests must define effective LF-line counting explicitly, including empty input and trailing newlines. Byte limits must not cut a UTF-8 code point. Lines, bytes, and provider tokens are different units.

Mandatory control content may exceed normal limits. Preserve valid media and necessary error/exit metadata. Short necessary plugin/LSP notes must remain model-visible even after aggregate spill; that targeted regression has evidence in the latest candidate, but the full [approval contract still fails](project-status.md).

Oversized ordinary output should leave a useful preview and a recoverable artifact. Require private artifact handling and redact public evidence. Preserve failure semantics: reducing output must not turn a failed command into success.

## Policy and aggregate limits

The prototype intends cached profile/session policy, so changes must be tested across existing and fresh sessions rather than assumed immediate. This repository supplies no configuration switches.

Historical aggregate accounting is best effort. Notices add overhead; these limits do not cap the entire conversation, provider billing, or tool work. Same-UID attackers sit outside the authorization boundary. Artifact confidentiality needs verification beyond a filename or permission claim.

## Protected-note contract under review

Treat plugin/LSP metadata as a call-ID-owned suffix, outside the genuine untrusted wrapper; preserve media order and exactly-once delivery. Proposed inline budgets are up to 4,096 UTF-8 bytes per note bundle and 8,192 per batch, subject to the active policy and explicit tiny-budget fallback decisions. Oversized notes use one private/redacted archive bundle and one final visible pointer per batch, or a bounded failure marker when recovery cannot be supplied. These are intended properties, not guarantees of the rejected prototype.

Reserve the entire rendered contribution, not raw note length. Remeasure after framing and the single corrective aggregate pass, including multimodal JSON escaping. Explicit irreducible aggregate-overhead reporting must not become an ordinary per-result byte exemption. A one-use read receipt may not be replayed for another dispatch, but its approved output must not be silently revoked during unchanged-row finalization.

Literal delimiters in the note itself need a defined sanitization policy. Missing segmented rows and already-delivered control notes need distinct ownership lifetimes; neither silent loss nor indefinite bookkeeping should be accepted without review. The [cycle findings](reviews/2026-11-03-protected-notes.md) and issue tracker record the remaining implementation gaps.

## Review evidence

Cover exact limits and adjacent values, complete versus partial reads, multibyte text, mandatory exceptions, media, artifact recovery/privacy, error codes, cached policy, and historical aggregate spill. Inspect the actual model-visible result, not only stored output. See [status](project-status.md), [benchmarking](benchmarking.md), and [rollout](rollout.md).
