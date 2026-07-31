"""
Командная палитра (Ctrl+Shift+P) - быстрый поиск и запуск любого действия
программы по названию, как в VSCode/Sublime/JetBrains.

Список команд собирается автоматически из меню окна (рекурсивно по
QMenuBar) - отдельный вручную поддерживаемый реестр не нужен и не может
разойтись с реальными пунктами меню.
"""
from dataclasses import dataclass
from typing import Callable, List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence


@dataclass
class Command:
    title: str                                                          
    run: Callable[[], None]
    shortcut: str = ""


def collect_commands_from_menubar(menubar) -> List[Command]:
    """Рекурсивно обходит все меню/подменю окна и собирает включённые
    действия с непустым текстом и обработчиком triggered - это и есть
    список доступных в палитре команд."""
    commands: List[Command] = []
    seen_actions = set()

    def clean_text(text: str) -> str:
        return text.replace("&", "").strip()

    def walk(actions, path: List[str]):
        for action in actions:
            if action.isSeparator():
                continue
            submenu = action.menu()
            label = clean_text(action.text())
            if submenu is not None:
                if label:
                    walk(submenu.actions(), path + [label])
                continue
            if not label or not action.isEnabled():
                continue
            if id(action) in seen_actions:
                continue
            seen_actions.add(id(action))
            full_title = " › ".join(path + [label]) if path else label
            shortcut = action.shortcut().toString(QKeySequence.SequenceFormat.NativeText) \
                if not action.shortcut().isEmpty() else ""
            commands.append(Command(title=full_title, run=action.trigger, shortcut=shortcut))

    walk(menubar.actions(), [])
    return commands


def _fuzzy_score(query: str, text: str) -> Optional[int]:
    """Простой fuzzy-скоринг: точная подстрока - лучший скор; иначе все
    символы запроса должны встретиться в тексте ПО ПОРЯДКУ (не обязательно
    подряд) - иначе совпадения нет вовсе. Меньше - лучше."""
    if not query:
        return 0
    q = query.lower()
    t = text.lower()
    idx = t.find(q)
    if idx >= 0:
        return idx                                                       

    ti = 0
    first_match = -1
    last_match = -1
    for ch in q:
        found_at = t.find(ch, ti)
        if found_at < 0:
            return None
        if first_match < 0:
            first_match = found_at
        last_match = found_at
        ti = found_at + 1
    spread = last_match - first_match
    return 1000 + spread + first_match


class CommandPaletteDialog(QDialog):
    def __init__(self, commands: List[Command], parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.commands = commands
        self.setFixedWidth(560)
        self.setStyleSheet("""
            QDialog { background:#20202a; border:1px solid #444; border-radius:8px; }
            QLineEdit {
                background:#161620; color:#fff; border:none; border-bottom:1px solid #444;
                padding:10px 12px; font-size:14px;
            }
            QListWidget {
                background:#20202a; color:#eee; border:none; padding:4px;
                font-size:13px; outline:none;
            }
            QListWidget::item { padding:6px 8px; border-radius:4px; }
            QListWidget::item:selected { background:#ff8c3d; color:#111; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(0)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Введите название команды...")
        self.search.textChanged.connect(self._refresh)
        layout.addWidget(self.search)

        self.list = QListWidget()
        self.list.setMaximumHeight(360)
        self.list.itemActivated.connect(self._run_selected)
        layout.addWidget(self.list)

        self.empty_lbl = QLabel("Ничего не найдено")
        self.empty_lbl.setStyleSheet("color:#888; padding:10px 12px;")
        self.empty_lbl.setVisible(False)
        layout.addWidget(self.empty_lbl)

        self.search.installEventFilter(self)
        self._refresh("")
        self.search.setFocus()

    def _refresh(self, query: str):
        self.list.clear()
        scored = []
        for cmd in self.commands:
            score = _fuzzy_score(query, cmd.title)
            if score is not None:
                scored.append((score, cmd))
        scored.sort(key=lambda x: (x[0], len(x[1].title)))
        for score, cmd in scored[:200]:
            suffix = f"   [{cmd.shortcut}]" if cmd.shortcut else ""
            item = QListWidgetItem(cmd.title + suffix)
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)
        self.empty_lbl.setVisible(self.list.count() == 0)

    def _run_selected(self, item: Optional[QListWidgetItem] = None):
        item = item or self.list.currentItem()
        if item is None:
            return
        cmd: Command = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
        cmd.run()

    def eventFilter(self, obj, event):
        if obj is self.search and event.type() == event.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Down:
                self.list.setCurrentRow(min(self.list.count() - 1, self.list.currentRow() + 1))
                return True
            if key == Qt.Key.Key_Up:
                self.list.setCurrentRow(max(0, self.list.currentRow() - 1))
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._run_selected()
                return True
            if key == Qt.Key.Key_Escape:
                self.reject()
                return True
        return super().eventFilter(obj, event)
