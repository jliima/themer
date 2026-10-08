# Themer

Themer installs a design system into every app on the desktop. A theme is a small folder with a `theme.toml` that
fills in a shared set of token names (grounds, text, eight hues, roles, syntax and terminal colors). Themer turns
those tokens into Plasma color schemes, Darkly and window decoration settings, fonts, Konsole schemes and profile,
Kate syntax themes, GTK 4 colors, Firefox `userChrome.css` / `userContent.css`, and pywal-compatible exports.
Any design system that uses the same token names works the same way.

```sh
themer apply --theme pare               # Pare, its default variant (dark)
themer apply --theme pare:light         # or: themer apply --theme pare --variant light
themer mode toggle                      # same theme, other variant
themer themes                           # what is installed
```

Bundled: **Pare** (`themes/pare`), cool blue-grey neutrals with tuned accents, dark and light.

Python 3.11 or newer, standard library only.

## Install into dotfiles

Themer is made to live in a dotfiles folder that mirrors `~` and is linked with GNU Stow (`stow .` from the folder).
Unpack it as `~/dotfiles/themer`, then:

```sh
cd ~/dotfiles/themer
./install.sh                            # see below; needs stow (sudo apt install stow)
themer doctor                           # Darkly, fonts, Firefox profile, dotfiles, KDE tools
themer apply --theme pare --dry-run     # every file it would write
themer apply --theme pare
```

`install.sh` does five things, and is safe to run again:

1. Adds `^/themer$` to `~/dotfiles/.stow-local-ignore` so stow does not link the tool itself to `~/themer`. If the
   file does not exist it is created with Stow's default ignore list first, because a local list replaces the
   defaults.
2. Moves an earlier plain install (a real `~/.config/themer` folder) into `~/dotfiles/.config/themer`, keeping a
   backup in `~/.local/state/themer`, and removes an old `~/.local/bin/themer` link.
3. Creates `~/dotfiles/.config/themer/` with `settings.toml` (dotfiles on), `themes/`, `templates/` and the Firefox
   snippet folders, plus the example snippet. Existing files are never overwritten.
4. Adds `~/dotfiles/.local/bin/themer`, a relative link to `themer/themer`.
5. Runs `stow --no-folding --dir=~/dotfiles --target=~ .`, so `~/.config/themer` and `~/.local/bin/themer` point
   into the dotfiles folder. This is the same as your `stow .`; links that already exist are left alone.

Other options: `./install.sh --dotfiles ~/elsewhere` for a different dotfiles folder, `./install.sh --no-dotfiles`
for a plain install into `~/.config/themer` with no stow.

Restart Firefox and open Qt apps once after the first apply. Konsole uses the "Themer" profile in new windows; Kate
switches to the "Themer Dark" or "Themer Light" syntax theme.

## Dotfiles and stow

With `[dotfiles]` on in `settings.toml`:

- **Your files** (themes, template overrides, Firefox snippets, `settings.toml`, an optional `targets.toml`) live in
  `~/dotfiles/.config/themer/`. Commands that create them (`new`, `edit`, `set`, `install`, `import`) write there and
  run stow.
- **Generated files Themer owns** are written into the dotfiles folder at their path relative to `~` and stowed:
  Plasma color schemes, Konsole color schemes and the Themer profile, Kate syntax themes, `~/.config/gtk-4.0/themer.css`
  and the pywal theme files. They are marked `dotfiles = true` in `targets.toml`. If an earlier run left a real file
  where the link should go, Themer backs it up and replaces it with the link.
- **Merged config files** (`kdeglobals`, `kwinrc`, `katerc`, `darklyrc`, `konsolerc`, Firefox `user.js`, the
  `gtk.css` import line) are edited in place, keeping everything Themer does not set. If you stow one of them
  yourself, Themer writes through the link into your dotfiles copy.
- **Machine-specific output** stays out of the repo: the Firefox profile's `chrome/` folder (its name differs on every
  machine), `~/.cache/themer`, `~/.cache/wal`, and backups and state in `~/.local/state/themer`.
- `themer apply` runs stow when one of its files is not linked yet, then links by itself any of its own files stow
  skipped (for example when stow stops on an unrelated conflict elsewhere in your dotfiles) and tells you why.
  `themer stow` runs stow by hand. The command is `[dotfiles] stow` in settings.toml; set it to `""` to run stow
  yourself.

The stow command uses `--no-folding`, so a folder that does not exist yet in `~` (say
`~/.local/share/org.kde.syntax-highlighting`) is created as a real folder with links to each file, instead of one
link to the whole folder. That keeps files other apps save there out of your dotfiles. Folders your own `stow .`
already folded stay folded; Themer then writes into them through the link, which ends up in the same place.

Since the generated files are in the repo, a second machine that pulls your dotfiles and runs `stow .` gets the
color schemes and profiles even before Themer runs there; `themer apply` then does the merged files and Firefox.

## Commands

| Command | What it does |
| --- | --- |
| `themer apply [--theme ID[:variant]] [--variant dark\|light]` | Render every target and reload Plasma, KWin and GTK. Without `--theme`, re-applies the current theme. |
| `themer apply --only kde,konsole` | Only some groups: `kde`, `konsole`, `kate`, `gtk`, `firefox`, `exports`. |
| `themer mode dark` / `light` / `toggle` | Switch the current theme's variant. Bind `themer mode toggle` to a shortcut in System Settings. |
| `themer themes`, `themer current` | Installed themes (bundled, user, edited) and the applied one. |
| `themer check --theme ID` | Text contrast report for every variant. Exits 1 if a pair fails. |
| `themer validate --theme ID` | Checks the theme fills the token contract. `apply` refuses a theme that does not. |
| `themer show`, `themer tokens` | Swatches in the terminal; every resolved token. |
| `themer get accent`, `themer get 'accent \| rgb' --theme ID` | One value, for scripts. |
| `themer set blue '#62b5fb' [--theme ID --variant dark]` | Change a value in place. A bundled theme is copied to your config first. |
| `themer new ID --from pare [--name "My Theme"]` | Start a theme from an existing one. |
| `themer edit [ID]` | Open a theme in `$EDITOR` (bundled themes are copied first). |
| `themer install PATH` | Install a theme folder, `theme.toml` or `.zip` into your themes folder. |
| `themer import tokens.json --id ID --name NAME` | Make a theme from a design system's `tokens.json`. |
| `themer remove ID` | Remove a user theme. Removing an edited bundled theme brings the original back. |
| `themer undo` | Restore the files the last apply changed (15 runs of backups in `~/.local/state/themer/backups`). |
| `themer stow` | Run the configured stow command (dotfiles mode). |
| `themer screens` | Recommended Plasma scale for each screen, with `kscreen-doctor` commands. |

## How it fits together

```
~/dotfiles/
  .stow-local-ignore         ^/themer$ keeps the tool itself out of ~
  themer/                    the tool (not stowed)
    themer                   the command
    defaults.toml            fallbacks every theme is layered over: roles, syntax, terminal colors, fonts, KDE
    contract.toml            the token names a theme must resolve
    targets.toml             what gets written where (same for every theme)
    templates/               one file per app integration
    themes/pare/             the bundled Pare theme
    skel/                    what install.sh copies into .config/themer
  .local/bin/themer          link to ../../themer/themer, stowed to ~/.local/bin/themer
  .config/themer/            stowed to ~/.config/themer
    settings.toml            machine settings: dotfiles, default theme, Firefox profile
    themes/<id>/             your themes, and edited copies of bundled ones (these win)
    templates/               your template overrides and additions (these win)
    targets.toml             optional: read on top of the shipped one, to add, replace or disable targets
    firefox/chrome/*.css     snippets added to the end of userChrome.css
    firefox/content/*.css    snippets added to the end of userContent.css
  .local/share/..., .config/gtk-4.0/themer.css, .config/wal/...   generated by themer apply, stowed
```

Lookup order for a template is `~/.config/themer/templates`, then the theme's own `templates/` folder, then the
shipped `templates/`. So a theme can ship its own Konsole profile or userChrome.css, and you can override any of
them without touching the theme.

Names that let apps follow theme changes without reselecting anything stay fixed: the Konsole profile is
`Themer.profile` and Kate's syntax themes are "Themer Dark" and "Themer Light". Plasma color schemes and Konsole
color schemes carry the theme name (`PareDark`, `PareLight.colorscheme`) so you can still pick them by hand.

## Window decoration and rounded corners

`decoration/` is a KWin window decoration drawn from the theme: title bar, round buttons, corner radius, ring and
shadow all come from tokens (`[window]` and the `titlebar-*` / `window-*` roles in `defaults.toml`, overridable per
theme). Build it with `decoration/build.sh` and select it in `settings.toml`; see `decoration/README.md`.

If the KDE-Rounded-Corners effect is installed, the "Rounded corners effect" target sets its radius to
`shape.radius-lg` and its ring to `window-outline`, so windows that draw their own title bar match.

## Machine overrides

`[overrides.<table>]` in `settings.toml` sets non-color values that win over every theme on this machine, with the
same table and key names as a `theme.toml`, e.g. `[overrides.kde] decoration-library = "themer"`.

## Firefox snippets

Every `.css` file in `~/.config/themer/firefox/chrome/` is appended to `userChrome.css` on `themer apply`, in file
name order, after the theme's own rules so it wins. Files in `firefox/content/` go to the end of `userContent.css`.
Name files `10-...`, `20-...` to order them; start a name with `_` to switch one off. A theme can ship snippets the
same way in its own `firefox/chrome/` and `firefox/content/` folders; a file of yours with the same name replaces
the theme's.

Snippets can use theme colors two ways: `var(--themer-accent)` (any token, from `themer-colors.css`) or
double-brace tokens like the templates (`{{ accent }}`, `{{ surface | alpha(0.8) }}`), which are filled in when
applied. An `@import` in a snippet is moved to the top of the file, where Firefox requires it.

If the profile already had a hand-written `userChrome.css` or `userContent.css` (not made by Themer), the first apply
keeps a copy as `firefox/chrome/_previous-userChrome.css` (and `firefox/content/_previous-userContent.css`). The
leading `_` keeps it off; rename it to layer your old rules on top of the theme.

The example installed by default, `bookmark-icons-only.css`, hides the label of every bookmarks toolbar item whose
name starts with `*`, so `*GitHub` shows just its icon.

## Making a theme

See [THEMES.md](THEMES.md) for the token contract and a complete minimal example. The short version:

```sh
themer new nord-ish --from pare --name "Nord-ish"
themer edit nord-ish                     # change colors
themer check --theme nord-ish
themer apply --theme nord-ish
```

A theme only has to define grounds, lines, text and the eight hues for each variant it supports. Roles, syntax
colors, terminal colors, hue steps, fonts and shapes fall back to `defaults.toml`.

## Adding an app

1. Write a template in `~/.config/themer/templates/`, for example `alacritty/colors.toml`:

   ```toml
   [colors.primary]
   background = "{{ bg }}"
   foreground = "{{ text }}"
   [colors.normal]
   blue = "{{ ansi-4 }}"
   ```

2. Add a target to `~/.config/themer/targets.toml`. That file is read on top of the shipped `targets.toml`: a
   target with a shipped name replaces it (`enabled = false` turns it off), any other name is added:

   ```toml
   [[target]]
   name = "Alacritty"
   group = "terminal"
   template = "alacritty/colors.toml"
   output = "~/.config/alacritty/themer.toml"
   ```

3. `themer apply --only terminal`. Every theme now themes Alacritty too.

Template syntax: `{{ token }}` gives `#rrggbb`; filters chain with `|`:

| Filter | Result for `accent` in Pare dark |
| --- | --- |
| `rgb` | `95,175,241` (KDE config files) |
| `strip` | `5faff1` |
| `rgbcss` | `rgb(95, 175, 241)` |
| `rgba(0.5)` | `rgba(95, 175, 241, 0.5)` |
| `alpha(0.5)` | `#5faff180` |
| `mix(bg, 0.4)` | 40% of the way from accent to bg, in OKLab |
| `lighten(0.05)`, `darken(0.05)` | OKLCH lightness shifted |
| `oklch` | `oklch(0.730 0.125 246.0)` |

Names available in templates besides the tokens: `theme` (`pare`), `name` (`Pare`), `variant` (`dark`), `Variant`
(`Dark`), `scheme` (`PareDark`), `is-dark`, `is-light`, and every key of the theme's non-color tables as
`table.key`: `fonts.sans`, `fonts.mono-size`, `fonts.ui-weight`, `shape.radius-sm`, `kde.widget-style`,
`konsole.margin`, `firefox.compact`. Numbers take `px`, `int` and `div(2)`.

Exports refreshed on every apply, for scripts and apps without a template: `~/.cache/themer/colors.json`,
`colors.css` (CSS variables `--themer-*`, every variant), `colors.sh` (`THEMER_ACCENT` and friends), and
pywal-compatible `~/.cache/wal/colors.json`, `colors.sh`, `colors.css`. Existing pywal templates can render from
the same palette with `wal --theme ~/.config/wal/colorschemes/dark/pare.json`.

## What it writes

| App | Files | Notes |
| --- | --- | --- |
| Plasma | `~/.local/share/color-schemes/<Name><Variant>.colors` | Applied with `plasma-apply-colorscheme`. Title bars and panels `bg-deep`, windows `bg`, views and inputs `bg-sunken`. |
| Plasma | `~/.config/kdeglobals` (merged) | Fonts from `[fonts]` with their weights (`ui-weight`, `title-weight`, `mono-weight`), widget style from `[kde]`, wallpaper accent off so the theme's accent wins. |
| Darkly | `~/.config/darklyrc` (merged) | Control radius `radius-sm`, window corners `radius-lg`, flat centered title bars, accent tab highlight. |
| KWin | `~/.config/kwinrc` (merged) | Decoration from `[kde]`, buttons minimize, maximize, close on the right. |
| Konsole | `<Name><Variant>.colorscheme` per variant, `Themer.profile`, `konsolerc` (merged) | Mono font, margin, accent I-beam cursor, hidden scrollbar. |
| Kate, KWrite | `Themer-Dark.theme`, `Themer-Light.theme`, `katerc` (merged) | Kate is switched to the Themer theme of the applied variant. |
| GTK 4 | `~/.config/gtk-4.0/themer.css`, an import line in `gtk.css` | libadwaita accent, header bars, sidebars, cards. |
| Firefox | `<profile>/chrome/themer-colors.css`, `userChrome.css`, `userContent.css`, lines in `user.js` | Enables userChrome loading, compact density, websites follow the variant. Snippets are appended to the css files. |

Files marked dotfiles in the table above (color schemes, Konsole, Kate, GTK css) go through your dotfiles folder when
dotfiles mode is on. Merged files keep every key Themer does not set. Every overwritten file is backed up first;
`themer undo` restores the last run.

## Screens

Plasma scales each display separately. These make one logical pixel look the same size everywhere: 27" 1440p at
100%, 32" 4K at 150% (both end up with a 2560x1440 workspace), 14" T14 at 125%. Keep fonts in points; the scale
does the rest. `themer screens` prints the commands.
