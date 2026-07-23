"""
Панель истории последних действий — список меток из UndoManager с
возможностью отменить сразу до конкретного шага (а не жать Ctrl+Z много
раз).
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox
)


class HistoryPanelDialog(QDialog):
    def __init__(self, undo_manager, on_undo_to, parent=None):
        super().__init__(parent)
        self.undo_manager = undo_manager
        self.on_undo_to = on_undo_to
        self.setWindowTitle("История действий")
        self.setMinimumSize(420, 480)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Последние действия (сверху — самое недавнее). Выберите шаг и "
            "нажмите «Отменить до этого шага», чтобы вернуться в состояние "
            "ПЕРЕД ним — все более поздние действия будут отменены разом."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(info)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Обновить")
        btn_refresh.clicked.connect(self.refresh)
        btn_row.addWidget(btn_refresh)
        btn_row.addStretch()
        self.btn_undo_to = QPushButton("⏪ Отменить до этого шага")
        self.btn_undo_to.setObjectName("btn_primary")
        self.btn_undo_to.clicked.connect(self._on_undo_to_clicked)
        btn_row.addWidget(self.btn_undo_to)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def refresh(self):
        self.list_widget.clear()
        labels = self.undo_manager.history_labels()                    
        if not labels:
            item = QListWidgetItem("(история пуста — отменять нечего)")
            self.list_widget.addItem(item)
            self.btn_undo_to.setEnabled(False)
            return
        self.btn_undo_to.setEnabled(True)
        n = len(labels)
        for i, label in enumerate(reversed(labels)):
            depth = i + 1                                                              
            item = QListWidgetItem(f"{n - i}. {label}")
            item.setData(1000, depth)
            self.list_widget.addItem(item)
        self.list_widget.setCurrentRow(0)

    def _on_undo_to_clicked(self):
        item = self.list_widget.currentItem()
        if item is None:
            return
        depth = item.data(1000)
        if not depth:
            return
        confirm = QMessageBox.question(
            self, "Подтверждение",
            f"Отменить {depth} действи{'е' if depth == 1 else 'й'} и вернуться "
            f"в состояние перед «{item.text().split('. ', 1)[-1]}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.on_undo_to(depth)
        self.refresh()
