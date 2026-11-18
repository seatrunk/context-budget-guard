"""Adapter-side private artifact storage, JSONL logging, retention pruning, and paginated recovery.

Note: Core budgeting modules (limits, sanitize, facts, render, notes, budget, verify) are pure
and perform zero I/O. This module centralizes hardened filesystem operations for runtime adapters.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
from typing import Any, Dict, Optional

from .limits import utf8_slice

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_NONBLOCK = getattr(os, "O_NONBLOCK", 0)  # a FIFO planted at an artifact path must not block open()

DEFAULT_MAX_ARTIFACTS = 200
DEFAULT_MAX_ARTIFACT_BYTES = 100 * 1024 * 1024  # 100 MiB


def is_valid_sha256(value: str) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.fullmatch(value))


def _ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix" and not path.is_symlink():
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass


def _fchmod_private(fd: int) -> None:
    if hasattr(os, "fchmod"):
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass


class ArtifactStore:
    """Manages ``receipts.jsonl``, ``errors.jsonl``, and content-addressed ``artifacts/<sha256>.txt``."""

    def __init__(
        self,
        root_dir: Path,
        *,
        max_artifacts: int = DEFAULT_MAX_ARTIFACTS,
        max_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
    ):
        self.root_dir = Path(root_dir).expanduser()
        self.artifacts_dir = self.root_dir / "artifacts"
        self.max_artifacts = max(1, int(max_artifacts))
        self.max_bytes = max(1024, int(max_bytes))

    def artifact_path(self, sha256: str) -> Path:
        if not is_valid_sha256(sha256):
            raise ValueError("invalid artifact sha256")
        return self.artifacts_dir / (sha256 + ".txt")

    def append_jsonl(self, filename: str, line: str) -> None:
        if "/" in filename or "\\" in filename or filename in ("", ".", ".."):
            raise ValueError("invalid log filename")
        _ensure_private_dir(self.root_dir)
        target = self.root_dir / filename
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | _NOFOLLOW
        fd = os.open(target, flags, 0o600)
        _fchmod_private(fd)
        payload = line if line.endswith("\n") else line + "\n"
        with os.fdopen(fd, "a", encoding="utf-8") as fh:
            fh.write(payload)

    def write_artifact(self, sha256: str, content: str) -> Path:
        """Idempotently writes content-addressed ``artifacts/<sha256>.txt`` (0600) and prunes old files."""
        target = self.artifact_path(sha256)
        _ensure_private_dir(self.root_dir)
        if self.artifacts_dir.is_symlink():  # O_NOFOLLOW only guards the last path component
            raise OSError("artifacts directory is a symlink")
        _ensure_private_dir(self.artifacts_dir)
        raw = content.encode("utf-8")
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | _NOFOLLOW
        fd = os.open(target, flags, 0o600)
        _fchmod_private(fd)
        with os.fdopen(fd, "wb") as fh:
            fh.write(raw)
        self.prune(keep_sha256=sha256)
        return target

    def read_slice(self, sha256: str, offset: int = 0, limit: int = 8192) -> Dict[str, Any]:
        """Reads a UTF-8-safe byte window from ``artifacts/<sha256>.txt`` without following symlinks."""
        target = self.artifact_path(sha256)
        limit = max(1, min(int(limit), 65536))
        offset = max(0, int(offset))
        if self.artifacts_dir.is_symlink():
            raise OSError("artifacts directory is a symlink")
        flags = os.O_RDONLY | _NOFOLLOW | _NONBLOCK
        fd = os.open(target, flags)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise OSError("artifact is not a regular file")
            total = st.st_size
            start = min(offset, total)
            with os.fdopen(fd, "rb") as fh:
                fd = -1
                fh.seek(start)
                # Read only the requested window plus 8 bytes of slack: enough to skip up to 3 leading
                # continuation bytes, complete one code point when ``limit`` is tiny, and still see
                # whether the window end splits a code point.
                window = fh.read(limit + 8)
        finally:
            if fd >= 0:
                os.close(fd)
        text, rel_next, _ = utf8_slice(window, offset=0, limit=limit)
        next_offset = start + rel_next
        return {
            "sha256": sha256,
            "offset": offset,
            "next_offset": next_offset,
            "returned_bytes": len(text.encode("utf-8")),
            "total_bytes": total,
            "eof": next_offset >= total,
            "text": text,
        }

    def prune(self, *, keep_sha256: Optional[str] = None) -> Dict[str, int]:
        """Evicts oldest ``.txt`` artifacts until count <= ``max_artifacts`` and bytes <= ``max_bytes``."""
        if not self.artifacts_dir.is_dir() or self.artifacts_dir.is_symlink():
            return {"removed_files": 0, "removed_bytes": 0, "remaining_files": 0, "remaining_bytes": 0}
        entries = []
        for entry in os.scandir(self.artifacts_dir):
            if not entry.name.endswith(".txt") or entry.is_symlink():
                continue
            stem = entry.name[:-4]
            if not is_valid_sha256(stem):
                continue
            try:
                st = entry.stat(follow_symlinks=False)
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode):
                entries.append((st.st_mtime_ns, entry.name, Path(entry.path), st.st_size, stem))
        entries.sort(key=lambda item: (item[0], item[1]))
        total_bytes = sum(item[3] for item in entries)
        total_files = len(entries)
        removed_files = 0
        removed_bytes = 0
        for _, _, path, size, stem in entries:
            if total_files <= self.max_artifacts and total_bytes <= self.max_bytes:
                break
            if keep_sha256 and stem == keep_sha256 and total_files == 1:
                break
            if keep_sha256 and stem == keep_sha256:
                continue
            try:
                path.unlink()
                total_files -= 1
                total_bytes -= size
                removed_files += 1
                removed_bytes += size
            except OSError:
                continue
        return {
            "removed_files": removed_files,
            "removed_bytes": removed_bytes,
            "remaining_files": total_files,
            "remaining_bytes": total_bytes,
        }
