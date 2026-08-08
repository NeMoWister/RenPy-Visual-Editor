                       
"""
Именованные кастомные переходы - когда пользователь настраивает переход
через диалог (в т.ч. ImageDissolve по своей маске) и сохраняет его под
именем, он попадает сюда и становится доступен для повторного выбора в
любом другом месте проекта (готовый список переходов), а также объявляется
как `define <имя> = <выражение>` в общем блоке дефайнов (см.
code_generator.generate_defines_only), чтобы сгенерированный .rpy был
компактным (переход пишется по имени, а не полным выражением в каждом with).

Хранится в секции "custom_transitions" общего editor_config.json (см.
core/unified_config.py) - формат: {"имя": "выражение Ren'Py", ...}.
"""
from typing import Dict, Optional

from core.unified_config import load_section, save_section

SECTION = "custom_transitions"


def load_custom_transitions(base_dir: str) -> Dict[str, str]:
    """name -> Ren'Py-выражение перехода (см. core/transitions.py:spec_to_expr)."""
    if not base_dir:
        return {}
    data = load_section(base_dir, SECTION)
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def save_custom_transition(base_dir: str, name: str, expr: str):
    if not base_dir or not name:
        return
    data = load_custom_transitions(base_dir)
    data[name] = expr
    save_section(base_dir, SECTION, data)


def delete_custom_transition(base_dir: str, name: str):
    if not base_dir or not name:
        return
    data = load_custom_transitions(base_dir)
    if name in data:
        del data[name]
        save_section(base_dir, SECTION, data)


def suggest_name(base_dir: str, hint: str) -> str:
    """Предлагает свободное имя на основе подсказки (например, имени файла
    маски или вида перехода) - добавляет _2, _3... при коллизии с уже
    занятыми именами (как встроенными, так и ранее сохранёнными кастомными)."""
    from core.transitions import BUILTIN_TRANSITIONS
    import re
    base = re.sub(r'[^a-zA-Z0-9_]+', '_', hint).strip('_').lower() or "custom_transition"
    existing = set(BUILTIN_TRANSITIONS.keys()) | set(load_custom_transitions(base_dir).keys())
    if base not in existing:
        return base
    i = 2
    while f"{base}_{i}" in existing:
        i += 1
    return f"{base}_{i}"


def resolve(text: str, base_dir: Optional[str]) -> str:
    """Если text - это имя сохранённого кастомного перехода, возвращает его
    выражение; иначе возвращает text как есть (голое встроенное имя или уже
    полное выражение - transitions.parse_transition разберётся сам)."""
    if not text or not base_dir:
        return text
    custom = load_custom_transitions(base_dir)
    return custom.get(text, text)
