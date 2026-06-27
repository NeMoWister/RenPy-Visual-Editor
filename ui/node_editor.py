"""
Панель редактирования ноды (правая панель)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QCheckBox, QDoubleSpinBox,
    QGroupBox, QScrollArea, QFrame, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.models import SceneNode, NodeType
from ui.resource_carousel import ResourceCarousel, FolderResourceCarousel, CharacterGroupPicker, CompositeSpriteCarousel


TRANSITIONS = ["", "dspr", "dissolve", "fade", "blinds", "squares",
               "wipeleft", "wiperight", "wipeup", "wipedown", "pixellate"]

NODE_TYPES = [
    ("dialogue",     "💬 Диалог"),
    ("narration",    "📖 Нарратор"),
    ("show_bg",   "🖼 Фон (scene)"),
    ("show_cg",           "🎨 CG (show)"),
    ("show_sprite",  "👤 Показать спрайт"),
    ("hide_sprite",  "❌ Скрыть спрайт"),
    ("play_music",        "🎵 Музыка"),
    ("play_sound",        "🔊 Звук"),
    ("label",        "🏷 Метка (label)"),
    ("jump",         "↪ Переход (jump)"),
    ("menu",         "📋 Меню выбора"),
    ("pause",        "⏸ Пауза"),
    ("return_",      "⏹ Return"),
    ("python",       "🐍 Python код"),
]


def _label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color:#aaa; font-size:11px;")
    return lbl


def _field(placeholder: str = "") -> QLineEdit:
    f = QLineEdit()
    f.setPlaceholderText(placeholder)
    f.setStyleSheet("""
        QLineEdit {
            background:#2a2a2a; color:#fff; border:1px solid #444;
            border-radius:4px; padding:4px 6px; font-size:12px;
        }
        QLineEdit:focus { border-color:#ff8c00; }
    """)
    return f


def _combo(items: list) -> QComboBox:
    cb = QComboBox()
    cb.addItems(items)
    cb.setStyleSheet("""
        QComboBox {
            background:#2a2a2a; color:#fff; border:1px solid #444;
            border-radius:4px; padding:4px 6px; font-size:12px;
        }
        QComboBox:focus { border-color:#ff8c00; }
        QComboBox QAbstractItemView {
            background:#2a2a2a; color:#fff; selection-background-color:#ff8c00;
        }
    """)
    return cb


CALL_VS_JUMP_TOOLTIP = (
    "По умолчанию переход на метку делается через jump.\n\n"
    "Разница между jump и call важна, если внутри метки что-то присваивается "
    "и затем стоит return:\n"
    "• jump — просто переходит на метку и забывает, откуда пришёл. Если в той "
    "метке встретится return, Ren'Py решит, что сценарий закончился, и игра "
    "выйдет в главное меню.\n"
    "• call — переходит на метку, но запоминает место вызова. После return "
    "игра вернётся обратно, на следующую строку после этого варианта меню.\n\n"
    "Включите галочку «call», если метка должна вернуть игрока сюда же после "
    "return, а не выкинуть в главное меню."
)


class MenuChoiceRow(QFrame):
    removed = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, text="", jump="", use_call=False):
        super().__init__()
        self.setStyleSheet("QFrame { background:#252525; border-radius:4px; padding:2px; }")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 2, 4, 2)
        outer.setSpacing(2)

        row = QHBoxLayout()
        self.text_edit = _field("Текст варианта")
        self.text_edit.setText(text)
        self.text_edit.textChanged.connect(lambda *_: self.changed.emit())
        self.jump_edit = _field("метка")
        self.jump_edit.setFixedWidth(120)
        self.jump_edit.setText(jump)
        self.jump_edit.textChanged.connect(lambda *_: self.changed.emit())
        btn = QPushButton("✕")
        btn.setFixedSize(24, 24)
        btn.setStyleSheet("QPushButton { background:#c0392b; color:#fff; border-radius:4px; }")
        btn.clicked.connect(self.removed.emit)
        row.addWidget(self.text_edit)
        row.addWidget(_label("→"))
        row.addWidget(self.jump_edit)
        row.addWidget(btn)
        outer.addLayout(row)

        call_row = QHBoxLayout()
        call_row.setContentsMargins(0, 0, 0, 0)
        self.call_check = QCheckBox("call (вернуться сюда после return, а не в jump)")
        self.call_check.setChecked(bool(use_call))
        self.call_check.setStyleSheet("QCheckBox { color:#aaa; font-size:11px; }")
        self.call_check.setToolTip(CALL_VS_JUMP_TOOLTIP)
        self.call_check.stateChanged.connect(lambda *_: self.changed.emit())
        call_row.addWidget(self.call_check)
        call_row.addStretch()
        help_lbl = QLabel("ⓘ")
        help_lbl.setStyleSheet("color:#888; font-weight:bold;")
        help_lbl.setToolTip(CALL_VS_JUMP_TOOLTIP)
        call_row.addWidget(help_lbl)
        outer.addLayout(call_row)

    def get_use_call(self) -> bool:
        return self.call_check.isChecked()


class NodeEditor(QWidget):
    node_changed = pyqtSignal()

    def __init__(self, resource_manager=None, parent=None):
        super().__init__(parent)
        self.rm = resource_manager
        self.node: SceneNode | None = None
        self.characters: list = []
        self.asset_vars: dict = {}
        self.choice_rows: list[MenuChoiceRow] = []
        self._build()
        self.refresh_resources()

    def _node_type_value(self, node_type):
        return node_type.value if hasattr(node_type, 'value') else node_type

    def set_characters(self, characters: list):
        self.characters = characters
        if self.node:
            self._rebuild_fields()

    def refresh_resources(self):
        asset_vars = {'bg': [], 'cg': [], 'sprites': [], 'music': [], 'sounds': []}
        if self.rm is not None:
            try:
                for cat in asset_vars:
                    asset_vars[cat] = [e.var_name for e in self.rm.get(cat)]
            except Exception:
                pass
        self.asset_vars = asset_vars
        if self.node:
            self._rebuild_fields()

    def load_node(self, node: SceneNode):
        self.set_node(node, self.characters, self.asset_vars)

    def clear_node(self):
        """Сбрасывает панель, когда нет валидного узла для редактирования
        (например, сцена пуста или была удалена)."""
        self.node = None
        self._clear_fields()

    def sync_xalign_from_preview(self, xalign: float):
        """Обновляет поле xalign в UI, если сейчас открыт узел 'показать спрайт',
        без повторного запуска цепочки _apply -> сигналы (избегаем циклов)."""
        if not self.node or self._node_type_value(self.node.node_type) != "show_sprite":
            return
        if not hasattr(self, "xalign_spin"):
            return
        self.xalign_spin.blockSignals(True)
        self.xalign_spin.setValue(xalign)
        self.xalign_spin.blockSignals(False)

    def _build(self):
        self.setStyleSheet("background:#1e1e1e;")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        title = QLabel("Панель параметров")
        title.setStyleSheet("color:#ff8c00; font-size:13px; font-weight:bold; padding:4px;")
        outer.addWidget(title)

        type_row = QHBoxLayout()
        type_row.addWidget(_label("Тип ноды:"))
        self.type_combo = _combo([label for _, label in NODE_TYPES])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_row.addWidget(self.type_combo)
        outer.addLayout(type_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:#1e1e1e; }")
        self.fields_widget = QWidget()
        self.fields_widget.setStyleSheet("background:#1e1e1e;")
        self.fields_layout = QVBoxLayout(self.fields_widget)
        self.fields_layout.setContentsMargins(0, 4, 0, 4)
        self.fields_layout.setSpacing(6)
        self.fields_layout.addStretch()
        scroll.setWidget(self.fields_widget)
        outer.addWidget(scroll)

        apply_btn = QPushButton("✔ Применить изменения")
        apply_btn.setStyleSheet("""
            QPushButton {
                background:#ff8c00; color:#000; font-weight:bold;
                border-radius:6px; padding:8px; font-size:12px;
            }
            QPushButton:hover { background:#ffa020; }
        """)
        apply_btn.clicked.connect(self._apply)
        outer.addWidget(apply_btn)


    def set_node(self, node: SceneNode, characters: list, asset_vars: dict):
        self.node = node
        self.characters = characters
        self.asset_vars = asset_vars
        type_keys = [k for k, _ in NODE_TYPES]
        current = self._node_type_value(node.node_type)
        idx = type_keys.index(current) if current in type_keys else 0
        self.type_combo.blockSignals(True)
        self.type_combo.setCurrentIndex(idx)
        self.type_combo.blockSignals(False)
        self._rebuild_fields()


    def _on_type_changed(self, idx: int):
        if self.node:
            mapping = {
                'background': NodeType.SHOW_BG,
                'cg': NodeType.SHOW_CG,
                'music': NodeType.PLAY_MUSIC,
                'sound': NodeType.PLAY_SOUND,
            }
            value = [k for k, _ in NODE_TYPES][idx]
            self.node.node_type = mapping.get(value, NodeType(value))
        self._rebuild_fields()

    def _clear_fields(self):
        self.choice_rows.clear()
        while self.fields_layout.count() > 1:
            item = self.fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _rebuild_fields(self):
        self._clear_fields()
        if not self.node:
            return
        t = self._node_type_value(self.node.node_type)

        if t in ("dialogue", "narration"):
            self._add_dialogue_fields()
        elif t in ("show_bg", "show_cg"):
            self._add_bg_fields(t)
        elif t == "show_sprite":
            self._add_sprite_fields()
        elif t == "hide_sprite":
            self._add_hide_fields()
        elif t in ("play_music", "play_sound"):
            self._add_audio_fields(t)
        elif t == "label":
            self._add_label_fields()
        elif t == "jump":
            self._add_jump_fields()
        elif t == "menu":
            self._add_menu_fields()
        elif t == "pause":
            self._add_pause_fields()
        elif t == "return_":
            self._add_return_fields()
        elif t == "python":
            self._add_python_fields()

    def _insert(self, widget: QWidget):
        self.fields_layout.insertWidget(self.fields_layout.count() - 1, widget)

    def _add_dialogue_fields(self):
        n = self.node
        if self._node_type_value(n.node_type) == "dialogue":
            grp = QGroupBox("Персонаж")
            grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
            g = QVBoxLayout(grp)
            self.char_combo = _combo(["— нарратор —"] + [c.variable for c in self.characters])
            if n.character_var:
                vars = [c.variable for c in self.characters]
                if n.character_var in vars:
                    self.char_combo.setCurrentIndex(vars.index(n.character_var) + 1)
            self.char_combo.currentIndexChanged.connect(lambda *_: self._apply())
            g.addWidget(self.char_combo)
            self._insert(grp)

        grp2 = QGroupBox("Текст реплики")
        grp2.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g2 = QVBoxLayout(grp2)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Введите текст реплики...")
        self.text_edit.setText(n.text)
        self.text_edit.setMinimumHeight(80)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background:#2a2a2a; color:#fff; border:1px solid #444;
                border-radius:4px; padding:4px; font-size:12px;
            }
            QTextEdit:focus { border-color:#ff8c00; }
        """)
        self.text_edit.textChanged.connect(lambda: self._apply())
        g2.addWidget(self.text_edit)
        self._insert(grp2)

    def _add_bg_fields(self, t: str):
        n = self.node
        cat = "bg" if t == "show_bg" else "cg"
        label = "Выберите фон" if t == "show_bg" else "Выберите CG"
        current = n.bg_var if t == "show_bg" else n.cg_var

        grp = QGroupBox(label)
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)

        entries = self.rm.get(cat) if self.rm is not None else []
        self.bg_carousel = ResourceCarousel(thumb_size=84)
        self.bg_carousel.set_entries(entries)
        if current:
            self.bg_carousel.select_by_var(current)
        self.bg_carousel.selection_changed.connect(lambda *_: self._apply())
        g.addWidget(self.bg_carousel)

        if not entries:
            empty = QLabel(f"Нет файлов в resources/{cat}/. Добавьте изображения и нажмите F5.")
            empty.setStyleSheet("color:#777; font-size:11px;")
            empty.setWordWrap(True)
            g.addWidget(empty)

        g.addWidget(_label("Переход:"))
        self.trans_combo = _combo(TRANSITIONS)
        self.trans_combo.setCurrentText(n.transition)
        self.trans_combo.currentIndexChanged.connect(lambda *_: self._apply())
        g.addWidget(self.trans_combo)
        self._insert(grp)

    def _add_sprite_fields(self):
        n = self.node
        grp = QGroupBox("Спрайт")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)

        has_composite = bool(self.rm and self.rm.composite_sprites)
        entries = self.rm.get("sprites") if self.rm is not None else []

        self.composite_sprite_carousel = None
        self.sprite_carousel = None

        if has_composite:
            composite_label = QLabel("Составные спрайты (sprites.rpy):")
            composite_label.setStyleSheet("color:#888; font-size:11px;")
            g.addWidget(composite_label)
            self.composite_sprite_carousel = CompositeSpriteCarousel(self.rm, thumb_size=84)
            self.composite_sprite_carousel.set_resource_manager(self.rm)
            if n.sprite_var:
                self.composite_sprite_carousel.select_by_name(n.sprite_var)
            self.composite_sprite_carousel.selection_changed.connect(self._on_composite_sprite_selected)
            g.addWidget(self.composite_sprite_carousel)

        if entries or not has_composite:
            if has_composite:
                plain_label = QLabel("Обычные спрайты (отдельные файлы):")
                plain_label.setStyleSheet("color:#888; font-size:11px; padding-top:6px;")
                g.addWidget(plain_label)
            self.sprite_carousel = FolderResourceCarousel(self.rm, category="sprites", thumb_size=84)
            self.sprite_carousel.set_resource_manager(self.rm, "sprites")
            if n.sprite_var:
                self.sprite_carousel.select_by_var(n.sprite_var)
            self.sprite_carousel.selection_changed.connect(self._on_plain_sprite_selected)
            g.addWidget(self.sprite_carousel)

        if not entries and not has_composite:
            empty = QLabel("Нет файлов в resources/sprites/. Разложите спрайты по папкам персонажей "
                            "(например resources/sprites/us/normal/), либо добавьте sprites.rpy "
                            "с составными спрайтами, и нажмите F5.")
            empty.setStyleSheet("color:#777; font-size:11px;")
            empty.setWordWrap(True)
            g.addWidget(empty)

        g.addWidget(_label("Позиция xalign (0.0 = лево, 0.5 = центр, 1.0 = право):"))
        self.xalign_spin = QDoubleSpinBox()
        self.xalign_spin.setRange(0.0, 1.0)
        self.xalign_spin.setSingleStep(0.05)
        self.xalign_spin.setValue(n.xalign)
        self.xalign_spin.setStyleSheet("QDoubleSpinBox { background:#2a2a2a; color:#fff; border:1px solid #444; border-radius:4px; padding:4px; }")
        self.xalign_spin.valueChanged.connect(lambda *_: self._apply())
        g.addWidget(self.xalign_spin)

        g.addWidget(_label("Переход:"))
        self.sprite_trans_combo = _combo(TRANSITIONS)
        self.sprite_trans_combo.setCurrentText(n.transition)
        self.sprite_trans_combo.currentIndexChanged.connect(lambda *_: self._apply())
        g.addWidget(self.sprite_trans_combo)
        hint = QLabel("Если несколько спрайтов показываются друг за другом с одним и тем же "
                       "переходом, при экспорте они объединяются в один блок \"show ... \\n show ... \\n with ...\".")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#666; font-size:10px; padding-top:2px;")
        g.addWidget(hint)

        self._insert(grp)

    def _on_composite_sprite_selected(self, sprite):
        if self.sprite_carousel is not None:
            self.sprite_carousel.selected_entry = None
            self.sprite_carousel._refresh_view()
        self._apply()

    def _on_plain_sprite_selected(self, *_):
        if self.composite_sprite_carousel is not None:
            self.composite_sprite_carousel.selected_sprite = None
            self.composite_sprite_carousel._refresh_view()
        self._apply()

    def _add_hide_fields(self):
        n = self.node
        grp = QGroupBox("Скрыть спрайт")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)

        g.addWidget(_label("Скрыть персонажа целиком (клик на папку — без захода внутрь):"))
        self.hide_group_picker = CharacterGroupPicker(self.rm, category="sprites", thumb_size=72)
        self.hide_group_picker.set_resource_manager(self.rm, "sprites")
        if n.hide_group:
            self.hide_group_picker.select_folder(n.hide_group)
        self.hide_group_picker.selection_changed.connect(self._on_hide_group_selected)
        g.addWidget(self.hide_group_picker)

        sep = QLabel("— или выбрать конкретный спрайт —")
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep.setStyleSheet("color:#666; font-size:10px; padding:4px;")
        g.addWidget(sep)

        self.hide_carousel = FolderResourceCarousel(self.rm, category="sprites", thumb_size=72)
        self.hide_carousel.set_resource_manager(self.rm, "sprites")
        if n.hide_var:
            self.hide_carousel.select_by_var(n.hide_var)
        self.hide_carousel.selection_changed.connect(self._on_hide_entry_selected)
        g.addWidget(self.hide_carousel)
        self._insert(grp)

    def _on_hide_group_selected(self, folder_name: str):
        if hasattr(self, "hide_carousel"):
            self.hide_carousel.selected_entry = None
            self.hide_carousel._refresh_view()
        self._apply()

    def _on_hide_entry_selected(self, *_):
        if hasattr(self, "hide_group_picker"):
            self.hide_group_picker.selected_folder = ""
            for card in self.hide_group_picker.cards:
                card.set_selected(False)
        self._apply()

    def _add_audio_fields(self, t: str):
        n = self.node
        cat = "music" if t == "play_music" else "sounds"
        grp = QGroupBox("Аудио")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)
        vars_list = self.asset_vars.get(cat, [])
        g.addWidget(_label("Файл:"))
        self.audio_combo = _combo(vars_list)
        if n.audio_var in vars_list:
            self.audio_combo.setCurrentText(n.audio_var)
        g.addWidget(self.audio_combo)
        if t == "play_music":
            self.loop_check = QCheckBox("Зациклить (loop)")
            self.loop_check.setChecked(n.audio_loop)
            self.loop_check.setStyleSheet("color:#ccc;")
            g.addWidget(self.loop_check)
        self._insert(grp)

    def _add_label_fields(self):
        n = self.node
        grp = QGroupBox("Метка")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)
        g.addWidget(_label("Имя метки:"))
        self.label_edit = _field("start, intro_scene, ...")
        self.label_edit.setText(n.label_name)
        g.addWidget(self.label_edit)
        self._insert(grp)

    def _add_jump_fields(self):
        n = self.node
        grp = QGroupBox("Переход")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)
        g.addWidget(_label("Цель перехода:"))
        self.jump_edit = _field("имя метки")
        self.jump_edit.setText(n.jump_target)
        g.addWidget(self.jump_edit)
        self._insert(grp)

    def _add_menu_fields(self):
        n = self.node
        grp = QGroupBox("Меню выбора")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)
        g.addWidget(_label("Вопрос/фраза перед меню:"))
        self.menu_q = _field("Необязательно")
        self.menu_q.setText(n.menu_question)
        self.menu_q.textChanged.connect(lambda *_: self._apply())
        g.addWidget(self.menu_q)

        g.addWidget(_label("Варианты ответов:"))
        self.choices_container = QWidget()
        self.choices_layout = QVBoxLayout(self.choices_container)
        self.choices_layout.setContentsMargins(0, 0, 0, 0)
        self.choices_layout.setSpacing(4)
        for text, jump, use_call in n.normalized_menu_choices():
            self._add_choice_row(text, jump, use_call)
        g.addWidget(self.choices_container)

        add_btn = QPushButton("+ Добавить вариант")
        add_btn.setStyleSheet("QPushButton { background:#333; color:#ff8c00; border-radius:4px; padding:4px; }")
        add_btn.clicked.connect(lambda: self._add_choice_row())
        g.addWidget(add_btn)

        info = QLabel(
            "По умолчанию переход на метку — jump. Включайте «call» у варианта, "
            "если после return в этой метке игрок должен вернуться обратно в меню, "
            "а не вылететь в главное меню (так ведёт себя jump + return)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#666; font-size:10px; padding-top:4px;")
        g.addWidget(info)

        self._insert(grp)

    def _add_choice_row(self, text="", jump="", use_call=False):
        row = MenuChoiceRow(text, jump, use_call)
        self.choice_rows.append(row)
        row.removed.connect(lambda: self._remove_choice(row))
        row.changed.connect(lambda *_: self._apply())
        self.choices_layout.addWidget(row)
        self._apply()

    def _remove_choice(self, row: MenuChoiceRow):
        self.choice_rows.remove(row)
        row.deleteLater()
        self._apply()

    def _add_python_fields(self):
        n = self.node
        grp = QGroupBox("Python код ($ prefix)")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)
        self.py_edit = QTextEdit()
        self.py_edit.setPlaceholderText("score += 1\nflag = True")
        self.py_edit.setText(n.python_code)
        self.py_edit.setMinimumHeight(100)
        self.py_edit.setStyleSheet("""
            QTextEdit {
                background:#1a1a2e; color:#7ec8e3; border:1px solid #444;
                font-family:monospace; font-size:12px; border-radius:4px; padding:4px;
            }
        """)
        g.addWidget(self.py_edit)
        self._insert(grp)

    def _add_pause_fields(self):
        n = self.node
        grp = QGroupBox("Пауза")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)
        g.addWidget(_label("Длительность в секундах (0 — ждать клика игрока):"))
        self.pause_spin = QDoubleSpinBox()
        self.pause_spin.setRange(0.0, 600.0)
        self.pause_spin.setSingleStep(0.5)
        self.pause_spin.setDecimals(1)
        self.pause_spin.setValue(n.pause_duration)
        self.pause_spin.setStyleSheet("QDoubleSpinBox { background:#2a2a2a; color:#fff; border:1px solid #444; border-radius:4px; padding:4px; }")
        self.pause_spin.valueChanged.connect(lambda *_: self._apply())
        g.addWidget(self.pause_spin)
        hint = QLabel("0 секунд — pause без числа: сцена ждёт клика игрока, "
                       "как обычная реплика без текста. Больше 0 — pause N: "
                       "ждёт указанное время и продолжает само.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#666; font-size:10px; padding-top:2px;")
        g.addWidget(hint)
        self._insert(grp)

    def _add_return_fields(self):
        grp = QGroupBox("Return")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)
        hint = QLabel(
            "Эта нода просто вставляет return в сценарий, без параметров.\n\n"
            "Если до этого места дошли через jump — Ren'Py решит, что сценарий "
            "закончился, и игра выйдет в главное меню.\n"
            "Если дошли через call (например, из варианта меню с галочкой "
            "«call») — игра вернётся обратно сразу после места вызова."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#999; font-size:11px; padding:4px;")
        g.addWidget(hint)
        self._insert(grp)

    def _apply(self):
        if not self.node:
            return
        t = self._node_type_value(self.node.node_type)

        if t == "dialogue":
            idx = self.char_combo.currentIndex()
            self.node.character_var = self.characters[idx - 1].variable if idx > 0 else ""
            self.node.text = self.text_edit.toPlainText()
        elif t == "narration":
            self.node.text = self.text_edit.toPlainText()
        elif t in ("show_bg", "show_cg"):
            selected = self.bg_carousel.get_selected()
            var = selected.var_name if selected else ""
            if t == "show_bg":
                self.node.bg_var = var
            else:
                self.node.cg_var = var
            self.node.transition = self.trans_combo.currentText()
        elif t == "show_sprite":
            composite_selected = self.composite_sprite_carousel.get_selected() if self.composite_sprite_carousel else None
            plain_selected = self.sprite_carousel.get_selected() if self.sprite_carousel else None
            if composite_selected is not None:
                self.node.sprite_var = composite_selected.full_name
            elif plain_selected is not None:
                self.node.sprite_var = plain_selected.var_name
            else:
                self.node.sprite_var = ""
            self.node.xalign = self.xalign_spin.value()
            self.node.transition = self.sprite_trans_combo.currentText()
        elif t == "hide_sprite":
            group = self.hide_group_picker.get_selected() if hasattr(self, "hide_group_picker") else ""
            if group:
                self.node.hide_group = group
                self.node.sprite_tag = None
            else:
                selected = self.hide_carousel.get_selected()
                self.node.hide_var = selected.var_name if selected else ""
                self.node.hide_group = None
        elif t in ("play_music", "play_sound"):
            self.node.audio_var = self.audio_combo.currentText()
            if t == "play_music":
                self.node.audio_loop = self.loop_check.isChecked()
        elif t == "label":
            self.node.label_name = self.label_edit.text().strip()
        elif t == "jump":
            self.node.jump_target = self.jump_edit.text().strip()
        elif t == "menu":
            self.node.menu_question = self.menu_q.text()
            self.node.menu_choices = [
                (r.text_edit.text(), r.jump_edit.text(), r.get_use_call())
                for r in self.choice_rows
            ]
        elif t == "pause":
            self.node.pause_duration = self.pause_spin.value()
        elif t == "python":
            self.node.python_code = self.py_edit.toPlainText()

        self.node_changed.emit()
