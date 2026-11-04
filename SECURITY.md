# Security policy

This repository ships the pure `cbg/` core, a Hermes plugin, an MCP stdio proxy, documentation and benchmark tooling. It does not ship the separate native runtime prototype. No supported runtime release or security audit is claimed. A passing test suite does not establish a security guarantee.

## Report privately

Do not put credentials, private transcripts, profile contents, session identifiers, or exploitable private details into public issues or PRs. Report privately through GitHub's [Report a vulnerability](https://github.com/seatrunk/context-budget-guard/security/advisories/new) form (private vulnerability reporting is enabled for this repository). If the form is unavailable, ask a maintainer for a private channel without posting the sensitive details.

Include the affected revision, a synthetic reproduction, expected boundary, and impact. Share the minimum evidence needed. Do not upload raw logs merely because an artifact is marked private. Remediation is coordinated privately before public disclosure.

## Response times

This project is maintained by one person, so these are best-effort targets, not a contractual SLA:

- Acknowledgement within **5 business days**.
- Initial assessment (severity, scope and next step) within **14 days**.

If you get no acknowledgement within that window, post a public issue that only asks for contact and contains no vulnerability details.

## Intended boundary

The proposed guard reduces model-visible tool text. It is not a sandbox, a total token/money cap, or protection against an attacker running under the same operating-system UID. Artifact access control and redaction still need independent verification. “Private” is a requirement, not proof of confidentiality.

The [known correctness blocker](docs/project-status.md) is not a claim of a security finding. Report any distinct security issue privately. See [design](docs/design.md) and [rollout](docs/rollout.md) for proposed safeguards.
