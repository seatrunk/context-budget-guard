#!/bin/sh
# Instala o plugin no Hermes do usuário (não ativa: Hermes exige plugins.enabled).
# Uso: sh adapters/hermes/install.sh   (HERMES_HOME opcional; default ~/.hermes)
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
DEST="${CBG_INSTALL_DEST:-${HERMES_HOME:-$HOME/.hermes}/plugins/context-budget-guard}"
# Normaliza barras finais e recusa destino vazio ou fora de */plugins/context-budget-guard
# antes de qualquer rm -rf.
while [ "${DEST%/}" != "$DEST" ]; do DEST=${DEST%/}; done
case "$DEST" in
  "") echo "install.sh: destino vazio; abortado" >&2; exit 2 ;;
  */plugins/context-budget-guard) ;;
  *) echo "install.sh: destino inesperado ($DEST); precisa terminar em /plugins/context-budget-guard" >&2; exit 2 ;;
esac
mkdir -p "$DEST/vendor"
cp "$ROOT/adapters/hermes/context_budget_guard/__init__.py" "$ROOT/adapters/hermes/context_budget_guard/plugin.yaml" "$DEST/"
rm -rf "$DEST/vendor/cbg"
cp -R "$ROOT/cbg" "$DEST/vendor/cbg"
find "$DEST" -name __pycache__ -prune -exec rm -rf {} +
echo "instalado em $DEST"
echo "ative com: hermes plugins enable context-budget-guard   (modo default: shadow)"
