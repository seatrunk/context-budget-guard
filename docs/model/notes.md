# Note ownership model (Stage 1)

Implementation: [`cbg/notes.py`](../../cbg/notes.py). Property test: [`tests/invariants/test_notes_model.py`](../../tests/invariants/test_notes_model.py) (10,000 sequences, fixed seed).

## States and events

| From | Event | To | Note |
| --- | --- | --- | --- |
| (none) | `queue(note_id, owner_call_id, text)` | PENDING | the owner is the call ID, not the session |
| PENDING | `bind(call_id, ids, rendered_sha256)` | DELIVERED | only if `call_id == owner`; records the sha256 of what the model sees |
| DELIVERED | re-settlement of the same call ID | DELIVERED | `eligible()` keeps returning the note; the sha256 is updated (B2, B3) |
| DELIVERED | `complete_batch(ids)` | RETIRED | called only after the batch's last settlement |
| DELIVERED | `rotate_session()` | RETIRED | PENDING does **not** change: a note for a row in another segment is not lost |
| RETIRED | late re-settlement of the same call ID | RETIRED | a capped history (`retired_cap`) keeps the note visible |

## Invariants

- N1: a note appears in exactly one rendered row, its owner's.
- N2: the sha256 recorded on the owner is that of the final delivered render, including marker or withheld (B2).
- N3: a policy or aggregate failure in the second settlement does not lose a delivered note (B3, #4).
- N4: session rotation does not remove a PENDING note from eligibility, and the note is included in the cap measurement (B1).
- N5: bounded state: `state_size() <= pending + retired_cap` (#9).
- Cap: every non-control row has `rendered_bytes <= cap`, measured on the final render (F1/B1/#6).

## Assumption and limit

Call IDs are unique per call. If a runtime reuses a call ID, a retired note can reappear in a re-settlement; the property test reuses IDs on purpose and only requires N1 within a batch. There is no TLA+ model in this stage: the decision was a stdlib property test (no dev dependency).
