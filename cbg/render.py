"""Renderização canônica e medição dos bytes finais que o modelo vê.

Uma única função gera o que é entregue e o que é medido: não existe "estimativa".

Formas de resultado aceitas:
- ``str``: texto de ferramenta.
- ``dict`` multimodal: ``{"_multimodal": True, "content": [parts...], "text_summary": ...}``
  com parts ``{"type": "text", "text": ...}`` ou mídia (``image_url``, ``image``, ...).

Formato renderizado:
- texto: ``<untrusted_tool_result>\\n{body}\\n</untrusted_tool_result>`` + sufixo de notas.
- multimodal: lista JSON de parts; o texto do corpo vai embrulhado na primeira part de texto,
  mídia mantém a ordem, e as notas viram a ÚLTIMA part de texto, fora do wrapper (issue #3).

Medida: texto -> bytes UTF-8; multimodal -> bytes UTF-8 de ``json.dumps(parts)`` (escaping JSON
real, inclusive de controles), com o payload de mídia contado por um marcador fixo, porque mídia
não é texto de contexto e é preservada como está (decisão registrada no README).
"""
from dataclasses import dataclass, field
import json
from typing import Any, List, Optional

from .sanitize import CLOSE, OPEN

MEDIA_PLACEHOLDER = "<media>"
NOTE_HEADER = "[cbg notes]"


@dataclass(frozen=True)
class Rendered:
    kind: str  # "text" | "multimodal"
    payload: Any  # str ou list[dict]
    media: List[dict] = field(default_factory=list)

    def model_text(self) -> str:
        """Texto canônico usado para medir e verificar."""
        if self.kind == "text":
            return self.payload
        return json.dumps(_measurable(self.payload), ensure_ascii=False, separators=(",", ":"))


def is_multimodal(result: Any) -> bool:
    return isinstance(result, dict) and result.get("_multimodal") is True


def split_result(result: Any):
    """Retorna (texto_do_corpo, partes_de_mídia_em_ordem, kind)."""
    if is_multimodal(result):
        texts, media = [], []
        for part in result.get("content") or []:
            if isinstance(part, dict) and part.get("type") == "text":
                texts.append(str(part.get("text", "")))
            else:
                media.append(part)
        if not texts and result.get("text_summary"):
            texts.append(str(result["text_summary"]))
        return "\n".join(texts), media, "multimodal"
    if isinstance(result, str):
        return result, [], "text"
    # dict/list estruturado não multimodal (probe P1): serialização determinística, sem .encode em hash.
    return json.dumps(result, ensure_ascii=False, sort_keys=True, default=str), [], "text"


def note_suffix(note_texts: List[str]) -> str:
    if not note_texts:
        return ""
    return "\n" + NOTE_HEADER + "\n" + "\n".join(note_texts)


def render(body: str, kind: str, note_texts: Optional[List[str]] = None,
           media: Optional[List[dict]] = None) -> Rendered:
    note_texts = list(note_texts or [])
    wrapped = OPEN + "\n" + body + "\n" + CLOSE
    if kind == "text":
        return Rendered("text", wrapped + note_suffix(note_texts))
    parts: List[dict] = [{"type": "text", "text": wrapped}]
    parts.extend(media or [])
    if note_texts:
        parts.append({"type": "text", "text": note_suffix(note_texts).lstrip("\n")})
    return Rendered("multimodal", parts, list(media or []))


def _measurable(parts: List[dict]) -> List[dict]:
    out = []
    for part in parts:
        if isinstance(part, dict) and part.get("type") == "text":
            out.append(part)
        else:
            out.append({"type": (part or {}).get("type", "media") if isinstance(part, dict) else "media",
                        "media": MEDIA_PLACEHOLDER})
    return out


def rendered_bytes(rendered: Rendered) -> int:
    return len(rendered.model_text().encode("utf-8"))


def overhead_bytes(kind: str, note_texts: List[str], media: List[dict]) -> int:
    """Bytes do render com corpo vazio: framing + escaping + sufixo + mídia."""
    return rendered_bytes(render("", kind, note_texts, media))
