# Themer for VS Code

The VS Code part of Themer. Themer renders a dark and a light color theme ("Themer Dark", "Themer Light") from the
template `templates/vscode/theme.json` into the installed extension. This extension adds what a theme file cannot do:
VS Code reads a theme file once and never again, so a theme or variant that Themer re-renders would keep the old
colors until the window is reloaded. The extension watches the rendered files and reloads the window when their
content changes (a notification instead while a debug session runs, or with `themer.autoReload` off).

Switching between dark and light needs no reload: both files are already loaded, and VS Code follows the desktop
mode with `window.autoDetectColorScheme`.

```sh
./install.sh                          # from this folder: packages with vsce, installs, runs themer apply --only vscode
./install.sh --profile "My Profile"   # also into another VS Code profile (extensions are installed per profile)
```

Needs `code` and npm (`npx` runs `@vscode/vsce`). Then select the themes in your settings:

```json
"workbench.colorTheme": "Themer Dark",
"window.autoDetectColorScheme": true,
"workbench.preferredDarkColorTheme": "Themer Dark",
"workbench.preferredLightColorTheme": "Themer Light"
```
