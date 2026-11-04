"""Replay OFFLINE (sem modelo, sem rede) com três braços e oráculos de fidelidade (issue #11).

Braços sobre entradas idênticas:
  none        sem orçamento: corpo inteiro + notas.
  historical  spill histórico: preview só da cabeça por CARACTERES até o teto, nota descartada
              quando a linha é spillada, e spill da maior linha quando o agregado estoura.
  candidate   núcleo cbg (finalize_batch).

Oráculos por linha (independentes do núcleo; usam a verdade da fixture):
  bytes<=teto, exit_code presente, local do erro presente, nota presente 1x fora do wrapper,
  wrapper único, mídia preservada; e agregado<=turn_budget por caso.

Uso: python3 benchmarks/replay/replay.py [--out benchmarks/replay/results/offline-replay.json]
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from cbg import NoteLedger, Policy, finalize_batch  # noqa: E402
from cbg.render import render, rendered_bytes, split_result  # noqa: E402

CAP = 16384
FIXTURES = Path(__file__).with_name("fixtures")
OPEN, CLOSE = "<untrusted_tool_result>", "</untrusted_tool_result>"


def arm_none(case):
    out = []
    for row in case["rows"]:
        body, media, kind = split_result(row["result"])
        notes = ["[note:%s] %s" % (n["note_id"], n["text"]) for n in case.get("notes", []) if n["owner"] == row["call_id"]]
        out.append(render(body, kind, notes, media))
    return out


def arm_historical(case):
    budget = case.get("turn_budget")
    bodies = []
    for row in case["rows"]:
        body, media, kind = split_result(row["result"])
        spilled = len(body) > CAP
        if spilled:
            body = body[:CAP - 200] + "\n[output truncated; full output saved]"
        bodies.append([body, media, kind, spilled, row["call_id"]])
    def total():
        return sum(len(b[0]) for b in bodies)
    if budget is not None and total() > budget:
        largest = max(bodies, key=lambda b: len(b[0]))
        largest[0] = largest[0][:max(0, len(largest[0]) - (total() - budget))] + "\n[aggregate budget: truncated]"
        largest[3] = True
    out = []
    for body, media, kind, spilled, cid in bodies:
        notes = [] if spilled else ["[note:%s] %s" % (n["note_id"], n["text"]) for n in case.get("notes", []) if n["owner"] == cid]
        out.append(render(body, kind, notes, media))
    return out


def arm_candidate(case):
    ledger = NoteLedger("replay")
    for n in case.get("notes", []):
        ledger.queue(n["note_id"], n["owner"], n["text"])
    outs = finalize_batch([dict(r) for r in case["rows"]], ledger=ledger, policy=Policy(result_cap=CAP),
                          turn_budget=case.get("turn_budget"))
    return [o.rendered for o in outs]


def oracles(case, rendered):
    res = []
    for row, r in zip(case["rows"], rendered):
        exp = case["expect"].get(row["call_id"], {})
        text = r.model_text()
        outside = text.rsplit(CLOSE, 1)[-1] if r.kind == "text" else \
            "\n".join(p.get("text", "") for p in r.payload[1:] if p.get("type") == "text")
        o = {"bytes_le_cap": rendered_bytes(r) <= CAP, "single_wrapper": text.count(OPEN) == 1 and text.count(CLOSE) == 1}
        if "exit_code" in exp:
            o["exit_code"] = bool(re.search(r"exit[_ ]?code\"?\s*[:=]\s*%d\b" % exp["exit_code"], text))
        for loc in exp.get("locations", []):
            o["location"] = o.get("location", True) and (loc in text or loc.replace(":", "(", 1) in text
                                                       or ('"%s", line %s' % tuple(loc.rsplit(":", 1))) in text)
        for nid in exp.get("notes", []):
            tag = "[note:%s]" % nid
            o["note_once_outside"] = o.get("note_once_outside", True) and text.count(tag) == 1 and tag in outside
        if "media" in exp:
            o["media_preserved"] = r.kind == "multimodal" and len(r.media) == exp["media"]
        res.append({"call_id": row["call_id"], "bytes": rendered_bytes(r), "oracles": o})
    agg = sum(x["bytes"] for x in res)
    case_ok = {"aggregate_le_budget": agg <= case["turn_budget"]} if case.get("turn_budget") else {}
    return res, agg, case_ok


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).with_name("results") / "offline-replay.json"))
    args = ap.parse_args(argv)
    arms = {"none": arm_none, "historical": arm_historical, "candidate": arm_candidate}
    report = {"schema": "cbg-offline-replay/1", "synthetic": True, "model_calls": 0, "cap_bytes": CAP,
              "fixtures": {}, "cases": [], "arms": {}}
    files = sorted(FIXTURES.glob("*.json"))
    for path in files:
        report["fixtures"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in arms:
        report["arms"][name] = {"bytes_total": 0, "oracle_checks": 0, "oracle_pass": 0, "failures": []}
    for path in files:
        case = json.loads(path.read_text(encoding="utf-8"))
        entry = {"case": case["case"], "language": case["language"], "arms": {}}
        for name, fn in arms.items():
            rows, agg, case_ok = oracles(case, fn(case))
            entry["arms"][name] = {"aggregate_bytes": agg, "rows": rows, **case_ok}
            a = report["arms"][name]
            a["bytes_total"] += agg
            checks = [(r["call_id"] + ":" + k, v) for r in rows for k, v in r["oracles"].items()] + list(case_ok.items())
            a["oracle_checks"] += len(checks)
            a["oracle_pass"] += sum(1 for _, v in checks if v)
            a["failures"] += [case["case"] + "/" + k for k, v in checks if not v]
        report["cases"].append(entry)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("cbg offline replay: %d casos sintéticos, 0 chamadas de modelo, teto %d bytes" % (len(files), CAP))
    print("%-11s %12s %10s  falhas" % ("braço", "bytes", "oráculos"))
    for name, a in report["arms"].items():
        print("%-11s %12d %5d/%-4d  %s" % (name, a["bytes_total"], a["oracle_pass"], a["oracle_checks"],
                                          ", ".join(a["failures"]) or "-"))
    cand = report["arms"]["candidate"]
    return 0 if cand["oracle_pass"] == cand["oracle_checks"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
