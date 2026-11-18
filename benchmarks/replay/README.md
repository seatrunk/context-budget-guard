# Offline replay (#11)

No model and no network. The synthetic fixtures are generated deterministically by `gen_fixtures.py`: Python, TypeScript, Rust, SQL, UTF-8, a JSON-escaped traceback, a mixed batch for water-filling, and the note/multimodal cases from issues #1, #6, #7 and #8.

```sh
python3 benchmarks/replay/gen_fixtures.py   # regenerates fixtures (deterministic)
python3 benchmarks/replay/replay.py         # writes results/offline-replay.json; exits 1 if the candidate fails any oracle
```

Arms:

- `none`: no budget.
- `historical`: character-based head preview; the note is dropped when its row is spilled; naive truncation of the largest row on aggregate overflow.
- `candidate`: the `spillway` core (`finalize_batch`).

The oracles are `bytes_le_cap`, `single_wrapper`, `exit_code`, `location`, `note_once_outside`, `media_preserved`, `min_bytes` and `aggregate_le_budget`. They check against each fixture's ground truth, not against Spillway's verifier, and they apply equally to every arm.

The current result (schema `spillway-offline-replay/2`) is 12 cases and 62 checks: candidate 62/62, `none` 46/62, `historical` 43/62. CI checks that a fresh run is byte-identical to `results/offline-replay.json`.

The `historical` arm is a documented emulation of the behavior described in the issues, not the private runtime. This replay does not measure tokens, cost or task success, and it does not support any savings claim for real tasks.
