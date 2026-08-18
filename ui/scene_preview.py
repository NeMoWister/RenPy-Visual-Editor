                       
import os
from typing import Optional, List
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, QTimer, QElapsedTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QTextDocument
from ui.pixmap_cache import get_scaled
from core.models import ANCHOR_POSITIONS, NAMED_SPRITE_POSITIONS, nearest_anchor_name
from core.renpy_text_tags import parse_renpy_text, runs_to_html
from core import atl as atl_engine
from core.transitions import TransitionSpec, TransitionKind
from ui.transition_compositor import render_transition_frame, punch_offset

PREVIEW_W = 640
PREVIEW_H = 360
CLICK_DRAG_THRESHOLD = 4
ANCHOR_XALIGNS = [NAMED_SPRITE_POSITIONS[name].xalign for name, _ in ANCHOR_POSITIONS]


def _snap_to_anchor(xalign: float) -> float:
    return min(ANCHOR_XALIGNS, key=lambda a: abs(a - xalign))


class SpriteLayer:
    def __init__(self, pixmap: QPixmap, xalign: float, yalign: float, zoom: float = 1.0, tag: str = "",
                 atl_script: str = "", image_variants: Optional[dict] = None):
        self.pixmap = pixmap
        self.xalign = xalign
        self.yalign = yalign
        self.zoom = zoom
        self.tag = tag
        self.atl_script = atl_script                                                        
        self.image_variants = image_variants or {}                                                                


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
        self.bg_atl_script: str = ""
        self._mask_resolver = None                                                        
        self._active_transition = None                                                    
        self._atl_clock = QElapsedTimer()
        self._atl_clock.start()
        self._atl_timer = QTimer(self)
        self._atl_timer.setInterval(33)
        self._atl_timer.timeout.connect(self._on_atl_tick)
        self._atl_timer.start()
        self.setFixedSize(PREVIEW_W, PREVIEW_H)
        self.setMouseTracking(True)

    def _on_atl_tick(self):
        """Живой предпросмотр ATL/переходов - перерисовывает кадр, только
        если реально что-то анимировано, чтобы не жечь CPU на статичных
        сценах."""
        if self._active_transition is not None:
            self.update()
            return
        if self.bg_atl_script and atl_engine.is_animated(self.bg_atl_script):
            self.update()
            return
        for layer in self.sprites:
            if layer.atl_script and atl_engine.is_animated(layer.atl_script):
                self.update()
                return

    def set_mask_resolver(self, fn):
        """fn(rel_path) -> abs_path|None - разрешает путь маски кастомного
        ImageDissolve-перехода в файл на диске (см. core/transitions.py)."""
        self._mask_resolver = fn

    def snapshot_current(self) -> QPixmap:
        """Снимок текущего кадра (фон+спрайты, БЕЗ редакторских оверлеев) -
        вызывается ПЕРЕД тем, как поменять состояние сцены, чтобы было с чем
        честно проиграть переход (см. start_transition)."""
        return self._render_scene_pixmap()

    def start_transition(self, old_pixmap: Optional[QPixmap], spec: Optional[TransitionSpec]):
        """Запускает честное проигрывание перехода old_pixmap -> текущее
        состояние (уже применённое к этому моменту через set_background/
        set_sprites) по спеке spec. Для PUNCH (тряска экрана) old_pixmap не
        нужен - просто трясётся текущий (уже новый) кадр."""
        if spec is None:
            return
        if spec.kind != TransitionKind.PUNCH and old_pixmap is None:
            return
        new_pixmap = self._render_scene_pixmap() if spec.kind != TransitionKind.PUNCH else None
        clock = QElapsedTimer()
        clock.start()
        self._active_transition = (old_pixmap, new_pixmap, spec, clock)
        self.update()

    def _render_scene_pixmap(self) -> QPixmap:
        """Рендерит ТЕКУЩЕЕ состояние (фон+спрайты, без UI-оверлеев вроде
        рамок выделения) в офф-скрин QPixmap логического размера
        PREVIEW_W x PREVIEW_H - используется для снимков переходов."""
        pm = QPixmap(PREVIEW_W, PREVIEW_H)
        pm.fill(QColor(20, 20, 30))
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self._paint_bg(p)
        self._paint_sprites(p, with_overlays=False)
        p.end()
        return pm

    def _paint_bg(self, painter: QPainter):
        if self.bg_pixmap:
            if self.bg_atl_script and self.bg_atl_script.strip():
                t = self._atl_clock.elapsed() / 1000.0
                vis = atl_engine.resolve_visual(
                    self.bg_atl_script, t, base_xalign=0.5, base_yalign=0.5, base_zoom=1.0,
                )
                dx = (vis["xalign"] - 0.5) * PREVIEW_W
                dy = (vis["yalign"] - 0.5) * PREVIEW_H
                zoom = max(0.2, min(3.0, vis["zoom"]))
                painter.save()
                painter.translate(PREVIEW_W / 2, PREVIEW_H / 2)
                painter.rotate(vis["rotate"])
                painter.scale(zoom, zoom)
                painter.translate(-PREVIEW_W / 2 + dx, -PREVIEW_H / 2 + dy)
                painter.setOpacity(max(0.0, min(1.0, vis["alpha"])))
                painter.drawPixmap(0, 0, self.bg_pixmap)
                painter.restore()
            else:
                painter.drawPixmap(0, 0, self.bg_pixmap)
        else:
            painter.fillRect(0, 0, PREVIEW_W, PREVIEW_H, QColor(20, 20, 30))
            painter.setPen(QColor(60, 60, 80))
            painter.setFont(QFont("Arial", 16))
            painter.drawText(QRect(0, 0, PREVIEW_W, PREVIEW_H), Qt.AlignmentFlag.AlignCenter, "[ Фон не задан ]")

    def _paint_sprites(self, painter: QPainter, with_overlays: bool = True):
        if with_overlays and self.dragging_sprite_idx is not None:
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
            vis = self._resolved_layer_transform(layer)
            draw_pixmap = layer.pixmap
            if vis.get("image_text") and layer.image_variants:
                draw_pixmap = layer.image_variants.get(vis["image_text"], layer.pixmap)
            scaled = draw_pixmap.scaled(rect.width(), rect.height(),
                                         Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation)
            painter.save()
            painter.setOpacity(max(0.0, min(1.0, vis["alpha"])))
            if abs(vis["rotate"]) > 1e-6:
                center = rect.center()
                painter.translate(center)
                painter.rotate(vis["rotate"])
                painter.translate(-center)
            painter.drawPixmap(rect.x(), rect.y(), scaled)
            painter.restore()
            if not with_overlays:
                continue
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

    def set_scale(self, factor: float):
        """Масштабирует превью целиком (от слайдера зума), не меняя логику
        отрисовки и попадания мышью - координаты ниже переведены в логические."""
        self.scale_factor = max(0.4, min(2.0, factor))
        self.setFixedSize(int(PREVIEW_W * self.scale_factor), int(PREVIEW_H * self.scale_factor))
        self.update()

    def _to_logical(self, pos: QPoint) -> QPoint:
        return QPoint(int(pos.x() / self.scale_factor), int(pos.y() / self.scale_factor))

    def set_background(self, path: Optional[str], atl_script: str = ""):
        if path and os.path.isfile(path):
            self.bg_pixmap = get_scaled(
                path, PREVIEW_W, PREVIEW_H,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            )
        else:
            self.bg_pixmap = None
        self.bg_atl_script = atl_script
        self._atl_clock.restart()
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

    def _resolved_layer_transform(self, layer: SpriteLayer) -> dict:
        """Честно проигранное на текущий момент состояние ATL-блока спрайта
        (см. core/atl.py) - xalign/yalign/zoom/alpha/rotate; если у слоя нет
        своего atl_script, просто возвращает его статичные значения."""
        if not layer.atl_script:
            return {"xalign": layer.xalign, "yalign": layer.yalign, "zoom": layer.zoom,
                    "alpha": 1.0, "rotate": 0.0}
        t = self._atl_clock.elapsed() / 1000.0
        return atl_engine.resolve_visual(
            layer.atl_script, t, base_xalign=layer.xalign,
            base_yalign=layer.yalign, base_zoom=layer.zoom,
        )

    def _sprite_rect(self, layer: SpriteLayer) -> QRect:
        pm = layer.pixmap
        vis = self._resolved_layer_transform(layer)
        natural_w, natural_h = pm.width(), pm.height()
        if natural_h <= 0:
            return QRect(0, 0, 0, 0)
        fit_h = int(PREVIEW_H * 0.85)
        base_scale = min(1.0, fit_h / natural_h)
        scale = base_scale * max(vis["zoom"], 0.01)

        w = int(natural_w * scale)
        h = int(natural_h * scale)
        hard_max_h = int(PREVIEW_H * 1.35)
        if h > hard_max_h:
            shrink = hard_max_h / h
            w = int(w * shrink)
            h = hard_max_h

        x = int(vis["xalign"] * PREVIEW_W - w / 2)
        y = int(vis["yalign"] * PREVIEW_H - h) - 10
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

        if self._active_transition is not None:
            old_pm, new_pm, spec, clock = self._active_transition
            t = clock.elapsed() / 1000.0
            if spec.kind == TransitionKind.PUNCH:
                dx, dy = punch_offset(spec, t)
                painter.save()
                painter.translate(dx, dy)
                self._paint_bg(painter)
                self._paint_sprites(painter)
                painter.restore()
            else:
                render_transition_frame(
                    painter, QRect(0, 0, PREVIEW_W, PREVIEW_H), old_pm, new_pm, spec, t,
                    mask_resolver=self._mask_resolver,
                )
            if t >= spec.total_duration:
                self._active_transition = None
        else:
            self._paint_bg(painter)
            self._paint_sprites(painter)

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
