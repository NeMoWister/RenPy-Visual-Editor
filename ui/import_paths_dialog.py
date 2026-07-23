                       
"""
Диалог импорта имён ресурсов, персонажей и музыки из существующих .rpy
файлов проекта (например, из старого сценария игры) — чтобы переменные,
которые редактор использует в сгенерированном коде, совпадали с теми,
что уже объявлены в реальном проекте Ren'Py.
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QCheckBox, QTabWidget,
    QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from core.rpy_path_import import (
    parse_image_and_define_paths, parse_characters, parse_music_list,
    build_import_report, apply_import_report, ImportReport,
)


class ImportPathsDialog(QDialog):
    characters_selected = pyqtSignal(list)                                                
    paths_applied = pyqtSignal()                                                        

    def __init__(self, resource_manager, parent=None):
        super().__init__(parent)
        self.rm = resource_manager
        self.report: ImportReport = ImportReport()
        self.setWindowTitle("Импорт путей из .rpy")
        self.setMinimumSize(820, 560)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        hint = QLabel(
            "Выберите один или несколько .rpy файлов существующего проекта Ren'Py "
            "(например, определения ресурсов или весь сценарий). Редактор найдёт "
            "там простые присвоения вида image/define = \"путь\", определения "
            "персонажей Character(...) и словарь music_list, сопоставит пути с "
            "файлами в resources/ и предложит переименовать переменные ресурсов "
            "так, как они уже названы в вашем проекте."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#999; font-size:11px;")
        layout.addWidget(hint)

        btn_row = QHBoxLayout()
        btn_files = QPushButton("📄 Выбрать .rpy файлы...")
        btn_files.clicked.connect(self._pick_files)
        btn_row.addWidget(btn_files)
        btn_folder = QPushButton("📁 Выбрать папку (рекурсивно)...")
        btn_folder.setObjectName("btn_secondary")
        btn_folder.clicked.connect(self._pick_folder)
        btn_row.addWidget(btn_folder)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.status_lbl = QLabel("Файлы не выбраны.")
        self.status_lbl.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(self.status_lbl)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.plan_table = QTableWidget()
        self.plan_table.setColumnCount(6)
        self.plan_table.setHorizontalHeaderLabels(
            ["✓", "Категория", "Путь", "Было", "Будет", "Строка"])
        self.plan_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.plan_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.plan_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.plan_table, "Переименования (0)")

        self.unmatched_table = QTableWidget()
        self.unmatched_table.setColumnCount(3)
        self.unmatched_table.setHorizontalHeaderLabels(["Имя в .rpy", "Путь", "Строка"])
        self.unmatched_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.unmatched_table, "Не найдено на диске (0)")

        self.chars_table = QTableWidget()
        self.chars_table.setColumnCount(4)
        self.chars_table.setHorizontalHeaderLabels(["✓", "Переменная", "Имя", "Цвет"])
        self.chars_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.chars_table, "Персонажи (0)")

        btn_bottom = QHBoxLayout()
        btn_cancel = QPushButton("Закрыть")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_bottom.addWidget(btn_cancel)
        btn_bottom.addStretch()
        self.btn_apply = QPushButton("✓ Применить отмеченное")
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self._apply)
        btn_bottom.addWidget(self.btn_apply)
        layout.addLayout(btn_bottom)

                                                                          

    def _pick_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Выберите .rpy файлы", "", "Ren'Py script (*.rpy)")
        if paths:
            self._process_files(paths)

    def _pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с .rpy файлами")
        if not folder:
            return
        found = []
        for dirpath, _dirnames, filenames in os.walk(folder):
            for fn in filenames:
                if fn.lower().endswith('.rpy'):
                    found.append(os.path.join(dirpath, fn))
        if not found:
            QMessageBox.information(self, "Импорт путей", "В выбранной папке не найдено .rpy файлов.")
            return
        self._process_files(found)

    def _process_files(self, paths):
        all_path_defs, all_characters, all_music = [], [], []
        read_errors = []
        for p in paths:
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception as e:
                read_errors.append(f"{os.path.basename(p)}: {e}")
                continue
            rel = os.path.basename(p)
            all_path_defs += parse_image_and_define_paths(text, source_file=rel)
            all_characters += parse_characters(text, source_file=rel)
            all_music += parse_music_list(text, source_file=rel)

        self.report = build_import_report(self.rm, all_path_defs, all_characters, all_music)
        self._fill_tables()

        status = f"Обработано файлов: {len(paths)}. Найдено переименований: {len(self.report.plan)}."
        if read_errors:
            status += f" Ошибки чтения: {len(read_errors)}."
        self.status_lbl.setText(status)
        self.btn_apply.setEnabled(bool(self.report.plan) or bool(self.report.characters))

                                                                          

    def _fill_tables(self):
        self.plan_table.setRowCount(0)
        for item in self.report.plan:
            row = self.plan_table.rowCount()
            self.plan_table.insertRow(row)
            cb = QCheckBox()
            cb.setChecked(True)
            cb.toggled.connect(lambda checked, it=item: setattr(it, 'apply', checked))
            self.plan_table.setCellWidget(row, 0, cb)
            for col, text in enumerate([item.category, item.game_path, item.old_var, item.new_var, str(item.source_line)], start=1):
                cell = QTableWidgetItem(text)
                cell.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.plan_table.setItem(row, col, cell)
        self.tabs.setTabText(0, f"Переименования ({len(self.report.plan)})")

        self.unmatched_table.setRowCount(0)
        for pd in self.report.unmatched:
            row = self.unmatched_table.rowCount()
            self.unmatched_table.insertRow(row)
            for col, text in enumerate([pd.var_name, pd.game_path, str(pd.source_line)]):
                cell = QTableWidgetItem(text)
                cell.setFlags(Qt.ItemFlag.ItemIsEnabled)
                cell.setForeground(Qt.GlobalColor.gray)
                self.unmatched_table.setItem(row, col, cell)
        self.tabs.setTabText(1, f"Не найдено на диске ({len(self.report.unmatched)})")

        self.chars_table.setRowCount(0)
        for ch in self.report.characters:
            row = self.chars_table.rowCount()
            self.chars_table.insertRow(row)
            cb = QCheckBox()
            cb.setChecked(True)
            self.chars_table.setCellWidget(row, 0, cb)
            for col, text in enumerate([ch.variable, ch.name, ch.color], start=1):
                cell = QTableWidgetItem(text)
                cell.setFlags(Qt.ItemFlag.ItemIsEnabled)
                if col == 3:
                    cell.setForeground(Qt.GlobalColor.white)
                    cell.setBackground(QColor(ch.color))
                self.chars_table.setItem(row, col, cell)
        self.tabs.setTabText(2, f"Персонажи ({len(self.report.characters)})")

                                                                          

    def _apply(self):
        applied_paths = apply_import_report(self.rm, self.report)

        selected_chars = []
        for row in range(self.chars_table.rowCount()):
            cb = self.chars_table.cellWidget(row, 0)
            if cb and cb.isChecked():
                selected_chars.append(self.report.characters[row])

        if selected_chars:
            self.characters_selected.emit(selected_chars)
        if applied_paths:
            self.paths_applied.emit()

        QMessageBox.information(
            self, "Импорт путей",
            f"Применено переименований: {applied_paths}.\n"
            f"Импортировано персонажей: {len(selected_chars)}."
        )
        self.accept()
