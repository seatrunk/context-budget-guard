"""Canonical rendering and exact measurement of final model-visible bytes. Pure stdlib, no I/O.

A single function produces both what is delivered and what is measured—never an estimate.

Accepted result shapes:
- ``str``: plain tool text.
- ``dict`` multimodal: ``{"_multimodal": True, "content": [parts...], "text_summary": ...}``
  with ``{"type": "text", "text": ...}`` or media parts (``image_url``, ``image``, etc.).
- other ``dict``/``list``: deterministic JSON serialization.

Rendered format:
- text: ``<untrusted_tool_result>\\n{body}\\n</untrusted_tool_result>`` + optional note suffix.
- multimodal: JSON list of parts; body text wrapped in the first text part, media preserved in
  original order, and notes placed in the LAST text part outside the wrapper (issue #3).
"""
from dataclasses import dataclass, field
import json
from typing import Any, List, Optional

from .sanitize import CLOSE, OPEN

MEDIA_PLACEHOLDER = "<media>"
NOTE_HEADER = "[spillway notes]"


def _strip_wrapper(wrapped_text: str) -> str:
    if wrapped_text.startswith(OPEN + "\n"):
        rest = wrapped_text[len(OPEN) + 1 :]
        end = rest.rfind("\n" + CLOSE)
        if end >= 0:
            return rest[:end] + rest[end + len(CLOSE) + 1 :]
    return wrapped_text


@dataclass(frozen=True)
class Rendered:
    kind: str  # "text" | "multimodal"
    payload: Any  # str or list[dict]
    media: List[dict] = field(default_factory=list)

    def model_text(self) -> str:
        """Canonical string representation measured against byte ceilings and checked by verify()."""
        if self.kind == "text":
            return self.payload
        return json.dumps(_measurable(self.payload), ensure_ascii=False, separators=(",", ":"))

    def unwrapped_payload(self) -> Any:
        """Returns payload without outer ``<untrusted_tool_result>`` tags for hosts that wrap externally."""
        if self.kind == "text":
            return _strip_wrapper(self.payload)
        if not self.payload:
            return []
        first = self.payload[0]
        if isinstance(first, dict) and first.get("type") == "text":
            first = dict(first, text=_strip_wrapper(str(first.get("text", ""))))
        return [first, *self.payload[1:]]


def is_multimodal(result: Any) -> bool:
    return isinstance(result, dict) and result.get("_multimodal") is True


def split_result(result: Any):
    """Returns ``(body_text, media_parts_in_order, kind)``."""
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
            out.append({
                "type": (part or {}).get("type", "media") if isinstance(part, dict) else "media",
                "media": MEDIA_PLACEHOLDER,
            })
    return out


def rendered_bytes(rendered: Rendered) -> int:
    return len(rendered.model_text().encode("utf-8"))


def overhead_bytes(kind: str, note_texts: List[str], media: List[dict]) -> int:
    """Rendered UTF-8 bytes with an empty body: framing + JSON escaping + note suffix + media markers."""
    return rendered_bytes(render("", kind, note_texts, media))
