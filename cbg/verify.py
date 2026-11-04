"""Verificador independente do recibo. Lê só a saída final renderizada.

Não importa o limitador (budget.py) de propósito: só limits/render/sanitize/facts para ler o texto.
Retorna a lista de violações; lista vazia = recibo válido.
"""
import hashlib
from typing import Iterable, List, Optional

from .facts import mentions_exit_code
from .render import Rendered, rendered_bytes
from .sanitize import CLOSE, OPEN, count_delimiters


def note_tag(note_id: str) -> str:
    return "[note:" + note_id + "]"


def sha256_of(rendered: Rendered) -> str:
    return hashlib.sha256(rendered.model_text().encode("utf-8")).hexdigest()


def verify(rendered: Rendered, *, cap: Optional[int], exit_code: Optional[int] = None,
           error_locations: Iterable[str] = (), note_ids: Iterable[str] = (),
           receipt: Optional[dict] = None) -> List[str]:
    problems: List[str] = []
    text = rendered.model_text()
    size = rendered_bytes(rendered)
    if cap is not None and size > cap:
        problems.append("teto: %d > %d bytes" % (size, cap))
    if receipt is not None:
        if receipt.get("rendered_bytes") != size:
            problems.append("recibo: rendered_bytes %r != medido %d" % (receipt.get("rendered_bytes"), size))
        if receipt.get("rendered_sha256") != sha256_of(rendered):
            problems.append("recibo: sha256 diverge do renderizado")
    if count_delimiters(text) != 2 or text.count(OPEN) != 1 or text.count(CLOSE) != 1:
        problems.append("wrapper: delimitadores ambíguos")
    if exit_code is not None and not mentions_exit_code(text, exit_code):
        problems.append("fato: exit_code=%d ausente" % exit_code)
    for loc in error_locations:
        if loc not in text:
            problems.append("fato: local %s ausente" % loc)
    outside = _outside_wrapper(rendered)
    for nid in note_ids:
        tag = note_tag(nid)
        if text.count(tag) != 1:
            problems.append("nota %s: %d ocorrências" % (nid, text.count(tag)))
        elif tag not in outside:
            problems.append("nota %s: dentro do wrapper" % nid)
    return problems


def _outside_wrapper(rendered: Rendered) -> str:
    if rendered.kind == "text":
        return rendered.payload.rsplit(CLOSE, 1)[-1]
    return "\n".join(p.get("text", "") for p in rendered.payload[1:] if isinstance(p, dict) and p.get("type") == "text")
