# Pare

The bundled Themer theme, generated from the Pare design system's `tokens.json`.

- Dark first: a deep cool blue-grey ground (`bg` #091017), one neutral family at OKLCH hue 248, and eight accents
  tuned so each reads as text on every ground. The light variant mirrors it hue for hue.
- Accent is blue (#5faff1 dark, #156eac light). Green is the signature mint for keywords and success.
- Fonts: SF Pro for the UI at Medium (500), a touch heavier than Regular so text holds up on the dark grounds;
  window titles at Semibold (600). Liga SFMono Nerd Font at Regular for code and terminals.
- Every pair in `themer check --theme pare` passes WCAG 4.5:1 for text and 3:1 for borders and focus rings.

Apply it with `themer apply --theme pare` or `themer apply --theme pare:light`. To change it, `themer edit pare`
copies it to your themes folder (`~/dotfiles/.config/themer/themes/pare/` in dotfiles mode), which then wins over
this bundled copy; `themer remove pare` brings this one back.

After changing colors in the design system, rebuild it with
`themer import tokens.json --id pare --name Pare --replace`.
