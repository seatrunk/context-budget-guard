"""Neutralizes trust-wrapper delimiters and reserved header tags (issue #8). Pure stdlib, no I/O."""
import re

WRAPPER = "untrusted_tool_result"
OPEN = "<" + WRAPPER + ">"
CLOSE = "</" + WRAPPER + ">"

# Matches any case/whitespace variant of <untrusted_tool_result...> or </ untrusted_tool_result>.
_DELIM = re.compile(r"<(\s*/?\s*)(untrusted_tool_result)", re.IGNORECASE)
_RESERVED_TAG = re.compile(r"\[(note:|spillway\b|cbg\b)", re.IGNORECASE)


def neutralize(text: str) -> str:
    """Replaces the leading '<' of each literal wrapper delimiter with '&lt;'.

    Deterministic and idempotent; keeps text readable while ensuring it never matches OPEN/CLOSE.
    """
    return _DELIM.sub(lambda m: "&lt;" + m.group(1) + m.group(2), text)


def count_delimiters(text: str) -> int:
    return len(_DELIM.findall(text))


def neutralize_body(text: str) -> str:
    """Neutralizes untrusted tool body text against wrapper escape and note/header tag forgery."""
    text = neutralize(text)
    return _RESERVED_TAG.sub(lambda m: "[untrusted-" + m.group(1), text)
