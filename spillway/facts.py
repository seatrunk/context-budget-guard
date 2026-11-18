"""Mandatory diagnostic facts that survive any cut: exit codes, source locations, and error clues."""
import json
import re
from typing import Any, Iterator, List, Optional

_EXIT = re.compile(r"(?:exit[ _]?code|returncode|exit status)[\"']?\s*[:=]?\s*(-?\d+)", re.IGNORECASE)

_EXT = (
    r"(?:py|pyi|ts|tsx|mts|cts|js|jsx|mjs|cjs|svelte|vue|astro|rs|go|c|cc|cpp|cxx|h|hpp|cs|"
    r"java|kt|kts|swift|scala|zig|ex|exs|erl|lua|dart|rb|php|pl|r|jl|hs|ml|mli|proto|graphql|"
    r"gql|sql|prisma|toml|yaml|yml|json|jsonc|xml|html|css|scss|cfg|ini|conf|env|sh|bash|zsh|"
    r"fish|ps1|cmake|mk|nix|tf|hcl)"
)
_NAMED = r"(?:Makefile|GNUmakefile|Dockerfile|Containerfile|Justfile|CMakeLists\.txt|BUILD(?:\.bazel)?|WORKSPACE|Rakefile|Gemfile)"
_FILE_TOKEN = r"(?:[\w./\-]+\." + _EXT + r"|(?:[\w./\-]+/)?" + _NAMED + r")"

_LOC = [
    # Python traceback: supports both raw File "x.py", line N and JSON-escaped File \"x.py\", line N
    re.compile(r'File \\?"([^"\\\n]+(?:\.' + _EXT + r"|(?:[/\\]|^)" + _NAMED + r'))\\?", line (\d+)'),
    # TypeScript / MSBuild style: src/view.ts(12,5)
    re.compile(r"(?<![\w./\-])(" + _FILE_TOKEN + r")\((\d+),(\d+)\)"),
    # GCC / Rustc / ESLint / SQL / Makefile style: path/file.ext:12[:5]
    re.compile(r"(?<![\w./\-])(" + _FILE_TOKEN + r"):(\d+)(?::(\d+))?"),
]

_CLUE = re.compile(
    r"^[ \t]*(?:FATAL|PANIC|panic|CRITICAL|ERROR|FAILED\b|[A-Z][A-Za-z0-9_]*(?:Error|Exception|Fault)\b)"
    r"[^\n]{0,160}",
    re.MULTILINE,
)


def _iter_json_strings(obj: Any) -> Iterator[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_json_strings(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_json_strings(item)


def _candidate_texts(text: str) -> List[str]:
    candidates = [text]
    stripped = text.lstrip()
    if stripped.startswith(("{", "[")):
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError, RecursionError):
            parsed = None
        if parsed is not None and not isinstance(parsed, str):
            unwrapped = "\n".join(_iter_json_strings(parsed))
            if unwrapped:
                candidates.append(unwrapped)
    return candidates


def exit_code_of(result: Any, explicit: Optional[int] = None) -> Optional[int]:
    if explicit is not None:
        return int(explicit)
    if isinstance(result, dict):
        for key in ("exit_code", "returncode", "exitCode"):
            val = result.get(key)
            if isinstance(val, int) and not isinstance(val, bool):
                return val
    return None


def error_locations(text: str, limit: int = 5) -> List[str]:
    """Unique ``file:line`` locations in appearance order; keeps the last ``limit`` frames."""
    seen = set()
    ordered: List[str] = []
    for chunk in _candidate_texts(text):
        found = []
        for pattern in _LOC:
            for m in pattern.finditer(chunk):
                found.append((m.start(), m.group(1) + ":" + m.group(2)))
        for _, loc in sorted(found):
            if loc not in seen:
                seen.add(loc)
                ordered.append(loc)
    return ordered[-limit:] if len(ordered) > limit else ordered


def diagnostic_clues(text: str, limit: int = 2, max_chars: int = 100) -> List[str]:
    """Short fatal/error lines preserved when no ``file:line`` location is present."""
    seen = set()
    clues: List[str] = []
    for chunk in _candidate_texts(text):
        for m in _CLUE.finditer(chunk):
            line = " ".join(m.group(0).strip().split())
            if len(line) > max_chars:
                line = line[: max_chars - 3] + "..."
            if line and line not in seen:
                seen.add(line)
                clues.append(line)
    return clues[-limit:] if len(clues) > limit else clues


def mentions_exit_code(text: str, code: int) -> bool:
    return any(int(m.group(1)) == code for m in _EXIT.finditer(text))
