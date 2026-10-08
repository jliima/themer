#!/usr/bin/env bash
# Registers the Themer native messaging host (themer-browser-host) with Firefox and the Chromium-based browsers, so
# the Dark Reader Themer and Stylus Themer extensions can receive the applied theme (see README.md). Safe to run again.
#
#   ./install.sh                         register the host for every browser found
#   ./install.sh --firefox-xpi FILE...   also install these unsigned Firefox builds into the Firefox installation
#                                        (sudo; see "Firefox" in README.md)
#   ./install.sh --uninstall             remove the host registrations, the installed builds and the prefs file
set -euo pipefail

here="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
host="$here/themer-browser-host"
name="themer"

# The extensions allowed to start the host. Firefox knows them by their gecko id; Chromium by the ID derived from the
# public "key" in each extension's MV3 manifest, which keeps it fixed for an unpacked extension.
firefox_ids=("darkreader-themer@jliima.github.io" "stylus-themer@jliima.github.io")
chromium_ids=("cpnjcddnplkinbmdjmikbopilgdhdmeb" "bpgefhlpgicjjbbbadkdcaedhfgepnio")

uninstall=no
xpis=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --uninstall) uninstall=yes; shift ;;
    --firefox-xpi)
      shift
      while [[ $# -gt 0 && "$1" != --* ]]; do xpis+=("$(readlink -f "$1")"); shift; done ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done

as_root() {
  if [[ $EUID -eq 0 ]]; then
    "$@"
  elif [[ -t 0 ]] && command -v sudo >/dev/null; then
    sudo "$@"
  else
    pkexec "$@"
  fi
}

json_list() {
  local out="" item
  for item in "$@"; do out+="${out:+, }\"$item\""; done
  echo "[$out]"
}

write_manifest() {  # folder, key, values
  local dir="$1" key="$2"
  shift 2
  mkdir -p "$dir"
  cat > "$dir/$name.json" <<EOF
{
  "name": "$name",
  "description": "Themer: live theme for the Dark Reader and Stylus forks",
  "path": "$host",
  "type": "stdio",
  "$key": $(json_list "$@")
}
EOF
  echo "registered $dir/$name.json"
}

firefox_dirs=("$HOME/.mozilla/native-messaging-hosts")
# Folders of Chromium-based browsers; only the ones whose config folder exists get the host.
chromium_dirs=()
for b in chromium google-chrome google-chrome-beta google-chrome-unstable BraveSoftware/Brave-Browser vivaldi \
         microsoft-edge; do
  [[ -d "$HOME/.config/$b" ]] && chromium_dirs+=("$HOME/.config/$b/NativeMessagingHosts")
done

# Firefox installations whose app scope accepts unsigned add-ons (built with MOZ_UNSIGNED_APP_SCOPE, as the Ubuntu and
# Debian packages are): <install>/browser/extensions/<id>.xpi.
firefox_installs=()
for d in /usr/lib/firefox /usr/lib/firefox-esr /usr/lib64/firefox /opt/firefox; do
  [[ -x "$d/firefox" && -d "$d/defaults/pref" ]] && firefox_installs+=("$d")
done

if [[ "$uninstall" == yes ]]; then
  for d in "${firefox_dirs[@]}" "${chromium_dirs[@]}"; do
    [[ -f "$d/$name.json" ]] && rm -f "$d/$name.json" && echo "removed $d/$name.json"
  done
  for d in "${firefox_installs[@]}"; do
    for id in "${firefox_ids[@]}"; do
      [[ -f "$d/browser/extensions/$id.xpi" ]] && as_root rm -f "$d/browser/extensions/$id.xpi" && echo "removed $id"
    done
    [[ -f "$d/defaults/pref/themer-extensions.js" ]] && as_root rm -f "$d/defaults/pref/themer-extensions.js"
  done
  exit 0
fi

chmod +x "$host"
for d in "${firefox_dirs[@]}"; do write_manifest "$d" allowed_extensions "${firefox_ids[@]}"; done
origins=()
for id in "${chromium_ids[@]}"; do origins+=("chrome-extension://$id/"); done
for d in "${chromium_dirs[@]}"; do write_manifest "$d" allowed_origins "${origins[@]}"; done

[[ ${#xpis[@]} -eq 0 ]] && exit 0
if [[ ${#firefox_installs[@]} -eq 0 ]]; then
  echo "No Firefox installation found in /usr/lib or /opt; install the .xpi files from about:debugging instead." >&2
  exit 1
fi
for d in "${firefox_installs[@]}"; do
  # Without these, Firefox only looks at the app scope after an upgrade and disables what it finds there until the
  # user enables it: rescan the app scope (4) at every start and do not auto-disable it (15 - 4).
  prefs="$(mktemp)"
  cat > "$prefs" <<'EOF'
// Installed by Themer (plugins/browser/install.sh): load the unsigned Themer extensions from browser/extensions.
pref("extensions.startupScanScopes", 4);
pref("extensions.autoDisableScopes", 11);
EOF
  dest="$d/defaults/pref/themer-extensions.js"
  cmp -s "$prefs" "$dest" || as_root install -m 644 "$prefs" "$dest"
  rm -f "$prefs"
  as_root mkdir -p "$d/browser/extensions"
  for xpi in "${xpis[@]}"; do
    id="$(unzip -p "$xpi" manifest.json \
      | python3 -c 'import json, sys; print(json.load(sys.stdin)["browser_specific_settings"]["gecko"]["id"])')"
    dest="$d/browser/extensions/$id.xpi"
    if cmp -s "$xpi" "$dest"; then
      echo "up to date: $dest"
    else
      as_root install -m 644 "$xpi" "$dest"
      echo "installed $dest (restart Firefox)"
    fi
  done
done
