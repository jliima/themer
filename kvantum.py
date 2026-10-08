"""Kvantum theme SVG for Themer: every widget part Kvantum draws, built from theme tokens.

Kvantum draws a widget from SVG objects named after its kvconfig elements: an interior (E-STATE) and eight frame
pieces (E-STATE-top, -topleft, ...) that it stretches like a nine-patch, plus indicators (arrows, check marks).
Missing objects fall back to Kvantum's own default theme, so this file defines every element the kvconfig template
(templates/kvantum/Themer.kvconfig) names. Shapes are flat: a fill, an optional border and rounded corners whose
radius is the frame width (minus an optional transparent margin).
"""

STATES = ("normal", "focused", "pressed", "toggled", "disabled")
SIDES = ("top", "bottom", "left", "right")
CORNERS = ("topleft", "topright", "bottomleft", "bottomright")


def _f(v):
  return f"{v:g}" if isinstance(v, (int, float)) else v


class Svg:
  def __init__(self):
    self.parts = []
    self.x = 0       # next free column, so objects do not overlap when the file is opened in Inkscape
    self.y = 0
    self.row_h = 0

  def place(self, w, h):
    if self.x + w > 2000:
      self.x, self.y, self.row_h = 0, self.y + self.row_h + 4, 0
    x, y = self.x, self.y
    self.x += w + 4
    self.row_h = max(self.row_h, h)
    return x, y

  def group(self, oid, x, y, w, h, body):
    # The transparent rect pins the object's bounds to its box, whatever is drawn inside.
    self.parts.append(f'<g id="{oid}"><rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" '
                      f'fill="#000000" fill-opacity="0"/>{body}</g>')

  def text(self):
    w = 2000
    h = self.y + self.row_h + 4
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
            + "\n".join(self.parts) + "\n</svg>\n")


def _fill(color, d, rule=None):
  if not color or color == "none":
    return ""
  r = f' fill-rule="{rule}"' if rule else ""
  return f'<path d="{d}" fill="{color}"{r}/>'


def _rect(x, y, w, h):
  return f"M{_f(x)},{_f(y)}h{_f(w)}v{_f(h)}h{_f(-w)}Z"


def _corner_shape(corner, x, y, f, m, r, my=None):
  """Path of the part of a rounded rectangle inside one f x f corner box at (x, y). The rectangle's edges sit m (and
  my vertically, default m) in from the box's outer sides and its corner radius is r."""
  ax = m
  ay = m if my is None else my
  if r <= 0:
    w, h = f - ax, f - ay
    if corner == "topleft":
      return _rect(x + ax, y + ay, w, h)
    if corner == "topright":
      return _rect(x, y + ay, w, h)
    if corner == "bottomleft":
      return _rect(x + ax, y, w, h)
    return _rect(x, y, w, h)
  if corner == "topleft":
    return (f"M{_f(x + ax)},{_f(y + f)}V{_f(y + ay + r)}A{_f(r)},{_f(r)} 0 0 1 {_f(x + ax + r)},{_f(y + ay)}"
            f"H{_f(x + f)}V{_f(y + f)}Z")
  if corner == "topright":
    return (f"M{_f(x)},{_f(y + ay)}H{_f(x + f - ax - r)}A{_f(r)},{_f(r)} 0 0 1 {_f(x + f - ax)},{_f(y + ay + r)}"
            f"V{_f(y + f)}H{_f(x)}Z")
  if corner == "bottomright":
    return (f"M{_f(x)},{_f(y)}H{_f(x + f - ax)}V{_f(y + f - ay - r)}A{_f(r)},{_f(r)} 0 0 1 {_f(x + f - ax - r)},"
            f"{_f(y + f - ay)}H{_f(x)}Z")
  return (f"M{_f(x + ax)},{_f(y)}H{_f(x + f)}V{_f(y + f - ay)}H{_f(x + ax + r)}A{_f(r)},{_f(r)} 0 0 1 {_f(x + ax)},"
          f"{_f(y + f - ay - r)}Z")


def _inset_corner(corner, x, y, f, m, r, bw, my=None):
  """The same corner shape shrunk by a border of width bw on its outer sides."""
  return _corner_shape(corner, x, y, f, m + bw, max(r - bw, 0), (m if my is None else my) + bw)


def frame_element(svg, name, f, styles, margin=0, radius=None, border=1, interior=True, states=STATES,
                  sides=True, margin_y=None):
  """Interior and frame objects of one element for each state in styles: {state: (fill, border color)}. A margin
  leaves a transparent strip on the outer sides (margin_y: top and bottom, default margin)."""
  my = margin if margin_y is None else margin_y
  r = f - max(margin, my) if radius is None else radius
  for state in states:
    if state not in styles:
      continue
    fill, line = styles[state]
    base = f"{name}-{state}"
    if interior:
      x, y = svg.place(f, f)
      svg.group(base, x, y, f, f, _fill(fill, _rect(x, y, f, f)))
    if not sides:
      continue
    for corner in CORNERS:
      x, y = svg.place(f, f)
      outer = _corner_shape(corner, x, y, f, margin, r, my)
      if line and line != "none" and border > 0:
        inner = _inset_corner(corner, x, y, f, margin, r, border, my)
        body = _fill(fill, inner) + _fill(line, outer + inner, "evenodd")
      else:
        body = _fill(fill, outer)
      svg.group(f"{base}-{corner}", x, y, f, f, body)
    for side in SIDES:
      x, y = svg.place(f, f)
      lw = border if line and line != "none" else 0
      m = margin
      if side == "top":
        body = _fill(line, _rect(x, y + my, f, lw)) + _fill(fill, _rect(x, y + my + lw, f, f - my - lw))
      elif side == "bottom":
        body = _fill(fill, _rect(x, y, f, f - my - lw)) + _fill(line, _rect(x, y + f - my - lw, f, lw))
      elif side == "left":
        body = _fill(line, _rect(x + m, y, lw, f)) + _fill(fill, _rect(x + m + lw, y, f - m - lw, f))
      else:
        body = _fill(fill, _rect(x, y, f - m - lw, f)) + _fill(line, _rect(x + f - m - lw, y, lw, f))
      svg.group(f"{base}-{side}", x, y, f, f, body)


def line_frames(svg, name, f, color, sides=("bottom",), states=("normal",), width=1, interior=None):
  """Frame objects that are only straight lines on some sides (tab bars, headers, underlines)."""
  for state in states:
    c = color[state] if isinstance(color, dict) else color
    base = f"{name}-{state}"
    x, y = svg.place(f, f)
    svg.group(base, x, y, f, f, _fill(interior, _rect(x, y, f, f)) if interior else "")
    for part in CORNERS + SIDES:
      x, y = svg.place(f, f)
      body = ""
      if c and c != "none":
        if "top" in part and "top" in sides:
          body += _fill(c, _rect(x, y, f, width))
        if "bottom" in part and "bottom" in sides:
          body += _fill(c, _rect(x, y + f - width, f, width))
        if part.endswith("left") and "left" in sides:
          body += _fill(c, _rect(x, y, width, f))
        if part.endswith("right") and "right" in sides:
          body += _fill(c, _rect(x + f - width, y, width, f))
      if interior and interior != "none":
        body = _fill(interior, _rect(x, y, f, f)) + body
      svg.group(f"{base}-{part}", x, y, f, f, body)


def empty(svg, *names, size=4):
  """Invisible objects, to switch off parts of Kvantum's default theme."""
  for n in names:
    x, y = svg.place(size, size)
    svg.group(n, x, y, size, size, "")


def _stroke(color, d, width):
  return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{_f(width)}" stroke-linecap="round" '
          f'stroke-linejoin="round"/>')


def glyph(svg, oid, size, color, kind, stroke=1.5):
  """Arrows and small marks in a size x size box."""
  x, y = svg.place(size, size)
  s = size
  c = (x + s / 2, y + s / 2)
  h = s * 0.25  # half height of a chevron
  w = s * 0.4   # half width of a chevron
  if kind == "down":
    d = f"M{_f(c[0] - w)},{_f(c[1] - h)}L{_f(c[0])},{_f(c[1] + h)}L{_f(c[0] + w)},{_f(c[1] - h)}"
  elif kind == "up":
    d = f"M{_f(c[0] - w)},{_f(c[1] + h)}L{_f(c[0])},{_f(c[1] - h)}L{_f(c[0] + w)},{_f(c[1] + h)}"
  elif kind == "left":
    d = f"M{_f(c[0] + h)},{_f(c[1] - w)}L{_f(c[0] - h)},{_f(c[1])}L{_f(c[0] + h)},{_f(c[1] + w)}"
  elif kind == "right":
    d = f"M{_f(c[0] - h)},{_f(c[1] - w)}L{_f(c[0] + h)},{_f(c[1])}L{_f(c[0] - h)},{_f(c[1] + w)}"
  elif kind == "plus":
    d = f"M{_f(c[0] - w)},{_f(c[1])}H{_f(c[0] + w)}M{_f(c[0])},{_f(c[1] - w)}V{_f(c[1] + w)}"
  elif kind == "minus":
    d = f"M{_f(c[0] - w)},{_f(c[1])}H{_f(c[0] + w)}"
  elif kind == "close":
    k = s * 0.3
    d = (f"M{_f(c[0] - k)},{_f(c[1] - k)}L{_f(c[0] + k)},{_f(c[1] + k)}"
         f"M{_f(c[0] + k)},{_f(c[1] - k)}L{_f(c[0] - k)},{_f(c[1] + k)}")
  else:
    raise ValueError(kind)
  svg.group(oid, x, y, s, s, _stroke(color, d, stroke) if color and color != "none" else "")


def check(svg, oid, size, ground, border, mark=None, kind="check", radius=4, bw=1):
  """A check box (kind check / tristate / none) or, with radius = size / 2, a radio button (kind dot)."""
  x, y = svg.place(size, size)
  s = size
  body = ""
  if border and border != "none":
    body += _rounded(x, y, s, s, radius, border)
    body += _rounded(x + bw, y + bw, s - 2 * bw, s - 2 * bw, max(radius - bw, 0), ground)
  else:
    body += _rounded(x, y, s, s, radius, ground)
  if mark:
    if kind == "check":
      d = (f"M{_f(x + s * 0.27)},{_f(y + s * 0.52)}L{_f(x + s * 0.43)},{_f(y + s * 0.68)}"
           f"L{_f(x + s * 0.74)},{_f(y + s * 0.34)}")
      body += _stroke(mark, d, max(1.5, s / 9))
    elif kind == "tristate":
      body += _stroke(mark, f"M{_f(x + s * 0.3)},{_f(y + s / 2)}H{_f(x + s * 0.7)}", max(1.5, s / 9))
    elif kind == "dot":
      body += f'<circle cx="{_f(x + s / 2)}" cy="{_f(y + s / 2)}" r="{_f(s * 0.2)}" fill="{mark}"/>'
  svg.group(oid, x, y, s, s, body)


def _rounded(x, y, w, h, r, color):
  if not color or color == "none":
    return ""
  return (f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="{_f(r)}" ry="{_f(r)}" '
          f'fill="{color}"/>')


def build(t, n):
  """The SVG for token colors t ({name: '#rrggbb'}) and numbers n (radii, sizes) as a string."""
  svg = Svg()
  rs, rm, rx = n["radius-sm"], n["radius-md"], n["radius-xs"]
  hover, active = t["surface-hover"], t["surface-active"]

  # Push buttons: secondary look with a line edge; the default button is tinted in the accent.
  frame_element(svg, "button", rs, {
    "normal": (hover, t["line"]),
    "focused": (active, t["line"]),
    "pressed": (t["surface-raised"], t["line-strong"]),
    "toggled": (t["accent-soft"], t["accent"]),
    "disabled": (t["surface"], t["line"]),
  })
  # Kvantum has no text color of its own for the default button, so it stays readable as a tinted accent button.
  frame_element(svg, "button-default", rs, {"normal": (t["accent-soft"], t["accent"])}, states=("normal",))
  # Kvantum names the default button objects without a state.
  svg.parts[-9:] = [p.replace('id="button-default-normal', 'id="button-default') for p in svg.parts[-9:]]
  empty(svg, "button-default-indicator")

  # Tool buttons and flat items: ghost until hovered.
  frame_element(svg, "tbutton", rs, {
    "normal": (None, None),
    "focused": (hover, None),
    "pressed": (active, None),
    "toggled": (t["accent-soft"], None),
    "disabled": (None, None),
  })

  # Line edits, spin boxes and editable combo boxes: sunken ground, a border you can see, the accent when focused.
  frame_element(svg, "lineedit", rs, {
    "normal": (t["bg-sunken"], t["line-strong"]),
    "focused": (t["bg-sunken"], t["focus-ring"]),
    "pressed": (t["bg-sunken"], t["focus-ring"]),
    "toggled": (t["bg-sunken"], t["focus-ring"]),
    "disabled": (t["bg-sunken"], t["line"]),
  })

  # Generic frames, group boxes, tab frames: hairline only.
  frame_element(svg, "common", rs, {"normal": (None, t["line"]), "disabled": (None, t["line"])},
                states=("normal", "disabled"))
  frame_element(svg, "group", rm, {"normal": (t["surface"], t["line"])}, states=("normal",))
  frame_element(svg, "tabframe", rs, {"normal": (None, t["line"])}, states=("normal",))

  # Tabs: no box, a 2px accent line under the active one.
  line_frames(svg, "tab", 3, {"normal": "none", "focused": t["line-strong"], "pressed": t["line-strong"],
                              "toggled": t["accent"], "disabled": "none"},
              sides=("bottom",), states=STATES, width=2)
  empty(svg, "tab-separator-normal")
  # The line under the whole tab bar.
  line_frames(svg, "tabbarframe", 2, t["line"], sides=("bottom",), width=1)

  # Item views: hover, pressed and selected rows, rounded.
  frame_element(svg, "itemview", rs, {
    "normal": (None, None),
    "focused": (hover, None),
    "pressed": (t["kde-selection"], None),
    "toggled": (t["kde-selection"], None),
    "disabled": (None, None),
  })
  for state in ("focused", "pressed", "toggled"):
    x, y = svg.place(rs, rs)
    svg.group(f"expand-itemview-{state}", x, y, rs, rs, _fill("#000000", _rect(x, y, rs, rs)))

  # Menus: raised ground with a hairline ring; items inset from the edge, highlighted in accent-soft.
  menu_f = rm
  frame_element(svg, "menu", menu_f, {"normal": (t["surface-raised"], t["line"])}, states=("normal",))
  item_margin = n["menu-padding"]
  frame_element(svg, "menuitem", item_margin + rs, {
    "normal": (None, None),
    "focused": (t["accent-soft"], None),
    "pressed": (t["accent-soft"], None),
    "toggled": (t["accent-soft"], None),
    "disabled": (None, None),
  }, margin=item_margin, margin_y=0, radius=rs)
  sep = n["menu-separator"]
  x, y = svg.place(20, sep)
  svg.group("menuitem-separator", x, y, 20, sep, _fill(t["line"], _rect(x, y + (sep - 1) / 2, 20, 1)))
  empty(svg, "menuitem-tearoff-normal", "menuitem-tearoff-focused")
  frame_element(svg, "menubaritem", rs, {
    "normal": (None, None),
    "focused": (hover, None),
    "pressed": (active, None),
    "toggled": (active, None),
  }, states=("normal", "focused", "pressed", "toggled"))
  frame_element(svg, "menubar", 2, {"normal": (None, None)}, states=("normal",))

  # Tool tips.
  frame_element(svg, "tooltip", rs, {"normal": (t["surface-raised"], t["line"])}, states=("normal",))

  # Toolbars and dock titles are flat on the window ground.
  frame_element(svg, "toolbar", 2, {"normal": (None, None), "disabled": (None, None)}, states=("normal", "disabled"))
  empty(svg, "toolbar-handle", "toolbar-separator", "sizegrip-normal", "sizegrip-focused", "grip-normal",
        "grip-focused", "grip-pressed", "splitter-grip-normal", "splitter-grip-focused", "splitter-grip-pressed")
  frame_element(svg, "dock", 2, {"normal": (t["bg-deep"], None)}, states=("normal",))
  frame_element(svg, "splitter", 1, {"normal": (None, None), "focused": (t["line-strong"], None),
                                     "pressed": (t["accent"], None)}, states=("normal", "focused", "pressed"))

  # Headers of item views: the view ground, a hairline under it and between sections.
  line_frames(svg, "header", 2, {s: t["line"] for s in STATES}, sides=("bottom",), states=STATES, width=1,
              interior=None)
  x, y = svg.place(1, 20)
  svg.group("header-separator", x, y, 1, 20, _fill(t["line"], _rect(x, y + 4, 1, 12)))

  # Scroll bars: a thin pill on no groove.
  sw = n["scroll-width"] / 2
  frame_element(svg, "scrollbarslider", sw, {
    "normal": (t["surface-active"], None),
    "focused": (t["line-strong"], None),
    "pressed": (t["text-faint"], None),
    "disabled": (None, None),
  }, states=("normal", "focused", "pressed", "disabled"))
  frame_element(svg, "scrollgroove", 2, {"normal": (None, None), "disabled": (None, None)},
                states=("normal", "disabled"))
  empty(svg, "scrollgroove-topglow", "scrollgroove-bottomglow", "scrollgroove-topglow-normal",
        "scrollgroove-bottomglow-normal")

  # Sliders: a thin groove, filled in the accent up to a round handle.
  gr = n["slider-width"] / 2
  frame_element(svg, "slider", gr, {
    "normal": (t["surface-active"], None),
    "focused": (t["surface-active"], None),
    "toggled": (t["accent"], None),
    "disabled": (t["surface-hover"], None),
  }, states=("normal", "focused", "toggled", "disabled"))
  x, y = svg.place(5, 1)
  svg.group("slider-tick", x, y, 5, 1, _fill(t["line-strong"], _rect(x, y, 5, 1)))
  hs = n["slider-handle"]
  for state, (ground, ring) in {"normal": (t["text"], t["bg"]), "focused": (t["text-bright"], t["bg"]),
                                "pressed": (t["accent"], t["bg"]), "disabled": (t["text-disabled"], t["bg"])}.items():
    check(svg, f"slidercursor-{state}", hs, ground, ring, radius=hs / 2, bw=2, kind="none")

  # Progress bars: a pill groove and an accent fill.
  pr = n["progress-thickness"] / 2
  frame_element(svg, "progress", pr, {"normal": (t["surface-active"], None), "disabled": (t["surface-hover"], None)},
                states=("normal", "disabled"))
  frame_element(svg, "progress-pattern", pr, {"normal": (t["accent"], None), "toggled": (t["accent"], None),
                                              "focused": (t["accent-hover"], None),
                                              "disabled": (t["text-disabled"], None)},
                states=("normal", "toggled", "focused", "disabled"))

  # Check boxes and radio buttons.
  cs = n["check-size"]
  for state, edge in {"normal": t["line-strong"], "focused": t["text-subtle"], "pressed": t["accent"],
                      "disabled": t["line"]}.items():
    check(svg, f"checkbox-{state}", cs, t["bg-sunken"], edge, radius=rx)
    check(svg, f"radio-{state}", cs, t["bg-sunken"], edge, radius=cs / 2, kind="none")
  for state, fill in {"normal": t["accent"], "focused": t["accent-hover"], "pressed": t["accent"],
                      "disabled": t["text-disabled"]}.items():
    check(svg, f"checkbox-checked-{state}", cs, fill, None, t["on-accent"], radius=rx)
    check(svg, f"checkbox-tristate-{state}", cs, fill, None, t["on-accent"], kind="tristate", radius=rx)
    check(svg, f"radio-checked-{state}", cs, fill, None, t["on-accent"], kind="dot", radius=cs / 2)

  # Arrows and marks: rest in text-subtle, text when hovered or pressed.
  colors = {"normal": t["text-subtle"], "focused": t["text"], "pressed": t["text"], "toggled": t["text"],
            "disabled": t["text-disabled"]}
  ar = n["arrow-size"]
  for state, c in colors.items():
    for d in ("up", "down", "left", "right"):
      glyph(svg, f"arrow-{d}-{state}", ar, c, d)
      glyph(svg, f"menuitem-{d}-{state}", ar, c, d)
    glyph(svg, f"arrow-plus-{state}", ar, c, "plus")
    glyph(svg, f"arrow-minus-{state}", ar, c, "minus")
    glyph(svg, f"arrow-down-{state}", ar, c, "down")
    glyph(svg, f"tab-close-{state}", ar, c if state != "focused" else t["danger"], "close")
  glyph(svg, "tab-close-toggled", ar, t["text-subtle"], "close")
  # Tree branches: chevrons.
  for state, c in colors.items():
    glyph(svg, f"tree-plus-{state}", ar, c, "right")
    glyph(svg, f"tree-minus-{state}", ar, c, "down")

  # Focus: a ring in the focus color around the focused widget.
  frame_element(svg, "focus", 2, {"normal": (None, t["focus-ring"])}, states=("normal",), radius=2, border=2,
                interior=False)
  # Kvantum's focus frame has no state in its object names.
  svg.parts[-8:] = [p.replace('id="focus-normal-', 'id="focus-') for p in svg.parts[-8:]]

  # MDI title bars (rare): flat.
  frame_element(svg, "titlebar", 2, {"normal": (t["bg-deep"], None), "focused": (t["bg-deep"], None)},
                states=("normal", "focused"))
  for state, c in colors.items():
    for k, kind in (("close", "close"), ("maximize", "up"), ("restore", "up"), ("minimize", "down"),
                    ("shade", "up")):
      glyph(svg, f"mdi-{k}-{state}", ar, c, kind)
  glyph(svg, "mdi-menu-normal", ar, t["text-subtle"], "down")
  return svg.text()
