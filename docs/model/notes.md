# Modelo de ownership de notas (Etapa 1)

Implementação: [`cbg/notes.py`](../../cbg/notes.py). Teste de propriedade: [`tests/invariants/test_notes_model.py`](../../tests/invariants/test_notes_model.py) (10.000 sequências, semente fixa).

## Estados e eventos

| De | Evento | Para | Observação |
| --- | --- | --- | --- |
| (nada) | `queue(note_id, owner_call_id, text)` | PENDING | dono é o call ID, não a sessão |
| PENDING | `bind(call_id, ids, sha256_renderizado)` | DELIVERED | só se `call_id == owner`; grava o sha256 do que o modelo vê |
| DELIVERED | re-settlement do mesmo call ID | DELIVERED | `eligible()` continua devolvendo a nota; sha256 é atualizado (B2, B3) |
| DELIVERED | `complete_batch(ids)` | RETIRED | chamado só depois do último settlement do lote |
| DELIVERED | `rotate_session()` | RETIRED | PENDING **não** muda: nota de linha de outro segmento não se perde |
| RETIRED | re-settlement tardio do mesmo call ID | RETIRED | histórico com teto (`retired_cap`) mantém a nota visível |

## Invariantes

- N1: uma nota aparece em exatamente uma linha renderizada, a do dono.
- N2: o sha256 registrado no dono é o do render final entregue, inclusive marcador ou withheld (B2).
- N3: falha de política ou de agregado no segundo settlement não perde nota entregue (B3, #4).
- N4: rotação de sessão não tira nota PENDING da elegibilidade, e a nota entra na medição do teto (B1).
- N5: estado limitado: `state_size() <= pendentes + retired_cap` (#9).
- Teto: toda linha não-control tem `rendered_bytes <= cap`, medido sobre o render final (F1/B1/#6).

## Premissa e limite

Call IDs são únicos por chamada. Se um runtime reutilizar call ID, uma nota aposentada pode reaparecer num re-settlement; o teste de propriedade reutiliza IDs de propósito e só exige N1 dentro do lote. Não há modelo TLA+ nesta etapa: a decisão foi teste de propriedade em stdlib (sem dependência de dev).
