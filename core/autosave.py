"""
Автосохранение проекта и восстановление после аварийного завершения.

Каждые N секунд (см. AppSettings.autosave_interval_sec), если в проекте
есть несохранённые изменения, текущее состояние целиком пишется в
единственный слот восстановления `<base_dir>/autosave/current.repj` (+
метаданные - исходный путь файла проекта и время). При штатном закрытии
редактора (после того как пользователь сохранил или явно отказался от
сохранения) слот очищается. Если при следующем запуске слот всё ещё
существует - значит, прошлый раз редактор закрылся аварийно, и можно
предложить восстановить.
"""
import json
import os
import time
from dataclasses import dataclass
from typing import Optional

from core.project_manager import project_to_dict

AUTOSAVE_SUBDIR = "autosave"
AUTOSAVE_FILE = "current.repj"
META_FILE = "current.meta.json"


def _autosave_dir(base_dir: str) -> str:
    d = os.path.join(base_dir, AUTOSAVE_SUBDIR)
    os.makedirs(d, exist_ok=True)
    return d


def write_autosave(base_dir: str, project, original_path: Optional[str]) -> bool:
    d = _autosave_dir(base_dir)
    data_path = os.path.join(d, AUTOSAVE_FILE)
    meta_path = os.path.join(d, META_FILE)
    try:
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(project_to_dict(project), f, ensure_ascii=False)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "original_path": original_path,
                "title": project.title,
                "timestamp": time.time(),
            }, f, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Ошибка автосохранения: {e}")
        return False


@dataclass
class AutosaveInfo:
    data: dict
    original_path: Optional[str]
    title: str
    timestamp: float


def read_autosave(base_dir: str) -> Optional[AutosaveInfo]:
    d = _autosave_dir(base_dir)
    data_path = os.path.join(d, AUTOSAVE_FILE)
    meta_path = os.path.join(d, META_FILE)
    if not os.path.isfile(data_path):
        return None
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        meta = {}
        if os.path.isfile(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        return AutosaveInfo(
            data=data,
            original_path=meta.get("original_path"),
            title=meta.get("title", data.get("title", "Проект")),
            timestamp=meta.get("timestamp", 0.0),
        )
    except Exception as e:
        print(f"Ошибка чтения автосохранения: {e}")
        return None


def has_autosave(base_dir: str) -> bool:
    return os.path.isfile(os.path.join(_autosave_dir(base_dir), AUTOSAVE_FILE))


def clear_autosave(base_dir: str):
    d = _autosave_dir(base_dir)
    for name in (AUTOSAVE_FILE, META_FILE):
        p = os.path.join(d, name)
        if os.path.isfile(p):
            try:
                os.remove(p)
            except OSError:
                pass
