# Context Budget Guard

![Less noise. Keep the clues. A tool-result stack preserves its failure diagnostic and a path to recover detail. Experimental operating skill and benchmark kit; native runtime not shipped; activation blocked.](docs/assets/hero.svg)

[![CI](https://github.com/seatrunk/context-budget-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/seatrunk/context-budget-guard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**[The idea](#the-idea) · [How it should work](#how-it-should-work) · [The plan](#the-plan) · [Evaluation](#how-we-plan-to-evaluate-it) · [Try the toolkit](#try-the-toolkit)**

> **Experimental · production activation BLOCKED.** Since Etapa 1 (PR #14) this repository ships a pure, dependency-free core (`cbg/`), a Hermes plugin and an MCP stdio proxy that default to `shadow`, and an offline replay where the candidate passes 39/39 oracles. See [Núcleo e adaptadores](#núcleo-e-adaptadores-v030). The private native patch is still not shipped: its combined local candidate **failed acceptance** and separate delivery-support code was **REJECTED**, as recorded in the [November 4 assessment](docs/reviews/2026-11-04-combined-assessment.md). Still pending: the Etapa 2 native gate, a real-task benchmark and independent review. The graphics explain the design, not measured savings.

## The idea

An agent can drown in tool output: a compiler dump, a long file, a giant JSON response. The important part may be just one exit code, one source location, or a short runtime notice.

**The goal is not to delete more text. It is to keep the information the next decision needs—and make the rest recoverable.**

| Keep in view | Keep recoverable | Never trade away |
| --- | --- | --- |
| Useful preview, failure status, necessary notices | Additional detail in a private/redacted artifact | Trust boundaries, valid media, mandatory controls, approved read semantics |

The [operating skill](SKILL.md) describes how to review that behavior. The runtime would enforce it. **Loading a skill is not installing a guard.** Conversation-summary compaction is another layer, not a different name for this tool-output policy.

## How it should work

![Design target: tool data passes through per-result and aggregate budgeting into a model-visible preview. Additional detail goes to a private/redacted artifact. A trusted runtime notice remains exactly once outside the genuine untrusted wrapper, and targeted reads recover extra detail.](docs/assets/output-flow.svg)

### One output, two destinations

1. **For the model:** a useful bounded preview, original error/exit semantics, valid media and any necessary notice.
2. **For recovery:** additional output in a private/redacted artifact, read with targeted `offset` / `limit` when the task actually needs it.
3. **Across both:** track notice ownership by call ID, reserve its complete rendered footprint before spilling, and never restore an unbounded note after the final cap.

A note sitting in a file is not the same as a note the model received. A small preview is not successful if it hides the reason a command failed.

### The proposed defaults

| Surface | Intended ordinary limit | Important boundary |
| --- | --- | --- |
| Complete file selection | 350 effective LF lines **and** 16,384 formatted UTF-8 bytes | Both limits apply; define empty/trailing-line behavior |
| Partial file selection | 150 effective LF lines **and** 16,384 formatted UTF-8 bytes | Paginate instead of silently presenting an incomplete read as complete |
| Final ordinary tool text | 16,384 UTF-8 bytes | Count the final representation, including framing and escaped metadata |
| Inline notice bundles | Up to 4,096 bytes per bundle; 8,192 per batch | Active policy/tiny-budget decisions still apply; archive or use a bounded marker |

Mandatory controls and valid one-use read receipts retain their defined exceptions. Aggregate turn accounting is separate from per-result bytes; irreducible-overhead reporting must not become a byte-limit escape hatch. None of these proposed limits is a total token, money, filesystem or same-UID security boundary. See the [full design](docs/design.md).

## The plan

![Six-stage promotion roadmap: define invariants is documented; the isolated build and review is rejected; repair and re-review is next; multi-code replay is proposed; real-task and compaction evaluation is not run; controlled rollout is locked. Offline characterization may expose failures earlier but cannot override a failing oracle.](docs/assets/roadmap.svg)

**Status after Etapa 1:** the published core closes B1–B3 and the core parts of #1 and #3–#9 in its own tests and offline replay. The native runtime is a separate matter: its Etapa 2 combined gate, a real-task benchmark and independent review are still pending, so this is not “ship it.”

### Historical record: native combined assessment (November 4, before Etapa 1)

Individual repairs for [#6](https://github.com/seatrunk/context-budget-guard/issues/6), [#7](https://github.com/seatrunk/context-budget-guard/issues/7), [#8](https://github.com/seatrunk/context-budget-guard/issues/8) and [#9](https://github.com/seatrunk/context-budget-guard/issues/9) reached scoped independent approvals, then the **combined gate failed: 649 passed, 13 failed, one existing Windows-only skip**. These are local runtime observations, not public CI results or proof of a shipped fix.

| Native blocker (recorded) | Observed result | Addressed in the published core by |
| --- | --- | --- |
| Session rotation | Two approved-read rows remain above 16,384 bytes | `test_B1_*` (re-measured final render; rotated-session receipt rejected) |
| Fallback ownership | A bounded media marker disagrees with the owned original suffix | `test_B2_*` (owner bound to the rendered SHA-256) |
| Persistent failure | Four SECOND-settlement cases lose a notice | `test_B3_*` (retirement only after the last settlement) |
| Delivery-support integrity | Independent review rejected two verifier gaps despite 37 existing tests passing | Not addressed: native delivery support is not published |

Six additional synthetic read/media probes fail before budget commit at an existing result-type guardrail; they are separately unsupported/unverified, not established new budget regressions. The parent independently reproduced all seven product-acceptance failures. The delivery-support implementation and its tests remain separate and are **not shipped on this documentation branch**.

Read the [latest findings and reviewer brief](docs/reviews/2026-11-04-combined-assessment.md), [sanitized evidence JSON](docs/reviews/2026-11-04-combined-assessment.json), and [current status](docs/project-status.md). The [earlier protected-note rejection](docs/reviews/2026-11-03-protected-notes.md) remains historical evidence. Native patches, full probes and the rejected support code are not distributed here; fingerprints are local snapshot identifiers, not a self-contained reproduction package. Issues remain open until the native gate and independent review pass; production activation remains blocked.

## How we plan to evaluate it

![Proposed evaluation: synthetic Python, TypeScript/JavaScript, Rust and SQL/config/log workloads enter paired unbudgeted, historical-spill and candidate-runtime arms. Independent correctness oracles veto broken results before bytes, recovery calls, latency or available token/cost data are compared. Protocol only; no benchmark scores are shown.](docs/assets/evaluation.svg)

### Fidelity first. Efficiency second.

- **Same workload, different arms:** freeze the inputs, call order, budgets and runtime fingerprints. Compare an unbudgeted reference, historical spilling and the actual isolated candidate—not a toy replacement.
- **Check what survives:** diagnostic facts, note placement, failure status, media order, receipt lifetime, artifact recovery and no repeated tool execution.
- **Then measure the whole cost:** output bytes, recovery/tool calls, timing, and actual provider/tokenizer usage when available. Count retries and follow-up reads; report unknown costs as unknown.
- **Only later, with separate approval:** real coding tasks and tests, followed by deliberate conversation-compaction interaction experiments. A benchmark cannot authorize production activation.

The [evaluation protocol](docs/multi-codebase-evaluation.md) is published; the replay harness and execution are **not implemented** by that document. [#11](https://github.com/seatrunk/context-budget-guard/issues/11) tracks the actual benchmark work.

The historical [November 2 baseline](benchmarks/results/2026-11-02-off-baseline.json) remains **guard off, one observation per case**. There is no published on-mode comparison, measured savings, or verified live-backend enforcement. The [benchmark guide](docs/benchmarking.md) explains the evidence limits.

## Núcleo e adaptadores (v0.3.0)

Desde a Etapa 1 o repo publica o núcleo puro, sem I/O e sem dependências (Python 3.11+ stdlib):

| Caminho | O que é |
| --- | --- |
| [`cbg/`](cbg/) | `limits` (linhas LF efetivas, corte UTF-8), `render` (bytes finais com framing, escaping JSON multimodal e sufixo de nota), `notes` (ownership por call ID), `sanitize` (delimitadores), `facts` (exit code e `arquivo:linha`), `budget` (limitador e lote) e `verify` (verificador independente do recibo) |
| [`adapters/hermes/`](adapters/hermes/README.md) | plugin do Hermes Agent via hook `transform_tool_result` |
| [`adapters/mcp_proxy/`](adapters/mcp_proxy/README.md) | proxy MCP stdio |
| [`benchmarks/replay/`](benchmarks/replay/README.md) | replay offline com três braços e oráculos de fidelidade |
| [`docs/model/notes.md`](docs/model/notes.md) | máquina de estados das notas |

O verificador relê a saída final e, se o recibo não bate, entrega um marcador limitado (fail closed). O patch nativo privado continua fora do repo. Ativação em produção segue bloqueada pelo [rollout](docs/rollout.md).

### Instalação no Hermes

```sh
sh adapters/hermes/install.sh
```

O script copia `adapters/hermes/context_budget_guard/__init__.py` e `plugin.yaml` para `${HERMES_HOME:-~/.hermes}/plugins/context-budget-guard/` e o núcleo `cbg/` inteiro para `vendor/cbg` dentro desse diretório, apagando `__pycache__`. Não ativa nada: o Hermes só carrega plugin listado em `plugins.enabled`.

### Ligar e desligar

```sh
hermes plugins enable context-budget-guard     # ou plugins.enabled: [context-budget-guard] em ~/.hermes/config.yaml
# reinicie o Hermes: o gateway descobre plugins uma vez por processo
hermes plugins disable context-budget-guard    # desliga; reinicie de novo
```

Remover de vez: apague `~/.hermes/plugins/context-budget-guard`.

### Modos e variáveis (adaptador Hermes)

| Variável | Default | Efeito |
| --- | --- | --- |
| `CBG_MODE` | `shadow` | `shadow` (observação): mede e grava recibo, o modelo recebe o original. `enforce`: substitui resultado acima do teto pelo preview e grava o original em `artifacts/`. `off`: não faz nada nem grava nada. Valor inválido vira `shadow` |
| `CBG_LOG_DIR` | `$HERMES_HOME/context-budget-guard` (ou `~/.hermes/context-budget-guard`) | diretório de `receipts.jsonl`, `errors.jsonl` e `artifacts/` |
| `CBG_RESULT_CAP` | `16384` | teto em bytes UTF-8 |
| `CBG_FRAMING_RESERVE` | `512` | bytes descontados do teto para o invólucro `untrusted_tool_result` que o Hermes aplica depois; o núcleo usa `max(256, CBG_RESULT_CAP - CBG_FRAMING_RESERVE)` |

Erro interno do plugin é fail-open: o resultado original segue e `errors.jsonl` recebe `{"tool", "error"}` (só o nome da exceção).

### Proxy MCP

```sh
python3 adapters/mcp_proxy/proxy.py [--mode shadow|enforce|off] [--log-dir DIR] [--cap N] -- <comando do servidor real> [args]
```

No cliente MCP, troque o comando do servidor por essa linha. O servidor real roda como processo filho. Toda mensagem passa sem mudança, exceto respostas a `tools/call`. Defaults: `--mode` vem de `CBG_MODE` (senão `shadow`), `--log-dir` de `CBG_LOG_DIR` (senão `~/.cache/context-budget-guard`), `--cap` de `CBG_RESULT_CAP` (senão `16384`, sem reserva de framing). Em `shadow` a resposta sai byte a byte igual. Em `enforce`, resposta acima do teto vira preview, `isError` e mídia são mantidos, o original vai para `artifacts/` e `structuredContent` é removido (ele contornaria o teto). `off` repassa tudo e não grava recibo.

### Recibos

Uma linha JSON por tool result em `receipts.jsonl`. Não contém conteúdo do resultado. Em `enforce`, `artifacts/<artifact_sha256>.txt` guarda o original completo (arquivos 0600, diretórios 0700).

Campos do núcleo (`cbg/budget.py`, `apply_budget`):

| Campo | Significado |
| --- | --- |
| `call_id` | call ID da ferramenta (no proxy, `mcp-<id JSON-RPC>`) |
| `mode` | `full` (coube inteiro), `preview` (cabeça e cauda com cabeçalho de fatos), `marker` (só cabeçalho), `withheld` (falha de política ou agregado), `failclosed` (verificador reprovou), `control` (controle obrigatório, sem teto) |
| `kind` | `text` ou `multimodal` |
| `cap` | teto aplicado em bytes (`null` para control) |
| `rendered_bytes` / `rendered_sha256` | tamanho e hash do render final medido |
| `original_bytes` / `original_lines` | tamanho em bytes UTF-8 e linhas LF efetivas do original |
| `exit_code` | exit code detectado (`null` se não houver) |
| `error_locations` | até 5 locais `arquivo:linha` extraídos |
| `notes_shown` / `notes_marked` | IDs de nota visíveis / representadas só por marcador (vazios no adaptador Hermes) |
| `media_parts` | número de partes de mídia preservadas |
| `artifact_sha256` / `artifact_bytes` | hash e tamanho do original |
| `receipt_used` | se um recibo de leitura aprovada (#7) foi aplicado |
| `verified` | o verificador aceitou o render final |
| `violations_before_failclose` | violações achadas antes do fail closed (lista vazia no caso normal) |
| `policy_error`, `aggregate_bytes`, `aggregate_unsatisfiable` | só em `finalize_batch` (lote), não aparecem nos adaptadores |

Campos acrescentados pelo adaptador Hermes: `ts`, `tool`, `session_id`, `adapter` (`hermes`), `adapter_mode`, `elapsed_us`, `would_change` (o modo não é `full` nem `control`, ou seja, o enforce mudaria o resultado). Pelo proxy: `ts`, `tool`, `adapter` (`mcp_proxy`), `adapter_mode`, `is_error`, `would_change`. O proxy em `enforce` grava também uma linha `{"call_id", "structured_content_dropped": true}` quando remove `structuredContent`.

### Riscos e limites conhecidos

- O patch nativo privado não foi provado. B1–B3 estão fechados no núcleo publicado, não no runtime privado; o gate nativo combinado continua pendente.
- O hook público do Hermes só vê resultado em texto. Multimodal passa sem mudança, e as notas de plugin/LSP do runtime não chegam ao hook.
- Reservamos 512 bytes para o invólucro do Hermes. Em `enforce` o recibo mede o nosso render, não o texto final montado pelo Hermes.
- O replay offline é sintético: não mede tokens nem custo, e o braço de spill histórico é uma emulação, não o runtime antigo.

### Roteiro de benchmark em tarefa real

1. Observação (`CBG_MODE=shadow`, uma semana ou um lote fixo de tarefas). Medir: bytes antes e depois (`original_bytes` e `rendered_bytes`), quantos resultados passariam do teto (`would_change`), violações de oráculo (`verified=false`, `mode=failclosed`, `violations_before_failclose` não vazio) e latência (`elapsed_us`, só no Hermes).
2. Enforce: as mesmas tarefas, em pares A/B (mesmo prompt, repositório no mesmo commit, mesmo modelo; um braço `shadow`, outro `enforce`, ordem alternada). Comparar sucesso da tarefa (testes passam, critério definido antes), tokens e custo pela fatura ou pelos logs do provedor, leituras de recuperação em `artifacts/` e regressões de fidelidade (o modelo perdeu exit code, local do erro ou nota). Pelo menos 5 pares por tarefa; reportar mediana e IQR.

Agregação com jq:

```sh
R=~/.hermes/context-budget-guard/receipts.jsonl
jq -s 'map(select(.mode)) | {total: length, passariam_do_teto: map(select(.would_change)) | length,
        bytes_antes: (map(.original_bytes) | add), bytes_depois: (map(.rendered_bytes) | add),
        nao_verificados: map(select(.verified == false or .mode == "failclosed")) | length,
        por_modo: (group_by(.mode) | map({(.[0].mode): length}) | add)}' "$R"
jq -s 'map(.elapsed_us // empty) | sort | {n: length, p50: .[length/2|floor], p95: .[length*0.95|floor], max: .[-1]}' "$R"
jq -r 'select(.would_change) | [.tool, .original_bytes, .rendered_bytes] | @tsv' "$R" | sort | uniq -c | sort -rn | head
```

Mesma coisa só com Python stdlib:

```sh
python3 - ~/.hermes/context-budget-guard/receipts.jsonl <<'PY'
import json, statistics, sys
r = [json.loads(l) for l in open(sys.argv[1]) if l.strip() and '"mode"' in l]
cut = [x for x in r if x.get("would_change")]
lat = sorted(x["elapsed_us"] for x in r if "elapsed_us" in x)
print("resultados", len(r), "passariam do teto", len(cut))
print("bytes antes", sum(x["original_bytes"] for x in r), "depois", sum(x["rendered_bytes"] for x in r))
print("nao verificados", sum(1 for x in r if not x.get("verified") or x["mode"] == "failclosed"))
if lat:
    print("latencia us p50", statistics.median(lat), "p95", lat[int(len(lat) * 0.95)], "max", lat[-1])
PY
```

Reproduzir o replay offline (0 chamadas de modelo):

```sh
python3 benchmarks/replay/replay.py --out /tmp/offline-replay.json
cmp /tmp/offline-replay.json benchmarks/replay/results/offline-replay.json && echo idêntico
```

O comando sai com 1 se o braço candidato falhar algum oráculo. O `cmp` deve ficar mudo e imprimir `idêntico`; o CI faz o mesmo.

## Try the toolkit

Python 3.11+, no dependency installation, credentials or live profile required:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_repo.py
python3 scripts/validate_benchmark.py benchmarks/results/2026-11-02-off-baseline.json
```

These check the **public tooling**, not the separate runtime. To create synthetic fixtures, choose a new output directory:

```sh
python3 scripts/generate_fixtures.py --output benchmark-fixtures
```

The generator refuses existing paths. Generating fixtures does not run a model, recreate measured timing, or complete the proposed multi-codebase benchmark.

## Go deeper

| Start here | What you get |
| --- | --- |
| [Operating skill](SKILL.md) | Repeatable evidence and review procedure |
| [Design](docs/design.md) | Invariants, exceptions and protected-note contract |
| [Project status](docs/project-status.md) | Etapa 1 delivery, native fingerprints and remaining gates |
| [Latest assessment / reviewer handoff](docs/reviews/2026-11-04-combined-assessment.md) | Scoped progress, combined failures, verifier findings and decisions for the next reviewer |
| [Prior protected-note cycle](docs/reviews/2026-11-03-protected-notes.md) | Historical rejection and original defect evidence |
| [Evaluation protocol](docs/multi-codebase-evaluation.md) | Proposed corpus, comparison arms, metrics and promotion gates |
| [Rollout](docs/rollout.md) | Separate approval and rollback requirements |
| [Governance](docs/repository-governance.md) | Required review and branch protections |
| [Visual guide](docs/visual-guide.html) · [artwork sources](docs/assets/README.md) | Self-contained offline gallery and editable SVG/PNG graphics |

Contributions are welcome, especially small adversarial reproductions. Start with [CONTRIBUTING.md](CONTRIBUTING.md). Keep sensitive reports private under [SECURITY.md](SECURITY.md), follow the [code of conduct](CODE_OF_CONDUCT.md), and preserve the existing [MIT license](LICENSE) attribution.
