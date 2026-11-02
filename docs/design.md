# Proposed design

These are intended properties of a separate experimental prototype, not guarantees implemented by this repository.

## Output policy

| Surface | Intended default |
| --- | --- |
| Complete file read | 350 effective LF lines |
| Partial file read | 150 effective LF lines |
| Final text | 16,384 UTF-8 bytes |

Tests must define effective LF-line counting explicitly, including empty input and trailing newlines. Byte limits must not cut a UTF-8 code point. Lines, bytes, and provider tokens are different units.

Mandatory control content may exceed normal limits. Preserve valid media and necessary error/exit metadata. Short necessary plugin/LSP notes must remain model-visible even after aggregate spill; losing them is the current approval blocker.

Oversized ordinary output should leave a useful preview and a recoverable artifact. Require private artifact handling and redact public evidence. Preserve failure semantics: reducing output must not turn a failed command into success.

## Policy and aggregate limits

The prototype intends cached profile/session policy, so changes must be tested across existing and fresh sessions rather than assumed immediate. This repository supplies no configuration switches.

Historical aggregate accounting is best effort. Notices add overhead; these limits do not cap the entire conversation, provider billing, or tool work. Same-UID attackers sit outside the authorization boundary. Artifact confidentiality needs verification beyond a filename or permission claim.

## Review evidence

Cover exact limits and adjacent values, complete versus partial reads, multibyte text, mandatory exceptions, media, artifact recovery/privacy, error codes, cached policy, and historical aggregate spill. Inspect the actual model-visible result, not only stored output. See [status](project-status.md), [benchmarking](benchmarking.md), and [rollout](rollout.md).
