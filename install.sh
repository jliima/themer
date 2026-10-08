#!/usr/bin/env bash
# Installs the themer command (a link in ~/.local/bin to this clone) and seeds its settings.
#
#   ./install.sh                      plain install: settings in ~/.config/themer, no stow
#   ./install.sh --dotfiles ~/dots    your settings, themes and templates live in the GNU Stow package ~/dots
#   ./install.sh --no-plugins         skip the plugins below
#
# It also installs the plugins in plugins/ for the apps it finds: VS Code (`code` on PATH), the JetBrains IDEs
# (a versioned folder in ~/.config/JetBrains), Firefox (an installation in /usr/lib or /opt; asks for sudo) and the
# browser extensions' native host (Firefox or a Chromium-based browser). A plugin that fails to install is reported and
# does not stop the rest.
# Themer ships no themes; install one with `themer install PATH` or keep them in <dotfiles>/.config/themer/themes.
# The templates are yours too: only the example templates/kde is copied, and only if you have no templates/kde yet.
# Safe to run again: existing files are kept. A previous plain install (a real ~/.config/themer folder) is moved into
# the dotfiles folder, with a backup in ~/.local/state/themer.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mode="plain"
dotfiles=""
plugins="yes"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dotfiles) dotfiles="$(cd "${2/#\~/$HOME}" && pwd)"; mode="dotfiles"; shift 2 ;;
    --no-plugins) plugins="no"; shift ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done

say() { printf '%s\n' "$*"; }
die() { printf 'install: %s\n' "$*" >&2; exit 1; }

python3 -c 'import sys, tomllib; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null \
  || die "Themer needs Python 3.11 or newer"
chmod +x "$here/themer"
stamp="$(date +%Y%m%d-%H%M%S)"
state="${XDG_STATE_HOME:-$HOME/.local/state}/themer"

# Copies every file under $1 to $2 unless it already exists there.
copy_missing() {
  local src="$1" dst="$2" rel
  (cd "$src" && find . -type f) | while read -r rel; do
    rel="${rel#./}"
    if [[ ! -e "$dst/$rel" && ! -L "$dst/$rel" ]]; then
      mkdir -p "$(dirname "$dst/$rel")"
      cp -P "$src/$rel" "$dst/$rel"
      say "added $dst/$rel"
    fi
  done
}

# Copies the skeleton (settings) without overwriting anything that exists.
seed() {
  local conf="$1" enabled="$2"
  mkdir -p "$conf/themes" "$conf/templates"
  copy_missing "$here/skel/.config/themer" "$conf"
  # The example template, as a whole folder and only when there is none yet, so a customized one is never touched.
  if [[ ! -e "$conf/templates/kde" && ! -L "$conf/templates/kde" ]]; then
    cp -r "$here/templates/kde" "$conf/templates/kde"
    say "added $conf/templates/kde (example template)"
  fi
  if ! grep -q '^\[dotfiles\]' "$conf/settings.toml"; then
    # An older settings.toml: add the dotfiles table from the skeleton.
    printf '\n' >> "$conf/settings.toml"
    sed -n '/^\[dotfiles\]/,/^stow = /p' "$here/skel/.config/themer/settings.toml" >> "$conf/settings.toml"
    say "added [dotfiles] to $conf/settings.toml"
  fi
  if [[ "$enabled" == false ]] && grep -q '^enabled = true' "$conf/settings.toml"; then
    sed -i 's|^enabled = true|enabled = false|' "$conf/settings.toml"
  fi
}

# The command: a link to this clone, so `git pull` here updates it.
link_command() {
  local bin="$HOME/.local/bin/themer"
  mkdir -p "$HOME/.local/bin"
  if [[ -e "$bin" && ! -L "$bin" ]]; then
    mkdir -p "$state/pre-install-$stamp"
    mv "$bin" "$state/pre-install-$stamp/"
    say "moved the old $bin to $state/pre-install-$stamp"
  fi
  ln -sfn "$here/themer" "$bin"
  say "linked ~/.local/bin/themer -> $here/themer"
  case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) say "note: ~/.local/bin is not on PATH; add it in your shell profile" ;;
  esac
}

# Installs the plugin of every app that is present. A failure is a warning: Themer itself is installed by now.
install_plugins() {
  [[ "$plugins" == "yes" ]] || return 0
  local found=()
  command -v code >/dev/null && found+=("VS Code:$here/plugins/vscode/install.sh")
  compgen -G "${XDG_CONFIG_HOME:-$HOME/.config}/JetBrains/*20[0-9][0-9].[0-9]*" >/dev/null \
    && found+=("JetBrains IDEs:$here/plugins/jetbrains/install.sh")
  # The native messaging host for the Dark Reader and Stylus forks; registering it needs no root.
  local b
  for b in .mozilla chromium google-chrome BraveSoftware/Brave-Browser vivaldi microsoft-edge; do
    if [[ -d "$HOME/$b" || -d "${XDG_CONFIG_HOME:-$HOME/.config}/$b" ]]; then
      found+=("browser extensions:$here/plugins/browser/install.sh")
      break
    fi
  done
  local fx
  for fx in /usr/lib/firefox /usr/lib/firefox-esr /usr/lib64/firefox /opt/firefox; do
    if [[ -x "$fx/firefox" && -d "$fx/defaults/pref" ]]; then
      found+=("Firefox:$here/plugins/firefox/install.sh")
      break
    fi
  done
  local entry
  for entry in "${found[@]}"; do
    say ""
    say "Installing the ${entry%%:*} plugin..."
    "${entry#*:}" || say "warning: the ${entry%%:*} plugin did not install; fix the error above and run ${entry#*:}"
  done
}

# The plugin installers call themer, so make sure it is found even when ~/.local/bin is not on PATH yet.
export PATH="$HOME/.local/bin:$PATH"

if [[ "$mode" == "plain" ]]; then
  seed "${XDG_CONFIG_HOME:-$HOME/.config}/themer" false
  link_command
  install_plugins
  say "Next: themer install <theme folder>, then themer doctor and themer apply --theme <id>"
  exit 0
fi

# ---- dotfiles install -------------------------------------------------------------------------------------------

[[ "$dotfiles" != "$HOME" ]] || die "the dotfiles folder cannot be your home folder"
command -v stow >/dev/null || die "GNU Stow is not installed: sudo apt install stow"
conf="$dotfiles/.config/themer"
say "dotfiles: $dotfiles"

# Move a previous plain install (a real ~/.config/themer folder) into the dotfiles folder.
old="${XDG_CONFIG_HOME:-$HOME/.config}/themer"
# Skip when it only holds links into the dotfiles copy (a stowed folder): there is nothing of a plain install in it.
if [[ -d "$old" && ! -L "$old" && -n "$(find "$old" -type f -print -quit)" ]]; then
  mkdir -p "$state/pre-dotfiles-$stamp" "$conf"
  cp -a "$old" "$state/pre-dotfiles-$stamp/"
  copy_missing "$old" "$conf" > /dev/null
  rm -rf "$old"
  say "moved $old into $conf (backup in $state/pre-dotfiles-$stamp)"
fi

# Settings and folders.
seed "$conf" true
link_command

# Stow links ~/.config/themer (and every other file of the package) into ~.
THEMER_SETTINGS="$conf/settings.toml" "$here/themer" stow \
  || die "stow reported conflicts; fix them and run: themer stow"

install_plugins

say ""
say "Themes in $conf/themes: $(ls "$conf/themes" 2>/dev/null | tr '\n' ' ')"
say "Next: themer doctor, then themer apply --theme <id>"
