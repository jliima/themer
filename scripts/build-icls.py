#!/usr/bin/env python3
"""Process pywal_color_scheme.icls template with colors from colors.json.

Substitutes {varName} placeholders with bare hex values (no #) from the
palette (see palette.py). ICLS format requires hex without the # prefix.

Usage:
    python3 scripts/build-icls.py [colors.json] [template.icls] [output.icls]

Defaults:
    colors.json   = ~/.cache/themer/jetbrains.json, else ~/.cache/wal/colors.json
    template      = <project>/pywal_color_scheme.icls
    output        = stdout
"""
import re
import sys
from pathlib import Path

from palette import default_colors_path, load_palette

PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_TEMPLATE = PROJECT_DIR / "pywal_color_scheme.icls"


def process_icls(colors_path: Path, template_path: Path) -> str:
    palette = load_palette(colors_path, strip_hash=True)
    template = template_path.read_text()

    def replace(match: re.Match) -> str:
        var_name = match.group(1)
        value = palette.get(var_name)
        if value is None:
            print(f"Warning: unmapped variable '{{{var_name}}}'", file=sys.stderr)
            return match.group(0)
        return value

    return re.sub(r'\{(\w+)\}', replace, template)


def main():
    colors_path   = Path(sys.argv[1]) if len(sys.argv) > 1 else default_colors_path()
    template_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_TEMPLATE
    output_path   = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    if not colors_path.exists():
        print(f"Error: {colors_path} not found", file=sys.stderr)
        sys.exit(1)
    if not template_path.exists():
        print(f"Error: {template_path} not found", file=sys.stderr)
        sys.exit(1)

    result = process_icls(colors_path, template_path)

    if output_path:
        output_path.write_text(result)
        print(f"Written to {output_path}")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
