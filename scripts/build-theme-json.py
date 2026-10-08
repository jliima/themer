#!/usr/bin/env python3
"""Combine colors.json + ui-mapping.json into a full IntelliJ theme JSON.

The theme's "dark" flag follows the palette's background (see palette.py), so a light Themer variant gives a
light IDE.

Usage:
    python3 scripts/build-theme-json.py [colors.json] [ui-mapping.json] [output.json]

Defaults:
    colors.json   = ~/.cache/themer/jetbrains.json, else ~/.cache/wal/colors.json
    ui-mapping    = <project>/theme/ui-mapping.json
    output        = stdout
"""
import json
import sys
from pathlib import Path

from palette import default_colors_path, load_palette

PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_MAPPING = PROJECT_DIR / "theme/ui-mapping.json"


def build_theme(colors_path: Path, mapping_path: Path) -> dict:
    palette = load_palette(colors_path)
    mapping = json.loads(mapping_path.read_text())

    # Build the colors section from the full palette
    colors_section = {k: v for k, v in palette.items() if v.startswith("#")}

    return {
        "name":         mapping["name"],
        "author":       mapping.get("author", ""),
        "dark":         palette["isDark"] == "true",
        "editorScheme": mapping["editorScheme"],
        "colors":       colors_section,
        "ui":           mapping["ui"],
        "icons":        mapping.get("icons", {}),
    }


def main():
    colors_path  = Path(sys.argv[1]) if len(sys.argv) > 1 else default_colors_path()
    mapping_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_MAPPING
    output_path  = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    if not colors_path.exists():
        print(f"Error: {colors_path} not found", file=sys.stderr)
        sys.exit(1)
    if not mapping_path.exists():
        print(f"Error: {mapping_path} not found", file=sys.stderr)
        sys.exit(1)

    theme = build_theme(colors_path, mapping_path)
    output = json.dumps(theme, indent=2)

    if output_path:
        output_path.write_text(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
