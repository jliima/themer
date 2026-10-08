#!/usr/bin/env bash
# Installs jetbrains-themer: builds the live reload plugin, puts the reload step on PATH as jetbrains-themer-apply
# (the command Themer's "JetBrains UI theme" target runs) and installs the plugin into every IDE.
#
#   ./install.sh
#
# Run it from the clone, wherever that is; nothing depends on its location. Re-run after a git pull.
# Requires: a JDK to build the plugin, unzip and curl (apply.sh).
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building the reload plugin..."
(
  cd "$here/reload-plugin"
  ./gradlew --console=plain -q buildPlugin 2>/dev/null || ./gradlew --console=plain -q --offline buildPlugin
)

mkdir -p "$HOME/.local/bin"
ln -sfn "$here/apply.sh" "$HOME/.local/bin/jetbrains-themer-apply"
echo "linked ~/.local/bin/jetbrains-themer-apply -> $here/apply.sh"
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo "note: ~/.local/bin is not on PATH; add it in your shell profile" ;;
esac

"$here/apply.sh"
echo "Next: themer apply --only jetbrains --force, then restart the IDEs once."
