#pragma once

#include <KDecoration3/Decoration>

#include <QVariant>

namespace KDecoration3
{
class DecorationButtonGroup;
}

namespace Themer
{

// KWin window decoration drawn from the applied Themer theme (~/.config/themerdecorationrc).
class Decoration : public KDecoration3::Decoration
{
  Q_OBJECT

public:
  explicit Decoration(QObject *parent = nullptr, const QVariantList &args = {});

  bool init() override;
  void paint(QPainter *painter, const QRectF &repaintArea) override;

private:
  void reconfigure();
  void updateBorders();
  void updateButtons();
  void updateShadow();

  bool isMaximized() const;
  qreal cornerRadius() const;
  QRectF captionRect(const QFont &font) const;

  KDecoration3::DecorationButtonGroup *m_left = nullptr;
  KDecoration3::DecorationButtonGroup *m_right = nullptr;
};

} // namespace Themer
