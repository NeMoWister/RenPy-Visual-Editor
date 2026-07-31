"""
Диалог «Статистика реплик» - баланс диалогов по персонажам: количество
реплик, слов и символов на каждого персонажа (плюс повествование).
Открывается через отдельное меню «Статистика» в главном окне.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QAbstractItemView
)
from PyQt6.QtCore import Qt

from core.dialogue_stats import compute_dialogue_stats, total_lines
from core.models import Project


class DialogueStatsDialog(QDialog):
    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Статистика реплик по персонажам")
        self.setMinimumSize(560, 420)
        self._setup_ui()
        self._reload()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.summary_lbl = QLabel()
        self.summary_lbl.setStyleSheet("color:#aaa; font-size:12px;")
        layout.addWidget(self.summary_lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Персонаж", "Реплик", "% от всех", "Слов", "Символов"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 5):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table, 1)

        note = QLabel(
            "Подсказка: Реплики считаются во всем проекте, "
            "вне зависимости от выбранного лейбла."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#777; font-size:11px;")
        layout.addWidget(note)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_refresh = QPushButton("🔄 Обновить")
        btn_refresh.clicked.connect(self._reload)
        btn_row.addWidget(btn_refresh)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _reload(self):
        stats = compute_dialogue_stats(self.project)
        total = total_lines(stats)

        self.summary_lbl.setText(
            f"Всего реплик: {total}   •   Персонажей с репликами: "
            f"{sum(1 for s in stats if s.key != '__narrator__')}"
        )

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(stats))
        for row, s in enumerate(stats):
            pct = (s.lines / total * 100) if total else 0.0

            name_item = QTableWidgetItem(s.display_name)
            lines_item = QTableWidgetItem()
            lines_item.setData(Qt.ItemDataRole.DisplayRole, s.lines)
            pct_item = QTableWidgetItem(f"{pct:.1f}%")
            words_item = QTableWidgetItem()
            words_item.setData(Qt.ItemDataRole.DisplayRole, s.words)
            chars_item = QTableWidgetItem()
            chars_item.setData(Qt.ItemDataRole.DisplayRole, s.chars)

            for item in (name_item, lines_item, pct_item, words_item, chars_item):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, lines_item)
            self.table.setItem(row, 2, pct_item)
            self.table.setItem(row, 3, words_item)
            self.table.setItem(row, 4, chars_item)

        self.table.setSortingEnabled(True)

        if not stats:
            self.summary_lbl.setText("В проекте пока нет ни одной реплики диалога.")
