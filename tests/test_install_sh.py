"""install.sh refuses dangerous destinations before rm -rf."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "adapters/hermes/install.sh"


@unittest.skipUnless(shutil.which("sh"), "sh unavailable")
class InstallSh(unittest.TestCase):
    def run_sh(self, **env):
        base = {"PATH": os.environ.get("PATH", ""), "HOME": env.pop("HOME", tempfile.gettempdir())}
        base.update(env)
        return subprocess.run(["sh", str(SCRIPT)], env=base, capture_output=True, text=True, timeout=30)

    def test_rejects_root_and_arbitrary_dest_without_deleting(self):
        with tempfile.TemporaryDirectory() as tmp:
            victim = Path(tmp, "victim")
            (victim / "vendor/cbg").mkdir(parents=True)
            cases = {"/": "empty destination", "//": "empty destination", str(victim): "unexpected destination",
                     str(victim) + "/": "unexpected destination",
                     tmp + "/plugins/context-budget-guard-x": "unexpected destination"}
            for dest, msg in cases.items():
                r = self.run_sh(CBG_INSTALL_DEST=dest)
                self.assertEqual(r.returncode, 2, (dest, r.stderr))
                self.assertIn(msg, r.stderr, dest)
            self.assertTrue((victim / "vendor/cbg").is_dir())

    def test_empty_dest_after_normalization(self):
        r = self.run_sh(CBG_INSTALL_DEST="///")
        self.assertEqual(r.returncode, 2)
        self.assertIn("empty destination", r.stderr)

    def test_valid_dest_in_temp_hermes_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self.run_sh(HERMES_HOME=tmp + "/")
            self.assertEqual(r.returncode, 0, r.stderr)
            dest = Path(tmp, "plugins/context-budget-guard")
            self.assertTrue((dest / "__init__.py").is_file())
            self.assertTrue((dest / "vendor/cbg/budget.py").is_file())
            self.assertFalse(list(dest.rglob("__pycache__")))
            r2 = self.run_sh(HERMES_HOME=tmp)  # idempotent reinstall
            self.assertEqual(r2.returncode, 0, r2.stderr)


if __name__ == "__main__":
    unittest.main()
