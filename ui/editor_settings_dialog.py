"""
Диалог «Настройки редактора» — горячие клавиши для частых операций
(добавление нод) и настройки автосохранения.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget, QWidget,
    QCheckBox, QSpinBox, QKeySequenceEdit
)
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import Qt

from core.hotkeys_store import HotkeyStore, ACTIONS
from core.app_settings import AppSettings


class EditorSettingsDialog(QDialog):
    def __init__(self, hotkey_store: HotkeyStore, app_settings: AppSettings, base_dir: str, parent=None):
        super().__init__(parent)
        self.hotkey_store = hotkey_store
        self.app_settings = app_settings
        self.base_dir = base_dir
        self.setWindowTitle("Настройки редактора")
        self.setMinimumSize(640, 520)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs, 1)

        hotkeys_tab = QWidget()
        tabs.addTab(hotkeys_tab, "⌨ Горячие клавиши")
        self._setup_hotkeys_tab(hotkeys_tab)

        autosave_tab = QWidget()
        tabs.addTab(autosave_tab, "💾 Автосохранение")
        self._setup_autosave_tab(autosave_tab)

        bottom = QHBoxLayout()
        bottom.addStretch()
        btn_close = QPushButton("Сохранить и закрыть")
        btn_close.setObjectName("btn_primary")
        btn_close.clicked.connect(self._save_and_close)
        bottom.addWidget(btn_close)
        layout.addLayout(bottom)

                                                                             

    def _setup_hotkeys_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)
        info = QLabel(
            "Клавиши для быстрого добавления нод нужного типа сразу после "
            "выбранной ноды в текущей сцене (без похода в комбобокс типа)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Действие", "Клавиша", ""])
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

            btn_reset = QPushButton("Сброс")
            btn_reset.clicked.connect(lambda _, aid=action_id: self._reset_key(aid))
            self.table.setCellWidget(row, 2, btn_reset)

        layout.addWidget(self.table, 1)

        btn_reset_all = QPushButton("Сбросить все клавиши к стандартным")
        btn_reset_all.clicked.connect(self._reset_all_keys)
        layout.addWidget(btn_reset_all)

    def _on_key_changed(self, action_id: str, edit: QKeySequenceEdit):
        seq = edit.keySequence().toString()
        conflict = self.hotkey_store.find_conflict(action_id, seq)
        if conflict:
            conflict_label = ACTIONS.get(conflict, (conflict,))[0]
            QMessageBox.warning(
                self, "Конфликт клавиш",
                f"Клавиша «{seq}» уже занята действием «{conflict_label}». "
                f"Выберите другую комбинацию."
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

        self.autosave_check = QCheckBox("Автоматически сохранять черновик проекта")
        self.autosave_check.setChecked(self.app_settings.autosave_enabled)
        layout.addWidget(self.autosave_check)

        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("Интервал автосохранения (секунд):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(30, 3600)
        self.interval_spin.setSingleStep(30)
        self.interval_spin.setValue(self.app_settings.autosave_interval_sec)
        interval_row.addWidget(self.interval_spin)
        interval_row.addStretch()
        layout.addLayout(interval_row)

        info = QLabel(
            "Автосохранение пишет черновик проекта в отдельный служебный файл "
            "(не поверх вашего .repj) каждые N секунд, если есть несохранённые "
            "изменения. Если редактор закроется аварийно (сбой/отключение "
            "питания), при следующем запуске будет предложено восстановить "
            "этот черновик. При обычном сохранении (Ctrl+S) черновик очищается."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(info)
        layout.addStretch()

    def _save_and_close(self):
        self.hotkey_store.save(self.base_dir)
        self.app_settings.autosave_enabled = self.autosave_check.isChecked()
        self.app_settings.autosave_interval_sec = self.interval_spin.value()
        self.app_settings.save(self.base_dir)
        self.accept()
