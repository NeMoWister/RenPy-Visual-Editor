"""
Панель версионирования проекта через Git — снепшоты (коммиты), история,
откат к сохранённой точке, пуш/пул на GitHub.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QTextEdit, QLineEdit, QMessageBox, QTabWidget, QWidget,
    QSplitter, QFileDialog
)
from PyQt6.QtCore import Qt
import os

from core import git_manager as git
from core.git_credentials_store import GitCredentials


class GitPanelDialog(QDialog):
    def __init__(self, repo_dir: str, base_dir: str, parent=None):
        super().__init__(parent)
        self.repo_dir = repo_dir
        self.base_dir = base_dir
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
                "автоматически — часто это из-за того, что exe запущен из проводника со "
                "«старым» PATH — укажите путь к git.exe вручную ниже."
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

        remote_tab = QWidget()
        tabs.addTab(remote_tab, "☁ GitHub")
        self._setup_remote_tab(remote_tab)

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
        self.commit_msg_edit.setPlaceholderText("Описание снепшота, напр. «Глава 2 — конец»")
        commit_row.addWidget(self.commit_msg_edit, 1)
        btn_commit = QPushButton("💾 Сделать снепшот")
        btn_commit.setObjectName("btn_primary")
        btn_commit.clicked.connect(self._on_commit)
        commit_row.addWidget(btn_commit)
        top_l.addLayout(commit_row)

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

    def _on_init(self):
        ok, out = git.init_repo(self.repo_dir)
        if not ok:
            QMessageBox.critical(self, "Ошибка", out)
        self._refresh_all()

    def _on_commit(self):
        msg = self.commit_msg_edit.text().strip() or "Снепшот проекта"
        ok, out = git.commit_all(self.repo_dir, msg)
        if not ok:
            QMessageBox.warning(self, "Не удалось создать снепшот", out or "Нет изменений для снепшота")
        else:
            self.commit_msg_edit.clear()
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
            f"Это создаст новый снепшот с восстановленным содержимым — история "
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
            "виде в настройках редактора на этом компьютере — не используйте токен "
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

        self._refresh_remote_status()
