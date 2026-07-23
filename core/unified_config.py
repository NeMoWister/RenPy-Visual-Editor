                       
"""
Единый файл конфигурации приложения — editor_config.json в базовой папке
(рядом с .exe или main.py). Раньше настройки окна/автообновлений,
персонажи, теги и переопределения имён ресурсов лежали в 4 разных
файлах (app_settings.json, characters_config.json, tags_config.json,
resources_config.json) — теперь всё в одном, разделённое на секции:

{
  "app_settings": {...},
  "characters": {...},
  "tags": {...},
  "resources": {...}
}

Каждый модуль (core/app_settings.py, core/characters_store.py,
core/tags_store.py, core/resource_manager.py) читает/пишет только свою
секцию через load_section/save_section — остальные секции при этом не
затрагиваются.

Если объединённого файла ещё нет, но остались старые отдельные файлы
(до обновления) — они автоматически подхватываются один раз и сразу
сохраняются в новый общий файл (миграция происходит прозрачно, без
участия пользователя).
"""
import json
import os
import threading

CONFIG_FILENAME = "editor_config.json"

                                                                         
                                                                       
                                                      
_LEGACY_FILES = {
    "app_settings.json": "app_settings",
    "characters_config.json": "characters",
    "tags_config.json": "tags",
    "resources_config.json": "resources",
}

_lock = threading.Lock()


def _config_path(base_dir: str) -> str:
    return os.path.join(base_dir, CONFIG_FILENAME)


def _migrate_legacy(base_dir: str) -> dict:
    merged = {}
    found = False
    for filename, section in _LEGACY_FILES.items():
        legacy_path = os.path.join(base_dir, filename)
        if os.path.isfile(legacy_path):
            try:
                with open(legacy_path, 'r', encoding='utf-8') as f:
                    merged[section] = json.load(f)
                found = True
            except Exception:
                pass
    if found:
        save_all(base_dir, merged)
    return merged


def load_all(base_dir: str) -> dict:
    path = _config_path(base_dir)
    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return _migrate_legacy(base_dir)


def save_all(base_dir: str, data: dict):
    path = _config_path(base_dir)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass                                                     


def load_section(base_dir: str, section: str) -> dict:
    return load_all(base_dir).get(section, {}) or {}


def save_section(base_dir: str, section: str, value):
    with _lock:
        data = load_all(base_dir)
        data[section] = value
        save_all(base_dir, data)
