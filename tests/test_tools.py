"""Behavior tests for the public fixture/measurement tools, not the runtime prototype."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def sample_report():
    return {
        "schema_version": 1, "recorded_on": "2026-11-02", "guard_enabled": False,
        "synthetic": True, "scope": "installed-cli", "samples_per_case": 1,
        "model": "synthetic-test-model", "provider": "synthetic-test-provider",
        "prototype": {"base_commit": "a" * 40, "patch_sha256": "b" * 64,
                      "review_status": "rejected", "desktop_loaded_provenance_verified": False},
        "billing": {"mode": "subscription_included", "actual_cost_usd": None},
        "measurements": [{"case": case, "wall_seconds": 1.0, "tool_content_utf8_bytes": 100,
                          "input_tokens": 100, "cache_read_tokens": 80, "output_tokens": 5,
                          "api_calls": 2, "tool_calls": 1}
                         for case in ("small", "over_lines", "over_result")],
        "limitations": ["Synthetic unit-test data, not a benchmark result."],
    }


class FixtureTests(unittest.TestCase):
    def call(self, output):
        return subprocess.run([sys.executable, str(ROOT / "scripts/generate_fixtures.py"),
                               "--output", str(output)], capture_output=True, text=True)

    def test_generates_exact_lines_and_nonzero_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "fixtures"
            result = self.call(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len((output / "small.txt").read_text().splitlines()), 12)
            self.assertEqual(len((output / "351-lines.txt").read_text().splitlines()), 351)
            command = subprocess.run([sys.executable, str(output / "oversized_failure.py")],
                                     capture_output=True)
            self.assertEqual(command.returncode, 7)
            self.assertGreater(len(command.stdout), 16384)
            if os.name == "posix":
                self.assertEqual(output.stat().st_mode & 0o777, 0o700)
                for path in output.iterdir():
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_unknown_sensitive_argument_does_not_echo_or_create_fixtures(self):
        private = "SYNTHETIC_PRIVATE_ARGUMENT_DO_NOT_ECHO"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "fixtures"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/generate_fixtures.py"),
                 "--output", str(output), "--unknown=" + private],
                capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])
            self.assertEqual(result.stdout, "")
            self.assertNotIn(private, result.stderr)
            self.assertEqual(result.stderr, "invalid arguments; use --help for usage\n")

    def test_refuses_existing_directory_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "fixtures"
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_text("keep")
            self.assertNotEqual(self.call(output).returncode, 0)
            self.assertEqual(sentinel.read_text(), "keep")
            self.assertEqual(list(output.iterdir()), [sentinel])

    @unittest.skipUnless(os.name == "posix", "symlink creation needs platform-specific permission")
    def test_refuses_symlink_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            target.mkdir()
            link = Path(tmp) / "link"
            link.symlink_to(target, target_is_directory=True)
            self.assertNotEqual(self.call(link).returncode, 0)
            self.assertEqual(list(target.iterdir()), [])


class MeasurementTests(unittest.TestCase):
    def validate(self, report):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(json.dumps(report))
            result = subprocess.run([sys.executable, str(ROOT / "scripts/validate_benchmark.py"),
                                     str(path)], capture_output=True, text=True)
            if result.returncode:
                self.assertTrue(result.stderr.startswith("invalid benchmark: "), result.stderr)
            return result

    @unittest.skipUnless(os.name == "posix", "FIFO input probe requires POSIX")
    def test_unknown_sensitive_argument_does_not_echo_or_open_input(self):
        private = "SYNTHETIC_PRIVATE_ARGUMENT_DO_NOT_ECHO"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            # Opening this FIFO for input would block: no writer is connected.
            os.mkfifo(path)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/validate_benchmark.py"),
                 str(path), "--unknown=" + private],
                capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(list(Path(tmp).iterdir()), [path])
            self.assertTrue(path.is_fifo())
            self.assertEqual(result.stdout, "")
            self.assertNotIn(private, result.stderr)
            self.assertEqual(result.stderr, "invalid arguments; use --help for usage\n")

    def test_accepts_off_only_report_without_savings_claim(self):
        result = self.validate(sample_report())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_nan_and_boolean_counters(self):
        for value in (float("nan"), True):
            with self.subTest(value=value):
                report = sample_report()
                report["measurements"][0]["input_tokens"] = value
                self.assertNotEqual(self.validate(report).returncode, 0)

    def test_rejects_cached_tokens_exceeding_input(self):
        report = sample_report()
        report["measurements"][0]["cache_read_tokens"] = 101
        self.assertNotEqual(self.validate(report).returncode, 0)

    def test_rejects_duplicate_cases(self):
        report = sample_report()
        report["measurements"][1] = copy.deepcopy(report["measurements"][0])
        self.assertNotEqual(self.validate(report).returncode, 0)

    def test_rejects_private_paths_without_echoing_them(self):
        report = sample_report()
        private = "/home/fictional-person/private-session"
        report["limitations"] = [private]
        result = self.validate(report)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(private, result.stdout + result.stderr)

    def test_rejects_credential_shaped_text(self):
        report = sample_report()
        report["limitations"] = ["ghp" + "_" + "A" * 40]
        self.assertNotEqual(self.validate(report).returncode, 0)

    def test_rejects_savings_claim_from_single_phase(self):
        report = sample_report()
        report["savings_percent"] = 99
        self.assertNotEqual(self.validate(report).returncode, 0)

    def test_rejects_enabled_report_without_approval(self):
        report = sample_report()
        report["guard_enabled"] = True
        self.assertNotEqual(self.validate(report).returncode, 0)

    def test_rejects_transcripts_in_measurement(self):
        report = sample_report()
        report["measurements"][0]["transcript"] = "unpublished"
        self.assertNotEqual(self.validate(report).returncode, 0)


if __name__ == "__main__":
    unittest.main()
