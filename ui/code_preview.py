from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QPlainTextEdit, QFileDialog, QMessageBox, QTabWidget
)
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression


class RenPyHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        def add(pattern, color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold: fmt.setFontWeight(700)
            if italic: fmt.setFontItalic(True)
            self.rules.append((QRegularExpression(pattern), fmt))
        for kw in ["label","scene","show","hide","play","stop","pause","jump","menu",
                   "python","define","image","with","music","sound","dissolve","fade","return","call"]:
            add(rf'\b{kw}\b', "#ff8c00", bold=True)
        add(r'"[^"]*"', "#98c379")
        add(r'#.*$', "#5c6370", italic=True)
        add(r'\b\d+\.?\d*\b', "#d19a66")
        add(r'^\s*\$.*$', "#c678dd")
        add(r'(?<=label )\w+', "#61afef", bold=True)
        add(r'(?<=jump )\w+', "#61afef")

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class CodePreviewDialog(QDialog):
    def __init__(self, full_code: str, defines_code: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Сгенерированный код Ren'Py")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        self.full_editor = QPlainTextEdit()
        self.full_editor.setFont(QFont("Courier New", 11))
        self.full_editor.setPlainText(full_code)
        RenPyHighlighter(self.full_editor.document())
        tabs.addTab(self.full_editor, "Полный сценарий (.rpy)")
        if defines_code:
            self.def_editor = QPlainTextEdit()
            self.def_editor.setFont(QFont("Courier New", 11))
            self.def_editor.setPlainText(defines_code)
            RenPyHighlighter(self.def_editor.document())
            tabs.addTab(self.def_editor, "Defines / Characters")
        layout.addWidget(tabs)
        btn_row = QHBoxLayout()
        btn_copy = QPushButton("📋 Копировать")
        btn_copy.clicked.connect(self._copy)
        btn_save = QPushButton("💾 Сохранить .rpy")
        btn_save.clicked.connect(self._save)
        btn_close = QPushButton("Закрыть")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_copy)
        btn_row.addWidget(btn_save)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _copy(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.full_editor.toPlainText())
        QMessageBox.information(self, "Скопировано", "Код скопирован в буфер обмена")

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить .rpy", "script.rpy", "Ren'Py Script (*.rpy);;Все файлы (*)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.full_editor.toPlainText())
                QMessageBox.information(self, "Готово", f"Файл сохранён:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
