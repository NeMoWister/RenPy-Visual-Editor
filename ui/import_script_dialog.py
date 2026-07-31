                       
"""
Диалог импорта .rpy-сценария: парсит файл в SceneNode-узлы, показывает
предпросмотр распознанных сцен и процент нераспознанных строк, после чего
добавляет выбранные сцены в текущий проект.
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QSplitter, QTextEdit,
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from core.rpy_script_import import parse_script, ScriptImportReport
from core.models import Scene


class ImportScriptDialog(QDialog):
    scenes_imported = pyqtSignal(list)                

    def __init__(self, resource_manager=None, parent=None):
        super().__init__(parent)
        self.rm = resource_manager
        self.report: ScriptImportReport = ScriptImportReport()
        self.setWindowTitle("Импорт .rpy сценария")
        self.setMinimumSize(880, 600)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        hint = QLabel(
            "Выберите .rpy файл сценария. Редактор распознает известные конструкции "
            "(scene/show/hide/play/stop/menu/jump/return/pause/диалог) и создаст "
            "соответствующие узлы. Всё нераспознанное сохраняется как Python-узел "
            "и не теряется при экспорте обратно."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#999; font-size:11px;")
        layout.addWidget(hint)

        top_row = QHBoxLayout()
        btn_file = QPushButton("📄 Открыть .rpy файл...")
        btn_file.clicked.connect(self._pick_file)
        top_row.addWidget(btn_file)
        self.file_lbl = QLabel("Файл не выбран")
        self.file_lbl.setStyleSheet("color:#888;")
        top_row.addWidget(self.file_lbl, 1)
        layout.addLayout(top_row)

        self.stat_lbl = QLabel("")
        self.stat_lbl.setStyleSheet("color:#aaa; font-size:11px;")
        layout.addWidget(self.stat_lbl)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)

                                              
        left_w = QLabel.__new__(QLabel)
        from PyQt6.QtWidgets import QWidget
        left_w = QWidget()
        left_l = QVBoxLayout(left_w)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.addWidget(QLabel("Найденные сцены и узлы:"))

        check_row = QHBoxLayout()
        btn_all = QPushButton("Все")
        btn_all.setObjectName("btn_secondary")
        btn_all.setFixedWidth(70)
        btn_all.clicked.connect(self._check_all)
        check_row.addWidget(btn_all)
        btn_none = QPushButton("Ни одной")
        btn_none.setObjectName("btn_secondary")
        btn_none.setFixedWidth(120)
        btn_none.clicked.connect(self._check_none)
        check_row.addWidget(btn_none)
        check_row.addStretch()
        left_l.addLayout(check_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Сцена / Узел"])
        self.tree.setColumnCount(1)
        self.tree.itemChanged.connect(self._on_item_changed)
        left_l.addWidget(self.tree, 1)
        splitter.addWidget(left_w)

                                               
        right_w = QWidget()
        right_l = QVBoxLayout(right_w)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.addWidget(QLabel("Нераспознанные строки (будут PYTHON-узлами):"))
        self.unrecog_edit = QTextEdit()
        self.unrecog_edit.setReadOnly(True)
        self.unrecog_edit.setPlaceholderText("Нераспознанного нет - отлично!")
        self.unrecog_edit.setStyleSheet("background:#1c1c22; color:#ddd; border:1px solid #3a3a46;")
        right_l.addWidget(self.unrecog_edit, 1)

        right_l.addWidget(QLabel("⚠ Импортированы, но ресурс не найден - нужно добавить:"))
        self.needs_res_edit = QTextEdit()
        self.needs_res_edit.setReadOnly(True)
        self.needs_res_edit.setPlaceholderText("Все ресурсы найдены - отлично!")
        self.needs_res_edit.setStyleSheet("background:#241c14; color:#ffcf8a; border:1px solid #4a3a20;")
        right_l.addWidget(self.needs_res_edit, 1)
        splitter.addWidget(right_w)
        splitter.setSizes([560, 300])

        btn_bottom = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_bottom.addWidget(btn_cancel)
        btn_bottom.addStretch()
        self.btn_import = QPushButton("⬇ Импортировать выбранные сцены")
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self._import)
        btn_bottom.addWidget(self.btn_import)
        layout.addLayout(btn_bottom)

                                                                          

    def _pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть .rpy файл", "", "Ren'Py script (*.rpy)")
        if not path:
            return
        self.file_lbl.setText(os.path.basename(path))
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка чтения", str(e))
            return
        self.report = parse_script(text, os.path.basename(path), rm=self.rm)
        self._fill_tree()
        self._fill_unrecognized()

                                                                           

    def _fill_tree(self):
        self.tree.blockSignals(True)
        self.tree.clear()
        for scene in self.report.scenes:
            scene_item = QTreeWidgetItem([scene.name])
            scene_item.setFlags(scene_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            scene_item.setCheckState(0, Qt.CheckState.Checked)
            scene_item.setData(0, Qt.ItemDataRole.UserRole, scene)
            for node in scene.nodes:
                node_item = QTreeWidgetItem([node.preview_text()])
                node_item.setFlags(node_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
                if node.node_type.value == 'raw':
                    node_item.setForeground(0, QColor("#ff9955"))
                self.tree.addTopLevelItem(scene_item)
                scene_item.addChild(node_item)
            scene_item.setExpanded(True)

        self.tree.blockSignals(False)

        ok = self.report.total_nodes > 0
        raw = sum(
            1 for sc in self.report.scenes
            for n in sc.nodes if n.node_type.value == 'raw'
        )
        pct = self.report.recognized_pct
        self.stat_lbl.setText(
            f"Сцен: {len(self.report.scenes)}  |  "
            f"Узлов: {self.report.total_nodes}  |  "
            f"Распознано: {pct:.0f}%  |  "
            f"Нераспознано (raw): {raw}"
        )
        self.btn_import.setEnabled(ok)

    def _fill_unrecognized(self):
        if not self.report.unrecognized:
            self.unrecog_edit.setPlainText("")
        else:
            lines = [f"Строка {ln}: {txt}" for ln, txt in self.report.unrecognized]
            self.unrecog_edit.setPlainText('\n'.join(lines))

        needs_res = getattr(self.report, "needs_resource", [])
        if not needs_res:
            self.needs_res_edit.setPlainText("")
        else:
            lines = [f"Строка {ln}: {txt}  →  ресурс «{var}»" for ln, txt, var in needs_res]
            self.needs_res_edit.setPlainText('\n'.join(lines))

                                                                          

    def _on_item_changed(self, item, col):
        pass                                    

    def _check_all(self):
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setCheckState(0, Qt.CheckState.Checked)
        self.tree.blockSignals(False)

    def _check_none(self):
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setCheckState(0, Qt.CheckState.Unchecked)
        self.tree.blockSignals(False)

                                                                          

    def _import(self):
        selected = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                scene = item.data(0, Qt.ItemDataRole.UserRole)
                if scene:
                    selected.append(scene)
        if not selected:
            QMessageBox.information(self, "Импорт", "Не выбрано ни одной сцены.")
            return
        self.scenes_imported.emit(selected)
        self.accept()
