#!/usr/bin/env bash
# Installs the Themer live settings into Firefox (see README.md): themer.cfg into the Firefox installation folder and
# defaults/pref/themer-autoconfig.js, which makes Firefox load it. That folder belongs to root, so the copies run with
# sudo (pkexec without a terminal). Safe to run again: only what differs is copied. Firefox reads them at its next
# start. Package upgrades keep the files (the package does not own them); run this again after a `git pull`.
#
#   ./install.sh                 every Firefox installation found
#   ./install.sh /opt/firefox    that installation
#   ./install.sh --uninstall     remove them again
set -euo pipefail

here="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
uninstall=no
dirs=()
for arg in "$@"; do
  case "$arg" in
    --uninstall) uninstall=yes ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) dirs+=("$arg") ;;
  esac
done

if [[ ${#dirs[@]} -eq 0 ]]; then
  for d in /usr/lib/firefox /usr/lib/firefox-esr /usr/lib64/firefox /opt/firefox; do
    [[ -x "$d/firefox" && -d "$d/defaults/pref" ]] && dirs+=("$d")
  done
fi
if [[ ${#dirs[@]} -eq 0 ]]; then
  echo "No Firefox installation with a writable layout found. The Snap and Flatpak builds cannot load autoconfig" >&2
  echo "files; install Firefox from Mozilla's apt repository or tarball, or pass its folder." >&2
  exit 1
fi

as_root() {
  if [[ $EUID -eq 0 ]]; then
    "$@"
  elif [[ -t 0 ]] && command -v sudo >/dev/null; then
    sudo "$@"
  else
    pkexec "$@"
  fi
}

for d in "${dirs[@]}"; do
  cfg="$d/themer.cfg"
  pref="$d/defaults/pref/themer-autoconfig.js"
  if [[ "$uninstall" == yes ]]; then
    as_root rm -f "$cfg" "$pref"
    echo "removed $cfg and $pref"
    continue
  fi
  if cmp -s "$here/themer.cfg" "$cfg" && cmp -s "$here/themer-autoconfig.js" "$pref"; then
    echo "up to date: $d"
    continue
  fi
  as_root install -m 644 "$here/themer.cfg" "$cfg"
  as_root install -m 644 "$here/themer-autoconfig.js" "$pref"
  echo "installed $cfg and $pref (restart Firefox once)"
done
