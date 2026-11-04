"""Neutralizes trust-wrapper delimiters (issue #8)."""
import re

WRAPPER = "untrusted_tool_result"
OPEN = "<" + WRAPPER + ">"
CLOSE = "</" + WRAPPER + ">"
# Any case/whitespace variant of <untrusted_tool_result ...> or </ untrusted_tool_result>.
_DELIM = re.compile(r"<(\s*/?\s*)(untrusted_tool_result)", re.IGNORECASE)


def neutralize(text: str) -> str:
    """Replaces the '<' of each literal delimiter with '&lt;'.

    Deterministic and idempotent; the text stays readable and never matches OPEN/CLOSE.
    """
    return _DELIM.sub(lambda m: "&lt;" + m.group(1) + m.group(2), text)


def count_delimiters(text: str) -> int:
    return len(_DELIM.findall(text))


def neutralize_body(text: str) -> str:
    """Untrusted body: besides delimiters, prevents forging cbg note/receipt tags."""
    text = neutralize(text)
    return re.sub(r"\[(note:|cbg)", lambda m: "[untrusted-" + m.group(1), text)
