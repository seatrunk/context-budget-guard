# Replay offline (#11)

Sem modelo e sem rede. Fixtures sintéticas geradas por `gen_fixtures.py` (Python, TypeScript, Rust, SQL, UTF-8 e casos de nota/multimodal das issues #1, #6, #7, #8).

```sh
python3 benchmarks/replay/gen_fixtures.py   # regenera fixtures (determinístico)
python3 benchmarks/replay/replay.py         # escreve results/offline-replay.json; sai 1 se o candidato falhar algum oráculo
```

Braços: `none` (sem orçamento), `historical` (preview por caracteres, nota descartada ao spillar) e `candidate` (núcleo `cbg`). Os oráculos usam a verdade da fixture, não o núcleo. O braço `historical` é uma emulação documentada do comportamento descrito nas issues, não o runtime privado. Este replay não mede tokens nem custo e não sustenta alegação de economia em tarefa real.
