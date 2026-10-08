# Themer window decoration

A KWin decoration (KDecoration3, Plasma 6) drawn entirely from the applied Themer theme, so a theme change restyles
window frames along with everything else. Themer writes `~/.config/themerdecorationrc` from the template
`templates/kde/themerdecorationrc.ini` on every apply and asks KWin to reconfigure; the decoration re-reads it.

- Title bar in `titlebar` (`titlebar-inactive`), title centered on the window in `titlebar-text` at
  `window.title-size` px and `fonts.title-weight`, elided between the button groups when it does not fit.
- Round buttons `window.button-size` wide: minimize and maximize are chevrons (a diamond when maximized), close a
  cross. Hover fades in `titlebar-button-hover` (close: `titlebar-close-hover` with `titlebar-close-text`) over
  `window.hover-duration` ms. `M` in `kde.buttons-left` shows the window icon and opens the window menu.
- Corners `shape.radius-lg`: the top is painted rounded, KWin clips the window content's bottom corners.
  An optional ring (`window.decoration-outline-width`, `window-outline`) and a CSS-like shadow
  (`0 window.shadow-offset window.shadow-blur window-shadow`, alpha `window.shadow-alpha-dark` or `-light`).
- Every value has a default in `defaults.toml` ([window] and the titlebar-* / window-* roles); a theme overrides
  any of them.

## Build and use

Needs `cmake ninja-build g++ qt6-base-dev libkf6config-dev libkf6coreaddons-dev libkdecorations3-dev`.

```sh
~/dotfiles/themer/decoration/build.sh   # builds, installs into ~/dotfiles/.local/lib/qt6/plugins, runs stow
```

`~/.local/lib/qt6/plugins` must be on `QT_PLUGIN_PATH` for KWin (an `environment.d` file does it). Then select it in
`settings.toml`, which wins over every theme on this machine, and apply:

```toml
[overrides.kde]
decoration-library = "themer"
decoration-theme = "Themer"
buttons-left = "M"
```

Rebuild after a Plasma upgrade that changes KDecoration.
