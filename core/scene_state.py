# -*- coding: utf-8 -*-
"""
Вычисление визуального состояния сцены (фон, CG, активные спрайты,
текущая реплика) на момент конкретного узла — используется для
предпросмотра сцены.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from .models import Scene, SceneNode, NodeType, SpritePosition
from .composite_sprite_parser import CompositeSprite


@dataclass
class ActiveSprite:
    var: str
    expression: Optional[str]
    position: SpritePosition
    tag: str
    group_path: str = ""  # топ-уровневая папка персонажа (и подпапка вариации) для обычных папочных спрайтов
    composite: Optional[CompositeSprite] = None  # заполнено, если это составной спрайт из sprites.rpy

    def top_group(self) -> str:
        """Имя персонажа: для составного спрайта — CompositeSprite.character,
        для обычного папочного — первый сегмент group_path."""
        if self.composite is not None:
            return self.composite.character
        return self.group_path.split('/')[0] if self.group_path else ""


@dataclass
class SceneState:
    bg_var: Optional[str] = None
    cg_var: Optional[str] = None
    sprites: Dict[str, ActiveSprite] = field(default_factory=dict)
    char_var: Optional[str] = None
    text: str = ""

    def sprite_list(self) -> List[ActiveSprite]:
        return list(self.sprites.values())


def compute_state_up_to(scene: Scene, node_index: int, rm=None) -> SceneState:
    """
    Проигрывает узлы сцены с начала до node_index (включительно) и
    возвращает итоговое визуальное состояние: какой фон/CG показан,
    какие спрайты на экране и где, какая реплика говорится сейчас.

    rm (ResourceManager, опционально) — если передан, для каждого активного
    спрайта разрешается его group_path (папка персонажа/вариации) для обычных
    спрайтов, либо CompositeSprite (персонаж/позиция/слои) для составных из
    sprites.rpy — нужно, чтобы можно было "скрыть любого спрайта персонажа X"
    без знания точного тега/вариации.
    """
    state = SceneState()
    if node_index < 0:
        return state

    last_index = min(node_index, len(scene.nodes) - 1)
    for i in range(last_index + 1):
        node = scene.nodes[i]
        _apply_node(state, node, is_current=(i == last_index), rm=rm)
    return state


def _resolve_sprite_tag(node: SceneNode, rm) -> tuple:
    """Возвращает (tag, composite_or_none) для узла SHOW_SPRITE/HIDE_SPRITE.
    Если sprite_var совпадает с составным спрайтом (sprites.rpy) — тег по
    умолчанию это имя персонажа (первое слово), а не полное составное имя,
    поэтому `hide cs` отрабатывает корректно без явного sprite_tag."""
    composite = rm.find_composite_by_name(node.sprite_var) if (rm is not None and node.sprite_var) else None
    if composite is not None:
        tag = node.sprite_tag or composite.character
        return tag, composite
    tag = node.sprite_tag or node.sprite_var
    return tag, None


def _apply_node(state: SceneState, node: SceneNode, is_current: bool, rm=None):
    t = node.node_type

    if t in (NodeType.SHOW_BG, NodeType.SCENE):
        state.bg_var = node.bg_var or None
        # Новый фон полностью переопределяет видимую сцену: CG (полноэкранная
        # картинка поверх фона) больше не актуален, иначе он навечно
        # перекрывал бы все последующие фоны в предпросмотре.
        state.cg_var = None
        # "scene"/смена фона в Ren'Py обычно сбрасывает спрайты на экране
        if t == NodeType.SCENE:
            state.sprites.clear()
    elif t == NodeType.SHOW_CG:
        state.cg_var = node.cg_var or None
    elif t == NodeType.HIDE_CG:
        state.cg_var = None
    elif t == NodeType.SHOW_SPRITE:
        if node.sprite_var:
            tag, composite = _resolve_sprite_tag(node, rm)
            group_path = ""
            if composite is None and rm is not None:
                entry = rm.find_by_var(node.sprite_var)
                if entry:
                    group_path = entry.group_path
            state.sprites[tag] = ActiveSprite(
                var=node.sprite_var,
                expression=node.sprite_expression,
                position=SpritePosition(
                    xalign=node.sprite_position.xalign,
                    yalign=node.sprite_position.yalign,
                    zoom=node.sprite_position.zoom,
                ),
                tag=tag,
                group_path=group_path,
                composite=composite,
            )
    elif t == NodeType.HIDE_SPRITE:
        if node.hide_group:
            # Скрыть ЛЮБОЙ активный спрайт, чья папка персонажа (верхний
            # уровень group_path, либо character у составного спрайта)
            # совпадает с hide_group — без необходимости знать точный
            # тег/вариацию, которая сейчас показана.
            to_remove = [tag for tag, sp in state.sprites.items() if sp.top_group() == node.hide_group]
            for tag in to_remove:
                del state.sprites[tag]
        else:
            tag, _ = _resolve_sprite_tag(node, rm)
            if tag and tag in state.sprites:
                del state.sprites[tag]

    if is_current:
        if t == NodeType.DIALOGUE:
            state.char_var = node.character_var or None
            state.text = node.text
        elif t == NodeType.NARRATION:
            state.char_var = None
            state.text = node.text
        else:
            # Для несценических узлов (label, jump, музыка и т.п.)
            # оставляем последнюю показанную реплику пустой, чтобы
            # не путать пользователя текстом из прошлого узла.
            if t not in (NodeType.SHOW_BG, NodeType.SHOW_CG, NodeType.SCENE,
                         NodeType.SHOW_SPRITE, NodeType.HIDE_SPRITE,
                         NodeType.HIDE_CG):
                state.char_var = None
                state.text = ""
