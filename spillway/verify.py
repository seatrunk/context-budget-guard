"""Independent receipt verifier. Inspects only the final rendered output. Pure stdlib, no I/O.

Deliberately does not import budget.py or artifacts.py: depends only on render/sanitize/facts.
Returns a list of violation descriptions; an empty list means a valid receipt.
"""
import hashlib
from typing import Iterable, List, Optional

from .facts import mentions_exit_code
from .render import Rendered, rendered_bytes
from .sanitize import CLOSE, OPEN, count_delimiters


def note_tag(note_id: str) -> str:
    return "[note:" + note_id + "]"


def location_present(loc: str, text: str) -> bool:
    """True if ``file:line`` appears in ``text`` in any form the extractor accepts.

    Forms: ``file:line[:col]`` (GCC/Rust/ESLint), ``file(line,col)`` (TypeScript/MSBuild) and
    ``File "file", line N`` (Python), raw or JSON-escaped. A full (uncut) body keeps the original
    form, so requiring the normalized ``file:line`` string would wrongly fail closed.
    """
    if loc in text:
        return True
    path, sep, line = loc.rpartition(":")
    if not sep:
        return False
    return (
        (path + "(" + line + ",") in text
        or ('"%s", line %s' % (path, line)) in text
        or ('\\"%s\\", line %s' % (path, line)) in text
    )


def sha256_of(rendered: Rendered) -> str:
    return hashlib.sha256(rendered.model_text().encode("utf-8")).hexdigest()


def verify(rendered: Rendered, *, cap: Optional[int], exit_code: Optional[int] = None,
           error_locations: Iterable[str] = (), note_ids: Iterable[str] = (),
           receipt: Optional[dict] = None) -> List[str]:
    problems: List[str] = []
    text = rendered.model_text()
    size = rendered_bytes(rendered)
    if cap is not None and size > cap:
        problems.append("cap: %d > %d bytes" % (size, cap))
    if receipt is not None:
        if receipt.get("rendered_bytes") != size:
            problems.append("receipt: rendered_bytes %r != measured %d" % (receipt.get("rendered_bytes"), size))
        if receipt.get("rendered_sha256") != sha256_of(rendered):
            problems.append("receipt: sha256 mismatch with rendered output")
    if count_delimiters(text) != 2 or text.count(OPEN) != 1 or text.count(CLOSE) != 1:
        problems.append("wrapper: ambiguous delimiters")
    if exit_code is not None and not mentions_exit_code(text, exit_code):
        problems.append("fact: missing exit_code=%d" % exit_code)
    for loc in error_locations:
        if not location_present(loc, text):
            problems.append("fact: missing location %s" % loc)
    outside = _outside_wrapper(rendered)
    for nid in note_ids:
        tag = note_tag(nid)
        if text.count(tag) != 1:
            problems.append("note %s: %d occurrences" % (nid, text.count(tag)))
        elif tag not in outside:
            problems.append("note %s: inside untrusted wrapper" % nid)
    return problems


def _outside_wrapper(rendered: Rendered) -> str:
    if rendered.kind == "text":
        return rendered.payload.rsplit(CLOSE, 1)[-1]
    return "\n".join(
        p.get("text", "") for p in rendered.payload[1:] if isinstance(p, dict) and p.get("type") == "text"
    )
