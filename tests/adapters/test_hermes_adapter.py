import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("spillway_hermes", ROOT / "adapters/hermes/spillway/__init__.py")
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)


class FakeCtx:
    def __init__(self):
        self.hooks = {}

    def register_hook(self, name, fn):
        self.hooks[name] = fn


class HermesAdapter(unittest.TestCase):
    def call(self, env, result):
        ctx = FakeCtx()
        plugin.register(ctx)
        clean = {k: v for k, v in os.environ.items() if not k.startswith(("SPILLWAY_", "CBG_"))}
        clean.update(env)
        with mock.patch.dict(os.environ, clean, clear=True):
            return ctx.hooks["transform_tool_result"](
                tool_name="terminal",
                args={},
                result=result,
                tool_call_id="call-1",
                session_id="s1",
                status="ok",
            )

    def test_default_is_shadow_and_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            big = json.dumps({"output": "y" * 40000, "exit_code": 2})
            self.assertIsNone(self.call({"SPILLWAY_LOG_DIR": tmp}, big))
            rec = json.loads(Path(tmp, "receipts.jsonl").read_text())
            self.assertEqual((rec["adapter_mode"], rec["would_change"], rec["exit_code"]), ("shadow", True, 2))

    def test_enforce_returns_bounded_body_with_path_and_json_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = json.dumps({
                "output": (
                    "y" * 25000
                    + '\nTraceback (most recent call last):\n  File "src/m.py", line 9, in run\nRuntimeError: err\n'
                    + "y" * 20000
                ),
                "exit_code": 2,
            })
            out = self.call({"SPILLWAY_LOG_DIR": tmp, "SPILLWAY_MODE": "enforce"}, payload)
            self.assertLessEqual(len(out.encode()), 16384 - 512)
            self.assertNotIn("untrusted_tool_result", out)
            self.assertIn("exit_code=2", out)
            self.assertIn("src/m.py:9", out)
            arts = list(Path(tmp, "artifacts").iterdir())
            self.assertEqual(len(arts), 1)
            self.assertIn(str(arts[0]), out)
            # Re-running identical output must overwrite idempotently, never double size via O_APPEND
            size_first = arts[0].stat().st_size
            self.call({"SPILLWAY_LOG_DIR": tmp, "SPILLWAY_MODE": "enforce"}, payload)
            self.assertEqual(arts[0].stat().st_size, size_first)

    def test_enforce_log_dir_with_braces_still_cuts(self):
        with tempfile.TemporaryDirectory() as tmp:
            logdir = Path(tmp, "a{b}c{sha256}")
            out = self.call({"SPILLWAY_LOG_DIR": str(logdir), "SPILLWAY_MODE": "enforce"}, "q" * 40000)
            self.assertIsNotNone(out, "brace-containing paths must not break str.format and fail open")
            self.assertLessEqual(len(out.encode()), 16384 - 512)
            arts = list((logdir / "artifacts").iterdir())
            self.assertEqual(len(arts), 1)
            self.assertIn(str(arts[0]), out)
            self.assertFalse(Path(logdir, "errors.jsonl").exists())

    def test_enforce_caps_output_with_lone_surrogate(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.call({"SPILLWAY_LOG_DIR": tmp, "SPILLWAY_MODE": "enforce"}, "x" * 50000 + "\udcff")
            self.assertIsNotNone(out, "must cap, not fail open with the full output")
            self.assertLessEqual(len(out.encode()), 16384 - 512)

    def test_fail_open_never_raises_on_bad_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"SPILLWAY_LOG_DIR": tmp, "SPILLWAY_MODE": "enforce", "SPILLWAY_MAX_ARTIFACTS": "abc"}
            self.assertIsNone(self.call(env, "q" * 40000))
            self.assertIn("ValueError", Path(tmp, "errors.jsonl").read_text())

    def test_empty_primary_env_falls_back_to_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.call({"SPILLWAY_MODE": "", "CBG_MODE": "enforce", "SPILLWAY_LOG_DIR": tmp}, "q" * 40000)
            self.assertIsNotNone(out)

    def test_legacy_cbg_env_fallback_and_off_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(self.call({"CBG_LOG_DIR": tmp, "CBG_MODE": "off"}, "z" * 90000))
            self.assertFalse(Path(tmp, "receipts.jsonl").exists())
            self.assertIsNone(self.call({"CBG_LOG_DIR": tmp, "CBG_MODE": "enforce"}, "small"))


if __name__ == "__main__":
    unittest.main()
