"""Palette loading shared by the build scripts.

The palette is a pywal-format colors.json: `special.*` (semantic names, syntax*, ramps) and `colors.color0-15`.
Themer writes one for the applied theme and variant to ~/.cache/themer/jetbrains.json (the "JetBrains IDEs" target
in ~/.config/themer/targets.toml); plain pywal writes ~/.cache/wal/colors.json, used when the Themer file is missing.

Two names are derived and added to every palette:
  parentScheme  Darcula for a dark background, Default for a light one (the ICLS template's parent_scheme)
  isDark        "true" or "false", from the background's luminance (the UI theme's "dark" flag)
"""
import json
from pathlib import Path

THEMER_COLORS = Path.home() / ".cache/themer/jetbrains.json"
WAL_COLORS = Path.home() / ".cache/wal/colors.json"


def default_colors_path() -> Path:
  """Themer's palette if it exists, else pywal's."""
  return THEMER_COLORS if THEMER_COLORS.exists() else WAL_COLORS


def luminance(hex_color: str) -> float:
  """WCAG relative luminance of #rrggbb."""
  def channel(c: int) -> float:
    s = c / 255
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
  h = hex_color.lstrip("#")
  r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def is_dark(palette: dict[str, str]) -> bool:
  return luminance(palette.get("background", "000000")) < 0.5


def load_palette(colors_path: Path, strip_hash: bool = False) -> dict[str, str]:
  """Flatten colors.json into name -> hex, with or without the leading #, plus the derived names."""
  data = json.loads(colors_path.read_text())
  palette: dict[str, str] = {}
  for section in ("special", "colors"):
    for k, v in data.get(section, {}).items():
      palette[k] = v.lstrip("#") if strip_hash else v
  dark = is_dark(palette)
  palette["parentScheme"] = "Darcula" if dark else "Default"
  palette["isDark"] = "true" if dark else "false"
  return palette
