"""
GlassPanel - a QFrame that renders a real, live-blurred "backdrop" behind
itself (true glassmorphism), instead of faking translucency with a flat
rgba() fill in QSS.

How it works:
    1. Periodically (and on resize/show), it hides itself for a single,
       synchronous render() call of its parent - so no frame is ever
       actually displayed without it - captures the pixels that would be
       behind it, then shows itself again.
    2. That captured pixmap is blurred off-screen using QGraphicsBlurEffect
       rendered through a QGraphicsScene.
    3. paintEvent() clips to a rounded-rect path and draws: blurred
       backdrop -> translucent tint -> soft border. Child widgets are then
       painted normally by Qt on top, unaffected by the blur.

This is a genuine (if lightweight/periodic rather than per-frame) backdrop
blur, not an approximation. It's intentionally used sparingly (a couple of
standout panels) rather than everywhere, since re-rendering a parent
widget tree has a real CPU cost.
"""

from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPixmap
from PyQt6.QtWidgets import QFrame, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
from ui.theme import theme_manager


class GlassPanel(QFrame):
    def __init__(self, parent=None, blur_radius=32, tint=QColor(255, 255, 255, 20),
                 border_color=QColor(255, 255, 255, 45), border_radius=14, refresh_ms=300):
        super().__init__(parent)
        self._blur_radius = blur_radius
        self._tint = tint
        self._border_color = border_color
        self._radius = border_radius
        self._bg_pixmap: QPixmap | None = None
        self._capturing = False
        self._capture_pending = False

        self._timer = QTimer(self)
        self._timer.setInterval(refresh_ms)
        self._timer.timeout.connect(self._request_capture)

                                                                      
    def showEvent(self, event):
        super().showEvent(event)
        self._timer.start()
        self._request_capture()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._request_capture()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._request_capture()

    def _request_capture(self):                   
        if self._capture_pending:
            return
        self._capture_pending = True
        QTimer.singleShot(0, self._capture_backdrop)

                                                                       
    def _capture_backdrop(self):
        self._capture_pending = False
        if self._capturing:
            return
        parent = self.parentWidget()
        if parent is None or not self.isVisible() or self.width() <= 0 or self.height() <= 0:
            return

        self._capturing = True
        try:
            geo = self.geometry()                            
            pixmap = QPixmap(parent.size())
            pixmap.fill(Qt.GlobalColor.transparent)              
            was_visible = self.isVisible()
            self.hide()
            parent.render(pixmap)
            if was_visible:
                self.show()

            cropped = pixmap.copy(geo)
            self._bg_pixmap = self._blur(cropped)
            self.update()
        finally:
            self._capturing = False

    def _blur(self, src: QPixmap) -> QPixmap:
        if src.isNull() or src.width() == 0 or src.height() == 0:
            return src
        scene = QGraphicsScene()
        item = QGraphicsPixmapItem(src)
        effect = QGraphicsBlurEffect()
        effect.setBlurRadius(self._blur_radius)
        effect.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)
        item.setGraphicsEffect(effect)
        scene.addItem(item)

        result = QPixmap(src.size())
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scene.render(painter, QRectF(result.rect()), QRectF(src.rect()))
        painter.end()
        return result

                                                                        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self._radius, self._radius)
        painter.setClipPath(path)

        if self._bg_pixmap is not None and not self._bg_pixmap.isNull():
            painter.drawPixmap(0, 0, self._bg_pixmap)
        else:
            fallback = QColor(theme_manager.tokens().bg_window)
            fallback.setAlpha(200)
            painter.fillPath(path, fallback)

        painter.fillPath(path, self._tint)

        painter.setClipping(False)
        pen = painter.pen()
        pen.setColor(self._border_color)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
