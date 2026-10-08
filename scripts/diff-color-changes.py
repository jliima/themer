#!/usr/bin/env python3
"""Diff color values between the Themer-rendered ICLS and a hand-edited ICLS file.

Compares the editor scheme Themer wrote into an IDE (colors/Themer.icls) against an edited file, option by option,
and suggests the Themer expression for every new color: a token (`syntax-keyword`) or a derived color from the UI
theme template's `colors` section (`red-dim | mix(red, 0.5)`).

Usage:
    python3 scripts/diff-color-changes.py <edited.icls> [applied.icls]

Arguments:
    edited.icls   Path to the hand-edited or IDE-exported ICLS file
    applied.icls  What Themer rendered (default: the newest ~/.config/JetBrains/*/colors/Themer.icls)

Environment:
    THEMER_JETBRAINS_TEMPLATES  folder with themer.icls and plugin/theme/themer.theme.json
                                (default ~/.config/themer/templates/jetbrains)

Examples:
    python3 scripts/diff-color-changes.py ~/Downloads/edited.icls
"""
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TEMPLATES = Path(os.environ.get("THEMER_JETBRAINS_TEMPLATES",
                                Path.home() / ".config/themer/templates/jetbrains"))
TEMPLATE = TEMPLATES / "themer.icls"
THEME_TEMPLATE = TEMPLATES / "plugin/theme/themer.theme.json"
THEME_JSON = Path.home() / ".cache/themer/jetbrains/themer.theme.json"

# Semantic expressions are preferred over raw hue steps when suggesting replacements. Higher priority = listed first.
SEMANTIC_PREFIXES = [
  "syntax-", "bg", "text", "surface", "accent", "line", "focus-ring", "selection", "link",
  "success", "warning", "danger", "info",
]

# ANSI colors for terminal output
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


TAG_RE = re.compile(r"\{\{\s*(.+?)\s*\}\}")


def tag_expression(value: str) -> str | None:
  """The Themer expression of a value that is one {{ ... }} tag, without the `| strip` that drops the #."""
  m = re.fullmatch(r"\{\{\s*(.+?)\s*\}\}", value)
  if not m:
    return None
  return re.sub(r"\s*\|\s*strip$", "", m.group(1))


def extract_template_variables(xml_text: str) -> dict[str, str]:
  """Extract the raw Themer expression for each option path in the template."""
  root = ET.fromstring(xml_text.replace("{{", "[[").replace("}}", "]]"))
  variables: dict[str, str] = {}

  def expr(value: str) -> str | None:
    return tag_expression(value.replace("[[", "{{").replace("]]", "}}"))

  colors_elem = root.find("colors")
  if colors_elem is not None:
    for opt in colors_elem.findall("option"):
      e = expr(opt.get("value", ""))
      if e:
        variables[f"colors/{opt.get('name', '')}"] = e

  attrs_elem = root.find("attributes")
  if attrs_elem is not None:
    for opt in attrs_elem.findall("option"):
      attr_name = opt.get("name", "")
      base_attr = opt.get("baseAttributes")
      if base_attr is not None:
        variables[f"attributes/{attr_name}/@baseAttributes"] = base_attr
        continue
      value_elem = opt.find("value")
      if value_elem is None:
        continue
      for sub_opt in value_elem.findall("option"):
        e = expr(sub_opt.get("value", ""))
        if e:
          variables[f"attributes/{attr_name}/{sub_opt.get('name', '')}"] = e

  return variables


def load_candidates() -> dict[str, str]:
  """Every Themer expression with a color: all tokens (`themer tokens`) plus the derived colors of the UI theme
  template, evaluated from the rendered theme JSON. Values are bare hex."""
  candidates: dict[str, str] = {}
  tokens = subprocess.run(["themer", "tokens"], capture_output=True, text=True, check=True).stdout
  for line in tokens.splitlines():
    parts = line.split()
    if len(parts) == 2 and parts[1].startswith("#"):
      candidates[parts[0]] = parts[1].lstrip("#")
  if THEME_TEMPLATE.exists() and THEME_JSON.exists():
    rendered = json.loads(THEME_JSON.read_text())["colors"]
    for name, raw in json.loads(re.sub(r"\{\{ dark-bool \}\}", "true", THEME_TEMPLATE.read_text()))["colors"].items():
      e = tag_expression(raw)
      if e and e not in candidates and name in rendered:
        candidates[e] = rendered[name].lstrip("#")
  return candidates


def extract_color_options(xml_text: str) -> dict[str, str]:
  """Extract all option name→value pairs from an ICLS file."""
  root = ET.fromstring(xml_text)
  options: dict[str, str] = {}

  colors_elem = root.find("colors")
  if colors_elem is not None:
    for opt in colors_elem.findall("option"):
      name = opt.get("name", "")
      value = opt.get("value", "")
      options[f"colors/{name}"] = value

  attrs_elem = root.find("attributes")
  if attrs_elem is not None:
    for opt in attrs_elem.findall("option"):
      attr_name = opt.get("name", "")
      base_attr = opt.get("baseAttributes")
      if base_attr is not None:
        options[f"attributes/{attr_name}/@baseAttributes"] = base_attr
        continue
      value_elem = opt.find("value")
      if value_elem is None:
        continue
      for sub_opt in value_elem.findall("option"):
        sub_name = sub_opt.get("name", "")
        sub_value = sub_opt.get("value", "")
        options[f"attributes/{attr_name}/{sub_name}"] = sub_value

  return options


def looks_like_hex_color(value: str) -> bool:
  """Check if a value looks like a hex color (3-8 hex chars)."""
  return bool(re.fullmatch(r'[0-9a-fA-F]{3,8}', value))


def normalize_hex(value: str) -> str:
  """Normalize a hex color to 6 digits uppercase for comparison.

  Handles the case where JetBrains IDE strips leading zeros (e.g. 0bde96 → bde96).
  """
  if looks_like_hex_color(value):
    return value.upper().zfill(6)
  return value.upper()


def variable_sort_key(name: str) -> tuple[int, str]:
  """Sort expressions: semantic tokens first, then hue steps, then ANSI colors."""
  for i, prefix in enumerate(SEMANTIC_PREFIXES):
    if name.startswith(prefix):
      return (0, f"{i:03d}_{name}")
  if name.startswith("ansi-"):
    return (2, name)
  return (1, name)


def find_variables_for_value(palette: dict[str, str], hex_value: str) -> list[str]:
  """Find expressions matching a hex value, sorted by semantic relevance."""
  normalized = normalize_hex(hex_value)
  matches = [k for k, v in palette.items() if normalize_hex(v) == normalized]
  return sorted(matches, key=variable_sort_key)


def format_candidates(variables: list[str]) -> str:
  """Format candidate expressions for display."""
  if not variables:
    return f"{DIM}(no matching Themer token){RESET}"
  # Bold the first (best) candidate
  parts = [f"{BOLD}{variables[0]}{RESET}"]
  if len(variables) > 1:
    parts.append(f"{DIM}{', '.join(variables[1:])}{RESET}")
  return ", ".join(parts)


def newest_applied() -> Path | None:
  files = list((Path.home() / ".config/JetBrains").glob("*/colors/Themer.icls"))
  return max(files, key=lambda f: f.stat().st_mtime) if files else None


def main():
  if len(sys.argv) < 2:
    print(__doc__, file=sys.stderr)
    sys.exit(1)

  edited_path = Path(sys.argv[1])
  applied_path = Path(sys.argv[2]) if len(sys.argv) > 2 else newest_applied()

  for path, label in [(edited_path, "edited file"), (applied_path, "applied scheme (run themer apply)"),
                      (TEMPLATE, "template")]:
    if path is None or not path.exists():
      print(f"Error: {label} not found: {path}", file=sys.stderr)
      sys.exit(1)

  palette = load_candidates()
  template_vars = extract_template_variables(TEMPLATE.read_text())

  resolved_options = extract_color_options(applied_path.read_text())
  edited_options = extract_color_options(edited_path.read_text())

  all_keys = sorted(set(resolved_options.keys()) | set(edited_options.keys()))

  changed = []
  only_in_template = []
  only_in_edited = []

  for key in all_keys:
    in_resolved = key in resolved_options
    in_edited = key in edited_options

    if in_resolved and not in_edited:
      only_in_template.append((key, resolved_options[key]))
    elif in_edited and not in_resolved:
      only_in_edited.append((key, edited_options[key]))
    else:
      rv = resolved_options[key]
      ev = edited_options[key]
      if normalize_hex(rv) != normalize_hex(ev):
        changed.append((key, rv, ev))

  # === Output ===

  if changed:
    print(f"\n{BOLD}VALUE CHANGES ({len(changed)}) — update these in the template:{RESET}")
    print(f"{'─' * 100}")

    colors_changes = [(k, r, e) for k, r, e in changed if k.startswith("colors/")]
    attr_changes = [(k, r, e) for k, r, e in changed if k.startswith("attributes/")]

    for section_name, section_changes in [("colors", colors_changes), ("attributes", attr_changes)]:
      if not section_changes:
        continue
      print(f"\n  {BOLD}{CYAN}[{section_name}]{RESET}")
      for key, resolved_val, edited_val in section_changes:
        display_key = key.split("/", 1)[1]
        template_var = template_vars.get(key)
        candidates = find_variables_for_value(palette, edited_val)

        print(f"\n    {YELLOW}{display_key}{RESET}")
        if template_var:
          print(f"      template:   {{{{ {template_var} }}}} → {resolved_val}")
        else:
          print(f"      template:   {resolved_val} (literal)")
        print(f"      edited:     {normalize_hex(edited_val)}")
        print(f"      candidates: {format_candidates(candidates)}")

  if only_in_template:
    print(f"\n{BOLD}REMOVE FROM TEMPLATE ({len(only_in_template)}):{RESET}")
    print(f"{'─' * 100}")
    for key, val in only_in_template:
      template_var = template_vars.get(key)
      var_info = f" ({{{{ {template_var} }}}})" if template_var else ""
      print(f"  {RED}✕ {key}{RESET} = {val}{var_info}")

  if only_in_edited:
    print(f"\n{BOLD}ADD TO TEMPLATE ({len(only_in_edited)}):{RESET}")
    print(f"{'─' * 100}")
    for key, val in only_in_edited:
      candidates = find_variables_for_value(palette, val) if looks_like_hex_color(val) else []
      candidate_str = f" → candidates: {format_candidates(candidates)}" if candidates else ""
      print(f"  {GREEN}+ {key}{RESET} = {normalize_hex(val)}{candidate_str}")

  if not changed and not only_in_template and not only_in_edited:
    print("No differences found.")
  else:
    total = len(changed) + len(only_in_template) + len(only_in_edited)
    print(f"\n{BOLD}Summary:{RESET} {len(changed)} changed, "
          f"{len(only_in_template)} to remove, "
          f"{len(only_in_edited)} to add "
          f"({total} total)")


if __name__ == "__main__":
  main()
