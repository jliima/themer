#!/usr/bin/env bash
# Installs Themer into your dotfiles and links it into ~ with GNU Stow.
#
#   ./install.sh                      dotfiles = the folder Themer was unpacked in (~/dotfiles/themer -> ~/dotfiles)
#   ./install.sh --dotfiles ~/dots    use another dotfiles folder
#   ./install.sh --no-dotfiles        plain install: ~/.local/bin/themer and ~/.config/themer, no stow
#
# Safe to run again: existing files in the dotfiles folder are kept. A previous plain install (a real
# ~/.config/themer folder) is moved into the dotfiles folder, with a backup in ~/.local/state/themer.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mode="dotfiles"
dotfiles="$(dirname "$here")"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dotfiles) dotfiles="$(cd "${2/#\~/$HOME}" && pwd)"; shift 2 ;;
    --no-dotfiles) mode="plain"; shift ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
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
  (cd "$src" && find . -type f -o -type l) | while read -r rel; do
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
  local conf="$1" enabled="$2" path="$3"
  mkdir -p "$conf/themes" "$conf/templates" "$conf/firefox/chrome" "$conf/firefox/content"
  copy_missing "$here/skel/.config/themer" "$conf"
  if ! grep -q '^\[dotfiles\]' "$conf/settings.toml"; then
    # An older settings.toml: add the dotfiles table from the skeleton.
    printf '\n' >> "$conf/settings.toml"
    sed -n '/^\[dotfiles\]/,/^stow = /p' "$here/skel/.config/themer/settings.toml" >> "$conf/settings.toml"
    say "added [dotfiles] to $conf/settings.toml"
  fi
  if grep -q '@DOTFILES@' "$conf/settings.toml"; then
    sed -i "s|@DOTFILES@|$path|; s|^enabled = true|enabled = $enabled|" "$conf/settings.toml"
  fi
}

if [[ "$mode" == "plain" ]]; then
  conf="${XDG_CONFIG_HOME:-$HOME/.config}/themer"
  seed "$conf" false "~/dotfiles"
  mkdir -p "$HOME/.local/bin"
  ln -sfn "$here/themer" "$HOME/.local/bin/themer"
  say "linked ~/.local/bin/themer -> $here/themer"
  say "Next: themer doctor, then themer apply --theme pare"
  exit 0
fi

# ---- dotfiles install -------------------------------------------------------------------------------------------

[[ "$dotfiles" != "$HOME" ]] || die "the dotfiles folder cannot be your home folder; use --dotfiles"
command -v stow >/dev/null || die "GNU Stow is not installed: sudo apt install stow"
conf="$dotfiles/.config/themer"
pretty="${dotfiles/#$HOME/\~}"
say "dotfiles: $dotfiles"

# 1. Keep stow from linking the tool itself into ~ (it would become ~/themer).
case "$here/" in
  "$dotfiles"/*)
    rel="${here#"$dotfiles"/}"
    ignore="$dotfiles/.stow-local-ignore"
    if [[ ! -e "$ignore" ]]; then
      # A .stow-local-ignore replaces Stow's built-in list, so start from that list.
      cat > "$ignore" <<EOF
# Stow's default ignore list (a local file replaces it, so it is repeated here)
RCS
.+,v
CVS
\.\#.+
\.cvsignore
\.svn
_darcs
\.hg
\.git
\.gitignore
\.gitmodules
.+~
\#.*\#
^/README.*
^/LICENSE.*
^/COPYING

# Themer itself; its config lives in .config/themer
^/$rel\$
EOF
      say "created $ignore (Stow's defaults plus ^/$rel)"
    elif ! grep -qxF "^/$rel\$" "$ignore" && ! grep -qxF "^/$rel" "$ignore"; then
      printf '\n# Themer itself; its config lives in .config/themer\n^/%s$\n' "$rel" >> "$ignore"
      say "added ^/$rel to $ignore"
    fi
    ;;
esac

# 2. Move a previous plain install into the dotfiles folder.
old="${XDG_CONFIG_HOME:-$HOME/.config}/themer"
# Skip when ~/.config/themer already is the dotfiles copy (a stowed or folded link somewhere up the path).
if [[ -d "$old" && ! -L "$old" && "$(readlink -f "$old")" != "$(readlink -f "$conf" 2>/dev/null || echo "$conf")" ]]; then
  mkdir -p "$state/pre-dotfiles-$stamp" "$conf"
  cp -a "$old" "$state/pre-dotfiles-$stamp/"
  copy_missing "$old" "$conf" > /dev/null
  rm -rf "$old"
  say "moved $old into $conf (backup in $state/pre-dotfiles-$stamp)"
fi
bin="$HOME/.local/bin/themer"
if [[ -L "$bin" && "$(readlink -f "$bin")" != "$dotfiles"/* ]]; then
  rm "$bin"
  say "removed the old $bin link"
elif [[ -e "$bin" && ! -L "$bin" ]]; then
  mkdir -p "$state/pre-dotfiles-$stamp"
  mv "$bin" "$state/pre-dotfiles-$stamp/"
  say "moved the old $bin to $state/pre-dotfiles-$stamp"
fi

# 3. Settings, folders and the example Firefox snippet.
seed "$conf" true "$pretty"

# 4. The command, as a relative link inside the dotfiles folder: stow links ~/.local/bin/themer to it.
mkdir -p "$dotfiles/.local/bin" "$HOME/.local/bin"
relpath='import os, sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))'
target="$(python3 -c "$relpath" "$here/themer" "$dotfiles/.local/bin")"
ln -sfn "$target" "$dotfiles/.local/bin/themer"
say "linked $pretty/.local/bin/themer -> $target"

# 5. Stow.
THEMER_SETTINGS="$conf/settings.toml" "$here/themer" stow \
  || die "stow reported conflicts; fix them and run: themer stow"

case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) say "note: ~/.local/bin is not on PATH; add it in ~/.zshrc" ;;
esac
say ""
say "Bundled themes: $(ls "$here/themes" | tr '\n' ' ')"
say "Next: themer doctor, then themer apply --theme pare"
