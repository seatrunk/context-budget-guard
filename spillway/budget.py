"""Core tool-output limiter and water-filling batch settler. Pure stdlib, no I/O.

The complete unredacted payload is returned in ``Outcome.artifact`` when output is cut so an
adapter can persist it privately; the core only computes sizes, hashes, previews, and receipts.
"""
from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional

from . import facts as _facts
from .limits import effective_lines, head_lines, snap_head, snap_tail, utf8_bytes, utf8_tail, utf8_truncate
from .notes import NoteLedger
from .render import Rendered, render, rendered_bytes, split_result
from .sanitize import neutralize, neutralize_body
from .verify import note_tag, sha256_of, verify

MIN_RESULT_CAP = 256
DEFAULT_ARTIFACT_HINT = "artifact sha256={sha256} (read with offset/limit)"


@dataclass(frozen=True)
class Policy:
    result_cap: int = 16384
    full_read_lines: int = 350
    partial_read_lines: int = 150
    note_cap: int = 4096
    note_batch_cap: int = 8192
    max_locations: int = 5
    min_row_cap: int = 1024  # floor per flexible row during aggregate batch settlement


@dataclass
class Receipt:
    """Single-use approved-read receipt (#7), bound to exact call ID and session."""
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
    """Maps eligible notes to ``(visible_lines, shown_ids, marker_only_ids)``."""
    if ledger is None:
        return [], [], []
    texts, shown, marked, used = [], [], [], 0
    for note in ledger.eligible(call_id):
        body = neutralize(_clean_text(note.text))
        if utf8_bytes(body) > policy.note_cap:
            body = (
                utf8_truncate(body, max(0, policy.note_cap - 64))
                + " [spillway: note truncated from %d bytes]" % utf8_bytes(_clean_text(note.text))
            )
        line = note_tag(note.note_id) + " " + body
        if used + utf8_bytes(line) > policy.note_batch_cap:
            marked.append(note.note_id)
            continue
        used += utf8_bytes(line)
        texts.append(line)
        shown.append(note.note_id)
    if marked:
        texts.append("[spillway: %d note(s) over note budget: %s]" % (len(marked), ",".join(marked)))
    return texts, shown, marked


def _note_marker(shown: List[str], marked: List[str]) -> List[str]:
    ids = shown + marked
    return ["[spillway: %d note(s) existed and were withheld: %s]" % (len(ids), ",".join(ids))] if ids else []


def _header(mode: str, orig: str, exit_code: Optional[int], locs: List[str], clues: List[str],
            art_sha: str, artifact_hint: str) -> str:
    parts = ["[spillway %s] original %d bytes, %d lines" % (mode, utf8_bytes(orig), effective_lines(orig))]
    if exit_code is not None:
        parts.append("exit_code=%d" % exit_code)
    if locs:
        parts.append("errors: " + ", ".join(locs))
    elif clues:
        parts.append("clues: " + " | ".join(clues))
    parts.append(artifact_hint.format(sha256=art_sha, sha256_short=art_sha[:16]))
    return "; ".join(parts) + "\n"


def apply_budget(call_id: str, result: Any, *, policy: Policy = Policy(), ledger: Optional[NoteLedger] = None,
                 exit_code: Optional[int] = None, read_kind: Optional[str] = None,
                 receipt: Optional[Receipt] = None, session_id: Optional[str] = None,
                 cap_override: Optional[int] = None, force: Optional[str] = None,
                 control: bool = False, artifact_hint: Optional[str] = None) -> Outcome:
    """Applies per-result line and byte budgets to a single tool result.

    ``force``: ``"withheld"`` (policy/aggregate failure: body withheld, notes preserved) or ``None``.
    """
    raw_body, media, kind = split_result(result)
    raw_body = _clean_text(raw_body)
    code = _facts.exit_code_of(result, exit_code)
    # Facts come from the raw body but are shown inside model-visible text: neutralize them exactly
    # like the body, so a path such as /p/[cbg]/a.py cannot forge a tag nor fail verification.
    locs = [neutralize_body(loc) for loc in _facts.error_locations(raw_body, policy.max_locations)]
    clues = [] if locs else [neutralize_body(c) for c in _facts.diagnostic_clues(raw_body)]
    artifact = raw_body if not media else _clean_text(
        raw_body + "\n" + json.dumps(media, ensure_ascii=False, sort_keys=True))
    art_sha = _sha(artifact)
    body = neutralize_body(raw_body)
    note_texts, shown, marked = _prepare_notes(ledger, call_id, policy)
    sid = session_id if session_id is not None else (ledger.session_id if ledger else "")
    hint = artifact_hint or DEFAULT_ARTIFACT_HINT

    cap: Optional[int] = max(MIN_RESULT_CAP, policy.result_cap)
    line_limit = {"full": policy.full_read_lines, "partial": policy.partial_read_lines}.get(read_kind or "")
    receipt_used = False
    if receipt is not None and receipt.admits(call_id, sid):
        cap = max(cap, receipt.max_bytes)
        line_limit = receipt.max_lines
        receipt.consumed_by = call_id
        receipt_used = True
    if cap_override is not None and not receipt_used:
        cap = min(cap, max(MIN_RESULT_CAP, cap_override))
    if control:
        cap, line_limit = None, None

    fact_line = "" if code is None or _facts.mentions_exit_code(body, code) else "[spillway] exit_code=%d\n" % code

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
            header = _header("preview", raw_body, code, locs, clues, art_sha, hint)
            src = head_lines(body, line_limit) if line_limit is not None else body
            sep = "\n[...]" if line_limit is not None else "\n[...]\n"
            budget = cap - rendered_bytes(render(header + sep, kind, note_texts, media))
            # Raw body bytes can never exceed ``budget`` in a fitting preview, so bounded prefixes and
            # suffixes keep each attempt O(cap) instead of re-encoding a huge body every iteration.
            src_p = src if len(src) <= budget else src[: max(budget, 0) + 1]
            body_t = body if len(body) <= budget else body[-(max(budget, 0) + 1):]

            def build(b: int) -> Rendered:
                head = _cut_head(src_p, b if line_limit is not None else b * 2 // 3)
                joiner = sep[1:] if head.endswith("\n") else sep
                if line_limit is not None:
                    return render(header + head + joiner, kind, note_texts, media)
                tail = utf8_tail(body_t, b - utf8_bytes(head))
                if tail != body_t:
                    tail = snap_tail(tail)
                return render(header + head + joiner + tail, kind, note_texts, media)

            if budget > 0 and kind == "text":
                for _ in range(64):  # text bytes map 1:1, so subtracting the exact excess converges
                    if budget <= 0:
                        break
                    candidate = build(budget)
                    excess = rendered_bytes(candidate) - cap
                    if excess <= 0:
                        mode, rendered = "preview", candidate
                        break
                    budget -= excess
            elif budget > 0:
                # Multimodal JSON escaping grows bytes non-linearly (e.g. '"' -> '\\"', '\\x01' -> '\\u0001'):
                # binary-search the largest raw budget whose complete render fits.
                lo, hi = 1, budget
                while lo <= hi:
                    mid = (lo + hi) // 2
                    candidate = build(mid)
                    if rendered_bytes(candidate) <= cap:
                        mode, rendered = "preview", candidate
                        lo = mid + 1
                    else:
                        hi = mid - 1
    if rendered is None:
        mode = "withheld" if force == "withheld" else "marker"
        header = _header(mode, raw_body, code, locs, clues, art_sha, hint)
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
        "call_id": call_id,
        "mode": mode,
        "kind": kind,
        "cap": cap,
        "rendered_bytes": rendered_bytes(rendered),
        "rendered_sha256": sha256_of(rendered),
        "original_bytes": utf8_bytes(raw_body),
        "original_lines": effective_lines(raw_body),
        "exit_code": code,
        "error_locations": locs,
        "diagnostic_clues": clues,
        "notes_shown": shown,
        "notes_marked": marked,
        "media_parts": len(media),
        "artifact_sha256": art_sha,
        "artifact_bytes": utf8_bytes(artifact),
        "receipt_used": receipt_used,
    }
    required_locs = locs if mode in ("full", "preview", "control", "marker", "withheld") else []
    violations = verify(
        rendered,
        cap=cap,
        exit_code=code if mode != "failclosed" else None,
        error_locations=required_locs,
        note_ids=shown,
        receipt=rec,
    )
    if violations and mode != "failclosed":
        rendered = _failclosed(cap, kind)
        mode = "failclosed"
        marked, shown = shown + marked, []
        rec.update(
            mode=mode,
            rendered_bytes=rendered_bytes(rendered),
            rendered_sha256=sha256_of(rendered),
            notes_shown=[],
            notes_marked=marked,
        )
    rec["verified"] = not verify(rendered, cap=cap, receipt=rec)
    rec["violations_before_failclose"] = violations
    if ledger is not None:
        ledger.bind(call_id, shown + marked, rec["rendered_sha256"])
    return Outcome(
        call_id,
        rendered,
        mode,
        rec,
        artifact if mode not in ("full", "control") else None,
        violations,
    )


def _clean_text(text: str) -> str:
    """Replaces lone surrogates (unencodable in UTF-8) so measurement and storage never raise."""
    try:
        text.encode("utf-8")
        return text
    except UnicodeEncodeError:
        return text.encode("utf-8", "replace").decode("utf-8")


def _cut_head(src: str, max_bytes: int) -> str:
    head = utf8_truncate(src, max_bytes)
    return snap_head(head) if head != src else head


def _failclosed(cap: Optional[int], kind: str) -> Rendered:
    text = "[spillway] result withheld: could not be bounded and verified within cap"
    r = render(text, kind)
    while cap is not None and rendered_bytes(r) > cap and text:
        text = text[:-1]
        r = render(text, kind)
    return r


def _waterfill_caps(sizes: Dict[int, int], available: int, floor: int) -> Dict[int, int]:
    """Computes per-row caps across ``sizes`` so small rows keep their size and only oversized rows shrink."""
    if not sizes:
        return {}
    ordered = sorted(sizes.items(), key=lambda kv: kv[1])
    rem_budget = available
    rem_count = len(ordered)
    caps: Dict[int, int] = {}
    for idx, (_, size) in enumerate(ordered):
        share = max(floor, rem_budget // rem_count)
        if size <= share:
            rem_budget -= size
            rem_count -= 1
        else:
            for j in range(idx, len(ordered)):
                caps[ordered[j][0]] = share
            break
    return caps


def finalize_batch(rows: List[Dict[str, Any]], *, ledger: Optional[NoteLedger] = None, policy: Policy = Policy(),
                   turn_budget: Optional[int] = None, policy_available: bool = True,
                   aggregate: Optional[Callable[[List[Outcome]], None]] = None,
                   artifact_hint: Optional[str] = None) -> List[Outcome]:
    """Settles a batch of tool results with water-filling aggregate turn budgeting.

    - Pass 1: per-result budget on every row.
    - Pass 2 (if ``turn_budget`` exceeded): treats ``control`` and approved-``Receipt`` rows as fixed,
      computes water-filling caps for flexible rows so small rows do not waste budget, and shrinks
      largest rows first while rolling forward any unused slack.
    - Policy/aggregate failure: every row becomes ``withheld`` with owned notes preserved; never re-runs tools.
    - ``complete_batch`` runs only after the final settlement (B3).
    """
    def run(row, **kw):
        return apply_budget(
            row["call_id"],
            row["result"],
            policy=policy,
            ledger=ledger,
            exit_code=row.get("exit_code"),
            read_kind=row.get("read_kind"),
            receipt=row.get("receipt"),
            control=row.get("control", False),
            artifact_hint=row.get("artifact_hint", artifact_hint),
            **kw,
        )

    try:
        if not policy_available:
            raise RuntimeError("policy unavailable")
        outs = [run(r) for r in rows]
        if turn_budget is not None and sum(o.nbytes for o in outs) > turn_budget:
            is_fixed = [bool(r.get("control")) or bool(o.receipt.get("receipt_used")) for o, r in zip(outs, rows)]
            fixed_bytes = sum(o.nbytes for o, fx in zip(outs, is_fixed) if fx)
            flex_sizes = {i: outs[i].nbytes for i, fx in enumerate(is_fixed) if not fx}
            caps = _waterfill_caps(flex_sizes, turn_budget - fixed_bytes, policy.min_row_cap)
            to_shrink = sorted(caps, key=lambda i: -outs[i].nbytes)
            rem_slack = 0
            for pos, i in enumerate(to_shrink):
                if sum(o.nbytes for o in outs) <= turn_budget:
                    break
                left = len(to_shrink) - pos
                target = caps[i] + (rem_slack // left if left > 0 else 0)
                if outs[i].nbytes > target:
                    outs[i] = run(rows[i], cap_override=target)
                    saved_below_target = max(0, target - outs[i].nbytes)
                    rem_slack = max(0, rem_slack - (rem_slack // left if left > 0 else 0)) + saved_below_target
        if aggregate is not None:
            aggregate(outs)
    except Exception as exc:  # fail closed: withhold untrusted body, preserve owned notes
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
