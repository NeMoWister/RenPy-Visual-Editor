"""
Менеджер Undo/Redo для проекта.

Работает на снапшотах всего проекта (через project_to_dict/project_from_dict).
Каждый шаг снабжён текстовой меткой (что за действие) — используется
панелью истории (ui/history_panel_dialog.py), чтобы можно было увидеть
список последних действий и отменить сразу до конкретного места, а не
жать Ctrl+Z много раз подряд.

Использование:
    undo_manager.push(snapshot_dict, "Добавлена реплика")
    ...
    label, snap = undo_manager.undo(current_snapshot_dict)   # или None
    label, snap = undo_manager.redo(current_snapshot_dict)   # или None
"""
from typing import Optional, List, Tuple

Entry = Tuple[str, dict]                      


class UndoManager:
    def __init__(self, max_depth: int = 100):
        self.max_depth = max_depth
        self._undo_stack: List[Entry] = []
        self._redo_stack: List[Entry] = []

    def push(self, snapshot: dict, label: str = "Изменение"):
        """Сохраняет снапшот состояния ДО мутации. Вызывать перед изменением
        модели. Любой push сбрасывает redo-стек (стандартное поведение
        undo/redo — новое действие "затирает" будущее)."""
        self._undo_stack.append((label, snapshot))
        if len(self._undo_stack) > self.max_depth:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def undo(self, current_snapshot: dict) -> Optional[Entry]:
        if not self._undo_stack:
            return None
        label, snap = self._undo_stack.pop()
        self._redo_stack.append((label, current_snapshot))
        return label, snap

    def redo(self, current_snapshot: dict) -> Optional[Entry]:
        if not self._redo_stack:
            return None
        label, snap = self._redo_stack.pop()
        self._undo_stack.append((label, current_snapshot))
        return label, snap

    def undo_to_depth(self, current_snapshot: dict, depth: int) -> Optional[dict]:
        """Отменяет сразу `depth` последних действий (depth=1 — как обычный
        undo, depth=3 — как три Ctrl+Z подряд). Возвращает итоговый снапшот
        или None, если стек короче depth."""
        if depth < 1 or depth > len(self._undo_stack):
            return None
        snap = current_snapshot
        for _ in range(depth):
            result = self.undo(snap)
            if result is None:
                return None
            _, snap = result
        return snap

    def history_labels(self) -> List[str]:
        """Метки ещё отменяемых действий, от самого старого к самому
        недавнему (индекс i соответствует "отменить (i+1) раз")."""
        return [label for label, _ in self._undo_stack]

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
