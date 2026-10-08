# Writing a Themer theme

A theme is a folder with a `theme.toml`, installed under `~/.config/themer/themes/<id>/` (or shipped in
`themes/<id>/` next to the tool). It may also carry a `README.md`, a `templates/` folder whose files replace the
shipped templates of the same path while the theme is applied, and `firefox/chrome/` and `firefox/content/` folders
of CSS snippets that are appended to `userChrome.css` and `userContent.css` (a user snippet with the same file name
replaces the theme's).

## theme.toml

```toml
[meta]
id = "ember"                       # lowercase, digits, - and _; the folder name if left out
name = "Ember"                     # shown in color scheme names: EmberDark, EmberLight
description = "Warm greys, orange accent"
version = "1.0.0"
variants = ["dark", "light"]       # any of dark, light; one is fine
default-variant = "dark"

[fonts]                            # optional, see defaults.toml
sans = "Inter"
mono = "JetBrains Mono"
ui-weight = 500                    # 100 to 900: Plasma UI text; title-weight and mono-weight too

[shape]                            # optional, logical px
radius-sm = 4

[roles]                            # optional; applies to every variant
accent = "{orange}"
accent-hover = "{orange-bright}"
accent-soft = "{orange-soft}"

[dark]                             # one table per variant
bg = "oklch(0.19 0.013 60)"
# ...
```

Color values are `"#rrggbb"`, `"oklch(L C H)"` or an alias `"{token}"`. Aliases resolve within the variant, so
`accent = "{orange}"` picks the dark orange in `[dark]` and the light orange in `[light]`.

Colors resolve by precedence: the theme's variant table, then the theme's `[roles]`, then `defaults.toml`'s variant
table, then `defaults.toml`'s `[roles]`. Other tables (`fonts`, `shape`, `kde`, `konsole`, `firefox`) merge key by
key over the defaults.

## The token contract

`contract.toml` lists every name templates use. `themer validate --theme <id>` checks a theme resolves all of them in
each variant, and `themer apply` refuses a theme that does not. What a theme must define itself, per variant:

| Group | Tokens | Meaning |
| --- | --- | --- |
| Grounds | `bg-deep`, `bg-sunken`, `bg`, `surface`, `surface-raised`, `surface-hover`, `surface-active` | Deepest to highest: title bars and panels, sidebars and inputs, windows, cards, menus, hover, pressed. |
| Lines | `line`, `line-strong` | Hairlines; borders that must be seen (3:1 on the grounds). |
| Text | `text-bright`, `text`, `text-muted`, `text-subtle`, `text-faint`, `text-disabled` | Brightest to dimmest. The first four should hold 4.5:1 on every ground. |
| Hues | `red`, `orange`, `yellow`, `green`, `cyan`, `blue`, `violet`, `magenta` | Readable as text on `bg`. |

Everything else has a default you can override:

| Group | Tokens | Default |
| --- | --- | --- |
| Hue steps | `<hue>-bright`, `<hue>-dim`, `<hue>-soft` | Derived in OKLCH from the base hue: brighter, a mid tone for borders, a tinted ground. |
| Roles | `accent`, `accent-hover`, `accent-soft`, `focus-ring`, `link`, `success`, `warning`, `danger`, `info` and their `-soft` grounds | Blue accent, green success, orange warning, red danger, cyan info. |
| Fills | `on-accent`, `selection`, `text-inverse` | Dark: `bg-deep` text on fills, a mid blue selection. Light: white text, a pale blue selection. |
| KDE | `kde-selection`, `kde-selection-text` | `selection` with `text`. Use `accent` with `on-accent` for vivid selections. |
| Syntax | `syntax-keyword`, `string`, `escape`, `number`, `constant`, `function`, `class`, `type`, `annotation`, `doc-tag`, `property`, `tag`, `attribute`, `variable`, `operator`, `punctuation`, `comment`, `heading`, `link`, `url`, `regex` (all `syntax-` prefixed) | Green structure, magenta literals, cyan names, blue calls and links, red values, orange and violet metadata. |
| Terminal | `ansi-0` to `ansi-15` | Hues and their bright steps, `surface-active` and `text-faint` for black and bright black. |

Any extra token a theme defines is available to templates too.

## A complete minimal theme

```toml
[meta]
id = "ember"
name = "Ember"
variants = ["dark"]

[roles]
accent = "{orange}"
accent-hover = "{orange-bright}"
accent-soft = "{orange-soft}"

[dark]
bg-deep = "oklch(0.15 0.012 60)"
bg-sunken = "oklch(0.17 0.012 60)"
bg = "oklch(0.19 0.013 60)"
surface = "oklch(0.23 0.015 60)"
surface-raised = "oklch(0.26 0.016 60)"
surface-hover = "oklch(0.29 0.017 60)"
surface-active = "oklch(0.33 0.018 60)"
line = "oklch(0.31 0.016 60)"
line-strong = "oklch(0.53 0.02 60)"
text-bright = "oklch(0.96 0.01 60)"
text = "oklch(0.9 0.015 60)"
text-muted = "oklch(0.79 0.018 60)"
text-subtle = "oklch(0.69 0.02 60)"
text-faint = "oklch(0.62 0.02 60)"
text-disabled = "oklch(0.47 0.02 60)"
red = "oklch(0.68 0.18 25)"
orange = "oklch(0.75 0.15 55)"
yellow = "oklch(0.85 0.14 90)"
green = "oklch(0.76 0.14 145)"
cyan = "oklch(0.76 0.11 195)"
blue = "oklch(0.74 0.11 245)"
violet = "oklch(0.72 0.13 300)"
magenta = "oklch(0.72 0.16 350)"
```

`themer install ./ember && themer check --theme ember && themer apply --theme ember`.

## From a design system

A design system whose `tokens.json` has color tokens with these names (a list of `{name, value: {dark, light}}`)
becomes a theme with `themer import tokens.json --id <id> --name <Name>`. It takes fonts from `type.families` and
corner radii from `radius`, writes aliases where the design system used them, and puts the result in
`~/.config/themer/themes/<id>/`. The bundled Pare theme was made this way from the Pare design system.

## Sharing a theme

Zip the folder and `themer install theme.zip` on the other machine. A theme never contains paths or commands; what
gets written where is decided by `targets.toml` on the machine that applies it.
