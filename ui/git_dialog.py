"""
Панель версионирования проекта через Git - снепшоты (коммиты), история,
откат к сохранённой точке, пуш/пул на GitHub.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QTextEdit, QLineEdit, QMessageBox, QTabWidget, QWidget,
    QSplitter, QFileDialog, QCheckBox, QGroupBox, QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os

from core import git_manager as git
from core.git_credentials_store import GitCredentials
from ui.git_graph_widget import GitGraphWidget, wrap_in_scroll_area
from ui.git_scene_commit_dialog import GitScenePartialCommitDialog


class _GitOpWorker(QThread):
    """Выполняет одну потенциально долгую git-операцию в фоне - на большом
    проекте / медленном HDD 'git add -A' первого коммита может идти
    заметно дольше пары секунд, и без этого UI просто "зависал" на глазах
    у пользователя без какой-либо обратной связи."""
    done = pyqtSignal(bool, str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn

    def run(self):
        try:
            ok, out = self.fn()
        except Exception as e:                                    
            ok, out = False, f"Неожиданная ошибка: {e}"
        self.done.emit(ok, out)


class _GitCommitProgressWorker(QThread):
    """Как _GitOpWorker, но конкретно для коммита - с честным (хоть и
    приблизительным) процентом через git.commit_all_with_progress, а не
    просто крутящимся индикатором. on_progress безопасно дёргается из
    фонового потока: сигнал Qt сам маршалит вызов в GUI-поток."""
    done = pyqtSignal(bool, str)
    progress = pyqtSignal(int, int)

    def __init__(self, repo_dir: str, message: str, parent=None):
        super().__init__(parent)
        self.repo_dir = repo_dir
        self.message = message

    def run(self):
        try:
            ok, out = git.commit_all_with_progress(
                self.repo_dir, self.message,
                on_progress=lambda done, total: self.progress.emit(done, total),
            )
        except Exception as e:
            ok, out = False, f"Неожиданная ошибка: {e}"
        self.done.emit(ok, out)


class GitPanelDialog(QDialog):
    def _run_with_progress(self, fn, busy_text: str) -> "tuple[bool, str]":
        """Гоняет fn() (обычно лямбда вокруг git.* команды) в фоновом
        потоке, показывая прогресс-бар (без точного процента - git не даёт
        удобного машиночитаемого прогресса для add/commit/push), чтобы
        интерфейс не выглядел зависшим на больших операциях."""
        progress = QProgressDialog(busy_text, None, 0, 0, self)
        progress.setWindowTitle("Git")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(300)
        progress.setCancelButton(None)                                                   

        result = {}
        worker = _GitOpWorker(fn, self)

        def on_done(ok, out):
            result["ok"] = ok
            result["out"] = out
            progress.close()

        worker.done.connect(on_done)
        worker.start()
        progress.exec()
        worker.wait()
        return result.get("ok", False), result.get("out", "")

    def _run_commit_with_progress(self, message: str) -> "tuple[bool, str]":
        """Как _run_with_progress, но с настоящим (приблизительным) процентом
        для коммита - git add -A --verbose печатает файлы по мере обработки,
        это и считаем прогрессом относительно числа изменённых файлов."""
        progress = QProgressDialog("Подготовка...", None, 0, 0, self)
        progress.setWindowTitle("Git - коммит")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(300)
        progress.setCancelButton(None)

        result = {}
        worker = _GitCommitProgressWorker(self.repo_dir, message, self)

        def on_progress(done, total):
            if total:
                progress.setMaximum(total)
                progress.setValue(done)
                progress.setLabelText(f"Добавление файлов в коммит... {done}/{total}")
            else:
                progress.setLabelText("Коммит...")

        def on_done(ok, out):
            result["ok"] = ok
            result["out"] = out
            progress.close()

        worker.progress.connect(on_progress)
        worker.done.connect(on_done)
        worker.start()
        progress.exec()
        worker.wait()
        return result.get("ok", False), result.get("out", "")

    def __init__(self, repo_dir: str, base_dir: str, parent=None, project_file: str = ""):
        super().__init__(parent)
        self.repo_dir = repo_dir
        self.base_dir = base_dir
        self.project_file = project_file                                                
        self.creds = GitCredentials.load(base_dir)
        if self.creds.git_exe_path:
            git.set_manual_git_path(self.creds.git_exe_path)
        self.setWindowTitle("Версионирование проекта (Git)")
        self.setMinimumSize(860, 620)
        self._setup_ui()
        self._refresh_all()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.repo_lbl = QLabel(f"Репозиторий: {self.repo_dir}")
        self.repo_lbl.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(self.repo_lbl)

        self._git_ok = git.is_git_available()
        if not self._git_ok:
            warn = QLabel(
                "⚠ Программа 'git' не найдена автоматически (ни в PATH, ни в стандартных "
                "папках установки, ни в реестре). Если Git установлен, но не находится "
                "автоматически - часто это из-за того, что exe запущен из проводника со "
                "«старым» PATH - укажите путь к git.exe вручную ниже."
            )
            warn.setWordWrap(True)
            warn.setStyleSheet("color:#ffb84d; background:#332a1a; padding:8px; border-radius:4px;")
            layout.addWidget(warn)

            path_row = QHBoxLayout()
            self.git_path_edit = QLineEdit(self.creds.git_exe_path)
            self.git_path_edit.setPlaceholderText(r"напр. C:\Program Files\Git\cmd\git.exe")
            path_row.addWidget(self.git_path_edit, 1)
            btn_browse = QPushButton("Обзор...")
            btn_browse.clicked.connect(self._browse_git_path)
            path_row.addWidget(btn_browse)
            btn_apply = QPushButton("Применить и проверить")
            btn_apply.setObjectName("btn_primary")
            btn_apply.clicked.connect(self._apply_git_path)
            path_row.addWidget(btn_apply)
            layout.addLayout(path_row)

        tabs = QTabWidget()
        layout.addWidget(tabs, 1)

        commit_tab = QWidget()
        tabs.addTab(commit_tab, "📝 Снепшоты")
        self._setup_commit_tab(commit_tab)

        graph_tab = QWidget()
        tabs.addTab(graph_tab, "🌳 Граф")
        self._setup_graph_tab(graph_tab)

        tags_tab = QWidget()
        tabs.addTab(tags_tab, "🏷 Теги")
        self._setup_tags_tab(tags_tab)

        remote_tab = QWidget()
        tabs.addTab(remote_tab, "☁ GitHub")
        self._setup_remote_tab(remote_tab)

        lfs_tab = QWidget()
        tabs.addTab(lfs_tab, "📦 LFS")
        self._setup_lfs_tab(lfs_tab)

        tabs.setEnabled(self._git_ok)

        bottom = QHBoxLayout()
        bottom.addStretch()
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        bottom.addWidget(btn_close)
        layout.addLayout(bottom)

                                                                             

    def _setup_commit_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)

        self.init_row = QHBoxLayout()
        self.init_lbl = QLabel()
        self.init_lbl.setWordWrap(True)
        self.init_row.addWidget(self.init_lbl, 1)
        self.btn_init = QPushButton("Инициализировать репозиторий здесь")
        self.btn_init.clicked.connect(self._on_init)
        self.init_row.addWidget(self.btn_init)
        self.btn_gitignore = QPushButton("📄 Обновить .gitignore шаблон")
        self.btn_gitignore.setToolTip(
            "Дописывает рекомендованные исключения (кэш, автосохранение, "
            "__pycache__ и т.п.) в .gitignore. Существующий файл не "
            "перезаписывается целиком - спросит подтверждение."
        )
        self.btn_gitignore.clicked.connect(self._on_update_gitignore)
        self.init_row.addWidget(self.btn_gitignore)
        layout.addLayout(self.init_row)

        split = QSplitter(Qt.Orientation.Vertical)

        top = QWidget()
        top_l = QVBoxLayout(top)
        top_l.addWidget(QLabel("Несохранённые изменения в рабочей папке:"))
        self.status_list = QListWidget()
        self.status_list.setMaximumHeight(120)
        top_l.addWidget(self.status_list)

        commit_row = QHBoxLayout()
        self.commit_msg_edit = QLineEdit()
        self.commit_msg_edit.setPlaceholderText("Описание снепшота, напр. «Глава 2 - конец»")
        commit_row.addWidget(self.commit_msg_edit, 1)
        btn_commit = QPushButton("💾 Сделать снепшот")
        btn_commit.setObjectName("btn_primary")
        btn_commit.clicked.connect(self._on_commit)
        commit_row.addWidget(btn_commit)
        top_l.addLayout(commit_row)

        btn_partial_row = QHBoxLayout()
        btn_partial_row.addStretch()
        btn_partial = QPushButton("📦 Commit по сценам...")
        btn_partial.setToolTip(
            "Выбрать, какие именно изменённые сцены попадут в этот снепшот, "
            "а какие останутся несохранёнными для отдельного коммита позже."
        )
        btn_partial.clicked.connect(self._on_partial_commit)
        btn_partial_row.addWidget(btn_partial)
        top_l.addLayout(btn_partial_row)

        bottom = QWidget()
        bottom_l = QVBoxLayout(bottom)
        bottom_l.addWidget(QLabel("История снепшотов:"))
        self.log_list = QListWidget()
        bottom_l.addWidget(self.log_list, 1)

        log_btn_row = QHBoxLayout()
        btn_diff = QPushButton("👁 Показать дифф этого снепшота")
        btn_diff.clicked.connect(self._on_show_diff)
        log_btn_row.addWidget(btn_diff)
        btn_restore = QPushButton("⏪ Восстановить эту версию")
        btn_restore.clicked.connect(self._on_restore)
        log_btn_row.addWidget(btn_restore)
        bottom_l.addLayout(log_btn_row)

        split.addWidget(top)
        split.addWidget(bottom)
        split.setSizes([220, 320])
        layout.addWidget(split, 1)

    def _setup_graph_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel(
            "История по всем веткам (не только текущей) - точки на дорожках "
            "показывают ветвления/слияния, бейджи - имена веток и HEAD."
        ))
        self.graph_widget = GitGraphWidget()
        self.graph_widget.commit_selected.connect(self._on_graph_commit_selected)
        layout.addWidget(wrap_in_scroll_area(self.graph_widget), 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_diff = QPushButton("👁 Показать дифф выбранного коммита")
        btn_diff.clicked.connect(self._on_graph_show_diff)
        btn_row.addWidget(btn_diff)
        layout.addLayout(btn_row)

    def _on_graph_commit_selected(self, commit_hash: str):
        self._graph_selected_hash = commit_hash

    def _on_graph_show_diff(self):
        commit_hash = getattr(self, "_graph_selected_hash", None)
        if not commit_hash:
            QMessageBox.information(self, "Ничего не выбрано", "Кликните на коммит в графе.")
            return
        diff_text = git.diff_commit(self.repo_dir, commit_hash)
        dlg = QDialog(self)
        dlg.setWindowTitle("Дифф коммита")
        dlg.resize(760, 560)
        l = QVBoxLayout(dlg)
        view = QTextEdit()
        view.setReadOnly(True)
        view.setStyleSheet("font-family: Consolas, monospace; font-size:11px; background:#1a1a21; color:#ccc;")
        view.setPlainText(diff_text)
        l.addWidget(view)
        dlg.exec()

    def _setup_tags_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel(
            "Теги - маркировка версий сценария (v1.0, v1.1, «демо для издателя» и т.п.), "
            "привязана к конкретному коммиту."
        ))
        self.tags_list = QListWidget()
        layout.addWidget(self.tags_list, 1)

        form = QHBoxLayout()
        self.tag_name_edit = QLineEdit()
        self.tag_name_edit.setPlaceholderText("напр. v1.0")
        form.addWidget(self.tag_name_edit)
        self.tag_msg_edit = QLineEdit()
        self.tag_msg_edit.setPlaceholderText("Сообщение релиза (необязательно)")
        form.addWidget(self.tag_msg_edit, 1)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_create = QPushButton("🏷 Создать тег на HEAD")
        btn_create.setObjectName("btn_primary")
        btn_create.clicked.connect(self._on_create_tag)
        btn_row.addWidget(btn_create)
        btn_delete = QPushButton("🗑 Удалить выбранный")
        btn_delete.clicked.connect(self._on_delete_tag)
        btn_row.addWidget(btn_delete)
        btn_push_one = QPushButton("⬆ Отправить выбранный")
        btn_push_one.clicked.connect(self._on_push_tag)
        btn_row.addWidget(btn_push_one)
        btn_push_all = QPushButton("⬆ Отправить все теги")
        btn_push_all.clicked.connect(self._on_push_all_tags)
        btn_row.addWidget(btn_push_all)
        layout.addLayout(btn_row)

    def _selected_tag(self) -> str:
        item = self.tags_list.currentItem()
        return item.data(1000) if item else ""

    def _on_create_tag(self):
        name = self.tag_name_edit.text().strip()
        if not name:
            QMessageBox.information(self, "Укажите имя", "Введите имя тега, например v1.0")
            return
        ok, out = git.create_tag(self.repo_dir, name, self.tag_msg_edit.text().strip())
        if not ok:
            QMessageBox.warning(self, "Не удалось создать тег", out)
        else:
            self.tag_name_edit.clear()
            self.tag_msg_edit.clear()
        self._refresh_all()

    def _on_delete_tag(self):
        name = self._selected_tag()
        if not name:
            return
        confirm = QMessageBox.question(self, "Удалить тег?", f"Удалить тег «{name}»?")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        ok, out = git.delete_tag(self.repo_dir, name)
        if not ok:
            QMessageBox.warning(self, "Ошибка", out)
        self._refresh_all()

    def _on_push_tag(self):
        name = self._selected_tag()
        if not name:
            QMessageBox.information(self, "Ничего не выбрано", "Выберите тег в списке.")
            return
        ok, out = git.push_tag(self.repo_dir, name, token=self.creds.token or None)
        if not ok:
            QMessageBox.warning(self, "Push тега не удался", out)
        else:
            QMessageBox.information(self, "Готово", out or "Тег отправлен.")

    def _on_push_all_tags(self):
        ok, out = git.push_all_tags(self.repo_dir, token=self.creds.token or None)
        if not ok:
            QMessageBox.warning(self, "Push тегов не удался", out)
        else:
            QMessageBox.information(self, "Готово", out or "Теги отправлены.")

    def _setup_lfs_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)
        self.lfs_status_lbl = QLabel()
        self.lfs_status_lbl.setWordWrap(True)
        layout.addWidget(self.lfs_status_lbl)

        info = QLabel(
            "Git LFS хранит большие бинарные файлы (спрайты, аудио, видео) отдельно "
            "от истории текстовых изменений - обычный git-репозиторий с ними быстро "
            "раздувается, LFS этого не допускает. Отметьте, какие типы файлов "
            "проекта нужно вести через LFS."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(info)

        patterns_box = QGroupBox("Типы файлов")
        pl = QVBoxLayout(patterns_box)
        self.lfs_checks = {}
        for pattern in git.LFS_RECOMMENDED_PATTERNS:
            cb = QCheckBox(pattern)
            self.lfs_checks[pattern] = cb
            pl.addWidget(cb)
        layout.addWidget(patterns_box)

        btn_row = QHBoxLayout()
        btn_apply = QPushButton("📦 Применить (git lfs track)")
        btn_apply.setObjectName("btn_primary")
        btn_apply.clicked.connect(self._on_lfs_apply)
        btn_row.addWidget(btn_apply)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addWidget(QLabel("Статус LFS:"))
        self.lfs_status_view = QTextEdit()
        self.lfs_status_view.setReadOnly(True)
        self.lfs_status_view.setStyleSheet(
            "font-family: Consolas, monospace; font-size:11px; background:#1a1a21; color:#ccc;")
        layout.addWidget(self.lfs_status_view, 1)

    def _on_lfs_apply(self):
        selected = [p for p, cb in self.lfs_checks.items() if cb.isChecked()]
        if not selected:
            QMessageBox.information(self, "Ничего не выбрано", "Отметьте хотя бы один тип файлов.")
            return
        ok, out = git.lfs_track(self.repo_dir, selected)
        if not ok:
            QMessageBox.warning(self, "Не удалось", out)
        else:
            QMessageBox.information(
                self, "Готово",
                f"{out}\n\nНе забудьте закоммитить .gitattributes (обычный снепшот подхватит его)."
            )
        self._refresh_lfs()

    def _refresh_lfs(self):
        available = git.is_lfs_available()
        if not available:
            self.lfs_status_lbl.setText(
                "⚠ Git LFS не найден в системе. Установите расширение: https://git-lfs.com"
            )
            self.lfs_status_lbl.setStyleSheet("color:#ffb84d;")
        else:
            self.lfs_status_lbl.setText("✓ Git LFS установлен.")
            self.lfs_status_lbl.setStyleSheet("color:#6fd68f;")
        tracked = set(git.lfs_tracked_patterns(self.repo_dir)) if git.is_repo(self.repo_dir) else set()
        for pattern, cb in self.lfs_checks.items():
            cb.blockSignals(True)
            cb.setChecked(pattern in tracked)
            cb.blockSignals(False)
        if git.is_repo(self.repo_dir):
            self.lfs_status_view.setPlainText(git.lfs_status(self.repo_dir) if available else "")

    def _browse_git_path(self):
        filt = "git.exe (git.exe);;Все файлы (*)" if os.name == "nt" else "Все файлы (*)"
        path, _ = QFileDialog.getOpenFileName(self, "Укажите путь к git.exe", "", filt)
        if path:
            self.git_path_edit.setText(path)

    def _apply_git_path(self):
        path = self.git_path_edit.text().strip()
        git.set_manual_git_path(path)
        if git.is_git_available():
            self.creds.git_exe_path = path
            self.creds.save(self.base_dir)
            QMessageBox.information(self, "Готово", "Git найден и подключён.")
            self.close()
            new_dlg = GitPanelDialog(self.repo_dir, self.base_dir, self.parent())
            new_dlg.exec()
        else:
            QMessageBox.warning(self, "Не удалось", f"По этому пути git не запускается:\n{path}")

    def _on_update_gitignore(self):
        ok, added = git.merge_recommended_gitignore(self.repo_dir)
        if not ok:
            QMessageBox.critical(self, "Ошибка", "Не удалось записать .gitignore")
        elif added == 0:
            QMessageBox.information(self, "Готово", "В .gitignore уже есть все рекомендованные исключения.")
        else:
            QMessageBox.information(self, "Готово", f"Добавлено строк в .gitignore: {added}")
        self._refresh_all()

    def _on_init(self):
        ok, out = git.init_repo(self.repo_dir)
        if not ok:
            QMessageBox.critical(self, "Ошибка", out)
        self._refresh_all()

    def _on_commit(self):
        msg = self.commit_msg_edit.text().strip() or "Снепшот проекта"
        ok, out = self._run_commit_with_progress(msg)
        if not ok:
            QMessageBox.warning(self, "Не удалось создать снепшот", out or "Нет изменений для снепшота")
        else:
            self.commit_msg_edit.clear()
        self._refresh_all()

    def _on_partial_commit(self):
        if not self.project_file:
            QMessageBox.information(
                self, "Недоступно",
                "Не удалось определить файл проекта для частичного коммита."
            )
            return
        abs_path = os.path.join(self.repo_dir, self.project_file)
        if not os.path.isfile(abs_path):
            QMessageBox.warning(self, "Файл не найден", f"Не найден файл проекта: {abs_path}")
            return
        dlg = GitScenePartialCommitDialog(self.repo_dir, abs_path, self.project_file, self)
        dlg.exec()
        self._refresh_all()

    def _selected_commit(self):
        row = self.log_list.currentRow()
        if row < 0:
            return None
        item = self.log_list.item(row)
        return item.data(1000) if item else None

    def _on_show_diff(self):
        commit_hash = self._selected_commit()
        if not commit_hash:
            return
        diff_text = git.diff_commit(self.repo_dir, commit_hash)
        dlg = QDialog(self)
        dlg.setWindowTitle("Дифф снепшота")
        dlg.resize(760, 560)
        l = QVBoxLayout(dlg)
        view = QTextEdit()
        view.setReadOnly(True)
        view.setStyleSheet("font-family: Consolas, monospace; font-size:11px; background:#1a1a21; color:#ccc;")
        view.setPlainText(diff_text)
        l.addWidget(view)
        dlg.exec()

    def _on_restore(self):
        commit_hash = self._selected_commit()
        if not commit_hash:
            return
        item = self.log_list.item(self.log_list.currentRow())
        confirm = QMessageBox.question(
            self, "Восстановить версию?",
            f"Восстановить файлы проекта к состоянию «{item.text()}»?\n\n"
            f"Текущие несохранённые изменения в рабочей папке будут ЗАМЕНЕНЫ. "
            f"Это создаст новый снепшот с восстановленным содержимым - история "
            f"не удаляется, при желании можно откатить и сам откат.\n\n"
            f"После восстановления перезагрузите проект в редакторе (Файл → Открыть).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        ok, out = git.restore_to_commit(self.repo_dir, commit_hash)
        if not ok:
            QMessageBox.critical(self, "Ошибка", out)
        else:
            QMessageBox.information(
                self, "Готово",
                "Файлы восстановлены. Откройте проект заново (Файл → Открыть), "
                "чтобы редактор подхватил восстановленную версию .repj."
            )
        self._refresh_all()

                                                                         

    def _setup_remote_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)

        info = QLabel(
            "Токен доступа GitHub (Personal Access Token, права 'repo') нужен для "
            "push/pull в приватный репозиторий. Он сохраняется ЛОКАЛЬНО в открытом "
            "виде в настройках редактора на этом компьютере - не используйте токен "
            "с лишними правами."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(info)

        layout.addWidget(QLabel("URL репозитория (https://github.com/user/repo.git):"))
        self.remote_url_edit = QLineEdit(self.creds.github_url)
        layout.addWidget(self.remote_url_edit)

        layout.addWidget(QLabel("Personal Access Token:"))
        self.token_edit = QLineEdit(self.creds.token)
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.token_edit)

        btn_save_remote = QPushButton("Сохранить и привязать удалённый репозиторий")
        btn_save_remote.clicked.connect(self._on_save_remote)
        layout.addWidget(btn_save_remote)

        self.remote_status_lbl = QLabel()
        self.remote_status_lbl.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(self.remote_status_lbl)

        btn_row = QHBoxLayout()
        btn_push = QPushButton("⬆ Отправить (push)")
        btn_push.setObjectName("btn_primary")
        btn_push.clicked.connect(self._on_push)
        btn_row.addWidget(btn_push)
        btn_pull = QPushButton("⬇ Получить (pull)")
        btn_pull.clicked.connect(self._on_pull)
        btn_row.addWidget(btn_pull)
        layout.addLayout(btn_row)

        self.remote_log = QTextEdit()
        self.remote_log.setReadOnly(True)
        self.remote_log.setStyleSheet("font-family: Consolas, monospace; font-size:11px; background:#1a1a21; color:#ccc;")
        layout.addWidget(self.remote_log, 1)

    def _on_save_remote(self):
        self.creds.github_url = self.remote_url_edit.text().strip()
        self.creds.token = self.token_edit.text().strip()
        self.creds.save(self.base_dir)
        if self.creds.github_url and git.is_repo(self.repo_dir):
            ok, out = git.set_remote_url(self.repo_dir, self.creds.github_url)
            self.remote_log.append(out or ("OK" if ok else "Ошибка"))
        self._refresh_remote_status()

    def _on_push(self):
        ok, out = git.push(self.repo_dir, token=self.creds.token or None)
        self.remote_log.append(("[push] " + out) if out else "[push] OK")
        if not ok:
            QMessageBox.warning(self, "Push не удался", out)

    def _on_pull(self):
        ok, out = git.pull(self.repo_dir, token=self.creds.token or None)
        self.remote_log.append(("[pull] " + out) if out else "[pull] OK")
        if not ok:
            QMessageBox.warning(self, "Pull не удался", out)
        else:
            QMessageBox.information(self, "Готово", "Изменения получены. Переоткройте проект (Файл → Открыть).")
        self._refresh_all()

    def _refresh_remote_status(self):
        url = git.get_remote_url(self.repo_dir) if self._git_ok and git.is_repo(self.repo_dir) else None
        self.remote_status_lbl.setText(f"Текущий удалённый репозиторий: {url or '(не настроен)'}")

                                                                           

    def _refresh_all(self):
        if not self._git_ok:
            return
        repo_exists = git.is_repo(self.repo_dir)
        self.btn_init.setEnabled(not repo_exists)
        self.init_lbl.setText(
            "Git-репозиторий уже инициализирован в этой папке." if repo_exists
            else "В папке проекта ещё нет Git-репозитория."
        )

        self.status_list.clear()
        self.log_list.clear()
        if not repo_exists:
            self._refresh_remote_status()
            return

        for st in git.get_status(self.repo_dir):
            self.status_list.addItem(QListWidgetItem(f"[{st.code}] {st.path}"))

        for c in git.get_log(self.repo_dir):
            item = QListWidgetItem(f"{c.date}  {c.short_hash}  {c.message}")
            item.setData(1000, c.commit_hash)
            self.log_list.addItem(item)

        self.graph_widget.set_commits(git.get_log_graph(self.repo_dir))

        self.tags_list.clear()
        for t in git.list_tags(self.repo_dir):
            item = QListWidgetItem(f"{t.name}   {t.date}   {t.commit_hash[:8]}   {t.message}")
            item.setData(1000, t.name)
            self.tags_list.addItem(item)

        self._refresh_lfs()

        self._refresh_remote_status()
