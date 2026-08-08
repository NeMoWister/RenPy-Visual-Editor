                       
"""
Диалог настройки перехода (то, что пишется после "with") - быстрый выбор
готового именованного перехода (см. core/transitions.py:BUILTIN_TRANSITIONS)
либо кастомная настройка через конструктор (Dissolve/Fade/Pixellate/Wipe/
Push/ImageDissolve), в т.ч. ImageDissolve по произвольному файлу-маске.
"""
import os
import random
import shutil
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QDoubleSpinBox, QSpinBox, QFrame, QFileDialog, QColorDialog, QTabWidget, QWidget,
    QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, QElapsedTimer, QRect
from PyQt6.QtGui import QPainter, QColor, QFont, QPixmap

from core import transitions as trmod
from core.transitions import TransitionSpec, TransitionKind, BUILTIN_TRANSITIONS, TRANSITION_NAMES, DIRECTIONS
from core import custom_transitions as ctstore
from core.i18n import tr
from ui.pixmap_cache import get_pixmap
from ui.transition_compositor import render_transition_frame, punch_offset, clear_mask_cache

PREVIEW_W = 480
PREVIEW_H = 270

KIND_ITEMS = [
    (TransitionKind.DISSOLVE, "trans.kind_dissolve"),
    (TransitionKind.FADE, "trans.kind_fade"),
    (TransitionKind.PIXELLATE, "trans.kind_pixellate"),
    (TransitionKind.IMAGE_DISSOLVE, "trans.kind_image_dissolve"),
    (TransitionKind.WIPE, "trans.kind_wipe"),
    (TransitionKind.PUSH, "trans.kind_push"),
    (TransitionKind.PUNCH, "trans.kind_punch"),
]


def _pick_demo_pixmap(rm, exclude: Optional[QPixmap]) -> Optional[QPixmap]:
    """Для наглядности предпросмотра берёт случайный фон/CG из ресурсов
    проекта (вместо тонирования той же картинки) - так по переходу видно
    реальную разницу кадров, а не просто цветной оверлей. None, если в
    проекте вообще нет фонов/CG (тогда предпросмотр покажет заглушку)."""
    if rm is None:
        return None
    entries = []
    for cat in ("bg", "cg"):
        try:
            entries.extend(rm.get(cat) or [])
        except Exception:
            pass
    random.shuffle(entries)
    for entry in entries:
        pm = get_pixmap(getattr(entry, "abs_path", None))
        if pm is not None and not pm.isNull():
            return pm
    return None


def _tint_pixmap(pm: QPixmap) -> QPixmap:
    """Фолбэк, если в проекте нет вообще никаких фонов/CG для честного
    демо-перехода (пустой проект) - просто лёгкое затемнение той же
    картинки, чтобы хоть что-то отличалось."""
    out = QPixmap(pm.size())
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.drawPixmap(0, 0, pm)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
    p.fillRect(out.rect(), QColor(20, 40, 90, 130))
    p.end()
    return out


class _TransitionPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(PREVIEW_W, PREVIEW_H)
        self._old_pm: Optional[QPixmap] = None
        self._new_pm: Optional[QPixmap] = None
        self._spec: Optional[TransitionSpec] = None
        self._mask_resolver = None
        self._clock = QElapsedTimer()
        self._clock.start()
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self.update)
        self._timer.start()

    def set_base_pixmap(self, pm: Optional[QPixmap], rm=None):
        def _fit(src: QPixmap) -> QPixmap:
            scaled = src.scaled(PREVIEW_W, PREVIEW_H, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                 Qt.TransformationMode.SmoothTransformation)
            crop = QPixmap(PREVIEW_W, PREVIEW_H)
            crop.fill(QColor("#1b1e24"))
            p = QPainter(crop)
            p.drawPixmap((PREVIEW_W - scaled.width()) // 2, (PREVIEW_H - scaled.height()) // 2, scaled)
            p.end()
            return crop

        if pm is not None and not pm.isNull():
            self._old_pm = _fit(pm)
            demo = _pick_demo_pixmap(rm, exclude=pm)
            self._new_pm = _fit(demo) if demo is not None else _tint_pixmap(self._old_pm)
        else:
                                                                          
                                                                    
            first = _pick_demo_pixmap(rm, exclude=None)
            second = _pick_demo_pixmap(rm, exclude=first)
            if first is not None:
                self._old_pm = _fit(first)
                self._new_pm = _fit(second) if second is not None else _tint_pixmap(self._old_pm)
            else:
                self._old_pm = None
                self._new_pm = None

    def set_mask_resolver(self, fn):
        self._mask_resolver = fn

    def set_spec(self, spec: TransitionSpec):
        self._spec = spec
        clear_mask_cache()
        self._clock.restart()

    def restart(self):
        self._clock.restart()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor("#101216"))
        if self._spec is None:
            return
        dur = self._spec.total_duration
        t = self._clock.elapsed() / 1000.0
        loop_t = t % (dur + 0.6)                                                    
        if self._spec.kind == TransitionKind.PUNCH:
            dx, dy = punch_offset(self._spec, loop_t)
            p.save()
            p.translate(dx, dy)
            if self._old_pm is not None:
                p.drawPixmap(0, 0, self._old_pm)
            p.restore()
        else:
            render_transition_frame(p, QRect(0, 0, PREVIEW_W, PREVIEW_H),
                                     self._old_pm, self._new_pm, self._spec, loop_t,
                                     mask_resolver=self._mask_resolver)
        p.setPen(QColor("#e8e8e8"))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(8, PREVIEW_H - 8, f"t={min(loop_t, dur):.2f}/{dur:.2f}s")


class TransitionEditorDialog(QDialog):
    def __init__(self, current_value: str, base_pixmap: Optional[QPixmap] = None,
                 mask_resolver=None, mask_import_fn=None, rm=None, parent=None):
        """mask_import_fn(src_abs_path) -> rel_path_for_code|None - копирует
        выбранный файл маски в ресурсы проекта и возвращает путь, который
        нужно записать в generated ImageDissolve(...) (см. node_editor.py).
        rm - ResourceManager: нужен, чтобы (а) подставить случайный фон/CG
        проекта в демо-предпросмотр вместо тонирования, и (б) сохранять/
        предлагать повторно использовать именованные кастомные переходы."""
        super().__init__(parent)
        self.setWindowTitle(tr("trans.dialog_title"))
        self.resize(980, 660)
        self.setMinimumSize(860, 600)
        self._mask_import_fn = mask_import_fn
        self._mask_resolver = mask_resolver
        self._rm = rm
        self._result_text = current_value or ""
        self._custom = ctstore.load_custom_transitions(getattr(rm, 'base_dir', None)) if rm else {}

        outer = QVBoxLayout(self)

        tabs = QTabWidget()

                                                    
        preset_tab = QWidget()
        preset_l = QVBoxLayout(preset_tab)
        preset_l.addWidget(QLabel(tr("trans.preset_hint")))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem(tr("trans.preset_none"), "")
        for name in TRANSITION_NAMES:
            self.preset_combo.addItem(name, name)
        if self._custom:
            self.preset_combo.insertSeparator(self.preset_combo.count())
            for name in sorted(self._custom.keys()):
                self.preset_combo.addItem(tr("trans.preset_custom_label", name=name), name)
        resolved_current = self._custom.get(current_value, current_value) if current_value else ""
        existing_spec = trmod.parse_transition(resolved_current) if resolved_current else None
        is_known_name = current_value in BUILTIN_TRANSITIONS or current_value in self._custom
        idx = self.preset_combo.findData(current_value if is_known_name else "")
        self.preset_combo.setCurrentIndex(max(0, idx))
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_l.addWidget(self.preset_combo)
        preset_l.addStretch()
        tabs.addTab(preset_tab, tr("trans.tab_preset"))

                                       
        custom_tab = QWidget()
        custom_l = QVBoxLayout(custom_tab)

        kind_row = QHBoxLayout()
        kind_row.addWidget(QLabel(tr("trans.kind_label")))
        self.kind_combo = QComboBox()
        for kind, key in KIND_ITEMS:
            self.kind_combo.addItem(tr(key), kind)
        self.kind_combo.currentIndexChanged.connect(self._on_kind_changed)
        kind_row.addWidget(self.kind_combo)
        kind_row.addStretch()
        custom_l.addLayout(kind_row)

                                                       
        self.dur_row, self.dur_spin = self._param_row(custom_l, tr("trans.duration_label"), 0.05, 10.0, 0.5)
                                                             
        self.fo_row, self.fo_spin = self._param_row(custom_l, tr("trans.fade_out_label"), 0.0, 10.0, 0.5)
        self.fh_row, self.fh_spin = self._param_row(custom_l, tr("trans.fade_hold_label"), 0.0, 10.0, 0.0)
        self.fi_row, self.fi_spin = self._param_row(custom_l, tr("trans.fade_in_label"), 0.0, 10.0, 0.5)
        self.color_row = QHBoxLayout()
        self.color_row.addWidget(QLabel(tr("trans.fade_color_label")))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 24)
        self.color_btn.clicked.connect(self._pick_color)
        self._fade_color = "#000000"
        self._update_color_btn()
        self.color_row.addWidget(self.color_btn)
        self.color_row.addStretch()
        custom_l.addLayout(self.color_row)

        self.steps_row, self.steps_spin = self._param_row(custom_l, tr("trans.pixellate_steps_label"), 1, 8, 5, is_int=True)

        self.mask_row = QHBoxLayout()
        self.mask_row.addWidget(QLabel(tr("trans.mask_label")))
        self.mask_path_lbl = QLabel(tr("trans.mask_none"))
        self.mask_path_lbl.setObjectName("hint_text")
        self.mask_row.addWidget(self.mask_path_lbl, 1)
        self.mask_browse_btn = QPushButton(tr("trans.mask_browse"))
        self.mask_browse_btn.clicked.connect(self._browse_mask)
        self.mask_row.addWidget(self.mask_browse_btn)
        custom_l.addLayout(self.mask_row)
        self.ramp_row, self.ramp_spin = self._param_row(custom_l, tr("trans.ramp_label"), 1, 255, 8, is_int=True)
        self._mask_abs_path: Optional[str] = None
        self._mask_rel_path: str = ""

        self.dir_row = QHBoxLayout()
        self.dir_row.addWidget(QLabel(tr("trans.direction_label")))
        self.dir_combo = QComboBox()
        for d in DIRECTIONS:
            self.dir_combo.addItem(tr(f"trans.dir_{d}"), d)
        self.dir_row.addWidget(self.dir_combo)
        self.dir_row.addStretch()
        custom_l.addLayout(self.dir_row)

        self.axis_row = QHBoxLayout()
        self.axis_row.addWidget(QLabel(tr("trans.punch_axis_label")))
        self.axis_combo = QComboBox()
        self.axis_combo.addItem(tr("trans.punch_h"), "h")
        self.axis_combo.addItem(tr("trans.punch_v"), "v")
        self.axis_row.addWidget(self.axis_combo)
        self.axis_row.addStretch()
        custom_l.addLayout(self.axis_row)

        for w in (self.dur_spin, self.fo_spin, self.fh_spin, self.fi_spin, self.steps_spin,
                  self.ramp_spin, self.dir_combo, self.axis_combo):
            sig = w.valueChanged if hasattr(w, "valueChanged") else w.currentIndexChanged
            sig.connect(self._on_param_changed)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        custom_l.addWidget(sep2)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel(tr("trans.save_name_label")))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("trans.save_name_placeholder"))
        name_row.addWidget(self.name_edit, 1)
        custom_l.addLayout(name_row)
        name_hint = QLabel(tr("trans.save_name_hint"))
        name_hint.setWordWrap(True)
        name_hint.setObjectName("hint_text")
        custom_l.addWidget(name_hint)

        custom_l.addStretch()
        tabs.addTab(custom_tab, tr("trans.tab_custom"))
        self.tabs = tabs

                                
        right = QVBoxLayout()
        right.addWidget(QLabel(tr("trans.preview_label")))
        self.preview = _TransitionPreviewWidget()
        self.preview.set_base_pixmap(base_pixmap, rm=rm)
        self.preview.set_mask_resolver(mask_resolver)
        right.addWidget(self.preview)
        demo_note = QLabel(tr("trans.demo_note"))
        demo_note.setWordWrap(True)
        demo_note.setObjectName("hint_text")
        right.addWidget(demo_note)
        replay_btn = QPushButton(tr("trans.replay_button"))
        replay_btn.clicked.connect(self.preview.restart)
        right.addWidget(replay_btn)
        right.addStretch()
        right_wrap = QWidget()
        right_wrap.setLayout(right)

        body = QHBoxLayout()
        body.addWidget(tabs, 1)
        body.addWidget(right_wrap)
        outer.addLayout(body, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(tr("trans.cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton(tr("trans.save"))
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        outer.addLayout(btn_row)

        if existing_spec is not None and current_value not in BUILTIN_TRANSITIONS:
            self.tabs.setCurrentIndex(1)
            self._load_spec_into_custom(existing_spec)
            if current_value in self._custom:
                self.name_edit.setText(current_value)
        self._sync_visibility()
        self._on_param_changed()

    def _param_row(self, layout, label, lo, hi, default, is_int=False):
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        if is_int:
            spin = QSpinBox()
        else:
            spin = QDoubleSpinBox()
            spin.setDecimals(2)
            spin.setSingleStep(0.05)
        spin.setRange(lo, hi)
        spin.setValue(default)
        row.addWidget(spin)
        row.addStretch()
        layout.addLayout(row)
        return row, spin

    def _update_color_btn(self):
        self.color_btn.setStyleSheet(f"background:{self._fade_color}; border:1px solid #666;")

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._fade_color), self, tr("trans.fade_color_label"))
        if c.isValid():
            self._fade_color = c.name()
            self._update_color_btn()
            self._on_param_changed()

    def _browse_mask(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("trans.mask_browse"), "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not path:
            return
        self._mask_abs_path = path
        self.mask_path_lbl.setText(os.path.basename(path))
        self.preview.set_mask_resolver(lambda rel, p=path: p)
        if not self.name_edit.text().strip():
            base_dir = getattr(self._rm, 'base_dir', None) if self._rm else None
            hint = os.path.splitext(os.path.basename(path))[0]
            self.name_edit.setText(ctstore.suggest_name(base_dir, hint) if base_dir else hint)
        self._on_param_changed()

    def _current_kind(self) -> TransitionKind:
        return self.kind_combo.currentData()

    def _sync_visibility(self):
        kind = self._current_kind()
        self.dur_row_widgets_visible(kind not in (TransitionKind.FADE, TransitionKind.PUNCH))
        for row, visible in (
            (self.fo_row, kind == TransitionKind.FADE),
            (self.fh_row, kind == TransitionKind.FADE),
            (self.fi_row, kind == TransitionKind.FADE),
            (self.color_row, kind == TransitionKind.FADE),
            (self.steps_row, kind == TransitionKind.PIXELLATE),
            (self.mask_row, kind == TransitionKind.IMAGE_DISSOLVE),
            (self.ramp_row, kind == TransitionKind.IMAGE_DISSOLVE),
            (self.dir_row, kind in (TransitionKind.WIPE, TransitionKind.PUSH)),
            (self.axis_row, kind == TransitionKind.PUNCH),
        ):
            self._set_row_visible(row, visible)

    def dur_row_widgets_visible(self, visible: bool):
        self._set_row_visible(self.dur_row, visible)

    def _set_row_visible(self, row: QHBoxLayout, visible: bool):
        for i in range(row.count()):
            w = row.itemAt(i).widget()
            if w is not None:
                w.setVisible(visible)

    def _on_kind_changed(self):
        self._sync_visibility()
        self._on_param_changed()

    def _build_spec(self) -> TransitionSpec:
        kind = self._current_kind()
        spec = TransitionSpec(kind=kind)
        spec.duration = self.dur_spin.value()
        spec.fade_out = self.fo_spin.value()
        spec.fade_hold = self.fh_spin.value()
        spec.fade_in = self.fi_spin.value()
        spec.fade_color = self._fade_color
        spec.pixellate_steps = int(self.steps_spin.value())
        spec.mask_path = self._mask_abs_path or ""
        spec.ramp = int(self.ramp_spin.value())
        spec.direction = self.dir_combo.currentData() or "left"
        spec.punch_axis = self.axis_combo.currentData() or "h"
        return spec

    def _on_param_changed(self):
        self.preview.set_spec(self._build_spec())

    def _load_spec_into_custom(self, spec: TransitionSpec):
        i = self.kind_combo.findData(spec.kind)
        self.kind_combo.setCurrentIndex(max(0, i))
        self.dur_spin.setValue(spec.duration)
        self.fo_spin.setValue(spec.fade_out)
        self.fh_spin.setValue(spec.fade_hold)
        self.fi_spin.setValue(spec.fade_in)
        self._fade_color = spec.fade_color or "#000000"
        self._update_color_btn()
        self.steps_spin.setValue(spec.pixellate_steps)
        self.ramp_spin.setValue(spec.ramp)
        di = self.dir_combo.findData(spec.direction)
        self.dir_combo.setCurrentIndex(max(0, di))
        ai = self.axis_combo.findData(spec.punch_axis)
        self.axis_combo.setCurrentIndex(max(0, ai))
        if spec.mask_path and spec.mask_path not in ("__builtin_blinds__", "__builtin_squares__"):
            self.mask_path_lbl.setText(spec.mask_path)
            self._mask_rel_path = spec.mask_path
                                                                                
                                                                              
                                                                             
            self._mask_abs_path = (self._mask_resolver(spec.mask_path)
                                    if self._mask_resolver else spec.mask_path)

    def _on_preset_changed(self):
        name = self.preset_combo.currentData()
        if not name:
            return
        spec = BUILTIN_TRANSITIONS.get(name)
        if spec is None and name in self._custom:
            spec = trmod.parse_transition(self._custom[name])
        if spec is not None:
            self.preview.set_spec(spec)

    def _on_save(self):
        if self.tabs.currentIndex() == 0:
            name = self.preset_combo.currentData()
            self._result_text = name or ""
        else:
            spec = self._build_spec()
            mask_display = None
            if spec.kind == TransitionKind.IMAGE_DISSOLVE and self._mask_abs_path and self._mask_import_fn:
                mask_display = self._mask_import_fn(self._mask_abs_path)
            expr = trmod.spec_to_expr(spec, mask_display_path=mask_display)

                                                                              
                                                                          
                                                                      
            name = self.name_edit.text().strip()
            if self._rm is not None:
                base_dir = getattr(self._rm, 'base_dir', None)
                if not name:
                    hint = (os.path.splitext(os.path.basename(mask_display or ""))[0]
                            if spec.kind == TransitionKind.IMAGE_DISSOLVE and mask_display
                            else spec.kind.value)
                    name = ctstore.suggest_name(base_dir, hint)
                ctstore.save_custom_transition(base_dir, name, expr)
                self._result_text = name
            else:
                                                                             
                self._result_text = expr
        self.accept()

    def result_text(self) -> str:
        return self._result_text
