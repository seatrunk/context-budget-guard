"""context-budget-guard: núcleo puro (sem I/O) de orçamento para tool results.

API pública estável desta etapa:
    Policy, Note, Receipt, Rendered, NoteLedger, apply_budget, finalize_batch, verify
"""
from .limits import effective_lines, utf8_bytes, utf8_truncate
from .render import Rendered, render, rendered_bytes
from .notes import Note, NoteLedger, NoteState
from .budget import Policy, Receipt, Outcome, apply_budget, finalize_batch
from .verify import verify

__all__ = ["effective_lines", "utf8_bytes", "utf8_truncate", "Rendered", "render", "rendered_bytes",
           "Note", "NoteLedger", "NoteState", "Policy", "Receipt", "Outcome", "apply_budget",
           "finalize_batch", "verify"]
__version__ = "0.3.0"
