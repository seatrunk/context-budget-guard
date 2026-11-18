"""Plugin/LSP note ownership by call ID: explicit bounded state machine. Pure stdlib, no I/O.

States: PENDING -> DELIVERED -> RETIRED. Specification in docs/model/notes.md.

Invariants (verified in tests/invariants/test_notes_model.py):
  N1 A note is delivered to at most one call ID and appears in at most one rendered row per batch.
  N2 The owner binds to the SHA-256 of what was actually rendered (B2); rebind only on the same call ID.
  N3 Re-settlement of the same call ID (corrective pass, policy failure) retains the delivered note (B3);
     retirement occurs only on complete_batch or rotate_session.
  N4 Session rotation preserves PENDING notes for cross-segment owners (B1) and retires only DELIVERED.
  N5 Bounded state (#9): DELIVERED transitions to RETIRED at batch completion with a fixed retired_cap
     ring, and orphaned PENDING notes are bounded by pending_cap.
"""
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Optional


class NoteState(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    RETIRED = "retired"


@dataclass
class Note:
    note_id: str
    owner_call_id: str
    text: str
    session_id: str = ""
    state: NoteState = NoteState.PENDING
    rendered_sha256: Optional[str] = None


class OwnershipError(RuntimeError):
    pass


class NoteLedger:
    def __init__(self, session_id: str = "s0", retired_cap: int = 64, pending_cap: int = 256):
        self.session_id = session_id
        self.retired_cap = max(0, retired_cap)
        self.pending_cap = max(1, pending_cap)
        self.evicted_pending = 0
        self._live: "OrderedDict[str, Note]" = OrderedDict()  # PENDING + DELIVERED
        self._retired: "OrderedDict[str, Note]" = OrderedDict()

    # -- state transitions -------------------------------------------------------------------
    def queue(self, note_id: str, owner_call_id: str, text: str) -> Note:
        if note_id in self._live or note_id in self._retired:
            raise OwnershipError("duplicate note_id: " + note_id)
        note = Note(note_id, owner_call_id, text, self.session_id)
        self._live[note_id] = note
        self._enforce_pending_cap()
        return note

    def eligible(self, call_id: str) -> List[Note]:
        """Notes owned by ``call_id``: pending, delivered in current batch, or retired (late re-settlement)."""
        live = [n for n in self._live.values() if n.owner_call_id == call_id]
        late = [n for n in self._retired.values() if n.owner_call_id == call_id]
        return live + late

    def bind(self, call_id: str, note_ids: Iterable[str], rendered_sha256: str) -> None:
        """Records that ``note_ids`` are bound to final render ``rendered_sha256`` of ``call_id``."""
        for nid in note_ids:
            note = self._live.get(nid) or self._retired.get(nid)
            if note is None:
                raise OwnershipError("unknown note: " + nid)
            if note.owner_call_id != call_id:
                raise OwnershipError("note %s belongs to %s, not to %s" % (nid, note.owner_call_id, call_id))
            if note.state is NoteState.PENDING:
                note.state = NoteState.DELIVERED
            note.rendered_sha256 = rendered_sha256

    def complete_batch(self, call_ids: Iterable[str]) -> None:
        ids = set(call_ids)
        for nid in [k for k, n in self._live.items() if n.owner_call_id in ids and n.state is NoteState.DELIVERED]:
            self._retire(nid)

    def rotate_session(self, new_session_id: str) -> None:
        for nid in [k for k, n in self._live.items() if n.state is NoteState.DELIVERED]:
            self._retire(nid)
        self.session_id = new_session_id

    # -- queries -----------------------------------------------------------------------------
    def state_size(self) -> int:
        return len(self._live) + len(self._retired)

    def pending(self) -> List[Note]:
        return [n for n in self._live.values() if n.state is NoteState.PENDING]

    def get(self, note_id: str) -> Optional[Note]:
        return self._live.get(note_id) or self._retired.get(note_id)

    def _retire(self, nid: str) -> None:
        note = self._live.pop(nid)
        note.state = NoteState.RETIRED
        self._retired[nid] = note
        while len(self._retired) > self.retired_cap:
            self._retired.popitem(last=False)

    def _enforce_pending_cap(self) -> None:
        pending_ids = [k for k, n in self._live.items() if n.state is NoteState.PENDING]
        while len(pending_ids) > self.pending_cap:
            oldest = pending_ids.pop(0)
            self._live.pop(oldest, None)
            self.evicted_pending += 1
