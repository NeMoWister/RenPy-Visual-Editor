from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QDialogButtonBox, QFrame, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.spellcheck_scanner import LineIssues

_KIND_ICON = {"spelling": "✍", "repeat": "🔁", "punctuation": "␣", "tag": "🏷"}


class SpellcheckReportDialog(QDialog):
    """Список проблемных реплик по всему проекту, с переходом к ноде по
    двойному клику (та же механика, что и 'где используется'), и быстрым
    добавлением слов в личный словарь прямо из списка замечаний."""
    navigate_requested = pyqtSignal(str, list, str)
    rescan_requested = pyqtSignal()

    def __init__(self, results: list, diagnostics: dict, whitelist_store, base_dir: str, parent=None):
        super().__init__(parent)
        self.results = results
        self.diagnostics = diagnostics
        self.whitelist_store = whitelist_store
        self.base_dir = base_dir
        self.setWindowTitle("Проверка реплик")
        self.setMinimumSize(700, 560)
        layout = QVBoxLayout(self)

        self._add_diagnostics_banner(layout)

        total_issues = sum(len(r.issues) for r in results)
        layout.addWidget(QLabel(f"Реплик с замечаниями: {len(results)}  ·  всего замечаний: {total_issues}"))

        self.lst = QListWidget()
        for r in results:
            kinds = " ".join(sorted({_KIND_ICON.get(i.kind, "?") for i in r.issues}))
            first_msgs = "; ".join(i.message for i in r.issues[:3])
            more = f" (+{len(r.issues) - 3})" if len(r.issues) > 3 else ""
            item = QListWidgetItem(f"{kinds}  {r.breadcrumb} - {r.char_label}: «{r.text_preview}»\n{first_msgs}{more}")
            item.setData(Qt.ItemDataRole.UserRole, r)
            item.setToolTip("Двойной клик - перейти к ноде")
            self.lst.addItem(item)
        self.lst.itemDoubleClicked.connect(self._on_activate)
        self.lst.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self.lst, 1)

        if not results:
            layout.addWidget(QLabel("Замечаний не найдено 🎉"))

        layout.addWidget(QLabel("Опечатки в выбранной реплике - можно сразу добавить в личный словарь:"))
        self.words_frame = QFrame()
        self.words_layout = QHBoxLayout(self.words_frame)
        self.words_layout.setContentsMargins(0, 0, 0, 0)
        self.words_layout.addWidget(QLabel("(выберите реплику выше)"))
        self.words_layout.addStretch()
        layout.addWidget(self.words_frame)

        btn_row = QHBoxLayout()
        go_btn = QPushButton("➡ Перейти к ноде")
        go_btn.clicked.connect(lambda: self._on_activate(self.lst.currentItem()))
        btn_row.addWidget(go_btn)
        btn_rescan = QPushButton("🔄 Пересканировать")
        btn_rescan.setToolTip("Например, после добавления слов в словарь")
        btn_rescan.clicked.connect(self._on_rescan)
        btn_row.addWidget(btn_rescan)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        close_btn = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_btn is not None:
            close_btn.clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _add_diagnostics_banner(self, layout):
        d = self.diagnostics
        ru_ok = d.get("pymorphy_ru_ok") or d["dictionaries"]["ru"]["ok"]
        en_ok = d["dictionaries"]["en"]["ok"]
        if ru_ok and en_ok:
            return
        if ru_ok and not en_ok and not d["import_ok"]:
                                                                                  
                                                                          
            text = (
                "ℹ Орфография для русского проверяется через pymorphy3. Для "
                "английского языка библиотека pyspellchecker не установлена "
                "(pip install pyspellchecker)."
            )
            color, fg = "#152233", "#9fd6ff"
        elif not d.get("pymorphy_import_ok") and not d["import_ok"]:
            text = (
                "ℹ Ни pymorphy3, ни pyspellchecker не установлены - орфография по "
                "словарю не проверяется (pip install pymorphy3 pymorphy3-dicts-ru "
                "pyspellchecker)."
            )
            color, fg = "#2a1f14", "#ffb84d"
        else:
            problems = []
            if not ru_ok:
                morph_err = d.get("pymorphy_import_error") or self.diagnostics["dictionaries"]["ru"]["error"]
                problems.append(f"русский недоступен ({morph_err or 'причина неизвестна'})")
            if not en_ok:
                en_err = d["dictionaries"]["en"]["error"]
                problems.append(f"английский недоступен ({en_err or 'pyspellchecker не установлен'})")
            text = (
                "⚠ Проверка орфографии работает частично: " + "; ".join(problems) + ". "
                "Если это собранный .exe - словари/данные pymorphy3 или "
                "pyspellchecker не были включены в сборку (это файлы данных, "
                "PyInstaller их не подхватывает автоматически)."
            )
            color, fg = "#2a1f14", "#ffb84d"
        text += (
            " Доступны технические проверки: незакрытые теги {b}/{i}/{color}, "
            "повторы слов, лишние пробелы и знаки препинания."
        )
        note = QLabel(text)
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{fg}; background:{color}; padding:6px; border-radius:4px;")
        layout.addWidget(note)

    def _on_selection_changed(self, current, previous):
        while self.words_layout.count():
            item = self.words_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if current is None:
            self.words_layout.addWidget(QLabel("(выберите реплику выше)"))
            self.words_layout.addStretch()
            return

        r: LineIssues = current.data(Qt.ItemDataRole.UserRole)
        spelling_words = sorted({i.word for i in r.issues if i.kind == "spelling" and i.word})
        if not spelling_words:
            self.words_layout.addWidget(QLabel("(в этой реплике нет замечаний по орфографии)"))
        for word in spelling_words:
            btn = QPushButton(f"✚ «{word}»")
            btn.setToolTip("Добавить это слово в личный словарь (больше не будет считаться опечаткой)")
            btn.clicked.connect(lambda _=False, w=word, b=btn: self._add_word(w, b))
            self.words_layout.addWidget(btn)
        self.words_layout.addStretch()

    def _add_word(self, word: str, btn: QPushButton):
        self.whitelist_store.add(word, self.base_dir)
        btn.setText(f"✓ «{word}» добавлено")
        btn.setEnabled(False)

    def _on_rescan(self):
        self.rescan_requested.emit()
        self.accept()

    def _on_activate(self, item):
        if item is None:
            return
        r: LineIssues = item.data(Qt.ItemDataRole.UserRole)
        self.navigate_requested.emit(r.scene_id, r.branch_path, r.node_id)
        self.accept()
