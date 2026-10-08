#include "themerbutton.h"

#include "themerconfig.h"
#include "themerdecoration.h"

#include <KDecoration3/DecoratedWindow>

#include <QPainter>
#include <QPainterPath>
#include <QVariantAnimation>

namespace Themer
{

using KDecoration3::DecorationButtonType;

namespace
{

QColor mix(const QColor &a, const QColor &b, qreal t)
{
  return QColor::fromRgbF(a.redF() + (b.redF() - a.redF()) * t, a.greenF() + (b.greenF() - a.greenF()) * t,
                          a.blueF() + (b.blueF() - a.blueF()) * t, a.alphaF() + (b.alphaF() - a.alphaF()) * t);
}

QColor withAlpha(QColor c, qreal factor)
{
  c.setAlphaF(c.alphaF() * factor);
  return c;
}

// Keeps a button in sync with whether the window allows its action.
template<typename Signal>
void bindVisible(Button *button, KDecoration3::DecoratedWindow *window, bool visible, Signal changed)
{
  button->setVisible(visible);
  QObject::connect(window, changed, button, &Button::setVisible);
}

template<typename Signal>
void bindChecked(Button *button, KDecoration3::DecoratedWindow *window, bool checked, Signal changed)
{
  button->setCheckable(true);
  button->setChecked(checked);
  QObject::connect(window, changed, button, &Button::setChecked);
}

} // namespace

Button::Button(DecorationButtonType type, Decoration *decoration, QObject *parent)
  : DecorationButton(type, decoration, parent)
  , m_hover(new QVariantAnimation(this))
{
  m_hover->setStartValue(0.0);
  m_hover->setEndValue(1.0);
  m_hover->setEasingCurve(QEasingCurve::OutCubic);
  connect(m_hover, &QVariantAnimation::valueChanged, this, [this](const QVariant &value) {
    m_hoverProgress = value.toReal();
    update();
  });
  connect(this, &DecorationButton::hoveredChanged, this, [this](bool hovered) {
    m_hover->setDirection(hovered ? QAbstractAnimation::Forward : QAbstractAnimation::Backward);
    if (m_hover->duration() <= 0) {
      m_hoverProgress = hovered ? 1 : 0;
      update();
    } else if (m_hover->state() != QAbstractAnimation::Running) {
      m_hover->start();
    }
  });
  connect(decoration->window(), &KDecoration3::DecoratedWindow::iconChanged, this, [this]() { update(); });
  connect(decoration->window(), &KDecoration3::DecoratedWindow::activeChanged, this, [this]() { update(); });
  reconfigure();
}

Button::Button(QObject *parent, const QVariantList &args)
  : Button(args.at(0).value<DecorationButtonType>(), args.at(1).value<Decoration *>(), parent)
{
  const auto &c = Config::get();
  setGeometry(QRectF(0, 0, c.buttonSize, c.titleHeight));
}

KDecoration3::DecorationButton *Button::create(DecorationButtonType type, KDecoration3::Decoration *decoration,
                                               QObject *parent)
{
  auto d = qobject_cast<Decoration *>(decoration);
  if (!d) {
    return nullptr;
  }
  auto b = new Button(type, d, parent);
  auto w = d->window();
  using W = KDecoration3::DecoratedWindow;
  switch (type) {
  case DecorationButtonType::Close:
    bindVisible(b, w, w->isCloseable(), &W::closeableChanged);
    break;
  case DecorationButtonType::Maximize:
    bindVisible(b, w, w->isMaximizeable(), &W::maximizeableChanged);
    bindChecked(b, w, w->isMaximized(), &W::maximizedChanged);
    break;
  case DecorationButtonType::Minimize:
    bindVisible(b, w, w->isMinimizeable(), &W::minimizeableChanged);
    break;
  case DecorationButtonType::ContextHelp:
    bindVisible(b, w, w->providesContextHelp(), &W::providesContextHelpChanged);
    break;
  case DecorationButtonType::Shade:
    bindVisible(b, w, w->isShadeable(), &W::shadeableChanged);
    bindChecked(b, w, w->isShaded(), &W::shadedChanged);
    break;
  case DecorationButtonType::OnAllDesktops:
    bindChecked(b, w, w->isOnAllDesktops(), &W::onAllDesktopsChanged);
    break;
  case DecorationButtonType::KeepAbove:
    bindChecked(b, w, w->isKeepAbove(), &W::keepAboveChanged);
    break;
  case DecorationButtonType::KeepBelow:
    bindChecked(b, w, w->isKeepBelow(), &W::keepBelowChanged);
    break;
  case DecorationButtonType::ExcludeFromCapture:
    bindChecked(b, w, w->isExcludedFromCapture(), &W::excludeFromCaptureChanged);
    break;
  case DecorationButtonType::ApplicationMenu:
    bindVisible(b, w, w->hasApplicationMenu(), &W::hasApplicationMenuChanged);
    break;
  default:
    break;
  }
  return b;
}

void Button::reconfigure()
{
  m_hover->setDuration(Config::get().hoverDuration);
}

void Button::paint(QPainter *painter, const QRectF &repaintArea)
{
  Q_UNUSED(repaintArea)
  if (!isVisible() || type() == DecorationButtonType::Spacer) {
    return;
  }
  const auto &c = Config::get();
  const auto window = decoration()->window();
  const QRectF g = geometry();
  const QPointF center = g.center();

  painter->save();
  painter->setRenderHint(QPainter::Antialiasing);

  if (type() == DecorationButtonType::Menu) {
    const qreal s = c.iconSize;
    const QRectF iconRect(center.x() - s / 2, center.y() - s / 2, s, s);
    window->icon().paint(painter, iconRect.toRect());
    painter->restore();
    return;
  }

  const bool close = type() == DecorationButtonType::Close;
  // Maximize shows its state through the glyph; only real toggles get a checked ground.
  const bool toggled = isChecked() && type() != DecorationButtonType::Maximize;
  const QColor rest = window->isActive() ? c.glyph : c.glyphInactive;

  QColor ground = toggled ? c.checked : QColor(Qt::transparent);
  QColor glyph = rest;
  if (isPressed()) {
    ground = close ? c.closePressed : c.buttonPressed;
    glyph = close ? c.closeGlyphHover : c.glyphHover;
  } else if (m_hoverProgress > 0) {
    const QColor hover = close ? c.closeHover : c.buttonHover;
    ground = toggled ? mix(c.checked, hover, m_hoverProgress) : withAlpha(hover, m_hoverProgress);
    glyph = mix(rest, close ? c.closeGlyphHover : c.glyphHover, m_hoverProgress);
  }

  if (ground.alpha() > 0) {
    const qreal r = c.buttonSize / 2;
    painter->setPen(Qt::NoPen);
    painter->setBrush(ground);
    painter->drawEllipse(center, r, r);
  }
  drawGlyph(painter, center, glyph);
  painter->restore();
}

void Button::drawGlyph(QPainter *painter, const QPointF &center, const QColor &color) const
{
  const auto &c = Config::get();
  const qreal s = c.glyphSize / 2;
  QPen pen(color, c.glyphStroke, Qt::SolidLine, Qt::RoundCap, Qt::RoundJoin);
  painter->setPen(pen);
  painter->setBrush(Qt::NoBrush);
  painter->translate(center);

  auto chevron = [&](qreal dy, bool up) {
    const qreal h = s / 2;
    const qreal y = up ? h : -h;
    painter->drawPolyline(QPolygonF{QPointF(-s, dy + y), QPointF(0, dy - y), QPointF(s, dy + y)});
  };

  switch (type()) {
  case DecorationButtonType::Minimize:
    chevron(0, false);
    break;
  case DecorationButtonType::Maximize:
    if (isChecked()) {
      // Restore: a small diamond, as in Breeze.
      painter->drawPolygon(QPolygonF{QPointF(0, -s), QPointF(s, 0), QPointF(0, s), QPointF(-s, 0)});
    } else {
      chevron(0, true);
    }
    break;
  case DecorationButtonType::Close:
    painter->drawLine(QPointF(-s, -s), QPointF(s, s));
    painter->drawLine(QPointF(s, -s), QPointF(-s, s));
    break;
  case DecorationButtonType::KeepAbove:
    chevron(-s / 2, true);
    chevron(s / 2, true);
    break;
  case DecorationButtonType::KeepBelow:
    chevron(-s / 2, false);
    chevron(s / 2, false);
    break;
  case DecorationButtonType::Shade:
    painter->drawLine(QPointF(-s, -s * 0.75), QPointF(s, -s * 0.75));
    chevron(s * 0.4, !isChecked());
    break;
  case DecorationButtonType::OnAllDesktops:
    painter->setPen(Qt::NoPen);
    painter->setBrush(color);
    painter->drawEllipse(QPointF(0, 0), s * 0.55, s * 0.55);
    break;
  case DecorationButtonType::ContextHelp: {
    QPainterPath q;
    q.moveTo(-s * 0.6, -s * 0.45);
    q.cubicTo(-s * 0.6, -s * 1.1, s * 0.7, -s * 1.1, s * 0.6, -s * 0.4);
    q.cubicTo(s * 0.5, 0, 0, -s * 0.05, 0, s * 0.35);
    painter->drawPath(q);
    painter->setPen(Qt::NoPen);
    painter->setBrush(color);
    painter->drawEllipse(QPointF(0, s * 0.9), c.glyphStroke * 0.7, c.glyphStroke * 0.7);
    break;
  }
  case DecorationButtonType::ApplicationMenu:
    for (qreal y : {-s * 0.7, 0.0, s * 0.7}) {
      painter->drawLine(QPointF(-s, y), QPointF(s, y));
    }
    break;
  case DecorationButtonType::ExcludeFromCapture:
    painter->drawEllipse(QPointF(0, 0), s * 0.8, s * 0.8);
    painter->drawLine(QPointF(-s, s), QPointF(s, -s));
    break;
  default:
    break;
  }
}

} // namespace Themer
