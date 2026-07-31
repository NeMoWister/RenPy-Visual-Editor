from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.resource_usage_scanner import UsageRef


class ResourceUsageDialog(QDialog):
    """Список мест использования одного ресурса ('где используется') с
    переходом к конкретной ноде - двойной клик или кнопка "Перейти"."""
    navigate_requested = pyqtSignal(str, list, str)                                     

    def __init__(self, var_name: str, display_name: str, refs: list[UsageRef], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Где используется: {display_name}")
        self.setMinimumSize(600, 420)
        layout = QVBoxLayout(self)

        if not refs:
            layout.addWidget(QLabel(
                f"Ресурс «{var_name}» нигде не используется в текущем проекте."
            ))
        else:
            count_word = "место" if len(refs) == 1 else ("места" if 2 <= len(refs) <= 4 else "мест")
            layout.addWidget(QLabel(f"Найдено {len(refs)} {count_word} использования - var: {var_name}"))

            self.lst = QListWidget()
            for ref in refs:
                item = QListWidgetItem(f"{ref.breadcrumb}\n{ref.preview}")
                item.setData(Qt.ItemDataRole.UserRole, ref)
                item.setToolTip("Двойной клик - перейти к ноде")
                self.lst.addItem(item)
            self.lst.itemDoubleClicked.connect(self._on_activate)
            layout.addWidget(self.lst, 1)

            btn_row = QHBoxLayout()
            go_btn = QPushButton("➡ Перейти к ноде")
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
