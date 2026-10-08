# JetBrains Pywal Theme

Dynamic pywal theme for all JetBrains IDEs: editor color scheme plus IDE UI, applied live without restart.

## Pipeline

```
~/dotfiles/.config/wal/colorschemes/dark/parecolors.json  (palette source)
  -> wal -> ~/.cache/wal/colors.json                      (what all scripts read)
  -> ~/dotfiles/scripts/pywal/applications/intellij.sh
       scripts/build-icls.py        pywal_color_scheme.icls -> ~/.config/JetBrains/<IDE>/colors/
       scripts/build-theme-json.py  theme/ui-mapping.json   -> pywal-theme.jar in ~/.local/share/JetBrains/<IDE>/pywal/lib/
       deploys reload-plugin jar, then POST localhost:9988/reload
```

Apply after any change: `bash ~/dotfiles/scripts/pywal/applications/intellij.sh`
(or `python3 ~/dotfiles/scripts/pywal/run-pywal.py --theme parecolors --app intellij`).
Only UI/editor colors live reload; changes to `reload-plugin/` need `./gradlew buildPlugin` in
`reload-plugin/`, the apply script, and an IDE restart.

## Key files

| File | Purpose |
|---|---|
| `pywal_color_scheme.icls` | Editor scheme template, `{varName}` placeholders (bare hex, no `#`, after build) |
| `theme/ui-mapping.json` | IntelliJ UI keys -> palette variable names, plus theme metadata |
| `assets/META-INF/` | Static plugin.xml / manifest / icon for the theme jar |
| `reload-plugin/` | Kotlin plugin: HTTP reload server (`ThemeReloader.kt`) and Copilot color patching |
| `scripts/diff-color-changes.py` | Diff an edited `.icls` against the template (see `update-color-scheme` skill) |
| `scripts/generate-template.py` | One-time dev tool to regenerate the ICLS template |

The reload plugin reads this repo from the hardcoded path `~/JetBrainsProjects/jetbrains-pywal-theme/`.

## Variables

All names come from `colors.json`: semantic `special.*` keys (`background`, `surface`, `overlay`, `foreground`,
`textMuted`, `accent`, `selection`, `border`, `syntax*`, ...), ramps `red|green|blue|yellow|cyan|magenta|grey|black|white`
1-5 (1 darkest, 5 brightest), and `color0-15` (avoid). Check `~/.cache/wal/colors.json` for current values.

- `ui-mapping.json` values are variable names, never hex. Nested objects join with `.`; numbers and booleans pass
  through (e.g. `VersionControl.Log.Graph.saturation`).
- Prefer semantic names over ramps; use ramps for VCS, diff, file colors.
- VCS log graph branch colors: `VersionControl.Log.Graph.color1..N`, handed out in first-paint order by
  `VcsLogGraphColorPatcher.kt` (the IDE hashes branch names otherwise). Themer's eight hues at level 5, then 4.
- VCS file status: added `green5`, modified `blue5`, deleted `red5`, conflict `yellow5`, ignored `textDisabled`.
- Background tints (diff lines, file colors, banners): ramp level 1-2 so text stays readable.
- New variables go into `parecolors.json` under `special`; only add universally useful ones.

## GitHub Copilot plugin colors

Copilot hardcodes most chat colors. `reload-plugin/.../CopilotColorPatcher.kt` maps `Copilot.*` keys in
`ui-mapping.json` onto the plugin's static color fields at startup and on every Look and Feel change:

| Key | Target |
|---|---|
| `Copilot.Palette.<field>` / `Copilot.Palette.<Obj>.<field>` | `com.github.copilot.style.CopilotPalette[$Obj]` |
| `Copilot.Style.<Group>.<field>` | `com.github.copilot.style.Style$Colors$<Group>` |
| `Copilot.Chat.<Name>.<field>` | Compose color objects listed in `chatClasses` (e.g. `UserBubbleColors`) |
| `Copilot.Nes.*` | Real theme keys the plugin reads itself |

Swing (`JBColor`) fields follow live reloads; Compose (`long`) fields may need an IDE restart. Unknown keys are
ignored and unmapped fields keep Copilot's colors. Plugin updates may rename fields; re-check with `javap`.

## Code style

- 2-space indent in JSON and Python; the Kotlin plugin uses 4 spaces.
- camelCase names, max line length 120.
