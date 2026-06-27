from pathlib import Path
from typing import Optional, List
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QPen
from ui.pixmap_cache import get_scaled

PREVIEW_W = 640
PREVIEW_H = 360
CLICK_DRAG_THRESHOLD = 4


class SpriteLayer:
    def __init__(self, pixmap: QPixmap, xalign: float, yalign: float, zoom: float = 1.0, tag: str = ""):
        self.pixmap = pixmap
        self.xalign = xalign
        self.yalign = yalign
        self.zoom = zoom
        self.tag = tag


class ScenePreview(QWidget):
    sprite_moved = pyqtSignal(float)
    sprite_delete_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.bg_pixmap: Optional[QPixmap] = None
        self.sprites: List[SpriteLayer] = []
        self.char_name: str = ""
        self.dialogue_text: str = ""
        self.dragging_sprite_idx: Optional[int] = None
        self.drag_offset = QPoint()
        self.press_pos: Optional[QPoint] = None
        self.did_drag = False
        self.hover_sprite_idx: Optional[int] = None
        self.setFixedSize(PREVIEW_W, PREVIEW_H)
        self.setMouseTracking(True)

    def set_background(self, path: Optional[str]):
        if path and Path(path).is_file():
            self.bg_pixmap = get_scaled(
                path, PREVIEW_W, PREVIEW_H,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            )
        else:
            self.bg_pixmap = None
        self.update()

    def set_sprites(self, sprite_layers: List[SpriteLayer]):
        self.sprites = sprite_layers
        self.hover_sprite_idx = None
        self.update()

    def set_dialogue(self, char_name: str, text: str):
        self.char_name = char_name
        self.dialogue_text = text
        self.update()

    def _sprite_rect(self, layer: SpriteLayer) -> QRect:
        pm = layer.pixmap
        w = int(pm.width() * layer.zoom)
        h = int(pm.height() * layer.zoom)
        max_h = int(PREVIEW_H * 0.85)
        if h > max_h:
            scale = max_h / h
            w = int(w * scale)
            h = max_h
        x = int(layer.xalign * PREVIEW_W - w / 2)
        y = PREVIEW_H - h - 10
        return QRect(x, y, w, h)

    def _sprite_at(self, pos: QPoint) -> Optional[int]:
        for i in range(len(self.sprites) - 1, -1, -1):
            if self._sprite_rect(self.sprites[i]).contains(pos):
                return i
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self.bg_pixmap:
            painter.drawPixmap(0, 0, self.bg_pixmap)
        else:
            painter.fillRect(0, 0, PREVIEW_W, PREVIEW_H, QColor(20, 20, 30))
            painter.setPen(QColor(60, 60, 80))
            painter.setFont(QFont("Arial", 16))
            painter.drawText(QRect(0, 0, PREVIEW_W, PREVIEW_H), Qt.AlignmentFlag.AlignCenter, "[ Фон не задан ]")

        for i, layer in enumerate(self.sprites):
            rect = self._sprite_rect(layer)
            scaled = layer.pixmap.scaled(rect.width(), rect.height(),
                                         Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(rect.x(), rect.y(), scaled)
            if self.dragging_sprite_idx == i:
                painter.setPen(QPen(QColor(255, 140, 0), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect)
            elif self.hover_sprite_idx == i:
                painter.setPen(QPen(QColor(255, 60, 60), 2, Qt.PenStyle.DashLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect)
                hint_text = "✕ удалить"
                painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                text_w = painter.fontMetrics().horizontalAdvance(hint_text) + 12
                hint_w = max(rect.width(), text_w)
                hint_x = rect.x() + rect.width() // 2 - hint_w // 2
                hint_y = max(0, rect.y() - 18)
                hint_rect = QRect(hint_x, hint_y, hint_w, 16)
                painter.fillRect(hint_rect, QColor(40, 0, 0, 200))
                painter.setPen(QPen(QColor(255, 60, 60), 1))
                painter.drawRect(hint_rect)
                painter.setPen(QColor(255, 120, 120))
                painter.drawText(hint_rect, Qt.AlignmentFlag.AlignCenter, hint_text)

        if self.dialogue_text or self.char_name:
            dbox_h = 85
            dbox_y = PREVIEW_H - dbox_h - 5
            painter.fillRect(0, dbox_y, PREVIEW_W, dbox_h, QColor(0, 0, 0, 180))
            if self.char_name:
                painter.fillRect(10, dbox_y - 22, 120, 22, QColor(50, 100, 180, 220))
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                painter.drawText(QRect(10, dbox_y - 22, 120, 22), Qt.AlignmentFlag.AlignCenter, self.char_name)
            painter.setPen(QColor(220, 220, 220))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(QRect(20, dbox_y + 10, PREVIEW_W - 40, dbox_h - 20),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                           self.dialogue_text)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            idx = self._sprite_at(pos)
            if idx is not None:
                self.dragging_sprite_idx = idx
                self.press_pos = pos
                self.did_drag = False
                self.drag_offset = pos - self._sprite_rect(self.sprites[idx]).center()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        if self.dragging_sprite_idx is not None:
            if self.press_pos is not None and not self.did_drag:
                moved = (pos - self.press_pos).manhattanLength()
                if moved > CLICK_DRAG_THRESHOLD:
                    self.did_drag = True
            if self.did_drag:
                new_x = pos.x() - self.drag_offset.x()
                xalign = max(0.0, min(1.0, new_x / PREVIEW_W))
                self.sprites[self.dragging_sprite_idx].xalign = xalign
                self.sprite_moved.emit(xalign)
                self.update()
        else:
            idx = self._sprite_at(pos)
            if idx != self.hover_sprite_idx:
                self.hover_sprite_idx = idx
                self.setCursor(Qt.CursorShape.PointingHandCursor if idx is not None else Qt.CursorShape.ArrowCursor)
                self.update()

    def mouseReleaseEvent(self, event):
        if self.dragging_sprite_idx is not None and not self.did_drag:
            tag = self.sprites[self.dragging_sprite_idx].tag
            self.sprite_delete_requested.emit(tag)
        self.dragging_sprite_idx = None
        self.press_pos = None
        self.did_drag = False
        pos = event.position().toPoint()
        idx = self._sprite_at(pos)
        self.hover_sprite_idx = idx
        self.setCursor(Qt.CursorShape.PointingHandCursor if idx is not None else Qt.CursorShape.ArrowCursor)
        self.update()

    def leaveEvent(self, event):
        if self.hover_sprite_idx is not None:
            self.hover_sprite_idx = None
            self.update()
        super().leaveEvent(event)
