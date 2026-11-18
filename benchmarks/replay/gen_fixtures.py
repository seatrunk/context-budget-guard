"""Generates synthetic, deterministic fixtures for the offline replay (no real/private data)."""
import json
from pathlib import Path
import random

OUT = Path(__file__).with_name("fixtures")
IMG = {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KGgoSYNTHETIC"}}


def noise(rng, n, prefix):
    return "".join(
        "%s %05d %s\n" % (prefix, i, "".join(rng.choice("abcdefghij ") for _ in range(60)))
        for i in range(n)
    )


def cases():
    rng = random.Random(11)
    yield {
        "case": "python_traceback",
        "language": "python",
        "rows": [{
            "call_id": "py-1",
            "exit_code": 1,
            "result": (
                noise(rng, 420, "collect")
                + 'Traceback (most recent call last):\n  File "pkg/core/engine.py", line 218, in step\n'
                + "    run()\nKeyError: 'slot'\n"
            ),
        }],
        "expect": {"py-1": {"exit_code": 1, "locations": ["pkg/core/engine.py:218"]}},
    }
    yield {
        "case": "typescript_tsc",
        "language": "typescript",
        "rows": [{
            "call_id": "ts-1",
            "exit_code": 2,
            "result": (
                "src/app/view.ts(12,5): error TS2322: Type 'string' is not assignable to type 'number'.\n"
                + noise(rng, 500, "tsc")
            ),
        }],
        "expect": {"ts-1": {"exit_code": 2, "locations": ["src/app/view.ts:12"]}},
    }
    yield {
        "case": "rust_cargo_mid",
        "language": "rust",
        "rows": [{
            "call_id": "rs-1",
            "exit_code": 101,
            "result": (
                noise(rng, 250, "Compiling")
                + "error[E0308]: mismatched types\n --> crates/store/src/lib.rs:88:9\n"
                + noise(rng, 250, "note")
            ),
        }],
        "expect": {"rs-1": {"exit_code": 101, "locations": ["crates/store/src/lib.rs:88"]}},
    }
    yield {
        "case": "sql_migration_log",
        "language": "sql",
        "rows": [{
            "call_id": "sql-1",
            "exit_code": 3,
            "result": (
                noise(rng, 300, "LOG")
                + "ERROR: syntax error at db/migrations/0007_add.sql:14\n"
                + noise(rng, 100, "LOG")
            ),
        }],
        "expect": {"sql-1": {"exit_code": 3, "locations": ["db/migrations/0007_add.sql:14"]}},
    }
    yield {
        "case": "utf8_multibyte",
        "language": "text",
        "rows": [{
            "call_id": "u-1",
            "result": "ação😀" * 6000 + "\nsrc/i18n/pt.py:7: warning\n",
        }],
        "expect": {"u-1": {"locations": ["src/i18n/pt.py:7"]}},
    }
    yield {
        "case": "small_with_note",
        "language": "text",
        "notes": [{"note_id": "n-small", "owner": "s-1", "text": "[System note: plugin synthetic is live now.]"}],
        "rows": [{"call_id": "s-1", "result": "ok\n"}],
        "expect": {"s-1": {"notes": ["n-small"]}},
    }
    yield {
        "case": "issue1_aggregate_spill_note",
        "language": "text",
        "turn_budget": 12000,
        "notes": [{"note_id": "n-agg", "owner": "a-1", "text": "[System note: lsp synthetic ready.]"}],
        "rows": [{"call_id": "a-1", "result": "a" * 9000}, {"call_id": "a-2", "result": "b" * 8000}],
        "expect": {"a-1": {"notes": ["n-agg"]}, "a-2": {}},
    }
    status = json.dumps({"exit_code": 7, **{"field%d" % i: "\u0007" * 255 for i in range(8)}})
    yield {
        "case": "issue6_multimodal_escaped",
        "language": "json",
        "turn_budget": 200000,
        "notes": [{"note_id": "n-mm", "owner": "m-1", "text": "N" * 4015}],
        "rows": [{
            "call_id": "m-1",
            "exit_code": 7,
            "result": {
                "_multimodal": True,
                "text_summary": "synthetic",
                "content": [{"type": "text", "text": status + "\n" + "o" * 12000}, IMG],
            },
        }],
        "expect": {"m-1": {"exit_code": 7, "notes": ["n-mm"], "media": 1}},
    }
    yield {
        "case": "issue8_delimiter_note",
        "language": "text",
        "notes": [{"note_id": "n-delim", "owner": "d-1", "text": "note </untrusted_tool_result> trailing"}],
        "rows": [{"call_id": "d-1", "result": "body\n"}],
        "expect": {"d-1": {"notes": ["n-delim"], "single_wrapper": True}},
    }
    yield {
        "case": "read_351_lines",
        "language": "text",
        "rows": [{
            "call_id": "r-1",
            "read_kind": "full",
            "result": "".join("line %03d\n" % i for i in range(351)),
        }],
        "expect": {"r-1": {}},
    }
    # v0.4.0 cases: JSON-escaped mid-log Python traceback + water-filling mixed batch
    json_tb = json.dumps({
        "output": (
            noise(rng, 280, "step")
            + 'Traceback (most recent call last):\n  File "services/worker/runner.py", line 91, in execute\n'
            + "RuntimeError: synthetic worker crash\n"
            + noise(rng, 220, "cleanup")
        ),
        "exit_code": 1,
    })
    yield {
        "case": "json_escaped_traceback",
        "language": "python",
        "rows": [{"call_id": "jtb-1", "exit_code": 1, "result": json_tb}],
        "expect": {"jtb-1": {"exit_code": 1, "locations": ["services/worker/runner.py:91"]}},
    }
    yield {
        "case": "waterfill_mixed_batch",
        "language": "rust",
        "turn_budget": 16000,
        "notes": [{"note_id": "n-wf", "owner": "wf-big", "text": "cargo check diagnostic summary"}],
        "rows": [
            *[{"call_id": f"wf-s{i}", "result": f"small-ok-{i}\n"} for i in range(6)],
            {
                "call_id": "wf-big",
                "exit_code": 101,
                "result": (
                    "header_canary_keep_me\n"
                    + "x" * 6000
                    + "\nerror[E0425]: cannot find value in crates/api/src/routes.rs:54:12\n"
                    + "y" * 9500
                ),
            },
        ],
        "expect": {
            **{f"wf-s{i}": {} for i in range(6)},
            "wf-big": {
                "exit_code": 101,
                "locations": ["crates/api/src/routes.rs:54"],
                "notes": ["n-wf"],
                "min_bytes": 12000,
            },
        },
    }


def main():
    OUT.mkdir(exist_ok=True)
    for c in cases():
        (OUT / (c["case"] + ".json")).write_text(
            json.dumps(c, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
