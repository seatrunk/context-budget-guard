"""Offline repository checks. These do not exercise the external runtime prototype."""
from pathlib import Path
import re
import sys

from validate_benchmark import PRIVATE, validate_report
import json

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["README.md", "LICENSE", "SKILL.md", "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md",
            "docs/design.md", "docs/benchmarking.md", "docs/project-status.md", "docs/rollout.md",
            "docs/repository-governance.md", ".github/CODEOWNERS", ".github/PULL_REQUEST_TEMPLATE.md",
            ".github/ISSUE_TEMPLATE/config.yml", ".github/ISSUE_TEMPLATE/bug.yml",
            ".github/ISSUE_TEMPLATE/feature.yml", ".github/ISSUE_TEMPLATE/benchmark.yml",
            ".github/workflows/ci.yml", ".github/dependabot.yml"]


def check():
    errors = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append("missing " + relative)
    markdown = [path for path in ROOT.rglob("*.md") if ".git" not in path.parts]
    for path in markdown:
        text = path.read_text(encoding="utf-8")
        label = str(path.relative_to(ROOT))
        if PRIVATE.search(text):
            errors.append(label + ": private-path or credential-shaped text")
        for match in re.finditer(r"!?\[[^\]]*\]\(([^\s)]+)\)", text):
            target = match.group(1).split("#", 1)[0].split("?", 1)[0]
            if not target or re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                errors.append(label + ": unresolved local link " + target)
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        if re.search(r"^\s*pull_request_target\s*:", text, flags=re.M):
            errors.append("privileged pull_request_target workflow is not allowed")
        for reference in re.findall(r"\buses:\s*([^\s#]+)", text):
            if not re.fullmatch(r"[^@]+@[0-9a-f]{40}", reference):
                errors.append("action reference is not pinned to a full commit SHA")
    for path in (ROOT / "benchmarks/results").glob("*.json"):
        try:
            validate_report(json.loads(path.read_text(encoding="utf-8")))
        except (ValueError, TypeError, OverflowError, RecursionError):
            errors.append(str(path.relative_to(ROOT)) + ": invalid or unsanitized report")
    skill = ROOT / "SKILL.md"
    if skill.exists():
        text = skill.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            errors.append("SKILL.md: missing YAML frontmatter")
    return errors


if __name__ == "__main__":
    problems = check()
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        raise SystemExit(1)
    print("Repository files, local link targets, action pins and sanitized benchmark reports: OK")
    print("External URLs, link anchors, and full YAML schemas are not checked by this script.")
