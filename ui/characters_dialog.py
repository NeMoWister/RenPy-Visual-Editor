import re
import json
from dataclasses import asdict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QGroupBox, QColorDialog,
    QDialogButtonBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from core.models import Character


class CharacterEditWidget(QGroupBox):
    def __init__(self):
        super().__init__("Персонаж")
        layout = QVBoxLayout(self)
        def row(label, widget):
            r = QHBoxLayout()
            r.addWidget(QLabel(label))
            r.addWidget(widget, 1)
            return r
        self.name_edit = QLineEdit(); self.name_edit.setPlaceholderText("Алеся")
        self.var_edit = QLineEdit(); self.var_edit.setPlaceholderText("alesya")
        layout.addLayout(row("Имя:", self.name_edit))
        layout.addLayout(row("Переменная:", self.var_edit))
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет:"))
        self.color_btn = QPushButton("#ffffff")
        self.color_btn.setFixedWidth(90)
        self._color = "#ffffff"
        self.color_btn.clicked.connect(self._pick_color)
        self._apply_color()
        color_row.addWidget(self.color_btn)
        color_row.addStretch()
        layout.addLayout(color_row)
        self.tag_edit = QLineEdit(); self.tag_edit.setPlaceholderText("Необязательно")
        layout.addLayout(row("Image tag:", self.tag_edit))
        self.name_edit.textChanged.connect(self._auto_var)

    def _auto_var(self, text):
        if not self.var_edit.text():
            self.var_edit.setText(re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9_]', '_', text).lower())

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self)
        if c.isValid():
            self._color = c.name()
            self.color_btn.setText(self._color)
            self._apply_color()

    def _apply_color(self):
        c = QColor(self._color)
        bright = (c.red()*299 + c.green()*587 + c.blue()*114) / 1000 > 128
        self.color_btn.setStyleSheet(
            f"background:{self._color}; color:{'#000' if bright else '#fff'}; "
            "border:1px solid #3a3a4a; border-radius:4px;"
        )

    def load(self, ch: Character):
        self.name_edit.setText(ch.name)
        self.var_edit.setText(ch.variable)
        self._color = ch.color
        self.color_btn.setText(self._color)
        self._apply_color()
        self.tag_edit.setText(ch.image_tag or "")

    def get_character(self) -> Character:
        return Character(
            name=self.name_edit.text().strip(),
            variable=self.var_edit.text().strip(),
            color=self._color,
            image_tag=self.tag_edit.text().strip() or None,
        )


class CharactersDialog(QDialog):
    characters_changed = pyqtSignal(list)

    def __init__(self, characters: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Персонажи")
        self.setMinimumSize(600, 400)
        import copy
        self.characters = copy.deepcopy(characters)
        self._setup_ui()
        self._rebuild_list()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        left = QVBoxLayout()
        left.addWidget(QLabel("Список персонажей:"))
        self.char_list = QListWidget()
        self.char_list.currentRowChanged.connect(self._on_select)
        left.addWidget(self.char_list)
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("+ Добавить")
        self.btn_add.clicked.connect(self._add_char)
        self.btn_del = QPushButton("✕ Удалить")
        self.btn_del.setObjectName("btn_danger")
        self.btn_del.clicked.connect(self._del_char)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_del)
        left.addLayout(btn_row)

        io_row = QHBoxLayout()
        self.btn_export = QPushButton("⬆ Экспорт...")
        self.btn_export.setToolTip("Сохранить список персонажей в отдельный JSON-файл, "
                                    "чтобы перенести в другой проект или сделать резервную копию.")
        self.btn_export.clicked.connect(self._export_characters)
        self.btn_import = QPushButton("⬇ Импорт...")
        self.btn_import.setToolTip("Загрузить персонажей из файла, ранее сохранённого через «Экспорт».")
        self.btn_import.clicked.connect(self._import_characters)
        io_row.addWidget(self.btn_export)
        io_row.addWidget(self.btn_import)
        left.addLayout(io_row)

        self.btn_reset = QPushButton("🗑 Сбросить список")
        self.btn_reset.setToolTip("Удалить ВСЕХ персонажей из текущего проекта.")
        self.btn_reset.clicked.connect(self._reset_characters)
        left.addWidget(self.btn_reset)

        layout.addLayout(left)

        right = QVBoxLayout()
        self.editor = CharacterEditWidget()
        right.addWidget(self.editor)
        self.btn_save_char = QPushButton("💾 Применить")
        self.btn_save_char.clicked.connect(self._save_char)
        right.addWidget(self.btn_save_char)
        right.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        right.addWidget(buttons)
        layout.addLayout(right)

    def _rebuild_list(self):
        self.char_list.clear()
        for ch in self.characters:
            self.char_list.addItem(f"{ch.name}  ({ch.variable})")

    def _on_select(self, row):
        if 0 <= row < len(self.characters):
            self.editor.load(self.characters[row])

    def _add_char(self):
        self.characters.append(Character(name="Новый", variable="new_char"))
        self._rebuild_list()
        self.char_list.setCurrentRow(len(self.characters)-1)

    def _del_char(self):
        row = self.char_list.currentRow()
        if 0 <= row < len(self.characters):
            self.characters.pop(row)
            self._rebuild_list()

    def _export_characters(self):
        if not self.characters:
            QMessageBox.information(self, "Нечего экспортировать", "Список персонажей пуст.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт персонажей", "characters.json",
            "JSON (*.json);;Все файлы (*)"
        )
        if not path:
            return
        try:
            data = {"characters": [asdict(ch) for ch in self.characters]}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Готово",
                                     f"Экспортировано {len(self.characters)} персонажей в:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", str(e))

    def _import_characters(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт персонажей", "",
            "JSON (*.json);;Все файлы (*)"
        )
        if not path:
            return

        reply = QMessageBox.question(
            self, "Как объединить?",
            "Добавить импортированных персонажей к текущим "
            "(совпадающие по переменной будут перезаписаны)?\n\n"
            "Да — добавить/обновить.\nНет — полностью заменить текущий список.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return
        merge = reply == QMessageBox.StandardButton.Yes

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            imported = [Character(**c) for c in data.get("characters", [])]
            if not imported:
                QMessageBox.warning(self, "Пустой файл", "В файле не найдено персонажей.")
                return

            if merge:
                by_var = {ch.variable: ch for ch in self.characters}
                for ch in imported:
                    by_var[ch.variable] = ch
                self.characters = list(by_var.values())
            else:
                self.characters = imported

            self._rebuild_list()
            if self.characters:
                self.char_list.setCurrentRow(0)
            QMessageBox.information(self, "Готово", f"Импортировано {len(imported)} персонажей.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка импорта", str(e))

    def _reset_characters(self):
        if not self.characters:
            QMessageBox.information(self, "Нечего сбрасывать", "Список персонажей уже пуст.")
            return
        reply = QMessageBox.question(
            self, "Сбросить список персонажей?",
            f"Удалить всех {len(self.characters)} персонажей из проекта? "
            "Узлы диалогов, ссылающиеся на них, останутся, но без привязки к персонажу.\n\n"
            "Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.characters = []
        self._rebuild_list()
        QMessageBox.information(self, "Готово", "Список персонажей сброшен.")

    def _save_char(self):
        row = self.char_list.currentRow()
        if 0 <= row < len(self.characters):
            ch = self.editor.get_character()
            if not ch.name or not ch.variable:
                QMessageBox.warning(self, "Ошибка", "Имя и переменная обязательны")
                return
            self.characters[row] = ch
            self._rebuild_list()
            self.char_list.setCurrentRow(row)

    def _on_ok(self):
        self.characters_changed.emit(self.characters)
        self.accept()
