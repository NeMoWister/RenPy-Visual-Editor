                       
"""
Проверка обновлений через GitHub Releases.

Как настроить:
1. Залейте проект в репозиторий на GitHub.
2. Впишите ниже владельца и имя репозитория в GITHUB_OWNER / GITHUB_REPO
   (например, для https://github.com/ivanov/renpy-editor это
   GITHUB_OWNER = "ivanov", GITHUB_REPO = "renpy-editor").
3. Перед каждым релизом поднимайте версию в version.py (APP_VERSION) и
   создавайте на GitHub Release с тегом такой же или более новой версии
   (тег вида "v1.2.0" или "1.2.0" — без разницы, буква "v" игнорируется).
4. Если приложите .exe как Asset релиза — кнопка "Скачать" в окне
   обновления будет вести прямо на файл. Если нет — откроется страница
   релиза, и пользователь скачает файл оттуда сам.

Пока GITHUB_OWNER/GITHUB_REPO не заполнены, проверка тихо ничего не делает
(не мешает работе и не показывает ошибок).
"""
import json
import re
import urllib.request
from typing import Optional, Dict

from version import APP_VERSION

                                                        
GITHUB_OWNER = "NeMoWister"
GITHUB_REPO = "RenPy-Visual-Editor"
                                                          

API_URL_TEMPLATE = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
USER_AGENT = "RenPyVisualScriptEditor-Updater"


def _parse_version(v: str):
    v = (v or "").strip().lstrip("vV")
    parts = re.findall(r"\d+", v)
    return tuple(int(p) for p in parts) if parts else (0,)


def is_newer(remote_version: str, local_version: str = APP_VERSION) -> bool:
    return _parse_version(remote_version) > _parse_version(local_version)


def is_configured() -> bool:
    return bool(GITHUB_OWNER and GITHUB_REPO)


def fetch_latest_release(timeout: float = 5.0) -> Optional[Dict]:
    """Запрашивает последний релиз репозитория на GitHub. Возвращает None
    при любой проблеме (нет сети, репозиторий не настроен, релизов ещё
    нет и т.п.) — проверка обновлений никогда не должна мешать работе
    программы или показывать пользователю ошибки сети."""
    if not is_configured():
        return None

    url = API_URL_TEMPLATE.format(owner=GITHUB_OWNER, repo=GITHUB_REPO)
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    tag = data.get("tag_name") or ""
    if not tag:
        return None

                                                                               
    page_url = data.get("html_url", "")
    download_url = page_url
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.lower().endswith(".exe"):
            download_url = asset.get("browser_download_url", page_url)
            break

    return {
        "version": tag,
        "page_url": page_url,
        "download_url": download_url,
        "notes": (data.get("body") or "").strip(),
        "published_at": data.get("published_at", ""),
    }


def check_for_update(timeout: float = 5.0) -> Optional[Dict]:
    """Возвращает информацию о релизе, если на GitHub есть версия новее
    текущей (APP_VERSION из version.py). Иначе — None."""
    release = fetch_latest_release(timeout=timeout)
    if not release:
        return None
    if is_newer(release["version"], APP_VERSION):
        return release
    return None
