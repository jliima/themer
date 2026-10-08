#include "themerdecoration.h"

#include "themerbutton.h"
#include "themerconfig.h"
#include "themershadow.h"

#include <KDecoration3/DecoratedWindow>
#include <KDecoration3/DecorationButtonGroup>
#include <KDecoration3/DecorationSettings>
#include <KDecoration3/ScaleHelpers>
#include <KPluginFactory>

#include <QPainter>
#include <QPainterPath>
#include <QTimer>

K_PLUGIN_FACTORY_WITH_JSON(ThemerDecorationFactory, "themer.json",
                           registerPlugin<Themer::Decoration>(); registerPlugin<Themer::Button>();)

namespace Themer
{

using KDecoration3::DecoratedWindow;
using KDecoration3::DecorationButtonGroup;

namespace
{

// Shadows are the same for every window with the same settings, so share them.
struct ShadowCache {
  qreal radius = -1;
  qreal blur = -1;
  qreal offset = -1;
  QColor active;
  QColor inactive;
  std::shared_ptr<KDecoration3::DecorationShadow> activeShadow;
  std::shared_ptr<KDecoration3::DecorationShadow> inactiveShadow;
};
ShadowCache g_shadows;

} // namespace

Decoration::Decoration(QObject *parent, const QVariantList &args)
  : KDecoration3::Decoration(parent, args)
{
}

bool Decoration::init()
{
  auto s = settings();
  auto w = window();

  connect(s.get(), &KDecoration3::DecorationSettings::reconfigured, this, &Decoration::reconfigure);
  connect(s.get(), &KDecoration3::DecorationSettings::fontChanged, this, [this]() { update(); });
  connect(s.get(), &KDecoration3::DecorationSettings::decorationButtonsLeftChanged, this,
          [this]() { QTimer::singleShot(0, this, &Decoration::updateButtons); });
  connect(s.get(), &KDecoration3::DecorationSettings::decorationButtonsRightChanged, this,
          [this]() { QTimer::singleShot(0, this, &Decoration::updateButtons); });

  connect(w, &DecoratedWindow::activeChanged, this, [this]() {
    updateBorders();
    updateShadow();
    update();
  });
  connect(w, &DecoratedWindow::captionChanged, this, [this]() { update(titleBar()); });
  connect(w, &DecoratedWindow::maximizedChanged, this, [this](bool maximized) {
    setOpaque(maximized);
    updateBorders();
    updateButtons();
  });
  for (auto signal : {&DecoratedWindow::maximizedHorizontallyChanged, &DecoratedWindow::maximizedVerticallyChanged,
                      &DecoratedWindow::shadedChanged}) {
    connect(w, signal, this, &Decoration::updateBorders);
  }
  connect(w, &DecoratedWindow::adjacentScreenEdgesChanged, this, &Decoration::updateBorders);
  connect(w, &DecoratedWindow::widthChanged, this, &Decoration::updateButtons);
  connect(w, &DecoratedWindow::nextScaleChanged, this, &Decoration::updateBorders);

  m_left = new DecorationButtonGroup(DecorationButtonGroup::Position::Left, this, &Button::create);
  m_right = new DecorationButtonGroup(DecorationButtonGroup::Position::Right, this, &Button::create);

  setOpaque(isMaximized());
  updateBorders();
  updateButtons();
  updateShadow();
  return true;
}

void Decoration::reconfigure()
{
  Config::reload();
  for (auto group : {m_left, m_right}) {
    for (auto button : group->buttons()) {
      static_cast<Button *>(button)->reconfigure();
    }
  }
  updateBorders();
  updateButtons();
  updateShadow();
  update();
}

bool Decoration::isMaximized() const
{
  return window()->isMaximized();
}

qreal Decoration::cornerRadius() const
{
  return isMaximized() ? 0 : KDecoration3::snapToPixelGrid(Config::get().cornerRadius, window()->nextScale());
}

void Decoration::updateBorders()
{
  const auto &c = Config::get();
  const qreal scale = window()->nextScale();
  const qreal top = KDecoration3::snapToPixelGrid(c.titleHeight, scale);
  setBorders(QMarginsF(0, top, 0, 0));
  setTitleBar(QRectF(0, 0, window()->width(), top));

  const auto w = window();
  const qreal ext = KDecoration3::snapToPixelGrid(c.resizeBorder, scale);
  setResizeOnlyBorders(QMarginsF(w->isMaximizedHorizontally() ? 0 : ext, 0, w->isMaximizedHorizontally() ? 0 : ext,
                                 w->isMaximizedVertically() ? 0 : ext));

  // KWin clips the window content's bottom corners to this radius; the decoration paints its rounded top itself.
  const Qt::Edges edges = w->adjacentScreenEdges();
  const qreal r = cornerRadius();
  const qreal bottomLeft = edges & (Qt::BottomEdge | Qt::LeftEdge) ? 0 : r;
  const qreal bottomRight = edges & (Qt::BottomEdge | Qt::RightEdge) ? 0 : r;
  setBorderRadius(KDecoration3::BorderRadius(0, 0, bottomRight, bottomLeft));

  if (isMaximized() || c.outlineWidth <= 0) {
    setBorderOutline(KDecoration3::BorderOutline());
  } else {
    const qreal thickness =
      std::max(KDecoration3::pixelSize(scale), KDecoration3::snapToPixelGrid(c.outlineWidth, scale));
    setBorderOutline(KDecoration3::BorderOutline(thickness, w->isActive() ? c.outline : c.outlineInactive,
                                                 KDecoration3::BorderRadius(r, r, bottomRight, bottomLeft)));
  }
}

void Decoration::updateButtons()
{
  if (!m_left || !m_right) {
    return;
  }
  const auto &c = Config::get();
  const qreal height = borderTop();
  for (auto group : {m_left, m_right}) {
    group->setSpacing(c.buttonSpacing);
    for (auto button : group->buttons()) {
      // The whole title bar height is clickable; the round ground is drawn centered in it.
      button->setGeometry(QRectF(0, 0, c.buttonSize, height));
    }
  }
  m_left->setPos(QPointF(c.paddingLeft, 0));
  m_right->setPos(QPointF(size().width() - c.paddingRight - m_right->geometry().width(), 0));
  update();
}

void Decoration::updateShadow()
{
  const auto &c = Config::get();
  const qreal radius = c.cornerRadius;
  if (g_shadows.radius != radius || g_shadows.blur != c.shadowBlur || g_shadows.offset != c.shadowOffset
      || g_shadows.active != c.shadow || g_shadows.inactive != c.shadowInactive) {
    g_shadows.radius = radius;
    g_shadows.blur = c.shadowBlur;
    g_shadows.offset = c.shadowOffset;
    g_shadows.active = c.shadow;
    g_shadows.inactive = c.shadowInactive;
    g_shadows.activeShadow = createShadow(radius, c.shadowBlur, c.shadowOffset, c.shadow);
    g_shadows.inactiveShadow = createShadow(radius, c.shadowBlur, c.shadowOffset, c.shadowInactive);
  }
  setShadow(window()->isActive() ? g_shadows.activeShadow : g_shadows.inactiveShadow);
}

QRectF Decoration::captionRect(const QFont &font) const
{
  const auto &c = Config::get();
  const QRectF bar = titleBar();
  const qreal gap = c.buttonSpacing + 4;
  const qreal left = m_left->buttons().isEmpty() ? c.paddingLeft : m_left->geometry().right() + gap;
  const qreal right = m_right->buttons().isEmpty() ? bar.right() - c.paddingRight : m_right->geometry().left() - gap;
  const QRectF available(left, bar.top(), std::max(0.0, right - left), bar.height());

  // Centered on the whole window when it fits, otherwise in the space between the buttons.
  const qreal textWidth = QFontMetricsF(font).horizontalAdvance(window()->caption());
  QRectF centered(bar.center().x() - textWidth / 2, bar.top(), textWidth, bar.height());
  if (centered.left() >= available.left() && centered.right() <= available.right()) {
    return centered;
  }
  return available;
}

void Decoration::paint(QPainter *painter, const QRectF &repaintArea)
{
  const auto &c = Config::get();
  const auto w = window();
  const bool active = w->isActive();
  const QRectF bar = titleBar();
  const qreal r = cornerRadius();

  painter->save();
  painter->setRenderHint(QPainter::Antialiasing);
  painter->setPen(Qt::NoPen);
  painter->setBrush(active ? c.titleBar : c.titleBarInactive);
  if (r > 0) {
    // Round only the top corners; the window content continues below.
    QPainterPath path;
    path.addRoundedRect(bar.adjusted(0, 0, 0, r), r, r);
    painter->setClipRect(bar);
    painter->drawPath(path);
    painter->setClipping(false);
  } else {
    painter->drawRect(bar);
  }

  QFont font = settings()->font();
  font.setPixelSize(qRound(c.titleFontSize));
  if (c.titleFontWeight > 0) {
    font.setWeight(QFont::Weight(c.titleFontWeight));
  }
  painter->setFont(font);
  painter->setPen(active ? c.title : c.titleInactive);
  const QRectF caption = captionRect(font);
  const QString text = QFontMetricsF(font).elidedText(w->caption(), Qt::ElideMiddle, caption.width());
  painter->drawText(caption, Qt::AlignCenter | Qt::TextSingleLine, text);
  painter->restore();

  m_left->paint(painter, repaintArea);
  m_right->paint(painter, repaintArea);
}

} // namespace Themer

#include "themerdecoration.moc"
