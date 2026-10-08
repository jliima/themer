# jetbrains-pywal-theme

A dynamic theme for all JetBrains IDEs that follows the desktop palette from Themer (the Pare design system in
[jliima/dotfiles](https://github.com/jliima/dotfiles)), or from [pywal](https://github.com/dylanaraps/pywal) /
[pywal16](https://github.com/eylles/pywal16). Dark and light variants both work: the IDE switches with the palette.

Covers both the **IDE UI** (chrome, tool windows, menus) and the **editor** (syntax highlighting, VCS colors, diff gutter).

> This is a personal theme built around a specific palette. It is not published to the JetBrains Marketplace.

---

## How it works

The theme is split into two parts:

1. **UI theme** — an IntelliJ Look and Feel plugin (`pywal-theme.jar`) built from a static mapping of UI keys to palette variables, combined with colors from pywal at apply-time.
2. **Editor color scheme** — an ICLS file (`pywal-color-scheme.icls`) generated from a template with `{varName}` placeholders, substituted with colors from pywal at apply-time.

A companion **live reload plugin** (`pywal-reload-plugin`) runs a local HTTP server inside the IDE, allowing the theme to update instantly without restarting.

```
themer apply ──► ~/.cache/themer/jetbrains.json ──apply.sh──► IDE (live reload via :9988/reload)
     (pywal-format palette for the applied theme and variant)
```

Without Themer, `apply.sh` falls back to pywal's `~/.cache/wal/colors.json`. Whether the IDE theme is dark or light
(UI `dark` flag, editor parent scheme Darcula or Default) follows the palette's background.

## Project structure

```
jetbrains-pywal-theme/
├── apply.sh                       # Builds and deploys everything, then triggers live reload
├── pywal_color_scheme.icls        # Editor scheme template ({varName} placeholders)
├── theme/
│   └── ui-mapping.json            # Maps IntelliJ UI keys → palette variable names
├── assets/
│   └── META-INF/
│       ├── plugin.xml             # Theme plugin metadata
│       └── pluginIcon.svg
├── scripts/
│   ├── palette.py                 # Palette path, loading, dark/light detection
│   ├── build-icls.py              # Processes ICLS template with colors.json
│   ├── build-theme-json.py        # Combines ui-mapping.json + colors.json → theme JSON
│   └── generate-template.py      # Dev tool: regenerate ICLS template from a scheme
└── reload-plugin/                 # Kotlin/Gradle IntelliJ plugin for live reload
    └── src/main/kotlin/.../
        ├── PywalReloadStartupActivity.kt
        ├── PywalReloadServer.kt   # HTTP server on localhost:9988
        └── ThemeReloader.kt       # Applies theme/scheme in-process
```

## Requirements

- Themer (from the dotfiles) or [pywal16](https://github.com/eylles/pywal16)
- Python 3.10+
- JDK (for `jar` command)
- A JetBrains IDE (tested: IntelliJ IDEA, PyCharm, WebStorm, Rider, DataGrip)
- The live reload plugin requires IntelliJ 2026.1+ (`since-build=261`)

## Setup

The repo must be at `~/JetBrainsProjects/jetbrains-pywal-theme/` (the reload plugin reads its templates from there).

1. Build the reload plugin once: `cd reload-plugin && ./gradlew buildPlugin`.
2. With Themer, add a target to `~/.config/themer/targets.toml` (the dotfiles already have it):

   ```toml
   [[target]]
   name = "JetBrains IDEs"
   group = "jetbrains"
   format = "pywal"
   output = "~/.cache/themer/jetbrains.json"
   reload = "~/JetBrainsProjects/jetbrains-pywal-theme/apply.sh"
   ```

   `themer apply` (or `themer mode toggle`) then writes the palette and runs `apply.sh` whenever it changes.
   `themer apply --only jetbrains --force` re-runs it by hand. With plain pywal, run `./apply.sh` after `wal`.

`apply.sh [colors.json]`:
1. Processes the ICLS template and deploys it to all IDE `colors/` directories
2. Builds the theme JSON, packages `pywal-theme.jar` and deploys it to all IDEs
3. Deploys the reload plugin JAR to all IDEs
4. Triggers live reload via `POST localhost:9988/reload`

## Customizing the theme

### Editor colors
Edit `pywal_color_scheme.icls`. Variables like `{syntaxKeyword}`, `{blue5}`, `{green3}` etc. are
substituted with actual hex values at apply-time. See `~/.cache/themer/jetbrains.json` for the available
variables.

### UI colors
Edit `theme/ui-mapping.json`. This file maps IntelliJ UI key paths to palette variable names.
You do **not** need to re-apply, just trigger a reload:

```bash
curl -X POST http://localhost:9988/reload
```

Changes take effect immediately in any running IDE with the reload plugin installed.

## Color palette

The palette is Themer's pywal export (`themer/themer`, `fmt_pywal`), which keeps the keys of the old
`parecolors.json`:

- Semantic variables: `background`, `foreground`, `accent`, `surface`, `selection`, …
- Syntax variables: `syntaxKeyword`, `syntaxString`, `syntaxType`, `syntaxComment`, …
- Palette ramps for `red green blue yellow cyan magenta orange violet grey black white`, levels 1 to 5

Ramps are relative to the background in both variants: level 1 is a faint tint, level 5 the full hue.
The brightest (`5`) ramp levels are used for VCS status colors and project avatars.
The faintest (`1`/`2`) levels are used for background tints (file colors, diff backgrounds).
VCS log graph branches get the eight hues at level 5, then level 4.

## Live reload

The reload plugin exposes:

```
POST http://localhost:9988/reload
```

It reads `~/.cache/themer/jetbrains.json` (else `~/.cache/wal/colors.json`) and the project template files at runtime,
builds the theme in-memory, and applies it via IntelliJ's internal APIs — no restart needed.

If no IDE is running, the script skips the reload silently; the new theme will apply on next IDE start.

## License

MIT
