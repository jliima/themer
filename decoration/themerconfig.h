#pragma once

#include <QColor>

namespace Themer
{

// Everything the decoration draws with, read from ~/.config/themerdecorationrc. Themer writes that file from the
// applied theme's tokens (template kde/themerdecorationrc.ini); the defaults below are Pare dark.
struct Config {
  // Title bar
  QColor titleBar;
  QColor titleBarInactive;
  QColor title;
  QColor titleInactive;
  qreal titleHeight;
  qreal titleFontSize; // px
  int titleFontWeight; // 100..900, 0 keeps the weight of the KDE window title font
  qreal paddingLeft;
  qreal paddingRight;

  // Buttons
  qreal buttonSize;
  qreal buttonSpacing;
  qreal glyphSize;
  qreal glyphStroke;
  qreal iconSize; // window icon of the Menu button
  QColor glyph;
  QColor glyphInactive;
  QColor glyphHover;
  QColor buttonHover;
  QColor buttonPressed;
  QColor closeHover;
  QColor closePressed;
  QColor closeGlyphHover;
  QColor checked; // ground of a checked toggle (keep above, on all desktops)
  int hoverDuration; // ms

  // Window shape
  qreal cornerRadius;
  qreal outlineWidth; // 0 leaves the outline to another effect
  QColor outline;
  QColor outlineInactive;
  qreal resizeBorder; // invisible resize area outside the window

  // Shadow, like CSS box-shadow: 0 <offset> <blur> <color>
  QColor shadow;
  QColor shadowInactive;
  qreal shadowBlur;
  qreal shadowOffset;

  static const Config &get();
  // Re-reads the file; returns true when something changed.
  static bool reload();
};

} // namespace Themer
