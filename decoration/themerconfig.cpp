#include "themerconfig.h"

#include <KConfigGroup>
#include <KSharedConfig>

#include <QVariant>

namespace Themer
{

namespace
{

Config g_config;
bool g_loaded = false;

QColor color(const KConfigGroup &group, const char *key, const QColor &fallback, qreal alpha = 1.0)
{
  QColor c = group.readEntry(key, fallback);
  const qreal a = group.readEntry(QString::fromLatin1(key) + QStringLiteral("Alpha"), alpha);
  if (a < 1.0) {
    c.setAlphaF(a);
  }
  return c;
}

bool isDark(const QColor &c)
{
  return c.lightnessF() < 0.5;
}

Config read()
{
  KSharedConfig::Ptr file = KSharedConfig::openConfig(QStringLiteral("themerdecorationrc"), KConfig::SimpleConfig);
  file->reparseConfiguration();
  const KConfigGroup colors(file, QStringLiteral("Colors"));
  const KConfigGroup metrics(file, QStringLiteral("Metrics"));

  Config c;
  c.titleBar = color(colors, "TitleBar", QColor(0x05, 0x09, 0x0e));
  c.titleBarInactive = color(colors, "TitleBarInactive", c.titleBar);
  c.title = color(colors, "Title", QColor(0x90, 0x9d, 0xaa));
  c.titleInactive = color(colors, "TitleInactive", QColor(0x78, 0x88, 0x98));
  c.glyph = color(colors, "Glyph", c.title);
  c.glyphInactive = color(colors, "GlyphInactive", c.titleInactive);
  c.glyphHover = color(colors, "GlyphHover", QColor(0xd1, 0xde, 0xeb));
  c.buttonHover = color(colors, "ButtonHover", QColor(0x28, 0x33, 0x3e));
  c.buttonPressed = color(colors, "ButtonPressed", QColor(0x1e, 0x29, 0x33));
  c.closeHover = color(colors, "CloseHover", QColor(0xf4, 0x59, 0x59));
  c.closePressed = color(colors, "ClosePressed", QColor(0xff, 0x7e, 0x79));
  c.closeGlyphHover = color(colors, "CloseGlyphHover", c.titleBar);
  c.checked = color(colors, "Checked", QColor(0x0f, 0x28, 0x3d));
  c.outline = color(colors, "Outline", QColor(0x22, 0x2b, 0x35));
  c.outlineInactive = color(colors, "OutlineInactive", c.outline);

  // Shadow alpha differs between dark and light themes; the title bar's lightness picks the pair.
  const bool dark = isDark(c.titleBar);
  c.shadow = colors.readEntry("Shadow", dark ? QColor(Qt::black) : QColor(0x0b, 0x16, 0x20));
  c.shadow.setAlphaF(colors.readEntry(dark ? "ShadowAlphaDark" : "ShadowAlphaLight", dark ? 0.8 : 0.2));
  c.shadowInactive = c.shadow;
  c.shadowInactive.setAlphaF(c.shadow.alphaF() * colors.readEntry("ShadowInactiveFactor", 0.6));

  c.titleHeight = metrics.readEntry("TitleHeight", 34.0);
  c.titleFontSize = metrics.readEntry("TitleFontSize", 12.0);
  c.titleFontWeight = metrics.readEntry("TitleFontWeight", 0);
  c.paddingLeft = metrics.readEntry("PaddingLeft", 12.0);
  c.paddingRight = metrics.readEntry("PaddingRight", 8.0);
  c.buttonSize = metrics.readEntry("ButtonSize", 22.0);
  c.buttonSpacing = metrics.readEntry("ButtonSpacing", 6.0);
  c.glyphSize = metrics.readEntry("GlyphSize", 8.0);
  c.glyphStroke = metrics.readEntry("GlyphStroke", 1.25);
  c.iconSize = metrics.readEntry("IconSize", 16.0);
  c.hoverDuration = metrics.readEntry("HoverDuration", 120);
  c.cornerRadius = metrics.readEntry("CornerRadius", 14.0);
  c.outlineWidth = metrics.readEntry("OutlineWidth", 1.0);
  c.resizeBorder = metrics.readEntry("ResizeBorder", 6.0);
  c.shadowBlur = metrics.readEntry("ShadowBlur", 64.0);
  c.shadowOffset = metrics.readEntry("ShadowOffset", 24.0);
  return c;
}

bool same(const Config &a, const Config &b)
{
  return a.titleBar == b.titleBar && a.titleBarInactive == b.titleBarInactive && a.title == b.title
    && a.titleInactive == b.titleInactive && a.glyph == b.glyph && a.glyphInactive == b.glyphInactive
    && a.glyphHover == b.glyphHover && a.buttonHover == b.buttonHover && a.buttonPressed == b.buttonPressed
    && a.closeHover == b.closeHover && a.closePressed == b.closePressed && a.closeGlyphHover == b.closeGlyphHover
    && a.checked == b.checked && a.outline == b.outline && a.outlineInactive == b.outlineInactive
    && a.shadow == b.shadow && a.shadowInactive == b.shadowInactive && a.titleHeight == b.titleHeight
    && a.titleFontSize == b.titleFontSize && a.titleFontWeight == b.titleFontWeight
    && a.paddingLeft == b.paddingLeft && a.paddingRight == b.paddingRight && a.buttonSize == b.buttonSize
    && a.buttonSpacing == b.buttonSpacing && a.glyphSize == b.glyphSize && a.glyphStroke == b.glyphStroke
    && a.iconSize == b.iconSize && a.hoverDuration == b.hoverDuration && a.cornerRadius == b.cornerRadius
    && a.outlineWidth == b.outlineWidth && a.resizeBorder == b.resizeBorder && a.shadowBlur == b.shadowBlur
    && a.shadowOffset == b.shadowOffset;
}

} // namespace

const Config &Config::get()
{
  if (!g_loaded) {
    g_config = read();
    g_loaded = true;
  }
  return g_config;
}

bool Config::reload()
{
  const Config next = read();
  const bool changed = !g_loaded || !same(next, g_config);
  g_config = next;
  g_loaded = true;
  return changed;
}

} // namespace Themer
