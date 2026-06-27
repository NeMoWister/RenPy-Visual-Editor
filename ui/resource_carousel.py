from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap
from core.resource_manager import ResourceEntry
from core.composite_sprite_parser import CompositeSprite
from pathlib import Path
from ui.pixmap_cache import get_scaled, get_composite


class ResourceCard(QFrame):
    clicked = pyqtSignal(object)

    LABEL_HEIGHT = 28

    def __init__(self, entry: ResourceEntry, thumb_size: int = 90):
        super().__init__()
        self.entry = entry
        self.selected = False
        self.thumb_size = thumb_size
        self.setFixedSize(thumb_size + 16, thumb_size + self.LABEL_HEIGHT + 14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("resource_card")
        self._setup_ui(thumb_size)

    def _setup_ui(self, thumb_size: int):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        self.preview = QLabel()
        self.preview.setFixedSize(thumb_size, thumb_size)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("background: #16161c; border-radius: 4px; border: 1px solid #3a3a4a;")

        ext = Path(self.entry.filename).suffix.lower()
        if ext in {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}:
            self.preview.setText("…")
            self.preview.setStyleSheet(self.preview.styleSheet() + "color:#555; font-size:11px;")
            self._needs_thumb = True
        else:
            icon = "🎵" if self.entry.category == 'music' else "🔊"
            self.preview.setText(icon)
            self.preview.setStyleSheet(self.preview.styleSheet() + "font-size:32px;")
            self._needs_thumb = False

        layout.addWidget(self.preview)
        name_label = QLabel(self.entry.display_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size:10px; color:#aaa;")
        name_label.setMaximumWidth(thumb_size + 8)
        layout.addWidget(name_label)
        self._update_style()

    def load_thumbnail(self):
        """Реально читает и масштабирует изображение. Вызывается отложенно
        (см. ResourceCarousel._schedule_thumbnails), не в конструкторе."""
        if not self._needs_thumb:
            return
        self._needs_thumb = False
        pm = get_scaled(self.entry.abs_path, self.thumb_size, self.thumb_size)
        if pm is not None:
            self.preview.setPixmap(pm)
            self.preview.setStyleSheet("background: #16161c; border-radius: 4px; border: 1px solid #3a3a4a;")
        else:
            self.preview.setText("🖼")
            self.preview.setStyleSheet("background: #16161c; border-radius: 4px; border: 1px solid #3a3a4a; font-size:24px;")

    def _update_style(self):
        if self.selected:
            self.setStyleSheet("""
                QFrame#resource_card { background: #2a1a00; border: 2px solid #ff8c00; border-radius: 6px; }
            """)
        else:
            self.setStyleSheet("""
                QFrame#resource_card { background: #22222a; border: 1px solid #3a3a4a; border-radius: 6px; }
                QFrame#resource_card:hover { border-color: #ff8c00; background: #2d2d37; }
            """)

    def set_selected(self, val: bool):
        self.selected = val
        self._update_style()

    def mousePressEvent(self, event):
        self.clicked.emit(self.entry)
        super().mousePressEvent(event)


class FolderCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, folder_name: str, thumb_size: int = 90):
        super().__init__()
        self.folder_name = folder_name
        self.thumb_size = thumb_size
        self.selected = False
        self.setFixedSize(thumb_size + 16, thumb_size + ResourceCard.LABEL_HEIGHT + 14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("folder_card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        self.icon = QLabel("📁")
        self.icon.setFixedSize(thumb_size, thumb_size)
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon.setStyleSheet("background: #16161c; border-radius: 4px; border: 1px solid #3a3a4a; font-size:36px;")
        layout.addWidget(self.icon)

        name_label = QLabel(folder_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size:11px; color:#ddd; font-weight:bold;")
        name_label.setMaximumWidth(thumb_size + 8)
        layout.addWidget(name_label)
        self._update_style()

    def _update_style(self):
        if self.selected:
            self.setStyleSheet("""
                QFrame#folder_card { background: #2a1a00; border: 2px solid #ff8c00; border-radius: 6px; }
            """)
        else:
            self.setStyleSheet("""
                QFrame#folder_card { background: #22222a; border: 1px solid #3a3a4a; border-radius: 6px; }
                QFrame#folder_card:hover { border-color: #ff8c00; background: #2d2d37; }
            """)

    def set_selected(self, val: bool):
        self.selected = val
        self._update_style()

    def mousePressEvent(self, event):
        self.clicked.emit(self.folder_name)
        super().mousePressEvent(event)


class CharacterGroupPicker(QWidget):
    """Простой выбор папки персонажа верхнего уровня (resources/sprites/<имя>)
    БЕЗ заходов внутрь — используется для 'Скрыть спрайт: выбрать персонажа
    целиком', где не важна конкретная вариация/файл, а нужно скрыть всё,
    что сейчас показано для этого персонажа."""
    selection_changed = pyqtSignal(str) 

    def __init__(self, resource_manager=None, category: str = "sprites", thumb_size: int = 84):
        super().__init__()
        self.rm = resource_manager
        self.category = category
        self.thumb_size = thumb_size
        self.cards: List[FolderCard] = []
        self.selected_folder: str = ""
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFixedHeight(self.thumb_size + 52)
        self.scroll.setWidgetResizable(False)

        self.container = QWidget()
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(4, 0, 4, 0)
        self.container_layout.setSpacing(6)
        self.container_layout.addStretch()
        self.scroll.setWidget(self.container)
        row.addWidget(self.scroll, 1)
        outer.addLayout(row)

        none_row = QHBoxLayout()
        self.btn_none = QPushButton("✕ Убрать выбор")
        self.btn_none.setObjectName("btn_secondary")
        self.btn_none.setFixedHeight(32)
        self.btn_none.clicked.connect(self._clear_selection)
        none_row.addWidget(self.btn_none)
        none_row.addStretch()
        outer.addLayout(none_row)

    def set_resource_manager(self, rm, category: Optional[str] = None):
        self.rm = rm
        if category:
            self.category = category
        self._refresh()

    def select_folder(self, folder_name: str):
        self.selected_folder = folder_name or ""
        self._refresh()

    def get_selected(self) -> str:
        return self.selected_folder

    def _refresh(self):
        for card in self.cards:
            card.setParent(None)
        self.cards.clear()
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        folders = list(self.rm.get_folders(self.category, "")) if self.rm else []
        if self.rm and self.category == "sprites":
            for character in self.rm.get_composite_characters():
                if character not in folders:
                    folders.append(character)
            folders.sort()

        for folder_name in folders:
            card = FolderCard(folder_name, self.thumb_size)
            card.set_selected(folder_name == self.selected_folder)
            card.clicked.connect(self._on_folder_clicked)
            self.cards.append(card)
            self.container_layout.addWidget(card)

        self.container_layout.addStretch()
        w = len(folders) * (self.thumb_size + 22) + 10
        self.container.setFixedWidth(max(w, 200))
        self.container.setFixedHeight(self.thumb_size + ResourceCard.LABEL_HEIGHT + 14)

    def _on_folder_clicked(self, folder_name: str):
        self.selected_folder = folder_name
        for card in self.cards:
            card.set_selected(card.folder_name == folder_name)
        self.selection_changed.emit(folder_name)

    def _clear_selection(self):
        self.selected_folder = ""
        for card in self.cards:
            card.set_selected(False)
        self.selection_changed.emit("")


class FolderResourceCarousel(QWidget):
    selection_changed = pyqtSignal(object)

    def __init__(self, resource_manager=None, category: str = "sprites",
                 category_label: str = "", thumb_size: int = 90):
        super().__init__()
        self.rm = resource_manager
        self.category = category
        self.thumb_size = thumb_size
        self.current_path: List[str] = []
        self.cards: List[QWidget] = []
        self.selected_entry: Optional[ResourceEntry] = None
        self._all_entries: List[ResourceEntry] = []
        self._setup_ui(category_label)

    def _setup_ui(self, label_text: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        if label_text:
            lbl = QLabel(label_text)
            lbl.setObjectName("section_title")
            outer.addWidget(lbl)

        self.breadcrumb_row = QHBoxLayout()
        self.breadcrumb_row.setContentsMargins(0, 0, 0, 0)
        self.breadcrumb_row.setSpacing(4)
        outer.addLayout(self.breadcrumb_row)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        self.btn_left = QPushButton("◀")
        self.btn_left.setFixedSize(24, self.thumb_size + 30)
        self.btn_left.setObjectName("btn_secondary")
        self.btn_left.clicked.connect(self._scroll_left)
        row.addWidget(self.btn_left)

        self.scroll = QScrollArea()
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFixedHeight(self.thumb_size + 52)
        self.scroll.setWidgetResizable(False)

        self.container = QWidget()
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(4, 0, 4, 0)
        self.container_layout.setSpacing(6)
        self.container_layout.addStretch()
        self.scroll.setWidget(self.container)
        row.addWidget(self.scroll, 1)

        self.btn_right = QPushButton("▶")
        self.btn_right.setFixedSize(24, self.thumb_size + 30)
        self.btn_right.setObjectName("btn_secondary")
        self.btn_right.clicked.connect(self._scroll_right)
        row.addWidget(self.btn_right)

        outer.addLayout(row)

        none_row = QHBoxLayout()
        self.btn_none = QPushButton("✕ Убрать выбор")
        self.btn_none.setObjectName("btn_secondary")
        self.btn_none.setFixedHeight(32)
        self.btn_none.clicked.connect(self._clear_selection)
        none_row.addWidget(self.btn_none)
        none_row.addStretch()
        outer.addLayout(none_row)

    def set_resource_manager(self, rm, category: Optional[str] = None):
        self.rm = rm
        if category:
            self.category = category
        self.current_path = []
        self.selected_entry = None
        self._refresh_view()

    def select_by_var(self, var: str):
        if not self.rm:
            return
        entry = self.rm.find_by_var(var)
        if entry and entry.category == self.category:
            self.current_path = entry.group_parts()
            self.selected_entry = entry
            self._refresh_view()
        else:
            self._refresh_view()

    def get_selected(self) -> Optional[ResourceEntry]:
        return self.selected_entry

    def _current_path_str(self) -> str:
        return "/".join(self.current_path)

    def _go_to(self, path_parts: List[str]):
        self.current_path = list(path_parts)
        self._refresh_view()

    def _enter_folder(self, folder_name: str):
        self.current_path.append(folder_name)
        self._refresh_view()

    def _rebuild_breadcrumbs(self):
        while self.breadcrumb_row.count():
            item = self.breadcrumb_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        root_label = self.rm.CATEGORIES.get(self.category, (self.category,))[0] if self.rm else self.category
        crumbs = [("🏠 " + root_label, [])]
        for i, part in enumerate(self.current_path):
            crumbs.append((part, self.current_path[:i + 1]))

        for i, (text, path) in enumerate(crumbs):
            btn = QPushButton(text)
            btn.setFlat(True)
            is_last = (i == len(crumbs) - 1)
            btn.setEnabled(not is_last)
            btn.setStyleSheet(f"""
                QPushButton {{
                    color: {'#ff8c00' if is_last else '#9aa'};
                    font-weight: {'bold' if is_last else 'normal'};
                    border: none; padding: 2px 4px; text-align: left;
                    background: transparent;
                }}
                QPushButton:hover {{ color: #ffa020; }}
                QPushButton:disabled {{ color: #ff8c00; }}
            """)
            btn.clicked.connect(lambda _=None, p=path: self._go_to(p))
            self.breadcrumb_row.addWidget(btn)
            if not is_last:
                sep = QLabel("›")
                sep.setStyleSheet("color:#666;")
                self.breadcrumb_row.addWidget(sep)
        self.breadcrumb_row.addStretch()

    def _refresh_view(self):
        self._rebuild_breadcrumbs()

        for card in self.cards:
            card.setParent(None)
        self.cards.clear()
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.rm:
            self.container.setFixedWidth(200)
            self.container.setFixedHeight(self.thumb_size + ResourceCard.LABEL_HEIGHT + 14)
            return

        folders = self.rm.get_folders(self.category, self._current_path_str())
        entries = self.rm.get_entries_in_folder(self.category, self._current_path_str())

        count = 0
        for folder_name in folders:
            card = FolderCard(folder_name, self.thumb_size)
            card.clicked.connect(self._enter_folder)
            self.cards.append(card)
            self.container_layout.addWidget(card)
            count += 1

        for entry in entries:
            card = ResourceCard(entry, self.thumb_size)
            card.clicked.connect(self._on_card_clicked)
            if self.selected_entry and entry.var_name == self.selected_entry.var_name:
                card.set_selected(True)
            self.cards.append(card)
            self.container_layout.addWidget(card)
            count += 1

        self.container_layout.addStretch()
        w = count * (self.thumb_size + 22) + 10
        self.container.setFixedWidth(max(w, 200))
        self.container.setFixedHeight(self.thumb_size + ResourceCard.LABEL_HEIGHT + 14)
        self._schedule_thumbnails()

    def _schedule_thumbnails(self):
        pending = [c for c in self.cards if isinstance(c, ResourceCard)]
        batch_size = 4

        def step():
            for _ in range(batch_size):
                if not pending:
                    return
                card = pending.pop(0)
                try:
                    card.load_thumbnail()
                except RuntimeError:
                    pass
            if pending:
                QTimer.singleShot(0, step)

        QTimer.singleShot(0, step)

    def _on_card_clicked(self, entry: ResourceEntry):
        for card in self.cards:
            if isinstance(card, ResourceCard):
                card.set_selected(card.entry is entry)
        self.selected_entry = entry
        self.selection_changed.emit(entry)

    def _clear_selection(self):
        for card in self.cards:
            if isinstance(card, ResourceCard):
                card.set_selected(False)
        self.selected_entry = None
        self.selection_changed.emit(None)

    def _scroll_left(self):
        sb = self.scroll.horizontalScrollBar()
        sb.setValue(sb.value() - (self.thumb_size + 22) * 3)

    def _scroll_right(self):
        sb = self.scroll.horizontalScrollBar()
        sb.setValue(sb.value() + (self.thumb_size + 22) * 3)


class ResourceCarousel(QWidget):
    selection_changed = pyqtSignal(object)

    def __init__(self, category_label: str = "", thumb_size: int = 90):
        super().__init__()
        self.thumb_size = thumb_size
        self.entries: List[ResourceEntry] = []
        self.cards: List[ResourceCard] = []
        self.selected_entry: Optional[ResourceEntry] = None
        self._setup_ui(category_label)

    def _setup_ui(self, label_text: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        if label_text:
            lbl = QLabel(label_text)
            lbl.setObjectName("section_title")
            outer.addWidget(lbl)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        self.btn_left = QPushButton("◀")
        self.btn_left.setFixedSize(24, self.thumb_size + 30)
        self.btn_left.setObjectName("btn_secondary")
        self.btn_left.clicked.connect(self._scroll_left)
        row.addWidget(self.btn_left)

        self.scroll = QScrollArea()
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFixedHeight(self.thumb_size + 52)
        self.scroll.setWidgetResizable(False)

        self.container = QWidget()
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(4, 0, 4, 0)
        self.container_layout.setSpacing(6)
        self.container_layout.addStretch()
        self.scroll.setWidget(self.container)
        row.addWidget(self.scroll, 1)

        self.btn_right = QPushButton("▶")
        self.btn_right.setFixedSize(24, self.thumb_size + 30)
        self.btn_right.setObjectName("btn_secondary")
        self.btn_right.clicked.connect(self._scroll_right)
        row.addWidget(self.btn_right)

        outer.addLayout(row)

        none_row = QHBoxLayout()
        self.btn_none = QPushButton("✕ Убрать выбор")
        self.btn_none.setObjectName("btn_secondary")
        self.btn_none.setFixedHeight(32)
        self.btn_none.clicked.connect(self._clear_selection)
        none_row.addWidget(self.btn_none)
        none_row.addStretch()
        outer.addLayout(none_row)

    def set_entries(self, entries: List[ResourceEntry]):
        for card in self.cards:
            card.setParent(None)
        self.cards.clear()
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.entries = entries
        for entry in entries:
            card = ResourceCard(entry, self.thumb_size)
            card.clicked.connect(self._on_card_clicked)
            self.cards.append(card)
            self.container_layout.addWidget(card)
        self.container_layout.addStretch()
        w = len(entries) * (self.thumb_size + 22) + 10
        self.container.setFixedWidth(max(w, 200))
        self.container.setFixedHeight(self.thumb_size + ResourceCard.LABEL_HEIGHT + 14)
        self.selected_entry = None
        self._schedule_thumbnails()

    def _schedule_thumbnails(self):
        pending = list(self.cards)
        batch_size = 4

        def step():
            for _ in range(batch_size):
                if not pending:
                    return
                card = pending.pop(0)
                try:
                    card.load_thumbnail()
                except RuntimeError:
                    pass
            if pending:
                QTimer.singleShot(0, step)

        QTimer.singleShot(0, step)

    def _on_card_clicked(self, entry: ResourceEntry):
        for card in self.cards:
            card.set_selected(card.entry is entry)
        self.selected_entry = entry
        self.selection_changed.emit(entry)

    def _clear_selection(self):
        for card in self.cards:
            card.set_selected(False)
        self.selected_entry = None
        self.selection_changed.emit(None)

    def _scroll_left(self):
        sb = self.scroll.horizontalScrollBar()
        sb.setValue(sb.value() - (self.thumb_size + 22) * 3)

    def _scroll_right(self):
        sb = self.scroll.horizontalScrollBar()
        sb.setValue(sb.value() + (self.thumb_size + 22) * 3)

    def get_selected(self) -> Optional[ResourceEntry]:
        return self.selected_entry

    def select_by_var(self, var: str):
        for card in self.cards:
            sel = card.entry.var_name == var
            card.set_selected(sel)
            if sel:
                self.selected_entry = card.entry


class CompositeSpriteCard(QFrame):
    """Карточка составного спрайта (sprites.rpy): миниатюра — это все его
    слои, наложенные друг на друга, как в самой игре, а не один файл."""
    clicked = pyqtSignal(object)

    LABEL_HEIGHT = ResourceCard.LABEL_HEIGHT

    def __init__(self, sprite: CompositeSprite, rm, thumb_size: int = 90):
        super().__init__()
        self.sprite = sprite
        self.rm = rm
        self.selected = False
        self.thumb_size = thumb_size
        self.setFixedSize(thumb_size + 16, thumb_size + self.LABEL_HEIGHT + 14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("resource_card")
        self._needs_thumb = True
        self._setup_ui(thumb_size)

    def _setup_ui(self, thumb_size: int):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        self.preview = QLabel()
        self.preview.setFixedSize(thumb_size, thumb_size)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("background: #16161c; border-radius: 4px; border: 1px solid #3a3a4a;")
        self.preview.setText("…")
        self.preview.setStyleSheet(self.preview.styleSheet() + "color:#555; font-size:11px;")
        layout.addWidget(self.preview)

        name_label = QLabel(self.sprite.display_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size:10px; color:#aaa;")
        name_label.setMaximumWidth(thumb_size + 8)
        layout.addWidget(name_label)
        self._update_style()

    def load_thumbnail(self):
        if not self._needs_thumb:
            return
        self._needs_thumb = False
        layers = [
            (self.rm.resolve_layer_path(layer.rel_path, self.sprite.source), layer.offset_x, layer.offset_y)
            for layer in self.sprite.layers
        ]
        pm = get_composite(layers, self.sprite.width, self.sprite.height,
                            target_w=self.thumb_size, target_h=self.thumb_size)
        if pm is not None:
            self.preview.setPixmap(pm)
            self.preview.setStyleSheet("background: #16161c; border-radius: 4px; border: 1px solid #3a3a4a;")
        else:
            self.preview.setText("🖼")
            self.preview.setStyleSheet("background: #16161c; border-radius: 4px; border: 1px solid #3a3a4a; font-size:24px;")

    def _update_style(self):
        if self.selected:
            self.setStyleSheet("""
                QFrame#resource_card { background: #2a1a00; border: 2px solid #ff8c00; border-radius: 6px; }
            """)
        else:
            self.setStyleSheet("""
                QFrame#resource_card { background: #22222a; border: 1px solid #3a3a4a; border-radius: 6px; }
                QFrame#resource_card:hover { border-color: #ff8c00; background: #2d2d37; }
            """)

    def set_selected(self, val: bool):
        self.selected = val
        self._update_style()

    def mousePressEvent(self, event):
        self.clicked.emit(self.sprite)
        super().mousePressEvent(event)


POSITION_LABELS = {"far": "Дальний план (far)", "close": "Крупный план (close)", "normal": "Средний план (normal)"}


class CompositeSpriteCarousel(QWidget):
    selection_changed = pyqtSignal(object)  # CompositeSprite | None

    def __init__(self, resource_manager=None, thumb_size: int = 90):
        super().__init__()
        self.rm = resource_manager
        self.thumb_size = thumb_size
        self.current_path: List[str] = []
        self.cards: List[QWidget] = []
        self.selected_sprite: Optional[CompositeSprite] = None
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        self.breadcrumb_row = QHBoxLayout()
        self.breadcrumb_row.setContentsMargins(0, 0, 0, 0)
        self.breadcrumb_row.setSpacing(4)
        outer.addLayout(self.breadcrumb_row)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        self.btn_left = QPushButton("◀")
        self.btn_left.setFixedSize(24, self.thumb_size + 30)
        self.btn_left.setObjectName("btn_secondary")
        self.btn_left.clicked.connect(self._scroll_left)
        row.addWidget(self.btn_left)

        self.scroll = QScrollArea()
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFixedHeight(self.thumb_size + 52)
        self.scroll.setWidgetResizable(False)

        self.container = QWidget()
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(4, 0, 4, 0)
        self.container_layout.setSpacing(6)
        self.container_layout.addStretch()
        self.scroll.setWidget(self.container)
        row.addWidget(self.scroll, 1)

        self.btn_right = QPushButton("▶")
        self.btn_right.setFixedSize(24, self.thumb_size + 30)
        self.btn_right.setObjectName("btn_secondary")
        self.btn_right.clicked.connect(self._scroll_right)
        row.addWidget(self.btn_right)
        outer.addLayout(row)

        none_row = QHBoxLayout()
        self.btn_none = QPushButton("✕ Убрать выбор")
        self.btn_none.setObjectName("btn_secondary")
        self.btn_none.setFixedHeight(32)
        self.btn_none.clicked.connect(self._clear_selection)
        none_row.addWidget(self.btn_none)
        none_row.addStretch()
        outer.addLayout(none_row)

    def set_resource_manager(self, rm):
        self.rm = rm
        self.current_path = []
        self.selected_sprite = None
        self._refresh_view()

    def select_by_name(self, full_name: str):
        """Находит составной спрайт по полному имени (как из image ...) и
        сразу переходит в его персонажа/позицию, подсвечивая карточку."""
        if not self.rm:
            return
        sprite = self.rm.find_composite_by_name(full_name)
        if sprite:
            self.current_path = [sprite.character, sprite.position]
            self.selected_sprite = sprite
        self._refresh_view()

    def get_selected(self) -> Optional[CompositeSprite]:
        return self.selected_sprite

    def _go_to(self, path_parts: List[str]):
        self.current_path = list(path_parts)
        self._refresh_view()

    def _enter(self, part: str):
        self.current_path.append(part)
        self._refresh_view()

    def _rebuild_breadcrumbs(self):
        while self.breadcrumb_row.count():
            item = self.breadcrumb_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        crumbs = [("🏠 Спрайты", [])]
        if len(self.current_path) >= 1:
            crumbs.append((self.current_path[0], self.current_path[:1]))
        if len(self.current_path) >= 2:
            pos = self.current_path[1]
            crumbs.append((POSITION_LABELS.get(pos, pos), self.current_path[:2]))

        for i, (text, path) in enumerate(crumbs):
            btn = QPushButton(text)
            btn.setFlat(True)
            is_last = (i == len(crumbs) - 1)
            btn.setEnabled(not is_last)
            btn.setStyleSheet(f"""
                QPushButton {{
                    color: {'#ff8c00' if is_last else '#9aa'};
                    font-weight: {'bold' if is_last else 'normal'};
                    border: none; padding: 2px 4px; text-align: left;
                    background: transparent;
                }}
                QPushButton:hover {{ color: #ffa020; }}
                QPushButton:disabled {{ color: #ff8c00; }}
            """)
            btn.clicked.connect(lambda _=None, p=path: self._go_to(p))
            self.breadcrumb_row.addWidget(btn)
            if not is_last:
                sep = QLabel("›")
                sep.setStyleSheet("color:#666;")
                self.breadcrumb_row.addWidget(sep)
        self.breadcrumb_row.addStretch()

    def _refresh_view(self):
        self._rebuild_breadcrumbs()

        for card in self.cards:
            card.setParent(None)
        self.cards.clear()
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.rm:
            self.container.setFixedWidth(200)
            self.container.setFixedHeight(self.thumb_size + ResourceCard.LABEL_HEIGHT + 14)
            return

        count = 0
        if len(self.current_path) == 0:
            for character in self.rm.get_composite_characters():
                card = FolderCard(character, self.thumb_size)
                card.clicked.connect(self._enter)
                self.cards.append(card)
                self.container_layout.addWidget(card)
                count += 1
        elif len(self.current_path) == 1:
            character = self.current_path[0]
            for pos in self.rm.get_composite_positions(character):
                card = FolderCard(POSITION_LABELS.get(pos, pos), self.thumb_size)
                card.folder_name = pos 
                card.clicked.connect(self._enter)
                self.cards.append(card)
                self.container_layout.addWidget(card)
                count += 1
        else:
            character, position = self.current_path[0], self.current_path[1]
            for sprite in self.rm.get_composite_sprites(character, position):
                card = CompositeSpriteCard(sprite, self.rm, self.thumb_size)
                card.clicked.connect(self._on_card_clicked)
                if self.selected_sprite and sprite.full_name == self.selected_sprite.full_name:
                    card.set_selected(True)
                self.cards.append(card)
                self.container_layout.addWidget(card)
                count += 1

        self.container_layout.addStretch()
        w = count * (self.thumb_size + 22) + 10
        self.container.setFixedWidth(max(w, 200))
        self.container.setFixedHeight(self.thumb_size + ResourceCard.LABEL_HEIGHT + 14)
        self._schedule_thumbnails()

    def _schedule_thumbnails(self):
        pending = [c for c in self.cards if isinstance(c, CompositeSpriteCard)]
        batch_size = 3
        def step():
            for _ in range(batch_size):
                if not pending:
                    return
                card = pending.pop(0)
                try:
                    card.load_thumbnail()
                except RuntimeError:
                    pass
            if pending:
                QTimer.singleShot(0, step)

        QTimer.singleShot(0, step)

    def _on_card_clicked(self, sprite: CompositeSprite):
        for card in self.cards:
            if isinstance(card, CompositeSpriteCard):
                card.set_selected(card.sprite is sprite)
        self.selected_sprite = sprite
        self.selection_changed.emit(sprite)

    def _clear_selection(self):
        for card in self.cards:
            if isinstance(card, CompositeSpriteCard):
                card.set_selected(False)
        self.selected_sprite = None
        self.selection_changed.emit(None)

    def _scroll_left(self):
        sb = self.scroll.horizontalScrollBar()
        sb.setValue(sb.value() - (self.thumb_size + 22) * 3)

    def _scroll_right(self):
        sb = self.scroll.horizontalScrollBar()
        sb.setValue(sb.value() + (self.thumb_size + 22) * 3)
