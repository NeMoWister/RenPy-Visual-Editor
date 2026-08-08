"""
Диалог «Шаблоны генерации кода» - свой стиль отступов, комментариев и
построчных Jinja2-шаблонов для каждого типа ноды, с живым предпросмотром.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTextEdit,
    QPushButton, QSpinBox, QLineEdit, QSplitter, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt

from core.code_templates import (
    CodeTemplateStore, DEFAULT_TEMPLATES, TEMPLATE_VARS_HELP,
    NODE_TYPE_LABELS, JINJA2_AVAILABLE,
)
from core.i18n import tr

                                                           
_SAMPLE_CONTEXT = {
    "dialogue": {"pad": "    ", "character_var": "alesya", "text": "Привет, как дела?"},
    "narration": {"pad": "    ", "text": "Прошло несколько часов."},
    "show_bg": {"pad": "    ", "bg_var": "room_day", "transition": "dissolve"},
    "scene": {"pad": "    ", "bg_var": "room_day", "transition": "dissolve"},
    "show_cg": {"pad": "    ", "cg_var": "cg_beach_01", "transition": "fade"},
    "hide_cg": {"pad": "    ", "cg_var": "cg_beach_01"},
    "play_music": {"pad": "    ", "music_var": "theme", "music_fadeout": 0, "music_fadeout_fmt": "0",
                    "music_fadein": 2, "music_fadein_fmt": "2"},
    "stop_music": {"pad": "    ", "music_fadeout": 1, "music_fadeout_fmt": "1"},
    "play_sound": {"pad": "    ", "sound_var": "door_open"},
    "play_ambience": {"pad": "    ", "ambience_var": "rain", "ambience_fadein": 1.5, "ambience_fadein_fmt": "1.5",
                       "ambience_fadeout": 0, "ambience_fadeout_fmt": "0"},
    "stop_ambience": {"pad": "    ", "ambience_fadeout": 1, "ambience_fadeout_fmt": "1"},
    "label": {"label_name": "chapter_1"},
    "jump": {"pad": "    ", "jump_target": "chapter_2"},
    "pause": {"pad": "    ", "pause_duration": 1.5},
    "return_": {"pad": "    "},
    "comment": {"pad": "    ", "comment_text": "TODO: доработать эту сцену"},
    "python": {"pad": "    ", "python_code": "renpy.notify('Привет')"},
    "menu_choice": {"pad": "        ", "choice_text": "Пойти домой"},
}


class CodeTemplatesDialog(QDialog):
    def __init__(self, store: CodeTemplateStore, base_dir: str, parent=None):
        super().__init__(parent)
        self.store = store
        self.base_dir = base_dir
        self.setWindowTitle(tr("code_templates.title"))
        self.setMinimumSize(760, 560)
        self._setup_ui()
        self._load_settings()
        self._select_node_type(0)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        if not JINJA2_AVAILABLE:
            warn = QLabel(tr("code_templates.no_jinja2"))
            warn.setWordWrap(True)
            warn.setObjectName("warning_banner")
            warn.setStyleSheet("padding:6px;")
            layout.addWidget(warn)

        settings_row = QHBoxLayout()
        settings_row.addWidget(QLabel(tr("code_templates.indent")))
        self.indent_unit_combo = QComboBox()
        self.indent_unit_combo.addItems([tr("code_templates.spaces"), tr("code_templates.tab")])
        self.indent_unit_combo.currentIndexChanged.connect(self._on_settings_changed)
        settings_row.addWidget(self.indent_unit_combo)
        settings_row.addWidget(QLabel(tr("code_templates.width")))
        self.indent_width_spin = QSpinBox()
        self.indent_width_spin.setRange(1, 8)
        self.indent_width_spin.valueChanged.connect(self._on_settings_changed)
        settings_row.addWidget(self.indent_width_spin)
        settings_row.addWidget(QLabel(tr("code_templates.comment_prefix")))
        self.comment_prefix_edit = QLineEdit()
        self.comment_prefix_edit.setFixedWidth(50)
        self.comment_prefix_edit.textChanged.connect(self._on_settings_changed)
        settings_row.addWidget(self.comment_prefix_edit)
        settings_row.addStretch()
        layout.addLayout(settings_row)

        split = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.addWidget(QLabel(tr("code_templates.node_type")))
        self.node_type_combo = QComboBox()
        for key in DEFAULT_TEMPLATES:
            label = NODE_TYPE_LABELS.get(key, key)
            marker = " ●" if self.store.is_customized(key) else ""
            self.node_type_combo.addItem(label + marker, key)
        self.node_type_combo.currentIndexChanged.connect(self._on_node_type_changed)
        left_l.addWidget(self.node_type_combo)

        self.vars_lbl = QLabel()
        self.vars_lbl.setWordWrap(True)
        self.vars_lbl.setObjectName("hint_text")
        left_l.addWidget(self.vars_lbl)

        left_l.addWidget(QLabel(tr("code_templates.jinja_template")))
        self.template_edit = QTextEdit()
        self.template_edit.setStyleSheet("font-family: monospace; font-size:12px;")
        self.template_edit.textChanged.connect(self._update_preview)
        left_l.addWidget(self.template_edit, 1)

        btn_row = QHBoxLayout()
        btn_reset = QPushButton(tr("code_templates.reset_default"))
        btn_reset.clicked.connect(self._reset_current)
        btn_row.addWidget(btn_reset)
        btn_row.addStretch()
        left_l.addLayout(btn_row)

        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.addWidget(QLabel(tr("code_templates.preview_label")))
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setObjectName("code_box")
        self.preview_edit.setStyleSheet("font-size:12px;")
        right_l.addWidget(self.preview_edit, 1)

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([420, 340])
        layout.addWidget(split, 1)

        bottom = QHBoxLayout()
        bottom.addStretch()
        btn_close = QPushButton(tr("code_templates.save_close"))
        btn_close.setObjectName("btn_primary")
        btn_close.clicked.connect(self._save_and_close)
        bottom.addWidget(btn_close)
        layout.addLayout(bottom)

    def _load_settings(self):
        self.indent_unit_combo.blockSignals(True)
        self.indent_unit_combo.setCurrentIndex(1 if self.store.indent_unit == "tab" else 0)
        self.indent_unit_combo.blockSignals(False)
        self.indent_width_spin.blockSignals(True)
        self.indent_width_spin.setValue(self.store.indent_width)
        self.indent_width_spin.blockSignals(False)
        self.comment_prefix_edit.blockSignals(True)
        self.comment_prefix_edit.setText(self.store.comment_prefix)
        self.comment_prefix_edit.blockSignals(False)

    def _on_settings_changed(self):
        self.store.indent_unit = "tab" if self.indent_unit_combo.currentIndex() == 1 else "spaces"
        self.store.indent_width = self.indent_width_spin.value()
        self.store.comment_prefix = self.comment_prefix_edit.text() or "#"
        self._update_preview()

    def _current_key(self) -> str:
        return self.node_type_combo.currentData()

    def _select_node_type(self, index: int):
        self._prev_key = None
        self.node_type_combo.setCurrentIndex(index)
        self._on_node_type_changed(index)

    def _on_node_type_changed(self, _index: int):
        prev_key = getattr(self, "_prev_key", None)
        if prev_key:
            self.store.set_template_text(prev_key, self.template_edit.toPlainText())
        key = self._current_key()
        self._prev_key = key
        if not key:
            return
        self.vars_lbl.setText(tr("code_templates.available_vars", vars=TEMPLATE_VARS_HELP.get(key, '')))
        self.template_edit.blockSignals(True)
        self.template_edit.setPlainText(self.store.get_template_text(key))
        self.template_edit.blockSignals(False)
        self._update_preview()

    def _reset_current(self):
        key = self._current_key()
        if not key:
            return
        self.template_edit.setPlainText(DEFAULT_TEMPLATES.get(key, ""))

    def _update_preview(self):
        key = self._current_key()
        if not key:
            return
        text = self.template_edit.toPlainText()
        sample = dict(_SAMPLE_CONTEXT.get(key, {}))
        sample.setdefault("comment_prefix", self.comment_prefix_edit.text() or "#")

        if not JINJA2_AVAILABLE:
            self.preview_edit.setPlainText(tr("code_templates.preview_unavailable"))
            return

        import jinja2
        try:
            rendered = jinja2.Template(text, undefined=jinja2.Undefined).render(**sample)
            self.preview_edit.setObjectName("code_box")
            self.preview_edit.setStyleSheet("font-size:12px;")
            self.preview_edit.setPlainText(rendered)
        except Exception as e:
            self.preview_edit.setObjectName("error_mono")
            self.preview_edit.setStyleSheet("font-size:12px;")
            self.preview_edit.setPlainText(tr("code_templates.template_error", error=e))

    def _save_and_close(self):
        key = self._current_key()
        if key:
            self.store.set_template_text(key, self.template_edit.toPlainText())
        self._on_settings_changed()
        self.store.save(self.base_dir)
        self.accept()

    def closeEvent(self, event):
        key = self._current_key()
        if key:
            self.store.set_template_text(key, self.template_edit.toPlainText())
        self.store.save(self.base_dir)
        super().closeEvent(event)
