                       
"""
Диалог редактирования ATL-блока (Ren'Py Animation & Transformation Language)
для нод show_sprite/show_bg/show_cg/scene - текстовый редактор + "честный"
живой предпросмотр анимации (позиция/зум/повтор/смена картинки), см.
core/atl.py.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QWidget, QListWidget, QSplitter, QTabWidget, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QElapsedTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QPixmap
from typing import Optional

from core import atl as atl_engine
from core.i18n import tr
from ui.atl_step_editor import AtlStepsPanel

PREVIEW_W = 660
PREVIEW_H = 371


class _AtlPreviewWidget(QWidget):
    """Мини-канва: честно проигрывает ATL-таймлайн (см.
    core/atl.resolve_visual) по реальному времени и рисует РЕАЛЬНУЮ картинку
    ноды (не силуэт-заглушку) - базовую или подменённую image-стейтментом,
    если удалось её разрешить через resolve_image_fn."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(PREVIEW_W, PREVIEW_H)
        self._atl_text = ""
        self._base_xalign = 0.5
        self._base_yalign = 1.0
        self._base_zoom = 1.0
        self._is_bg = False
        self._label = ""
        self._base_pixmap: Optional[QPixmap] = None
        self._resolve_image_fn = None
        self._img_cache: dict = {}
        self._clock = QElapsedTimer()
        self._clock.start()
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self.update)
        self._timer.start()

    def set_atl(self, text: str, base_xalign: float, base_yalign: float,
                base_zoom: float, is_bg: bool, label: str,
                base_pixmap: Optional[QPixmap] = None, resolve_image_fn=None):
        """ВАЖНО: раньше здесь при КАЖДОМ изменении текста (в т.ч. от
        перетаскивания ползунка в панели шагов) сравнивался старый/новый
        текст и, если он отличался, проигрывание сбрасывалось на t=0 -
        из-за этого анимация постоянно перезапускалась при любой правке
        параметров и посмотреть на неё "в развитии" было невозможно.
        Теперь параметры/текст просто обновляются на лету, а перезапуск
        происходит только явно - см. restart()/кнопку "Проиграть" в
        AtlEditorDialog."""
        self._atl_text = text
        self._base_xalign = base_xalign
        self._base_yalign = base_yalign
        self._base_zoom = base_zoom
        self._is_bg = is_bg
        self._label = label
        if base_pixmap is not None:
            self._base_pixmap = base_pixmap
        if resolve_image_fn is not None:
            self._resolve_image_fn = resolve_image_fn
        self.update()

    def restart(self):
        self._clock.restart()

    def _pixmap_for(self, image_text: str):
        """Возвращает QPixmap для варианта картинки, на который переключает
        ATL (image_text), с маленьким кэшем - или базовый pixmap ноды/None,
        если resolve_image_fn не задан или не нашёл ресурс."""
        if not image_text:
            return self._base_pixmap
        if image_text in self._img_cache:
            return self._img_cache[image_text] or self._base_pixmap
        pm = self._resolve_image_fn(image_text) if self._resolve_image_fn else None
        self._img_cache[image_text] = pm
        return pm or self._base_pixmap

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor("#1b1e24"))

                                 
        pen = QPen(QColor("#3a3f4a"))
        p.setPen(pen)
        for frac in (0.25, 0.5, 0.75):
            x = int(self.width() * frac)
            p.drawLine(x, 0, x, self.height())
            y = int(self.height() * frac)
            p.drawLine(0, y, self.width(), y)

        t = self._clock.elapsed() / 1000.0
        vis = atl_engine.resolve_visual(
            self._atl_text, t, base_xalign=self._base_xalign,
            base_yalign=self._base_yalign, base_zoom=self._base_zoom,
        )

        pm = self._pixmap_for(vis.get("image_text"))

        if pm is not None and not pm.isNull():
            if self._is_bg:
                scaled = pm.scaled(self.width(), self.height(),
                                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                    Qt.TransformationMode.SmoothTransformation)
                dx = (vis["xalign"] - 0.5) * self.width()
                dy = (vis["yalign"] - 0.5) * self.height()
                zoom = max(0.15, min(3.0, vis["zoom"]))
                x0 = (self.width() - scaled.width()) // 2
                y0 = (self.height() - scaled.height()) // 2
                p.save()
                p.translate(self.width() / 2, self.height() / 2)
                p.rotate(vis["rotate"])
                p.scale(zoom, zoom)
                p.translate(-self.width() / 2 + dx, -self.height() / 2 + dy)
                p.setOpacity(max(0.0, min(1.0, vis["alpha"])))
                p.drawPixmap(x0, y0, scaled)
                p.restore()
            else:
                zoom = max(0.15, min(3.0, vis["zoom"]))
                max_h = int(self.height() * 0.9)
                sh = min(max_h, int(pm.height() * zoom * 0.35))
                sw = int(pm.width() * (sh / pm.height())) if pm.height() else 0
                scaled = pm.scaled(sw, sh, Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
                cx = vis["xalign"] * self.width()
                cy = vis["yalign"] * self.height()
                x0 = int(cx - sw / 2)
                y0 = int(cy - sh)
                p.save()
                p.setOpacity(max(0.0, min(1.0, vis["alpha"])))
                if abs(vis["rotate"]) > 1e-6:
                    center = QRectF(x0, y0, sw, sh).center()
                    p.translate(center)
                    p.rotate(vis["rotate"])
                    p.translate(-center)
                p.drawPixmap(x0, y0, scaled)
                p.restore()
        else:
                                                                             
            w = self.width() * max(0.15, min(2.5, vis["zoom"])) if self._is_bg else \
                90 * max(0.15, min(3.0, vis["zoom"]))
            h = self.height() * max(0.15, min(2.5, vis["zoom"])) if self._is_bg else \
                150 * max(0.15, min(3.0, vis["zoom"]))
            cx = vis["xalign"] * self.width()
            cy = vis["yalign"] * self.height()
            rect = QRectF(cx - w / 2, cy - h / 2, w, h) if self._is_bg else \
                QRectF(cx - w / 2, cy - h, w, h)
            p.setOpacity(max(0.0, min(1.0, vis["alpha"])))
            p.translate(rect.center())
            p.rotate(vis["rotate"])
            p.translate(-rect.center())
            p.setBrush(QColor("#ff8c3d") if not self._is_bg else QColor("#4d8cff"))
            p.setPen(QPen(QColor("#ffffff"), 1))
            p.drawRoundedRect(rect, 6, 6)
            p.setOpacity(1.0)
            p.resetTransform()

        name = vis["image_text"] or self._label or "?"
        p.setPen(QPen(QColor("#e8e8e8")))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(8, self.height() - 10, f"{name}   t={t:0.2f}s")

        dur = atl_engine.cycle_duration(self._atl_text)
        if dur:
            p.drawText(8, 18, tr("atl.loop_duration", dur=f"{dur:.2f}"))
        elif atl_engine.is_animated(self._atl_text):
            p.drawText(8, 18, tr("atl.infinite_loop"))


class AtlEditorDialog(QDialog):
    """base_xalign/base_yalign/base_zoom - текущая позиция ноды (запасной
    вариант, если в ATL-блоке нет своих xalign/yalign/zoom) - для честного
    старта предпросмотра. is_bg - рисовать как фон (во весь экран) или как
    спрайт (силуэт персонажа)."""

    def __init__(self, atl_text: str, base_xalign: float = 0.5, base_yalign: float = 1.0,
                 base_zoom: float = 1.0, is_bg: bool = False, label: str = "", parent=None,
                 base_pixmap: Optional[QPixmap] = None, resolve_image_fn=None):
        super().__init__(parent)
        self.setWindowTitle(tr("atl.dialog_title"))
                                                                              
                                                                        
        from ui.theme import fit_window_to_screen
        fit_window_to_screen(self, 1500, 940, min_w=1200, min_h=780)
        self._base_xalign = base_xalign
        self._base_yalign = base_yalign
        self._base_zoom = base_zoom
        self._is_bg = is_bg
        self._label = label
        self._base_pixmap = base_pixmap
        self._resolve_image_fn = resolve_image_fn

        outer = QVBoxLayout(self)
        hint = QLabel(tr("atl.hint"))
        hint.setWordWrap(True)
        hint.setObjectName("hint_text")
        outer.addWidget(hint)

        split = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(split, 1)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        left_l.addWidget(self.tabs, 1)

        text_tab = QWidget()
        text_l = QVBoxLayout(text_tab)
        text_l.setContentsMargins(4, 4, 4, 4)
        text_l.addWidget(QLabel(tr("atl.code_label")))
        self.editor = QPlainTextEdit()
        self.editor.setPlainText(atl_text or "")
        self.editor.setFont(QFont("Consolas", 10))
        self.editor.setTabStopDistance(28)
        self.editor.textChanged.connect(self._on_text_changed)
        text_l.addWidget(self.editor, 1)
        self.tabs.addTab(text_tab, tr("atl.tab_text"))

        steps_tab = QWidget()
        steps_l = QVBoxLayout(steps_tab)
        steps_l.setContentsMargins(4, 4, 4, 4)
        steps_scroll = QScrollArea()
        steps_scroll.setWidgetResizable(True)
        steps_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.steps_panel = AtlStepsPanel()
        self.steps_panel.set_base(base_xalign, base_yalign, base_zoom)
        self.steps_panel.changed.connect(self._on_steps_changed)
        steps_scroll.setWidget(self.steps_panel)
        steps_l.addWidget(steps_scroll)
        self._steps_tab_index = self.tabs.addTab(steps_tab, tr("atl.tab_steps"))

        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._last_steps_text: Optional[str] = None
        self._syncing_from_steps = False

        self.warnings_label = QLabel("")
        self.warnings_label.setWordWrap(True)
        self.warnings_label.setObjectName("hint_text")
        self.warnings_label.setStyleSheet("color:#ffb84d;")
        left_l.addWidget(self.warnings_label)
        split.addWidget(left)

        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.addWidget(QLabel(tr("atl.preview_label")))
        self.preview = _AtlPreviewWidget()
        right_l.addWidget(self.preview)
        preview_btn_row = QHBoxLayout()
        preview_btn_row.addStretch()
        play_btn = QPushButton(tr("atl.play_button"))
        play_btn.clicked.connect(self.preview.restart)
        preview_btn_row.addWidget(play_btn)
        right_l.addLayout(preview_btn_row)
        right_l.addStretch()
        split.addWidget(right)
        split.setSizes([880, 620])

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        clear_btn = QPushButton(tr("atl.clear_button"))
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(clear_btn)
        cancel_btn = QPushButton(tr("atl.cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        ok_btn = QPushButton(tr("atl.save"))
        ok_btn.setObjectName("btn_apply_primary")
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        outer.addLayout(btn_row)

        self._on_text_changed()

    def _clear(self):
        self.editor.setPlainText("")

    def _on_steps_changed(self):
        """Панель шагов - источник истины, пока активна её вкладка: сразу
        пересобираем ATL-текст из шагов и прокидываем в текстовый редактор
        (а он уже сам обновит предпросмотр через _on_text_changed)."""
        text = self.steps_panel.to_atl_text()
        self._last_steps_text = text
        self._syncing_from_steps = True
        self.editor.setPlainText(text)
        self._syncing_from_steps = False

    def _on_tab_changed(self, index: int):
        if index != self._steps_tab_index:
            return
        current_text = self.editor.toPlainText()
                                                                          
                                                                          
        if current_text == (self._last_steps_text or ""):
            return
        lossy = self.steps_panel.load_from_text(
            current_text, self._base_xalign, self._base_yalign, self._base_zoom)
        self._last_steps_text = self.steps_panel.to_atl_text()
        if lossy:
            self.warnings_label.setText(tr("atl_steps.lossy_import_warning"))

    def _on_text_changed(self):
        text = self.editor.toPlainText()
        self.preview.set_atl(text, self._base_xalign, self._base_yalign,
                              self._base_zoom, self._is_bg, self._label,
                              base_pixmap=self._base_pixmap, resolve_image_fn=self._resolve_image_fn)
        warns = atl_engine.describe(text)
        if warns:
            preview = "; ".join(warns[:3])
            more = f" (+{len(warns) - 3})" if len(warns) > 3 else ""
            self.warnings_label.setText(tr("atl.unrecognized_lines", lines=preview + more))
        else:
            self.warnings_label.setText("")

    def atl_text(self) -> str:
        return self.editor.toPlainText().strip("\n")
