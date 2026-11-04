"""Testes permanentes do harness de replay offline (#11)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks/replay"))
import replay  # noqa: E402


class Replay(unittest.TestCase):
    def test_candidate_green_and_known_baseline_failures_stay_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "r.json"
            self.assertEqual(replay.main(["--out", str(out)]), 0)
            report = json.loads(out.read_text())
            arms = report["arms"]
            self.assertEqual(report["model_calls"], 0)
            self.assertEqual(arms["candidate"]["failures"], [])
            self.assertIn("issue1_aggregate_spill_note/a-1:note_once_outside", arms["historical"]["failures"])
            self.assertIn("issue8_delimiter_note/d-1:single_wrapper", arms["none"]["failures"])
            self.assertLess(arms["candidate"]["bytes_total"], arms["none"]["bytes_total"])

    def test_deterministic_and_matches_committed_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "r.json"
            replay.main(["--out", str(out)])
            committed = ROOT / "benchmarks/replay/results/offline-replay.json"
            self.assertEqual(out.read_text(), committed.read_text())

    def test_fixtures_are_synthetic_and_clean(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from validate_benchmark import PRIVATE
        for path in (ROOT / "benchmarks/replay/fixtures").glob("*.json"):
            self.assertIsNone(PRIVATE.search(path.read_text()), path.name)


if __name__ == "__main__":
    unittest.main()
