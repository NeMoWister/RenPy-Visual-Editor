"""
Версионирование проекта через настоящий Git (локальный репозиторий +
пуш/пул на GitHub). Обёртка над системным `git` CLI через subprocess —
без сторонних Python-зависимостей.

Репозиторий инициализируется в папке, где лежит сохранённый файл проекта
(.repj) — так под версионированием оказывается весь проект целиком
(ресурсы, .repj и т.п.), а не только один файл.

GitHub-токен используется ТОЛЬКО в момент push/pull (подставляется в URL
для одного вызова) и не сохраняется в конфиг git-репозитория — только (по
желанию пользователя) в локальных настройках редактора в открытом виде
(см. GitCredentialsStore), т.к. система не имеет доступа к keyring/OS-хранилищу
паролей на всех платформах.
"""
import os
import re
import shutil
import subprocess
import sys
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
    """На Windows Git for Windows пишет свой путь установки в реестр —
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
    PATH может быть "заморожен" на момент запуска explorer.exe/логина —
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


def init_repo(repo_dir: str) -> Tuple[bool, str]:
    ok, out = _run(["init"], repo_dir)
    if ok:
        _run(["config", "user.email", "editor@local"], repo_dir)
        _run(["config", "user.name", "RenPy Visual Editor"], repo_dir)
        gitignore_path = os.path.join(repo_dir, ".gitignore")
        if not os.path.isfile(gitignore_path):
            try:
                with open(gitignore_path, "w", encoding="utf-8") as f:
                    f.write("autosave/\n__pycache__/\n*.pyc\n")
            except OSError:
                pass
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


def commit_all(repo_dir: str, message: str) -> Tuple[bool, str]:
    ok, out = _run(["add", "-A"], repo_dir)
    if not ok:
        return False, out
    return _run(["commit", "-m", message], repo_dir)


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
    новый коммит «Откат к ...». История НЕ переписывается — это позволяет
    в любой момент откатить сам откат."""
    ok, out = _run(["checkout", commit_hash, "--", "."], repo_dir)
    if not ok:
        return False, out
    if not has_changes(repo_dir):
        return True, "Уже в этом состоянии — новых изменений нет."
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
    https://TOKEN@github.com/user/repo.git — не сохраняется на диск."""
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
