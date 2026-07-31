"""
Проверка орфографии/технических проблем по ВСЕМ репликам проекта разом (а не
только в одном открытом поле) - с переходом к конкретной ноде по клику,
на тех же "хлебных крошках" (scene_id + branch_path), что и в
core.resource_usage_scanner ("где используется"), включая ноды внутри веток
меню (доработка #1).
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import re

from core.models import Project, NodeType
from core.spellcheck import check_text, SpellIssue

BranchPath = List[Tuple[str, int]]


@dataclass
class LineIssues:
    scene_id: str
    node_id: str
    char_label: str
    text_preview: str
    breadcrumb: str
    issues: List[SpellIssue] = field(default_factory=list)
    branch_path: BranchPath = field(default_factory=list)


def _char_label(project: Project, node) -> str:
    if node.node_type == NodeType.NARRATION or not node.character_var:
        return "(рассказчик)"
    ch = project.get_character_by_var(node.character_var)
    return ch.name if ch else node.character_var


def _count_lines(project: Project) -> int:
    total = 0

    def walk(nodes):
        nonlocal total
        for node in nodes:
            if node.node_type in (NodeType.DIALOGUE, NodeType.NARRATION) and node.text:
                total += 1
            elif node.node_type == NodeType.MENU:
                for _t, _j, _uc, _rb, choice_nodes in node.normalized_menu_choices():
                    if choice_nodes:
                        walk(choice_nodes)

    for scene in project.scenes:
        walk(scene.nodes)
    return total


def _auto_whitelist(project: Project) -> set:
    """Имена персонажей проекта - почти гарантированно словами, которых нет
    в общем словаре (собственные имена), и раньше они просто засоряли
    список ложными срабатываниями на каждой реплике. Добавляем их (и
    отдельные слова из многословных имён) в белый список автоматически."""
    words = set()
    for ch in project.characters:
        for part in re.findall(r"[A-Za-zА-Яа-яЁё]+", ch.name or ""):
            if len(part) >= 2:
                words.add(part.lower())
    return words


def scan_project_spelling(project: Project, on_progress=None, should_cancel=None,
                           extra_whitelist: Optional[set] = None) -> List[LineIssues]:
    """on_progress(done, total) - необязательный колбэк для прогресс-бара (на
    больших проектах словарная проверка орфографии может занимать заметное
    время). should_cancel() - необязательный колбэк, возвращающий True, если
    пользователь отменил проверку (тогда возвращаем то, что успели собрать).
    extra_whitelist - дополнительные слова (в любом регистре), которые
    пользователь явно пометил как «не опечатка» (core.spellcheck_whitelist_store),
    поверх автоматического белого списка из имён персонажей проекта."""
    whitelist = _auto_whitelist(project)
    if extra_whitelist:
        whitelist |= {w.lower() for w in extra_whitelist}
    results: List[LineIssues] = []
    total = _count_lines(project) if on_progress else 0
    done = 0
    cancelled = False

    def walk(nodes, scene_id: str, breadcrumb: str, branch_path: BranchPath):
        nonlocal done, cancelled
        for node in nodes:
            if cancelled:
                return
            if should_cancel is not None and should_cancel():
                cancelled = True
                return
            if node.node_type in (NodeType.DIALOGUE, NodeType.NARRATION) and node.text:
                issues = check_text(node.text, whitelist=whitelist)
                if issues:
                    results.append(LineIssues(
                        scene_id=scene_id, node_id=node.node_id,
                        char_label=_char_label(project, node),
                        text_preview=node.text[:80],
                        breadcrumb=breadcrumb, issues=issues,
                        branch_path=list(branch_path),
                    ))
                done += 1
                if on_progress is not None:
                    on_progress(done, total)
            elif node.node_type == NodeType.MENU:
                for ci, (text, jump, use_call, raw_body, choice_nodes) in enumerate(node.normalized_menu_choices()):
                    if choice_nodes:
                        label = (text or "(без текста)")[:24]
                        walk(choice_nodes, scene_id, f'{breadcrumb} › «{label}»',
                             branch_path + [(node.node_id, ci)])
                        if cancelled:
                            return

    for scene in project.scenes:
        walk(scene.nodes, scene.scene_id, scene.name, [])
        if cancelled:
            break

    return results
