#include "themershadow.h"

#include <QImage>
#include <QPainter>

#include <algorithm>
#include <cmath>
#include <vector>

namespace Themer
{

namespace
{

// Box sizes for three box blurs that together approximate a gaussian of the given sigma.
std::array<int, 3> boxesForGauss(qreal sigma)
{
  const qreal ideal = std::sqrt(12.0 * sigma * sigma / 3 + 1);
  int lower = int(std::floor(ideal));
  if (lower % 2 == 0) {
    lower--;
  }
  const int upper = lower + 2;
  const qreal m = std::round((12 * sigma * sigma - 3 * lower * lower - 12 * lower - 9) / (-4 * lower - 4));
  std::array<int, 3> sizes;
  for (int i = 0; i < 3; ++i) {
    sizes[i] = i < m ? lower : upper;
  }
  return sizes;
}

// One box blur pass of the given radius along rows (step 1) or columns (step = stride).
void boxBlur(const std::vector<float> &src, std::vector<float> &dst, int width, int height, int radius, bool rows)
{
  const int lines = rows ? height : width;
  const int length = rows ? width : height;
  const int step = rows ? 1 : width;
  const float scale = 1.0f / (2 * radius + 1);
  for (int line = 0; line < lines; ++line) {
    const int base = rows ? line * width : line;
    float sum = 0;
    for (int i = -radius - 1; i < radius; ++i) {
      const int j = std::clamp(i, 0, length - 1);
      sum += src[base + j * step];
    }
    for (int i = 0; i < length; ++i) {
      sum += src[base + std::min(i + radius, length - 1) * step];
      sum -= src[base + std::max(i - radius - 1, 0) * step];
      dst[base + i * step] = sum * scale;
    }
  }
}

} // namespace

std::shared_ptr<KDecoration3::DecorationShadow> createShadow(qreal radius, qreal blur, qreal offset,
                                                           const QColor &color)
{
  if (blur <= 0 || color.alpha() == 0) {
    return nullptr;
  }

  // The window stand-in: just big enough that the blurred corners do not meet.
  const int box = int(std::ceil(2 * radius + 2 * blur)) + 1;
  // A gaussian of sigma = blur / 2 has faded out after 3 sigma.
  const int pad = int(std::ceil(blur * 1.5));
  const int padTop = std::max(0, pad - int(offset));
  const int padBottom = pad + int(offset);
  const int width = box + 2 * pad;
  const int height = box + padTop + padBottom;
  const QRectF window(pad, padTop, box, box);

  // Shadow shape, blurred with sigma = blur / 2 like a CSS box-shadow.
  QImage mask(width, height, QImage::Format_Alpha8);
  mask.fill(0);
  {
    QPainter p(&mask);
    p.setRenderHint(QPainter::Antialiasing);
    p.setPen(Qt::NoPen);
    p.setBrush(Qt::black);
    p.drawRoundedRect(window.translated(0, offset), radius, radius);
  }
  std::vector<float> a(size_t(width) * height), b(a.size());
  for (int y = 0; y < height; ++y) {
    const uchar *line = mask.constScanLine(y);
    for (int x = 0; x < width; ++x) {
      a[size_t(y) * width + x] = line[x];
    }
  }
  for (int size : boxesForGauss(blur / 2)) {
    const int r = (size - 1) / 2;
    boxBlur(a, b, width, height, r, true);
    boxBlur(b, a, width, height, r, false);
  }

  QImage image(width, height, QImage::Format_ARGB32_Premultiplied);
  for (int y = 0; y < height; ++y) {
    auto *line = reinterpret_cast<QRgb *>(image.scanLine(y));
    for (int x = 0; x < width; ++x) {
      const qreal alpha = std::clamp(a[size_t(y) * width + x] / 255.0, 0.0, 1.0) * color.alphaF();
      line[x] = qPremultiply(qRgba(color.red(), color.green(), color.blue(), int(std::round(alpha * 255))));
    }
  }

  // Nothing under the window itself.
  {
    QPainter p(&image);
    p.setRenderHint(QPainter::Antialiasing);
    p.setPen(Qt::NoPen);
    p.setBrush(Qt::black);
    p.setCompositionMode(QPainter::CompositionMode_DestinationOut);
    p.drawRoundedRect(window.adjusted(1, 1, -1, -1), radius, radius);
  }

  auto shadow = std::make_shared<KDecoration3::DecorationShadow>();
  shadow->setPadding(QMarginsF(pad, padTop, pad, padBottom));
  shadow->setInnerShadowRect(QRectF(image.rect().center(), QSizeF(1, 1)));
  shadow->setShadow(image);
  return shadow;
}

} // namespace Themer
