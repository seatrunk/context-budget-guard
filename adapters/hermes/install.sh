#!/bin/sh
# Installs the Spillway plugin into the user's Hermes home (does not enable it automatically).
# Usage: sh adapters/hermes/install.sh   (HERMES_HOME optional; default ~/.hermes)
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
DEST="${SPILLWAY_INSTALL_DEST:-${CBG_INSTALL_DEST:-${HERMES_HOME:-$HOME/.hermes}/plugins/spillway}}"
# Strip trailing slashes and refuse empty or unexpected destinations before any rm -rf.
while [ "${DEST%/}" != "$DEST" ]; do DEST=${DEST%/}; done
case "$DEST" in
  "") echo "install.sh: empty destination; aborted" >&2; exit 2 ;;
  */plugins/spillway) ;;
  *) echo "install.sh: unexpected destination ($DEST); must end in /plugins/spillway" >&2; exit 2 ;;
esac
mkdir -p "$DEST/vendor"
cp "$ROOT/adapters/hermes/spillway/__init__.py" "$ROOT/adapters/hermes/spillway/plugin.yaml" "$DEST/"
rm -rf "$DEST/vendor/spillway" "$DEST/vendor/cbg"
cp -R "$ROOT/spillway" "$DEST/vendor/spillway"
find "$DEST" -name __pycache__ -prune -exec rm -rf {} +
echo "installed in $DEST"
echo "enable with: hermes plugins enable spillway   (default mode: shadow)"
