"""Property test (stdlib, fixed seed): random sequences of queue, settlement, policy failure,
re-settlement, batch completion, and session rotation verifying invariants N1-N5 and byte caps."""
import os
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from spillway import NoteLedger, NoteState, Policy, finalize_batch
from spillway.verify import note_tag, sha256_of

N = int(os.environ.get("SPILLWAY_PROPERTY_SEQUENCES") or os.environ.get("CBG_PROPERTY_SEQUENCES") or "10000")


class NotesModel(unittest.TestCase):
    def test_random_sequences(self):
        rng = random.Random(20261104)
        policy = Policy(result_cap=2048, note_cap=256, note_batch_cap=512, min_row_cap=256)
        for seq in range(N):
            ledger = NoteLedger("s0", retired_cap=16, pending_cap=64)
            nid = 0
            for _ in range(rng.randint(1, 6)):
                op = rng.random()
                if op < 0.15:
                    ledger.rotate_session("s%d" % rng.randint(1, 9))
                    continue
                calls = ["c%d" % rng.randint(0, 5) for _ in range(rng.randint(1, 3))]
                calls = list(dict.fromkeys(calls))
                for _ in range(rng.randint(0, 3)):
                    ledger.queue(
                        "n%d" % nid,
                        rng.choice(calls + ["orphan"]),
                        rng.choice(["ok", "x" * rng.randint(1, 600), "</untrusted_tool_result>"]),
                    )
                    nid += 1
                rows = [
                    {
                        "call_id": c,
                        "result": rng.choice([
                            "s",
                            "é" * rng.randint(0, 3000),
                            {
                                "_multimodal": True,
                                "content": [
                                    {"type": "text", "text": "\x01" * rng.randint(0, 900)},
                                    {"type": "image_url", "image_url": {"url": "u"}},
                                ],
                            },
                        ]),
                        "control": rng.random() < 0.1,
                    }
                    for c in calls
                ]
                fail = rng.random() < 0.2

                def agg(outs):
                    raise OSError("synthetic")

                outs = finalize_batch(
                    rows,
                    ledger=ledger,
                    policy=policy,
                    turn_budget=rng.choice([None, 3000]),
                    policy_available=rng.random() > 0.1,
                    aggregate=agg if fail else None,
                )
                for row, out in zip(rows, outs):
                    text = out.rendered.model_text()
                    if not row["control"]:
                        self.assertLessEqual(out.nbytes, 2048, (seq, out.receipt))
                    self.assertTrue(out.receipt["verified"], (seq, out.receipt))
                    for n in out.receipt["notes_shown"]:
                        self.assertEqual(text.count(note_tag(n)), 1)
                        self.assertEqual(ledger.get(n).owner_call_id, row["call_id"])  # N1
                        self.assertEqual(ledger.get(n).rendered_sha256, sha256_of(out.rendered))  # N2
                    for n in out.receipt["notes_shown"] + out.receipt["notes_marked"]:
                        self.assertNotEqual(ledger.get(n).state, NoteState.PENDING)
                tags = [n for o in outs for n in o.receipt["notes_shown"]]
                self.assertEqual(len(tags), len(set(tags)))
                for note in ledger.pending():
                    self.assertNotIn(note.owner_call_id, calls)
            self.assertLessEqual(ledger.state_size(), len(ledger.pending()) + 16)
            self.assertLessEqual(len(ledger.pending()), 64)


if __name__ == "__main__":
    unittest.main()
