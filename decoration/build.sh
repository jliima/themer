#!/bin/bash
# Builds the Themer KWin decoration and installs it into the dotfiles' .local, which stow links into ~/.local:
#   ~/.local/lib/qt6/plugins/org.kde.kdecoration3/themer.so
# Needs: cmake, ninja, g++, qt6-base-dev, libkf6config-dev, libkf6coreaddons-dev, libkdecorations3-dev.
# Rebuild after a Plasma upgrade. KWin loads it on its next start (or log out and in).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
dotfiles=$(cd "$here/../.." && pwd)
cmake -S "$here" -B "$here/build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$dotfiles/.local"
cmake --build "$here/build"
cmake --install "$here/build"
stow --no-folding --dir="$dotfiles" --target="$HOME" .
