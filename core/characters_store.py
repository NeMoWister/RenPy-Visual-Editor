                       
"""
Глобальный список персонажей, который сохраняется между сессиями
независимо от текущего открытого проекта - по тому же принципу, что и
переопределения имён ресурсов в resource_manager.py.

Хранится в секции "characters" общего файла editor_config.json (см.
core/unified_config.py) - в базовой папке приложения (рядом с .exe или
main.py, см. core/paths.py).

Это сделано как глобальный пресет: при старте новый проект сразу
подхватывает персонажей, заведённых ранее, не нужно создавать их заново
каждый раз. Открытие существующего .repj-проекта всё равно использует
персонажей, сохранённых внутри него - глобальный список только подсказка
для новых/пустых проектов.
"""
from dataclasses import asdict
from typing import List

from core.models import Character
from core.unified_config import load_section, save_section


def load_global_characters(base_dir: str) -> List[Character]:
    data = load_section(base_dir, "characters")
    try:
        return [Character(**c) for c in data.get("characters", [])]
    except Exception:
        return []


def save_global_characters(base_dir: str, characters: List[Character]):
    save_section(base_dir, "characters", {"characters": [asdict(ch) for ch in characters]})
