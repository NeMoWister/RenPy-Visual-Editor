"""
Вспомогательная навигация по проекту для режима «презентации» — быстрого
прогона сценария по нодам с показом результата подряд, без экспорта в
Ren'Py. Не полноценная VM Ren'Py: call-стек не поддерживается (return
просто завершает прогон), но jump/label по меткам работают.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

from core.models import Project, NodeType


@dataclass(frozen=True)
class Position:
    scene_idx: int
    node_idx: int


def first_position(project: Project) -> Optional[Position]:
    for si, scene in enumerate(project.scenes):
        if scene.nodes:
            return Position(si, 0)
    return None


def next_position(project: Project, pos: Position) -> Optional[Position]:
    scene = project.scenes[pos.scene_idx]
    if pos.node_idx + 1 < len(scene.nodes):
        return Position(pos.scene_idx, pos.node_idx + 1)
    for si in range(pos.scene_idx + 1, len(project.scenes)):
        if project.scenes[si].nodes:
            return Position(si, 0)
    return None


def find_label(project: Project, label_name: str) -> Optional[Position]:
    """Ищет ноду LABEL с данным именем по всему проекту (по всем сценам),
    возвращает позицию НАЧАЛА выполнения — ноду сразу ПОСЛЕ метки (если её
    нет — саму метку)."""
    if not label_name:
        return None
    for si, scene in enumerate(project.scenes):
        for ni, node in enumerate(scene.nodes):
            if node.node_type == NodeType.LABEL and node.label_name == label_name:
                if ni + 1 < len(scene.nodes):
                    return Position(si, ni + 1)
                for sj in range(si + 1, len(project.scenes)):
                    if project.scenes[sj].nodes:
                        return Position(sj, 0)
                return None
    return None


def node_at(project: Project, pos: Position):
    return project.scenes[pos.scene_idx].nodes[pos.node_idx]


def scene_at(project: Project, pos: Position):
    return project.scenes[pos.scene_idx]
