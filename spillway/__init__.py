"""Spillway: verifiable fidelity-first tool-output budgeting core and runtime helpers.

Pure (zero-I/O) budgeting API:
    Policy, Note, Receipt, Rendered, NoteLedger, Outcome, apply_budget, finalize_batch, verify

Adapter storage helper (isolated I/O):
    ArtifactStore, is_valid_sha256
"""
from .artifacts import ArtifactStore, is_valid_sha256
from .budget import MIN_RESULT_CAP, Outcome, Policy, Receipt, apply_budget, finalize_batch
from .limits import effective_lines, utf8_bytes, utf8_slice, utf8_tail, utf8_truncate
from .notes import Note, NoteLedger, NoteState, OwnershipError
from .render import Rendered, render, rendered_bytes
from .verify import verify

__all__ = [
    "ArtifactStore",
    "is_valid_sha256",
    "MIN_RESULT_CAP",
    "effective_lines",
    "utf8_bytes",
    "utf8_slice",
    "utf8_tail",
    "utf8_truncate",
    "Rendered",
    "render",
    "rendered_bytes",
    "Note",
    "NoteLedger",
    "NoteState",
    "OwnershipError",
    "Policy",
    "Receipt",
    "Outcome",
    "apply_budget",
    "finalize_batch",
    "verify",
]
__version__ = "0.4.0"
