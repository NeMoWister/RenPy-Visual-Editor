"""
Поиск "где используется" для конкретного ресурса (var_name) по всему проекту:
обходит все сцены и, рекурсивно, все вложенные ноды веток меню (см.
SceneNode.normalized_menu_choices / доработку #1), собирая индекс
var_name -> список мест использования с "хлебными крошками" для навигации.

Категория ресурса (bg/cg/sprites/music/sounds/ambience) в самом индексе не
нужна: var_name внутри одного проекта не пересекается между категориями на
практике (авто-имена разных категорий формируются по-разному - 'bg x',
'cg x', 'sfx_x', 'music_list["x"]", голый 'x' для спрайтов), поэтому просто
матчим по значению поля ноды.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from core.models import Project, SceneNode, NodeType

                                                                          
                                                              
BranchPath = List[Tuple[str, int]]


@dataclass
class UsageRef:
    scene_id: str
    scene_name: str
    node_id: str
    node_type: str
    preview: str
    breadcrumb: str
    branch_path: BranchPath = field(default_factory=list)


def _node_resource_vars(node: SceneNode) -> List[str]:
    """var_name всех ресурсов, на которые ссылается конкретная нода."""
    t = node.node_type
    if t in (NodeType.SHOW_BG, NodeType.SCENE):
        return [node.bg_var] if node.bg_var else []
    if t == NodeType.SHOW_CG:
        return [node.cg_var] if node.cg_var else []
    if t == NodeType.SHOW_SPRITE:
        return [node.sprite_var] if node.sprite_var else []
    if t == NodeType.HIDE_SPRITE:
        return [node.sprite_tag] if node.sprite_tag else []
    if t == NodeType.PLAY_MUSIC:
        return [node.music_var] if node.music_var else []
    if t == NodeType.PLAY_SOUND:
        return [node.sound_var] if node.sound_var else []
    if t == NodeType.PLAY_AMBIENCE:
        return [node.ambience_var] if node.ambience_var else []
    return []


def scan_project_usage(project: Project) -> Dict[str, List[UsageRef]]:
    """Строит индекс var_name -> [UsageRef, ...] по всему проекту, включая
    ноды внутри веток меню (на любую глубину вложенности)."""
    index: Dict[str, List[UsageRef]] = {}

    def add(var: str, ref: UsageRef):
        index.setdefault(var, []).append(ref)

    def walk(nodes: List[SceneNode], scene_id: str, scene_name: str,
             branch_path: BranchPath, breadcrumb: str):
        for node in nodes:
            for var in _node_resource_vars(node):
                add(var, UsageRef(
                    scene_id=scene_id, scene_name=scene_name, node_id=node.node_id,
                    node_type=node.node_type.value, preview=node.preview_text(),
                    breadcrumb=breadcrumb, branch_path=list(branch_path),
                ))
            if node.node_type == NodeType.MENU:
                for ci, (text, jump, use_call, raw_body, choice_nodes) in enumerate(node.normalized_menu_choices()):
                    if choice_nodes:
                        choice_label = (text or "(без текста)")[:24]
                        sub_crumb = f'{breadcrumb} › «{choice_label}»'
                        walk(choice_nodes, scene_id, scene_name,
                             branch_path + [(node.node_id, ci)], sub_crumb)

    for scene in project.scenes:
        walk(scene.nodes, scene.scene_id, scene.name, [], scene.name)

    return index


def find_usages(project: Project, var_name: str) -> List[UsageRef]:
    if not var_name:
        return []
    return scan_project_usage(project).get(var_name, [])
