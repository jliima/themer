# Themer live settings for Firefox

Firefox reads `userChrome.css`, `userContent.css` and `user.js` only when it starts. This plugin lets Themer change a
few things in a running Firefox, in every profile: the default page zoom, preferences, and a scale for the font sizes
in `userChrome.css`. Screen profiles (`themer screens`, `[[profile]]` in `settings.toml`) use it to make Firefox larger
on a big screen and smaller again when it is unplugged.

```
themer apply ──► ~/.cache/themer/firefox/live.json ──(checked every 2 s)──► themer.cfg in Firefox ──► zoom, prefs, UI scale
```

## Install

```sh
./install.sh          # sudo: copies themer.cfg and defaults/pref/themer-autoconfig.js into /usr/lib/firefox
```

Then restart Firefox once. It uses Firefox's
[autoconfig](https://support.mozilla.org/kb/customizing-firefox-using-autoconfig): `themer-autoconfig.js` names
`themer.cfg`, a script Firefox runs with chrome privileges at startup. The Snap and Flatpak builds cannot load it;
Mozilla's apt package, the tarball and distribution packages can. Package upgrades keep the files. Run `install.sh`
again after pulling a new version of this plugin; `--uninstall` removes them.

## live.json

The target "Firefox live settings" renders it from your template `~/.config/themer/templates/firefox/live.json`, so
its values can be tokens:

```json
{
  "zoom": {{ firefox.zoom }},
  "ui-scale": {{ firefox.ui-scale }},
  "prefs": {
    "font.name.sans-serif.x-western": "{{ fonts.sans }}",
    "font.name.monospace.x-western": "{{ fonts.mono }}"
  }
}
```

| Key | Effect |
| --- | --- |
| `zoom` | The default zoom (Settings > Zoom). Open tabs follow at once; sites with their own zoom keep it. `1` resets it. |
| `ui-scale` | Set as `--themer-ui-scale` on every browser window. Use it in `userChrome.css`: `font-size: calc(12px * var(--themer-ui-scale, 1))`. |
| `prefs` | Preferences to set: strings, integers and booleans, as in `user.js`. |

The file is applied when its time stamp changes, and at every start. Errors show in the Browser Console
(Ctrl+Shift+J) as `themer.cfg: ...`.
