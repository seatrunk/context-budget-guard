# Contributing

Start with [project status](docs/project-status.md). This is a specification, operating-skill, and benchmark-tooling repository, not a runtime package. Keep proposals small enough to review without a private session dump.

## Pick a useful change

- Reproduce the missing plugin/LSP note after aggregate spill using synthetic text.
- Add boundary cases, clarify units, or improve evidence validation.
- Fix confusing docs without suggesting that activation is available.

Use the bug, feature, or benchmark issue form. Include a repository revision, relevant runtime version (or “not applicable”), expected versus observed behavior, and a minimal synthetic reproduction. Never paste real profile contents or private transcripts. See [SECURITY.md](SECURITY.md) for sensitive reports.

## Change and verify

For script changes, write a failing regression test first, then make it pass. Use only the Python standard library, Python 3.11+, and synthetic fixtures. Do not install dependencies for these checks.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_repo.py
python3 scripts/validate_benchmark.py benchmarks/results/2026-11-02-off-baseline.json
```

Check local links and report actual outcomes in the PR template. Describe benchmark impact even when it is “none.” Read [benchmarking](docs/benchmarking.md) before adding measurements. Do not rewrite an existing result to manufacture a comparison.

Preserve the [design invariants](docs/design.md): necessary notes, mandatory control exceptions, valid media, error/exit metadata, and privacy matter more than hitting a size target. Changing an invariant requires an explicit design discussion and regression evidence.

## Review boundaries

Keep the existing [MIT license](LICENSE) and copyright attribution. Follow the [code of conduct](CODE_OF_CONDUCT.md). A maintainer reviews contributions under the [governance policy](docs/repository-governance.md).

Passing CI is not activation approval. A runtime candidate needs independent review of its exact fingerprint, a resolved blocker, and the separate [rollout gates](docs/rollout.md). Do not publish private evidence, enable a prototype, or modify real profiles as part of routine contribution checks.
