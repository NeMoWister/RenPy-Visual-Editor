from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.resource_usage_scanner import UsageRef
from core.i18n import tr, plural


class ResourceUsageDialog(QDialog):
    """Список мест использования одного ресурса ('где используется') с
    переходом к конкретной ноде - двойной клик или кнопка "Перейти"."""   
    navigate_requested = pyqtSignal(str, list, str)                                     

    def __init__(self, var_name: str, display_name: str, refs: list[UsageRef], parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("res_usage.title", name=display_name))
        self.setMinimumSize(600, 420)
        layout = QVBoxLayout(self)

        if not refs:
            layout.addWidget(QLabel(tr("res_usage.not_used", var=var_name)))
        else:
            count_word = plural(len(refs), {"ru": ("место", "места", "мест"), "en": ("location", "locations")})
            layout.addWidget(QLabel(tr("res_usage.found", count=len(refs), word=count_word, var=var_name)))

            self.lst = QListWidget()
            for ref in refs:
                item = QListWidgetItem(f"{ref.breadcrumb}\n{ref.preview}")
                item.setData(Qt.ItemDataRole.UserRole, ref)
                item.setToolTip(tr("res_usage.dblclick_tooltip"))
                self.lst.addItem(item)
            self.lst.itemDoubleClicked.connect(self._on_activate)
            layout.addWidget(self.lst, 1)

            btn_row = QHBoxLayout()
            go_btn = QPushButton(tr("res_usage.go_to_node"))
            go_btn.clicked.connect(lambda: self._on_activate(self.lst.currentItem()))
            btn_row.addWidget(go_btn)
            btn_row.addStretch()
            layout.addLayout(btn_row)
            self.lst.setCurrentRow(0)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        close_btn = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_btn is not None:
            close_btn.clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _on_activate(self, item: QListWidgetItem):
        if item is None:
            return
        ref: UsageRef = item.data(Qt.ItemDataRole.UserRole)
        self.navigate_requested.emit(ref.scene_id, ref.branch_path, ref.node_id)
        self.accept()
