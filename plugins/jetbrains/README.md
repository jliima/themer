# jetbrains-themer

A dynamic theme for all JetBrains IDEs that follows the desktop theme from Themer (the Pare design system in
[jliima/dotfiles](https://github.com/jliima/dotfiles)). Dark and light variants both work: the IDE switches with
`themer mode toggle`.

Covers both the **IDE UI** (chrome, tool windows, menus) and the **editor** (syntax highlighting, VCS colors, diff gutter).

> This is a personal theme built around Themer. It is not published to the JetBrains Marketplace.

---

## How it works

Everything that has colors is a Themer template in the dotfiles, `.config/themer/templates/jetbrains/`:

| Template | What Themer writes |
|---|---|
| `themer.icls` | the editor scheme "Themer", `~/.config/JetBrains/<IDE>/colors/Themer.icls` for every installed IDE |
| `plugin/` | a small theme plugin ("Themer", UI colors) zipped to `~/.local/share/JetBrains/<IDE>/themer/lib/themer-theme.jar` |
| `plugin/theme/themer.theme.json` | the same UI theme as plain JSON, `~/.cache/themer/jetbrains/themer.theme.json` |

Colors are Themer tokens (`{{ syntax-keyword }}`, `{{ accent-soft }}`), so a new theme or variant restyles the IDEs
without touching this repo. The three targets are in `.config/themer/targets.toml` (group `jetbrains`).

This repo holds the part Themer cannot render: the **reload plugin**, a Kotlin plugin that runs a local HTTP server
inside the IDE so a theme change shows up live, without a restart.

```
themer apply ──► colors/Themer.icls, themer-theme.jar, themer.theme.json ──apply.sh──► IDE (live reload via :9988/reload)
```

## Project structure

```
jetbrains-themer/
├── install.sh                     # builds the reload plugin, links jetbrains-themer-apply onto PATH
├── apply.sh                       # Themer's reload step: installs the reload plugin, triggers reload
├── scripts/
│   └── diff-color-changes.py      # Diff a hand-edited .icls against what Themer rendered (see the update-color-scheme skill)
└── reload-plugin/                 # Kotlin/Gradle IntelliJ plugin for live reload
    └── src/main/kotlin/.../
        ├── ThemerReloadStartupActivity.kt
        ├── ThemerReloadServer.kt  # HTTP server on localhost:9988
        ├── ThemeReloader.kt       # Applies the rendered theme/scheme in-process
        ├── CopilotColorPatcher.kt
        └── VcsLogGraphColorPatcher.kt
```

## Requirements

- [Themer](https://github.com/jliima/themer), with the JetBrains templates and targets from the dotfiles
  ([jliima/dotfiles](https://github.com/jliima/dotfiles), `.config/themer/`) stowed
- JDK (to build the reload plugin), `unzip` and `curl` (apply.sh)
- A JetBrains IDE (tested: IntelliJ IDEA, PyCharm, WebStorm, Rider, DataGrip)
- The live reload plugin requires IntelliJ 2026.1+ (`since-build=261`)

## Setup

Clone the repo anywhere; nothing depends on where.

1. `./install.sh` builds the reload plugin, links `~/.local/bin/jetbrains-themer-apply` to `apply.sh` (the command
   the "JetBrains UI theme" target runs after rendering) and installs the plugin into every IDE.
2. `themer apply --only jetbrains --force` (the dotfiles already have the targets). From then on `themer apply` and
   `themer mode toggle` re-render and reload by themselves.
3. Restart the IDEs once. Each IDE selects the Themer theme and scheme on its first start with the plugin (a marker
   file `options/themer-theme-selected` in its config folder records it); after that Themer drives them.

`jetbrains-themer-apply` installs the reload plugin jar into every IDE and calls `POST localhost:9988/reload`. It is
idempotent, and Themer skips it quietly when it is not installed. Re-run `./install.sh` after a `git pull`.

## Customizing the theme

### Editor colors
Edit `themer.icls` in your Themer templates (`~/.config/themer/templates/jetbrains/`). Colors are Themer expressions: a token (`{{ syntax-keyword | strip }}`, the
`strip` drops the `#` the ICLS format does not want) or a filter chain (`{{ red-dim | mix(red, 0.5) | strip }}`).
`themer tokens` lists them. To pull colors you tuned in the IDE back into the template, use the
`update-color-scheme` skill (`scripts/diff-color-changes.py`).

### UI colors
Edit `plugin/theme/themer.theme.json` in the same folder. Its `colors` section names the Themer colors the `ui` section
uses; the `ui` section maps IntelliJ UI key paths to those names. Then `themer apply --only jetbrains --force`.

## Colors

Prefer semantic tokens (`bg`, `text`, `accent`, `line`, `syntax-*`). Hue steps are `<hue>-soft` (faint tint),
`<hue>-mid`, `<hue>-dim` and the hue itself; `<hue>-mix` in the theme template is dim mixed halfway to the hue.
The full hues are used for VCS status colors and project avatars, the faint steps for background tints (file colors,
diff backgrounds). VCS log graph branches get the eight hues, then their `-mix` steps.

## Live reload

The reload plugin exposes:

```
POST http://localhost:9988/reload
```

It reads `~/.cache/themer/jetbrains/themer.theme.json` and the IDE's own `colors/Themer.icls`, both rendered by
Themer, and applies them via IntelliJ's internal APIs. No restart needed. If no IDE is running, the script skips the
reload silently; the new theme applies on the next IDE start.

## License

MIT
