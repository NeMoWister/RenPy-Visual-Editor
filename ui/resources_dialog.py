                       
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QDialogButtonBox, QGroupBox, QHeaderView, QMessageBox, QCheckBox,
    QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.resource_manager import ResourceManager
from core.tags_store import TagsStore
from core.resource_usage_store import ResourceUsageStore
from core.resource_usage_scanner import scan_project_usage
from ui.tags_dialog import TagPickerDialog
from ui.resource_usage_dialog import ResourceUsageDialog

TAGGABLE_CATEGORIES = {"bg", "cg"}
AUDIO_CATEGORIES = {"music", "sounds", "ambience"}


class ResourcesConfigDialog(QDialog):
    navigate_requested = pyqtSignal(str, list, str)                                     

    def __init__(self, resource_manager: ResourceManager, tags_store: TagsStore = None,
                 base_dir: str = "", parent=None, usage_store: ResourceUsageStore = None,
                 project=None):
        super().__init__(parent)
        self.rm = resource_manager
        self.tags_store = tags_store
        self.base_dir = base_dir
        self.usage_store = usage_store
        self.project = project
        self._usage_index = scan_project_usage(project) if project is not None else {}
        self._volume_spins = {}                              
        self.setWindowTitle("Настройки ресурсов")
        self.setMinimumSize(760, 500)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        path_group = QGroupBox("Путь к папке ресурсов")
        pg = QHBoxLayout(path_group)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("resources")
        pg.addWidget(self.path_edit, 1)
        btn_browse = QPushButton("📁 Обзор")
        btn_browse.clicked.connect(self._browse_path)
        pg.addWidget(btn_browse)
        layout.addWidget(path_group)

        info = QLabel(
            "Структура: resources/default/... и resources/custom/...\n"
            "Внутри каждой - bg/  cg/  sprites/  music/  sounds/ (одинаковая структура в обеих).\n"
            "Разница: объявления (image/define) генерируются ТОЛЬКО для ресурсов из custom/ - "
            "default/ считается уже объявленным где-то ещё и не дублируется в коде.\n"
            "Спрайты можно раскладывать по подпапкам персонажей и вариаций, например:\n"
            "resources/custom/sprites/us/normal/smile.png\n"
            "Имена переменных генерируются из имён файлов (и пути подпапки). Ниже можно задать свои."
        )
        info.setStyleSheet("color: #888; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        if self.usage_store is not None:
            self.fav_recent_check = QCheckBox("Показывать «Избранное» и «Недавние» вверху карусели ресурсов")
            self.fav_recent_check.setChecked(self.usage_store.enabled)
            self.fav_recent_check.setStyleSheet("color:#ccc;")
            self.fav_recent_check.toggled.connect(self._on_fav_recent_toggled)
            layout.addWidget(self.fav_recent_check)

        og = QGroupBox("Переопределения имён, теги и использование")
        og_l = QVBoxLayout(og)
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Файл", "Источник", "Авто-переменная", "Своё имя", "Своя переменная",
            "Теги", "Использование", "Громкость"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        og_l.addWidget(self.table)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить переопределения")
        save_btn.clicked.connect(self._save_overrides)
        btn_row.addWidget(save_btn)
        btn_row.addStretch()
        export_btn = QPushButton("⬆ Экспорт в файл...")
        export_btn.setToolTip("Сохранить набор переопределённых имён в отдельный JSON-файл, "
                               "чтобы перенести в другой проект или сделать резервную копию.")
        export_btn.clicked.connect(self._export_overrides)
        btn_row.addWidget(export_btn)
        import_btn = QPushButton("⬇ Импорт из файла...")
        import_btn.setToolTip("Загрузить переопределённые имена из файла, ранее сохранённого "
                               "через «Экспорт в файл».")
        import_btn.clicked.connect(self._import_overrides)
        btn_row.addWidget(import_btn)
        reset_btn = QPushButton("🗑 Сбросить переопределения")
        reset_btn.setToolTip("Полностью удалить все свои имена/переменные - ресурсы вернутся "
                              "к автоматически сгенерированным именам.")
        reset_btn.setObjectName("btn_secondary")
        reset_btn.clicked.connect(self._reset_overrides)
        btn_row.addWidget(reset_btn)
        og_l.addLayout(btn_row)
        layout.addWidget(og)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        self.path_edit.setText(self.rm.config.resources_path)
        self.table.setRowCount(0)
        self._volume_spins = {}
        for entries in self.rm.resources.values():
            for e in entries:
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col, text in enumerate([e.rel_path, e.source, e.var_name]):
                    item = QTableWidgetItem(text)
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    item.setForeground(Qt.GlobalColor.gray)
                    self.table.setItem(row, col, item)
                override = self.rm.config.overrides.get(e.rel_path)
                self.table.setItem(row, 3, QTableWidgetItem(override.custom_name if override else ""))
                self.table.setItem(row, 4, QTableWidgetItem(override.custom_var if override else ""))

                if self.tags_store is not None and e.category in TAGGABLE_CATEGORIES:
                    self.table.setCellWidget(row, 5, self._make_tags_button(e.var_name, e.display_name))
                else:
                    self.table.setItem(row, 5, self._placeholder_item())

                self.table.setCellWidget(row, 6, self._make_usage_button(e.var_name, e.display_name))

                if e.category in AUDIO_CATEGORIES:
                    spin = QDoubleSpinBox()
                    spin.setRange(0.0, 1.0)
                    spin.setSingleStep(0.05)
                    spin.setDecimals(2)
                    current = self.rm.get_volume(e.rel_path)
                    spin.setValue(current if current is not None else 1.0)
                    spin.setToolTip(
                        "Громкость по умолчанию для этого трека/канала (0.0–1.0).\n"
                        "Если оставить 1.00 - параметр volume не попадёт в сгенерированный код."
                    )
                    self.table.setCellWidget(row, 7, spin)
                    self._volume_spins[row] = (e.rel_path, spin)
                else:
                    self.table.setItem(row, 7, self._placeholder_item())

    def _placeholder_item(self) -> QTableWidgetItem:
        placeholder = QTableWidgetItem("-")
        placeholder.setFlags(Qt.ItemFlag.ItemIsEnabled)
        placeholder.setForeground(Qt.GlobalColor.darkGray)
        placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return placeholder

    def _make_usage_button(self, var_name: str, display_name: str) -> QPushButton:
        count = len(self._usage_index.get(var_name, []))
        btn = QPushButton(f"🔍 {count}" if count else "🔍 0")
        btn.setObjectName("btn_secondary")
        btn.setToolTip("Показать все места использования этого ресурса и перейти к ноде")
        if self.project is None:
            btn.setEnabled(False)
            btn.setToolTip("Недоступно: проект не передан в диалог")

        def on_click():
            refs = self._usage_index.get(var_name, [])
            dlg = ResourceUsageDialog(var_name, display_name, refs, self)
            dlg.navigate_requested.connect(self._on_usage_navigate)
            dlg.exec()

        btn.clicked.connect(on_click)
        return btn

    def _on_usage_navigate(self, scene_id: str, branch_path: list, node_id: str):
                                                                                
                                                                                 
        self.navigate_requested.emit(scene_id, branch_path, node_id)
        self.accept()

    def _make_tags_button(self, var_name: str, display_name: str) -> QPushButton:
        def label():
            keys = self.tags_store.get_tags_for(var_name)
            return f"🏷 {len(keys)}" if keys else "🏷 Теги..."

        btn = QPushButton(label())
        btn.setObjectName("btn_secondary")

        def on_click():
            dlg = TagPickerDialog(self.tags_store, self.base_dir, var_name, display_name, self)
            if dlg.exec():
                btn.setText(label())

        btn.clicked.connect(on_click)
        return btn

    def _browse_path(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите папку ресурсов")
        if d:
            self.path_edit.setText(d)

    def _on_fav_recent_toggled(self, checked: bool):
        if self.usage_store is not None:
            self.usage_store.enabled = checked
            self.usage_store.save(self.base_dir)

    def _save_overrides(self):
        for row in range(self.table.rowCount()):
            rel = self.table.item(row, 0).text()
            name = self.table.item(row, 3).text().strip()
            var = self.table.item(row, 4).text().strip()
            if name or var:
                self.rm.set_override(rel, name, var)
            if row in self._volume_spins:
                spin_rel, spin = self._volume_spins[row]
                value = round(spin.value(), 2)
                self.rm.set_volume(spin_rel, None if abs(value - 1.0) < 1e-6 else value)
        QMessageBox.information(self, "Готово", "Переопределения сохранены")

    def _export_overrides(self):
                                                                      
                                                                                
        for row in range(self.table.rowCount()):
            rel = self.table.item(row, 0).text()
            name = self.table.item(row, 3).text().strip()
            var = self.table.item(row, 4).text().strip()
            if name or var:
                self.rm.set_override(rel, name, var)
            if row in self._volume_spins:
                spin_rel, spin = self._volume_spins[row]
                value = round(spin.value(), 2)
                self.rm.set_volume(spin_rel, None if abs(value - 1.0) < 1e-6 else value)

        if not self.rm.config.overrides:
            QMessageBox.information(self, "Нечего экспортировать",
                                     "Список переопределений пуст - нет ни одного "
                                     "своего имени или переменной.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт переопределений", "resource_overrides.json",
            "JSON (*.json);;Все файлы (*)"
        )
        if not path:
            return
        try:
            self.rm.export_overrides(path)
            QMessageBox.information(self, "Готово",
                                     f"Экспортировано {len(self.rm.config.overrides)} переопределений в:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", str(e))

    def _import_overrides(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт переопределений", "",
            "JSON (*.json);;Все файлы (*)"
        )
        if not path:
            return

        reply = QMessageBox.question(
            self, "Как объединить?",
            "Добавить импортированные переопределения к текущим "
            "(совпадающие файлы будут перезаписаны)?\n\n"
            "Да - добавить/обновить.\nНет - полностью заменить текущий список.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return
        merge = reply == QMessageBox.StandardButton.Yes

        try:
            count = self.rm.import_overrides(path, merge=merge)
            self.rm.save_config()
            self.rm.scan()                                                                          
            self._load_data()
            QMessageBox.information(self, "Готово", f"Импортировано {count} переопределений.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка импорта", str(e))

    def _reset_overrides(self):
        if not self.rm.config.overrides:
            QMessageBox.information(self, "Нечего сбрасывать", "Список переопределений уже пуст.")
            return
        reply = QMessageBox.question(
            self, "Сбросить переопределения?",
            f"Удалить все {len(self.rm.config.overrides)} переопределённых имён/переменных? "
            "Ресурсы вернутся к автоматически сгенерированным именам.\n\n"
            "Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.rm.config.overrides.clear()
        self.rm.save_config()
        self.rm.scan()
        self._load_data()
        QMessageBox.information(self, "Готово", "Все переопределения сброшены.")

    def _on_ok(self):
        new_path = self.path_edit.text().strip()
        if new_path != self.rm.config.resources_path:
            self.rm.config.resources_path = new_path
            self.rm.save_config()
        self._save_overrides()
        self.accept()
