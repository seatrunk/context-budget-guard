"""Canonical rendering and measurement of the final bytes the model sees.

A single function produces what is delivered and what is measured: there is no "estimate".

Accepted result shapes:
- ``str``: tool text.
- ``dict`` multimodal: ``{"_multimodal": True, "content": [parts...], "text_summary": ...}``
  with parts ``{"type": "text", "text": ...}`` or media (``image_url``, ``image``, ...).

Rendered format:
- text: ``<untrusted_tool_result>\\n{body}\\n</untrusted_tool_result>`` + note suffix.
- multimodal: a JSON list of parts; the body text is wrapped in the first text part,
  media keeps its order, and notes become the LAST text part, outside the wrapper (issue #3).

Measure: text -> UTF-8 bytes; multimodal -> UTF-8 bytes of ``json.dumps(parts)`` (real JSON
escaping, including control characters), with the media payload counted as a fixed marker, because
media is not context text and is preserved as-is (decision recorded in the README).
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
    payload: Any  # str or list[dict]
    media: List[dict] = field(default_factory=list)

    def model_text(self) -> str:
        """Canonical text used for measuring and verifying."""
        if self.kind == "text":
            return self.payload
        return json.dumps(_measurable(self.payload), ensure_ascii=False, separators=(",", ":"))


def is_multimodal(result: Any) -> bool:
    return isinstance(result, dict) and result.get("_multimodal") is True


def split_result(result: Any):
    """Returns (body_text, media_parts_in_order, kind)."""
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
    # structured non-multimodal dict/list (probe P1): deterministic serialization, no .encode on a hash.
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
    """Bytes of the render with an empty body: framing + escaping + suffix + media."""
    return rendered_bytes(render("", kind, note_texts, media))
