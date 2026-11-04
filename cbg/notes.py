"""Ownership de notas (plugin/LSP) por call ID: máquina de estados explícita.

Estados: PENDING -> DELIVERED -> RETIRED.  Modelo em docs/model/notes.md.

Invariantes (testadas em tests/invariants/test_notes_model.py):
  N1 uma nota é entregue a exatamente um call ID e aparece em exatamente uma linha renderizada.
  N2 o dono aponta para o sha256 do que foi de fato renderizado (B2); rebind só no mesmo call ID.
  N3 re-settlement do mesmo call ID (pass corretivo, falha de política) continua recebendo a nota
     já entregue (B3); só complete_batch/rotate_session aposentam.
  N4 rotação de sessão não exclui nota PENDING da elegibilidade do dono (B1) e aposenta só DELIVERED.
  N5 estado limitado (#9): DELIVERED vira RETIRED no fim do lote e sai do ledger; resta um histórico
     de aposentadas com teto fixo, usado só para não perder nota num re-settlement tardio.
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
            raise OwnershipError("note_id duplicado: " + note_id)
        note = Note(note_id, owner_call_id, text, self.session_id)
        self._live[note_id] = note
        return note

    def eligible(self, call_id: str) -> List[Note]:
        """Notas que pertencem à linha ``call_id``: pendentes, já entregues a ela, ou aposentadas
        dela (re-settlement tardio). Independe da sessão em que foram enfileiradas (B1)."""
        live = [n for n in self._live.values() if n.owner_call_id == call_id]
        late = [n for n in self._retired.values() if n.owner_call_id == call_id]
        return live + late

    def bind(self, call_id: str, note_ids: Iterable[str], rendered_sha256: str) -> None:
        """Registra que ``note_ids`` estão no render final ``rendered_sha256`` da linha ``call_id``."""
        for nid in note_ids:
            note = self._live.get(nid) or self._retired.get(nid)
            if note is None:
                raise OwnershipError("nota desconhecida: " + nid)
            if note.owner_call_id != call_id:
                raise OwnershipError("nota %s pertence a %s, não a %s" % (nid, note.owner_call_id, call_id))
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
