"""Limit units: effective LF lines and UTF-8 byte slicing. Pure stdlib, no I/O."""
from typing import Tuple


def utf8_bytes(text: str) -> int:
    return len(text.encode("utf-8"))


def effective_lines(text: str) -> int:
    """Effective LF lines: "" -> 0; "a" -> 1; "a\\n" -> 1; "a\\nb" -> 2; "\\n" -> 1.

    Only LF counts as a line separator; a lone CR does not start a new line.
    """
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def head_lines(text: str, n: int) -> str:
    """First ``n`` effective LF lines, preserving original line endings."""
    if n <= 0:
        return ""
    pos = -1
    for _ in range(n):
        pos = text.find("\n", pos + 1)
        if pos < 0:
            return text
    return text[: pos + 1]


def utf8_truncate(text: str, max_bytes: int) -> str:
    """Longest prefix of ``text`` within ``max_bytes`` UTF-8 bytes without splitting a code point."""
    if max_bytes <= 0:
        return ""
    data = text.encode("utf-8")
    if len(data) <= max_bytes:
        return text
    cut = max_bytes
    while cut > 0 and (data[cut] & 0xC0) == 0x80:
        cut -= 1
    return data[:cut].decode("utf-8")


def utf8_tail(text: str, max_bytes: int) -> str:
    """Longest suffix of ``text`` within ``max_bytes`` UTF-8 bytes without splitting a code point."""
    if max_bytes <= 0:
        return ""
    data = text.encode("utf-8")
    if len(data) <= max_bytes:
        return text
    start = len(data) - max_bytes
    while start < len(data) and (data[start] & 0xC0) == 0x80:
        start += 1
    return data[start:].decode("utf-8")


def snap_head(head: str) -> str:
    """Drops a trailing partial line from a cut prefix when that keeps at least half of it."""
    cut = head.rfind("\n")
    return head[: cut + 1] if cut >= 0 and cut + 1 >= len(head) // 2 else head


def snap_tail(tail: str) -> str:
    """Drops a leading partial line from a cut suffix when that keeps at least half of it."""
    cut = tail.find("\n")
    return tail[cut + 1 :] if 0 <= cut < len(tail) // 2 else tail


def utf8_slice(data: bytes, offset: int = 0, limit: int = 8192) -> Tuple[str, int, bool]:
    """UTF-8-safe byte window returning ``(decoded_text, next_offset, eof)``.

    Advances ``offset`` past any leading UTF-8 continuation bytes and trims ``end``
    before any split multi-byte sequence so sequential ``next_offset`` reads are lossless.
    """
    total = len(data)
    start = max(0, min(offset, total))
    while start < total and (data[start] & 0xC0) == 0x80:
        start += 1
    if limit <= 0 or start >= total:
        return "", start, start >= total
    end = min(total, start + limit)
    if end < total:
        while end > start and (data[end] & 0xC0) == 0x80:
            end -= 1
        if end == start:
            # ``limit`` is smaller than the code point at ``start``: return that whole code point
            # (at most 3 bytes over ``limit``) so sequential reads always make progress.
            end = start + 1
            while end < total and (data[end] & 0xC0) == 0x80:
                end += 1
    chunk = data[start:end].decode("utf-8", errors="replace")
    return chunk, end, end >= total
