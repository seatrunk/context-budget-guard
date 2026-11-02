# Security policy

This repository ships documentation and benchmark tooling, not the separate runtime prototype. No supported runtime release or security audit is claimed. A passing test suite does not establish a security guarantee.

## Report privately

Do not put credentials, private transcripts, profile contents, session identifiers, or exploitable private details into public issues or PRs. Use the repository's **Security → Report a vulnerability** entry for private reporting; availability depends on repository settings. If that entry is unavailable, ask a maintainer for a private channel without posting the sensitive details.

Include the affected revision, a synthetic reproduction, expected boundary, and impact. Share the minimum evidence needed. Do not upload raw logs merely because an artifact is marked private. Maintainers should acknowledge and coordinate remediation privately before public disclosure; no response-time SLA is promised.

## Intended boundary

The proposed guard reduces model-visible tool text. It is not a sandbox, a total token/money cap, or protection against an attacker running under the same operating-system UID. Artifact access control and redaction still need independent verification. “Private” is a requirement, not proof of confidentiality.

The [known correctness blocker](docs/project-status.md) is not a claim of a security finding. Report any distinct security issue privately. See [design](docs/design.md) and [rollout](docs/rollout.md) for proposed safeguards.
