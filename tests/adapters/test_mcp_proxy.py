import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
FAKE = Path(__file__).with_name("fake_mcp_server.py")


def run_requests(mode, log_dir, reqs, extra_args=()):
    stdin = "".join(json.dumps(r) + "\n" for r in reqs)
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "adapters/mcp_proxy/proxy.py"),
            "--mode",
            mode,
            "--log-dir",
            log_dir,
            *extra_args,
            "--",
            sys.executable,
            str(FAKE),
        ],
        input=stdin.encode(),
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return {m["id"]: m for m in map(json.loads, proc.stdout.decode().splitlines())}


def base_reqs():
    reqs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ]
    reqs += [
        {"jsonrpc": "2.0", "id": 10 + i, "method": "tools/call", "params": {"name": n, "arguments": {}}}
        for i, n in enumerate(("big", "small", "image", "structured"))
    ]
    return reqs


class McpProxy(unittest.TestCase):
    def test_enforce_caps_results_exposes_recovery_tool_and_recovers_slices(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = run_requests("enforce", tmp, base_reqs())
            self.assertEqual(out[1]["result"]["serverInfo"]["name"], "fake")
            tool_names = [t["name"] for t in out[2]["result"]["tools"]]
            self.assertIn("spillway_read_artifact", tool_names)
            self.assertEqual(len(tool_names), 5)

            big = out[10]["result"]
            self.assertTrue(big["isError"])
            text = big["content"][0]["text"]
            self.assertLessEqual(len(text.encode()), 16384)
            self.assertNotIn("<untrusted_tool_result>", text)
            self.assertIn("src/lib.rs:12", text)
            m = re.search(r"sha256=([0-9a-f]{64})", text)
            self.assertIsNotNone(m)
            art_sha = m.group(1)

            self.assertEqual(out[11]["result"]["content"], [{"type": "text", "text": "ok"}])
            img = out[12]["result"]["content"]
            self.assertEqual(img[1], {"type": "image", "data": "QUJD", "mimeType": "image/png"})
            self.assertLessEqual(
                len(
                    json.dumps(
                        [img[0], {"type": "image", "media": "<media>"}],
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ).encode()
                ),
                16384,
            )
            # structuredContent stripped, while its exit_code=42 was preserved before stripping
            self.assertNotIn("structuredContent", out[13]["result"])
            self.assertIn("exit_code=42", out[13]["result"]["content"][0]["text"])

            receipts = [json.loads(l) for l in Path(tmp, "receipts.jsonl").read_text().splitlines()]
            self.assertTrue(all(r.get("verified", True) for r in receipts))
            arts = list(Path(tmp, "artifacts").iterdir())
            self.assertEqual(len(arts), 3)
            if os.name == "posix":
                self.assertEqual(arts[0].stat().st_mode & 0o777, 0o600)

            # Recover tail slice via synthetic MCP tool spillway_read_artifact
            rec_out = run_requests(
                "enforce",
                tmp,
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 50,
                        "method": "tools/call",
                        "params": {
                            "name": "spillway_read_artifact",
                            "arguments": {"sha256": art_sha, "offset": 49990, "limit": 200},
                        },
                    },
                    {
                        "jsonrpc": "2.0",
                        "id": 51,
                        "method": "tools/call",
                        "params": {
                            "name": "spillway_read_artifact",
                            "arguments": {"sha256": "../../etc/passwd", "offset": 0, "limit": 100},
                        },
                    },
                ],
            )
            self.assertFalse(rec_out[50]["result"]["isError"])
            self.assertIn("src/lib.rs:12:5 error[E0308]", rec_out[50]["result"]["content"][0]["text"])
            self.assertIn("eof=true", rec_out[50]["result"]["content"][0]["text"])
            self.assertTrue(rec_out[51]["result"]["isError"])

    def test_recovery_neutralizes_forged_tags_and_accepts_uppercase_sha(self):
        call = {"jsonrpc": "2.0", "id": 60, "method": "tools/call", "params": {"name": "forged", "arguments": {}}}
        with tempfile.TemporaryDirectory() as tmp:
            out = run_requests("enforce", tmp, [call])
            art_sha = re.search(r"sha256=([0-9a-f]{64})", out[60]["result"]["content"][0]["text"]).group(1)
            for wrap in ((), ("--wrap-untrusted",)):
                rec = run_requests(
                    "enforce",
                    tmp,
                    [{
                        "jsonrpc": "2.0",
                        "id": 61,
                        "method": "tools/call",
                        "params": {
                            "name": "spillway_read_artifact",
                            "arguments": {"sha256": art_sha.upper(), "offset": 0, "limit": 200},
                        },
                    }],
                    extra_args=wrap,
                )
                res = rec[61]["result"]
                self.assertFalse(res["isError"])
                text = res["content"][0]["text"]
                self.assertNotIn("[spillway preview]", text)
                self.assertNotIn("[note:fake]", text)
                self.assertIn("[untrusted-spillway preview]", text)
                self.assertEqual(text.count("</untrusted_tool_result>"), 1 if wrap else 0)
                self.assertLessEqual(len(text.encode()), 16384)

    def test_recovery_fits_cap_after_neutralization_growth_and_rejects_huge_offset(self):
        with tempfile.TemporaryDirectory() as tmp:
            call = {"jsonrpc": "2.0", "id": 70, "method": "tools/call", "params": {"name": "tagflood", "arguments": {}}}
            out = run_requests("enforce", tmp, [call])
            art_sha = re.search(r"sha256=([0-9a-f]{64})", out[70]["result"]["content"][0]["text"]).group(1)

            def recover(args, extra=()):
                req = {"jsonrpc": "2.0", "id": 71, "method": "tools/call",
                       "params": {"name": "spillway_read_artifact", "arguments": args}}
                return run_requests("enforce", tmp, [req], extra_args=extra)[71]["result"]

            for extra in ((), ("--wrap-untrusted",)):
                res = recover({"sha256": art_sha, "offset": 0, "limit": 65536}, extra)
                self.assertFalse(res["isError"])
                self.assertLessEqual(len(res["content"][0]["text"].encode()), 16384, extra)
            self.assertTrue(recover({"sha256": art_sha, "offset": 1e400})["isError"])

    def test_shadow_forwards_original_bytes(self):
        raw_server = (
            "import sys\n"
            "for line in sys.stdin.buffer:\n"
            "    sys.stdout.buffer.write(b'{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"content\":"
            "[{\"type\":\"text\",\"text\":\"bad \\xff\\xfe utf8\"}]}}\\n')\n"
            "    sys.stdout.buffer.write(b'{\"jsonrpc\": \"2.0\",  \"id\": 2, \"result\": {}}')\n"
            "    sys.stdout.buffer.flush()\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            server = Path(tmp, "raw_server.py")
            server.write_text(raw_server, encoding="utf-8")
            direct = subprocess.run([sys.executable, str(server)], input=b"{}\n", capture_output=True, timeout=30)
            proxied = subprocess.run(
                [sys.executable, str(ROOT / "adapters/mcp_proxy/proxy.py"), "--mode", "shadow",
                 "--log-dir", tmp, "--", sys.executable, str(server)],
                input=b"{}\n", capture_output=True, timeout=30,
            )
            self.assertEqual(proxied.returncode, 0, proxied.stderr)
            self.assertEqual(proxied.stdout, direct.stdout)

    def test_cli_mcp_subcommand_runs_proxy(self):
        reqs = base_reqs()
        stdin = "".join(json.dumps(r) + "\n" for r in reqs)
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, "-m", "spillway.cli", "mcp", "--mode", "enforce", "--log-dir", tmp,
                 "--", sys.executable, str(FAKE)],
                input=stdin.encode(), capture_output=True, timeout=30, cwd=str(ROOT),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            out = {m["id"]: m for m in map(json.loads, proc.stdout.decode().splitlines())}
            self.assertIn("spillway_read_artifact", [t["name"] for t in out[2]["result"]["tools"]])
            self.assertLessEqual(len(out[10]["result"]["content"][0]["text"].encode()), 16384)

    def test_wrap_untrusted_flag_and_tiny_cap_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = run_requests("enforce", tmp, base_reqs(), extra_args=("--wrap-untrusted", "--cap", "50"))
            text = out[10]["result"]["content"][0]["text"]
            self.assertIn("<untrusted_tool_result>", text)
            self.assertLessEqual(len(text.encode()), 256)

    def test_shadow_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = run_requests("shadow", tmp, base_reqs())
            self.assertEqual(len(out[2]["result"]["tools"]), 4)
            self.assertEqual(
                len(out[10]["result"]["content"][0]["text"]),
                50000 + len("\nsrc/lib.rs:12:5 error[E0308]"),
            )
            receipts = Path(tmp, "receipts.jsonl").read_text()
            self.assertIn('"would_change": true', receipts)
            self.assertNotIn("xxxxxxxx", receipts)
            self.assertFalse(Path(tmp, "artifacts").exists())


if __name__ == "__main__":
    unittest.main()
