"""Mandatory facts that survive any cut: exit code and error location."""
import re
from typing import Any, List, Optional

_EXIT = re.compile(r"(?:exit[ _]?code|returncode|exit status)[\"']?\s*[:=]?\s*(-?\d+)", re.IGNORECASE)
_EXT = r"(?:py|pyi|ts|tsx|js|jsx|mjs|cjs|rs|go|c|cc|cpp|h|hpp|java|kt|rb|php|sql|toml|yaml|yml|json|cfg|ini|sh)"
# path:line[:col] (gcc/rustc/tsc/eslint/pytest), File "x.py", line N (traceback), x.ts(12,5) (tsc)
_LOC = [
    re.compile(r"File \"([^\"\n]+\." + _EXT + r")\", line (\d+)"),
    # the lookbehind anchors at the start of a token: avoids quadratic backtracking on long runs.
    re.compile(r"(?<![\w./\-])([\w./\-]+\." + _EXT + r")\((\d+),(\d+)\)"),
    re.compile(r"(?<![\w./\-])([\w./\-]+\." + _EXT + r"):(\d+)(?::(\d+))?"),
]


def exit_code_of(result: Any, explicit: Optional[int] = None) -> Optional[int]:
    if explicit is not None:
        return int(explicit)
    if isinstance(result, dict):
        for key in ("exit_code", "returncode", "exitCode"):
            if isinstance(result.get(key), int):
                return result[key]
    return None


def error_locations(text: str, limit: int = 5) -> List[str]:
    """Unique ``file:line`` locations in order of appearance; when there are more than ``limit``,
    keeps the last ones (in a traceback the relevant frame is the last)."""
    found = []
    for pattern in _LOC:
        for m in pattern.finditer(text):
            found.append((m.start(), m.group(1) + ":" + m.group(2)))
    seen, ordered = set(), []
    for _, loc in sorted(found):
        if loc not in seen:
            seen.add(loc)
            ordered.append(loc)
    return ordered[-limit:] if len(ordered) > limit else ordered


def mentions_exit_code(text: str, code: int) -> bool:
    return any(int(m.group(1)) == code for m in _EXIT.finditer(text))
