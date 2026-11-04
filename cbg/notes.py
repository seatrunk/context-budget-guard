"""Note (plugin/LSP) ownership by call ID: an explicit state machine.

States: PENDING -> DELIVERED -> RETIRED.  Model in docs/model/notes.md.

Invariants (tested in tests/invariants/test_notes_model.py):
  N1 a note is delivered to exactly one call ID and appears in exactly one rendered row.
  N2 the owner points to the sha256 of what was actually rendered (B2); rebind only on the same call ID.
  N3 a re-settlement of the same call ID (corrective pass, policy failure) keeps receiving the
     already delivered note (B3); only complete_batch/rotate_session retire.
  N4 session rotation does not remove a PENDING note from its owner's eligibility (B1) and retires only DELIVERED.
  N5 bounded state (#9): DELIVERED becomes RETIRED at the end of the batch and leaves the ledger; a
     fixed-cap history of retired notes remains, used only so a late re-settlement does not lose a note.
"""
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, List, Optional


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
    def __init__(self, session_id: str = "s0", retired_cap: int = 64):
        self.session_id = session_id
        self.retired_cap = retired_cap
        self._live: "OrderedDict[str, Note]" = OrderedDict()  # PENDING + DELIVERED
        self._retired: "OrderedDict[str, Note]" = OrderedDict()

    # -- eventos -----------------------------------------------------------------------------
    def queue(self, note_id: str, owner_call_id: str, text: str) -> Note:
        if note_id in self._live or note_id in self._retired:
            raise OwnershipError("duplicate note_id: " + note_id)
        note = Note(note_id, owner_call_id, text, self.session_id)
        self._live[note_id] = note
        return note

    def eligible(self, call_id: str) -> List[Note]:
        """Notes that belong to row ``call_id``: pending, already delivered to it, or retired from it
        (late re-settlement). Independent of the session in which they were queued (B1)."""
        live = [n for n in self._live.values() if n.owner_call_id == call_id]
        late = [n for n in self._retired.values() if n.owner_call_id == call_id]
        return live + late

    def bind(self, call_id: str, note_ids: Iterable[str], rendered_sha256: str) -> None:
        """Records that ``note_ids`` are in the final render ``rendered_sha256`` of row ``call_id``."""
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

    # -- consulta ----------------------------------------------------------------------------
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
