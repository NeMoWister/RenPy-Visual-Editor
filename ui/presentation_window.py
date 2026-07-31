"""
Режим «презентации» - быстрый прогон сценария по нодам с показом
результата подряд, без экспорта в Ren'Py. Открывается в отдельном окне на
весь экран и ведёт себя как обычная Ren'Py игра: клик/пробел - дальше,
меню кликабельно, есть автопрогон по таймеру и история реплик (backlog).

Не является полноценной VM Ren'Py: python/call-стек не выполняется,
raw-код меню не исполняется - только текстовые эффекты (фон/спрайты/
музыка/переходы/меню/паузы/jump-label).
"""
import os
from dataclasses import dataclass
from typing import List, Optional

from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRect, QRectF, QTimer, pyqtSignal, QUrl
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QKeyEvent, QTextDocument

from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from core.models import Project, NodeType
from core.presentation_engine import (
    Position, first_position, next_position, find_label, node_at, scene_at, fast_forward_state
)
from core.scene_state import SceneState, _apply_node
from ui.pixmap_cache import get_pixmap, get_composite
from core.renpy_text_tags import parse_renpy_text, runs_to_html, truncate_runs, visible_length, strip_tags as _clean


@dataclass
class BacklogEntry:
    char_name: str
    text: str


class PresentationCanvas(QWidget):
    advance_requested = pyqtSignal()
    choice_selected = pyqtSignal(int)
    reveal_complete = pyqtSignal(bool)                                                  

    TYPEWRITER_CPS = 42                                  

    def __init__(self):
        super().__init__()
        self.bg_pixmap: Optional[QPixmap] = None
        self.sprites: List[tuple] = []                                          
        self.char_name = ""
        self.char_color: Optional[str] = None
        self.text = ""
        self.menu_choices: Optional[List[str]] = None
        self._choice_rects: List[QRect] = []
        self.backlog: List[BacklogEntry] = []
        self.backlog_visible = False
        self.nvl_mode = False
        self.nvl_history: List[tuple] = []                                          
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._runs = []
        self._events = []
        self._reveal_count = 0
        self._total_len = 0
        self._consumed_event_idx = 0
        self.cps = self.TYPEWRITER_CPS                                                     
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(max(5, 1000 // self.cps))
        self._tick_timer.timeout.connect(self._on_tick)
        self._w_timer = QTimer(self)
        self._w_timer.setSingleShot(True)
        self._w_timer.timeout.connect(self._resume_from_w)

    def set_cps(self, cps: int):
        """Меняет скорость печати текста на лету (в т.ч. посреди уже идущей
        реплики) - используется переключателем скорости в presentation mode."""
        self.cps = max(1, cps)
        self._tick_timer.setInterval(max(5, 1000 // self.cps))

    def set_background(self, path: Optional[str]):
        self.bg_pixmap = get_pixmap(path) if path and os.path.isfile(path) else None
        self.update()

    def set_sprites(self, sprites: List[tuple]):
        self.sprites = sprites
        self.update()

    def set_nvl_mode(self, on: bool):
        if self.nvl_mode != on:
            self.nvl_mode = on
            self.update()

    def nvl_clear(self):
        self.nvl_history = []
        self.update()

    def start_typewriter(self, char_name: str, raw_text: str, color: Optional[str]):
        """Запускает посимвольную печать реплики с поддержкой тегов Ren'Py
        ({i}/{b}/{u}/{color}/{size}/{alpha}) и таймингов {w}/{nw}/{fast}."""
        if self.nvl_mode and (self.char_name or self.text):
                                                                              
                                                                          
            self.nvl_history.append((self.char_name, self.text, self.char_color))
            self.nvl_history = self.nvl_history[-8:]
        self.char_name = char_name
        self.char_color = color
        self.menu_choices = None
        self._tick_timer.stop()
        self._w_timer.stop()
        self._runs, self._events = parse_renpy_text(raw_text)
        self.text = raw_text
        self._total_len = visible_length(self._runs)
        self._reveal_count = 0
        self._consumed_event_idx = 0
        if self._total_len == 0:
            self.reveal_complete.emit(any(e.kind == "nw" for e in self._events))
        else:
            self._tick_timer.start()
        self.update()

    def _on_tick(self):
        while self._consumed_event_idx < len(self._events) and \
                self._events[self._consumed_event_idx].pos <= self._reveal_count:
            ev = self._events[self._consumed_event_idx]
            if ev.kind == "w" and ev.pos == self._reveal_count:
                self._consumed_event_idx += 1
                self._tick_timer.stop()
                if ev.duration:
                    self._w_timer.start(int(ev.duration * 1000))
                self.update()
                return
            self._consumed_event_idx += 1

        if self._reveal_count >= self._total_len:
            self._finish_reveal()
            return

        step = max(1, self.cps // 20)
        self._reveal_count = min(self._total_len, self._reveal_count + step)
        self.update()
        if self._reveal_count >= self._total_len:
            self._finish_reveal()

    def _resume_from_w(self):
        if self._reveal_count < self._total_len:
            self._tick_timer.start()
        else:
            self._finish_reveal()

    def _finish_reveal(self):
        self._tick_timer.stop()
        self._w_timer.stop()
        is_nw = any(e.kind == "nw" for e in self._events)
        self.reveal_complete.emit(is_nw)

    def is_fully_revealed(self) -> bool:
        return (self._reveal_count >= self._total_len
                and not self._tick_timer.isActive() and not self._w_timer.isActive())

    def skip_to_end(self):
        """Клик во время печати/паузы {w} - мгновенно показать весь текст
        (как в обычном Ren'Py)."""
        self._tick_timer.stop()
        self._w_timer.stop()
        self._reveal_count = self._total_len
        self.update()
        self.reveal_complete.emit(any(e.kind == "nw" for e in self._events))

    def set_dialogue(self, char_name: str, text: str, color: Optional[str]):
        """Мгновенный (без печати) показ текста - для служебных сообщений
        (конец прогона, пустой проект и т.п.), не для реплик сценария."""
        self._tick_timer.stop()
        self._w_timer.stop()
        self.char_name = char_name
        self.char_color = color
        self.menu_choices = None
        self._runs, self._events = parse_renpy_text(text)
        self.text = text
        self._total_len = visible_length(self._runs)
        self._reveal_count = self._total_len
        self.update()

    def set_menu(self, prompt: str, choices: List[str]):
        self._tick_timer.stop()
        self._w_timer.stop()
        self.char_name = ""
        self.char_color = None
        self.text = prompt
        self.menu_choices = choices
        self.update()

    def toggle_backlog(self):
        self.backlog_visible = not self.backlog_visible
        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(0, 0, w, h, QColor(0, 0, 0))

        if self.bg_pixmap:
            scaled = self.bg_pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                            Qt.TransformationMode.SmoothTransformation)
            x = (w - scaled.width()) // 2
            y = (h - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.setPen(QColor(70, 70, 85))
            painter.setFont(QFont("Arial", 20))
            painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "[ Нет фона ]")

        for pm, xalign, yalign, zoom in self.sprites:
            sw = int(pm.width() * zoom * (h / 720))
            sh = int(pm.height() * zoom * (h / 720))
            max_h = int(h * 0.92)
            if sh > max_h:
                scale = max_h / sh
                sw = int(sw * scale)
                sh = max_h
            x = int(xalign * w - sw / 2)
            y = int(h - sh - h * 0.02)
            scaled = pm.scaled(sw, sh, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(x, y, scaled)

        if self.menu_choices is not None:
            self._paint_menu(painter, w, h)
        elif self.nvl_mode:
            self._paint_nvl(painter, w, h)
        elif self.text or self.char_name:
            self._paint_dialogue(painter, w, h)

        if self.backlog_visible:
            self._paint_backlog(painter, w, h)

        painter.end()

    def _paint_dialogue(self, painter: QPainter, w: int, h: int):
        pad = int(w * 0.03)
        base_font_px = max(13, int(h * 0.024))
        min_box_h = int(h * 0.22)
        max_box_h = int(h * 0.6)

        visible_runs = truncate_runs(self._runs, self._reveal_count) if self._runs else []
        html = runs_to_html(visible_runs, base_size=base_font_px) if visible_runs else ""
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Arial", base_font_px))
        doc.setTextWidth(w - 2 * pad)
        doc.setHtml(f'<div style="color:#e6e6e6;">{html}</div>')

                                                                          
                                                                      
                                                                         
                                                                          
        text_area_h = max(int(doc.size().height()), 1)
        box_h = min(max_box_h, max(min_box_h, text_area_h + int(min_box_h * 0.25)))
        box_y = h - box_h - int(h * 0.03)
        painter.fillRect(0, box_y, w, box_h, QColor(0, 0, 0, 190))

        text_top = box_y + int(box_h * 0.15)
        if self.char_name:
            name_h = int(min_box_h * 0.28)
            painter.fillRect(pad, box_y - name_h, int(w * 0.16), name_h, QColor(5, 5, 5, 230))
            color = QColor(self.char_color) if self.char_color and QColor(self.char_color).isValid() else QColor(255, 255, 255)
            painter.setPen(color)
            painter.setFont(QFont("Arial", max(12, int(h * 0.022)), QFont.Weight.Bold))
            painter.drawText(QRect(pad, box_y - name_h, int(w * 0.16), name_h),
                              Qt.AlignmentFlag.AlignCenter, self.char_name)

        painter.setPen(QColor(230, 230, 230))
        painter.setFont(QFont("Arial", base_font_px))
        text_rect = QRect(pad, text_top, w - 2 * pad, box_h - int(box_h * 0.15) - 10)
        if visible_runs:
            painter.save()
            painter.translate(text_rect.topLeft())
            doc.drawContents(painter)
            painter.restore()

        painter.setPen(QColor(150, 150, 150))
        painter.setFont(QFont("Arial", 10))
        hint = "клик / пробел ▶" if self.is_fully_revealed() else "клик - показать целиком"
        painter.drawText(QRect(w - 220, h - 22, 210, 20), Qt.AlignmentFlag.AlignRight, hint)

    def _paint_nvl(self, painter: QPainter, w: int, h: int):
        """NVL-режим: во весь экран, реплики накапливаются друг под другом
        (последние self.nvl_history + текущая печатающаяся внизу списка) -
        в отличие от ADV, где видна только одна текущая реплика в окне снизу.

        Важно: все строки собираются в ОДИН QTextDocument (параграфами), а не
        рисуются по отдельности каждая своим документом - иначе Qt-раскладка
        текста для каждой строки считается независимо и может неверно
        обрезаться/наезжать друг на друга. drawContents() вызывается БЕЗ
        прямоугольника (без клиппинга) - иначе при недооценке высоты текст
        обрезался посередине."""
        pad_x = int(w * 0.08)
        pad_top = int(h * 0.05)
        base_font_px = max(15, int(h * 0.032))

        html_parts = []
        for char_name, text, color in self.nvl_history:
            runs, _ = parse_renpy_text(text)
            html_parts.append(self._nvl_line_html(char_name, runs, color, dim=True, base_size=base_font_px))

        visible_runs = truncate_runs(self._runs, self._reveal_count) if self._runs else []
        if visible_runs or self.char_name:
            html_parts.append(self._nvl_line_html(self.char_name, visible_runs, self.char_color, dim=False, base_size=base_font_px))

                                                                         
                                                                           
                                                                            
                                                                            
                                                                           
                                                                     
        panel_h = int(h * 0.88)
        doc = None
        if html_parts:
            doc = QTextDocument()
            doc.setDefaultFont(QFont("Arial", base_font_px))
            doc.setTextWidth(w - 2 * pad_x)
            doc.setHtml("".join(html_parts))

        painter.fillRect(0, 0, w, panel_h, QColor(6, 6, 10, 210))

        if doc is not None:
            painter.save()
            painter.translate(pad_x, pad_top)
            doc.drawContents(painter)                                          
            painter.restore()

        painter.setPen(QColor(150, 150, 150))
        painter.setFont(QFont("Arial", 10))
        hint = "клик / пробел ▶" if self.is_fully_revealed() else "клик - показать целиком"
        painter.drawText(QRect(w - 220, h - 26, 210, 20), Qt.AlignmentFlag.AlignRight, hint)

    def _nvl_line_html(self, char_name: str, runs, color: Optional[str], dim: bool, base_size: int = 15) -> str:
        prefix_html = ""
        if char_name:
            c = QColor(color) if color and QColor(color).isValid() else QColor(255, 255, 255)
                                                                           
                                                                          
                                                                         
                                            
            prefix_html = f'<b style="color:{c.name()}; font-size:{base_size}px;">{char_name}:</b>&nbsp;'
        body_html = runs_to_html(runs, base_size=base_size) if runs else ""
        text_color = "#8d8d92" if dim else "#e9e9ee"
        return f'<p style="color:{text_color}; margin:0 0 16px 0; line-height:140%;">{prefix_html}{body_html}</p>'

    def _paint_menu(self, painter: QPainter, w: int, h: int):
        painter.fillRect(0, 0, w, h, QColor(0, 0, 0, 140))
        if self.text:
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", max(16, int(h * 0.03)), QFont.Weight.Bold))
            painter.drawText(QRect(0, int(h * 0.18), w, int(h * 0.1)),
                              Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, _clean(self.text))

        self._choice_rects = []
        n = len(self.menu_choices)
        btn_w = int(w * 0.4)
        btn_h = int(h * 0.07)
        gap = int(h * 0.02)
        total_h = n * btn_h + (n - 1) * gap
        start_y = int(h * 0.35) if not self.text else int(h * 0.32)
        start_y = max(start_y, (h - total_h) // 2)
        x = (w - btn_w) // 2
        painter.setFont(QFont("Arial", max(13, int(h * 0.022))))
        for i, choice in enumerate(self.menu_choices):
            y = start_y + i * (btn_h + gap)
            rect = QRect(x, y, btn_w, btn_h)
            self._choice_rects.append(rect)
            painter.setPen(QPen(QColor(255, 140, 60), 2))
            painter.setBrush(QColor(20, 20, 26, 220))
            painter.drawRoundedRect(rect, 8, 8)
            painter.setPen(QColor(240, 240, 240))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, _clean(choice))

    def _paint_backlog(self, painter: QPainter, w: int, h: int):
        painter.fillRect(0, 0, w, h, QColor(5, 5, 8, 235))
        painter.setPen(QColor(255, 140, 60))
        painter.setFont(QFont("Arial", max(15, int(h * 0.026)), QFont.Weight.Bold))
        painter.drawText(QRect(0, int(h * 0.04), w, 40), Qt.AlignmentFlag.AlignCenter, "История реплик (Tab - закрыть)")

        pad = int(w * 0.12)
        content_w = w - 2 * pad
        y = int(h * 0.12)
        max_y = h - 30
        font = QFont("Arial", max(12, int(h * 0.02)))
        painter.setFont(font)
        metrics = painter.fontMetrics()
        gap = int(h * 0.015)

        for entry in self.backlog[-30:]:
            if y > max_y:
                break
            prefix = f"{entry.char_name}: " if entry.char_name else ""
            full_text = f"{prefix}{_clean(entry.text)}"
            needed_rect = metrics.boundingRect(QRect(0, 0, content_w, 10_000),
                                                Qt.TextFlag.TextWordWrap, full_text)
            entry_h = max(metrics.height(), needed_rect.height())
            painter.setPen(QColor(255, 180, 100) if entry.char_name else QColor(200, 200, 200))
            painter.drawText(QRect(pad, y, content_w, entry_h),
                              Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, full_text)
            y += entry_h + gap

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self.backlog_visible:
            self.backlog_visible = False
            self.update()
            return
        if self.menu_choices is not None:
            pos = event.position().toPoint()
            for i, rect in enumerate(self._choice_rects):
                if rect.contains(pos):
                    self.choice_selected.emit(i)
                    return
            return
        if not self.is_fully_revealed():
            self.skip_to_end()
            return
        self.advance_requested.emit()


class PresentationWindow(QWidget):
    def __init__(self, project: Project, rm, parent=None, start_pos: Optional[Position] = None):
        super().__init__(parent, Qt.WindowType.Window)
        self.project = project
        self.rm = rm
        self.setWindowTitle(f"Презентация - {project.title}")
        self.setStyleSheet("background:#000;")
        self.state = SceneState()
        self.pos: Optional[Position] = None
        self.autoplay = False
        self._pending_choice_positions: List[Optional[Position]] = []
                                                                     
        self.label_trail: List[str] = []
                                                                              
                                                                          
                                                                              
        self._line_history: List[Position] = []
        self._speed_presets = [0.5, 1.0, 1.5, 2.0, 3.0]
        self._speed_idx = 1                    

        self.canvas = PresentationCanvas()
        self.canvas.advance_requested.connect(self._on_advance_clicked)
        self.canvas.choice_selected.connect(self._on_choice_selected)
        self.canvas.reveal_complete.connect(self._on_reveal_complete)

        self._setup_audio()
        self._setup_ui()

        self.auto_timer = QTimer(self)
        self.auto_timer.setSingleShot(True)
        self.auto_timer.timeout.connect(self._on_advance_clicked)

        self.showFullScreen()
        self._start(start_pos)

    def _setup_audio(self):
        self.music_player = QMediaPlayer(self)
        self.music_output = QAudioOutput(self)
        self.music_player.setAudioOutput(self.music_output)
        self.sound_player = QMediaPlayer(self)
        self.sound_output = QAudioOutput(self)
        self.sound_player.setAudioOutput(self.sound_output)
        self.ambience_player = QMediaPlayer(self)
        self.ambience_output = QAudioOutput(self)
        self.ambience_player.setAudioOutput(self.ambience_output)
        for p in (self.music_player, self.ambience_player):
            try:
                p.setLoops(QMediaPlayer.Loops.Infinite)
            except Exception:
                pass

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        bar = QWidget(self)
        bar.setStyleSheet("background: rgba(15,15,20,180); border-radius: 8px;")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(8, 4, 8, 4)

        btn_style = """
            QPushButton {
                background: #ff8c3d; color: #1a1005; font-weight: bold;
                border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px;
            }
            QPushButton:hover { background: #ffa020; }
            QPushButton:pressed { background: #e6752a; }
            QPushButton:checked { background: #cc5500; color: #fff; }
        """

        self.autoplay_btn = QPushButton("▶ Автопрогон: выкл")
        self.autoplay_btn.setCheckable(True)
        self.autoplay_btn.setStyleSheet(btn_style)
        self.autoplay_btn.clicked.connect(self._toggle_autoplay)
        bl.addWidget(self.autoplay_btn)

        btn_prev_line = QPushButton("⏮ Пред. реплика (←)")
        btn_prev_line.setStyleSheet(btn_style)
        btn_prev_line.clicked.connect(self._step_back_line)
        bl.addWidget(btn_prev_line)

        self.speed_btn = QPushButton()
        self.speed_btn.setStyleSheet(btn_style)
        self.speed_btn.setToolTip("Скорость печати текста ([ медленнее / ] быстрее)")
        self.speed_btn.clicked.connect(self._cycle_speed)
        self._update_speed_btn_text()
        bl.addWidget(self.speed_btn)

        btn_backlog = QPushButton("📜 История (Tab)")
        btn_backlog.setStyleSheet(btn_style)
        btn_backlog.clicked.connect(self.canvas.toggle_backlog)
        bl.addWidget(btn_backlog)

        btn_skip = QPushButton("⏭ Пропустить шаг")
        btn_skip.setStyleSheet(btn_style)
        btn_skip.clicked.connect(self._on_advance_clicked)
        bl.addWidget(btn_skip)

        btn_close = QPushButton("✕ Выход (Esc)")
        btn_close.setStyleSheet(btn_style)
        btn_close.clicked.connect(self.close)
        bl.addWidget(btn_close)

        bar.setParent(self)
        bar.move(16, 16)
        bar.adjustSize()
        self._toolbar = bar

                                                    
        crumbs = QWidget(self)
        crumbs.setStyleSheet("background: rgba(15,15,20,150); border-radius: 6px;")
        cl = QHBoxLayout(crumbs)
        cl.setContentsMargins(10, 4, 10, 4)
        self.breadcrumb_label = QLabel("")
        self.breadcrumb_label.setStyleSheet("color:#9fd6ff; font-size:11px;")
        cl.addWidget(self.breadcrumb_label)
        crumbs.setParent(self)
        crumbs.adjustSize()
        self._breadcrumb_bar = crumbs

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_toolbar"):
            self._toolbar.move(16, 16)
        if hasattr(self, "_breadcrumb_bar"):
            self._breadcrumb_bar.move(16, self._toolbar.height() + 24)

                                                                           

    def _start(self, start_pos: Optional[Position] = None):
        self._line_history = []
        if start_pos is not None:
            state, last_music, last_ambience, last_label, nvl_lines = fast_forward_state(
                self.project, start_pos, rm=self.rm)
            self.state = state
            self.pos = start_pos
            self.label_trail = [last_label] if last_label else []
            self.canvas.nvl_history = list(nvl_lines)
            self._refresh_visuals()
            if last_music is not None:
                self._handle_audio(last_music)
            if last_ambience is not None:
                self._handle_audio(last_ambience)
        else:
            self.pos = first_position(self.project)
            self.state = SceneState()
            self.label_trail = []
        self._update_breadcrumb()
        if self.pos is None:
            self.canvas.set_dialogue("", "В проекте нет ни одной сцены с нодами.", None)
            return
        self._run_until_blocking()

    def _refresh_visuals(self):
        self.canvas.set_nvl_mode(self.state.nvl_mode)
        bg_path = self._resolve(self.state.cg_var) or self._resolve(self.state.bg_var)
        self.canvas.set_background(bg_path)
        sprites = []
        for sp in self.state.sprite_list():
            pm = None
            if sp.composite is not None:
                layer_paths = [
                    (self.rm.resolve_layer_path(layer.rel_path, sp.composite.source), layer.offset_x, layer.offset_y)
                    for layer in sp.composite.layers
                ]
                pm = get_composite(layer_paths, sp.composite.width, sp.composite.height)
            else:
                path = self._resolve(sp.var)
                if path:
                    pm = get_pixmap(path)
            if pm is not None:
                sprites.append((pm, sp.position.xalign, sp.position.yalign, sp.position.zoom))
        self.canvas.set_sprites(sprites)

    def _resolve(self, var: Optional[str]) -> Optional[str]:
        if not var or self.rm is None:
            return None
        entry = self.rm.find_by_var(var)
        return entry.abs_path if entry else None

    def _handle_audio(self, node):
        t = node.node_type
        if t == NodeType.PLAY_MUSIC and node.music_var:
            path = self._resolve(node.music_var)
            if path:
                self.music_player.setSource(QUrl.fromLocalFile(path))
                self.music_player.play()
        elif t == NodeType.STOP_MUSIC:
            self.music_player.stop()
        elif t == NodeType.PLAY_AMBIENCE and node.ambience_var:
            path = self._resolve(node.ambience_var)
            if path:
                self.ambience_player.setSource(QUrl.fromLocalFile(path))
                self.ambience_player.play()
        elif t == NodeType.STOP_AMBIENCE:
            self.ambience_player.stop()
        elif t == NodeType.PLAY_SOUND and node.sound_var:
            path = self._resolve(node.sound_var)
            if path:
                self.sound_player.setSource(QUrl.fromLocalFile(path))
                self.sound_player.play()

    def _run_until_blocking(self):
        """Проигрывает ноды подряд, автоматически применяя эффекты, пока не
        встретит ноду, требующую реакции игрока (реплика/меню/пауза-клик)
        или конца прогона."""
        self.auto_timer.stop()
        while True:
            if self.pos is None:
                self._show_end()
                return
            node = node_at(self.project, self.pos)
            _apply_node(self.state, node, is_current=True, rm=self.rm)
            self._handle_audio(node)
            self._refresh_visuals()

            t = node.node_type
            if t == NodeType.LABEL:
                self._push_breadcrumb(node.label_name)
            if t == NodeType.NVL_MODE and node.nvl_action in ("enter", "clear"):
                self.canvas.nvl_clear()
            if t in (NodeType.DIALOGUE, NodeType.NARRATION):
                self._record_line_position(self.pos)
                char_label = ""
                color = None
                if self.state.char_var:
                    ch = self.project.get_character_by_var(self.state.char_var)
                    char_label = ch.name if ch else self.state.char_var
                    color = ch.color if ch else None
                self.canvas.start_typewriter(char_label, self.state.text, color)
                self.canvas.backlog.append(BacklogEntry(char_label, self.state.text))
                return
            if t == NodeType.MENU:
                choices = node.normalized_menu_choices()
                self._pending_choice_positions = []
                labels = []
                for ct, cj, use_call, raw_body, _nodes in choices:
                    labels.append(ct)
                    self._pending_choice_positions.append(find_label(self.project, cj) if cj else None)
                self.canvas.set_menu(node.menu_prompt, labels)
                return
            if t == NodeType.PAUSE:
                if node.pause_duration and node.pause_duration > 0:
                    self.pos = next_position(self.project, self.pos)
                    self.auto_timer.start(int(node.pause_duration * 1000))
                    return
                self.canvas.set_dialogue("", "", None)
                self.pos = next_position(self.project, self.pos)
                return
            if t == NodeType.RETURN:
                self.pos = None
                continue
            if t == NodeType.JUMP:
                self.pos = find_label(self.project, node.jump_target)
                continue

            self.pos = next_position(self.project, self.pos)

    def _push_breadcrumb(self, label_name: str):
        if not label_name:
            return
        if not self.label_trail or self.label_trail[-1] != label_name:
            self.label_trail.append(label_name)
            self.label_trail = self.label_trail[-8:]
        self._update_breadcrumb()

    def _update_breadcrumb(self):
        if not hasattr(self, "breadcrumb_label"):
            return
        if not self.label_trail:
            self.breadcrumb_label.setText("")
            self._breadcrumb_bar.setVisible(False)
            return
        prefix = "… › " if len(self.label_trail) >= 8 else ""
        self.breadcrumb_label.setText(prefix + " › ".join(self.label_trail))
        self._breadcrumb_bar.setVisible(True)
        self._breadcrumb_bar.adjustSize()

    def _record_line_position(self, pos: Position):
        if not self._line_history or self._line_history[-1] != pos:
            self._line_history.append(pos)

    def _step_back_line(self):
        """Перемотка назад на предыдущую реплику (Left/A/кнопка) - состояние
        пересчитывается заново через fast_forward_state, без "отмены"
        побочных эффектов (это не undo, а честный пересчёт state на нужный
        момент)."""
        if len(self._line_history) < 2:
            return
        self._line_history.pop()
        target = self._line_history[-1]
        state, last_music, last_ambience, last_label, nvl_lines = fast_forward_state(self.project, target, rm=self.rm)
        node = node_at(self.project, target)
        _apply_node(state, node, is_current=True, rm=self.rm)
        self.state = state
        self.pos = target
        self.label_trail = [last_label] if last_label else []
        self.canvas.nvl_history = list(nvl_lines)
        self._update_breadcrumb()
        self._refresh_visuals()
        if last_music is not None:
            self._handle_audio(last_music)
        else:
            self.music_player.stop()
        if last_ambience is not None:
            self._handle_audio(last_ambience)
        else:
            self.ambience_player.stop()

        char_label = ""
        color = None
        if self.state.char_var:
            ch = self.project.get_character_by_var(self.state.char_var)
            char_label = ch.name if ch else self.state.char_var
            color = ch.color if ch else None
        self.auto_timer.stop()
        self.canvas.set_dialogue(char_label, self.state.text, color)

    def _update_speed_btn_text(self):
        mult = self._speed_presets[self._speed_idx]
        label = "мгновенно" if mult >= 3.0 else f"{mult:g}x"
        self.speed_btn.setText(f"⚡ Скорость текста: {label}")

    def _cycle_speed(self):
        self._speed_idx = (self._speed_idx + 1) % len(self._speed_presets)
        self._apply_speed()

    def _adjust_speed(self, delta: int):
        self._speed_idx = max(0, min(len(self._speed_presets) - 1, self._speed_idx + delta))
        self._apply_speed()

    def _apply_speed(self):
        mult = self._speed_presets[self._speed_idx]
        self.canvas.set_cps(int(self.canvas.TYPEWRITER_CPS * mult))
        self._update_speed_btn_text()

    def _show_end(self):
        self.auto_timer.stop()
        self.canvas.set_dialogue("", "- Конец прогона -\n\nEsc - закрыть, клик - начать сначала.", None)

    def _on_advance_clicked(self):
        if self.pos is None:
            self._start()
            return
        self.pos = next_position(self.project, self.pos)
        self._run_until_blocking()

    def _on_key_or_click_advance(self):
        """Space/Enter - то же самое, что клик по канве: если текст ещё
        печатается или стоит на паузе {w}, сначала показать его целиком, и
        только следующее нажатие переходит дальше."""
        if self.canvas.menu_choices is None and not self.canvas.is_fully_revealed():
            self.canvas.skip_to_end()
            return
        self._on_advance_clicked()

    def _on_reveal_complete(self, is_nw: bool):
        """Текст реплики допечатан полностью."""
        if is_nw:
            self._on_advance_clicked()
        elif self.autoplay:
            ms = min(6000, max(1200, len(_clean(self.canvas.text)) * 45))
            self.auto_timer.start(ms)

    def _on_choice_selected(self, index: int):
        if 0 <= index < len(self._pending_choice_positions):
            target = self._pending_choice_positions[index]
            self.pos = target if target is not None else next_position(self.project, self.pos)
        self._run_until_blocking()

    def _toggle_autoplay(self, checked: bool):
        self.autoplay = checked
        self.autoplay_btn.setText(f"▶ Автопрогон: {'вкл' if checked else 'выкл'}")
        if not checked:
            self.auto_timer.stop()
        elif self.pos is not None and self.canvas.is_fully_revealed():
            node = node_at(self.project, self.pos)
            if node.node_type in (NodeType.DIALOGUE, NodeType.NARRATION):
                ms = min(6000, max(1200, len(_clean(self.canvas.text)) * 45))
                self.auto_timer.start(ms)

    def wheelEvent(self, event):
        """Ctrl + колесо мыши - перемотка по репликам (вперёд/назад), как
        зажатый Ctrl для быстрой перемотки в самом Ren'Py. Без Ctrl колесо
        не используется, чтобы не перематывать случайно."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            notches = int(delta / 120) if delta else 0
            if notches > 0:
                for _ in range(notches):
                    self._step_back_line()
            elif notches < 0:
                for _ in range(-notches):
                    self._on_key_or_click_advance()
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close()
        elif key == Qt.Key.Key_Tab:
            self.canvas.toggle_backlog()
        elif key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Right):
            self._on_key_or_click_advance()
        elif key == Qt.Key.Key_Left:
            self._step_back_line()
        elif key == Qt.Key.Key_BracketLeft:
            self._adjust_speed(-1)
        elif key == Qt.Key.Key_BracketRight:
            self._adjust_speed(1)
        elif key == Qt.Key.Key_A:
            self.autoplay_btn.toggle()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.auto_timer.stop()
        self.canvas._tick_timer.stop()
        self.canvas._w_timer.stop()
        self.music_player.stop()
        self.sound_player.stop()
        self.ambience_player.stop()
        super().closeEvent(event)
