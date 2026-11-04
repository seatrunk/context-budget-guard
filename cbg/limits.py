"""Limit units: effective LF lines and UTF-8 bytes. No I/O."""


def utf8_bytes(text: str) -> int:
    return len(text.encode("utf-8"))


def effective_lines(text: str) -> int:
    """Linhas LF efetivas: "" -> 0; "a" -> 1; "a\\n" -> 1; "a\\nb" -> 2; "\\n" -> 1.

    Only LF counts as a separator; a lone CR does not start a new line.
    """
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def head_lines(text: str, n: int) -> str:
    """First ``n`` effective lines, keeping the original LFs."""
    if n <= 0:
        return ""
    pos = -1
    for _ in range(n):
        pos = text.find("\n", pos + 1)
        if pos < 0:
            return text
    return text[: pos + 1]


def utf8_truncate(text: str, max_bytes: int) -> str:
    """Longest prefix of ``text`` with at most ``max_bytes`` UTF-8 bytes, without splitting a code point."""
    if max_bytes <= 0:
        return ""
    data = text.encode("utf-8")
    if len(data) <= max_bytes:
        return text
    cut = max_bytes
    while cut > 0 and (data[cut] & 0xC0) == 0x80:  # data[cut] is a continuation byte
        cut -= 1
    return data[:cut].decode("utf-8")


def utf8_tail(text: str, max_bytes: int) -> str:
    """Longest suffix with at most ``max_bytes`` UTF-8 bytes, without splitting a code point."""
    if max_bytes <= 0:
        return ""
    data = text.encode("utf-8")
    if len(data) <= max_bytes:
        return text
    start = len(data) - max_bytes
    while start < len(data) and (data[start] & 0xC0) == 0x80:
        start += 1
    return data[start:].decode("utf-8")
