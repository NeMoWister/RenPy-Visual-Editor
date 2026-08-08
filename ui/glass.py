"""
Настоящий (не имитационный) blur для "стеклянных" панелей.

QSS сам по себе не умеет backdrop-blur, поэтому здесь используется
QGraphicsBlurEffect - родной блюр-движок Qt (тот же, что стоит за
QGraphicsBlurEffect в графических сценах) - чтобы по-настоящему
разложить в размытый растр пиксели того, что должно "просвечивать"
сквозь стекло, а не просто подделать эффект полупрозрачностью.

AmbientGlassFrame берёт снимок (grab) виджета-источника - например,
живого предпросмотра сцены - размывает его через QGraphicsBlurEffect
и рисует как собственный фон, поверх которого дальше как обычно
рисуются дочерние виджеты рамки. Получается эффект "ambient glow":
матовое стекло вокруг картинки светится/окрашивается её же
размытыми цветами, как в Spotify/Apple Music вокруг обложки.

Ограничение: это статический снимок, а не покадровый живой блюр
"насквозь окна" (Qt не даёт дешёвого системного backdrop-blur для
произвольных виджетов). Поэтому вызывающий код должен явно звать
refresh_glass() всякий раз, когда контент источника меняется
(новый шаг сцены, зум и т.п.) - см. использование в main_window.py.
"""

from PyQt6.QtWidgets import QFrame, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
from PyQt6.QtGui import QPainter, QPixmap, QColor, QPainterPath, QPen
from PyQt6.QtCore import Qt, QRectF


def blur_pixmap(source: QPixmap, radius: float = 32.0) -> QPixmap:
    """Реальный блюр через QGraphicsBlurEffect (движок Qt, не питон-цикл по пикселям)."""
    if source.isNull():
        return source
    scene = QGraphicsScene()
    item = QGraphicsPixmapItem(source)
    effect = QGraphicsBlurEffect()
    effect.setBlurRadius(radius)
    effect.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)
    item.setGraphicsEffect(effect)
    scene.addItem(item)
    result = QPixmap(source.size())
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    scene.render(painter, QRectF(result.rect()), QRectF(source.rect()))
    painter.end()
    return result


class AmbientGlassFrame(QFrame):
    """QFrame с настоящим блюр-фоном, взятым со снимка виджета-источника."""

    def __init__(self, source_widget=None, parent=None,
                 blur_radius: float = 40.0,
                 tint: QColor = QColor(18, 18, 24, 150),
                 border_radius: int = 14,
                 upscale: float = 1.15):
        super().__init__(parent)
        self._source = source_widget
        self._blur_radius = blur_radius
        self._tint = tint
        self._border_radius = border_radius
        self._upscale = upscale
        self._cached: QPixmap | None = None
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_source(self, widget):
        self._source = widget
        self.refresh_glass()

    def refresh_glass(self):
        """Пересчитать размытую подложку из текущего состояния источника.
        Вызывать явно после того, как контент источника изменился.""" 
        src = self._source
        if src is None or src.width() <= 0 or src.height() <= 0:
            self._cached = None
            self.update()
            return
        raw = src.grab()
        if raw.isNull():
            self._cached = None
            self.update()
            return
                                                                                
                                                            
        big = raw.scaled(
            int(raw.width() * self._upscale), int(raw.height() * self._upscale),
            Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self._cached = blur_pixmap(big, self._blur_radius)
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_glass()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, self._border_radius, self._border_radius)
        painter.setClipPath(path)

        if self._cached is not None and not self._cached.isNull():
            painter.drawPixmap(self.rect(), self._cached, self._cached.rect())
        else:
            painter.fillRect(rect, QColor(20, 20, 26))

        painter.fillRect(rect, self._tint)
        painter.setClipping(False)
        painter.setPen(QPen(QColor(255, 255, 255, 35), 1))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), self._border_radius, self._border_radius)
        painter.end()
                                                                             
                                                                         
