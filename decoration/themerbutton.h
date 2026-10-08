#pragma once

#include <KDecoration3/DecorationButton>

#include <QVariant>

class QVariantAnimation;

namespace Themer
{

class Decoration;

// A round title bar button: the glyph rests in the title color, hover fades in a ground behind it.
class Button : public KDecoration3::DecorationButton
{
  Q_OBJECT

public:
  Button(KDecoration3::DecorationButtonType type, Decoration *decoration, QObject *parent = nullptr);
  // Used by the decoration KCM to preview single buttons.
  Button(QObject *parent, const QVariantList &args);

  static KDecoration3::DecorationButton *create(KDecoration3::DecorationButtonType type,
                                                KDecoration3::Decoration *decoration, QObject *parent);

  void paint(QPainter *painter, const QRectF &repaintArea) override;
  void reconfigure();

private:
  void drawGlyph(QPainter *painter, const QPointF &center, const QColor &color) const;

  QVariantAnimation *m_hover;
  qreal m_hoverProgress = 0;
};

} // namespace Themer
