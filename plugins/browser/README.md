# Themer for Dark Reader and Stylus

Two browser extensions follow Themer live, in Firefox and in Chromium-based browsers:

- **Dark Reader Themer** (fork of [Dark Reader](https://github.com/darkreader/darkreader), `~/Git/darkreader-themer`):
  page background and text from the theme, plus any Dark Reader setting you put in a template (mode, contrast,
  brightness, sepia, engine, selection and scrollbar colors, on/off, ...).
- **Stylus Themer** (fork of [Stylus](https://github.com/openstyles/stylus), `~/Git/stylus-themer`): user styles can
  use the theme as CSS variables, `var(--themer-accent)`, `var(--themer-bg)`, `var(--themer-font-sans)`,
  `var(--themer-radius-md)`, with the names of `~/.cache/themer/colors.css`. UserCSS styles are also kept as files
  in a folder, so they can be edited, versioned and shared outside the browser.

Open tabs restyle the moment `themer apply` or `themer mode toggle` finishes; nothing reloads.

```
themer apply ──► ~/.cache/themer/browser/tokens.json, darkreader.json
                     │ inotify
                     ▼
              themer-browser-host ──(native messaging, stdio)──► extension background ──► open tabs
                     ▲
                     │ inotify, both ways
              <styles folder>/*.user.css  (Stylus only)
```

`themer-browser-host` is a native messaging host (Python, standard library only). The browser starts it when an
extension connects and stops it when the browser closes; there is no daemon. Extensions can not read local files, and
this is the WebExtension way for a local program to talk to one. The host only answers the two extension IDs in
`install.sh`.

## Install

```sh
./install.sh                                    # register the host with Firefox and every Chromium-based browser
~/Git/darkreader-themer/themer-build.sh         # build the extensions (npm, pnpm through npx)
~/Git/stylus-themer/themer-build.sh
./install.sh --firefox-xpi ~/Git/darkreader-themer/build/release/darkreader-firefox.xpi \
                           ~/Git/stylus-themer/dist-xpi/stylus-themer.xpi
themer apply --only browser
```

The top-level `install.sh` of Themer runs the first line for you. Run the others again after pulling a fork.

**Firefox** release builds only load add-ons that Mozilla signed, except from the installation's own
`browser/extensions/` folder in builds made with `MOZ_UNSIGNED_APP_SCOPE` (the Ubuntu and Debian packages, and
Mozilla's are not). `--firefox-xpi` copies the builds there as `<id>.xpi` (sudo) and adds
`defaults/pref/themer-extensions.js`, so Firefox looks at that folder at every start and does not disable what it
finds. Restart Firefox; the extensions are in every profile and can be turned off per profile in about:addons. Disable
the original Dark Reader and Stylus where both are installed. In Firefox Developer Edition or Nightly you can instead
set `xpinstall.signatures.required` to false and install the .xpi files from about:addons.

**Chromium, Chrome, Brave, Vivaldi, Edge**: open `chrome://extensions`, turn on Developer mode, "Load unpacked" and
pick `~/Git/darkreader-themer/build/release/chrome-mv3` and `~/Git/stylus-themer/dist-chrome-mv3`. The public key in
each manifest keeps the extension IDs fixed, which is what the host allows. A rebuild needs the reload button there.

## Dark Reader settings

The target "Dark Reader settings" renders your template `~/.config/themer/templates/browser/darkreader.json` to
`~/.cache/themer/browser/darkreader.json`. It is a partial Dark Reader settings object: what it names is set, the rest
is left as you set it in the popup. Without a template the background and text follow `bg` and `text`, and the mode
follows the variant.

```json
{
  "enabled": true,
  "theme": {
    "mode": {{ is-dark | pick(1, 0) }},
    "contrast": 100,
    "{{ is-dark | pick(darkScheme, lightScheme) }}BackgroundColor": "{{ bg }}",
    "{{ is-dark | pick(darkScheme, lightScheme) }}TextColor": "{{ text }}",
    "selectionColor": "{{ selection }}"
  }
}
```

The keys are those of Dark Reader's `UserSettings` and `Theme` (`src/definitions.d.ts` in the fork): `theme.mode` (1
dark, 0 light), `brightness`, `contrast` (0 to 200), `grayscale`, `sepia` (0 to 100), `engine` (`dynamicTheme`,
`staticTheme`, `cssFilter`, `svgFilter`), `useFont`, `fontFamily`, `textStroke`, `scrollbarColor`, `selectionColor`,
`styleSystemControls`, and top-level ones like `enabled`, `changeBrowserTheme` or `automation`. Colors are `#rrggbb`.
Unknown keys and values Dark Reader rejects are skipped and logged to `~/.local/state/themer/browser-host.log`.

## Stylus

### Variables

Every token of the applied variant, plus the fonts and radii, as in `colors.css`:

```css
@-moz-document domain("example.com") {
  body { background: var(--themer-bg); color: var(--themer-text); }
  a { color: var(--themer-accent); }
  pre, code { font-family: var(--themer-font-mono); border-radius: var(--themer-radius-sm); }
}
```

They are set on `:root` only in pages (and frames) where an applied style mentions `--themer-`. They do not count as a
style in the toolbar badge.

### Styles folder

Every UserCSS style is mirrored to one `*.user.css` file:

- Saving a style in the editor writes its file; a new UserCSS style gets a file named after it.
- Editing a file outside the browser updates the style in open tabs. A new file installs a new style (it needs a
  `==UserStyle==` header with `@name` and `@namespace`).
- Deleting a file while the browser runs deletes its style. Deleting a style in the browser moves its file to
  `.deleted/` in the folder.
- Subfolders work like the folder itself, at any depth. Moving or renaming a file (or a whole subfolder) keeps its
  style as it was, enabled or not; a style made in the browser gets its file at the top. Hidden files and folders
  (`.deleted`, `.git`, editor temp files) are left alone.
- When the extension connects, files and styles are matched by file name, then by `@name` and `@namespace`; where
  both changed, the newer one wins. A style without a file is exported, also one whose file was deleted while the
  browser was closed.

Classic (non-UserCSS) styles are not mirrored. To convert one, use Export in its editor, copy the text into a new
style made with "Write new style as UserCSS" on, and delete the old one (or drop a `.user.css` file into the folder).
Turn the folder off in Stylus options, Advanced, "Mirror UserCSS styles to Themer's styles folder".

The folder is `stylus/` next to the real `settings.toml` (in the dotfiles when they are stowed, so the styles are
versioned with them), or:

```toml
[browser]
stylus-styles = "~/somewhere/else"
```

Styles you do not want in a public dotfiles repository can live in a git-ignored subfolder, for example `vault/` with
`**/vault/` in `.gitignore`, synced between machines some other way (Syncthing).

## Troubleshooting

- `~/.local/state/themer/browser-host.log`: host errors and what the extensions skipped.
- Firefox: about:debugging, the extension's Inspect, Console. Chromium: chrome://extensions, "service worker".
  "Specified native messaging host not found" means `install.sh` did not run for that browser, or the extension ID
  differs from the ones in `install.sh`. A browser started with its own `--user-data-dir` looks for the host in
  `<that dir>/NativeMessagingHosts/`.
- The extensions reconnect on their own (5 s, doubling to 5 min) when the host was missing or stopped.
