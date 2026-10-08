#!/usr/bin/env bash
# The reload step of Themer's JetBrains targets (they run it when the theme or variant changed).
#
#   ./apply.sh
#
# Themer has already written the editor scheme (colors/Themer.icls) and the UI theme plugin
# (themer/lib/themer-theme.jar) into every installed IDE, and ~/.cache/themer/jetbrains/themer.theme.json for the live
# reload. This script installs the reload plugin next to them, removes what the old Pywal setup left behind, and asks
# running IDEs to reload.
# Requires: unzip, curl. Build the reload plugin once: cd reload-plugin && ./gradlew buildPlugin
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config/JetBrains"
SHARE_DIR="$HOME/.local/share/JetBrains"
RELOAD_PLUGIN_ZIP="$PROJECT_DIR/reload-plugin/build/distributions/themer-reload-plugin-1.0.0.zip"
RELOAD_PORT=9988

# Versioned IDE folders only (IntelliJIdea2026.2, PyCharm2026.1, ...), not Toolbox, consentOptions and the like.
ide_dirs() {
  find "$1" -maxdepth 1 -mindepth 1 -type d -name '*20[0-9][0-9].[0-9]*' 2>/dev/null
}

# ── Old Pywal files ──────────────────────────────────────────────────────────
while IFS= read -r ide_dir; do
  rm -rf "$ide_dir/pywal" "$ide_dir/pywal-reload-plugin" "$ide_dir/pywal-theme.jar"
done < <(ide_dirs "$SHARE_DIR")
while IFS= read -r ide_dir; do
  rm -f "$ide_dir/colors/pywal-color-scheme.icls"
done < <(ide_dirs "$CONFIG_DIR")

# ── Reload plugin ────────────────────────────────────────────────────────────
if [[ -f "$RELOAD_PLUGIN_ZIP" ]]; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  unzip -q "$RELOAD_PLUGIN_ZIP" -d "$tmp"
  plugin_jar="$(find "$tmp" -name '*.jar' | head -1)"
  installed=0
  while IFS= read -r ide_dir; do
    target="$ide_dir/themer-reload-plugin/lib/$(basename "$plugin_jar")"
    if ! cmp -s "$plugin_jar" "$target"; then
      mkdir -p "$(dirname "$target")"
      cp "$plugin_jar" "$target"
      echo "  → $target"
      ((installed++)) || true
    fi
  done < <(ide_dirs "$SHARE_DIR")
  echo "✓ Reload plugin installed or updated in $installed IDE share directories"
else
  echo "⚠ Reload plugin not built, so running IDEs cannot reload live." >&2
  echo "  Build it with: cd $PROJECT_DIR/reload-plugin && ./gradlew buildPlugin" >&2
fi

# ── Live reload of running IDEs ──────────────────────────────────────────────
reload_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  "http://localhost:$RELOAD_PORT/reload" --max-time 3 2>/dev/null || true)

if [[ "$reload_response" == "200" ]]; then
  echo "✓ Live reload triggered (port $RELOAD_PORT)"
else
  echo "  (No running IDE responded on port $RELOAD_PORT; restart to apply)"
fi
