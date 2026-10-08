#!/usr/bin/env bash
# Installs the Themer extension into VS Code and has Themer render its themes into it.
#
#   ./install.sh                         the default profile
#   ./install.sh --profile "My Profile"  also install into another VS Code profile (repeatable)
#
# Run it from the Themer clone, wherever that is; nothing depends on its location. Re-run after a git pull.
# Requires: code, npm (npx runs vsce to package the extension) and themer.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
profiles=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) profiles+=("$2"); shift 2 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done

command -v code >/dev/null || { echo "install: VS Code (code) is not on PATH" >&2; exit 1; }
# nvm is often loaded lazily by the shell profile, so a script does not see npm until nvm.sh is sourced.
if ! command -v npx >/dev/null && [[ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]]; then
  # shellcheck disable=SC1091
  . "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
fi
command -v npx >/dev/null || { echo "install: npm is not installed: sudo apt install npm" >&2; exit 1; }

version="$(node -p "require('$here/package.json').version")"
vsix="$here/themer-$version.vsix"
(cd "$here" && npx --yes @vscode/vsce@3.2.1 package --skip-license --allow-missing-repository -o "$vsix")

code --install-extension "$vsix" --force
for p in "${profiles[@]}"; do
  code --install-extension "$vsix" --force --profile "$p"
done
rm -f "$vsix"

# Themer renders the themes into the installed extension (the "VS Code themes" target in targets.toml).
if command -v themer >/dev/null; then
  themer apply --only vscode --force
else
  echo "themer is not installed; run 'themer apply --only vscode --force' once it is"
fi
echo "Select the themes with: \"workbench.colorTheme\": \"Themer Dark\" and \"window.autoDetectColorScheme\": true."
