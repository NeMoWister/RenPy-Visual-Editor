"""
"Коммит по сценам" - частичный commit: пользователь выбирает, какие именно
изменённые сцены попадают в снепшот, а какие остаются "на потом".

Технически: .repj - один JSON-файл со списком сцен. Чтобы закоммитить
только часть изменений, мы временно подменяем на диске содержимое
НЕвыбранных сцен версией из HEAD (или убираем их вовсе, если они новые),
коммитим этот "частичный" файл, а затем ГАРАНТИРОВАННО возвращаем на диск
полную текущую версию - так что в самом редакторе и на диске ничего не
теряется, а в истории Git снепшот получается по-настоящему выборочным.

Работает поверх .repj как обычного JSON-словаря (без Project/SceneNode
моделей и без PyQt) - логику можно проверить в изоляции, без запуска GUI.
"""
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from core import git_manager as git

STATUS_ADDED = "added"
STATUS_REMOVED = "removed"
STATUS_MODIFIED = "modified"


@dataclass
class SceneDiffEntry:
    scene_id: str
    name: str
    status: str


def read_json_file(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def read_head_json(repo_dir: str, relpath: str) -> Optional[dict]:
    """Содержимое файла проекта на момент HEAD (последнего коммита), либо
    None - если файла ещё не было в истории (первый коммит) или он не JSON."""
    ok, out = git._run(["show", f"HEAD:{relpath}"], repo_dir)
    if not ok:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def diff_scenes(old_data: Optional[dict], new_data: dict) -> List[SceneDiffEntry]:
    """Какие сцены отличаются между HEAD (old_data) и текущим файлом на
    диске (new_data) - по scene_id, сравнение содержимого целиком."""
    old_scenes = {s["scene_id"]: s for s in (old_data or {}).get("scenes", []) if "scene_id" in s}
    new_scenes = {s["scene_id"]: s for s in new_data.get("scenes", []) if "scene_id" in s}
    entries: List[SceneDiffEntry] = []
    for sid, s in new_scenes.items():
        if sid not in old_scenes:
            entries.append(SceneDiffEntry(sid, s.get("name", sid), STATUS_ADDED))
        elif json.dumps(s, sort_keys=True, ensure_ascii=False) != \
                json.dumps(old_scenes[sid], sort_keys=True, ensure_ascii=False):
            entries.append(SceneDiffEntry(sid, s.get("name", sid), STATUS_MODIFIED))
    for sid, s in old_scenes.items():
        if sid not in new_scenes:
            entries.append(SceneDiffEntry(sid, s.get("name", sid), STATUS_REMOVED))
    return entries


def build_partial_project(old_data: Optional[dict], new_data: dict, selected_scene_ids: Set[str]) -> dict:
    """Версия словаря проекта для частичного коммита: выбранные сцены - из
    new_data (текущее состояние), остальные изменившиеся/новые/удалённые -
    откатываются к old_data (или исключаются, если их не было в old_data -
    т.е. ещё не добавляем в этот коммит новую сцену, которую не выбрали)."""
    old_scenes = {s["scene_id"]: s for s in (old_data or {}).get("scenes", []) if "scene_id" in s}
    new_scenes_list = new_data.get("scenes", [])
    new_ids = {s["scene_id"] for s in new_scenes_list if "scene_id" in s}

    result_scenes = []
    for s in new_scenes_list:
        sid = s.get("scene_id")
        if sid in selected_scene_ids:
                                                        
            result_scenes.append(s)
        elif sid in old_scenes:
                                                                 
            result_scenes.append(old_scenes[sid])
                                                                                     
                                                                             
    for sid, s in old_scenes.items():
        if sid not in new_ids and sid not in selected_scene_ids:
            result_scenes.append(s)

    partial = dict(new_data)
    partial["scenes"] = result_scenes
    return partial


def commit_selected_scenes(repo_dir: str, project_abs_path: str, relpath: str,
                            selected_scene_ids: Set[str], message: str, on_progress=None) -> Tuple[bool, str]:
    """Коммитит только выбранные сцены. Полное текущее состояние на диске
    восстанавливается в любом случае (успех/неуспех коммита) - потери
    несохранённого/несвязанного с коммитом содержимого не происходит."""
    current_data = read_json_file(project_abs_path)
    if current_data is None:
        return False, "Не удалось прочитать файл проекта"
    old_data = read_head_json(repo_dir, relpath)

    partial = build_partial_project(old_data, current_data, selected_scene_ids)

    try:
        with open(project_abs_path, "w", encoding="utf-8") as f:
            json.dump(partial, f, ensure_ascii=False, indent=2)
    except OSError as e:
        return False, str(e)

    ok, out = git.commit_all_with_progress(repo_dir, message, on_progress=on_progress)

    try:
        with open(project_abs_path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        return False, f"{out}\n\nВНИМАНИЕ: не удалось восстановить полный файл проекта на диске: {e}"

    return ok, out
