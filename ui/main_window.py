"""
Главное окно приложения
"""
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QGroupBox,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QInputDialog,
    QScrollArea, QFrame, QLineEdit, QDialog, QStyle
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QFont

from core.models import Project, Scene, SceneNode, NodeType
from core.resource_manager import ResourceManager
from core.project_manager import ProjectManager
from core.code_generator import generate_full_script, generate_defines_only
from core.scene_state import compute_state_up_to

from ui.node_editor import NodeEditor
from ui.characters_dialog import CharactersDialog
from ui.code_preview import CodePreviewDialog
from ui.resources_dialog import ResourcesConfigDialog
from ui.scene_preview import ScenePreview, SpriteLayer
from ui.pixmap_cache import get_pixmap, get_composite, invalidate as invalidate_pixmap_cache
from ui.help_dialog import HelpDialog
from ui.resources_download_dialog import ResourcesDownloadDialog
from PyQt6.QtGui import QPixmap


from paths import BASE_DIR

class SceneListPanel(QWidget):
    """Левая панель: список сцен и узлов"""
    scene_selected = pyqtSignal(int)       # index
    node_selected = pyqtSignal(int, int)   # scene_idx, node_idx
    node_order_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.project: Optional[Project] = None
        self._current_scene = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        scenes_group = QGroupBox("Сцены")
        sg_layout = QVBoxLayout(scenes_group)
        sg_layout.setContentsMargins(4, 8, 4, 4)

        self.scene_list = QListWidget()
        self.scene_list.setMaximumHeight(120)
        self.scene_list.currentRowChanged.connect(self._on_scene_changed)
        sg_layout.addWidget(self.scene_list)

        sc_btn_row = QHBoxLayout()
        btn_add_scene = QPushButton(" + Сцена")
        btn_add_scene.setFixedHeight(26)
        btn_add_scene.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        btn_add_scene.clicked.connect(self._add_scene)
        btn_rename_scene = QPushButton()
        btn_rename_scene.setFixedSize(26, 26)
        btn_rename_scene.setObjectName("btn_secondary")
        btn_rename_scene.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        btn_rename_scene.setToolTip("Переименовать сцену")
        btn_rename_scene.clicked.connect(self._rename_scene)
        btn_del_scene = QPushButton()
        btn_del_scene.setFixedSize(26, 26)
        btn_del_scene.setObjectName("btn_danger")
        btn_del_scene.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton))
        btn_del_scene.setToolTip("Удалить сцену")
        btn_del_scene.clicked.connect(self._del_scene)
        sc_btn_row.addWidget(btn_add_scene, 1)
        sc_btn_row.addWidget(btn_rename_scene)
        sc_btn_row.addWidget(btn_del_scene)
        sg_layout.addLayout(sc_btn_row)

        layout.addWidget(scenes_group)

        nodes_group = QGroupBox("Элементы сцены")
        ng_layout = QVBoxLayout(nodes_group)
        ng_layout.setContentsMargins(4, 8, 4, 4)

        self.node_list = QListWidget()
        self.node_list.currentRowChanged.connect(self._on_node_changed)
        ng_layout.addWidget(self.node_list)

        nd_btn_row = QHBoxLayout()
        btn_add_node = QPushButton(" + Добавить")
        btn_add_node.setFixedHeight(26)
        btn_add_node.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        btn_add_node.clicked.connect(self._add_node)

        btn_dup = QPushButton()
        btn_dup.setFixedSize(26, 26)
        btn_dup.setObjectName("btn_secondary")
        btn_dup.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        btn_dup.setToolTip("Дублировать")
        btn_dup.clicked.connect(self._dup_node)

        btn_up = QPushButton()
        btn_up.setFixedSize(26, 26)
        btn_up.setObjectName("btn_secondary")
        btn_up.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        btn_up.setToolTip("Переместить вверх")
        btn_up.clicked.connect(self._move_up)

        btn_down = QPushButton()
        btn_down.setFixedSize(26, 26)
        btn_down.setObjectName("btn_secondary")
        btn_down.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
        btn_down.setToolTip("Переместить вниз")
        btn_down.clicked.connect(self._move_down)

        btn_del_node = QPushButton()
        btn_del_node.setFixedSize(26, 26)
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

    def _rebuild_nodes(self):
        self.node_list.blockSignals(True)
        row = self.node_list.currentRow()
        self.node_list.clear()
        scene = self._get_current_scene()
        if scene:
            for i, node in enumerate(scene.nodes):
                item = QListWidgetItem(f"  {i+1:02d}  {node.preview_text()}")
                self.node_list.addItem(item)
            if scene.nodes:
                r = max(0, min(row, len(scene.nodes) - 1))
                self.node_list.setCurrentRow(r)
        self.node_list.blockSignals(False)

    def refresh_current_node_text(self):
        scene = self._get_current_scene()
        row = self.node_list.currentRow()
        if scene and 0 <= row < len(scene.nodes):
            self.node_list.item(row).setText(
                f"  {row+1:02d}  {scene.nodes[row].preview_text()}"
            )

    def _select_node_row(self, row: int):
        """Выбирает строку в списке узлов и ГАРАНТИРОВАННО уведомляет об этом,
        даже если currentRow уже равен row (Qt в этом случае не эмиттит
        currentRowChanged сам, а нам нужно прогрузить узел в редактор)."""
        if self.node_list.currentRow() == row:
            scene_idx = self.scene_list.currentRow()
            self.node_selected.emit(scene_idx, row)
        else:
            self.node_list.setCurrentRow(row)

    def notify_current_selection(self):
        """Принудительно уведомляет внешний код о текущей выбранной сцене/узле.
        Нужно вызывать после операций, где список перестраивается с заблокированными
        сигналами (Qt не уведомит сам, если индекс строки не изменился)."""
        scene_idx = self.scene_list.currentRow()
        node_idx = self.node_list.currentRow()
        self.node_selected.emit(scene_idx, node_idx)

    def _get_current_scene(self) -> Optional[Scene]:
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

    def _on_node_changed(self, idx: int):
        scene_idx = self.scene_list.currentRow()
        self.node_selected.emit(scene_idx, idx)


    def _add_scene(self):
        if not self.project:
            return
        name, ok = QInputDialog.getText(self, "Новая сцена", "Название:")
        if ok and name.strip():
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
            self.project.scenes.pop(idx)
            self._current_scene = max(0, idx - 1)
            self._rebuild_scenes()
            self.notify_current_selection()


    def _add_node(self):
        scene = self._get_current_scene()
        if not scene:
            return
        node = SceneNode(node_type=NodeType.DIALOGUE)
        row = self.node_list.currentRow()
        if row < 0:
            scene.nodes.append(node)
        else:
            scene.nodes.insert(row + 1, node)
        self._rebuild_nodes()
        new_row = row + 1 if row >= 0 else len(scene.nodes) - 1
        self._select_node_row(new_row)

    def _dup_node(self):
        scene = self._get_current_scene()
        if not scene:
            return
        row = self.node_list.currentRow()
        if 0 <= row < len(scene.nodes):
            import copy, uuid
            dup = copy.deepcopy(scene.nodes[row])
            dup.node_id = str(uuid.uuid4())[:8]
            scene.nodes.insert(row + 1, dup)
            self._rebuild_nodes()
            self.node_list.setCurrentRow(row + 1)

    def _move_up(self):
        scene = self._get_current_scene()
        if not scene:
            return
        row = self.node_list.currentRow()
        if row > 0:
            scene.nodes[row], scene.nodes[row-1] = scene.nodes[row-1], scene.nodes[row]
            self._rebuild_nodes()
            self.node_list.setCurrentRow(row - 1)
            self.node_order_changed.emit()

    def _move_down(self):
        scene = self._get_current_scene()
        if not scene:
            return
        row = self.node_list.currentRow()
        if row < len(scene.nodes) - 1:
            scene.nodes[row], scene.nodes[row+1] = scene.nodes[row+1], scene.nodes[row]
            self._rebuild_nodes()
            self.node_list.setCurrentRow(row + 1)
            self.node_order_changed.emit()

    def _del_node(self):
        scene = self._get_current_scene()
        if not scene:
            return
        row = self.node_list.currentRow()
        if 0 <= row < len(scene.nodes):
            scene.nodes.pop(row)
            self._rebuild_nodes()
            new_row = self.node_list.currentRow()
            scene_idx = self.scene_list.currentRow()
            self.node_selected.emit(scene_idx, new_row)


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
        title.setStyleSheet("color:#ff8c00; font-size:13px; font-weight:bold; padding:4px;")
        layout.addWidget(title)

        preview_wrap = QFrame()
        preview_wrap.setStyleSheet("QFrame { background:#0c0c10; border:1px solid #3a3a4a; border-radius:6px; }")
        pw_layout = QVBoxLayout(preview_wrap)
        pw_layout.setContentsMargins(6, 6, 6, 6)

        self.preview = ScenePreview()

        preview_scroll = QScrollArea()
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
        self.hint_lbl.setStyleSheet("color:#777; font-size:10px; padding:2px 4px;")
        layout.addWidget(self.hint_lbl)

        self.step_lbl = QLabel("")
        self.step_lbl.setWordWrap(True)
        self.step_lbl.setStyleSheet("color:#aaa; font-size:11px; padding:4px;")
        layout.addWidget(self.step_lbl)

        layout.addStretch()

        self.preview.sprite_moved.connect(self._on_sprite_dragged)
        self.preview.sprite_delete_requested.connect(self._on_sprite_delete_requested)
        self._current_node: Optional[SceneNode] = None
        self._current_scene: Optional[Scene] = None
        self._current_node_index: int = -1

    def set_context(self, rm: ResourceManager, project: Project):
        self.rm = rm
        self.project = project

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
            self.preview.set_dialogue("", "")
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
        if state.char_var and self.project:
            char = self.project.get_character_by_var(state.char_var)
            char_label = char.name if char else state.char_var
        self.preview.set_dialogue(char_label, state.text)

        self.step_lbl.setText(f"Шаг {node_index + 1} из {len(scene.nodes)}: {scene.nodes[node_index].preview_text()}")

    def _on_sprite_dragged(self, xalign: float):
        if self._current_node and self._current_node.node_type == NodeType.SHOW_SPRITE:
            self._current_node.xalign = xalign
            self.sprite_position_changed.emit(xalign)

    def _on_sprite_delete_requested(self, tag: str):
        """Клик (без перемещения) по спрайту в превью: удаляет из сцены узел
        SHOW_SPRITE, который вывел этот тег на экран к текущему шагу. Ищем
        с конца назад от текущего шага — это и есть узел, отвечающий за
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
        self.rm.scan()
        self._current_scene_idx = 0
        self._current_node_idx = -1

        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._load_project_to_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.scene_panel = SceneListPanel()
        self.scene_panel.setMinimumWidth(230)
        self.scene_panel.setMaximumWidth(320)
        self.scene_panel.scene_selected.connect(self._on_scene_selected)
        self.scene_panel.node_selected.connect(self._on_node_selected)
        self.scene_panel.node_order_changed.connect(self._on_node_changed)
        splitter.addWidget(self.scene_panel)

        self.node_editor = NodeEditor(self.rm)
        self.node_editor.set_characters(self.pm.project.characters)
        self.node_editor.node_changed.connect(self._on_node_changed)
        self.node_editor.refresh_resources()

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
        act_new.triggered.connect(self._new_project)
        file_menu.addAction(act_new)

        act_open = QAction("Открыть...", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self._open_project)
        file_menu.addAction(act_open)

        act_save = QAction("Сохранить", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self._save_project)
        file_menu.addAction(act_save)

        act_save_as = QAction("Сохранить как...", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(self._save_project_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()
        act_quit = QAction("Выход", self)
        act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        proj_menu = mb.addMenu("Проект")

        act_chars = QAction("Персонажи...", self)
        act_chars.setShortcut(QKeySequence("Ctrl+P"))
        act_chars.triggered.connect(self._edit_characters)
        proj_menu.addAction(act_chars)

        act_res = QAction("Настройки ресурсов...", self)
        act_res.triggered.connect(self._edit_resources)
        proj_menu.addAction(act_res)

        act_download_res = QAction("Скачать ресурсы для модификаций...", self)
        act_download_res.triggered.connect(self._show_resources_download)
        proj_menu.addAction(act_download_res)

        act_rescan = QAction("Переиндексировать ресурсы", self)
        act_rescan.setShortcut(QKeySequence("F5"))
        act_rescan.triggered.connect(self._rescan_resources)
        proj_menu.addAction(act_rescan)

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
        act_preview.triggered.connect(self._show_code_preview)
        gen_menu.addAction(act_preview)

        act_export = QAction("Экспорт .rpy...", self)
        act_export.setShortcut(QKeySequence("Ctrl+E"))
        act_export.triggered.connect(self._export_rpy)
        gen_menu.addAction(act_export)

        act_defines = QAction("Экспорт блока defines...", self)
        act_defines.triggered.connect(self._export_defines)
        gen_menu.addAction(act_defines)

        gen_menu.addSeparator()
        act_res_defines = QAction("Экспорт defines ресурсов...", self)
        act_res_defines.triggered.connect(self._export_resource_defines)
        gen_menu.addAction(act_res_defines)

        help_menu = mb.addMenu("Справка")

        act_guide = QAction("Руководство пользователя...", self)
        act_guide.setShortcut(QKeySequence("F1"))
        act_guide.triggered.connect(self._show_help)
        help_menu.addAction(act_guide)

    def _setup_toolbar(self):
        tb = QToolBar("Основная панель")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(tb)
        style = self.style()

        def act(label, shortcut, slot, icon=None):
            a = QAction(label, self)
            if icon is not None:
                a.setIcon(style.standardIcon(icon))
            if shortcut:
                a.setShortcut(QKeySequence(shortcut))
            a.triggered.connect(slot)
            return a

        SP = QStyle.StandardPixmap
        tb.addAction(act("Новый", "Ctrl+N", self._new_project, SP.SP_FileIcon))
        tb.addAction(act("Открыть", "Ctrl+O", self._open_project, SP.SP_DialogOpenButton))
        tb.addAction(act("Сохранить", "Ctrl+S", self._save_project, SP.SP_DialogSaveButton))
        tb.addSeparator()
        tb.addAction(act("Персонажи", "Ctrl+P", self._edit_characters, SP.SP_FileDialogContentsView))
        tb.addAction(act("Переиндексировать", "F5", self._rescan_resources, SP.SP_DirIcon))
        tb.addAction(act("Скачать ресурсы", "", self._show_resources_download, SP.SP_DriveNetIcon))
        tb.addSeparator()
        tb.addAction(act("Генерировать", "Ctrl+G", self._show_code_preview, SP.SP_FileDialogDetailedView))
        tb.addAction(act("Экспорт .rpy", "Ctrl+E", self._export_rpy, SP.SP_DialogSaveButton))
        tb.addSeparator()
        tb.addAction(act("Руководство", "F1", self._show_help, SP.SP_DialogHelpButton))

        tb.addSeparator()
        self.lbl_project = QLabel()
        self.lbl_project.setStyleSheet("color: #ff8c00; font-weight: bold; padding: 0 12px;")
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
        self.setWindowTitle(f"RenPy Visual Script Editor — {p.title}")
        self.lbl_project.setText(f"Проект: {p.title}")
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

    def _new_project(self):
        reply = QMessageBox.question(self, "Новый проект",
                                     "Создать новый проект? Несохранённые данные будут потеряны.")
        if reply == QMessageBox.StandardButton.Yes:
            name, ok = QInputDialog.getText(self, "Новый проект", "Название проекта:", text="Мой проект")
            if ok:
                self.pm.new_project(name.strip() or "Мой проект")
                self._load_project_to_ui()
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
                self.status_lbl.setText(f"Загружен: {path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось загрузить проект")

    def _save_project(self):
        if not self.pm.current_path:
            self._save_project_as()
        else:
            ok = self.pm.save()
            if ok:
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
                self.status_lbl.setText(f"Сохранено: {path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить проект")


    def _rename_project(self):
        name, ok = QInputDialog.getText(self, "Переименовать проект",
                                        "Название:", text=self.pm.project.title)
        if ok and name.strip():
            self.pm.project.title = name.strip()
            self.setWindowTitle(f"RenPy Visual Script Editor — {self.pm.project.title}")
            self.lbl_project.setText(f"Проект: {self.pm.project.title}")

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

    def _edit_resources(self):
        dlg = ResourcesConfigDialog(self.rm, self)
        dlg.exec()
        self._rescan_resources()

    def _show_resources_download(self):
        dlg = ResourcesDownloadDialog(self)
        dlg.exec()

    def _show_help(self):
        dlg = HelpDialog(self)
        dlg.exec()

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

    def _on_node_selected(self, scene_idx: int, node_idx: int):
        p = self.pm.project
        self._current_scene_idx = scene_idx
        self._current_node_idx = node_idx
        loaded = False
        if 0 <= scene_idx < len(p.scenes):
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

    def _on_sprite_dragged_in_preview(self, xalign: float):
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
        scene = p.scenes[scene_idx] if 0 <= scene_idx < len(p.scenes) else None
        self.preview_panel.show_state(scene, node_idx, p)

    def _show_code_preview(self):
        full = generate_full_script(self.pm.project, rm=self.rm)
        defines = generate_defines_only(self.pm.project)
        res_defines = self.rm.generate_define_block()
        combined_defines = res_defines + "\n" + defines
        dlg = CodePreviewDialog(full, combined_defines, self)
        dlg.exec()

    def _export_rpy(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт сценария", "script.rpy",
            "Ren'Py Script (*.rpy);;Все файлы (*)"
        )
        if path:
            try:
                code = generate_full_script(self.pm.project, rm=self.rm)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(code)
                self.status_lbl.setText(f"Экспортировано: {path}")
                QMessageBox.information(self, "Готово", f"Сценарий сохранён:\n{path}")
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
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(code)
                self.status_lbl.setText(f"Defines экспортированы: {path}")
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
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(code)
                self.status_lbl.setText(f"Defines ресурсов сохранены: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Выход",
            "Сохранить проект перед выходом?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Save:
            self._save_project()
            event.accept()
        elif reply == QMessageBox.StandardButton.Discard:
            event.accept()
        else:
            event.ignore()
