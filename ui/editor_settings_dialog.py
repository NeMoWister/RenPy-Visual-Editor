"""
Диалог «Настройки редактора» - горячие клавиши для частых операций
(добавление нод) и настройки автосохранения.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget, QWidget,
    QCheckBox, QSpinBox, QKeySequenceEdit, QRadioButton, QButtonGroup, QGroupBox,
    QComboBox, QApplication
)
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import Qt

from core.hotkeys_store import HotkeyStore, ACTIONS
from core.app_settings import AppSettings
from core.i18n import tr, available_languages, language_display_name, get_language
from ui.theme import theme_manager, QFLUENT_AVAILABLE, fade_in_widget


class EditorSettingsDialog(QDialog):
    def __init__(self, hotkey_store: HotkeyStore, app_settings: AppSettings, base_dir: str, parent=None):
        super().__init__(parent)
        self.hotkey_store = hotkey_store
        self.app_settings = app_settings
        self.base_dir = base_dir
        self.setWindowTitle(tr("editor_settings.title"))
                                                     
        from ui.theme import fit_window_to_screen
        fit_window_to_screen(self, 960, 780, min_w=760, min_h=560)
        self._setup_ui()
        fade_in_widget(self, duration=220)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs, 1)

        hotkeys_tab = QWidget()
        tabs.addTab(hotkeys_tab, tr("editor_settings.tab.hotkeys"))
        self._setup_hotkeys_tab(hotkeys_tab)

        autosave_tab = QWidget()
        tabs.addTab(autosave_tab, tr("editor_settings.tab.autosave"))
        self._setup_autosave_tab(autosave_tab)

        codegen_tab = QWidget()
        tabs.addTab(codegen_tab, tr("editor_settings.tab.codegen"))
        self._setup_codegen_tab(codegen_tab)

        language_tab = QWidget()
        tabs.addTab(language_tab, tr("settings.tab.language"))
        self._setup_language_tab(language_tab)

        appearance_tab = QWidget()
        tabs.addTab(appearance_tab, tr("settings.tab.appearance"))
        self._setup_appearance_tab(appearance_tab)

        bottom = QHBoxLayout()
        bottom.addStretch()
        btn_close = QPushButton(tr("editor_settings.save_close"))
        btn_close.setObjectName("btn_primary")
        btn_close.clicked.connect(self._save_and_close)
        bottom.addWidget(btn_close)
        layout.addLayout(bottom)

                                                                             

    def _setup_hotkeys_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)
        info = QLabel(tr("editor_settings.hotkeys.info"))
        info.setWordWrap(True)
        info.setObjectName("hint_text")
        layout.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([tr("editor_settings.hotkeys.col_action"), tr("editor_settings.hotkeys.col_key"), ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.horizontalHeader().setMinimumSectionSize(120)
        self.table.setRowCount(len(ACTIONS))

        self._key_edits = {}
        for row, (action_id, (label, _default)) in enumerate(ACTIONS.items()):
            name_item = QTableWidgetItem(label)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            edit = QKeySequenceEdit(QKeySequence(self.hotkey_store.get(action_id)))
            edit.editingFinished.connect(lambda aid=action_id, e=edit: self._on_key_changed(aid, e))
            self.table.setCellWidget(row, 1, edit)
            self._key_edits[action_id] = edit

            btn_reset = QPushButton(tr("editor_settings.hotkeys.reset"))
            btn_reset.clicked.connect(lambda _, aid=action_id: self._reset_key(aid))
            self.table.setCellWidget(row, 2, btn_reset)

        layout.addWidget(self.table, 1)

        btn_reset_all = QPushButton(tr("editor_settings.hotkeys.reset_all"))
        btn_reset_all.clicked.connect(self._reset_all_keys)
        layout.addWidget(btn_reset_all)

    def _on_key_changed(self, action_id: str, edit: QKeySequenceEdit):
        seq = edit.keySequence().toString()
        conflict = self.hotkey_store.find_conflict(action_id, seq)
        if conflict:
            conflict_label = ACTIONS.get(conflict, (conflict,))[0]
            QMessageBox.warning(
                self, tr("editor_settings.hotkeys.conflict_title"),
                tr("editor_settings.hotkeys.conflict_text", key=seq, action=conflict_label)
            )
            edit.setKeySequence(QKeySequence(self.hotkey_store.get(action_id)))
            return
        self.hotkey_store.set(action_id, seq)

    def _reset_key(self, action_id: str):
        self.hotkey_store.reset(action_id)
        self._key_edits[action_id].setKeySequence(QKeySequence(self.hotkey_store.get(action_id)))

    def _reset_all_keys(self):
        self.hotkey_store.reset_all()
        for action_id, edit in self._key_edits.items():
            edit.setKeySequence(QKeySequence(self.hotkey_store.get(action_id)))

                                                                         

    def _setup_autosave_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)

        self.autosave_check = QCheckBox(tr("editor_settings.autosave.checkbox"))
        self.autosave_check.setChecked(self.app_settings.autosave_enabled)
        layout.addWidget(self.autosave_check)

        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel(tr("editor_settings.autosave.interval_label")))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(30, 3600)
        self.interval_spin.setSingleStep(30)
        self.interval_spin.setValue(self.app_settings.autosave_interval_sec)
        interval_row.addWidget(self.interval_spin)
        interval_row.addStretch()
        layout.addLayout(interval_row)

        info = QLabel(tr("editor_settings.autosave.info"))
        info.setWordWrap(True)
        info.setObjectName("hint_text")
        layout.addWidget(info)
        layout.addStretch()

    def _setup_codegen_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)

        box = QGroupBox(tr("editor_settings.codegen.group"))
        bl = QVBoxLayout(box)
        self.nvl_style_group = QButtonGroup(box)

        self.nvl_style_character_rb = QRadioButton(
            tr("editor_settings.codegen.character_mode")
        )
        self.nvl_style_function_rb = QRadioButton(
            tr("editor_settings.codegen.function_mode")
        )
        self.nvl_style_group.addButton(self.nvl_style_character_rb, 0)
        self.nvl_style_group.addButton(self.nvl_style_function_rb, 1)
        if self.app_settings.nvl_codegen_style == "function":
            self.nvl_style_function_rb.setChecked(True)
        else:
            self.nvl_style_character_rb.setChecked(True)
        bl.addWidget(self.nvl_style_character_rb)

        char_info = QLabel(tr("editor_settings.codegen.character_info"))
        char_info.setWordWrap(True)
        char_info.setObjectName("hint_text")
        char_info.setStyleSheet("margin-left:20px;")
        bl.addWidget(char_info)

        bl.addWidget(self.nvl_style_function_rb)
        fn_info = QLabel(tr("editor_settings.codegen.function_info"))
        fn_info.setWordWrap(True)
        fn_info.setObjectName("hint_text")
        fn_info.setStyleSheet("margin-left:20px;")
        bl.addWidget(fn_info)

        layout.addWidget(box)
        layout.addStretch()

    def _setup_language_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)

        row = QHBoxLayout()
        row.addWidget(QLabel(tr("settings.language.label")))
        self.language_combo = QComboBox()
        self._language_codes = available_languages()
        for code in self._language_codes:
            self.language_combo.addItem(language_display_name(code), code)
        current = self.app_settings.language or get_language()
        if current in self._language_codes:
            self.language_combo.setCurrentIndex(self._language_codes.index(current))
        row.addWidget(self.language_combo)
        row.addStretch()
        layout.addLayout(row)

        info = QLabel(tr("settings.language.info"))
        info.setWordWrap(True)
        info.setObjectName("hint_text")
        layout.addWidget(info)
        layout.addStretch()

    def _setup_appearance_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)

        box = QGroupBox(tr("settings.tab.appearance"))
        bl = QVBoxLayout(box)

        row = QHBoxLayout()
        row.addWidget(QLabel(tr("settings.appearance.theme_label")))
        self.theme_combo = QComboBox()
        self._theme_ids = []
        current_id = self.app_settings.theme or theme_manager.current_id
        for tokens in theme_manager.available():
            self.theme_combo.addItem(tokens.display_name, tokens.id)
            self._theme_ids.append(tokens.id)
        if current_id in self._theme_ids:
            self.theme_combo.setCurrentIndex(self._theme_ids.index(current_id))
        self.theme_combo.currentIndexChanged.connect(self._on_theme_preview)
        row.addWidget(self.theme_combo)
        row.addStretch()
        bl.addLayout(row)

        info = QLabel(tr("settings.appearance.info"))
        info.setWordWrap(True)
        info.setObjectName("hint_text")
        bl.addWidget(info)

        if not QFLUENT_AVAILABLE:
            fluent_info = QLabel(tr("settings.appearance.fluent_missing"))
            fluent_info.setWordWrap(True)
            fluent_info.setObjectName("accent_caption")
            fluent_info.setStyleSheet("font-size:11px; font-weight:normal;")
            bl.addWidget(fluent_info)

        layout.addWidget(box)
        layout.addStretch()

    def _on_theme_preview(self, _index: int):
        """Тема применяется сразу же, чтобы пользователь видел результат,
        не закрывая диалог. Сохраняется на диск только по кнопке
        "Сохранить и закрыть".""" 
        theme_id = self.theme_combo.currentData()
        app = QApplication.instance()
        if app is not None and theme_id:
            theme_manager.apply(app, theme_id, animate_widget=self.window())

    def _save_and_close(self):
        self.hotkey_store.save(self.base_dir)
        self.app_settings.autosave_enabled = self.autosave_check.isChecked()
        self.app_settings.autosave_interval_sec = self.interval_spin.value()
        self.app_settings.nvl_codegen_style = (
            "function" if self.nvl_style_function_rb.isChecked() else "character"
        )
        self.app_settings.language = self.language_combo.currentData()
        self.app_settings.theme = self.theme_combo.currentData() or self.app_settings.theme
        self.app_settings.save(self.base_dir)
        self.accept()

    def reject(self):
                                                                            
                                                                          
                                                                           
        app = QApplication.instance()
        if app is not None:
            theme_manager.apply(app, self.app_settings.theme)
        super().reject()
