---
name: update-color-scheme
description: Apply a hand-edited or exported .icls file back into the Themer template themer.icls using Themer tokens. Use when the user tweaked editor colors in the IDE and wants them in the template.
---

# Update Color Scheme Template

Apply hand-edited ICLS color changes back into the Themer template
`~/.config/themer/templates/jetbrains/themer.icls` (work in a dotfiles worktree if another agent is active).

You are given a path to an edited `.icls` file. Your job is to diff it against the
template and apply every change using the right Themer expression.

Values in the template are `{{ expr | strip }}` tags: `expr` is a Themer token (`syntax-keyword`, `bg-sunken`,
`red-dim`) or a filter chain (`red-dim | mix(red, 0.5)`); `strip` removes the `#` the ICLS format does not want.

## Step 1 — Run the diff script

```bash
python3 scripts/diff-color-changes.py <path-to-edited.icls>
```

If no path was provided by the user, ask which file to diff against.

The script outputs three sections. Process each one fully before moving to the next.

## Step 2 — Process VALUE CHANGES

For each entry the script shows:
- `template:` — the current `{{ expr }}` and its resolved hex
- `edited:` — the target hex
- `candidates:` — Themer expressions matching the target, sorted by semantic relevance

**Pick the variable** using these rules (in priority order):

1. **Exact semantic match** — if the option name tells you what the color represents,
   pick the variable whose documented purpose matches:
   - Keyword-like options (`*KEYWORD*`, `*MODIFIER*`) → `syntax-keyword`
   - Function/method options (`*FUNCTION*`, `*METHOD*`, `*CALL*`) → `syntax-function`
   - Class/interface options (`*CLASS*`, `*INTERFACE*`, `*TYPE_REFERENCE*`) → `syntax-class` or `syntax-type`
   - String options (`*STRING*`, `*HEREDOC*`) → `syntax-string`
   - Comment options (`*COMMENT*`, `*DOC_COMMENT*`) → `syntax-comment`
   - Number/constant options (`*NUMBER*`, `*CONSTANT*`) → `syntax-number` or `syntax-constant`
   - Variable/field options (`*VARIABLE*`, `*FIELD*`, `*PROPERTY*`) → `syntax-variable`
   - Annotation/attribute options (`*ANNOTATION*`, `*ATTRIBUTE*`, `*DECORATOR*`) → `syntax-annotation`
   - Escape sequence options (`*ESCAPE*`) → `syntax-escape`
   - Doc tag options (`*DOC_TAG*`, `*TAG*` in doc context) → `syntax-doc-tag`
   - Operator options (`*OPERATOR*`) → `syntax-operator`
   - Punctuation options (`*BRACE*`, `*BRACKET*`, `*PAREN*`) → `syntax-punctuation`

2. **UI semantic match** — for non-syntax options (backgrounds, headers, links):
   - Background options → `bg`, `bg-sunken`, `surface`, `surface-raised`
   - Foreground/text options → `text`, `text-muted`, `text-subtle`, `text-disabled`
   - Header/title options → `accent` (headers should stand out)
   - Link/URL options → `textLink` or `syntax-string` (depending on context)
   - Error stripe/effect → `danger`, `warning`, `info` (match the severity)
   - Selection/highlight → `selection`, `surface-hover`, `surface-active`
   - Border → `line`, `surface-hover`, `focus-ring`

3. **First candidate** — if no semantic rule applies, use the first candidate from the
   script output (they are sorted by semantic relevance).

4. **Hue step** — if the first candidate is a raw hue step (e.g. `blue`, `red-dim`),
   that's fine. Use it.

**Apply the change** in `themer.icls`: find the `<option>` block and replace
the `value="{{ old | strip }}"` with `value="{{ new | strip }}"`.

## Step 3 — Process REMOVE FROM TEMPLATE

For each `✕` entry, find and delete the entire XML block from `themer.icls`.

- For entries like `attributes/SOME_NAME/FOREGROUND`: if that's the **only** sub-option
  in its parent `<option name="SOME_NAME">` block, remove the entire parent block.
  If other sub-options remain, remove only the specific `<option name="FOREGROUND" .../>` line.
- For `@baseAttributes` entries: remove the entire `<option name="..." baseAttributes="..."/>` line.

## Step 4 — Process ADD TO TEMPLATE

For each `+` entry, add it to `themer.icls` in **alphabetical order** within
the correct section (`<colors>` or `<attributes>`).

### Adding value options

If the entry is `attributes/OPTION_NAME/SUB_OPTION = HEX_VALUE`:

1. Check if `<option name="OPTION_NAME">` already exists in the template.
   - **Yes**: add the sub-option inside its existing `<value>` block.
   - **No**: create a new block. Use `grep` to find the alphabetical neighbors, then insert.

2. Pick the expression for the hex value using the same rules from Step 2.

3. Use this XML format:
   ```xml
   <option name="OPTION_NAME">
     <value>
       <option name="SUB_OPTION" value="{{ chosen | strip }}"/>
     </value>
   </option>
   ```

4. For non-color values (like `EFFECT_TYPE`, `FONT_TYPE`), use the literal number — no variable.

### Adding baseAttributes options

If the entry is `attributes/OPTION_NAME/@baseAttributes = PARENT_NAME`:

Insert a single self-closing tag in alphabetical order:
```xml
<option name="OPTION_NAME" baseAttributes="PARENT_NAME"/>
```

## Step 5 — Verify

Re-render with `themer apply --only jetbrains --force` (from the dotfiles folder holding the edited template), then
run the diff script again:

```bash
python3 scripts/diff-color-changes.py <same-path>
```

It **must** report `No differences found.` If not, fix the remaining issues and re-verify.

## Important rules

- **Never write raw hex values** in the template. Always use Themer `{{ ... | strip }}` tags
  for color values. The only literals allowed are non-color values like `EFFECT_TYPE`
  and `FONT_TYPE` integers.
- **Preserve indentation**: 2-space indent inside XML, matching the surrounding context.
- **Alphabetical order**: new entries must be inserted in the correct alphabetical position
  within `<colors>` or `<attributes>`.
- If an option has both a `<value>` block AND a `baseAttributes` — `baseAttributes` wins.
  The `<value>` children are ignored when `baseAttributes` is present.
