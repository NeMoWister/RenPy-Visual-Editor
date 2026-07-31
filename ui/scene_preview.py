                       
import os
from typing import Optional, List
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QTextDocument
from ui.pixmap_cache import get_scaled
from core.models import ANCHOR_POSITIONS, NAMED_SPRITE_POSITIONS, nearest_anchor_name
from core.renpy_text_tags import parse_renpy_text, runs_to_html

PREVIEW_W = 640
PREVIEW_H = 360
CLICK_DRAG_THRESHOLD = 4                                                                

                                                                           
                                                                          
                                                                  
                                                      
ANCHOR_XALIGNS = [NAMED_SPRITE_POSITIONS[name].xalign for name, _ in ANCHOR_POSITIONS]


def _snap_to_anchor(xalign: float) -> float:
    return min(ANCHOR_XALIGNS, key=lambda a: abs(a - xalign))


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
    zoom_step_requested = pyqtSignal(int)                                                 

    def __init__(self):
        super().__init__()
        self.bg_pixmap: Optional[QPixmap] = None
        self.sprites: List[SpriteLayer] = []
        self.char_name: str = ""
        self.char_color: Optional[str] = None
        self.dialogue_text: str = ""
        self.nvl_mode: bool = False
        self.nvl_history: List[tuple] = []
        self.dragging_sprite_idx: Optional[int] = None
        self.drag_offset = QPoint()
        self.press_pos: Optional[QPoint] = None
        self.did_drag = False
        self.hover_sprite_idx: Optional[int] = None
        self.scale_factor: float = 1.0
        self.setFixedSize(PREVIEW_W, PREVIEW_H)
        self.setMouseTracking(True)

    def set_scale(self, factor: float):
        """Масштабирует превью целиком (от слайдера зума), не меняя логику
        отрисовки и попадания мышью - координаты ниже переведены в логические."""
        self.scale_factor = max(0.4, min(2.0, factor))
        self.setFixedSize(int(PREVIEW_W * self.scale_factor), int(PREVIEW_H * self.scale_factor))
        self.update()

    def _to_logical(self, pos: QPoint) -> QPoint:
        return QPoint(int(pos.x() / self.scale_factor), int(pos.y() / self.scale_factor))

    def set_background(self, path: Optional[str]):
        if path and os.path.isfile(path):
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

    def set_dialogue(self, char_name: str, text: str, char_color: Optional[str] = None):
        self.char_name = char_name
        self.char_color = char_color
        self.dialogue_text = text
        self.update()

    def set_nvl_mode(self, on: bool):
        if self.nvl_mode != on:
            self.nvl_mode = on
            self.update()

    def set_nvl_history(self, history: List[tuple]):
        """history - список (char_name, text, color) уже показанных реплик
        NVL-экрана (без текущей) в хронологическом порядке - как в режиме
        презентации, чтобы предпросмотр вёл себя так же: каждая следующая
        нода дописывается СНИЗУ, а не заменяет предыдущую сверху."""
        if self.nvl_history != history:
            self.nvl_history = history
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
        painter.scale(self.scale_factor, self.scale_factor)

        if self.bg_pixmap:
            painter.drawPixmap(0, 0, self.bg_pixmap)
        else:
            painter.fillRect(0, 0, PREVIEW_W, PREVIEW_H, QColor(20, 20, 30))
            painter.setPen(QColor(60, 60, 80))
            painter.setFont(QFont("Arial", 16))
            painter.drawText(QRect(0, 0, PREVIEW_W, PREVIEW_H), Qt.AlignmentFlag.AlignCenter, "[ Фон не задан ]")

        if self.dragging_sprite_idx is not None:
                                                                    
                                                                         
                                                          
            painter.setFont(QFont("Arial", 8))
            active_layer = self.sprites[self.dragging_sprite_idx]
            for name, _ in ANCHOR_POSITIONS:
                ax = NAMED_SPRITE_POSITIONS[name].xalign
                x = int(ax * PREVIEW_W)
                is_active = abs(ax - active_layer.xalign) < 1e-6
                color = QColor(255, 140, 0, 220) if is_active else QColor(255, 255, 255, 60)
                painter.setPen(QPen(color, 2 if is_active else 1, Qt.PenStyle.DashLine))
                painter.drawLine(x, 0, x, PREVIEW_H)
                painter.setPen(color)
                painter.drawText(x - 15, 12, name)

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
            if self.nvl_mode:
                                                                          
                                                                           
                                                                          
                                                                         
                                                                           
                dbox_h = int(PREVIEW_H * 0.88)
                painter.fillRect(0, 0, PREVIEW_W, dbox_h, QColor(6, 6, 10, 200))
                painter.setPen(QColor("#ffb84d"))
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.drawText(QRect(10, 4, PREVIEW_W - 20, 14), Qt.AlignmentFlag.AlignLeft, "NVL")

                pad_x = 16
                pad_top = 20
                base_size = 12
                html_parts = []
                for hist_name, hist_text, hist_color in self.nvl_history:
                    html_parts.append(self._nvl_line_html(hist_name, hist_text, hist_color, dim=True, base_size=base_size))
                if self.dialogue_text or self.char_name:
                    html_parts.append(self._nvl_line_html(self.char_name, self.dialogue_text, self.char_color, dim=False, base_size=base_size))

                doc = QTextDocument()
                doc.setDefaultFont(QFont("Arial", base_size))
                doc.setTextWidth(PREVIEW_W - 2 * pad_x)
                doc.setHtml("".join(html_parts))
                painter.save()
                painter.translate(pad_x, pad_top)
                doc.drawContents(painter)
                painter.restore()
            else:
                min_dbox_h = 85
                max_dbox_h = int(PREVIEW_H * 0.8)
                needed_h = self._rich_text_height(self.dialogue_text, PREVIEW_W - 40, QFont("Arial", 12))
                dbox_h = min(max_dbox_h, max(min_dbox_h, needed_h + 20))
                dbox_y = PREVIEW_H - dbox_h - 5
                painter.fillRect(0, dbox_y, PREVIEW_W, dbox_h, QColor(0, 0, 0, 180))
                if self.char_name:
                    painter.fillRect(10, dbox_y - 22, 120, 22, QColor(5, 5, 5, 220))
                    name_color = QColor(255, 255, 255)
                    if self.char_color:
                        candidate = QColor(self.char_color)
                        if candidate.isValid():
                            name_color = candidate
                    painter.setPen(name_color)
                    painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                    painter.drawText(QRect(10, dbox_y - 22, 120, 22), Qt.AlignmentFlag.AlignCenter, self.char_name)
                painter.setPen(QColor(220, 220, 220))
                painter.setFont(QFont("Arial", 12))
                                                                              
                                                                          
                                                                        
                             
                self._draw_rich_text(
                    painter, QRect(20, dbox_y + 10, PREVIEW_W - 40, dbox_h - 20),
                    self.dialogue_text, clip=False
                )

        painter.end()

    def _nvl_line_html(self, char_name: str, raw_text: str, color: Optional[str], dim: bool, base_size: int) -> str:
        """Строит HTML одной реплики NVL: имя - тем же кеглем, что и текст,
        слева от реплики (как в режиме презентации), а не отдельной крупной
        строкой сверху."""
        prefix_html = ""
        if char_name:
            c = QColor(color) if color and QColor(color).isValid() else QColor(255, 255, 255)
            prefix_html = f'<b style="color:{c.name()}; font-size:{base_size}px;">{char_name}:</b>&nbsp;'
        runs, _events = parse_renpy_text(raw_text) if raw_text else ([], [])
        body_html = runs_to_html(runs, base_size=base_size) if runs else ""
        text_color = "#8d8d92" if dim else "#e6e6e6"
        return f'<p style="color:{text_color}; margin:0 0 8px 0; line-height:130%;">{prefix_html}{body_html}</p>'

    def _rich_text_height(self, raw_text: str, width: int, font: QFont) -> int:
        """Считает высоту, которую реально займёт реплика при заданной
        ширине блока - используется, чтобы подогнать высоту диалогового
        окна под текст (см. _draw_rich_text)."""
        runs, _events = parse_renpy_text(raw_text)
        html = runs_to_html(runs, base_size=13)
        doc = QTextDocument()
        doc.setDefaultFont(font)
        doc.setTextWidth(max(1, width))
        doc.setHtml(f'<div style="color:#dcdcdc;">{html}</div>')
        return int(doc.size().height())

    def _draw_rich_text(self, painter: QPainter, rect: QRect, raw_text: str, clip: bool = True):
        """Рендерит текст реплики с поддержкой тегов Ren'Py ({i},{b},{u},
        {color=..},{size=..},{alpha=..}) через QTextDocument - теги видны
        визуально в превью, но статично (без покадровой печати - та есть
        только в режиме презентации).

        clip=False (для NVL) - не обрезает документ по высоте rect: там
        площадь под текст лишь прикидка, и если реплика длиннее ожидаемого,
        обрезка по rect.height() рубила текст на середине."""
        runs, _events = parse_renpy_text(raw_text)
        html = runs_to_html(runs, base_size=13)
        doc = QTextDocument()
        doc.setDefaultFont(painter.font())
        doc.setTextWidth(rect.width())
        doc.setHtml(f'<div style="color:#dcdcdc;">{html}</div>')
        painter.save()
        painter.translate(rect.topLeft())
        if clip:
            doc.drawContents(painter, QRectF(0, 0, rect.width(), rect.height()))
        else:
            doc.drawContents(painter)
        painter.restore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self._to_logical(event.position().toPoint())
            idx = self._sprite_at(pos)
            if idx is not None:
                self.dragging_sprite_idx = idx
                self.press_pos = pos
                self.did_drag = False
                self.drag_offset = pos - self._sprite_rect(self.sprites[idx]).center()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        pos = self._to_logical(event.position().toPoint())
        if self.dragging_sprite_idx is not None:
            if self.press_pos is not None and not self.did_drag:
                moved = (pos - self.press_pos).manhattanLength()
                if moved > CLICK_DRAG_THRESHOLD:
                    self.did_drag = True
            if self.did_drag:
                new_x = pos.x() - self.drag_offset.x()
                raw_xalign = max(0.0, min(1.0, new_x / PREVIEW_W))
                xalign = _snap_to_anchor(raw_xalign)
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
        pos = self._to_logical(event.position().toPoint())
        idx = self._sprite_at(pos)
        self.hover_sprite_idx = idx
        self.setCursor(Qt.CursorShape.PointingHandCursor if idx is not None else Qt.CursorShape.ArrowCursor)
        self.update()

    def wheelEvent(self, event):
        """Ctrl+колесо - зум превью прямо здесь, как в Ren'Py (Ctrl+колесо/
        Ctrl+=/Ctrl+- в dev-консоли). Без Ctrl - обычная прокрутка (передаём
        родителю/QScrollArea, если превью не помещается целиком)."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            steps = event.angleDelta().y() // 120
            if steps != 0:
                self.zoom_step_requested.emit(steps)
            event.accept()
        else:
            super().wheelEvent(event)

    def leaveEvent(self, event):
        if self.hover_sprite_idx is not None:
            self.hover_sprite_idx = None
            self.update()
        super().leaveEvent(event)
