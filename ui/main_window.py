                       
"""
Главное окно приложения
"""
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QGroupBox,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QInputDialog,
    QScrollArea, QFrame, QLineEdit, QDialog, QStyle, QSlider, QStackedWidget,
    QAbstractItemView, QMenu, QColorDialog, QProgressDialog
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QFont, QColor, QBrush, QPainter, QShortcut

from core.models import Project, Scene, SceneNode, NodeType, Character
from core.resource_manager import ResourceManager
from core.project_manager import ProjectManager, project_to_dict, project_from_dict
from core.undo_manager import UndoManager
from core.code_generator import generate_full_script, generate_defines_only
from core.scene_state import compute_state_up_to
from core import presentation_engine

from ui.glass_panel import GlassPanel
from ui.node_editor import NodeEditor
from ui.characters_dialog import CharactersDialog
from ui.code_preview import CodePreviewDialog
from ui.resources_dialog import ResourcesConfigDialog
from ui.scene_preview import ScenePreview, SpriteLayer
from ui.pixmap_cache import get_pixmap, get_composite, invalidate as invalidate_pixmap_cache
from ui.help_dialog import HelpDialog
from ui.resources_download_dialog import ResourcesDownloadDialog
from ui.update_dialog import UpdateCheckThread, UpdateAvailableDialog
from core.app_settings import AppSettings
from core.characters_store import load_global_characters, save_global_characters
from core.tags_store import TagsStore
from core.resource_usage_store import ResourceUsageStore
from ui.dialogue_stats_dialog import DialogueStatsDialog
from ui.find_replace_dialog import FindReplaceDialog
from core.custom_node_templates import CustomNodeTemplateStore
from ui.custom_node_templates_dialog import CustomNodeTemplatesDialog
from ui.presentation_window import PresentationWindow
from ui.screenplay_dialog import ScreenplayExportImportDialog
from ui.tags_dialog import TagsManagerDialog
from ui.import_paths_dialog import ImportPathsDialog
from core.hotkeys_store import HotkeyStore
from core.autosave import write_autosave, read_autosave, has_autosave, clear_autosave
from ui.editor_settings_dialog import EditorSettingsDialog
from ui.history_panel_dialog import HistoryPanelDialog
from ui.diff_preview_dialog import DiffPreviewDialog
from ui.split_export_dialog import SplitExportDialog
from ui.command_palette import CommandPaletteDialog, collect_commands_from_menubar
from ui.git_dialog import GitPanelDialog
from ui.import_script_dialog import ImportScriptDialog
from PyQt6.QtGui import QPixmap


from core.paths import get_base_dir

BASE_DIR = get_base_dir()

DEFAULT_TAG_COLORS = ["#ff5b3d", "#ff8c3d", "#ffd23f", "#4cd97b", "#3fb6ff", "#a78bfa", "#ff6fb0", "#8a8a94"]


def _color_icon(hex_color: str) -> QIcon:
    pm = QPixmap(14, 14)
    pm.fill(QColor(hex_color))
    return QIcon(pm)


def _row_swatch_icon(node_color: Optional[str], group_color: Optional[str]) -> QIcon:
    """Полоска цвета группы слева + квадрат цвета метки ноды - рисуется в
    пиксмапе, а не через QSS/палитру, поэтому видна независимо от темы
    (setBackground на QListWidgetItem не работает из-за стилей ::item)."""
    if not node_color and not group_color:
        return QIcon()
    pm = QPixmap(26, 16)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    if group_color:
        painter.setBrush(QColor(group_color))
        painter.drawRoundedRect(0, 1, 6, 14, 2, 2)
    if node_color:
        painter.setBrush(QColor(node_color))
        painter.drawRoundedRect(10, 2, 12, 12, 3, 3)
    painter.end()
    return QIcon(pm)


def _group_folder_icon(color: str, collapsed: bool) -> QIcon:
    """Единая (нарисованная, а не эмодзи-символ) иконка папки-группы - тот же
    визуальный язык, что и у цветовых меток нод, чтобы не мешать разные
    системы обозначений. Открытая/закрытая форма отличает свёрнутое
    состояние без текстовых стрелок."""
    pm = QPixmap(20, 16)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(color))
    if collapsed:
        p.drawRoundedRect(1, 5, 18, 9, 2, 2)
        p.drawRoundedRect(1, 2, 8, 5, 2, 2)
    else:
        p.drawRoundedRect(1, 3, 18, 11, 2, 2)
        p.drawRoundedRect(1, 1, 8, 4, 2, 2)
    p.end()
    return QIcon(pm)


_NODE_TYPE_HINTS = {
    NodeType.DIALOGUE: "💬 Реплика персонажа - станет строкой вида: имя_переменной \"текст\"",
    NodeType.NARRATION: "📖 Повествование от автора - строка текста без указания персонажа",
    NodeType.SHOW_BG: "🖼 Показывает фон (show bg с опциональным переходом)",
    NodeType.SCENE: "🎬 Полная смена сцены (scene - сбрасывает все показанные спрайты)",
    NodeType.SHOW_SPRITE: "🧍 Показывает спрайт персонажа в заданной позиции",
    NodeType.HIDE_SPRITE: "🚫 Скрывает ранее показанный спрайт",
    NodeType.SHOW_CG: "🖼 Показывает CG-иллюстрацию",
    NodeType.HIDE_CG: "🗑 Скрывает CG-иллюстрацию",
    NodeType.PLAY_MUSIC: "🎵 Запускает фоновую музыку (play music)",
    NodeType.STOP_MUSIC: "🔇 Останавливает музыку",
    NodeType.PLAY_SOUND: "🔊 Проигрывает звуковой эффект один раз",
    NodeType.PLAY_AMBIENCE: "🌬 Запускает фоновый эмбиенс-звук",
    NodeType.STOP_AMBIENCE: "🔇 Останавливает эмбиенс",
    NodeType.LABEL: "🏷 Метка - точка, на которую можно перейти через jump",
    NodeType.JUMP: "➡ Безусловный переход на другую метку",
    NodeType.MENU: "📋 Меню выбора для игрока",
    NodeType.PYTHON: "🐍 Произвольный Python-код ($ или python:)",
    NodeType.PAUSE: "⏸ Пауза (по времени или до клика игрока)",
    NodeType.RETURN: "⏹ Возврат из label (return)",
    NodeType.COMMENT: "# Комментарий - не попадает в игру, только для заметок в редакторе",
    NodeType.WINDOW: "🪟 Управление текстовым окном (window show/hide/auto)",
    NodeType.WITH_TRANSITION: "🎞 Отдельная команда перехода (with transition)",
    NodeType.RAW: "🧩 Нераспознанный при импорте код - сохранён как есть",
    NodeType.CUSTOM: "🧬 Пользовательская нода по вашему шаблону (Проект → Шаблоны пользовательских нод)",
}


class _SpellcheckWorker(QThread):
    """Сканирование реплик всего проекта в фоне - на больших проектах
    (особенно если установлен pyspellchecker) синхронный обход в GUI-потоке
    ощущался как зависание приложения без какой-либо обратной связи."""
    progress = pyqtSignal(int, int)
    finished_scan = pyqtSignal(list)

    def __init__(self, project, parent=None, extra_whitelist=None):
        super().__init__(parent)
        self.project = project
        self._cancelled = False
        self.extra_whitelist = extra_whitelist

    def cancel(self):
        self._cancelled = True

    def run(self):
        from core.spellcheck_scanner import scan_project_spelling
        last_emitted = -1

        def on_progress(done, total):
            nonlocal last_emitted
                                                                       
                                                          
            step = max(1, total // 200) if total else 1
            if done - last_emitted >= step or done == total:
                last_emitted = done
                self.progress.emit(done, total)

        results = scan_project_spelling(
            self.project, on_progress=on_progress, should_cancel=lambda: self._cancelled,
            extra_whitelist=self.extra_whitelist,
        )
        self.finished_scan.emit(results)


class SceneListPanel(QWidget):
    """Левая панель: список сцен и узлов"""
    scene_selected = pyqtSignal(int)              
    node_selected = pyqtSignal(int, int)                        
    node_order_changed = pyqtSignal()
    before_change = pyqtSignal(str)
    branch_back_requested = pyqtSignal()
    present_from_here_requested = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.project: Optional[Project] = None
        self._current_scene = 0
        self._row_to_node = {}
        self._node_to_row = {}
        self._header_rows = {}
                                                                           
                                                                        
                                                                  
        self._branch_scene: Optional[Scene] = None
        self._setup_ui()

    def is_in_branch_mode(self) -> bool:
        return self._branch_scene is not None

    def enter_branch(self, scene: Scene, label: str):
        """Переключает панель на редактирование ветки меню как обычной сцены."""
        self._branch_scene = scene
        self._branch_label.setText(label)
        self._branch_bar.setVisible(True)
        self.scenes_group.setEnabled(False)
        self._rebuild_nodes()

    def exit_branch(self):
        self._branch_scene = None
        self._branch_bar.setVisible(False)
        self.scenes_group.setEnabled(True)
        self._rebuild_nodes()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

                     
        scenes_group = QGroupBox("Сцены")
        self.scenes_group = scenes_group
        sg_layout = QVBoxLayout(scenes_group)
        sg_layout.setContentsMargins(4, 8, 4, 4)

        self.scene_list = QListWidget()
        self.scene_list.setMaximumHeight(120)
        self.scene_list.currentRowChanged.connect(self._on_scene_changed)
        sg_layout.addWidget(self.scene_list)

        sc_btn_row = QHBoxLayout()
        btn_add_scene = QPushButton("Новый label")
        btn_add_scene.setFixedHeight(36)
        btn_add_scene.clicked.connect(self._add_scene)
        btn_rename_scene = QPushButton()
        btn_rename_scene.setFixedSize(36, 36)
        btn_rename_scene.setObjectName("btn_secondary")
        btn_rename_scene.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        btn_rename_scene.setToolTip("Переименовать сцену")
        btn_rename_scene.clicked.connect(self._rename_scene)
        btn_del_scene = QPushButton()
        btn_del_scene.setFixedSize(36, 36)
        btn_del_scene.setObjectName("btn_danger")
        btn_del_scene.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton))
        btn_del_scene.setToolTip("Удалить сцену")
        btn_del_scene.clicked.connect(self._del_scene)
        sc_btn_row.addWidget(btn_add_scene, 1)
        sc_btn_row.addWidget(btn_rename_scene)
        sc_btn_row.addWidget(btn_del_scene)
        sg_layout.addLayout(sc_btn_row)

        layout.addWidget(scenes_group)

                                                
        self._branch_bar = QFrame()
        self._branch_bar.setStyleSheet(
            "QFrame { background:#2d4a3a; border-radius:4px; }"
        )
        bb_layout = QHBoxLayout(self._branch_bar)
        bb_layout.setContentsMargins(6, 4, 6, 4)
        self._branch_label = QLabel("Ветка меню")
        self._branch_label.setWordWrap(True)
        self._branch_label.setStyleSheet("color:#6fd68f; font-size:11px; font-weight:bold;")
        btn_branch_back = QPushButton("← Назад к сцене")
        btn_branch_back.setStyleSheet(
            "QPushButton { background:#1e1e1e; color:#ddd; border-radius:4px; padding:4px 8px; }"
            "QPushButton:hover { background:#333; }"
        )
        btn_branch_back.clicked.connect(self.branch_back_requested.emit)
        bb_layout.addWidget(self._branch_label, 1)
        bb_layout.addWidget(btn_branch_back)
        self._branch_bar.setVisible(False)
        layout.addWidget(self._branch_bar)

                             
        nodes_group = QGroupBox("Элементы сцены")
        ng_layout = QVBoxLayout(nodes_group)
        ng_layout.setContentsMargins(4, 4, 4, 4)

        search_row = QHBoxLayout()
        self.node_search = QLineEdit()
        self.node_search.setPlaceholderText("🔎 Поиск по репликам / спрайтам / персонажам...")
        self.node_search.textChanged.connect(self._on_search_text)
        self.node_search.returnPressed.connect(self._search_next)
        search_row.addWidget(self.node_search, 1)
        self.search_status_lbl = QLabel("")
        self.search_status_lbl.setObjectName("search_status_lbl")
        search_row.addWidget(self.search_status_lbl)
        ng_layout.addLayout(search_row)

        self.node_list = QListWidget()
        self.node_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.node_list.currentRowChanged.connect(self._on_node_changed)
        self.node_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.node_list.customContextMenuRequested.connect(self._show_node_context_menu)
        self.node_list.itemDoubleClicked.connect(self._on_node_item_double_clicked)
        ng_layout.addWidget(self.node_list)

        sc_copy = QShortcut(QKeySequence.StandardKey.Copy, self.node_list,
                            activated=lambda: self._copy_nodes(self._selected_node_rows() or
                                                                 ([self._current_node_index()] if self._current_node_index() >= 0 else [])))
        sc_paste = QShortcut(QKeySequence.StandardKey.Paste, self.node_list,
                             activated=lambda: self._paste_clipboard_after(self._current_node_index()))
        sc_del = QShortcut(QKeySequence.StandardKey.Delete, self.node_list, activated=self._del_node)
        for sc in (sc_copy, sc_paste, sc_del):
            sc.setContext(Qt.ShortcutContext.WidgetShortcut)

        self._search_matches = []
        self._search_pos = -1

        nd_btn_row = QHBoxLayout()
        btn_add_node = QPushButton("Добавить")
        btn_add_node.setFixedHeight(36)
        btn_add_node.clicked.connect(self._add_node)

        btn_dup = QPushButton()
        btn_dup.setFixedSize(36, 36)
        btn_dup.setObjectName("btn_secondary")
        btn_dup.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        btn_dup.setToolTip("Дублировать")
        btn_dup.clicked.connect(self._dup_node)

        btn_up = QPushButton()
        btn_up.setFixedSize(36, 36)
        btn_up.setObjectName("btn_secondary")
        btn_up.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        btn_up.setToolTip("Переместить вверх")
        btn_up.clicked.connect(self._move_up)

        btn_down = QPushButton()
        btn_down.setFixedSize(36, 36)
        btn_down.setObjectName("btn_secondary")
        btn_down.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
        btn_down.setToolTip("Переместить вниз")
        btn_down.clicked.connect(self._move_down)

        btn_del_node = QPushButton()
        btn_del_node.setFixedSize(36, 36)
        btn_del_node.setObjectName("btn_danger")
        btn_del_node.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton))
        btn_del_node.setToolTip("Удалить")
        btn_del_node.clicked.connect(self._del_node)

        nd_btn_row.addWidget(btn_add_node, 1)
        nd_btn_row.addWidget(btn_dup)
        nd_btn_row.addWidget(btn_up)
        nd_btn_row.addWidget(btn_down)
        nd_btn_row.addWidget(btn_del_node)
        ng_layout.addLayout(nd_btn_row)

        layout.addWidget(nodes_group, 1)

    def load_project(self, project: Project):
        self.project = project
        self._rebuild_scenes()

    def _rebuild_scenes(self):
        self.scene_list.blockSignals(True)
        self.scene_list.clear()
        if self.project:
            for s in self.project.scenes:
                self.scene_list.addItem(s.name)
            if self.project.scenes:
                idx = min(self._current_scene, len(self.project.scenes) - 1)
                self.scene_list.setCurrentRow(idx)
        self.scene_list.blockSignals(False)
        self._rebuild_nodes()

    def _group_for_node_id(self, node_id: str) -> Optional["NodeGroup"]:
        scene = self._get_current_scene()
        if not scene:
            return None
        for g in scene.groups:
            if node_id in g.node_ids:
                return g
        return None

    def _style_item(self, item: QListWidgetItem, node, i: int, scene):
        prefix = "⚠ " if node.import_warning else ""
        item.setText(f"  {i+1:02d}  {prefix}{node.preview_text()}")
        grp = self._group_for_node_id(node.node_id)
        item.setIcon(_row_swatch_icon(node.color_tag, grp.color if grp else None))
        tooltip = _NODE_TYPE_HINTS.get(node.node_type, "") + "\n\n" + node.preview_text()
        if node.import_warning:
            tooltip += f"\n\n⚠ {node.import_warning}"
            item.setForeground(QColor("#ffb84d"))
        item.setToolTip(tooltip)

    def _current_node_index(self) -> int:
        """Индекс ноды в scene.nodes для текущей выбранной строки списка.
        Строка списка и индекс ноды больше НЕ совпадают: у групп есть
        отдельная строка-заголовок, которая нодой не является."""
        row = self.node_list.currentRow()
        idx = self._row_to_node.get(row, -1)
        return idx if idx is not None else -1

    def _rebuild_nodes(self):
        self.node_list.blockSignals(True)
        prev_idx = self._current_node_index()
        self.node_list.clear()
        self._row_to_node = {}
        self._node_to_row = {}
        self._header_rows = {}
        scene = self._get_current_scene()
        if scene:
            rendered_groups = set()
            for i, node in enumerate(scene.nodes):
                grp = self._group_for_node_id(node.node_id)
                if grp is not None and grp.group_id not in rendered_groups:
                    rendered_groups.add(grp.group_id)
                    count = sum(1 for n in scene.nodes if n.node_id in grp.node_ids)
                    header = QListWidgetItem(self._group_header_text(grp, count))
                    header.setIcon(_group_folder_icon(grp.color, grp.collapsed))
                    hf = header.font()
                    hf.setBold(True)
                    header.setFont(hf)
                    header.setFlags(header.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    self.node_list.addItem(header)
                    self._header_rows[self.node_list.count() - 1] = grp.group_id

                item = QListWidgetItem("")
                self._style_item(item, node, i, scene)
                self.node_list.addItem(item)
                row = self.node_list.count() - 1
                self._row_to_node[row] = i
                self._node_to_row[i] = row

            self._apply_group_collapse_visibility(scene)
            if scene.nodes:
                target_idx = prev_idx if 0 <= prev_idx < len(scene.nodes) else 0
                self.node_list.setCurrentRow(self._node_to_row.get(target_idx, 0))
        self.node_list.blockSignals(False)
        self._apply_search_highlight()

    def _group_header_text(self, grp, count: int) -> str:
        suffix = "   (свёрнуто)" if grp.collapsed else ""
        word = "нода" if count == 1 else ("ноды" if 2 <= count <= 4 else "нод")
        return f"{grp.title}   ·   {count} {word}{suffix}"

    def _apply_group_collapse_visibility(self, scene):
        for g in scene.groups:
            if not g.collapsed:
                continue
            for i, n in enumerate(scene.nodes):
                if n.node_id in g.node_ids:
                    row = self._node_to_row.get(i)
                    if row is not None:
                        self.node_list.item(row).setHidden(True)

    def refresh_current_node_text(self):
        scene = self._get_current_scene()
        idx = self._current_node_index()
        if scene and 0 <= idx < len(scene.nodes):
            row = self._node_to_row.get(idx)
            if row is not None:
                self._style_item(self.node_list.item(row), scene.nodes[idx], idx, scene)

    def _effective_scene_idx(self) -> int:
        """scene_idx, передаваемый наружу через node_selected: обычный индекс
        сцены проекта, либо -2 как признак 'мы сейчас внутри ветки меню' -
        MainWindow в этом случае берёт сцену через _get_current_scene(), а не
        по индексу в project.scenes."""
        if self._branch_scene is not None:
            return -2
        return self.scene_list.currentRow()

    def _select_node_row(self, idx: int):
        """Выбирает ноду по её индексу в scene.nodes (НЕ строку списка) и
        ГАРАНТИРОВАННО уведомляет об этом, даже если currentRow уже указывает
        туда же (Qt в этом случае не эмиттит currentRowChanged сам, а нам
        нужно прогрузить узел в редактор)."""
        row = self._node_to_row.get(idx, -1)
        if row < 0:
            return
        if self.node_list.currentRow() == row:
            self.node_selected.emit(self._effective_scene_idx(), idx)
        else:
            self.node_list.setCurrentRow(row)

    def notify_current_selection(self):
        """Принудительно уведомляет внешний код о текущей выбранной сцене/узле.
        Нужно вызывать после операций, где список перестраивается с заблокированными
        сигналами (Qt не уведомит сам, если индекс строки не изменился)."""
        node_idx = self._current_node_index()
        self.node_selected.emit(self._effective_scene_idx(), node_idx)

    def _get_current_scene(self) -> Optional[Scene]:
        if self._branch_scene is not None:
            return self._branch_scene
        if not self.project:
            return None
        idx = self.scene_list.currentRow()
        if 0 <= idx < len(self.project.scenes):
            return self.project.scenes[idx]
        return None

    def _on_scene_changed(self, idx: int):
        self._current_scene = idx
        self._rebuild_nodes()
        self.scene_selected.emit(idx)

    def _on_node_changed(self, row: int):
        idx = self._row_to_node.get(row)
        if idx is None:
            return
        self.node_selected.emit(self._effective_scene_idx(), idx)

                            

    def _add_scene(self):
        if not self.project:
            return
        name, ok = QInputDialog.getText(self, "Новая сцена", "Название:")
        if ok and name.strip():
            self.before_change.emit(f"Добавлена сцена «{name.strip()}»")
            self.project.scenes.append(Scene(name=name.strip()))
            self._rebuild_scenes()
            self.scene_list.setCurrentRow(len(self.project.scenes) - 1)
            self.notify_current_selection()

    def _rename_scene(self):
        scene = self._get_current_scene()
        if not scene:
            return
        name, ok = QInputDialog.getText(self, "Переименовать", "Новое название:", text=scene.name)
        if ok and name.strip():
            self.before_change.emit(f"Сцена «{scene.name}» переименована в «{name.strip()}»")
            scene.name = name.strip()
            self._rebuild_scenes()

    def _del_scene(self):
        if not self.project:
            return
        idx = self.scene_list.currentRow()
        if idx < 0:
            return
        if len(self.project.scenes) <= 1:
            QMessageBox.warning(self, "Нельзя", "Должна быть хотя бы одна сцена")
            return
        reply = QMessageBox.question(self, "Удалить сцену",
                                     f"Удалить сцену «{self.project.scenes[idx].name}»?")
        if reply == QMessageBox.StandardButton.Yes:
            self.before_change.emit(f"Удалена сцена «{self.project.scenes[idx].name}»")
            self.project.scenes.pop(idx)
            self._current_scene = max(0, idx - 1)
            self._rebuild_scenes()
            self.notify_current_selection()

                           

    def add_node_of_type(self, node_type: NodeType, label: str = "Добавлена нода"):
        scene = self._get_current_scene()
        if not scene:
            return
        node = SceneNode(node_type=node_type)
        idx = self._current_node_index()
        self.before_change.emit(label)
        if idx < 0:
            scene.nodes.append(node)
            new_idx = len(scene.nodes) - 1
        else:
            scene.nodes.insert(idx + 1, node)
            new_idx = idx + 1
        self._rebuild_nodes()
        self._select_node_row(new_idx)

    def _add_node(self):
        self.add_node_of_type(NodeType.DIALOGUE, "Добавлена нода: 💬 Реплика")

    def _dup_node(self):
        scene = self._get_current_scene()
        if not scene:
            return
        idx = self._current_node_index()
        if 0 <= idx < len(scene.nodes):
            import copy, uuid
            self.before_change.emit(f"Дублирована нода: {scene.nodes[idx].preview_text()[:60]}")
            dup = copy.deepcopy(scene.nodes[idx])
            dup.node_id = str(uuid.uuid4())[:8]
            scene.nodes.insert(idx + 1, dup)
            self._rebuild_nodes()
            self._select_node_row(idx + 1)

    def _move_up(self):
        scene = self._get_current_scene()
        if not scene:
            return
        idx = self._current_node_index()
        if idx > 0:
            self.before_change.emit(f"Нода перемещена вверх: {scene.nodes[idx].preview_text()[:60]}")
            scene.nodes[idx], scene.nodes[idx-1] = scene.nodes[idx-1], scene.nodes[idx]
            self._rebuild_nodes()
            self._select_node_row(idx - 1)
            self.node_order_changed.emit()

    def _move_down(self):
        scene = self._get_current_scene()
        if not scene:
            return
        idx = self._current_node_index()
        if 0 <= idx < len(scene.nodes) - 1:
            self.before_change.emit(f"Нода перемещена вниз: {scene.nodes[idx].preview_text()[:60]}")
            scene.nodes[idx], scene.nodes[idx+1] = scene.nodes[idx+1], scene.nodes[idx]
            self._rebuild_nodes()
            self._select_node_row(idx + 1)
            self.node_order_changed.emit()

    def _del_node(self):
        scene = self._get_current_scene()
        if not scene:
            return
        idx = self._current_node_index()
        if 0 <= idx < len(scene.nodes):
            self.before_change.emit(f"Удалена нода: {scene.nodes[idx].preview_text()[:60]}")
            deleted_id = scene.nodes[idx].node_id
            scene.nodes.pop(idx)
            for g in scene.groups:
                if deleted_id in g.node_ids:
                    g.node_ids.remove(deleted_id)
            scene.groups = [g for g in scene.groups if g.node_ids]
            self._rebuild_nodes()
            self.notify_current_selection()

                         

    def set_nodes_color(self, rows: list, color: Optional[str]):
        scene = self._get_current_scene()
        if not scene:
            return
        self.before_change.emit(f"Изменён цвет {len(rows)} нод(ы)")
        for r in rows:
            if 0 <= r < len(scene.nodes):
                scene.nodes[r].color_tag = color
        self._rebuild_nodes()

    def duplicate_branch(self, row: int):
        """Дублирует цепочку узлов начиная с row до ближайшего label/return
        (не включая её) или до конца сцены - то есть весь текущий 'блок
        диалога/ветки', а не одну ноду."""
        scene = self._get_current_scene()
        if not scene or not (0 <= row < len(scene.nodes)):
            return
        end = row
        for i in range(row + 1, len(scene.nodes)):
            if scene.nodes[i].node_type in (NodeType.LABEL, NodeType.RETURN):
                break
            end = i
        import copy, uuid
        self.before_change.emit(f"Дублирована ветка ({end - row + 1} нод, начиная с «{scene.nodes[row].preview_text()[:40]}»)")
        chunk = [copy.deepcopy(n) for n in scene.nodes[row:end + 1]]
        for n in chunk:
            n.node_id = str(uuid.uuid4())[:8]
        for offset, n in enumerate(chunk):
            scene.nodes.insert(end + 1 + offset, n)
        self._rebuild_nodes()
        self._select_node_row(end + 1)

    def paste_nodes_after(self, row: int, clip_data: list):
        scene = self._get_current_scene()
        if not scene:
            return
        from core.project_manager import node_from_dict
        import uuid
        self.before_change.emit(f"Вставлено нод: {len(clip_data)}")
        insert_at = row + 1 if row >= 0 else len(scene.nodes)
        for offset, d in enumerate(clip_data):
            node = node_from_dict(d, new_id=True)
            scene.nodes.insert(insert_at + offset, node)
        self._rebuild_nodes()
        self._select_node_row(insert_at)

    def create_group(self, rows: list, title: str):
        scene = self._get_current_scene()
        if not scene:
            return
        node_ids = [scene.nodes[r].node_id for r in rows if 0 <= r < len(scene.nodes)]
        if not node_ids:
            return
        from core.models import NodeGroup
        self.before_change.emit(f"Создана группа «{title}» ({len(node_ids)} нод)")
        scene.groups.append(NodeGroup(title=title, node_ids=node_ids))
        self._rebuild_nodes()

    def ungroup(self, group_id: str):
        scene = self._get_current_scene()
        if not scene:
            return
        old_title = next((g.title for g in scene.groups if g.group_id == group_id), "")
        self.before_change.emit(f"Разгруппировано: «{old_title}»")
        scene.groups = [g for g in scene.groups if g.group_id != group_id]
        self._rebuild_nodes()

    def toggle_group_collapsed(self, group_id: str):
        scene = self._get_current_scene()
        if not scene:
            return
        grp = next((g for g in scene.groups if g.group_id == group_id), None)
        if not grp:
            return
        self.before_change.emit(f"{'Свёрнута' if not grp.collapsed else 'Развёрнута'} группа «{grp.title}»")
        grp.collapsed = not grp.collapsed
        self._rebuild_nodes()

    def rename_group(self, group_id: str, title: str):
        scene = self._get_current_scene()
        if not scene:
            return
        grp = next((g for g in scene.groups if g.group_id == group_id), None)
        if not grp:
            return
        self.before_change.emit(f"Группа «{grp.title}» переименована в «{title}»")
        grp.title = title
        self._rebuild_nodes()

    def recolor_group(self, group_id: str, color: str):
        scene = self._get_current_scene()
        if not scene:
            return
        grp = next((g for g in scene.groups if g.group_id == group_id), None)
        if not grp:
            return
        self.before_change.emit(f"Изменён цвет группы «{grp.title}»")
        grp.color = color
        self._rebuild_nodes()

                                          

    def _selected_node_rows(self) -> list:
        """Индексы (в scene.nodes) выбранных строк списка, заголовки групп
        игнорируются (они не выбираемы, но проверка на всякий случай)."""
        rows = {self.node_list.row(it) for it in self.node_list.selectedItems()}
        return sorted(self._row_to_node[r] for r in rows if r in self._row_to_node)

    def _on_node_item_double_clicked(self, item: QListWidgetItem):
        row = self.node_list.row(item)
        gid = self._header_rows.get(row)
        if gid is not None:
            self.toggle_group_collapsed(gid)

    def _show_node_context_menu(self, pos):
        scene = self._get_current_scene()
        if not scene:
            return
        item = self.node_list.itemAt(pos)
        row = self.node_list.row(item) if item else -1
        header_gid = self._header_rows.get(row) if row >= 0 else None
        clicked_idx = self._row_to_node.get(row, -1) if row >= 0 else -1

        menu = QMenu(self)

        if header_gid is not None:
            grp = next((g for g in scene.groups if g.group_id == header_gid), None)
            if grp:
                act_toggle = menu.addAction("Свернуть/развернуть группу")
                act_toggle.triggered.connect(lambda: self.toggle_group_collapsed(grp.group_id))
                act_rn = menu.addAction("Переименовать группу...")
                act_rn.triggered.connect(lambda: self._rename_group_dialog(grp.group_id))
                act_col = menu.addMenu("Цвет группы")
                for c in DEFAULT_TAG_COLORS:
                    a = act_col.addAction("")
                    a.setIcon(_color_icon(c))
                    a.triggered.connect(lambda checked=False, col=c: self.recolor_group(grp.group_id, col))
                act_ungroup = menu.addAction("Разгруппировать")
                act_ungroup.triggered.connect(lambda: self.ungroup(grp.group_id))
            menu.exec(self.node_list.mapToGlobal(pos))
            return

        rows = self._selected_node_rows()
        if clicked_idx >= 0 and clicked_idx not in rows:
            rows = [clicked_idx]
            target_row = self._node_to_row.get(clicked_idx)
            if target_row is not None:
                self.node_list.setCurrentRow(target_row)

        act_color = menu.addMenu("Цвет метки ноды")
        for c in DEFAULT_TAG_COLORS:
            a = act_color.addAction("")
            a.setIcon(_color_icon(c))
            a.triggered.connect(lambda checked=False, col=c, rows=rows: self.set_nodes_color(rows, col))
        act_color.addSeparator()
        act_clear_color = act_color.addAction("Без метки")
        act_clear_color.triggered.connect(lambda checked=False, rows=rows: self.set_nodes_color(rows, None))

        menu.addSeparator()
        act_copy = menu.addAction("Копировать (Ctrl+C)")
        act_copy.setEnabled(bool(rows))
        act_copy.triggered.connect(lambda: self._copy_nodes(rows))
        act_paste = menu.addAction("Вставить после (Ctrl+V)")
        act_paste.setEnabled(self._has_clipboard_nodes())
        paste_after_idx = clicked_idx if clicked_idx >= 0 else self._current_node_index()
        act_paste.triggered.connect(lambda: self._paste_clipboard_after(paste_after_idx))

        if clicked_idx >= 0:
            act_dup_branch = menu.addAction("Дублировать блок диалога (до label/return/конца)")
            act_dup_branch.triggered.connect(lambda: self.duplicate_branch(clicked_idx))

            if not self.is_in_branch_mode():
                menu.addSeparator()
                act_present_from = menu.addAction("▶ Запустить прогон отсюда")
                act_present_from.triggered.connect(
                    lambda: self.present_from_here_requested.emit(self.scene_list.currentRow(), clicked_idx)
                )

        if len(rows) >= 2:
            menu.addSeparator()
            act_group = menu.addAction(f"Сгруппировать выбранные ноды ({len(rows)})")
            act_group.triggered.connect(lambda: self._make_group_dialog(rows))

        menu.exec(self.node_list.mapToGlobal(pos))

    def _rename_group_dialog(self, group_id: str):
        scene = self._get_current_scene()
        grp = next((g for g in (scene.groups if scene else []) if g.group_id == group_id), None)
        if not grp:
            return
        title, ok = QInputDialog.getText(self, "Название группы", "Название:", text=grp.title)
        if ok and title.strip():
            self.rename_group(group_id, title.strip())

    def _make_group_dialog(self, rows: list):
        if rows != list(range(rows[0], rows[-1] + 1)):
            QMessageBox.warning(self, "Нельзя сгруппировать",
                                 "Можно сгруппировать только идущие подряд ноды.")
            return
        title, ok = QInputDialog.getText(self, "Новая группа", "Название группы (акт/глава):", text="Акт")
        if ok and title.strip():
            self.create_group(rows, title.strip())

                                                                                

    def _copy_nodes(self, rows: list):
        scene = self._get_current_scene()
        if not scene or not rows:
            return
        from core.project_manager import node_to_dict
        import json
        data = [node_to_dict(scene.nodes[r]) for r in rows if 0 <= r < len(scene.nodes)]
        if not data:
            return
        try:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(json.dumps({"renpy_editor_nodes": data}, ensure_ascii=False))
        except Exception:
            pass

    def _has_clipboard_nodes(self) -> bool:
        return self._read_clipboard_nodes() is not None

    def _read_clipboard_nodes(self):
        try:
            from PyQt6.QtWidgets import QApplication
            import json
            txt = QApplication.clipboard().text()
            data = json.loads(txt)
            nodes = data.get("renpy_editor_nodes")
            if isinstance(nodes, list) and nodes:
                return nodes
        except Exception:
            pass
        return None

    def _paste_clipboard_after(self, row: int):
        data = self._read_clipboard_nodes()
        if not data:
            return
        self.paste_nodes_after(row, data)

                                             

    def _on_search_text(self, text: str):
        scene = self._get_current_scene()
        text = text.strip().lower()
        self._search_matches = []
        self._search_pos = -1
        if text and scene:
            for r, n in enumerate(scene.nodes):
                haystack = " ".join(filter(None, [
                    n.text, n.character_var, n.sprite_var, n.label_name,
                    n.jump_target, n.bg_var, n.cg_var, n.menu_prompt,
                ])).lower()
                if text in haystack:
                    self._search_matches.append(r)
        self.search_status_lbl.setText(f"{len(self._search_matches)} совп." if text else "")
        self._apply_search_highlight()
        if self._search_matches:
            self._search_pos = 0
            self._goto_search_match()

    def _search_next(self):
        if not self._search_matches:
            return
        self._search_pos = (self._search_pos + 1) % len(self._search_matches)
        self._goto_search_match()

    def _goto_search_match(self):
        idx = self._search_matches[self._search_pos]
        scene = self._get_current_scene()
        grp = self._group_for_node_id(scene.nodes[idx].node_id) if scene else None
        if grp is not None and grp.collapsed:
            grp.collapsed = False
            self._rebuild_nodes()
        self._select_node_row(idx)
        row = self._node_to_row.get(idx)
        if row is not None:
            self.node_list.scrollToItem(self.node_list.item(row))
        self.search_status_lbl.setText(f"{self._search_pos + 1}/{len(self._search_matches)}")

    def _apply_search_highlight(self):
        match_rows = {self._node_to_row.get(m) for m in self._search_matches}
        match_rows.discard(None)
        for r in range(self.node_list.count()):
            item = self.node_list.item(r)
            f = item.font()
            f.setBold(r in match_rows)
            item.setFont(f)


class ScenePreviewPanel(QWidget):
    """Правая панель: живой предпросмотр текущего шага сцены"""
    sprite_position_changed = pyqtSignal(float)
    sprite_node_deleted = pyqtSignal()                                                                                        

    def __init__(self):
        super().__init__()
        self.rm: Optional[ResourceManager] = None
        self.project: Optional[Project] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Предпросмотр сцены")
        title.setStyleSheet("color:#ff8c3d; font-size:13px; font-weight:600; padding:4px;")
        layout.addWidget(title)

        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel("Масштаб:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(50, 150)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(160)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        zoom_row.addWidget(self.zoom_slider)
        self.zoom_lbl = QLabel("100%")
        self.zoom_lbl.setFixedWidth(40)
        self.zoom_lbl.setStyleSheet("color:#a8a8b3; font-size:11px;")
        zoom_row.addWidget(self.zoom_lbl)
        zoom_row.addStretch()
        layout.addLayout(zoom_row)

        preview_wrap = GlassPanel(self, blur_radius=36, border_radius=14)
        pw_layout = QVBoxLayout(preview_wrap)
        pw_layout.setContentsMargins(6, 6, 6, 6)

        self.preview = ScenePreview()

        self.preview_scroll = QScrollArea()
        preview_scroll = self.preview_scroll
        preview_scroll.setWidgetResizable(False)
        preview_scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        preview_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        preview_scroll.setWidget(self.preview)
        preview_scroll.setFixedHeight(self.preview.height() + 4)
        pw_layout.addWidget(preview_scroll)
        layout.addWidget(preview_wrap, 0, Qt.AlignmentFlag.AlignTop)

        self.hint_lbl = QLabel("Спрайт можно тащить мышью, чтобы сдвинуть, или кликнуть по нему (без перетаскивания), чтобы убрать со сцены.")
        self.hint_lbl.setWordWrap(True)
        self.hint_lbl.setStyleSheet("color:#75757f; font-size:10px; padding:2px 4px;")
        layout.addWidget(self.hint_lbl)

        self.step_lbl = QLabel("")
        self.step_lbl.setWordWrap(True)
        self.step_lbl.setStyleSheet("color:#a8a8b3; font-size:11px; padding:4px;")
        layout.addWidget(self.step_lbl)

        layout.addStretch()

        self.preview.sprite_moved.connect(self._on_sprite_dragged)
        self.preview.sprite_delete_requested.connect(self._on_sprite_delete_requested)
        self.preview.zoom_step_requested.connect(self._on_preview_zoom_wheel)
        self._current_node: Optional[SceneNode] = None
        self._current_scene: Optional[Scene] = None
        self._current_node_index: int = -1
        self.before_delete_cb = None                                                               

    def set_context(self, rm: ResourceManager, project: Project):
        self.rm = rm
        self.project = project

    def _on_zoom_changed(self, value: int):
        self.zoom_lbl.setText(f"{value}%")
        self.preview.set_scale(value / 100)
        self.preview_scroll.setFixedHeight(self.preview.height() + 4)

    def _on_preview_zoom_wheel(self, steps: int):
        step_pct = 10 * steps
        new_val = max(self.zoom_slider.minimum(),
                       min(self.zoom_slider.maximum(), self.zoom_slider.value() + step_pct))
        self.zoom_slider.setValue(new_val)

    def _resolve_path(self, var: str) -> Optional[str]:
        if not var or self.rm is None:
            return None
        entry = self.rm.find_by_var(var)
        return entry.abs_path if entry else None

    def show_state(self, scene: Optional[Scene], node_index: int, project: Optional[Project] = None):
        """Отображает визуальное состояние сцены на момент узла node_index"""
        if project is not None:
            self.project = project
        self._current_scene = scene
        self._current_node_index = node_index
        if not scene or node_index < 0 or node_index >= len(scene.nodes):
            self.preview.set_background(None)
            self.preview.set_sprites([])
            self.preview.set_dialogue("", "", None)
            self.preview.set_nvl_mode(False)
            self.preview.set_nvl_history([])
            self._current_node = None
            self.step_lbl.setText("Нет выбранного шага сцены.")
            return

        state = compute_state_up_to(scene, node_index, rm=self.rm)
        self._current_node = scene.nodes[node_index]

                                                 
        bg_path = self._resolve_path(state.cg_var) or self._resolve_path(state.bg_var)
        self.preview.set_background(bg_path)

        layers = []
        for sprite in state.sprite_list():
            pm = None
            if sprite.composite is not None:
                layer_paths = [
                    (self.rm.resolve_layer_path(layer.rel_path, sprite.composite.source), layer.offset_x, layer.offset_y)
                    for layer in sprite.composite.layers
                ]
                pm = get_composite(layer_paths, sprite.composite.width, sprite.composite.height)
            else:
                path = self._resolve_path(sprite.var)
                if path:
                    pm = get_pixmap(path)
            if pm is not None:
                layers.append(SpriteLayer(
                    pixmap=pm,
                    xalign=sprite.position.xalign,
                    yalign=sprite.position.yalign,
                    zoom=sprite.position.zoom,
                    tag=sprite.tag,
                ))
        self.preview.set_sprites(layers)

        char_label = ""
        char_color = None
        if state.char_var and self.project:
            char = self.project.get_character_by_var(state.char_var)
            char_label = char.name if char else state.char_var
            if char and getattr(char, "color", None):
                char_color = char.color
        self.preview.set_dialogue(char_label, state.text, char_color)
        self.preview.set_nvl_mode(state.nvl_mode)

        nvl_history = []
        if state.nvl_mode and self.project is not None:
            try:
                scene_idx = self.project.scenes.index(scene)
                _, _, _, _, nvl_history = presentation_engine.fast_forward_state(
                    self.project, presentation_engine.Position(scene_idx, node_index), rm=self.rm
                )
            except ValueError:
                nvl_history = []
        self.preview.set_nvl_history(nvl_history)

        self.step_lbl.setText(f"Шаг {node_index + 1} из {len(scene.nodes)}: {scene.nodes[node_index].preview_text()}")

    def _on_sprite_dragged(self, xalign: float):
                                                                             
                                                              
        if self._current_node and self._current_node.node_type == NodeType.SHOW_SPRITE:
            self._current_node.xalign = xalign
            self.sprite_position_changed.emit(xalign)

    def _on_sprite_delete_requested(self, tag: str):
        """Клик (без перемещения) по спрайту в превью: удаляет из сцены узел
        SHOW_SPRITE, который вывел этот тег на экран к текущему шагу. Ищем
        с конца назад от текущего шага - это и есть узел, отвечающий за
        текущую видимость спрайта (если между ним и текущим шагом был hide
        и повторный show, найдётся именно последний show)."""
        scene = self._current_scene
        idx = self._current_node_index
        if not scene or idx < 0 or not tag:
            return
        for i in range(idx, -1, -1):
            node = scene.nodes[i]
            if node.node_type == NodeType.SHOW_SPRITE:
                node_tag = node.sprite_tag
                if not node_tag:
                    composite = self.rm.find_composite_by_name(node.sprite_var) if (self.rm and node.sprite_var) else None
                    node_tag = composite.character if composite else node.sprite_var
                if node_tag == tag:
                    if self.before_delete_cb:
                        self.before_delete_cb()
                    del scene.nodes[i]
                    if idx >= i:
                        self._current_node_index = idx - 1
                    self.sprite_node_deleted.emit()
                    self.show_state(scene, self._current_node_index, self.project)
                    return
            elif node.node_type == NodeType.SCENE:
                                                                                    
                                                                         
                break


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RenPy Visual Script Editor")
        self.setMinimumSize(1600, 860)
        self.resize(1760, 940)

        self.pm = ProjectManager()
        self.rm = ResourceManager(BASE_DIR)
        self.pm.new_project()
        self.pm.project.characters = load_global_characters(BASE_DIR)
        self.rm.scan()
        self._current_scene_idx = 0
        self._current_node_idx = -1
        self.app_settings = AppSettings.load(BASE_DIR)
        self.tags_store = TagsStore.load(BASE_DIR)
        self.usage_store = ResourceUsageStore.load(BASE_DIR)
        self.custom_node_template_store = CustomNodeTemplateStore.load(BASE_DIR)
        self.hotkey_store = HotkeyStore.load(BASE_DIR)
        self._dirty = False
        self._update_thread: Optional[UpdateCheckThread] = None

        self.undo_manager = UndoManager()
        self._edit_group_open = False
        self._node_load_snapshot: Optional[dict] = None

        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._load_project_to_ui()
        self._restore_window_state()
        self._setup_hotkey_shortcuts()
        self._setup_autosave()
        self._check_crash_recovery()

        if self.app_settings.check_updates_on_startup:
            self._start_update_check(manual=False)

    def _restore_window_state(self):
        """Восстанавливает размер/положение окна из предыдущей сессии.
        Если ничего не сохранено (первый запуск) - оставляем как есть,
        main.py откроет окно развёрнутым."""
        self._restored_geometry = False
        geo_hex = self.app_settings.window_geometry
        state_hex = self.app_settings.window_state
        if geo_hex:
            try:
                self.restoreGeometry(bytes.fromhex(geo_hex))
                self._restored_geometry = True
            except Exception:
                pass
        if state_hex:
            try:
                self.restoreState(bytes.fromhex(state_hex))
            except Exception:
                pass

    def _setup_hotkey_shortcuts(self):
        """(Пере)создаёт QShortcut-ы для быстрого добавления нод по
        настраиваемым горячим клавишам (см. Проект → Настройки редактора)."""
        for sc in getattr(self, "_hotkey_shortcuts", []):
            sc.setParent(None)
            sc.deleteLater()
        self._hotkey_shortcuts = []

        node_type_map = {
            "add_dialogue": (NodeType.DIALOGUE, "Добавлена реплика"),
            "add_narration": (NodeType.NARRATION, "Добавлено повествование"),
            "add_show_sprite": (NodeType.SHOW_SPRITE, "Добавлен показ спрайта"),
            "add_hide_sprite": (NodeType.HIDE_SPRITE, "Добавлено скрытие спрайта"),
            "add_show_bg": (NodeType.SHOW_BG, "Добавлен показ фона"),
            "add_pause": (NodeType.PAUSE, "Добавлена пауза"),
            "add_menu": (NodeType.MENU, "Добавлено меню"),
        }
        simple_action_map = {
            "duplicate_node": self.scene_panel._dup_node,
            "move_node_up": self.scene_panel._move_up,
            "move_node_down": self.scene_panel._move_down,
        }

        for action_id, key_seq in self.hotkey_store.bindings.items():
            if not key_seq:
                continue
            if action_id in node_type_map:
                node_type, label = node_type_map[action_id]
                handler = (lambda nt=node_type, lb=label: self.scene_panel.add_node_of_type(nt, lb))
            elif action_id in simple_action_map:
                handler = simple_action_map[action_id]
            else:
                continue
            sc = QShortcut(QKeySequence(key_seq), self)
            sc.activated.connect(handler)
            self._hotkey_shortcuts.append(sc)

    def _setup_autosave(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._do_autosave)
        self._apply_autosave_interval()

    def _apply_autosave_interval(self):
        self.autosave_timer.stop()
        if self.app_settings.autosave_enabled:
            self.autosave_timer.start(max(30, self.app_settings.autosave_interval_sec) * 1000)

    def _do_autosave(self):
        if not self.app_settings.autosave_enabled or not self._dirty:
            return
        write_autosave(BASE_DIR, self.pm.project, self.pm.current_path)

    def _check_crash_recovery(self):
        if not has_autosave(BASE_DIR):
            return
        info = read_autosave(BASE_DIR)
        if info is None:
            clear_autosave(BASE_DIR)
            return
        reply = QMessageBox.question(
            self, "Восстановление после сбоя",
            f"Обнаружены несохранённые изменения из прошлой сессии "
            f"(«{info.title}»), похоже, редактор закрылся аварийно.\n\n"
            f"Восстановить их?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.pm.project = project_from_dict(info.data)
                self.pm.current_path = info.original_path
                self._load_project_to_ui()
                self._mark_dirty()
                self.status_lbl.setText("Восстановлено из автосохранения - не забудьте сохранить (Ctrl+S)")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка восстановления", str(e))
        clear_autosave(BASE_DIR)

    def _edit_editor_settings(self):
        dlg = EditorSettingsDialog(self.hotkey_store, self.app_settings, BASE_DIR, self)
        dlg.exec()
        self._setup_hotkey_shortcuts()
        self._apply_autosave_interval()

    def _show_history_panel(self):
        dlg = HistoryPanelDialog(self.undo_manager, self._undo_to_depth, self)
        dlg.exec()

    def _undo_to_depth(self, depth: int):
        current = project_to_dict(self.pm.project)
        snap = self.undo_manager.undo_to_depth(current, depth)
        if snap is None:
            return
        self._restore_snapshot(snap)
        self._mark_dirty()
        self.status_lbl.setText(f"Отменено действий: {depth}")

                                                                          
                                                                        
                                                                     
                                                                           
                                             
        self._geo_save_timer = QTimer(self)
        self._geo_save_timer.setSingleShot(True)
        self._geo_save_timer.timeout.connect(self._save_geometry_now)

    def _schedule_geometry_save(self):
        if hasattr(self, "_geo_save_timer"):
            self._geo_save_timer.start(800)

    def _save_geometry_now(self):
        self.app_settings.window_geometry = bytes(self.saveGeometry()).hex()
        self.app_settings.window_state = bytes(self.saveState()).hex()
        self.app_settings.save(BASE_DIR)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._schedule_geometry_save()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._schedule_geometry_save()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

                                  
        self.scene_panel = SceneListPanel()
        self.scene_panel.setMinimumWidth(320)
        self.scene_panel.setMaximumWidth(320)
        self.scene_panel.scene_selected.connect(self._on_scene_selected)
        self.scene_panel.node_selected.connect(self._on_node_selected)
        self.scene_panel.node_order_changed.connect(self._on_node_changed)
        self.scene_panel.before_change.connect(self._begin_change)
        self.scene_panel.branch_back_requested.connect(self._exit_menu_branch)
        self.scene_panel.present_from_here_requested.connect(self._start_presentation_from)
        splitter.addWidget(self.scene_panel)

                               
        self.node_editor = NodeEditor(self.rm)
        self.node_editor.tags_store = self.tags_store
        self.node_editor.usage_store = self.usage_store
        self.node_editor.custom_template_store = self.custom_node_template_store
        self.node_editor.set_characters(self.pm.project.characters)
        self.node_editor.node_changed.connect(self._on_node_field_changed)
        self.node_editor.open_menu_branch.connect(self._enter_menu_branch)
        self.node_editor.refresh_resources()
        self._reload_spellcheck_whitelist()
        scroll = QScrollArea()
        scroll.setWidget(self.node_editor)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(440)
        splitter.addWidget(scroll)

                                            
        self.preview_panel = ScenePreviewPanel()
        self.preview_panel.set_context(self.rm, self.pm.project)
        self.preview_panel.setMinimumWidth(680)
        self.preview_panel.sprite_position_changed.connect(self._on_sprite_dragged_in_preview)
        self.preview_panel.sprite_node_deleted.connect(self._on_sprite_node_deleted_in_preview)
        self.preview_panel.before_delete_cb = self._begin_change
        splitter.addWidget(self.preview_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([260, 660, 680])

        main_layout.addWidget(splitter)

    def _setup_menu(self):
        mb = self.menuBar()

              
        file_menu = mb.addMenu("Файл")

        act_new = QAction("Новый проект", self)
        act_new.setShortcut(QKeySequence.StandardKey.New)
        act_new.setIconText("Новый")
        act_new.triggered.connect(self._new_project)
        file_menu.addAction(act_new)
        self.act_new = act_new

        act_open = QAction("Открыть...", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.setIconText("Открыть")
        act_open.triggered.connect(self._open_project)
        file_menu.addAction(act_open)
        self.act_open = act_open

        act_save = QAction("Сохранить", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self._save_project)
        file_menu.addAction(act_save)
        self.act_save = act_save

        act_save_as = QAction("Сохранить как...", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(self._save_project_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()
        act_quit = QAction("Выход", self)
        act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

              
        edit_menu = mb.addMenu("Правка")

        act_palette = QAction("Командная палитра...", self)
        act_palette.setShortcut(QKeySequence("Ctrl+Shift+P"))
        act_palette.triggered.connect(self._show_command_palette)
        edit_menu.addAction(act_palette)
        edit_menu.addSeparator()

        act_undo = QAction("Отменить", self)
        act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        act_undo.setIconText("Отменить")
        act_undo.triggered.connect(self._undo)
        act_undo.setEnabled(False)
        edit_menu.addAction(act_undo)
        self.act_undo = act_undo

        act_redo = QAction("Повторить", self)
        act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        act_redo.setIconText("Повторить")
        act_redo.triggered.connect(self._redo)
        act_redo.setEnabled(False)
        edit_menu.addAction(act_redo)
        self.act_redo = act_redo

        edit_menu.addSeparator()
        act_find_replace = QAction("Найти и заменить...", self)
        act_find_replace.setShortcut(QKeySequence("Ctrl+H"))
        act_find_replace.triggered.connect(self._show_find_replace)
        edit_menu.addAction(act_find_replace)

        edit_menu.addSeparator()
        act_history = QAction("История действий...", self)
        act_history.setShortcut(QKeySequence("Ctrl+Alt+H"))
        act_history.triggered.connect(self._show_history_panel)
        edit_menu.addAction(act_history)

        act_editor_settings = QAction("Настройки редактора (клавиши, автосохранение)...", self)
        act_editor_settings.triggered.connect(self._edit_editor_settings)
        edit_menu.addAction(act_editor_settings)

                
        proj_menu = mb.addMenu("Проект")

        act_chars = QAction("Персонажи...", self)
        act_chars.setShortcut(QKeySequence("Ctrl+P"))
        act_chars.setIconText("Персонажи")
        act_chars.triggered.connect(self._edit_characters)
        proj_menu.addAction(act_chars)
        self.act_chars = act_chars

        act_res = QAction("Настройки ресурсов...", self)
        act_res.triggered.connect(self._edit_resources)
        proj_menu.addAction(act_res)

        act_tags = QAction("Категории тегов (фоны/CG)...", self)
        act_tags.triggered.connect(self._edit_tags)
        proj_menu.addAction(act_tags)

        act_code_templates = QAction("Шаблоны пользовательских нод...", self)
        act_code_templates.triggered.connect(self._edit_code_templates)
        proj_menu.addAction(act_code_templates)

        proj_menu.addSeparator()
        act_presentation = QAction("▶ Режим презентации", self)
        act_presentation.setShortcut(QKeySequence("Shift+F5"))
        act_presentation.triggered.connect(self._start_presentation)
        proj_menu.addAction(act_presentation)

        act_timing = QAction("⏱ Проверка тайминга...", self)
        act_timing.triggered.connect(self._show_timing_report)
        proj_menu.addAction(act_timing)

        act_spellcheck = QAction("🔤 Проверка реплик...", self)
        act_spellcheck.triggered.connect(self._show_spellcheck_report)
        proj_menu.addAction(act_spellcheck)

        act_import_paths = QAction("Импорт путей из .rpy...", self)
        act_import_paths.triggered.connect(self._import_paths)
        proj_menu.addAction(act_import_paths)

        act_import_script = QAction("Импорт скрипта из .rpy...", self)
        act_import_script.triggered.connect(self._import_script)
        proj_menu.addAction(act_import_script)

        act_screenplay = QAction("Экспорт/импорт текста для вычитки...", self)
        act_screenplay.triggered.connect(self._show_screenplay_dialog)
        proj_menu.addAction(act_screenplay)

        act_git = QAction("Версионирование проекта (Git)...", self)
        act_git.triggered.connect(self._show_git_panel)
        proj_menu.addAction(act_git)

        act_download_res = QAction("Скачать ресурсы для модификаций...", self)
        act_download_res.setIconText("Скачать ресурсы")
        act_download_res.triggered.connect(self._show_resources_download)
        proj_menu.addAction(act_download_res)
        self.act_download_res = act_download_res

        act_rescan = QAction("Переиндексировать ресурсы", self)
        act_rescan.setShortcut(QKeySequence("F5"))
        act_rescan.setIconText("Переиндексировать")
        act_rescan.triggered.connect(self._rescan_resources)
        proj_menu.addAction(act_rescan)
        self.act_rescan = act_rescan

        proj_menu.addSeparator()
        act_rename = QAction("Переименовать проект...", self)
        act_rename.triggered.connect(self._rename_project)
        proj_menu.addAction(act_rename)

        act_label = QAction("Главная метка (label)...", self)
        act_label.triggered.connect(self._set_main_label)
        proj_menu.addAction(act_label)

                   
        gen_menu = mb.addMenu("Генерация")

        act_preview = QAction("Просмотр кода...", self)
        act_preview.setShortcut(QKeySequence("Ctrl+G"))
        act_preview.setIconText("Генерировать")
        act_preview.triggered.connect(self._show_code_preview)
        gen_menu.addAction(act_preview)
        self.act_preview = act_preview

        act_export = QAction("Экспорт .rpy...", self)
        act_export.setShortcut(QKeySequence("Ctrl+E"))
        act_export.setIconText("Экспорт .rpy")
        act_export.triggered.connect(self._export_rpy)
        gen_menu.addAction(act_export)
        self.act_export = act_export

        act_export_split = QAction("Экспорт в несколько файлов (по главам/актам)...", self)
        act_export_split.triggered.connect(self._export_split)
        gen_menu.addAction(act_export_split)

        act_defines = QAction("Экспорт блока defines...", self)
        act_defines.triggered.connect(self._export_defines)
        gen_menu.addAction(act_defines)

        gen_menu.addSeparator()
        act_res_defines = QAction("Экспорт defines ресурсов...", self)
        act_res_defines.triggered.connect(self._export_resource_defines)
        gen_menu.addAction(act_res_defines)

                 
        stats_menu = mb.addMenu("Статистика")
        act_stats = QAction("Статистика реплик по персонажам...", self)
        act_stats.triggered.connect(self._show_dialogue_stats)
        stats_menu.addAction(act_stats)

                 
        help_menu = mb.addMenu("Справка")

        act_guide = QAction("Руководство пользователя...", self)
        act_guide.setShortcut(QKeySequence("F1"))
        act_guide.setIconText("Руководство")
        act_guide.triggered.connect(self._show_help)
        help_menu.addAction(act_guide)
        self.act_guide = act_guide

        help_menu.addSeparator()
        act_check_updates = QAction("Проверить обновления...", self)
        act_check_updates.triggered.connect(lambda: self._start_update_check(manual=True))
        help_menu.addAction(act_check_updates)

        self.act_autoupdate = QAction("Проверять обновления при запуске", self)
        self.act_autoupdate.setCheckable(True)
        self.act_autoupdate.setChecked(self.app_settings.check_updates_on_startup)
        self.act_autoupdate.toggled.connect(self._on_autoupdate_toggled)
        help_menu.addAction(self.act_autoupdate)

    def _setup_toolbar(self):
        tb = QToolBar("Основная панель")
        tb.setObjectName("main_toolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(tb)
        style = self.style()
        SP = QStyle.StandardPixmap

                                                                          
                                                                   
                                                                 
                                                                 
                                                                    
                                                                        
        def with_icon(action: QAction, icon) -> QAction:
            action.setIcon(style.standardIcon(icon))
            return action

        tb.addAction(with_icon(self.act_new, SP.SP_FileIcon))
        tb.addAction(with_icon(self.act_open, SP.SP_DialogOpenButton))
        tb.addAction(with_icon(self.act_save, SP.SP_DialogSaveButton))
        tb.addSeparator()
        tb.addAction(with_icon(self.act_chars, SP.SP_FileDialogContentsView))
        tb.addAction(with_icon(self.act_rescan, SP.SP_DirIcon))
        tb.addAction(with_icon(self.act_download_res, SP.SP_DriveNetIcon))
        tb.addSeparator()
        tb.addAction(with_icon(self.act_preview, SP.SP_FileDialogDetailedView))
        tb.addAction(with_icon(self.act_export, SP.SP_DialogSaveButton))
        tb.addSeparator()
        tb.addAction(with_icon(self.act_guide, SP.SP_DialogHelpButton))

                          
        tb.addSeparator()
        self.lbl_project = QLabel()
        self.lbl_project.setStyleSheet("color: #ff8c3d; font-weight: 600; padding: 0 12px;")
        tb.addWidget(self.lbl_project)

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.status_lbl = QLabel("Готов")
        self.statusbar.addWidget(self.status_lbl)
        self.status_res = QLabel()
        self.statusbar.addPermanentWidget(self.status_res)

    def _update_status(self):
        counts = {cat: len(entries) for cat, entries in self.rm.resources.items()}
        self.status_res.setText(
            f"  BG:{counts.get('bg',0)}  CG:{counts.get('cg',0)}  "
            f"Спрайты:{counts.get('sprites',0)}  "
            f"Музыка:{counts.get('music',0)}  Звуки:{counts.get('sounds',0)}  "
        )

                                                         

    def _load_project_to_ui(self):
        p = self.pm.project
        self._update_title()
        if not p.scenes:
            p.scenes.append(Scene(name="Сцена 1"))
        self.scene_panel.load_project(p)
        self.node_editor.set_characters(p.characters)
        self.node_editor.refresh_resources()
        self.preview_panel.set_context(self.rm, p)
        self._update_status()
                             
        if p.scenes and p.scenes[0].nodes:
            self._on_node_selected(0, 0)
        else:
            self._current_scene_idx = 0
            self._current_node_idx = -1
            self._refresh_preview()
        self.undo_manager.clear()
        self._edit_group_open = False
        self._node_load_snapshot = project_to_dict(p)
        self._update_undo_actions()

                                                        

    def _mark_dirty(self):
        if not self._dirty:
            self._dirty = True
            self._update_title()

    def _mark_clean(self):
        if self._dirty:
            self._dirty = False
            self._update_title()

    def _update_title(self):
        title = self.pm.project.title if self.pm and self.pm.project else "Проект"
        marker = " ●" if self._dirty else ""
        self.setWindowTitle(f"RenPy Visual Script Editor - {title}{marker}")
        if hasattr(self, "lbl_project"):
            self.lbl_project.setText(f"Проект: {title}{marker}")

    def _begin_change(self, label: str = "Изменение"):
        """Вызывать ПЕРЕД любой дискретной (не коалесцируемой) мутацией
        модели проекта: добавление/удаление/перемещение узла или сцены и т.п.
        Каждый вызов - это отдельный шаг в истории отмены."""
        self.undo_manager.push(project_to_dict(self.pm.project), label)
        self._edit_group_open = False
        self._update_undo_actions()
        self._mark_dirty()

    def _begin_edit_group(self, label: str = "Правка поля"):
        """Вызывать перед мутацией, которая может повторяться много раз подряд
        не создавая новую точку истории - правка текста в поле, перетаскивание
        спрайта мышью. Снапшот берётся с момента выбора ноды/начала правки:
        все правки одной "сессии" редактирования схлопываются в один шаг
        отмены, пока не сменится выбранная нода."""
        if not self._edit_group_open:
            self.undo_manager.push(self._node_load_snapshot, label)
            self._edit_group_open = True
            self._update_undo_actions()
        self._mark_dirty()

    def _update_undo_actions(self):
        if hasattr(self, "act_undo"):
            self.act_undo.setEnabled(self.undo_manager.can_undo())
        if hasattr(self, "act_redo"):
            self.act_redo.setEnabled(self.undo_manager.can_redo())

    def _undo(self):
        current = project_to_dict(self.pm.project)
        result = self.undo_manager.undo(current)
        if result is None:
            return
        label, snap = result
        self._restore_snapshot(snap)
        self._mark_dirty()
        self.status_lbl.setText(f"Отменено: {label}")

    def _redo(self):
        current = project_to_dict(self.pm.project)
        result = self.undo_manager.redo(current)
        if result is None:
            return
        label, snap = result
        self._restore_snapshot(snap)
        self._mark_dirty()
        self.status_lbl.setText(f"Повторено: {label}")

    def _restore_snapshot(self, data: dict):
        keep_scene = self._current_scene_idx
        keep_node = self._current_node_idx

        self.pm.project = project_from_dict(data)
        p = self.pm.project
        self._update_title()
        if not p.scenes:
            p.scenes.append(Scene(name="Сцена 1"))
        self.scene_panel.load_project(p)
        self.node_editor.set_characters(p.characters)
        self.node_editor.refresh_resources()
        self.preview_panel.set_context(self.rm, p)
        self._update_status()

        self._edit_group_open = False

        si = max(0, min(keep_scene, len(p.scenes) - 1))
        self.scene_panel.scene_list.setCurrentRow(si)
        scene = p.scenes[si]
        ni = max(0, min(keep_node, len(scene.nodes) - 1)) if scene.nodes else -1
        self.scene_panel._select_node_row(ni)

        self._update_undo_actions()

                                                        

    def _new_project(self):
        reply = QMessageBox.question(self, "Новый проект",
                                     "Создать новый проект? Несохранённые данные будут потеряны.")
        if reply == QMessageBox.StandardButton.Yes:
            name, ok = QInputDialog.getText(self, "Новый проект", "Название проекта:", text="Мой проект")
            if ok:
                self.pm.new_project(name.strip() or "Мой проект")
                self.pm.project.characters = load_global_characters(BASE_DIR)
                self._load_project_to_ui()
                clear_autosave(BASE_DIR)
                self._mark_clean()
                self.status_lbl.setText("Новый проект создан")

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть проект", "",
            "RenPy Editor Project (*.repj);;Все файлы (*)"
        )
        if path:
            project = self.pm.load(path)
            if project:
                self._load_project_to_ui()
                save_global_characters(BASE_DIR, project.characters)
                clear_autosave(BASE_DIR)
                self._mark_clean()
                self.status_lbl.setText(f"Загружен: {path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось загрузить проект")

    def _save_project(self):
        if not self.pm.current_path:
            self._save_project_as()
        else:
            ok = self.pm.save()
            if ok:
                self._mark_clean()
                clear_autosave(BASE_DIR)
                self.status_lbl.setText(f"Сохранено: {self.pm.current_path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить проект")

    def _save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить проект", f"{self.pm.project.title}.repj",
            "RenPy Editor Project (*.repj);;Все файлы (*)"
        )
        if path:
            ok = self.pm.save(path)
            if ok:
                self._mark_clean()
                clear_autosave(BASE_DIR)
                self.status_lbl.setText(f"Сохранено: {path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить проект")

                                                        

    def _rename_project(self):
        name, ok = QInputDialog.getText(self, "Переименовать проект",
                                        "Название:", text=self.pm.project.title)
        if ok and name.strip():
            self._begin_change("Переименован проект")
            self.pm.project.title = name.strip()
            self._update_title()

    def _set_main_label(self):
        lbl, ok = QInputDialog.getText(self, "Главная метка",
                                       "Имя label для входа:", text=self.pm.project.label_name)
        if ok and lbl.strip():
            self.pm.project.label_name = lbl.strip()

    def _edit_characters(self):
        dlg = CharactersDialog(self.pm.project.characters, self)
        dlg.characters_changed.connect(self._on_characters_changed)
        dlg.exec()

    def _on_characters_changed(self, chars: list):
        self.pm.project.characters = chars
        self.node_editor.set_characters(chars)
        self.status_lbl.setText(f"Персонажей: {len(chars)}")
        self._refresh_preview()
        save_global_characters(BASE_DIR, chars)

    def _edit_resources(self):
        dlg = ResourcesConfigDialog(self.rm, self.tags_store, BASE_DIR, self,
                                     usage_store=self.usage_store, project=self.pm.project)
        dlg.navigate_requested.connect(self._navigate_to_usage)
        dlg.exec()

    def _edit_code_templates(self):
        dlg = CustomNodeTemplatesDialog(self.custom_node_template_store, BASE_DIR, self)
        dlg.templates_changed.connect(self._on_custom_templates_changed)
        dlg.exec()

    def _on_custom_templates_changed(self):
        if hasattr(self.node_editor, "custom_template_store"):
            self.node_editor.custom_template_store = self.custom_node_template_store
        if self.node_editor.node is not None and self.node_editor.node.node_type == NodeType.CUSTOM:
            self.node_editor._rebuild_fields()

    def _show_spellcheck_report(self):
        if not self.pm or not self.pm.project:
            return
        from core.spellcheck_whitelist_store import SpellcheckWhitelist
        whitelist_store = SpellcheckWhitelist.load(BASE_DIR)

        progress = QProgressDialog("Проверка реплик...", "Отмена", 0, 0, self)
        progress.setWindowTitle("Проверка реплик")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(300)                                                  
        progress.setAutoClose(False)
        progress.setValue(0)

        worker = _SpellcheckWorker(self.pm.project, self, extra_whitelist=whitelist_store.as_set())
        self._spellcheck_worker = worker                                                       

        def on_progress(done, total):
            if total:
                progress.setMaximum(total)
                progress.setLabelText(f"Проверка реплик... {done}/{total}")
            progress.setValue(done)

        def on_finished(results):
            progress.close()
            from core.spellcheck import get_diagnostics
            from ui.spellcheck_report_dialog import SpellcheckReportDialog
            dlg = SpellcheckReportDialog(results, get_diagnostics(), whitelist_store, BASE_DIR, self)
            dlg.navigate_requested.connect(self._navigate_to_usage)
            dlg.rescan_requested.connect(self._show_spellcheck_report)
            dlg.exec()
            self._reload_spellcheck_whitelist()
            self._spellcheck_worker = None

        worker.progress.connect(on_progress)
        worker.finished_scan.connect(on_finished)
        progress.canceled.connect(worker.cancel)
        worker.start()
        progress.exec()

    def _show_timing_report(self):
        if not self.pm or not self.pm.project:
            return
        from core.timing_estimator import estimate_timing
        from ui.timing_report_dialog import TimingReportDialog
        stats = estimate_timing(self.pm.project)
        dlg = TimingReportDialog(stats, self)
        dlg.exec()

    def _reload_spellcheck_whitelist(self):
        from core.spellcheck_whitelist_store import SpellcheckWhitelist
        from core.spellcheck_scanner import _auto_whitelist
        store = SpellcheckWhitelist.load(BASE_DIR)
        words = store.as_set()
        if self.pm and self.pm.project:
            words |= _auto_whitelist(self.pm.project)
        self.node_editor.set_spellcheck_whitelist(words)

    def _show_command_palette(self):
        commands = collect_commands_from_menubar(self.menuBar())
        dlg = CommandPaletteDialog(commands, self)
        geo = self.geometry()
        dlg.move(geo.center().x() - dlg.width() // 2, geo.top() + 90)
        dlg.exec()

    def _start_presentation(self):
        if not self.pm or not self.pm.project:
            return
        self._presentation_window = PresentationWindow(self.pm.project, self.rm, self)
        self._presentation_window.show()

    def _start_presentation_from(self, scene_idx: int, node_idx: int):
        if not self.pm or not self.pm.project:
            return
        from core.presentation_engine import Position
        p = self.pm.project
        if not (0 <= scene_idx < len(p.scenes) and 0 <= node_idx < len(p.scenes[scene_idx].nodes)):
            return
        pos = Position(scene_idx, node_idx)
        self._presentation_window = PresentationWindow(p, self.rm, self, start_pos=pos)
        self._presentation_window.show()

    def _show_git_panel(self):
        if not self.pm.current_path:
            QMessageBox.information(
                self, "Сначала сохраните проект",
                "Версионирование работает с папкой, где лежит файл проекта. "
                "Сначала сохраните проект (Ctrl+S), затем откройте версионирование снова."
            )
            return
        repo_dir = os.path.dirname(os.path.abspath(self.pm.current_path))
        project_file = os.path.basename(self.pm.current_path)
        dlg = GitPanelDialog(repo_dir, BASE_DIR, self, project_file=project_file)
        dlg.exec()

    def _show_screenplay_dialog(self):
        if not self.pm or not self.pm.project:
            return
        self._begin_change("Импорт правок из текста для вычитки")
        dlg = ScreenplayExportImportDialog(self.pm.project, self)
        dlg.imported.connect(self._on_find_replace_applied)
        dlg.exec()

    def _show_dialogue_stats(self):
        if not self.pm or not self.pm.project:
            return
        dlg = DialogueStatsDialog(self.pm.project, self)
        dlg.exec()

    def _show_find_replace(self):
        if not self.pm or not self.pm.project:
            return
        self._begin_change("Найти и заменить")
        dlg = FindReplaceDialog(self.pm.project, self)
        dlg.replaced.connect(self._on_find_replace_applied)
        dlg.exec()

    def _on_find_replace_applied(self):
        self._load_project_to_ui()
        self.status_lbl.setText("Массовая замена текста применена.")
                                                                             
                                                                               
                                                   
        self._rescan_resources()

    def _edit_tags(self):
        dlg = TagsManagerDialog(self.tags_store, BASE_DIR, self)
        dlg.changed.connect(self._on_tags_changed)
        dlg.exec()

    def _on_tags_changed(self):
                                                                           
                                                               
        if hasattr(self.node_editor, "bg_carousel") and self.node_editor.bg_carousel is not None:
            try:
                self.node_editor.bg_carousel.refresh_tag_categories()
            except RuntimeError:
                pass

    def _import_paths(self):
        dlg = ImportPathsDialog(self.rm, self)
        dlg.characters_selected.connect(self._on_characters_imported)
        dlg.paths_applied.connect(self._rescan_resources)
        dlg.exec()

    def _import_script(self):
        dlg = ImportScriptDialog(resource_manager=self.rm, parent=self)
        dlg.scenes_imported.connect(self._on_scenes_imported)
        dlg.exec()

    def _on_scenes_imported(self, scenes: list):
        p = self.pm.project
        existing_by_name = {s.name: s for s in p.scenes}
        collisions = [s for s in scenes if s.name in existing_by_name]

        mode = "add"                                      
        if collisions:
            names_preview = ", ".join(f"«{s.name}»" for s in collisions[:5])
            more = f" и ещё {len(collisions) - 5}" if len(collisions) > 5 else ""
            box = QMessageBox(self)
            box.setWindowTitle("Повторный импорт")
            box.setText(
                f"{len(collisions)} импортируемых сцен уже есть в проекте по имени метки "
                f"({names_preview}{more}).\n\nЧто сделать с совпадающими?"
            )
            btn_replace = box.addButton("🔄 Заменить содержимое", QMessageBox.ButtonRole.AcceptRole)
            btn_skip = box.addButton("⏭ Пропустить совпадающие", QMessageBox.ButtonRole.YesRole)
            btn_dupe = box.addButton("➕ Всё равно добавить как дубликаты", QMessageBox.ButtonRole.DestructiveRole)
            box.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
            box.exec()
            clicked = box.clickedButton()
            if clicked == btn_replace:
                mode = "replace"
            elif clicked == btn_skip:
                mode = "skip"
            elif clicked == btn_dupe:
                mode = "add"
            else:
                return                                

        added, replaced, skipped = 0, 0, 0
        for scene in scenes:
            existing = existing_by_name.get(scene.name)
            if existing is not None and mode == "skip":
                skipped += 1
                continue
            if existing is not None and mode == "replace":
                existing.nodes = scene.nodes
                existing.groups = scene.groups
                replaced += 1
                continue
            p.scenes.append(scene)
            added += 1

        self._load_project_to_ui()
        parts = [f"добавлено сцен: {added}"]
        if replaced:
            parts.append(f"заменено: {replaced}")
        if skipped:
            parts.append(f"пропущено (уже есть): {skipped}")
        self.status_lbl.setText("Импорт - " + ", ".join(parts))

    def _on_characters_imported(self, parsed_characters: list):
        existing_vars = {c.variable for c in self.pm.project.characters}
        existing_by_name = {c.name.strip().lower(): c for c in self.pm.project.characters if c.name}
        added, matched_by_name, skipped_same_var = 0, 0, 0
        for pc in parsed_characters:
            if pc.variable in existing_vars:
                skipped_same_var += 1                                           
                continue
            name_key = (pc.name or "").strip().lower()
            existing = existing_by_name.get(name_key) if name_key else None
            if existing is not None:
                                                                           
                                                                        
                                                                          
                matched_by_name += 1
                continue
            new_char = Character(name=pc.name, variable=pc.variable, color=pc.color)
            self.pm.project.characters.append(new_char)
            existing_vars.add(pc.variable)
            existing_by_name[name_key] = new_char
            added += 1
        if added:
            self._on_characters_changed(self.pm.project.characters)
        if matched_by_name or skipped_same_var:
            parts = [f"добавлено новых: {added}"]
            if matched_by_name:
                parts.append(f"совпало по имени (дубликаты не созданы): {matched_by_name}")
            if skipped_same_var:
                parts.append(f"уже было (та же переменная): {skipped_same_var}")
            self.status_lbl.setText("Импорт персонажей - " + ", ".join(parts))

    def _show_resources_download(self):
        dlg = ResourcesDownloadDialog(self)
        dlg.exec()

    def _show_help(self):
        dlg = HelpDialog(self)
        dlg.exec()

    def _on_autoupdate_toggled(self, checked: bool):
        self.app_settings.check_updates_on_startup = checked
        self.app_settings.save(BASE_DIR)

    def _start_update_check(self, manual: bool = False):
                                                                     
                                                                          
                                                      
        if self._update_thread is not None and self._update_thread.isRunning():
            if manual:
                QMessageBox.information(self, "Обновления", "Проверка уже выполняется, подождите.")
            return
        self._update_thread = UpdateCheckThread()
        self._update_thread.finished_check.connect(
            lambda release: self._on_update_check_result(release, manual)
        )
        self._update_thread.start()

    def _on_update_check_result(self, release, manual: bool):
        if not release:
            if manual:
                QMessageBox.information(
                    self, "Обновления",
                    f"У вас установлена последняя версия (текущая: {self._app_version()})."
                )
            return

        if not manual and release.get("version") == self.app_settings.skipped_version:
                                                                      
                                                                      
            return

        dlg = UpdateAvailableDialog(release, self)
        dlg.exec()
        if dlg.disable_autocheck:
            self.app_settings.check_updates_on_startup = False
            if hasattr(self, "act_autoupdate"):
                self.act_autoupdate.setChecked(False)
        if dlg.result() == QDialog.DialogCode.Rejected:
            self.app_settings.skipped_version = release.get("version", "")
        else:
            self.app_settings.skipped_version = ""
        self.app_settings.save(BASE_DIR)

    @staticmethod
    def _app_version() -> str:
        from version import APP_VERSION
        return APP_VERSION

    def _rescan_resources(self):
        self.rm.scan()
        invalidate_pixmap_cache()
        self.node_editor.refresh_resources()
        self._update_status()
        counts = sum(len(v) for v in self.rm.resources.values())
        self.status_lbl.setText(f"Ресурсы переиндексированы: {counts} файлов")
        self._refresh_preview()

                                                            

    def _on_scene_selected(self, scene_idx: int):
        pass                                              

    def _enter_menu_branch(self, node: SceneNode, choice_idx: int):
        """Открывает ветку меню как полноценный редактируемый список нод -
        та же панель сцен/нод, что и для обычной сцены, только источник
        данных подменяется на choice['nodes'] (мутируется по ссылке)."""
        choices = node.normalized_menu_choices()
        if not (0 <= choice_idx < len(choices)):
            return
        text, jump, use_call, raw_body, nodes = choices[choice_idx]
        self._branch_parent_node = node
        self._branch_choice_idx = choice_idx
        self._branch_return_scene_idx = getattr(self, "_current_scene_idx", -1)
        self._branch_return_node_idx = getattr(self, "_current_node_idx", -1)
        branch_scene = Scene(name=f"Ветка меню: {text or '(без текста)'}", nodes=nodes, groups=[])
        label = f"✏️ Ветка меню: «{(text or '(без текста)')[:40]}»"
        self.scene_panel.enter_branch(branch_scene, label)
        if nodes:
            self.scene_panel._select_node_row(0)
        else:
            self._current_scene_idx = -2
            self._current_node_idx = -1
            self.node_editor.clear_node()
            self._refresh_preview()

    def _exit_menu_branch(self):
        node = getattr(self, "_branch_parent_node", None)
        self.scene_panel.exit_branch()
        self._branch_parent_node = None
        self._branch_choice_idx = None
        return_scene = getattr(self, "_branch_return_scene_idx", -1)
        return_node = getattr(self, "_branch_return_node_idx", -1)
        if 0 <= return_scene < len(self.pm.project.scenes):
            self.scene_panel.scene_list.setCurrentRow(return_scene)
        if node is not None:
                                                                        
                                                                          
            self.node_editor.load_node(node)
        if return_node is not None and return_node >= 0:
            self.scene_panel._select_node_row(return_node)
        self.scene_panel.refresh_current_node_text()
        self._refresh_preview()

    def _navigate_to_usage(self, scene_id: str, branch_path: list, node_id: str):
        """Переход к конкретной ноде по результату 'где используется':
        находит сцену по scene_id, при необходимости заходит во вложенные
        ветки меню (переиспользуя _enter_menu_branch из #1) и выбирает ноду
        по node_id."""
        p = self.pm.project
        scene_idx = next((i for i, s in enumerate(p.scenes) if s.scene_id == scene_id), None)
        if scene_idx is None:
            QMessageBox.warning(self, "Не найдено", "Сцена с этим использованием больше не существует.")
            return
        if self.scene_panel.is_in_branch_mode():
            self._exit_menu_branch()
        self.scene_panel.scene_list.setCurrentRow(scene_idx)

        for menu_node_id, choice_idx in branch_path:
            scene = self.scene_panel._get_current_scene()
            if not scene:
                return
            menu_idx = next((i for i, n in enumerate(scene.nodes) if n.node_id == menu_node_id), -1)
            if menu_idx < 0:
                QMessageBox.warning(self, "Не найдено", "Ветка меню, ведущая к использованию, больше не найдена.")
                return
            self.scene_panel._select_node_row(menu_idx)
            self._enter_menu_branch(scene.nodes[menu_idx], choice_idx)

        scene = self.scene_panel._get_current_scene()
        if not scene:
            return
        node_idx = next((i for i, n in enumerate(scene.nodes) if n.node_id == node_id), -1)
        if node_idx < 0:
            QMessageBox.warning(self, "Не найдено", "Нода с этим использованием больше не найдена.")
            return
        self.scene_panel._select_node_row(node_idx)
        self.raise_()
        self.activateWindow()

    def _on_node_selected(self, scene_idx: int, node_idx: int):
        p = self.pm.project
        self._current_scene_idx = scene_idx
        self._current_node_idx = node_idx
        self._edit_group_open = False
        self._node_load_snapshot = project_to_dict(p)
        loaded = False
        if scene_idx == -2:
                                                                            
            scene = self.scene_panel._get_current_scene()
            if scene and 0 <= node_idx < len(scene.nodes):
                self.node_editor.load_node(scene.nodes[node_idx])
                loaded = True
        elif 0 <= scene_idx < len(p.scenes):
            scene = p.scenes[scene_idx]
            if 0 <= node_idx < len(scene.nodes):
                self.node_editor.load_node(scene.nodes[node_idx])
                loaded = True
        if not loaded:
            self.node_editor.clear_node()
        self._refresh_preview()

    def _on_node_changed(self, *args):
        self.scene_panel.refresh_current_node_text()
        self._refresh_preview()

    def _on_node_field_changed(self, *args):
        node = self.node_editor.node
        hint = node.preview_text()[:50] if node else ""
        self._begin_edit_group(f"Правка ноды: {hint}")
        self._on_node_changed(*args)

    def _on_sprite_dragged_in_preview(self, xalign: float):
        node = self.node_editor.node
        hint = node.preview_text()[:50] if node else ""
        self._begin_edit_group(f"Перемещение спрайта: {hint}")
        self.node_editor.sync_xalign_from_preview(xalign)
        self.scene_panel.refresh_current_node_text()

    def _on_sprite_node_deleted_in_preview(self):
                                                                       
                                                                       
                                                              
        new_idx = getattr(self.preview_panel, "_current_node_index", -1)
        self.scene_panel._rebuild_nodes()
        self.scene_panel._select_node_row(max(0, new_idx))

    def _refresh_preview(self):
        p = self.pm.project
        scene_idx = getattr(self, "_current_scene_idx", -1)
        node_idx = getattr(self, "_current_node_idx", -1)
        if scene_idx == -2:
            scene = self.scene_panel._get_current_scene()
        else:
            scene = p.scenes[scene_idx] if 0 <= scene_idx < len(p.scenes) else None
        self.preview_panel.show_state(scene, node_idx, p)

                                                       

    def _show_code_preview(self):
        full = generate_full_script(self.pm.project, rm=self.rm, custom_templates=self.custom_node_template_store,
                                     nvl_style=self.app_settings.nvl_codegen_style)
        defines = generate_defines_only(self.pm.project)
        res_defines = self.rm.generate_define_block()
        combined_defines = res_defines + "\n" + defines
        dlg = CodePreviewDialog(full, combined_defines, self)
        dlg.exec()

    def _write_rpy_with_diff_check(self, path: str, code: str) -> Optional[str]:
        """Записывает код в path, но если файл уже существует и отличается -
        сначала показывает предпросмотр диффа (чтобы не потерять ручные
        правки). Возвращает итоговый путь записи или None, если пользователь
        отменил."""
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    old_code = f.read()
            except Exception:
                old_code = None
            if old_code is not None and old_code != code:
                dlg = DiffPreviewDialog(old_code, code, path, self)
                if dlg.exec() != QDialog.DialogCode.Accepted or dlg.action is None:
                    return None
                if dlg.action == "copy":
                    path = dlg.copy_path
                elif dlg.action == "merge":
                    code = dlg.merged_text
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)
        return path

    def _export_split(self):
        if not self.pm or not self.pm.project:
            return
        if not self.pm.project.scenes:
            QMessageBox.information(self, "Экспорт", "В проекте нет ни одной сцены.")
            return
        dlg = SplitExportDialog(self.pm.project, rm=self.rm,
                                 custom_templates=self.custom_node_template_store, parent=self,
                                 nvl_style=self.app_settings.nvl_codegen_style)
        dlg.exec()

    def _export_rpy(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт сценария", "script.rpy",
            "Ren'Py Script (*.rpy);;Все файлы (*)"
        )
        if path:
            try:
                code = generate_full_script(self.pm.project, rm=self.rm, custom_templates=self.custom_node_template_store,
                                             nvl_style=self.app_settings.nvl_codegen_style)
                written_path = self._write_rpy_with_diff_check(path, code)
                if written_path is None:
                    self.status_lbl.setText("Экспорт отменён")
                    return
                self.status_lbl.setText(f"Экспортировано: {written_path}")
                QMessageBox.information(self, "Готово", f"Сценарий сохранён:\n{written_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _export_defines(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт defines", "defines.rpy",
            "Ren'Py Script (*.rpy);;Все файлы (*)"
        )
        if path:
            try:
                code = self.rm.generate_define_block() + "\n" + generate_defines_only(self.pm.project)
                written_path = self._write_rpy_with_diff_check(path, code)
                if written_path is None:
                    self.status_lbl.setText("Экспорт отменён")
                    return
                self.status_lbl.setText(f"Defines экспортированы: {written_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _export_resource_defines(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт defines ресурсов", "resources_defines.rpy",
            "Ren'Py Script (*.rpy);;Все файлы (*)"
        )
        if path:
            try:
                code = self.rm.generate_define_block()
                written_path = self._write_rpy_with_diff_check(path, code)
                if written_path is None:
                    self.status_lbl.setText("Экспорт отменён")
                    return
                self.status_lbl.setText(f"Defines ресурсов сохранены: {written_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def closeEvent(self, event):
        self.app_settings.window_geometry = bytes(self.saveGeometry()).hex()
        self.app_settings.window_state = bytes(self.saveState()).hex()
        self.app_settings.save(BASE_DIR)

        if not self._dirty:
            clear_autosave(BASE_DIR)
            event.accept()
            return

        reply = QMessageBox.question(
            self, "Выход",
            "Сохранить проект перед выходом?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Save:
            self._save_project()
            if self._dirty:
                event.ignore()
                return
            clear_autosave(BASE_DIR)
            event.accept()
        elif reply == QMessageBox.StandardButton.Discard:
            clear_autosave(BASE_DIR)
            event.accept()
        else:
            event.ignore()
