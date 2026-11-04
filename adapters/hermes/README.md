# Adaptador Hermes Agent

Plugin de usuário que registra o hook público `transform_tool_result` do Hermes e chama o núcleo `cbg`. Não altera código do Hermes.

## Instalar e ligar

```sh
sh adapters/hermes/install.sh            # copia para ~/.hermes/plugins/context-budget-guard (ou $HERMES_HOME)
hermes plugins enable context-budget-guard
# reinicie o Hermes (o gateway descobre plugins uma vez por processo)
```

Equivalente manual: em `~/.hermes/config.yaml`, `plugins.enabled: [context-budget-guard]`.

Modo, por variável de ambiente do processo do Hermes:

| Variável | Default | Efeito |
| --- | --- | --- |
| `CBG_MODE` | `shadow` | `shadow` só mede e grava recibos; `enforce` substitui o resultado pelo preview; `off` não faz nada |
| `CBG_LOG_DIR` | `$HERMES_HOME/context-budget-guard` | onde ficam `receipts.jsonl`, `errors.jsonl` e `artifacts/` |
| `CBG_RESULT_CAP` | `16384` | teto em bytes UTF-8 |
| `CBG_FRAMING_RESERVE` | `512` | bytes reservados para o wrapper que o próprio Hermes aplica |

## Onde ver os resultados

- `~/.hermes/context-budget-guard/receipts.jsonl`: uma linha por tool result de texto, sem conteúdo. Campos úteis: `tool`, `mode` (full, preview, marker, failclosed), `would_change`, `original_bytes`, `rendered_bytes`, `cap`, `exit_code`, `error_locations`, `verified`, `elapsed_us`.
- `artifacts/<sha256>.txt` (0600): original completo, só em `enforce`.
- Resumo rápido: `python3 -c "import json,sys;r=[json.loads(l) for l in open(sys.argv[1])];print(len(r),'resultados',sum(x['would_change'] for x in r),'seriam cortados',sum(x['original_bytes']-x['rendered_bytes'] for x in r if x['would_change']),'bytes poupados')" ~/.hermes/context-budget-guard/receipts.jsonl`

## Desligar

`hermes plugins disable context-budget-guard` e reinicie, ou `CBG_MODE=off`. Para remover: apague `~/.hermes/plugins/context-budget-guard`.

## Limites conhecidos

- O hook público só vê o resultado em string. Resultados multimodais passam sem mudança.
- As notas de plugin/LSP do Hermes não chegam ao hook público, então o ledger de notas do núcleo não é usado aqui. O proxy MCP e o patch nativo podem usá-lo.
- Em `enforce`, o Hermes ainda aplica o próprio wrapper `untrusted_tool_result` por fora; por isso existe a reserva de framing.
- Qualquer erro interno é fail-open: o resultado original segue e o erro vai para `errors.jsonl`.
