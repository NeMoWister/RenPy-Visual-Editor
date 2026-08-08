                       
"""
Диалог импорта имён ресурсов, персонажей и музыки из существующих .rpy
файлов проекта (например, из старого сценария игры) - чтобы переменные,
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
from core.i18n import tr


class ImportPathsDialog(QDialog):
    characters_selected = pyqtSignal(list)                                                
    paths_applied = pyqtSignal()                                                        

    def __init__(self, resource_manager, parent=None):
        super().__init__(parent)
        self.rm = resource_manager
        self.report: ImportReport = ImportReport()
        self.setWindowTitle(tr("import_paths.title"))
        self.setMinimumSize(820, 560)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        hint = QLabel(tr("import_paths.hint"))
        hint.setWordWrap(True)
        hint.setObjectName("hint_text")
        layout.addWidget(hint)

        btn_row = QHBoxLayout()
        btn_files = QPushButton(tr("import_paths.pick_files"))
        btn_files.clicked.connect(self._pick_files)
        btn_row.addWidget(btn_files)
        btn_folder = QPushButton(tr("import_paths.pick_folder"))
        btn_folder.setObjectName("btn_secondary")
        btn_folder.clicked.connect(self._pick_folder)
        btn_row.addWidget(btn_folder)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.status_lbl = QLabel(tr("import_paths.no_files"))
        self.status_lbl.setObjectName("hint_text")
        layout.addWidget(self.status_lbl)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.plan_table = QTableWidget()
        self.plan_table.setColumnCount(6)
        self.plan_table.setHorizontalHeaderLabels([
            tr("import_paths.col_check"), tr("import_paths.col_category"), tr("import_paths.col_path"),
            tr("import_paths.col_old"), tr("import_paths.col_new"), tr("import_paths.col_line"),
        ])
        self.plan_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.plan_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.plan_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.plan_table, tr("import_paths.tab_renames", count=0))

        self.unmatched_table = QTableWidget()
        self.unmatched_table.setColumnCount(3)
        self.unmatched_table.setHorizontalHeaderLabels([tr("import_paths.col_rpy_name"), tr("import_paths.col_path"), tr("import_paths.col_line")])
        self.unmatched_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.unmatched_table, tr("import_paths.tab_unmatched", count=0))

        self.chars_table = QTableWidget()
        self.chars_table.setColumnCount(4)
        self.chars_table.setHorizontalHeaderLabels([tr("import_paths.col_check"), tr("import_paths.col_variable"), tr("import_paths.col_name"), tr("import_paths.col_color")])
        self.chars_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.chars_table, tr("import_paths.tab_characters", count=0))

        btn_bottom = QHBoxLayout()
        btn_cancel = QPushButton(tr("import_paths.close"))
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_bottom.addWidget(btn_cancel)
        btn_bottom.addStretch()
        self.btn_apply = QPushButton(tr("import_paths.apply_checked"))
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self._apply)
        btn_bottom.addWidget(self.btn_apply)
        layout.addLayout(btn_bottom)

                                                                          

    def _pick_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, tr("import_paths.pick_files_title"), "", "Ren'Py script (*.rpy)")
        if paths:
            self._process_files(paths)

    def _pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr("import_paths.pick_folder_title"))
        if not folder:
            return
        found = []
        for dirpath, _dirnames, filenames in os.walk(folder):
            for fn in filenames:
                if fn.lower().endswith('.rpy'):
                    found.append(os.path.join(dirpath, fn))
        if not found:
            QMessageBox.information(self, tr("import_paths.dialog_title"), tr("import_paths.no_rpy_found"))
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

        status = tr("import_paths.status", files=len(paths), renames=len(self.report.plan))
        if read_errors:
            status += tr("import_paths.read_errors", count=len(read_errors))
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
        self.tabs.setTabText(0, tr("import_paths.tab_renames", count=len(self.report.plan)))

        self.unmatched_table.setRowCount(0)
        for pd in self.report.unmatched:
            row = self.unmatched_table.rowCount()
            self.unmatched_table.insertRow(row)
            for col, text in enumerate([pd.var_name, pd.game_path, str(pd.source_line)]):
                cell = QTableWidgetItem(text)
                cell.setFlags(Qt.ItemFlag.ItemIsEnabled)
                cell.setForeground(Qt.GlobalColor.gray)
                self.unmatched_table.setItem(row, col, cell)
        self.tabs.setTabText(1, tr("import_paths.tab_unmatched", count=len(self.report.unmatched)))

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
        self.tabs.setTabText(2, tr("import_paths.tab_characters", count=len(self.report.characters)))

                                                                          

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
            self, tr("import_paths.dialog_title"),
            tr("import_paths.applied_result", renames=applied_paths, chars=len(selected_chars))
        )
        self.accept()
