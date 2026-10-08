#!/usr/bin/env bash
# Installs the themer command (a link in ~/.local/bin to this clone) and seeds its settings.
#
#   ./install.sh                      plain install: settings in ~/.config/themer, no stow
#   ./install.sh --dotfiles ~/dots    your settings, themes and templates live in the GNU Stow package ~/dots
#
# Themer ships no themes; install one with `themer install PATH` or keep them in <dotfiles>/.config/themer/themes.
# Safe to run again: existing files are kept. A previous plain install (a real ~/.config/themer folder) is moved into
# the dotfiles folder, with a backup in ~/.local/state/themer.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mode="plain"
dotfiles=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dotfiles) dotfiles="$(cd "${2/#\~/$HOME}" && pwd)"; mode="dotfiles"; shift 2 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
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

# Copies the skeleton (settings, example snippets) without overwriting anything that exists.
seed() {
  local conf="$1" enabled="$2"
  mkdir -p "$conf/themes" "$conf/templates" "$conf/firefox/chrome" "$conf/firefox/content"
  copy_missing "$here/skel/.config/themer" "$conf"
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

if [[ "$mode" == "plain" ]]; then
  seed "${XDG_CONFIG_HOME:-$HOME/.config}/themer" false
  link_command
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

# Settings, folders and the example Firefox snippet.
seed "$conf" true
link_command

# Stow links ~/.config/themer (and every other file of the package) into ~.
THEMER_SETTINGS="$conf/settings.toml" "$here/themer" stow \
  || die "stow reported conflicts; fix them and run: themer stow"

say ""
say "Themes in $conf/themes: $(ls "$conf/themes" 2>/dev/null | tr '\n' ' ')"
say "Next: themer doctor, then themer apply --theme <id>"
