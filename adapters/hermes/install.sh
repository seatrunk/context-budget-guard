#!/bin/sh
# Installs the plugin into the user's Hermes (does not enable it: Hermes requires plugins.enabled).
# Usage: sh adapters/hermes/install.sh   (HERMES_HOME optional; default ~/.hermes)
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
DEST="${CBG_INSTALL_DEST:-${HERMES_HOME:-$HOME/.hermes}/plugins/context-budget-guard}"
# Strip trailing slashes and refuse an empty destination or one outside */plugins/context-budget-guard
# before any rm -rf.
while [ "${DEST%/}" != "$DEST" ]; do DEST=${DEST%/}; done
case "$DEST" in
  "") echo "install.sh: empty destination; aborted" >&2; exit 2 ;;
  */plugins/context-budget-guard) ;;
  *) echo "install.sh: unexpected destination ($DEST); it must end in /plugins/context-budget-guard" >&2; exit 2 ;;
esac
mkdir -p "$DEST/vendor"
cp "$ROOT/adapters/hermes/context_budget_guard/__init__.py" "$ROOT/adapters/hermes/context_budget_guard/plugin.yaml" "$DEST/"
rm -rf "$DEST/vendor/cbg"
cp -R "$ROOT/cbg" "$DEST/vendor/cbg"
find "$DEST" -name __pycache__ -prune -exec rm -rf {} +
echo "installed in $DEST"
echo "enable with: hermes plugins enable context-budget-guard   (default mode: shadow)"
