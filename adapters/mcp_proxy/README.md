# Proxy MCP stdio

Fica entre o cliente MCP e um servidor MCP real e aplica o orçamento às respostas de `tools/call`. Só stdlib.

```sh
python3 adapters/mcp_proxy/proxy.py --mode shadow --log-dir ~/.cache/context-budget-guard -- <comando do servidor MCP> [args]
```

No cliente, troque o comando do servidor pelo comando acima. Default `shadow` (resposta byte a byte igual, só recibos). `--mode enforce` corta para `--cap` bytes (default 16384), grava o original em `artifacts/` (0600) e remove `structuredContent` de respostas cortadas, porque ele contornaria o teto. `isError` e mídia são mantidos. Erro interno no processamento de uma mensagem é fail-open.

Testes: `tests/adapters/test_mcp_proxy.py`, com servidor falso em `tests/adapters/fake_mcp_server.py`.
