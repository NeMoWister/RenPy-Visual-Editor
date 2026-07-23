from typing import List, Dict, Optional
from .models import Project, Scene, SceneNode, NodeType, Character
from .custom_node_templates import CustomNodeTemplateStore

INDENT = "    "
COMMENT_PREFIX = "#"

                                                                          
                                                                             
                                                                              
_GROUPABLE_TRANSITION_TYPES = {
    NodeType.SCENE, NodeType.SHOW_BG, NodeType.SHOW_CG,
    NodeType.SHOW_SPRITE, NodeType.WINDOW,
}


def _fmt_seconds(value) -> str:
    """Форматирует число секунд для fadein/fadeout: целые без '.0' (3, не 3.0),
    дробные с одним знаком после запятой (1.5)."""
    value = round(float(value), 1)
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"


def _sprite_tag(node: SceneNode, rm=None) -> str:
    """Тег спрайта по умолчанию: для составных спрайтов из sprites.rpy — имя
    персонажа (первое слово имени), как и ожидает Ren'Py при show с составным
    именем (он сам берёт первое слово как тег) — поэтому hide cs работает,
    а не hide "cs normal stethoscope far". Для обычных спрайтов — var_name
    целиком, как раньше."""
    if node.sprite_tag:
        return node.sprite_tag
    if rm is not None and node.sprite_var:
        composite = rm.find_composite_by_name(node.sprite_var)
        if composite is not None:
            return composite.character
    return node.sprite_var or ""


def _render_sprite_show_lines(node: SceneNode, pad: str) -> List[str]:
    """Строки show-блока одного спрайта БЕЗ завершающего with — он добавляется
    отдельно вызывающей стороной (см. _render_sprite_group), чтобы несколько
    спрайтов с одинаковым переходом можно было объединить в один with-блок."""
    spr = node.sprite_var or ""
    if not spr:
        return []
    expr = f" {node.sprite_expression}" if node.sprite_expression else ""
    pos = node.sprite_position
    lines = [f"{pad}show {spr}{expr}:"]
    lines.append(f"{pad}{INDENT}xalign {pos.xalign:.2f}")
    lines.append(f"{pad}{INDENT}yalign {pos.yalign:.2f}")
    if pos.zoom != 1.0:
        lines.append(f"{pad}{INDENT}zoom {pos.zoom:.2f}")
    return lines


def _render_sprite_group(nodes: List[SceneNode], pad: str) -> List[str]:
    """Рендерит ПОДРЯД идущие SHOW_SPRITE-узлы с одинаковым transition как
    один блок:
        show a:
            xalign ...
        show b:
            xalign ...
        with dissolve
    Если transition пуст (\"без перехода\"), with-строка не добавляется.
    Ожидается, что все nodes уже отфильтрованы как имеющие одинаковый
    transition (см. generate_full_script, где группы формируются)."""
    lines: List[str] = []
    for node in nodes:
        lines.extend(_render_sprite_show_lines(node, pad))
    transition = nodes[0].transition if nodes else ""
    if transition:
        lines.append(f"{pad}with {transition}")
    return lines


def _render_node_no_transition(node: SceneNode, pad: str) -> List[str]:
    """Рендерит 'тело' групппируемой ноды БЕЗ хвостового 'with X' — для нод,
    которые попали в общую группу с единым переходом (см. _group_with_runs).
    Поддерживает только типы из _GROUPABLE_TRANSITION_TYPES."""
    t = node.node_type
    if t == NodeType.SHOW_SPRITE:
        return _render_sprite_show_lines(node, pad)
    if t == NodeType.SCENE:
        return [f"{pad}scene {node.bg_var or 'black'}"]
    if t == NodeType.SHOW_BG:
        return [f"{pad}show {node.bg_var or 'black'}"]
    if t == NodeType.SHOW_CG:
        return [f"{pad}show {node.cg_var}"] if node.cg_var else []
    if t == NodeType.WINDOW:
        return [f"{pad}window {node.window_action}"]
    return []


def generate_node(node: SceneNode, indent: int = 1, active_sprites: Optional[Dict[str, str]] = None,
                   rm=None, custom_templates: Optional[CustomNodeTemplateStore] = None) -> List[str]:
    """
    active_sprites: словарь {tag: group_path верхнего уровня (имя папки персонажа)}
    активных на сцене спрайтов на момент ДО этого узла — нужен только для
    HIDE_SPRITE с hide_group (скрыть "любой спрайт этого персонажа"), чтобы
    сгенерировать `hide <реальный_тег>` вместо неизвестной папки.
    Вызывающая сторона (generate_full_script) обновляет active_sprites после
    каждого узла через update_active_sprites().

    ВАЖНО: SHOW_SPRITE сюда передаётся для узлов, которые НЕ группируются
    (одиночный показ спрайта, не подряд с другими show_sprite одинакового
    перехода) — группировка происходит на уровне generate_full_script,
    которая вызывает _render_sprite_group напрямую для серий подряд идущих
    show_sprite с одинаковым переходом, минуя generate_node для них.
    """
    pad = INDENT * indent
    lines = []
    t = node.node_type

    if t == NodeType.COMMENT:
        if node.comment_text:
            lines.append(f"{pad}{COMMENT_PREFIX} {node.comment_text}")
    elif t == NodeType.LABEL:
        lines.append("")
        lines.append(f"label {node.label_name}:")
    elif t == NodeType.SCENE:
        bg = node.bg_var or "black"
        if node.transition:
            lines.append(f"{pad}scene {bg} with {node.transition}")
        else:
            lines.append(f"{pad}scene {bg}")
    elif t == NodeType.SHOW_BG:
        if node.transition:
            lines.append(f"{pad}show {node.bg_var or 'black'} with {node.transition}")
        else:
            lines.append(f"{pad}show {node.bg_var or 'black'}")
    elif t == NodeType.SHOW_CG:
        if node.cg_var:
            if node.transition:
                lines.append(f"{pad}show {node.cg_var} with {node.transition}")
            else:
                lines.append(f"{pad}show {node.cg_var}")
    elif t == NodeType.HIDE_CG:
        if node.cg_var:
            lines.append(f"{pad}hide {node.cg_var} with dissolve")
    elif t == NodeType.SHOW_SPRITE:
                                                                       
                                                                   
        lines.extend(_render_sprite_group([node], pad))
    elif t == NodeType.HIDE_SPRITE:
        if node.hide_group and active_sprites is not None:
                                                                                 
            tags = [tag for tag, group in active_sprites.items() if group == node.hide_group]
            for tag in tags:
                lines.append(f"{pad}hide {tag} with dissolve")
        else:
            tag = node.sprite_tag or node.sprite_var or ""
            if not node.sprite_tag and rm is not None and node.sprite_var:
                composite = rm.find_composite_by_name(node.sprite_var)
                if composite is not None:
                    tag = composite.character
            if tag:
                lines.append(f"{pad}hide {tag} with dissolve")
    elif t == NodeType.PLAY_MUSIC:
        if node.music_var:
            fadeout = f" fadeout {_fmt_seconds(node.music_fadeout)}" if node.music_fadeout else ""
            fadein = f" fadein {_fmt_seconds(node.music_fadein)}" if node.music_fadein else ""
            lines.append(f"{pad}play music {node.music_var}{fadeout}{fadein}")
    elif t == NodeType.STOP_MUSIC:
        fadeout = f" fadeout {_fmt_seconds(node.music_fadeout)}" if node.music_fadeout else ""
        lines.append(f"{pad}stop music{fadeout}")
    elif t == NodeType.PLAY_AMBIENCE:
        if node.ambience_var:
            fadeout = f" fadeout {_fmt_seconds(node.ambience_fadeout)}" if node.ambience_fadeout else ""
            fadein = f" fadein {_fmt_seconds(node.ambience_fadein)}" if node.ambience_fadein else ""
            lines.append(f"{pad}play ambience {node.ambience_var}{fadeout}{fadein}")
    elif t == NodeType.STOP_AMBIENCE:
        fadeout = f" fadeout {_fmt_seconds(node.ambience_fadeout)}" if node.ambience_fadeout else ""
        lines.append(f"{pad}stop ambience{fadeout}")
    elif t == NodeType.WINDOW:
        trans = f" with {node.transition}" if node.transition else ""
        lines.append(f"{pad}window {node.window_action}{trans}")
    elif t == NodeType.WITH_TRANSITION:
        if node.transition:
            lines.append(f"{pad}with {node.transition}")
    elif t == NodeType.PLAY_SOUND:
        if node.sound_var:
            lines.append(f"{pad}play sound {node.sound_var}")
    elif t == NodeType.DIALOGUE:
        text = node.text.replace('"', '\\"')
        if node.character_var:
            lines.append(f'{pad}{node.character_var} "{text}"')
        else:
            lines.append(f'{pad}"{text}"')
    elif t == NodeType.NARRATION:
        text = node.text.replace('"', '\\"')
        lines.append(f'{pad}"{text}"')
    elif t == NodeType.PAUSE:
        if node.pause_duration > 0:
            lines.append(f"{pad}pause {node.pause_duration:.1f}")
        else:
            lines.append(f"{pad}pause")
    elif t == NodeType.RETURN:
        lines.append(f"{pad}return")
    elif t == NodeType.JUMP:
        if node.jump_target:
            lines.append(f"{pad}jump {node.jump_target}")
    elif t == NodeType.MENU:
        prompt = node.menu_prompt.replace('"', '\\"')
        lines.append(f'{pad}menu:')
        if prompt:
            lines.append(f'{pad}{INDENT}"{prompt}"')
        for ct, cj, use_call, raw_body in node.normalized_menu_choices():
            ct = ct.replace('"', '\\"')
            lines.append(f'{pad}{INDENT}"{ct}":')
            if raw_body and raw_body.strip():
                                                                         
                                                          
                for bl in raw_body.splitlines():
                    lines.append(f'{pad}{INDENT}{INDENT}{bl}' if bl.strip() else '')
            elif cj:
                kw = "call" if use_call else "jump"
                lines.append(f'{pad}{INDENT}{INDENT}{kw} {cj}')
            else:
                lines.append(f'{pad}{INDENT}{INDENT}pass')
    elif t == NodeType.PYTHON:
        code_lines = node.python_code.splitlines()
        if len(code_lines) == 1:
            lines.append(f"{pad}$ {code_lines[0]}")
        else:
            lines.append(f"{pad}python:")
            for cl in code_lines:
                lines.append(f"{pad}{INDENT}{cl}" if cl.strip() else "")
    elif t == NodeType.RAW:
        for cl in node.python_code.splitlines():
            lines.append(f"{pad}{cl}" if cl.strip() else "")
    elif t == NodeType.CUSTOM:
        lines.extend(_render_custom_node(node, pad, custom_templates))
    return lines


def _render_custom_node(node: SceneNode, pad: str, custom_templates: Optional[CustomNodeTemplateStore]) -> List[str]:
    """Рендерит пользовательскую ноду (см. core/custom_node_templates.py) по
    её Jinja2-шаблону кода. Если хранилище шаблонов не передано, шаблон не
    найден или Jinja2 не установлен — выводит предупреждающий комментарий
    вместо кода (чтобы не потерять ноду молча)."""
    if custom_templates is None:
        return [f"{pad}{COMMENT_PREFIX} [пользовательская нода: хранилище шаблонов недоступно]"]
    tmpl = custom_templates.get(node.custom_template_id)
    if tmpl is None:
        return [f"{pad}{COMMENT_PREFIX} [пользовательская нода: шаблон '{node.custom_template_id}' не найден]"]
    rendered = custom_templates.render(tmpl, node.custom_params, pad=pad)
    if rendered is None:
        return [f"{pad}{COMMENT_PREFIX} [пользовательская нода '{tmpl.name}': Jinja2 не установлен]"]
    lines = []
    for line in rendered.splitlines():
        lines.append(line if line.strip() else "")
    return lines


def _update_active_sprites(active_sprites: Dict[str, str], node: SceneNode, rm=None):
    """Обновляет словарь {tag: top_group} активных спрайтов по факту узла —
    используется генератором, чтобы знать состояние сцены при встрече
    HIDE_SPRITE с hide_group. Логика зеркалит core/scene_state.py."""
    t = node.node_type
    if t == NodeType.SCENE:
        active_sprites.clear()
    elif t == NodeType.SHOW_SPRITE and node.sprite_var:
        composite = rm.find_composite_by_name(node.sprite_var) if rm is not None else None
        if composite is not None:
            tag = node.sprite_tag or composite.character
            top_group = composite.character
        else:
            tag = node.sprite_tag or node.sprite_var
            top_group = ""
            if rm is not None:
                entry = rm.find_by_var(node.sprite_var)
                if entry:
                    top_group = entry.group_parts()[0] if entry.group_parts() else ""
        active_sprites[tag] = top_group
    elif t == NodeType.HIDE_SPRITE:
        if node.hide_group:
            for tag in [tg for tg, grp in active_sprites.items() if grp == node.hide_group]:
                del active_sprites[tag]
        else:
            tag = _sprite_tag(node, rm)
            active_sprites.pop(tag, None)


def _group_with_runs(nodes: List[SceneNode]) -> List[List[SceneNode]]:
    """Разбивает список узлов сцены на единицы рендеринга, обобщая
    _group_consecutive_sprites на ЛЮБЫЕ группируемые типы, а не только
    show_sprite: подряд идущие ноды из _GROUPABLE_TRANSITION_TYPES с
    ОДИНАКОВЫМ непустым transition объединяются в один блок с единственным
    общим 'with X' в конце.

    Это нужно, чтобы при обратной генерации .rpy

        window hide
        scene black
        with dissolve

    не превращалось в семантически другой код

        window hide with dissolve
        scene black with dissolve

    (два последовательных перехода вместо одного общего — на импорте
    rpy_script_import.py кладёт оба узла в очередь 'pending' и присваивает
    им один и тот же transition, см. _PENDING_TRANSITION_TYPES; здесь это
    собирается обратно в исходную форму)."""
    units: List[List[SceneNode]] = []
    current: List[SceneNode] = []

    def is_groupable(node: SceneNode) -> bool:
        if node.node_type not in _GROUPABLE_TRANSITION_TYPES:
            return False
        if not node.transition:
            return False
        if node.node_type == NodeType.SHOW_SPRITE and not node.sprite_var:
            return False
        return True

    def flush():
        if current:
            units.append(list(current))
            current.clear()

    for node in nodes:
        if is_groupable(node) and current and current[-1].transition == node.transition:
            current.append(node)
        elif is_groupable(node):
            flush()
            current.append(node)
        else:
            flush()
            units.append([node])
    flush()
    return units


def generate_full_script(project: Project, rm=None, custom_templates: Optional[CustomNodeTemplateStore] = None) -> str:
    lines = [
        f"{COMMENT_PREFIX} Сценарий: {project.title}",
        f"{COMMENT_PREFIX} Сгенерировано RenPy Visual Editor",
        "",
    ]
    if project.characters:
        lines.append(f"{COMMENT_PREFIX} ===== Персонажи =====")
        for ch in project.characters:
            lines.append(ch.to_renpy())
        lines.append("")

    lines.append(f"label {project.label_name}:")
    lines.append("")
    for scene in project.scenes:
        lines.append(f"{INDENT}{COMMENT_PREFIX} --- {scene.name} ---")
        active_sprites: Dict[str, str] = {}
        for unit in _group_with_runs(scene.nodes):
            if len(unit) > 1:
                for node in unit:
                    lines.extend(_render_node_no_transition(node, INDENT))
                lines.append(f"{INDENT}with {unit[0].transition}")
                for node in unit:
                    _update_active_sprites(active_sprites, node, rm=rm)
            else:
                node = unit[0]
                lines.extend(generate_node(node, indent=1, active_sprites=active_sprites, rm=rm,
                                            custom_templates=custom_templates))
                _update_active_sprites(active_sprites, node, rm=rm)
        lines.append("")
    lines.append(f"{INDENT}return")
    lines.append("")
    return "\n".join(lines)


def generate_defines_only(project: Project) -> str:
    lines = ["# ===== Персонажи ====="]
    for ch in project.characters:
        lines.append(ch.to_renpy())
    lines.append("")
    return "\n".join(lines)
