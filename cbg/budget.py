"""Limiter: decides what enters the window and emits the receipt. No I/O.

The artifact (complete original) is returned in ``Outcome.artifact`` for the adapter to write
somewhere private; the core only computes sha256 and size.
"""
from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional

from . import facts as _facts
from .limits import effective_lines, head_lines, utf8_bytes, utf8_tail, utf8_truncate
from .notes import NoteLedger
from .render import Rendered, render, rendered_bytes, split_result
from .sanitize import neutralize, neutralize_body
from .verify import note_tag, sha256_of, verify


@dataclass(frozen=True)
class Policy:
    result_cap: int = 16384
    full_read_lines: int = 350
    partial_read_lines: int = 150
    note_cap: int = 4096
    note_batch_cap: int = 8192
    max_locations: int = 5
    min_row_cap: int = 1024  # floor for the aggregate corrective pass


@dataclass
class Receipt:
    """Approved-read receipt (#7): single use, bound to call ID and session."""
    call_id: str
    session_id: str
    max_bytes: int
    max_lines: Optional[int] = None
    consumed_by: Optional[str] = None

    def admits(self, call_id: str, session_id: str) -> bool:
        if self.call_id != call_id or self.session_id != session_id:
            return False
        return self.consumed_by in (None, call_id)  # re-finalizing the SAME call does not revoke


@dataclass
class Outcome:
    call_id: str
    rendered: Rendered
    mode: str  # full | preview | marker | withheld | failclosed | control
    receipt: Dict[str, Any]
    artifact: Optional[str]
    violations: List[str] = field(default_factory=list)

    @property
    def nbytes(self) -> int:
        return rendered_bytes(self.rendered)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _prepare_notes(ledger: Optional[NoteLedger], call_id: str, policy: Policy):
    """Eligible notes -> (visible texts, visible ids, marker-only ids)."""
    if ledger is None:
        return [], [], []
    texts, shown, marked, used = [], [], [], 0
    for note in ledger.eligible(call_id):
        body = neutralize(note.text)
        if utf8_bytes(body) > policy.note_cap:
            body = utf8_truncate(body, policy.note_cap - 64) + " [cbg: nota truncada de %d bytes]" % utf8_bytes(note.text)
        line = note_tag(note.note_id) + " " + body
        if used + utf8_bytes(line) > policy.note_batch_cap:
            marked.append(note.note_id)
            continue
        used += utf8_bytes(line)
        texts.append(line)
        shown.append(note.note_id)
    if marked:
        texts.append("[cbg: %d nota(s) acima do orçamento de notas: %s]" % (len(marked), ",".join(marked)))
    return texts, shown, marked


def _note_marker(shown: List[str], marked: List[str]) -> List[str]:
    ids = shown + marked
    return ["[cbg: %d nota(s) existiam e foram retidas: %s]" % (len(ids), ",".join(ids))] if ids else []


def _header(mode: str, orig: str, exit_code, locs, art_sha: str) -> str:
    parts = ["[cbg %s] original %d bytes, %d linhas" % (mode, utf8_bytes(orig), effective_lines(orig))]
    if exit_code is not None:
        parts.append("exit_code=%d" % exit_code)
    if locs:
        parts.append("erros: " + ", ".join(locs))
    parts.append("artefato sha256=%s (ler com offset/limit)" % art_sha[:16])
    return "; ".join(parts) + "\n"


def apply_budget(call_id: str, result: Any, *, policy: Policy = Policy(), ledger: Optional[NoteLedger] = None,
                 exit_code: Optional[int] = None, read_kind: Optional[str] = None,
                 receipt: Optional[Receipt] = None, session_id: Optional[str] = None,
                 cap_override: Optional[int] = None, force: Optional[str] = None,
                 control: bool = False) -> Outcome:
    """Applies the budget to a tool result.

    ``force``: "withheld" (policy/aggregate failure: body withheld, notes kept) or None.
    """
    raw_body, media, kind = split_result(result)
    code = _facts.exit_code_of(result, exit_code)
    locs = _facts.error_locations(raw_body, policy.max_locations)
    artifact = raw_body if not media else raw_body + "\n" + json.dumps(media, ensure_ascii=False, sort_keys=True)
    art_sha = _sha(artifact)
    body = neutralize_body(raw_body)
    note_texts, shown, marked = _prepare_notes(ledger, call_id, policy)
    sid = session_id if session_id is not None else (ledger.session_id if ledger else "")

    cap = policy.result_cap
    line_limit = {"full": policy.full_read_lines, "partial": policy.partial_read_lines}.get(read_kind or "")
    receipt_used = False
    if receipt is not None and receipt.admits(call_id, sid):
        cap = max(cap, receipt.max_bytes)
        line_limit = receipt.max_lines
        receipt.consumed_by = call_id
        receipt_used = True
    if cap_override is not None:
        cap = min(cap, cap_override) if not receipt_used else cap
    if control:
        cap, line_limit = None, None

    # An exit code from metadata always enters as a visible fact.
    fact_line = "" if code is None or _facts.mentions_exit_code(body, code) else "[cbg] exit_code=%d\n" % code

    def fits(r: Rendered) -> bool:
        return cap is None or rendered_bytes(r) <= cap

    mode, rendered = None, None
    if force != "withheld":
        full_body = fact_line + body
        within_lines = line_limit is None or effective_lines(raw_body) <= line_limit
        candidate = render(full_body, kind, note_texts, media)
        if within_lines and fits(candidate):
            mode, rendered = ("control" if control else "full"), candidate
        else:
            header = _header("preview", raw_body, code, locs, art_sha)
            src = head_lines(body, line_limit) if line_limit is not None else body
            budget = cap - rendered_bytes(render(header + "\n[...]\n", kind, note_texts, media))
            for _ in range(64):
                if budget <= 0:
                    break
                head = utf8_truncate(src, budget * 2 // 3)
                tail = utf8_tail(body, budget - utf8_bytes(head)) if line_limit is None else ""
                candidate = render(header + head + "\n[...]\n" + tail, kind, note_texts, media)
                excess = rendered_bytes(candidate) - cap
                if excess <= 0:
                    mode, rendered = "preview", candidate
                    break
                budget -= excess  # re-measure everything after each cut (JSON escaping included)
    if rendered is None:
        mode = "withheld" if force == "withheld" else "marker"
        header = _header(mode, raw_body, code, locs, art_sha)
        for notes_variant in (note_texts, _note_marker(shown, marked)):
            candidate = render(header, kind, notes_variant, media)
            if fits(candidate):
                rendered = candidate
                if notes_variant is not note_texts:
                    marked, shown = shown + marked, []
                break
    if rendered is None:
        mode = "failclosed"
        rendered = _failclosed(cap, kind)
        marked, shown = shown + marked, []

    rec = {
        "call_id": call_id, "mode": mode, "kind": kind, "cap": cap,
        "rendered_bytes": rendered_bytes(rendered), "rendered_sha256": sha256_of(rendered),
        "original_bytes": utf8_bytes(raw_body), "original_lines": effective_lines(raw_body),
        "exit_code": code, "error_locations": locs, "notes_shown": shown, "notes_marked": marked,
        "media_parts": len(media), "artifact_sha256": art_sha, "artifact_bytes": utf8_bytes(artifact),
        "receipt_used": receipt_used,
    }
    required_locs = locs if mode in ("full", "preview", "control", "marker", "withheld") else []
    violations = verify(rendered, cap=cap, exit_code=code if mode != "failclosed" else None,
                        error_locations=required_locs, note_ids=shown, receipt=rec)
    if violations and mode != "failclosed":
        rendered = _failclosed(cap, kind)
        mode = "failclosed"
        marked, shown = shown + marked, []
        rec.update(mode=mode, rendered_bytes=rendered_bytes(rendered), rendered_sha256=sha256_of(rendered),
                   notes_shown=[], notes_marked=marked)
    rec["verified"] = not verify(rendered, cap=cap, receipt=rec)
    rec["violations_before_failclose"] = violations
    if ledger is not None:
        ledger.bind(call_id, shown + marked, rec["rendered_sha256"])
    return Outcome(call_id, rendered, mode, rec, artifact if mode != "full" and mode != "control" else None, violations)


def _failclosed(cap: Optional[int], kind: str) -> Rendered:
    text = "[cbg] resultado retido: verificador reprovou o recibo"
    r = render(text, kind)
    while cap is not None and rendered_bytes(r) > cap and text:
        text = text[:-1]
        r = render(text, kind)
    return r


def finalize_batch(rows: List[Dict[str, Any]], *, ledger: Optional[NoteLedger] = None, policy: Policy = Policy(),
                   turn_budget: Optional[int] = None, policy_available: bool = True,
                   aggregate: Optional[Callable[[List[Outcome]], None]] = None) -> List[Outcome]:
    """Settlement of a batch. rows: dicts with call_id, result and optional exit_code, read_kind,
    receipt, control.

    - settlement 1: per-result budget;
    - single aggregate corrective pass (if turn_budget): shrinks the largest non-control rows;
    - policy/aggregate failure (exception or policy_available=False): every row becomes withheld with
      notes kept (#4, B2, B3); never re-executes a tool;
    - complete_batch only at the end: a note retires only after the last settlement (B3).
    """
    def run(row, **kw):
        return apply_budget(row["call_id"], row["result"], policy=policy, ledger=ledger,
                            exit_code=row.get("exit_code"), read_kind=row.get("read_kind"),
                            receipt=row.get("receipt"), control=row.get("control", False), **kw)

    try:
        if not policy_available:
            raise RuntimeError("policy unavailable")
        outs = [run(r) for r in rows]
        if turn_budget is not None and sum(o.nbytes for o in outs) > turn_budget:
            fixed = sum(o.nbytes for o, r in zip(outs, rows) if r.get("control"))
            flexible = [i for i, r in enumerate(rows) if not r.get("control")]
            share = max(policy.min_row_cap, (turn_budget - fixed) // max(1, len(flexible)))
            for i in sorted(flexible, key=lambda i: -outs[i].nbytes):
                if sum(o.nbytes for o in outs) <= turn_budget:
                    break
                if outs[i].nbytes > share:
                    outs[i] = run(rows[i], cap_override=share)
        if aggregate is not None:
            aggregate(outs)
    except Exception as exc:  # fail closed: body withheld, note kept
        outs = [run(r, force="withheld") for r in rows]
        for o in outs:
            o.receipt["policy_error"] = type(exc).__name__
    if turn_budget is not None:
        total = sum(o.nbytes for o in outs)
        for o in outs:
            o.receipt["aggregate_bytes"] = total
            o.receipt["aggregate_unsatisfiable"] = total > turn_budget
    if ledger is not None:
        ledger.complete_batch(r["call_id"] for r in rows)
    return outs
