"""
Вспомогательная навигация по проекту для режима «презентации» - быстрого
прогона сценария по нодам с показом результата подряд, без экспорта в
Ren'Py. Не полноценная VM Ren'Py: call-стек не поддерживается (return
просто завершает прогон), но jump/label по меткам работают.
"""
from dataclasses import dataclass
from typing import Optional, Tuple, List

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
    возвращает позицию НАЧАЛА выполнения - ноду сразу ПОСЛЕ метки (если её
    нет - саму метку)."""
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


def iter_positions(project: Project):
    """Все позиции проекта в физическом порядке (сцена за сценой, нода за
    нодой) - ТОТ ЖЕ порядок, в котором code_generator раскладывает их по
    файлу. Не следует jump/label - просто линейный проход по списку нод."""
    for si, scene in enumerate(project.scenes):
        for ni in range(len(scene.nodes)):
            yield Position(si, ni)


def fast_forward_state(project: Project, target: Position, rm=None):
    """Восстанавливает визуальное состояние (фон/CG/спрайты/текущий
    персонаж) и "что сейчас должно играть" (последний play_music/play_ambience
    до target), чтобы можно было начать прогон презентации не с начала, а с
    произвольной ноды/метки - БЕЗ повторного проигрывания побочных эффектов
    (звуки не спамятся, переходы не воспроизводятся).

    Намеренно идёт по ФИЗИЧЕСКОМУ порядку нод (см. iter_positions), а не по
    графу jump/label: с учётом того, что в сценариях бывают циклы (jump
    назад), "честная" симуляция ходов игрока потребовала бы либо угадывать
    его выбор в каждом menu, либо рисковать бесконечным циклом. Физический
    порядок - предсказуемая и быстрая (без риска зависания) аппроксимация,
    которая на практике совпадает с сюжетным для большинства линейных
    сценариев (в духе того, как их же раскладывает генератор кода).

    Возвращает (SceneState, last_music_node_or_None, last_ambience_node_or_None,
    last_label_name, nvl_lines) - nvl_lines это накопленные к этому моменту
    строки NVL-экрана (char_label, text, color), если мы сейчас в NVL-режиме
    (сбрасывается при enter/clear) - нужно, чтобы "запуск презентации не с
    начала" и перемотка назад по репликам корректно показывали уже
    накопленный NVL-текст, а не только текущую строку.
    """
    from core.scene_state import SceneState, _apply_node

    state = SceneState()
    last_music = None
    last_ambience = None
    last_label = ""
    nvl_lines: List[tuple] = []

    def char_label_for(node) -> str:
        if node.node_type == NodeType.NARRATION or not node.character_var:
            return ""
        ch = project.get_character_by_var(node.character_var)
        return ch.name if ch else node.character_var

    for pos in iter_positions(project):
        if pos.scene_idx > target.scene_idx or \
                (pos.scene_idx == target.scene_idx and pos.node_idx >= target.node_idx):
            break
        node = project.scenes[pos.scene_idx].nodes[pos.node_idx]
        prev_nvl_mode = state.nvl_mode
        _apply_node(state, node, is_current=False, rm=rm)
        if node.node_type == NodeType.LABEL:
            last_label = node.label_name
        elif node.node_type == NodeType.PLAY_MUSIC:
            last_music = node
        elif node.node_type == NodeType.STOP_MUSIC:
            last_music = None
        elif node.node_type == NodeType.PLAY_AMBIENCE:
            last_ambience = node
        elif node.node_type == NodeType.STOP_AMBIENCE:
            last_ambience = None
        elif node.node_type == NodeType.NVL_MODE and node.nvl_action in ("enter", "clear"):
            nvl_lines = []
        elif node.node_type in (NodeType.DIALOGUE, NodeType.NARRATION) and prev_nvl_mode:
                                                                       
                                                                          
            ch = project.get_character_by_var(node.character_var) if node.character_var else None
            color = ch.color if ch else None
            nvl_lines.append((char_label_for(node), node.text, color))
            nvl_lines = nvl_lines[-8:]

    return state, last_music, last_ambience, last_label, nvl_lines
