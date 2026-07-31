"""
Версионирование проекта через настоящий Git (локальный репозиторий +
пуш/пул на GitHub). Обёртка над системным `git` CLI через subprocess -
без сторонних Python-зависимостей.

Репозиторий инициализируется в папке, где лежит сохранённый файл проекта
(.repj) - так под версионированием оказывается весь проект целиком
(ресурсы, .repj и т.п.), а не только один файл.

GitHub-токен используется ТОЛЬКО в момент push/pull (подставляется в URL
для одного вызова) и не сохраняется в конфиг git-репозитория - только (по
желанию пользователя) в локальных настройках редактора в открытом виде
(см. GitCredentialsStore), т.к. система не имеет доступа к keyring/OS-хранилищу
паролей на всех платформах.
"""
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.unified_config import load_section, save_section

                                                              
_resolved_git_path: Optional[str] = None
_manual_override_path: Optional[str] = None                                        

_WINDOWS_COMMON_PATHS = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
    r"C:\Program Files (x86)\Git\bin\git.exe",
]


def _creation_flags() -> int:
                                                                   
                                                             
    if os.name == "nt":
        return subprocess.CREATE_NO_WINDOW
    return 0


def _candidates_from_registry() -> List[str]:
    """На Windows Git for Windows пишет свой путь установки в реестр -
    это надёжный способ найти git.exe, даже если PATH, унаследованный
    процессом (особенно у скомпилированного .exe, запущенного двойным
    кликом из проводника), устарел и не содержит папку Git."""
    if os.name != "nt":
        return []
    paths = []
    try:
        import winreg
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for subkey in (r"SOFTWARE\GitForWindows", r"SOFTWARE\WOW6432Node\GitForWindows"):
                try:
                    with winreg.OpenKey(hive, subkey) as key:
                        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                        if install_path:
                            paths.append(os.path.join(install_path, "cmd", "git.exe"))
                            paths.append(os.path.join(install_path, "bin", "git.exe"))
                except OSError:
                    continue
    except ImportError:
        pass
    return paths


def set_manual_git_path(path: Optional[str]):
    """Ручное указание пути к git.exe (см. диалог версионирования), на
    случай если автопоиск не сработал ни одним способом."""
    global _manual_override_path, _resolved_git_path
    _manual_override_path = path or None
    _resolved_git_path = None                                   


def resolve_git_executable(force: bool = False) -> Optional[str]:
    """Находит рабочий git.exe/git несколькими способами по очереди, НЕ
    полагаясь только на переменную PATH, унаследованную процессом (у
    скомпилированного .exe, запущенного двойным кликом из проводника,
    PATH может быть "заморожен" на момент запуска explorer.exe/логина -
    даже если Git установлен и виден из свежего терминала)."""
    global _resolved_git_path
    if _resolved_git_path and not force:
        return _resolved_git_path

    candidates: List[str] = []
    if _manual_override_path:
        candidates.append(_manual_override_path)

    which_result = shutil.which("git")
    if which_result:
        candidates.append(which_result)

    candidates.append("git")                                                 

    if os.name == "nt":
        candidates.extend(_candidates_from_registry())
        candidates.extend(_WINDOWS_COMMON_PATHS)
        for env_var in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            base = os.environ.get(env_var)
            if base:
                candidates.append(os.path.join(base, "Git", "cmd", "git.exe"))
                candidates.append(os.path.join(base, "Programs", "Git", "cmd", "git.exe"))

    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            r = subprocess.run([candidate, "--version"], capture_output=True, timeout=5,
                                creationflags=_creation_flags())
            if r.returncode == 0:
                _resolved_git_path = candidate
                return candidate
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            continue

    return None


def is_git_available() -> bool:
    return resolve_git_executable() is not None


def _run(args: List[str], cwd: str, timeout: int = 30) -> Tuple[bool, str]:
    git_exe = resolve_git_executable()
    if not git_exe:
        return False, (
            "Программа 'git' не найдена ни в PATH, ни в стандартных папках установки. "
            "Установите Git (https://git-scm.com/downloads) или укажите путь к git.exe "
            "вручную в настройках версионирования."
        )
    try:
        r = subprocess.run([git_exe] + args, cwd=cwd, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=timeout,
                            creationflags=_creation_flags())
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode == 0, out.strip()
    except FileNotFoundError:
        return False, "Команда 'git' не найдена. Установите Git: https://git-scm.com/downloads"
    except subprocess.TimeoutExpired:
        return False, "Превышено время ожидания git-команды"
    except Exception as e:
        return False, str(e)


def is_repo(repo_dir: str) -> bool:
    return os.path.isdir(os.path.join(repo_dir, ".git"))


RECOMMENDED_GITIGNORE = """\
# --- RenPy Visual Editor: автосохранение и временные файлы ---
autosave/
*.repj.bak
*.repj.tmp

# --- Кэш превью/миниатюр (если используется) ---
.cache/
.thumbnails/
preview_cache/
*_cache/
*.thumb.png
*.thumb.jpg

# --- Python (на случай кастомных нод-шаблонов/скриптов рядом с проектом) ---
__pycache__/
*.pyc
*.pyo

# --- Мусор ОС ---
.DS_Store
Thumbs.db
desktop.ini

# --- Временные файлы редакторов/IDE ---
*.swp
*.swp~
*~
.idea/
.vscode/
"""


def gitignore_path(repo_dir: str) -> str:
    return os.path.join(repo_dir, ".gitignore")


def write_recommended_gitignore(repo_dir: str, overwrite: bool = False) -> bool:
    """Записывает рекомендованный .gitignore. Если файл уже есть и
    overwrite=False - ничего не делает (не затирает то, что пользователь
    мог настроить вручную), возвращает False."""
    path = gitignore_path(repo_dir)
    if os.path.isfile(path) and not overwrite:
        return False
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(RECOMMENDED_GITIGNORE)
        return True
    except OSError:
        return False


def merge_recommended_gitignore(repo_dir: str) -> Tuple[bool, int]:
    """Дописывает в СУЩЕСТВУЮЩИЙ .gitignore только те строки из шаблона,
    которых там ещё нет (построчное сравнение, без учёта пустых строк и
    комментариев) - не трогает и не дублирует то, что пользователь уже
    настроил сам. Возвращает (успех, сколько строк добавлено)."""
    path = gitignore_path(repo_dir)
    try:
        existing = ""
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = f.read()
        existing_lines = {ln.strip() for ln in existing.splitlines() if ln.strip() and not ln.strip().startswith("#")}
        to_add = []
        for ln in RECOMMENDED_GITIGNORE.splitlines():
            stripped = ln.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped not in existing_lines:
                to_add.append(stripped)
                existing_lines.add(stripped)
        if not to_add:
            return True, 0
        with open(path, "a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("\n# --- добавлено из рекомендованного шаблона RenPy Visual Editor ---\n")
            f.write("\n".join(to_add) + "\n")
        return True, len(to_add)
    except OSError:
        return False, 0


def init_repo(repo_dir: str) -> Tuple[bool, str]:
    ok, out = _run(["init"], repo_dir)
    if ok:
        _run(["config", "user.email", "editor@local"], repo_dir)
        _run(["config", "user.name", "RenPy Visual Editor"], repo_dir)
        write_recommended_gitignore(repo_dir, overwrite=False)
    return ok, out


@dataclass
class GitFileStatus:
    code: str                                   
    path: str


def get_status(repo_dir: str) -> List[GitFileStatus]:
    ok, out = _run(["status", "--porcelain"], repo_dir)
    if not ok or not out:
        return []
    result = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        code = line[:2].strip()
        path = line[3:]
        result.append(GitFileStatus(code=code or "?", path=path))
    return result


def has_changes(repo_dir: str) -> bool:
    return bool(get_status(repo_dir))


def commit_all_with_progress(repo_dir: str, message: str, on_progress=None,
                              timeout: int = 900) -> Tuple[bool, str]:
    """То же самое, что commit_all, но с честным (хоть и приблизительным)
    прогрессом вместо просто "крутящегося" индикатора: git не даёт готового
    процента для add/commit, но `git add -A --verbose` печатает построчно
    add/remove по мере обработки каждого файла - эту потоковую печать и
    считаем как прогресс относительно числа изменённых файлов (git status
    --porcelain, посчитанный заранее). Это приближение (крупные файлы
    занимают непропорционально больше времени, чем мелкие, но всё равно
    честнее, чем индикатор без деления на шаги).

    on_progress(done, total) - total=0 означает "не знаем общее число"
    (тогда вызывающая сторона может просто показать индикатор активности)."""
    git_exe = resolve_git_executable()
    if not git_exe:
        return False, "git не найден. Укажите путь к git.exe в настройках версионирования."

    ok, status_out = _run(["status", "--porcelain", "-uall"], repo_dir, timeout=min(timeout, 120))
    total = len(status_out.splitlines()) if ok and status_out else 0
    if on_progress is not None:
        on_progress(0, total)

    if total == 0:
                                                                       
        return commit_all(repo_dir, message, timeout=timeout)

    try:
        proc = subprocess.Popen(
            [git_exe, "add", "-A", "--verbose"], cwd=repo_dir,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            creationflags=_creation_flags(),
        )
    except OSError as e:
        return False, str(e)

    done = 0
    output_lines: List[str] = []
    start = time.monotonic()
    while True:
        line = proc.stdout.readline() if proc.stdout else ""
        if line:
            output_lines.append(line)
            done += 1
            if on_progress is not None:
                on_progress(min(done, total), total)
            continue
        if proc.poll() is not None:
            break
        if time.monotonic() - start > timeout:
            proc.kill()
            return False, f"Превышен таймаут ({timeout}с) на этапе 'git add' - большой проект/медленный диск?"

    proc.wait()
    if proc.returncode != 0:
        return False, "".join(output_lines) or "git add завершился с ошибкой"

    if on_progress is not None:
        on_progress(total, total)

    return _run(["commit", "-m", message], repo_dir, timeout=timeout)


def commit_all(repo_dir: str, message: str, timeout: int = 900) -> Tuple[bool, str]:
    """timeout по умолчанию - 15 минут: `git add -A` на большом проекте
    (особенно первый коммит, когда ВСЁ ещё не захэшировано) на медленном
    HDD может идти заметно дольше стандартных 30 секунд - раньше это
    приводило к обрыву по таймауту прямо посреди операции."""
    ok, out = _run(["add", "-A"], repo_dir, timeout=timeout)
    if not ok:
        return False, out
    return _run(["commit", "-m", message], repo_dir, timeout=timeout)


@dataclass
class CommitInfo:
    commit_hash: str
    short_hash: str
    author: str
    date: str
    message: str


_LOG_SEP = "\x1f"


def get_log(repo_dir: str, limit: int = 100) -> List[CommitInfo]:
    fmt = f"%H{_LOG_SEP}%h{_LOG_SEP}%an{_LOG_SEP}%ad{_LOG_SEP}%s"
    ok, out = _run(["log", f"-{limit}", f"--pretty=format:{fmt}", "--date=short"], repo_dir)
    if not ok or not out:
        return []
    commits = []
    for line in out.splitlines():
        parts = line.split(_LOG_SEP)
        if len(parts) == 5:
            commits.append(CommitInfo(commit_hash=parts[0], short_hash=parts[1],
                                       author=parts[2], date=parts[3], message=parts[4]))
    return commits


def diff_working_tree(repo_dir: str) -> str:
    ok, out = _run(["diff", "HEAD"], repo_dir)
    return out if ok else f"Ошибка: {out}"


def diff_commit(repo_dir: str, commit_hash: str) -> str:
    ok, out = _run(["show", commit_hash], repo_dir)
    return out if ok else f"Ошибка: {out}"


def restore_to_commit(repo_dir: str, commit_hash: str) -> Tuple[bool, str]:
    """НЕразрушающий откат: копирует состояние файлов на момент commit_hash
    поверх рабочей копии (git checkout <hash> -- .), затем коммитит это как
    новый коммит «Откат к ...». История НЕ переписывается - это позволяет
    в любой момент откатить сам откат."""
    ok, out = _run(["checkout", commit_hash, "--", "."], repo_dir)
    if not ok:
        return False, out
    if not has_changes(repo_dir):
        return True, "Уже в этом состоянии - новых изменений нет."
    short = commit_hash[:8]
    return commit_all(repo_dir, f"Откат к версии {short}")


def get_remote_url(repo_dir: str, remote: str = "origin") -> Optional[str]:
    ok, out = _run(["remote", "get-url", remote], repo_dir)
    return out.strip() if ok and out.strip() else None


def set_remote_url(repo_dir: str, url: str, remote: str = "origin") -> Tuple[bool, str]:
    if get_remote_url(repo_dir, remote):
        return _run(["remote", "set-url", remote, url], repo_dir)
    return _run(["remote", "add", remote, url], repo_dir)


def current_branch(repo_dir: str) -> str:
    ok, out = _run(["rev-parse", "--abbrev-ref", "HEAD"], repo_dir)
    return out.strip() if ok else "main"


def _inject_token(url: str, token: str) -> str:
    """Вставляет токен в HTTPS-URL github для одноразовой аутентификации:
    https://TOKEN@github.com/user/repo.git - не сохраняется на диск."""
    m = re.match(r"^https://(?:[^@]+@)?(.+)$", url)
    if not m or not token:
        return url
    return f"https://{token}@{m.group(1)}"


def push(repo_dir: str, token: Optional[str] = None, remote: str = "origin",
         branch: Optional[str] = None) -> Tuple[bool, str]:
    url = get_remote_url(repo_dir, remote)
    if not url:
        return False, f"Удалённый репозиторий '{remote}' не настроен"
    branch = branch or current_branch(repo_dir)
    push_url = _inject_token(url, token) if token else url
    return _run(["push", push_url, branch], repo_dir, timeout=120)


def pull(repo_dir: str, token: Optional[str] = None, remote: str = "origin",
         branch: Optional[str] = None) -> Tuple[bool, str]:
    url = get_remote_url(repo_dir, remote)
    if not url:
        return False, f"Удалённый репозиторий '{remote}' не настроен"
    branch = branch or current_branch(repo_dir)
    pull_url = _inject_token(url, token) if token else url
    return _run(["pull", pull_url, branch], repo_dir, timeout=120)


def clone(url: str, dest_dir: str, token: Optional[str] = None) -> Tuple[bool, str]:
    clone_url = _inject_token(url, token) if token else url
    parent = os.path.dirname(dest_dir.rstrip("/\\")) or "."
    name = os.path.basename(dest_dir.rstrip("/\\"))
    return _run(["clone", clone_url, name], parent, timeout=120)


                                                              
                                    
                                                              

@dataclass
class TagInfo:
    name: str
    commit_hash: str
    message: str
    date: str
    is_annotated: bool


def list_tags(repo_dir: str) -> List[TagInfo]:
    """Список тегов (версий) с датой и сообщением - работает и для
    аннотированных, и для лёгких (lightweight) тегов."""
    sep = "\x01"
    fmt = sep.join([
        "%(refname:short)", "%(objectname)", "%(*objectname)",
        "%(creatordate:short)", "%(subject)",
    ])
    ok, out = _run(["for-each-ref", "refs/tags", "--sort=-creatordate", f"--format={fmt}"], repo_dir)
    if not ok or not out:
        return []
    result = []
    for line in out.splitlines():
        parts = line.split(sep)
        if len(parts) < 5:
            continue
        name, obj_hash, deref_hash, date, subject = parts[:5]
        commit_hash = deref_hash or obj_hash
        result.append(TagInfo(
            name=name, commit_hash=commit_hash, message=subject,
            date=date, is_annotated=bool(deref_hash),
        ))
    return result


def create_tag(repo_dir: str, name: str, message: str = "", commit_hash: Optional[str] = None) -> Tuple[bool, str]:
    """Аннотированный тег (хранит сообщение и дату) - то, что обычно нужно
    для маркировки версий сценария (v1.0, v1.1 и т.п.)."""
    name = (name or "").strip()
    if not name:
        return False, "Не указано имя тега"
    args = ["tag", "-a", name, "-m", message or name]
    if commit_hash:
        args.append(commit_hash)
    return _run(args, repo_dir)


def delete_tag(repo_dir: str, name: str) -> Tuple[bool, str]:
    return _run(["tag", "-d", name], repo_dir)


def push_tag(repo_dir: str, name: str, token: Optional[str] = None, remote: str = "origin") -> Tuple[bool, str]:
    url = get_remote_url(repo_dir, remote)
    if not url:
        return False, f"Удалённый репозиторий '{remote}' не настроен"
    push_url = _inject_token(url, token) if token else url
    return _run(["push", push_url, name], repo_dir, timeout=60)


def push_all_tags(repo_dir: str, token: Optional[str] = None, remote: str = "origin") -> Tuple[bool, str]:
    url = get_remote_url(repo_dir, remote)
    if not url:
        return False, f"Удалённый репозиторий '{remote}' не настроен"
    push_url = _inject_token(url, token) if token else url
    return _run(["push", push_url, "--tags"], repo_dir, timeout=120)


                                                              
                             
                                                              

def is_lfs_available() -> bool:
    git_exe = resolve_git_executable()
    if not git_exe:
        return False
    try:
        r = subprocess.run([git_exe, "lfs", "version"], capture_output=True, timeout=5,
                            creationflags=_creation_flags())
        return r.returncode == 0
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False


LFS_RECOMMENDED_PATTERNS = [
    "*.png", "*.jpg", "*.jpeg", "*.webp",
    "*.ogg", "*.mp3", "*.wav", "*.opus", "*.flac",
    "*.mp4", "*.webm",
    "*.ttf", "*.otf",
]


def lfs_install(repo_dir: str) -> Tuple[bool, str]:
    return _run(["lfs", "install", "--local"], repo_dir)


def lfs_tracked_patterns(repo_dir: str) -> List[str]:
    path = os.path.join(repo_dir, ".gitattributes")
    if not os.path.isfile(path):
        return []
    patterns = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "filter=lfs" in line:
                    patterns.append(line.split()[0])
    except OSError:
        pass
    return patterns


def lfs_track(repo_dir: str, patterns: List[str]) -> Tuple[bool, str]:
    """Добавляет паттерны файлов под Git LFS (пишет .gitattributes через
    `git lfs track`) - большие бинарные ресурсы (спрайты/аудио) хранятся
    отдельно от истории текстовых изменений, репозиторий не раздувается."""
    if not is_lfs_available():
        return False, (
            "Git LFS не найден. Установите расширение: https://git-lfs.com "
            "(после установки может понадобиться перезапустить редактор)."
        )
    ok_install, out_install = lfs_install(repo_dir)
    if not ok_install:
        return False, out_install
    messages = []
    all_ok = True
    for pattern in patterns:
        ok, out = _run(["lfs", "track", pattern], repo_dir)
        all_ok = all_ok and ok
        if out:
            messages.append(out)
    return all_ok, "\n".join(messages)


def lfs_untrack(repo_dir: str, patterns: List[str]) -> Tuple[bool, str]:
    messages = []
    all_ok = True
    for pattern in patterns:
        ok, out = _run(["lfs", "untrack", pattern], repo_dir)
        all_ok = all_ok and ok
        if out:
            messages.append(out)
    return all_ok, "\n".join(messages)


def lfs_status(repo_dir: str) -> str:
    ok, out = _run(["lfs", "status"], repo_dir)
    return out if ok else f"Ошибка: {out}"


                                                              
                                       
                                                              

@dataclass
class GraphCommit:
    commit_hash: str
    short_hash: str
    parents: List[str]
    author: str
    date: str
    message: str
    refs: List[str]
    lane: int = 0


def _assign_lanes(commits: List["GraphCommit"]):
    """Простое построчное присвоение "дорожек" (lanes) коммитам для отрисовки
    графа веток - коммиты уже должны идти в порядке `git log` (дети раньше
    родителей). Каждая дорожка "ожидает" определённый следующий hash;
    коммит занимает дорожку, которая его ждёт (т.е. дорожку своего ребёнка),
    либо получает новую (кончик ветки). После коммита дорожка начинает
    ждать его первого родителя; дополнительные родители (merge) получают
    свободные дорожки или новые."""
    active: List[Optional[str]] = []
    for c in commits:
        lane = None
        for i, expected in enumerate(active):
            if expected == c.commit_hash:
                lane = i
                break
        if lane is None:
            lane = len(active)
            active.append(None)
        c.lane = lane
        active[lane] = c.parents[0] if c.parents else None
        for p in c.parents[1:]:
            if p in active:
                continue
            free_idx = next((i for i, v in enumerate(active) if v is None), None)
            if free_idx is not None:
                active[free_idx] = p
            else:
                active.append(p)


def get_log_graph(repo_dir: str, limit: int = 300) -> List[GraphCommit]:
    """История по ВСЕМ веткам (не только текущей) с родителями и
    декорациями (имена веток/тегов) - основа для графа коммитов в
    git-диалоге. Дорожки (lane) уже посчитаны, см. _assign_lanes."""
    sep = "\x01"
    fmt = sep.join(["%H", "%h", "%P", "%an", "%ad", "%s", "%D"])
    ok, out = _run(["log", f"-{limit}", "--all", "--date=short", f"--pretty=format:{fmt}"], repo_dir)
    if not ok or not out:
        return []
    commits = []
    for line in out.splitlines():
        parts = line.split(sep)
        if len(parts) < 7:
            continue
        h, sh, parents_str, an, ad, subj, refs_str = parts[:7]
        parents = parents_str.split() if parents_str else []
        refs = [r.strip() for r in refs_str.split(',') if r.strip()] if refs_str else []
        commits.append(GraphCommit(commit_hash=h, short_hash=sh, parents=parents,
                                    author=an, date=ad, message=subj, refs=refs))
    _assign_lanes(commits)
    return commits


def list_branches(repo_dir: str) -> List[str]:
    ok, out = _run(["branch", "--all", "--format=%(refname:short)"], repo_dir)
    if not ok or not out:
        return []
    return [ln.strip() for ln in out.splitlines() if ln.strip()]
