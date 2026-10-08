#pragma once

#include <KDecoration3/DecorationShadow>

#include <QColor>

#include <memory>

namespace Themer
{

// A CSS-like box shadow (0 <offset> <blur> <color>) around a rounded window, as a KWin decoration shadow. The part
// under the window is cut out, so translucent windows do not show it.
std::shared_ptr<KDecoration3::DecorationShadow> createShadow(qreal radius, qreal blur, qreal offset,
                                                           const QColor &color);

} // namespace Themer
