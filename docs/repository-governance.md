# Repository governance

This page specifies the required protection policy. Documentation and workflow files do not prove GitHub settings are active; maintainers must verify the effective rules before claiming enforcement.

## Pull requests and branches

Target protections require pull requests, one CODEOWNER approval, dismissal of stale approvals, approval of the most recent reviewable push by someone other than its pusher, resolved review conversations, and passing `repository-checks` and `pr-policy` checks. The intended CODEOWNER is `@seatrunk`.

Require linear history, prohibit force pushes and branch deletion, and allow squash merging only. The main-branch ruleset has no bypass actors. Maintainers cannot approve their own PRs: with only `@seatrunk` listed, owner-authored changes need another eligible CODEOWNER through deliberate maintainer onboarding. Do not silently relax review requirements or represent self-approval as independent approval.

The PR policy checks nonempty Summary, Verification, Benchmark impact, and Privacy and rollout sections plus the checked privacy declaration. These checks supplement human review; they do not prove a contribution is safe.

## Automation and reports

Use read-only `GITHUB_TOKEN` permissions and prevent Actions from creating or approving pull requests. Require approval for all external fork contributors. Allow only the checkout action and pin actions to full commit SHAs; the repository setting enforces pinning in addition to CI checks. Keep secret scanning, push protection, dependency alerts, and private vulnerability reporting enabled. Review untrusted changes before allowing execution; never expose secrets to contributor-controlled code.

Issue forms require version/context, synthetic reproduction, and privacy acknowledgment. Disable blank issues and direct sensitive reports to private security reporting. Forms guide the web UI; they do not prevent issues created through the API.

Maintainers must verify effective branch/ruleset settings, merge options, token permissions, fork approvals, labels, and private vulnerability reporting separately. Record any unavailable setting as a gap rather than silently weakening the policy.

See [contribution rules](../CONTRIBUTING.md), [security reporting](../SECURITY.md), and [rollout](rollout.md). Repository merge approval is not runtime activation approval.
