# JetBrains Themer Theme

Dynamic theme for all JetBrains IDEs, driven by Themer (dotfiles): editor color scheme plus IDE UI,
applied live without restart. Dark or light follows the Themer variant.

## Pipeline

```
themer apply (dotfiles; targets in ~/.config/themer/targets.toml, templates in .config/themer/templates/jetbrains/)
  -> ~/.config/JetBrains/<IDE>/colors/Themer.icls                (themer.icls)
  -> ~/.local/share/JetBrains/<IDE>/themer/lib/themer-theme.jar  (plugin/, zipped by Themer: archive = true)
  -> ~/.cache/themer/jetbrains/themer.theme.json                 (plugin/theme/themer.theme.json), then runs apply.sh
       apply.sh: installs the reload plugin jar into each IDE, removes old pywal* files, POST localhost:9988/reload
```

Apply after any change: `themer apply --only jetbrains --force`.
Only UI/editor colors live reload; changes to `reload-plugin/` need `./gradlew buildPlugin` in `reload-plugin/`,
`./apply.sh`, and an IDE restart. Gradle works with `--offline`.

All colors are Themer tokens rendered by Themer; nothing here computes a color. The dark flag and the ICLS
`parent_scheme` come from `{{ dark-bool }}` and `{{ is-dark | pick(Darcula, Default) }}`.

## Key files

| File | Purpose |
|---|---|
| `~/dotfiles/.config/themer/templates/jetbrains/themer.icls` | Editor scheme template, `{{ token | strip }}` values |
| `.../jetbrains/plugin/theme/themer.theme.json` | UI theme: a `colors` section of Themer tokens, then the `ui` and `icons` maps |
| `.../jetbrains/plugin/META-INF/` | plugin.xml / manifest / icon of the theme jar |
| `reload-plugin/` | Kotlin plugin: HTTP reload server (`ThemeReloader.kt`) and Copilot/VCS log color patching |
| `scripts/diff-color-changes.py` | Diff an edited `.icls` against the rendered one (see `update-color-scheme` skill) |

## Colors

Names in the `ui` section are the keys of the theme template's `colors` section, which are Themer tokens
(`bg`, `text`, `line`, `accent-soft`, `red-soft`, `red-mid`, `red-dim`, `red`, ...) or derived colors defined there
(`<hue>-mix`, `text-mid`, `line-weak`, `line-mid`). `themer tokens` lists the tokens.

- `ui` values are color names, never hex. Nested objects join with `.`; numbers and booleans pass through (e.g.
  `VersionControl.Log.Graph.saturation`).
- Prefer semantic names over hue steps; use hue steps for VCS, diff, file colors.
- VCS log graph branch colors: `VersionControl.Log.Graph.color1..N`, handed out in first-paint order by
  `VcsLogGraphColorPatcher.kt` (the IDE hashes branch names otherwise). Themer's eight hues, then their `-mix` steps.
- VCS file status: added `green`, modified `blue`, deleted `red`, conflict `yellow`, ignored `text-disabled`.
- Background tints (diff lines, file colors, banners): `-soft` or `-mid` steps so text stays readable.
- A color Themer lacks is better added to Themer (`themer/themer`, a new filter or token) than computed here.

## GitHub Copilot plugin colors

Copilot hardcodes most chat colors. `reload-plugin/.../CopilotColorPatcher.kt` maps `Copilot.*` keys in
the UI theme template onto the plugin's static color fields at startup and on every Look and Feel change:

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
