"""Tests for ArtifactStore security/retention and the unified Spillway CLI."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from spillway import cli
from spillway.artifacts import ArtifactStore


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ArtifactStoreTests(unittest.TestCase):
    def test_prunes_oldest_by_count_and_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp), max_artifacts=3, max_bytes=2500)
            shas = []
            for i in range(5):
                payload = f"item-{i}-" + ("x" * 700)
                h = sha(payload)
                shas.append(h)
                store.write_artifact(h, payload)
                time.sleep(0.002)
            remaining = {p.stem for p in store.artifacts_dir.glob("*.txt")}
            self.assertLessEqual(len(remaining), 3)
            self.assertIn(shas[-1], remaining)
            total_bytes = sum(p.stat().st_size for p in store.artifacts_dir.glob("*.txt"))
            self.assertLessEqual(total_bytes, 2500)

    @unittest.skipUnless(os.name == "posix", "POSIX permissions and symlinks")
    def test_tightens_existing_0644_log_and_rejects_symlink_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "logs"
            root.mkdir(mode=0o755)
            receipts = root / "receipts.jsonl"
            receipts.write_text("", encoding="utf-8")
            os.chmod(receipts, 0o644)

            store = ArtifactStore(root)
            store.append_jsonl("receipts.jsonl", '{"ok":true}')
            self.assertEqual(receipts.stat().st_mode & 0o777, 0o600)
            self.assertEqual(root.stat().st_mode & 0o777, 0o700)

            # Symlink inside artifacts/ must be refused on read_slice
            store.artifacts_dir.mkdir(exist_ok=True, mode=0o700)
            secret = Path(tmp) / "secret.txt"
            secret.write_text("top-secret", encoding="utf-8")
            fake_sha = "a" * 64
            (store.artifacts_dir / (fake_sha + ".txt")).symlink_to(secret)
            with self.assertRaises(OSError):
                store.read_slice(fake_sha, 0, 100)


    def test_read_slice_streams_window_and_paginates_multibyte_losslessly(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp))
            payload = "a" * 1000 + "é漢🙂" * 300 + "tail"
            h = sha(payload)
            store.write_artifact(h, payload)
            total = len(payload.encode("utf-8"))
            for limit in (1, 2, 3, 5, 64, 4096):
                parts, offset, steps = [], 0, 0
                while True:
                    info = store.read_slice(h, offset, limit)
                    self.assertEqual(info["total_bytes"], total)
                    self.assertGreater(info["next_offset"], offset, "pagination must always progress")
                    self.assertLessEqual(info["returned_bytes"], max(limit, 4))
                    parts.append(info["text"])
                    offset = info["next_offset"]
                    steps += 1
                    if info["eof"]:
                        break
                    self.assertLess(steps, total + 1)
                self.assertEqual("".join(parts), payload, limit)
            # Random access at every offset (including inside 4-byte characters) matches utf8_slice.
            from spillway.limits import utf8_slice
            data = payload.encode("utf-8")
            for offset in range(1000, 1040):
                for limit in (1, 2, 3, 4, 7):
                    info = store.read_slice(h, offset, limit)
                    self.assertEqual(
                        (info["text"], info["next_offset"], info["eof"]), utf8_slice(data, offset, limit),
                        (offset, limit),
                    )
                    self.assertNotIn("�", info["text"])
            # Offset past the end: empty, eof, no error.
            info = store.read_slice(h, total + 10, 100)
            self.assertEqual((info["text"], info["eof"], info["next_offset"]), ("", True, total))


    @unittest.skipUnless(os.name == "posix" and hasattr(os, "mkfifo"), "POSIX FIFOs and symlinks")
    def test_fifo_artifact_and_symlinked_artifacts_dir_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp))
            store.artifacts_dir.mkdir(parents=True)
            os.mkfifo(store.artifacts_dir / ("b" * 64 + ".txt"))
            with self.assertRaises(OSError):  # must not block forever in open()
                store.read_slice("b" * 64, 0, 10)
            elsewhere = Path(tmp, "elsewhere")
            elsewhere.mkdir()
            other = ArtifactStore(Path(tmp, "logs2"))
            other.root_dir.mkdir()
            other.artifacts_dir.symlink_to(elsewhere)
            with self.assertRaises(OSError):
                other.write_artifact(sha("x"), "x")
            self.assertEqual(list(elsewhere.iterdir()), [])


class CliTests(unittest.TestCase):
    def test_stats_skips_corrupt_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipts.jsonl"
            path.write_text(
                json.dumps({"mode": "full", "original_bytes": 10, "rendered_bytes": 60}) + "\n"
                + '{"mode": "prev\n'  # truncated write
                + "[1, 2]\n",
                encoding="utf-8",
            )
            import contextlib
            import io
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(cli.main(["stats", "--json", str(path)]), 0)
            summary = json.loads(buf.getvalue())
            self.assertEqual(summary["total_results"], 1)
            self.assertEqual(summary["skipped_lines"], 1)

    def test_unknown_command_and_missing_file(self):
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["bogus"]), 2)
            self.assertEqual(cli.main(["stats", "/nonexistent/receipts.jsonl"]), 2)

    def test_version_stats_and_prune_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp))
            h1 = sha("a" * 2000)
            store.write_artifact(h1, "a" * 2000)
            store.append_jsonl(
                "receipts.jsonl",
                json.dumps({
                    "mode": "preview",
                    "original_bytes": 25000,
                    "rendered_bytes": 15800,
                    "would_change": True,
                    "verified": True,
                    "elapsed_us": 420,
                }),
            )
            self.assertEqual(cli.main(["--version"]), 0)
            self.assertEqual(cli.main(["stats", str(Path(tmp) / "receipts.jsonl")]), 0)
            self.assertEqual(cli.main(["stats", "--json", str(Path(tmp) / "receipts.jsonl")]), 0)
            self.assertEqual(cli.main(["prune", "--log-dir", tmp, "--max-artifacts", "1"]), 0)


if __name__ == "__main__":
    unittest.main()
