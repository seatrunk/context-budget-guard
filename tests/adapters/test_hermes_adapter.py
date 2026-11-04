import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("cbg_hermes", ROOT / "adapters/hermes/context_budget_guard/__init__.py")
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
        with mock.patch.dict(os.environ, env, clear=False):
            return ctx.hooks["transform_tool_result"](tool_name="terminal", args={}, result=result,
                                                       tool_call_id="call-1", session_id="s1", status="ok")

    def test_default_is_shadow_and_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"CBG_LOG_DIR": tmp}
            os.environ.pop("CBG_MODE", None)
            big = json.dumps({"output": "y" * 40000, "exit_code": 2})
            self.assertIsNone(self.call(env, big))
            rec = json.loads(Path(tmp, "receipts.jsonl").read_text())
            self.assertEqual((rec["adapter_mode"], rec["would_change"], rec["exit_code"]), ("shadow", True, 2))

    def test_enforce_returns_bounded_body_without_our_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.call({"CBG_LOG_DIR": tmp, "CBG_MODE": "enforce"},
                            json.dumps({"output": "y" * 40000 + "\nsrc/m.py:9: E", "exit_code": 2}))
            self.assertLessEqual(len(out.encode()), 16384 - 512)
            self.assertNotIn("untrusted_tool_result", out)
            self.assertIn("exit_code=2", out)
            self.assertIn("src/m.py:9", out)
            self.assertEqual(len(list(Path(tmp, "artifacts").iterdir())), 1)

    def test_off_and_small(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(self.call({"CBG_LOG_DIR": tmp, "CBG_MODE": "off"}, "z" * 90000))
            self.assertFalse(Path(tmp, "receipts.jsonl").exists())
            self.assertIsNone(self.call({"CBG_LOG_DIR": tmp, "CBG_MODE": "enforce"}, "small"))


if __name__ == "__main__":
    unittest.main()
