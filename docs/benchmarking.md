# Benchmarking

## Published off-only baseline

[Raw public data](../benchmarks/results/2026-11-02-off-baseline.json) records actual synthetic CLI runs on November 2, 2026 using `gpt-6.1-sol` through `openai-codex`. Each case used a fresh session, one tool call, and two API calls. Each has **n=1**.

| Case | Stored API UTF-8 bytes | Wall seconds | Input tokens | Cached input tokens | Output tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Small | 372 | 11.887317224 | 38,877 | 7,680 | 69 |
| 351 lines | 7,394 | 24.432428351 | 41,631 | 23,168 | 71 |
| Oversized terminal | 32,162 | 15.156795696 | 44,301 | 43,904 | 90 |

The terminal case intentionally exited with code 7; that failure was preserved. All runs had the guard off. There is no on-mode comparator and no evidence of savings.

Wall time includes startup, inference, and tools; it does not isolate guard overhead. Cached tokens are already included in input tokens: do not add them again. Stored API bytes are not token counts. Actual USD cost is unknown; the subscription-included execution does not establish zero marginal or billed cost. Three single observations cannot support statistical conclusions.

## Reproduce repository checks

Use Python 3.11+ from the repository root; no dependencies need installing.

```sh
python3 scripts/generate_fixtures.py --output benchmark-fixtures
python3 -m unittest discover -s tests -v
python3 scripts/check_repo.py
python3 scripts/validate_benchmark.py benchmarks/results/2026-11-02-off-baseline.json
```

Fixture generation refuses an existing output path. Choose a new path; do not delete an existing directory just to make the command pass. Generating fixtures and validating JSON do not replay provider calls or recreate measured timings.

## Submit useful evidence

1. Use synthetic inputs only. Include minimal reproduction and expected/model-visible output without private profiles, transcripts, paths, session identifiers, credentials, or raw logs.
2. Record date, repository revision, runtime candidate fingerprint when applicable, model/provider, mode, fixture definition, repetitions, and session/cache conditions. Distinguish actual observations from simulated projections.
3. Report bytes, tokens, wall-time scope, tool/API call counts, failure codes, and cost provenance with explicit units and unknowns. Preserve failed runs.
4. For a later approved comparison, use matched off/on workloads, repeated runs, and disclosed cache/order controls. Do not collect on-mode data by bypassing the [rollout gates](rollout.md).
5. Validate the result schema and request independent review. Keep historical data intact and label corrected or replacement results explicitly.

Use the benchmark issue form for proposals. Public benchmark files are evidence, not a release certificate. The validator's private-path and credential-pattern checks are a limited sanity check, not DLP; manually inspect every public artifact. The repository checker verifies local link targets and action pins, not external URLs, anchors, or complete YAML schemas.
