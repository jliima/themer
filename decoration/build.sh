#!/bin/bash
# Builds the Themer KWin decoration and installs it for this user (or into PREFIX):
#   ~/.local/lib/qt6/plugins/org.kde.kdecoration3/themer.so
# Needs: cmake, ninja, g++, qt6-base-dev, libkf6config-dev, libkf6coreaddons-dev, libkdecorations3-dev.
# Rebuild after a Plasma upgrade. KWin loads it on its next start (or log out and in). Qt must look in
# ~/.local/lib/qt6/plugins: QT_PLUGIN_PATH=$HOME/.local/lib/qt6/plugins, for example from
# ~/.config/environment.d/50-qt-plugins.conf.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
prefix=${PREFIX:-$HOME/.local}
cmake -S "$here" -B "$here/build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$prefix"
cmake --build "$here/build"
cmake --install "$here/build"
