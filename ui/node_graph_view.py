"""
Визуальный canvas-граф нод сцены (альтернатива списку).

NodeGraphCanvas - самодостаточный виджет: рисует ноды сцены сверху вниз,
стрелки последовательности, пунктирные стрелки jump/menu -> label, рамки
групп (сворачиваемые), поддерживает pan/zoom, мини-карту, поиск и цветовые
метки. Все мутации модели (порядок, группы, цвета, копирование) идут через
переданный `panel` (SceneListPanel) - так undo/redo, отрисовка списка и
canvas остаются синхронизированы автоматически.
"""
import json
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsObject, QGraphicsItem, QGraphicsPathItem, QLineEdit, QPushButton,
    QMenu, QColorDialog, QInputDialog, QLabel, QToolButton, QGraphicsRectItem
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QSizeF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QWheelEvent,
    QMouseEvent, QLinearGradient, QPolygonF, QKeySequence
)

from core.models import Scene, SceneNode, NodeType, NodeGroup

NODE_W = 260
NODE_H = 54
GAP_Y = 22
GROUP_HEADER_H = 26
GROUP_PAD = 14
LEFT_X = 40

DEFAULT_COLORS = ["#ff5b3d", "#ff8c3d", "#ffd23f", "#4cd97b", "#3fb6ff", "#a78bfa", "#ff6fb0", "#8a8a94"]


def _clip(text: str, n: int) -> str:
    text = text.replace("\n", " ")
    return text[:n] + ("…" if len(text) > n else "")


class NodeBoxItem(QGraphicsObject):
    clicked = pyqtSignal(int)
    context_requested = pyqtSignal(int, object)

    def __init__(self, row: int, node: SceneNode, is_current: bool = False, matched: bool = False):
        super().__init__()
        self.row = row
        self.node = node
        self.is_current = is_current
        self.matched = matched
        self.setAcceptHoverEvents(True)
        self._hover = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setZValue(10)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, NODE_W, NODE_H)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.boundingRect()

        base = QColor("#232330") if not self._hover else QColor("#2a2a3a")
        painter.setBrush(QBrush(base))
        border_color = QColor("#ff5b3d") if self.isSelected() else QColor("#3d3d4a")
        pen = QPen(border_color, 2.4 if self.isSelected() else 1.2)
        painter.setPen(pen)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)

        if self.node.color_tag:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(self.node.color_tag)))
            painter.drawRoundedRect(QRectF(0, 0, 6, NODE_H), 3, 3)

        painter.setPen(QColor("#f1f1f4"))
        f = QFont()
        f.setPointSize(9)
        painter.setFont(f)
        text = _clip(self.node.preview_text(), 42)
        painter.drawText(QRectF(14, 6, NODE_W - 24, NODE_H - 12),
                          Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
                          text)

        if self.is_current:
            painter.setPen(QPen(QColor("#ff8c3d"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)

        if self.matched and not self.isSelected():
            painter.setPen(QPen(QColor("#ffd23f"), 1.6, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 8, 8)

    def hoverEnterEvent(self, e):
        self._hover = True
        self.update()

    def hoverLeaveEvent(self, e):
        self._hover = False
        self.update()

    def mousePressEvent(self, e: QMouseEvent):
                                                                                     
                                                                       
        super().mousePressEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.row)

    def contextMenuEvent(self, e):
        if not self.isSelected():
            if self.scene() is not None:
                self.scene().clearSelection()
            self.setSelected(True)
            self.clicked.emit(self.row)
        self.context_requested.emit(self.row, e.screenPos())
        e.accept()


class GroupFrameItem(QGraphicsObject):
    toggle_requested = pyqtSignal(str)
    header_context = pyqtSignal(str, object)

    def __init__(self, group: NodeGroup, rect: QRectF, count: int):
        super().__init__()
        self.group = group
        self._rect = rect
        self.count = count
        self.setZValue(0)
        self.setAcceptHoverEvents(True)

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(self.group.color)
        header = QRectF(self._rect.x(), self._rect.y(), self._rect.width(), GROUP_HEADER_H)

        body_brush = QColor(color)
        body_brush.setAlpha(18)
        painter.setBrush(QBrush(body_brush))
        painter.setPen(QPen(color, 1.4))
        painter.drawRoundedRect(self._rect, 12, 12)

        head_brush = QColor(color)
        head_brush.setAlpha(70)
        painter.setBrush(QBrush(head_brush))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(header, 12, 12)
        painter.drawRect(QRectF(header.x(), header.y() + 10, header.width(), 10))

        painter.setPen(QColor("#101014"))
        f = QFont()
        f.setPointSize(9)
        f.setBold(True)
        painter.setFont(f)
        arrow = "▾" if not self.group.collapsed else "▸"
        label = f"{arrow}  {self.group.title}  ({self.count})"
        painter.drawText(header.adjusted(10, 0, -10, 0),
                          Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

    def mousePressEvent(self, e: QMouseEvent):
        header = QRectF(self._rect.x(), self._rect.y(), self._rect.width(), GROUP_HEADER_H)
        if header.contains(e.pos()) and e.button() == Qt.MouseButton.LeftButton:
            self.toggle_requested.emit(self.group.group_id)
            return
        e.ignore()

    def contextMenuEvent(self, e):
        header = QRectF(self._rect.x(), self._rect.y(), self._rect.width(), GROUP_HEADER_H)
        if header.contains(e.pos()):
            self.header_context.emit(self.group.group_id, e.screenPos())


def _arrow_path(p1: QPointF, p2: QPointF, dashed: bool = False, curve: bool = False) -> QPainterPath:
    path = QPainterPath(p1)
    if curve:
        dx = max(60.0, abs(p2.x() - p1.x()) * 0.6)
        c1 = QPointF(p1.x() + dx, p1.y())
        c2 = QPointF(p2.x() + dx, p2.y())
        path.cubicTo(c1, c2, p2)
    else:
        mid_y = (p1.y() + p2.y()) / 2
        path.cubicTo(QPointF(p1.x(), mid_y), QPointF(p2.x(), mid_y), p2)
    return path


class GraphScene(QGraphicsScene):
    pass


class MiniMapView(QGraphicsView):
    """Кликабельная мини-карта: показывает всю сцену целиком, клик/драг
    переносит основной вид к нужному месту."""
    navigate = pyqtSignal(QPointF)

    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.setFixedSize(190, 220)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QGraphicsView { background: rgba(20,20,26,215); border: 1px solid rgba(255,255,255,40);
                             border-radius: 10px; }
        """)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setInteractive(False)

    def refresh(self):
        r = self.scene().itemsBoundingRect()
        if r.isValid():
            r = r.adjusted(-40, -40, 40, 40)
            self.fitInView(r, Qt.AspectRatioMode.KeepAspectRatio)

    def _emit_nav(self, e):
        pt = self.mapToScene(e.pos())
        self.navigate.emit(pt)

    def mousePressEvent(self, e):
        self._emit_nav(e)

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton:
            self._emit_nav(e)


class GraphCanvasView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._panning = False
        self._pan_start = QPointF()
        self._zoom = 1.0
        self.owner = None                                                            
        self.setStyleSheet("QGraphicsView { background: #17171d; border: none; }")

    def wheelEvent(self, e: QWheelEvent):
        factor = 1.15 if e.angleDelta().y() > 0 else (1 / 1.15)
        new_zoom = self._zoom * factor
        if 0.25 <= new_zoom <= 2.5:
            self._zoom = new_zoom
            self.scale(factor, factor)
        e.accept()

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = e.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            e.accept()
            return
        super().mousePressEvent(e)
        self.setFocus(Qt.FocusReason.MouseFocusReason)

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._panning:
            delta = e.position() - self._pan_start
            self._pan_start = e.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            e.accept()
            return
        super().mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        if self.owner is not None:
            if e.matches(QKeySequence.StandardKey.Copy):
                self.owner.copy_selection()
                e.accept()
                return
            if e.matches(QKeySequence.StandardKey.Paste):
                self.owner.paste_after(self.owner._current_row)
                e.accept()
                return
        super().keyPressEvent(e)


class NodeGraphCanvas(QWidget):
    """Основной публичный виджет. `panel` - SceneListPanel, владеющий данными
    и уже умеющий делать undo-безопасные мутации (before_change и т.п)."""

    node_clicked = pyqtSignal(int)

    def __init__(self, panel, parent=None):
        super().__init__(parent)
        self.panel = panel
        self.scene: Optional[Scene] = None
        self._current_row = -1
        self._row_items = {}
        self._clipboard: List[dict] = []

        self.gscene = GraphScene(self)
        self.gscene.setBackgroundBrush(QColor("#17171d"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔎 Поиск по репликам / спрайтам / персонажам...")
        self.search_edit.setStyleSheet("""
            QLineEdit { background:#232330; color:#fff; border:1px solid #3d3d4a;
                        border-radius:6px; padding:5px 8px; font-size:12px; }
        """)
        self.search_edit.textChanged.connect(self._on_search)
        self.search_edit.returnPressed.connect(self._search_next)
        search_row.addWidget(self.search_edit, 1)
        self.search_status = QLabel("")
        self.search_status.setStyleSheet("color:#a8a8b3; font-size:11px;")
        search_row.addWidget(self.search_status)
        layout.addLayout(search_row)

        self.view = GraphCanvasView(self.gscene)
        self.view.owner = self
        self.view.setMinimumHeight(300)
        layout.addWidget(self.view, 1)

        self.minimap = MiniMapView(self.gscene, self.view)
        self.minimap.navigate.connect(self._on_minimap_navigate)

        self._search_matches: List[int] = []
        self._search_pos = -1

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._position_minimap()

    def _position_minimap(self):
        m = self.minimap
        vp = self.view.size()
        m.move(vp.width() - m.width() - 14, vp.height() - m.height() - 14)

    def showEvent(self, e):
        super().showEvent(e)
        self._position_minimap()

    def _on_minimap_navigate(self, scene_pt: QPointF):
        self.view.centerOn(scene_pt)

                                                                             

    def set_scene(self, scene: Optional[Scene], current_row: int, selected_rows=None):
        self.scene = scene
        self._current_row = current_row
        self._rebuild()

    def _group_for_node(self, node_id: str) -> Optional[NodeGroup]:
        if not self.scene:
            return None
        for g in self.scene.groups:
            if node_id in g.node_ids:
                return g
        return None

    def _rebuild(self):
        self.gscene.clear()
        self._row_items = {}
        if not self.scene or not self.scene.nodes:
            self.minimap.refresh()
            return

        nodes = self.scene.nodes
        y = 20.0
        positions = {}                    
        visible_rows = []
        i = 0
        rendered_group_ids = set()
        group_spans = []                                    

        while i < len(nodes):
            node = nodes[i]
            grp = self._group_for_node(node.node_id)
            if grp is not None and grp.group_id not in rendered_group_ids:
                rendered_group_ids.add(grp.group_id)
                member_rows = [r for r, n in enumerate(nodes) if n.node_id in grp.node_ids]
                if grp.collapsed:
                    top = y
                    y += GROUP_HEADER_H + GAP_Y
                    group_spans.append((grp, top, y - GAP_Y, member_rows))
                    for r in member_rows:
                        positions[r] = None                        
                    i = max(member_rows) + 1 if member_rows else i + 1
                    continue
                else:
                    top = y
                    y += GROUP_HEADER_H + GROUP_PAD
                    for r in member_rows:
                        if r < i:
                            continue
                        positions[r] = y
                        visible_rows.append(r)
                        y += NODE_H + GAP_Y
                    y += GROUP_PAD - GAP_Y
                    group_spans.append((grp, top, y, member_rows))
                    i = max(member_rows) + 1 if member_rows else i + 1
                    continue
            positions[i] = y
            visible_rows.append(i)
            y += NODE_H + GAP_Y
            i += 1

                                           
        for grp, top, bottom, member_rows in group_spans:
            rect = QRectF(LEFT_X - GROUP_PAD, top, NODE_W + GROUP_PAD * 2, bottom - top)
            item = GroupFrameItem(grp, rect, len(member_rows))
            item.setPos(0, 0)
            item.toggle_requested.connect(self._toggle_group)
            item.header_context.connect(self._group_context_menu)
            self.gscene.addItem(item)

               
        for r in visible_rows:
            py = positions.get(r)
            if py is None:
                continue
            node = nodes[r]
            box = NodeBoxItem(r, node, is_current=(r == self._current_row), matched=(r in self._search_matches))
            box.setPos(LEFT_X, py)
            if r == self._current_row:
                box.setSelected(True)
            box.clicked.connect(self._on_node_clicked)
            box.context_requested.connect(self._on_node_context)
            self.gscene.addItem(box)
            self._row_items[r] = (box, py)

                                                           
        vis_sorted = sorted(self._row_items.keys())
        for a, b in zip(vis_sorted, vis_sorted[1:]):
            y1 = self._row_items[a][1] + NODE_H
            y2 = self._row_items[b][1]
            p1 = QPointF(LEFT_X + NODE_W / 2, y1)
            p2 = QPointF(LEFT_X + NODE_W / 2, y2)
            path = _arrow_path(p1, p2)
            pen = QPen(QColor("#55555f"), 1.6)
            pitem = QGraphicsPathItem(path)
            pitem.setPen(pen)
            pitem.setZValue(1)
            self.gscene.addItem(pitem)

                                                                 
        label_row = {}
        for r, n in enumerate(nodes):
            if n.node_type == NodeType.LABEL and n.label_name:
                label_row[n.label_name] = r

        def target_pos(target_row):
            if target_row in self._row_items:
                py = self._row_items[target_row][1]
                return QPointF(LEFT_X, py + NODE_H / 2)
            return None

        for r, n in enumerate(nodes):
            if r not in self._row_items:
                continue
            src_box_y = self._row_items[r][1]
            src_pt = QPointF(LEFT_X, src_box_y + NODE_H / 2)
            targets = []
            if n.node_type == NodeType.JUMP and n.jump_target in label_row:
                targets.append(label_row[n.jump_target])
            elif n.node_type == NodeType.MENU:
                for choice in n.normalized_menu_choices():
                    jump = choice[1]
                    if jump and jump in label_row:
                        targets.append(label_row[jump])
            for tr in targets:
                if tr == r:
                    continue
                tp = target_pos(tr)
                if tp is None:
                    continue
                path = _arrow_path(src_pt, tp, dashed=True, curve=True)
                pen = QPen(QColor("#ff8c3d"), 1.4, Qt.PenStyle.DashLine)
                pitem = QGraphicsPathItem(path)
                pitem.setPen(pen)
                pitem.setZValue(1)
                self.gscene.addItem(pitem)

        self.gscene.setSceneRect(self.gscene.itemsBoundingRect().adjusted(-60, -60, 60, 60))
        self.minimap.refresh()

                                                                             

    def _on_node_clicked(self, row: int):
        self.node_clicked.emit(row)
        self._current_row = row
        for r, (box, py) in self._row_items.items():
            new_is_current = (r == row)
            if box.is_current != new_is_current:
                box.is_current = new_is_current
                box.update()
        self.view.setFocus(Qt.FocusReason.MouseFocusReason)

    def focus_row(self, row: int):
        if row in self._row_items:
            box, py = self._row_items[row]
            self.view.centerOn(box)

    def _selected_rows_list(self) -> List[int]:
        return sorted({item.row for item in self.gscene.selectedItems() if isinstance(item, NodeBoxItem)})

                                                                               

    def _on_node_context(self, row: int, screen_pos):
        rows = self._selected_rows_list()
        if row not in rows:
            rows = [row]
        self._current_row = row
        menu = QMenu(self)
        act_color = menu.addMenu("🎨 Цвет метки")
        for c in DEFAULT_COLORS:
            a = act_color.addAction("   ")
            a.setData(c)
            pm_icon = QColor(c)
            from PyQt6.QtGui import QIcon, QPixmap
            pix = QPixmap(16, 16)
            pix.fill(pm_icon)
            a.setIcon(QIcon(pix))
            a.triggered.connect(lambda checked=False, col=c, rows=rows: self.panel.set_nodes_color(rows, col))
        act_color.addSeparator()
        act_clear = act_color.addAction("Без метки")
        act_clear.triggered.connect(lambda checked=False, rows=rows: self.panel.set_nodes_color(rows, None))

        menu.addSeparator()
        act_copy = menu.addAction("📋 Копировать (Ctrl+C)")
        act_copy.triggered.connect(self.copy_selection)
        act_paste = menu.addAction("📥 Вставить после (Ctrl+V)")
        act_paste.setEnabled(bool(self._clipboard) or bool(self._read_system_clipboard()))
        act_paste.triggered.connect(lambda checked=False, row=row: self.paste_after(row))

        act_dup_branch = menu.addAction("🔁 Дублировать блок диалога (до label/return/конца)")
        act_dup_branch.triggered.connect(lambda checked=False, row=row: self.panel.duplicate_branch(row))

        if len(rows) >= 2:
            menu.addSeparator()
            act_group = menu.addAction(f"🗂 Сгруппировать выбранные ноды ({len(rows)})")
            act_group.triggered.connect(lambda checked=False, rows=rows: self._make_group(rows))

        menu.exec(screen_pos.toPoint() if hasattr(screen_pos, "toPoint") else screen_pos)

    def _group_context_menu(self, group_id: str, screen_pos):
        menu = QMenu(self)
        act_rename = menu.addAction("Переименовать группу...")
        act_rename.triggered.connect(lambda: self._rename_group(group_id))
        act_recolor = menu.addMenu("Цвет рамки")
        for c in DEFAULT_COLORS:
            a = act_recolor.addAction("   ")
            a.setData(c)
            from PyQt6.QtGui import QIcon, QPixmap
            pix = QPixmap(16, 16)
            pix.fill(QColor(c))
            a.setIcon(QIcon(pix))
            a.triggered.connect(lambda checked=False, col=c: self.panel.recolor_group(group_id, col))
        act_ungroup = menu.addAction("Разгруппировать")
        act_ungroup.triggered.connect(lambda: self.panel.ungroup(group_id))
        menu.exec(screen_pos.toPoint() if hasattr(screen_pos, "toPoint") else screen_pos)

    def _rename_group(self, group_id: str):
        grp = next((g for g in (self.scene.groups if self.scene else []) if g.group_id == group_id), None)
        if not grp:
            return
        title, ok = QInputDialog.getText(self, "Название группы", "Название:", text=grp.title)
        if ok and title.strip():
            self.panel.rename_group(group_id, title.strip())

    def _toggle_group(self, group_id: str):
        self.panel.toggle_group_collapsed(group_id)

    def _make_group(self, rows: List[int]):
        if not self.scene:
            return
                                                                 
        if rows != list(range(rows[0], rows[-1] + 1)):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Нельзя сгруппировать",
                                 "Можно сгруппировать только идущие подряд ноды.")
            return
        title, ok = QInputDialog.getText(self, "Новая группа", "Название группы (акт/глава):", text="Акт")
        if ok and title.strip():
            self.panel.create_group(rows, title.strip())

                                                                             

    def copy_selection(self):
        if not self.scene:
            return
        rows = self._selected_rows_list()
        if not rows and self._current_row >= 0:
            rows = [self._current_row]
        if not rows:
            return
        from core.project_manager import node_to_dict
        nodes_data = [node_to_dict(self.scene.nodes[r]) for r in rows if 0 <= r < len(self.scene.nodes)]
        self._clipboard = nodes_data
        try:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(json.dumps({"renpy_editor_nodes": nodes_data}, ensure_ascii=False))
        except Exception:
            pass

    def paste_after(self, row: int):
        clip = self._read_system_clipboard() or self._clipboard
        if not clip:
            return
        self.panel.paste_nodes_after(row, clip)

    def _read_system_clipboard(self):
        try:
            from PyQt6.QtWidgets import QApplication
            txt = QApplication.clipboard().text()
            data = json.loads(txt)
            nodes = data.get("renpy_editor_nodes")
            if isinstance(nodes, list) and nodes:
                return nodes
        except Exception:
            pass
        return None

                                                                              

    def _on_search(self, text: str):
        text = text.strip().lower()
        self._search_matches = []
        self._search_pos = -1
        if text and self.scene:
            for r, n in enumerate(self.scene.nodes):
                haystack = " ".join(filter(None, [
                    n.text, n.character_var, n.sprite_var, n.label_name,
                    n.jump_target, n.bg_var, n.cg_var, n.menu_prompt,
                ])).lower()
                if text in haystack:
                    self._search_matches.append(r)
        self.search_status.setText(f"{len(self._search_matches)} совп." if text else "")
        if self._search_matches:
            self._search_pos = 0
            self._goto_search_match()
        else:
            self._rebuild()

    def _search_next(self):
        if not self._search_matches:
            return
        self._search_pos = (self._search_pos + 1) % len(self._search_matches)
        self._goto_search_match()

    def _goto_search_match(self):
        row = self._search_matches[self._search_pos]
        self.node_clicked.emit(row)
        self._current_row = row
        self._rebuild()
        self.focus_row(row)
        self.search_status.setText(f"{self._search_pos + 1}/{len(self._search_matches)}")

