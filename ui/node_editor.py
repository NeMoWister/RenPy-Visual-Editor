"""
Панель редактирования ноды (правая панель)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QCheckBox, QDoubleSpinBox,
    QGroupBox, QScrollArea, QFrame, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.models import SceneNode, NodeType, ANCHOR_POSITIONS, NAMED_SPRITE_POSITIONS, nearest_anchor_name
from ui.resource_carousel import ResourceCarousel, FolderResourceCarousel, CharacterGroupPicker, CompositeSpriteCarousel
from ui.audio_preview import get_player as get_audio_player


TRANSITIONS = ["", "dissolve", "fade", "fade2", "fade3", "flash", "pixellate",
               "blinds", "squares", "wipeleft", "wiperight", "wipeup",
               "wipedown", "vpunch", "hpunch", "dspr"]

NODE_TYPES = [
    ("dialogue",     "💬 Диалог"),
    ("narration",    "📖 Нарратор"),
    ("scene",     "🎬 Сцена (scene)"),
    ("show_bg",   "🖼 Фон (show)"),
    ("show_cg",           "🎨 CG (show)"),
    ("show_sprite",  "👤 Показать спрайт"),
    ("hide_sprite",  "❌ Скрыть спрайт"),
    ("window",       "🪟 Текстовое окно (show/hide)"),
    ("with_transition", "✨ Эффект (with)"),
    ("play_music",        "🎵 Музыка"),
    ("stop_music",        "🔇 Стоп музыка"),
    ("play_sound",        "🔊 Звук"),
    ("play_ambience",     "🌬 Эмбиенс (play)"),
    ("stop_ambience",     "🌬 Эмбиенс (stop)"),
    ("label",        "🏷 Метка (label)"),
    ("jump",         "↪ Переход (jump)"),
    ("menu",         "📋 Меню выбора"),
    ("pause",        "⏸ Пауза"),
    ("return_",      "⏹ Return"),
    ("python",       "🐍 Python код"),
    ("raw",          "🧩 Необработанный код (импорт)"),
    ("custom",       "🧬 Пользовательская нода..."),
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
        QLineEdit:focus { border-color:#ff8c3d; }
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
        QComboBox:focus { border-color:#ff8c3d; }
        QComboBox QAbstractItemView {
            background:#2a2a2a; color:#fff; selection-background-color:#ff8c3d;
        }
    """)
    return cb


def _transition_combo(current_value: str = "") -> QComboBox:
    """Комбобокс переходов, который можно редактировать вручную — нужно,
    чтобы нестандартные переходы (свои define transform, специфичные для
    конкретной игры) не терялись при открытии узла, импортированного из
    .rpy, если их вдруг нет в списке TRANSITIONS."""
    cb = QComboBox()
    cb.addItems(TRANSITIONS)
    cb.setEditable(True)
    cb.setStyleSheet("""
        QComboBox {
            background:#2a2a2a; color:#fff; border:1px solid #444;
            border-radius:4px; padding:4px 28px 4px 6px; font-size:12px;
        }
        QComboBox:focus { border-color:#ff8c3d; }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 22px;
            border-left: 1px solid #555;
            border-radius: 0 4px 4px 0;
            background: #3a3a3a;
        }
        QComboBox::down-arrow {
            width: 10px; height: 10px;
            border-left: 2px solid #aaa;
            border-bottom: 2px solid #aaa;
            transform: rotate(-45deg);
        }
        QComboBox QAbstractItemView {
            background:#2a2a2a; color:#fff;
            selection-background-color:#ff8c3d;
            border: 1px solid #555;
        }
        QComboBox QLineEdit {
            background:#2a2a2a; color:#fff;
            border: none; padding: 0;
        }
    """)
    if current_value and current_value not in TRANSITIONS:
        cb.addItem(current_value)
    cb.setCurrentText(current_value)
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

    def __init__(self, text="", jump="", use_call=False, raw_body=""):
        super().__init__()
        self.setStyleSheet("QFrame { background:#252525; border-radius:4px; padding:2px; }")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 2, 4, 2)
        outer.setSpacing(2)

        row = QHBoxLayout()
        self.text_edit = _field("Текст варианта")
        self.text_edit.setText(text)
        self.text_edit.textChanged.connect(lambda *_: self.changed.emit())
        self.jump_edit = _field("метка (если jump/call)")
        self.jump_edit.setFixedWidth(150)
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

                                                                             
        body_toggle_row = QHBoxLayout()
        body_toggle_row.setContentsMargins(0, 2, 0, 0)
        self._body_toggle_btn = QPushButton("▶ Тело варианта (inline-сценарий)")
        self._body_toggle_btn.setFlat(True)
        self._body_toggle_btn.setStyleSheet(
            "QPushButton { color:#ff8c3d; font-size:11px; text-align:left; border:none; padding:0; }"
            "QPushButton:hover { color:#ffa020; }"
        )
        self._body_toggle_btn.clicked.connect(self._toggle_body)
        body_toggle_row.addWidget(self._body_toggle_btn)
        body_toggle_row.addStretch()
        outer.addLayout(body_toggle_row)

        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText(
            "Код варианта — будет вставлен как есть (scene, show, диалог, jump, ...)"
        )
        self.body_edit.setPlainText(raw_body)
        self.body_edit.setMinimumHeight(90)
        self.body_edit.setMaximumHeight(300)
        self.body_edit.setStyleSheet(
            "QTextEdit { background:#1e1e1e; color:#ddd; border:1px solid #444;"
            " border-radius:4px; padding:4px; font-family:monospace; font-size:11px; }"
            "QTextEdit:focus { border-color:#ff8c3d; }"
        )
        self.body_edit.textChanged.connect(lambda: self.changed.emit())
        outer.addWidget(self.body_edit)

                                                    
        self._body_visible = bool(raw_body and raw_body.strip())
        self.body_edit.setVisible(self._body_visible)
        self._body_toggle_btn.setText(
            "▼ Тело варианта (inline-сценарий)" if self._body_visible
            else "▶ Тело варианта (inline-сценарий)"
        )

    def _toggle_body(self):
        self._body_visible = not self._body_visible
        self.body_edit.setVisible(self._body_visible)
        self._body_toggle_btn.setText(
            "▼ Тело варианта (inline-сценарий)" if self._body_visible
            else "▶ Тело варианта (inline-сценарий)"
        )

    def get_use_call(self) -> bool:
        return self.call_check.isChecked()

    def get_raw_body(self) -> str:
        return self.body_edit.toPlainText()


class NodeEditor(QWidget):
    node_changed = pyqtSignal()                          

    def __init__(self, resource_manager=None, parent=None):
        super().__init__(parent)
        self.rm = resource_manager
        self.tags_store = None
        self.usage_store = None
        self.custom_template_store = None
                                                                       
                                                                      
                                                                            
                                                                            
                                                                             
                                                                               
        self.last_group_by_type: dict = {}
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
        asset_vars = {'bg': [], 'cg': [], 'sprites': [], 'music': [], 'sounds': [], 'ambience': []}
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
        name = nearest_anchor_name(xalign)
        idx = self.xalign_spin.findData(name)
        if idx < 0:
            return
        self.xalign_spin.blockSignals(True)
        self.xalign_spin.setCurrentIndex(idx)
        self.xalign_spin.blockSignals(False)

    def _build(self):
        self.setStyleSheet("background:#1e1e1e;")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        title = QLabel("Панель параметров")
        title.setStyleSheet("color:#ff8c3d; font-size:13px; font-weight:bold; padding:4px;")
        outer.addWidget(title)

                            
        type_row = QHBoxLayout()
        type_row.addWidget(_label("Тип ноды:"))
        self.type_combo = _combo([label for _, label in NODE_TYPES])
        self.type_combo.setToolTip("Тип ноды определяет, какая команда Ren'Py будет сгенерирована (реплика, показ фона, переход, пауза и т.д.)")
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
                background:#ff8c3d; color:#000; font-weight:bold;
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
        elif t in ("show_bg", "show_cg", "scene"):
            self._add_bg_fields(t)
        elif t == "show_sprite":
            self._add_sprite_fields()
        elif t == "hide_sprite":
            self._add_hide_fields()
        elif t == "window":
            self._add_window_fields()
        elif t == "with_transition":
            self._add_with_transition_fields()
        elif t in ("play_music", "play_sound", "play_ambience"):
            self._add_audio_fields(t)
        elif t in ("stop_music", "stop_ambience"):
            self._add_stop_audio_fields(t)
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
        elif t == "raw":
            self._add_raw_fields()
        elif t == "custom":
            self._add_custom_fields()

    def _insert(self, widget: QWidget):
        self.fields_layout.insertWidget(self.fields_layout.count() - 1, widget)

    def _add_dialogue_fields(self):
        n = self.node
        if self._node_type_value(n.node_type) == "dialogue":
            grp = QGroupBox("Персонаж")
            grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
            g = QVBoxLayout(grp)
            self.char_combo = _combo(["— нарратор —"] + [c.name for c in self.characters])
            self.char_combo.setToolTip("Кто говорит эту реплику. «— нарратор —» — реплика без персонажа (показывается без имени, обычно курсивом/по-другому в теме игры)")
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

        tag_row = QHBoxLayout()
        tag_row.setSpacing(3)

        def _tag_btn(label: str, tooltip: str, handler):
            btn = QPushButton(label)
            btn.setObjectName("btn_secondary")
            btn.setFixedHeight(24)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("QPushButton { padding:0 6px; font-size:11px; }")
            btn.clicked.connect(handler)
            tag_row.addWidget(btn)
            return btn

        _tag_btn("𝑖", "Курсив {i}...{/i}", lambda: self._wrap_selection_with_tag("i"))
        _tag_btn("𝐛", "Жирный {b}...{/b}", lambda: self._wrap_selection_with_tag("b"))
        _tag_btn("u̲", "Подчёркнутый {u}...{/u}", lambda: self._wrap_selection_with_tag("u"))
        _tag_btn("🤫", "Шёпот (уменьшенный, приглушённый курсив)", self._insert_whisper_tag)
        _tag_btn("A±", "Размер шрифта {size=+10}...{/size}", lambda: self._wrap_selection_with_tag("size=+10", "size"))
        _tag_btn("🎨", "Цвет текста {color=#ffcf40}...{/color}", self._insert_color_tag)
        _tag_btn("⏳w", "Пауза с ожиданием клика {w}", lambda: self._insert_at_cursor("{w}"))
        _tag_btn("⏭nw", "Продолжить без ожидания {nw}", lambda: self._insert_at_cursor("{nw}"))
        tag_row.addStretch()
        g2.addLayout(tag_row)

        self.text_edit = QTextEdit()
        self.text_edit.setToolTip("Текст реплики/повествования. Можно использовать теги Ren'Py ({i}, {b}, {color=...} и т.п.) — см. панель тегов выше.")
        self.text_edit.setPlaceholderText("Введите текст реплики...")
        self.text_edit.setText(n.text)
        self.text_edit.setMinimumHeight(80)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background:#2a2a2a; color:#fff; border:1px solid #444;
                border-radius:4px; padding:4px; font-size:12px;
            }
            QTextEdit:focus { border-color:#ff8c3d; }
        """)
        self.text_edit.textChanged.connect(lambda: self._apply())
        self.text_edit.textChanged.connect(self._update_length_hint)
        g2.addWidget(self.text_edit)

        self.length_hint_lbl = QLabel()
        self.length_hint_lbl.setStyleSheet("font-size:11px; padding:2px 0;")
        self.length_hint_lbl.setWordWrap(True)
        g2.addWidget(self.length_hint_lbl)
        self._update_length_hint()

        self._insert(grp2)

                                                                      
                                                                            
    DIALOGUE_LEN_OK = 200
    DIALOGUE_LEN_UGLY = 340

    def _wrap_selection_with_tag(self, open_inner: str, close_name: str = None):
        """Оборачивает выделенный текст в тег Ren'Py {open_inner}...{/close_name}.
        Если выделения нет — вставляет пустую пару тегов и ставит курсор внутрь."""
        close_name = close_name or open_inner
        cursor = self.text_edit.textCursor()
        open_tag, close_tag = "{%s}" % open_inner, "{/%s}" % close_name
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(open_tag + selected + close_tag)
        else:
            pos = cursor.position()
            cursor.insertText(open_tag + close_tag)
            cursor.setPosition(pos + len(open_tag))
            self.text_edit.setTextCursor(cursor)
        self.text_edit.setFocus()

    def _insert_whisper_tag(self):
        """«Шёпот» — не отдельный нативный тег Ren'Py, а комбинация уменьшенного
        приглушённого курсива: {size=-4}{alpha=0.75}{i}...{/i}{/alpha}{/size}."""
        cursor = self.text_edit.textCursor()
        open_tag = "{size=-4}{alpha=0.75}{i}"
        close_tag = "{/i}{/alpha}{/size}"
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(open_tag + selected + close_tag)
        else:
            pos = cursor.position()
            cursor.insertText(open_tag + close_tag)
            cursor.setPosition(pos + len(open_tag))
            self.text_edit.setTextCursor(cursor)
        self.text_edit.setFocus()

    def _insert_color_tag(self):
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor()
        if not color.isValid():
            return
        self._wrap_selection_with_tag(f"color={color.name()}", "color")

    def _insert_at_cursor(self, text: str):
        cursor = self.text_edit.textCursor()
        cursor.insertText(text)
        self.text_edit.setFocus()

    def _update_length_hint(self):
        if not hasattr(self, "length_hint_lbl"):
            return
        count = len(self.text_edit.toPlainText())
        if count <= self.DIALOGUE_LEN_OK:
            color = "#7ed957"
            msg = f"✓ {count} симв. — уместится в диалоговое окно нормально."
        elif count <= self.DIALOGUE_LEN_UGLY:
            color = "#ffb84d"
            msg = (f"⚠ {count} симв. — влезет, но может выглядеть некрасиво "
                   f"(мелкий текст/много строк). Стоит сократить.")
        else:
            color = "#ff6b6b"
            msg = (f"✕ {count} симв. — скорее всего НЕ влезет в стандартное "
                   f"диалоговое окно. Разбейте реплику на несколько.")
        self.length_hint_lbl.setStyleSheet(f"font-size:11px; padding:2px 0; color:{color};")
        self.length_hint_lbl.setText(msg)

    def _add_bg_fields(self, t: str):
        n = self.node
        cat = "cg" if t == "show_cg" else "bg"                                          
        label = "Выберите CG" if t == "show_cg" else "Выберите фон"
        current = n.cg_var if t == "show_cg" else n.bg_var

        grp = QGroupBox(label)
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)

        entries = self.rm.get(cat) if self.rm is not None else []
        last_group = self.last_group_by_type.get(t)
        self.bg_carousel = ResourceCarousel(
            thumb_size=160, tags_store=self.tags_store,
            initial_group_id=last_group, category=cat, usage_store=self.usage_store, rm=self.rm
        )
        self.bg_carousel.group_changed.connect(lambda gid: self._on_bg_group_changed(gid, t))
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
        self.trans_combo = _transition_combo(n.transition)
        self.trans_combo.setToolTip("Анимация перехода Ren'Py (with dissolve и т.п.). Пусто — мгновенная смена без анимации.")
        self.trans_combo.currentIndexChanged.connect(lambda *_: self._apply())
        g.addWidget(self.trans_combo)
        self._insert(grp)

    def _on_bg_group_changed(self, category_id, t: str):
        self.last_group_by_type[t] = category_id

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
            self.composite_sprite_carousel = CompositeSpriteCarousel(self.rm, thumb_size=160)
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
            self.sprite_carousel = FolderResourceCarousel(self.rm, category="sprites", thumb_size=160)
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

        g.addWidget(_label("Позиция на сцене (якорь):"))
        self.xalign_spin = QComboBox()
        for name, label in ANCHOR_POSITIONS:
            self.xalign_spin.addItem(label, name)
        current_name = nearest_anchor_name(n.xalign)
        idx = self.xalign_spin.findData(current_name)
        if idx >= 0:
            self.xalign_spin.setCurrentIndex(idx)
        self.xalign_spin.setStyleSheet("QComboBox { background:#2a2a2a; color:#fff; border:1px solid #444; border-radius:4px; padding:4px; }")
        self.xalign_spin.currentIndexChanged.connect(lambda *_: self._apply())
        g.addWidget(self.xalign_spin)

        g.addWidget(_label("Переход:"))
        self.sprite_trans_combo = _transition_combo(n.transition)
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
        self.hide_group_picker = CharacterGroupPicker(self.rm, category="sprites", thumb_size=160)
        self.hide_group_picker.set_resource_manager(self.rm, "sprites")
        if n.hide_group:
            self.hide_group_picker.select_folder(n.hide_group)
        self.hide_group_picker.selection_changed.connect(self._on_hide_group_selected)
        g.addWidget(self.hide_group_picker)

        sep = QLabel("— или выбрать конкретный спрайт —")
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep.setStyleSheet("color:#666; font-size:10px; padding:4px;")
        g.addWidget(sep)

        self.hide_carousel = FolderResourceCarousel(self.rm, category="sprites", thumb_size=160)
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

    def _add_window_fields(self):
        n = self.node
        grp = QGroupBox("Текстовое окно")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)

        g.addWidget(_label("Действие:"))
        self.window_action_combo = _combo(["show", "hide"])
        self.window_action_combo.setCurrentText(n.window_action or "show")
        self.window_action_combo.currentIndexChanged.connect(lambda *_: self._apply())
        g.addWidget(self.window_action_combo)

        g.addWidget(_label("Переход (необязательно):"))
        self.window_trans_combo = _transition_combo(n.transition)
        self.window_trans_combo.currentIndexChanged.connect(lambda *_: self._apply())
        g.addWidget(self.window_trans_combo)

        self._insert(grp)

    def _add_with_transition_fields(self):
        n = self.node
        grp = QGroupBox("Эффект (with)")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)

        hint = QLabel(
            "Самостоятельная инструкция \"with переход\" — применяет эффект ко "
            "всему экрану, не привязываясь к конкретному show/scene/hide "
            "(например, эффект тряски vpunch после реплики)."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#777; font-size:11px;")
        g.addWidget(hint)

        g.addWidget(_label("Переход:"))
        self.with_trans_combo = _transition_combo(n.transition)
        self.with_trans_combo.currentIndexChanged.connect(lambda *_: self._apply())
        g.addWidget(self.with_trans_combo)

        self._insert(grp)

    def _add_raw_fields(self):
        n = self.node
        grp = QGroupBox("Необработанный код (импортирован дословно)")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)

        hint = QLabel(
            "Этот блок не удалось распознать как одну из известных команд "
            "редактора при импорте .rpy — он сохранён дословно и будет "
            "воспроизведён в коде в точности как есть, без изменений."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#ff9955; font-size:11px;")
        g.addWidget(hint)

        self.raw_edit = QTextEdit()
        self.raw_edit.setPlainText(n.python_code)
        self.raw_edit.setMinimumHeight(120)
        self.raw_edit.setStyleSheet("""
            QTextEdit {
                background:#1c1c22; color:#ddd; border:1px solid #444;
                border-radius:4px; padding:4px; font-family:Consolas,monospace; font-size:11px;
            }
        """)
        self.raw_edit.textChanged.connect(lambda: self._apply())
        g.addWidget(self.raw_edit)

        self._insert(grp)

    def _add_custom_fields(self):
        n = self.node
        grp = QGroupBox("Пользовательская нода")
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)

        self.custom_param_widgets = {}
        templates = self.custom_template_store.templates if self.custom_template_store else []

        if not templates:
            empty = QLabel(
                "Пока нет ни одного шаблона пользовательской ноды. Создайте его в "
                "«Проект → Шаблоны пользовательских нод...», затем выберите здесь."
            )
            empty.setWordWrap(True)
            empty.setStyleSheet("color:#ff9955; font-size:11px;")
            g.addWidget(empty)
            self._insert(grp)
            return

        g.addWidget(_label("Шаблон:"))
        self.custom_template_combo = _combo([t.name for t in templates])
        ids = [t.template_id for t in templates]
        if n.custom_template_id in ids:
            self.custom_template_combo.setCurrentIndex(ids.index(n.custom_template_id))
        else:
            n.custom_template_id = ids[0]
            n.custom_params = templates[0].default_params()
        self.custom_template_combo.currentIndexChanged.connect(self._on_custom_template_changed)
        g.addWidget(self.custom_template_combo)

        current = self.custom_template_store.get(n.custom_template_id)
        if current and current.description:
            desc = QLabel(current.description)
            desc.setWordWrap(True)
            desc.setStyleSheet("color:#888; font-size:11px;")
            g.addWidget(desc)

        self.custom_params_box = QVBoxLayout()
        g.addLayout(self.custom_params_box)
        self._rebuild_custom_param_fields(current)

        self._insert(grp)

    def _rebuild_custom_param_fields(self, template):
        while self.custom_params_box.count():
            item = self.custom_params_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.custom_param_widgets = {}
        if not template:
            return
        n = self.node
        values = dict(template.default_params())
        values.update(n.custom_params or {})
        for p in template.params:
            row = QHBoxLayout()
            row.addWidget(_label((p.label or p.name) + ":"))
            if p.param_type == "bool":
                w = QCheckBox()
                w.setChecked(bool(values.get(p.name, p.default)))
                w.toggled.connect(lambda *_: self._apply())
            elif p.param_type in ("int", "float"):
                w = QLineEdit(str(values.get(p.name, p.default)))
                w.editingFinished.connect(self._apply)
            else:
                w = QLineEdit(str(values.get(p.name, p.default)))
                w.editingFinished.connect(self._apply)
            self.custom_param_widgets[p.name] = (w, p)
            row.addWidget(w)
            container = QWidget()
            container.setLayout(row)
            self.custom_params_box.addWidget(container)

    def _on_custom_template_changed(self, idx: int):
        templates = self.custom_template_store.templates if self.custom_template_store else []
        if 0 <= idx < len(templates):
            template = templates[idx]
            self.node.custom_template_id = template.template_id
            self.node.custom_params = template.default_params()
            self._rebuild_custom_param_fields(template)
            self._apply()

    def _add_audio_fields(self, t: str):
        n = self.node
        cat = {"play_music": "music", "play_sound": "sounds", "play_ambience": "ambience"}[t]
        title = {"play_music": "Аудио (музыка)", "play_sound": "Аудио (звук)",
                 "play_ambience": "Аудио (эмбиенс)"}[t]
        grp = QGroupBox(title)
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)
        vars_list = self.asset_vars.get(cat, [])
        g.addWidget(_label("Файл:"))

        combo_row = QHBoxLayout()
        self.audio_combo = _combo(vars_list)
        if n.audio_var in vars_list:
            self.audio_combo.setCurrentText(n.audio_var)
        combo_row.addWidget(self.audio_combo, 1)

        btn_play = QPushButton("▶️")
        btn_play.setToolTip(
            "Прослушать выбранный файл" +
            (" (с 1/5 от начала трека)" if cat == "music" else " (с начала)")
        )
        btn_play.setObjectName("btn_secondary")
        btn_play.setFixedWidth(48)
        btn_play.clicked.connect(self._play_audio_preview)
        combo_row.addWidget(btn_play)

        btn_stop = QPushButton("⏹️")
        btn_stop.setToolTip("Остановить прослушивание")
        btn_stop.setObjectName("btn_secondary")
        btn_stop.setFixedWidth(48)
        btn_stop.clicked.connect(lambda: get_audio_player().stop())
        combo_row.addWidget(btn_stop)

        g.addLayout(combo_row)

        if t == "play_music":
            self.loop_check = QCheckBox("Зациклить (loop)")
            self.loop_check.setChecked(n.audio_loop)
            self.loop_check.setStyleSheet("color:#ccc;")
            g.addWidget(self.loop_check)

        if t in ("play_music", "play_ambience"):
            fadein_attr = "fadein_spin"
            fadeout_attr = "ambience_fadeout_spin" if t == "play_ambience" else None
            value_fadein = n.music_fadein if t == "play_music" else n.ambience_fadein

            fadein_row = QHBoxLayout()
            fadein_row.addWidget(_label("Fade in (сек):"))
            self.fadein_spin = QDoubleSpinBox()
            self.fadein_spin.setRange(0.0, 60.0)
            self.fadein_spin.setSingleStep(0.5)
            self.fadein_spin.setDecimals(1)
            self.fadein_spin.setValue(value_fadein)
            self.fadein_spin.setToolTip("Плавное нарастание громкости в начале (fadein N)")
            self.fadein_spin.valueChanged.connect(lambda *_: self._apply())
            fadein_row.addWidget(self.fadein_spin)
            fadein_row.addStretch()
            g.addLayout(fadein_row)

        if t == "play_ambience":
            fadeout_row = QHBoxLayout()
            fadeout_row.addWidget(_label("Fade out (сек):"))
            self.ambience_fadeout_spin = QDoubleSpinBox()
            self.ambience_fadeout_spin.setRange(0.0, 60.0)
            self.ambience_fadeout_spin.setSingleStep(0.5)
            self.ambience_fadeout_spin.setDecimals(1)
            self.ambience_fadeout_spin.setValue(n.ambience_fadeout)
            self.ambience_fadeout_spin.valueChanged.connect(lambda *_: self._apply())
            fadeout_row.addWidget(self.ambience_fadeout_spin)
            fadeout_row.addStretch()
            g.addLayout(fadeout_row)

        self._insert(grp)

    def _add_stop_audio_fields(self, t: str):
        """stop_music / stop_ambience — только канал и опциональный fadeout."""
        n = self.node
        title = "Стоп музыка" if t == "stop_music" else "Стоп эмбиенс"
        grp = QGroupBox(title)
        grp.setStyleSheet("QGroupBox { color:#888; border:1px solid #333; border-radius:4px; margin-top:8px; padding-top:8px; }")
        g = QVBoxLayout(grp)

        fadeout_row = QHBoxLayout()
        fadeout_row.addWidget(_label("Fade out (сек):"))
        self.stop_fadeout_spin = QDoubleSpinBox()
        self.stop_fadeout_spin.setRange(0.0, 60.0)
        self.stop_fadeout_spin.setSingleStep(0.5)
        self.stop_fadeout_spin.setDecimals(1)
        self.stop_fadeout_spin.setValue(n.music_fadeout if t == "stop_music" else n.ambience_fadeout)
        self.stop_fadeout_spin.valueChanged.connect(lambda *_: self._apply())
        fadeout_row.addWidget(self.stop_fadeout_spin)
        fadeout_row.addStretch()
        g.addLayout(fadeout_row)

        self._insert(grp)

    def _play_audio_preview(self):
        var_name = self.audio_combo.currentText() if hasattr(self, "audio_combo") else ""
        if not var_name or self.rm is None:
            return
        entry = self.rm.find_by_var(var_name)
        if not entry:
            return
                                                                     
                                                                        
        is_music = self._node_type_value(self.node.node_type) == "play_music"
        get_audio_player().play(entry.abs_path, start_fraction=0.2 if is_music else 0.0)

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
        self.jump_edit.setToolTip("Имя label, на которую нужно перейти (jump). Должна существовать где-то в сценарии — иначе Ren'Py выдаст ошибку при запуске игры.")
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
        for text, jump, use_call, raw_body in n.normalized_menu_choices():
            self._add_choice_row(text, jump, use_call, raw_body)
        g.addWidget(self.choices_container)

        add_btn = QPushButton("+ Добавить вариант")
        add_btn.setStyleSheet("QPushButton { background:#333; color:#ff8c3d; border-radius:4px; padding:4px; }")
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

    def _add_choice_row(self, text="", jump="", use_call=False, raw_body=""):
        row = MenuChoiceRow(text, jump, use_call, raw_body)
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
        self.pause_spin.setToolTip("Длительность паузы в секундах. 0 — пауза до клика игрока (эквивалент голой команды pause).")
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
        elif t in ("show_bg", "show_cg", "scene"):
            selected = self.bg_carousel.get_selected()
            var = selected.var_name if selected else ""
            if t == "show_cg":
                self.node.cg_var = var
            else:
                                                                        
                                                                              
                self.node.bg_var = var
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
            anchor_name = self.xalign_spin.currentData()
            self.node.xalign = NAMED_SPRITE_POSITIONS[anchor_name].xalign if anchor_name else 0.5
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
        elif t in ("play_music", "play_sound", "play_ambience"):
            self.node.audio_var = self.audio_combo.currentText()
            if t == "play_music":
                self.node.audio_loop = self.loop_check.isChecked()
                self.node.music_fadein = self.fadein_spin.value()
            elif t == "play_ambience":
                self.node.ambience_fadein = self.fadein_spin.value()
                self.node.ambience_fadeout = self.ambience_fadeout_spin.value()
        elif t in ("stop_music", "stop_ambience"):
            if t == "stop_music":
                self.node.music_fadeout = self.stop_fadeout_spin.value()
            else:
                self.node.ambience_fadeout = self.stop_fadeout_spin.value()
        elif t == "window":
            self.node.window_action = self.window_action_combo.currentText()
            self.node.transition = self.window_trans_combo.currentText()
        elif t == "with_transition":
            self.node.transition = self.with_trans_combo.currentText()
        elif t == "label":
            self.node.label_name = self.label_edit.text().strip()
        elif t == "jump":
            self.node.jump_target = self.jump_edit.text().strip()
        elif t == "menu":
            self.node.menu_question = self.menu_q.text()
            self.node.menu_choices = [
                (r.text_edit.text(), r.jump_edit.text(), r.get_use_call(), r.get_raw_body())
                for r in self.choice_rows
            ]
        elif t == "pause":
            self.node.pause_duration = self.pause_spin.value()
        elif t == "python":
            self.node.python_code = self.py_edit.toPlainText()
        elif t == "raw":
            self.node.python_code = self.raw_edit.toPlainText()
        elif t == "custom":
            params = {}
            for name, (widget, pdef) in getattr(self, "custom_param_widgets", {}).items():
                if pdef.param_type == "bool":
                    raw_value = widget.isChecked()
                else:
                    raw_value = widget.text()
                params[name] = pdef.coerce(raw_value)
            self.node.custom_params = params

        self.node_changed.emit()
