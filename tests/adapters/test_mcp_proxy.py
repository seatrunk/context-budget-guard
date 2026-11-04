import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FAKE = Path(__file__).with_name("fake_mcp_server.py")


def session(mode, log_dir):
    reqs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
    reqs += [{"jsonrpc": "2.0", "id": 10 + i, "method": "tools/call", "params": {"name": n, "arguments": {}}}
             for i, n in enumerate(("big", "small", "image", "structured"))]
    stdin = "".join(json.dumps(r) + "\n" for r in reqs)
    proc = subprocess.run([sys.executable, str(ROOT / "adapters/mcp_proxy/proxy.py"), "--mode", mode,
                           "--log-dir", log_dir, "--", sys.executable, str(FAKE)],
                          input=stdin.encode(), capture_output=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return {m["id"]: m for m in map(json.loads, proc.stdout.decode().splitlines())}


class McpProxy(unittest.TestCase):
    def test_enforce_caps_tool_results_and_passes_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = session("enforce", tmp)
            self.assertEqual(out[1]["result"]["serverInfo"]["name"], "fake")
            self.assertEqual(len(out[2]["result"]["tools"]), 4)
            big = out[10]["result"]
            self.assertTrue(big["isError"])
            text = big["content"][0]["text"]
            self.assertLessEqual(len(text.encode()), 16384)
            self.assertIn("src/lib.rs:12", text)
            self.assertEqual(out[11]["result"]["content"], [{"type": "text", "text": "ok"}])
            img = out[12]["result"]["content"]
            self.assertEqual(img[1], {"type": "image", "data": "QUJD", "mimeType": "image/png"})
            self.assertLessEqual(len(json.dumps([img[0], {"type": "image", "media": "<media>"}],
                                                ensure_ascii=False, separators=(",", ":")).encode()), 16384)
            self.assertNotIn("structuredContent", out[13]["result"])
            receipts = [json.loads(l) for l in Path(tmp, "receipts.jsonl").read_text().splitlines()]
            self.assertTrue(all(r.get("verified", True) for r in receipts))
            arts = list(Path(tmp, "artifacts").iterdir())
            self.assertEqual(len(arts), 3)
            if os.name == "posix":
                self.assertEqual(arts[0].stat().st_mode & 0o777, 0o600)

    def test_shadow_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = session("shadow", tmp)
            self.assertEqual(len(out[10]["result"]["content"][0]["text"]), 50000 + len("\nsrc/lib.rs:12:5 error[E0308]"))
            receipts = Path(tmp, "receipts.jsonl").read_text()
            self.assertIn('"would_change": true', receipts)
            self.assertNotIn("xxxxxxxx", receipts)  # recibo sem conteúdo
            self.assertFalse(Path(tmp, "artifacts").exists())


if __name__ == "__main__":
    unittest.main()
