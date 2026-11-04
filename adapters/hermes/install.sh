#!/bin/sh
# Instala o plugin no Hermes do usuário (não ativa: Hermes exige plugins.enabled).
# Uso: sh adapters/hermes/install.sh   (HERMES_HOME opcional; default ~/.hermes)
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
DEST="${HERMES_HOME:-$HOME/.hermes}/plugins/context-budget-guard"
mkdir -p "$DEST/vendor"
cp "$ROOT/adapters/hermes/context_budget_guard/__init__.py" "$ROOT/adapters/hermes/context_budget_guard/plugin.yaml" "$DEST/"
rm -rf "$DEST/vendor/cbg"
cp -R "$ROOT/cbg" "$DEST/vendor/cbg"
find "$DEST" -name __pycache__ -prune -exec rm -rf {} +
echo "instalado em $DEST"
echo "ative com: hermes plugins enable context-budget-guard   (modo default: shadow)"
