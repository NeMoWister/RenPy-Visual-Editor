"""
Полный экспорт проекта одной кнопкой (см. ui/export_project_dialog.py):

  - script.rpy (или несколько файлов при разбиении по сценам/label'ам/N-в-файл,
    см. core.split_export) - ТОЛЬКО сам сценарий (label'ы, реплики, show/scene
    и т.п.), без единого define/image - это отдельный файл.
  - defines.rpy - все объявления (персонажи, кастомные переходы, image/define
    ресурсов), КАЖДЫЙ блок можно исключить чекбоксом в диалоге экспорта.
  - resources/... ТОЛЬКО реально используемые в проекте файлы ресурсов -
    см. collect_export_assets.

О путях (важно!): Ren'Py резолвит "bg/room.png" в `image x = "bg/room.png"`
относительно СВОЕЙ папки game/, а не относительно инструмента. Внутри
инструмента ресурсы физически лежат в resources/custom/bg/room.png (и
resources/default/... для стандартных), но "custom"/"default" - это
организация только для самого редактора. При экспорте эта часть пути
ОТБРАСЫВАЕТСЯ: файл должен лечь ровно по тому пути, который фигурирует в
сгенерированном коде (тот же game_path/mask_path/layer.rel_path), иначе
экспортированный проект не соберётся в Ren'Py ("Couldn't find file ...").

Почему одного core.resource_usage_scanner недостаточно, чтобы понять, что
использовано (см. collect_export_assets):

  1. Составные спрайты (ConditionSwitch/im.Composite из <source>/sprites/
     sprites.rpy) - у них нет отдельного ResourceEntry (см.
     ResourceManager._scan_composite_sprites), их слои резолвятся отдельно.
  2. Маски ImageDissolve-переходов (with ImageDissolve("...", ...)) - файл
     в resources/custom/transitions/, на который ссылается node.transition
     (напрямую или через core.custom_transitions - именованный кастомный
     переход, сохранённый через диалог перехода). node.transition вообще не
     входит в индекс ресурсов - переходы отдельная сущность.
"""
import os
import shutil
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from core.models import Project, SceneNode, NodeType
from core.resource_usage_scanner import scan_project_usage
from core.custom_transitions import load_custom_transitions
from core.transitions import parse_transition, TransitionKind
from core.code_generator import (
    generate_full_script, CustomNodeTemplateStore, COMMENT_PREFIX, _project_uses_nvl,
)
from core.split_export import split_project, SPLIT_RULES, ExportChunk

_BUILTIN_MASK_SENTINELS = {"__builtin_blinds__", "__builtin_squares__"}

SPRITES_RPY_DEST = "sprites/sprites.rpy"


@dataclass
class ExportAsset:
    """Один файл-ресурс, который нужно скопировать в экспорт."""
    dest_rel_path: str                    # путь ОТНОСИТЕЛЬНО game/ - ровно как в сгенерированном коде
    abs_path: str                         # где реально лежит на диске (источник копирования)
    var_name: str = ""                    # var ресурса или имя перехода, из-за которого он попал в список
    kind: str = "resource"                # resource | transition_mask | composite_def | composite_layer
    missing: bool = False                 # файл не найден на диске (ничего не скопировано)


@dataclass
class DefinesOptions:
    """Что включать в defines.rpy - управляется чекбоксами в диалоге экспорта."""
    characters: bool = True
    custom_transitions: bool = True
    resource_defines: bool = True         # image/define блоки для bg/cg/sprites/sounds/ambience
    resource_defines_used_only: bool = True   # True - только используемые (обязательно при export_project,
                                               # т.к. copy-фаза копирует только их); False - все ресурсы проекта


@dataclass
class ExportOptions:
    dest_dir: str
    split_rule: str = "single"            # "single" | одно из core.split_export.SPLIT_RULES
    count_per_file: int = 5
    defines: DefinesOptions = field(default_factory=DefinesOptions)
    nvl_style: str = "character"
    script_filename: str = "script.rpy"
    defines_filename: str = "defines.rpy"


@dataclass
class ExportResult:
    script_paths: List[str] = field(default_factory=list)
    defines_path: str = ""
    copied_assets: List[ExportAsset] = field(default_factory=list)
    missing_assets: List[ExportAsset] = field(default_factory=list)
    unresolved_vars: List[str] = field(default_factory=list)   # использованный var без найденного файла


# ------------------------------------------------------------------ #
#  Обход всех нод проекта (включая ветки меню на любую глубину) -
#  повторяет логику core.resource_usage_scanner.scan_project_usage,
#  но плоско отдаёт сами ноды, а не индекс "где используется".
# ------------------------------------------------------------------ #

def _iter_all_nodes(project: Project):
    def walk(nodes: List[SceneNode]):
        for node in nodes:
            yield node
            if node.node_type == NodeType.MENU:
                for _text, _jump, _use_call, _raw_body, choice_nodes in node.normalized_menu_choices():
                    if choice_nodes:
                        yield from walk(choice_nodes)

    for scene in project.scenes:
        yield from walk(scene.nodes)


def collect_used_transition_names(project: Project) -> Set[str]:
    """Все непустые значения node.transition, встречающиеся в проекте (в
    т.ч. внутри веток меню). Значение - либо голое имя (встроенное или
    сохранённое кастомное), либо полное Ren'Py-выражение, набранное вручную."""
    names: Set[str] = set()
    for node in _iter_all_nodes(project):
        t = getattr(node, "transition", "")
        if t and t.strip():
            names.add(t.strip())
    return names


# ------------------------------------------------------------------ #
#  Сбор списка файлов-ресурсов
# ------------------------------------------------------------------ #

def collect_export_assets(project: Project, rm) -> Tuple[List[ExportAsset], List[str]]:
    """Возвращает (assets, unresolved_vars).
    assets - все файлы, которые реально нужно скопировать (только source
    "custom" - "default"-ресурсы считаются частью самого Ren'Py проекта и
    экспортом не трогаются, как и в core.resource_manager.generate_define_block).
    dest_rel_path у каждого asset - ровно тот путь, который фигурирует в
    сгенерированном коде (не resources/custom/..., а просто bg/..., cg/...,
    transitions/..., sprites/... - т.е. относительно будущей game/ Ren'Py).
    unresolved_vars - использованные var_name, для которых не нашлось ни
    обычного ResourceEntry, ни составного спрайта (вероятно, ресурс был
    удалён с диска - стоит показать пользователю)."""
    if rm is None:
        return [], []

    assets: Dict[str, ExportAsset] = {}
    unresolved: List[str] = []

    used_vars = scan_project_usage(project).keys()
    for var in sorted(used_vars):
        entry = rm.find_by_var(var)
        if entry is not None:
            if entry.source == "custom":
                assets[entry.game_path] = ExportAsset(
                    dest_rel_path=entry.game_path, abs_path=entry.abs_path,
                    var_name=var, kind="resource",
                    missing=not os.path.isfile(entry.abs_path),
                )
            continue

        cs = rm.find_composite_by_name(var)
        if cs is not None:
            if cs.source == "custom":
                rpy_path = os.path.join(rm.get_source_root("custom"), "sprites", "sprites.rpy")
                assets[SPRITES_RPY_DEST] = ExportAsset(
                    dest_rel_path=SPRITES_RPY_DEST, abs_path=rpy_path,
                    var_name=var, kind="composite_def",
                    missing=not os.path.isfile(rpy_path),
                )
                for layer in cs.layers:
                    dest_rel = layer.rel_path
                    layer_abs = rm.resolve_layer_path(layer.rel_path, source="custom")
                    assets[dest_rel] = ExportAsset(
                        dest_rel_path=dest_rel, abs_path=layer_abs,
                        var_name=var, kind="composite_layer",
                        missing=not os.path.isfile(layer_abs),
                    )
            continue

        unresolved.append(var)

    custom_transitions = load_custom_transitions(getattr(rm, "base_dir", None))
    for name in collect_used_transition_names(project):
        expr = custom_transitions.get(name, name)
        spec = parse_transition(expr)
        if spec is None or spec.kind != TransitionKind.IMAGE_DISSOLVE:
            continue
        mask = spec.mask_path
        if not mask or mask in _BUILTIN_MASK_SENTINELS or os.path.isabs(mask):
            # __builtin_*__ рисуются кодом, без файла; абсолютный путь
            # означает файл вне resources/ (набран вручную) - копировать
            # некуда, оставляем выражение как есть в define.
            continue
        abs_path = os.path.join(rm.get_source_root("custom"), mask)
        assets[mask] = ExportAsset(
            dest_rel_path=mask, abs_path=abs_path,
            var_name=name, kind="transition_mask",
            missing=not os.path.isfile(abs_path),
        )

    return list(assets.values()), unresolved


# ------------------------------------------------------------------ #
#  defines.rpy - только выбранные чекбоксами блоки, и только для РЕАЛЬНО
#  использованных ресурсов (иначе image-объявление сослалось бы на файл,
#  который экспорт сознательно не скопировал, и Ren'Py не соберёт проект)
# ------------------------------------------------------------------ #

def _characters_block(project: Project, nvl_style: str) -> List[str]:
    if not project.characters:
        return []
    lines = [f"{COMMENT_PREFIX} ===== Персонажи ====="]
    for ch in project.characters:
        lines.append(ch.to_renpy())
    if _project_uses_nvl(project) and nvl_style == "character":
        lines.append("")
        lines.append(f"{COMMENT_PREFIX} ===== NVL-варианты персонажей (для NVL_MODE-нод) =====")
        for ch in project.characters:
            lines.append(ch.to_renpy_nvl())
    lines.append("")
    return lines


def _custom_transitions_block(rm) -> List[str]:
    if rm is None:
        return []
    custom = load_custom_transitions(getattr(rm, "base_dir", None))
    if not custom:
        return []
    lines = [f"{COMMENT_PREFIX} ===== Кастомные переходы (заданы через диалог перехода) ====="]
    for name, expr in sorted(custom.items()):
        lines.append(f"define {name} = {expr}")
    lines.append("")
    return lines


def _resource_defines_block(project: Project, rm, used_only: bool = True) -> List[str]:
    """Аналог ResourceManager.generate_define_block(), но с возможностью
    ограничиться только использованными в проекте ресурсами (used_only=True -
    так и должно быть при экспорте всего проекта, иначе объявление
    сослалось бы на файл, который мы не копируем; used_only=False - для
    самостоятельного экспорта defines, когда copy-фазы вообще нет и
    ограничивать нечем/незачем)."""
    if rm is None:
        return []
    used_vars = scan_project_usage(project).keys() if used_only else None
    lines: List[str] = []
    for cat, (label, _exts) in rm.CATEGORIES.items():
        if cat == "music":
            continue
        entries = [e for e in rm.get(cat)
                   if e.source == "custom" and (used_vars is None or e.var_name in used_vars)]
        if not entries:
            continue
        lines.append(f"{COMMENT_PREFIX} {label}")
        for e in entries:
            if cat in ("bg", "cg", "sprites"):
                lines.append(f'image {e.var_name} = "{e.game_path}"')
            else:
                lines.append(f'define {e.var_name} = "{e.game_path}"')
        lines.append("")
    has_composites = bool(rm.composite_sprites) and (
        used_vars is None or any(cs.full_name in used_vars for cs in rm.composite_sprites)
    )
    if has_composites:
        lines.append(f"{COMMENT_PREFIX} Составные спрайты (персонаж/позиция/эмоция) уже объявлены")
        lines.append(f"{COMMENT_PREFIX} в sprites/sprites.rpy - подключите этот файл к проекту Ren'Py.")
        lines.append("")
    return lines


# Совместимость: старое имя, всегда только используемые ресурсы (так и
# нужно во время export_project - см. ниже).
def _used_resource_defines_block(project: Project, rm) -> List[str]:
    return _resource_defines_block(project, rm, used_only=True)


def generate_defines(project: Project, rm, options: DefinesOptions,
                      nvl_style: str = "character") -> str:
    lines: List[str] = []
    if options.characters:
        lines.extend(_characters_block(project, nvl_style))
    if options.custom_transitions:
        lines.extend(_custom_transitions_block(rm))
    if options.resource_defines:
        lines.extend(_resource_defines_block(project, rm, used_only=options.resource_defines_used_only))
    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Собственно экспорт
# ------------------------------------------------------------------ #

def _copy_assets(dest_dir: str, assets: List[ExportAsset]) -> Tuple[List[ExportAsset], List[ExportAsset]]:
    copied: List[ExportAsset] = []
    missing: List[ExportAsset] = []
    for asset in assets:
        if asset.missing:
            missing.append(asset)
            continue
        target = os.path.join(dest_dir, *asset.dest_rel_path.split("/"))
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(asset.abs_path, target)
            copied.append(asset)
        except OSError:
            asset.missing = True
            missing.append(asset)
    return copied, missing


def export_project(project: Project, rm, options: ExportOptions,
                    custom_templates: Optional[CustomNodeTemplateStore] = None) -> ExportResult:
    """Пишет script.rpy (либо несколько файлов, если options.split_rule !=
    "single" - см. core.split_export) с ЧИСТЫМ сценарием без единого define,
    отдельный defines.rpy (только отмеченные чекбоксами блоки), и копирует
    ТОЛЬКО используемые файлы ресурсов - каждый ровно по тому пути, что
    фигурирует в сгенерированном коде (без resources/custom/...)."""
    dest_dir = options.dest_dir
    os.makedirs(dest_dir, exist_ok=True)

    script_paths: List[str] = []
    if options.split_rule == "single":
        code = generate_full_script(
            project, rm=rm, custom_templates=custom_templates,
            nvl_style=options.nvl_style, include_defines=False,
        )
        path = os.path.join(dest_dir, options.script_filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        script_paths.append(path)
    else:
        if options.split_rule not in SPLIT_RULES:
            raise ValueError(f"Неизвестное правило разбиения: {options.split_rule!r}")
        chunks: List[ExportChunk] = split_project(
            project, options.split_rule, rm=rm, custom_templates=custom_templates,
            count_per_file=options.count_per_file, defines_in_first_file=False,
            nvl_style=options.nvl_style,
        )
        # defines_in_first_file=False заводит отдельный синтетический чанк
        # "00_characters.rpy" (scene_names=[]) - он нам не нужен, defines
        # пишем сами одним общим файлом ниже.
        chunks = [c for c in chunks if c.scene_names]
        for chunk in chunks:
            path = os.path.join(dest_dir, chunk.filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(chunk.code)
            script_paths.append(path)

    defines_code = generate_defines(project, rm, options.defines, nvl_style=options.nvl_style)
    defines_path = os.path.join(dest_dir, options.defines_filename)
    with open(defines_path, "w", encoding="utf-8") as f:
        f.write(defines_code)

    assets, unresolved = collect_export_assets(project, rm)
    copied, missing = _copy_assets(dest_dir, assets)

    return ExportResult(
        script_paths=script_paths, defines_path=defines_path,
        copied_assets=copied, missing_assets=missing, unresolved_vars=unresolved,
    )
