#!/usr/bin/env python3
"""Diff color values between the auto-generated and hand-edited ICLS files.

Builds the resolved ICLS from the template + colors.json, then compares
every color value against an edited ICLS file to show what was changed.

Usage:
    python3 scripts/diff-color-changes.py <edited.icls> [colors.json]

Arguments:
    edited.icls  Path to the hand-edited or IDE-exported ICLS file
    colors.json  Palette (default: ~/.cache/themer/jetbrains.json, else ~/.cache/wal/colors.json)

Examples:
    # Diff against a hand-edited file in the project
    python3 scripts/diff-color-changes.py pywal_color_scheme_käsin_paranneltu.icls

    # Diff against the currently installed scheme in IntelliJ
    python3 scripts/diff-color-changes.py \\
        ~/.config/JetBrains/IntelliJIdea2026.1/colors/pywal-color-scheme.icls
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from palette import default_colors_path, load_palette

PROJECT_DIR = Path(__file__).parent.parent
TEMPLATE = PROJECT_DIR / "pywal_color_scheme.icls"

# Semantic variables are preferred over raw color names when suggesting
# replacements. Higher priority = listed first.
SEMANTIC_PREFIXES = [
  "syntax", "background", "foreground", "surface", "overlay", "accent",
  "highlight", "border", "text", "success", "warning", "error", "info",
]

# ANSI colors for terminal output
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def resolve_template(template_text: str, palette: dict[str, str]) -> str:
  """Substitute {varName} placeholders with bare hex values."""
  def replace(match: re.Match) -> str:
    var_name = match.group(1)
    value = palette.get(var_name)
    if value is None:
      print(f"Warning: unmapped variable '{{{var_name}}}'", file=sys.stderr)
      return match.group(0)
    return value

  return re.sub(r'\{(\w+)\}', replace, template_text)


def extract_template_variables(xml_text: str) -> dict[str, str]:
  """Extract the raw {varName} placeholder for each option path in the template."""
  root = ET.fromstring(xml_text)
  variables: dict[str, str] = {}

  colors_elem = root.find("colors")
  if colors_elem is not None:
    for opt in colors_elem.findall("option"):
      name = opt.get("name", "")
      value = opt.get("value", "")
      m = re.fullmatch(r'\{(\w+)\}', value)
      if m:
        variables[f"colors/{name}"] = m.group(1)

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
        sub_name = sub_opt.get("name", "")
        sub_value = sub_opt.get("value", "")
        m = re.fullmatch(r'\{(\w+)\}', sub_value)
        if m:
          variables[f"attributes/{attr_name}/{sub_name}"] = m.group(1)

  return variables


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
  """Sort variables: semantic names first, then raw color names."""
  for i, prefix in enumerate(SEMANTIC_PREFIXES):
    if name.startswith(prefix):
      return (0, f"{i:03d}_{name}")
  if re.fullmatch(r'(red|green|blue|yellow|cyan|magenta|black|white|grey)\d', name):
    return (1, name)
  if re.fullmatch(r'color\d+', name):
    return (2, name)
  return (1, name)


def find_variables_for_value(palette: dict[str, str], hex_value: str) -> list[str]:
  """Find palette variables matching a hex value, sorted by semantic relevance."""
  normalized = normalize_hex(hex_value)
  matches = [k for k, v in palette.items() if normalize_hex(v) == normalized]
  return sorted(matches, key=variable_sort_key)


def format_candidates(variables: list[str]) -> str:
  """Format candidate variables for display."""
  if not variables:
    return f"{DIM}(no matching palette variable){RESET}"
  # Bold the first (best) candidate
  parts = [f"{BOLD}{variables[0]}{RESET}"]
  if len(variables) > 1:
    parts.append(f"{DIM}{', '.join(variables[1:])}{RESET}")
  return ", ".join(parts)


def main():
  if len(sys.argv) < 2:
    print("Usage: python3 scripts/diff-color-changes.py <edited.icls> [colors.json]",
          file=sys.stderr)
    print("\nCompares the resolved template against an edited ICLS file.", file=sys.stderr)
    print("See script header for examples.", file=sys.stderr)
    sys.exit(1)

  edited_path = Path(sys.argv[1])
  colors_path = Path(sys.argv[2]) if len(sys.argv) > 2 else default_colors_path()

  for path, label in [(edited_path, "edited file"), (colors_path, "colors.json"),
                       (TEMPLATE, "template")]:
    if not path.exists():
      print(f"Error: {label} not found: {path}", file=sys.stderr)
      sys.exit(1)

  palette = load_palette(colors_path, strip_hash=True)
  template_text = TEMPLATE.read_text()

  # Extract raw template variables before resolving
  template_vars = extract_template_variables(template_text)

  # Build resolved version and parse both
  resolved_text = resolve_template(template_text, palette)
  resolved_options = extract_color_options(resolved_text)
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
          print(f"      template:   {{{template_var}}} → {resolved_val}")
        else:
          print(f"      template:   {resolved_val} (literal)")
        print(f"      edited:     {normalize_hex(edited_val)}")
        print(f"      candidates: {format_candidates(candidates)}")

  if only_in_template:
    print(f"\n{BOLD}REMOVE FROM TEMPLATE ({len(only_in_template)}):{RESET}")
    print(f"{'─' * 100}")
    for key, val in only_in_template:
      template_var = template_vars.get(key)
      var_info = f" ({{{template_var}}})" if template_var else ""
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
