import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QRadioButton, QButtonGroup, QSpinBox, QCheckBox, QMessageBox, QGroupBox,
    QTextEdit,
)

from core.project_export import export_project, ExportOptions, DefinesOptions, generate_defines
from core.i18n import tr


class ExportDefinesDialog(QDialog):
    """Экспорт defines.rpy отдельно от сценария - персонажи / кастомные
    переходы / defines ресурсов, каждый блок можно выключить чекбоксом.
    Заменяет старые кнопки 'Экспорт defines' и 'Экспорт defines ресурсов',
    у которых не было вообще никаких опций (генерировали фиксированный
    набор блоков без возможности что-то исключить)."""

    def __init__(self, project, rm=None, parent=None, nvl_style="character"):
        super().__init__(parent)
        self.project = project
        self.rm = rm
        self.nvl_style = nvl_style
        self.setWindowTitle(tr("export_defines.title"))
        self.setMinimumSize(480, 420)
        self._setup_ui()
        self._update_preview()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        box = QGroupBox(tr("export_defines.what_box"))
        bl = QVBoxLayout(box)
        self.cb_characters = QCheckBox(tr("export_project.cb_characters"))
        self.cb_transitions = QCheckBox(tr("export_project.cb_transitions"))
        self.cb_resources = QCheckBox(tr("export_project.cb_resources"))
        self.cb_used_only = QCheckBox(tr("export_defines.cb_used_only"))
        self.cb_used_only.setChecked(False)
        for cb in (self.cb_characters, self.cb_transitions, self.cb_resources):
            cb.setChecked(True)
            cb.toggled.connect(self._update_preview)
        self.cb_used_only.toggled.connect(self._update_preview)
        self.cb_resources.toggled.connect(self.cb_used_only.setEnabled)
        bl.addWidget(self.cb_characters)
        bl.addWidget(self.cb_transitions)
        bl.addWidget(self.cb_resources)
        bl.addWidget(self.cb_used_only)
        layout.addWidget(box)

        layout.addWidget(QLabel(tr("export_defines.preview_label")))
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        font = self.preview.font()
        font.setFamily("Consolas")
        self.preview.setFont(font)
        layout.addWidget(self.preview, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton(tr("split_export.cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        self.btn_save = QPushButton(tr("export_defines.save_as"))
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.clicked.connect(self._do_export)
        btn_row.addWidget(self.btn_save)
        layout.addLayout(btn_row)

    def _build_options(self) -> DefinesOptions:
        return DefinesOptions(
            characters=self.cb_characters.isChecked(),
            custom_transitions=self.cb_transitions.isChecked(),
            resource_defines=self.cb_resources.isChecked(),
            resource_defines_used_only=self.cb_used_only.isChecked(),
        )

    def _update_preview(self):
        try:
            code = generate_defines(self.project, self.rm, self._build_options(), nvl_style=self.nvl_style)
        except Exception as e:
            code = f"# {e}"
        self.preview.setPlainText(code)

    def _do_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("export_defines.save_title"), "defines.rpy",
            f"Ren'Py Script (*.rpy);;{tr('mw.all_files2')} (*)"
        )
        if not path:
            return
        try:
            code = generate_defines(self.project, self.rm, self._build_options(), nvl_style=self.nvl_style)
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            QMessageBox.critical(self, tr("mw.error_title"), str(e))
            return
        self.accept()


class ExportProjectDialog(QDialog):
    """Экспорт всего проекта: сценарий (.rpy, одним файлом или разбитым по
    сценам/label'ам/N-в-файл - см. core.split_export) + отдельный defines.rpy
    (персонажи / кастомные переходы / defines ресурсов - каждый блок можно
    выключить чекбоксом) + ТОЛЬКО используемые файлы ресурсов, разложенные
    точно по тем путям, что фигурируют в сгенерированном коде (см.
    core.project_export)."""

    def __init__(self, project, rm=None, custom_templates=None, parent=None, nvl_style="character"):
        super().__init__(parent)
        self.project = project
        self.rm = rm
        self.custom_templates = custom_templates
        self.nvl_style = nvl_style
        self.target_dir = ""
        self.setWindowTitle(tr("export_project.title"))
        self.setMinimumSize(560, 560)
        self._setup_ui()
        self._update_summary()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        dir_row = QHBoxLayout()
        self.dir_lbl = QLabel(tr("export_project.dir_not_selected"))
        self.dir_lbl.setObjectName("hint_text")
        dir_row.addWidget(self.dir_lbl, 1)
        btn_dir = QPushButton(tr("export_project.pick_dir"))
        btn_dir.clicked.connect(self._pick_dir)
        dir_row.addWidget(btn_dir)
        layout.addLayout(dir_row)

        split_box = QGroupBox(tr("export_project.split_box"))
        sl = QVBoxLayout(split_box)
        self.rule_group = QButtonGroup(self)
        self.rb_single = QRadioButton(tr("export_project.rb_single"))
        self.rb_label = QRadioButton(tr("split_export.rb_label"))
        self.rb_scene = QRadioButton(tr("split_export.rb_scene"))
        self.rb_count = QRadioButton(tr("split_export.rb_count"))
        self.rb_single.setChecked(True)
        self.rule_group.addButton(self.rb_single, 0)
        self.rule_group.addButton(self.rb_label, 1)
        self.rule_group.addButton(self.rb_scene, 2)
        self.rule_group.addButton(self.rb_count, 3)
        for rb in (self.rb_single, self.rb_label, self.rb_scene, self.rb_count):
            rb.toggled.connect(self._update_summary)
        sl.addWidget(self.rb_single)
        sl.addWidget(self.rb_label)
        sl.addWidget(self.rb_scene)
        count_row = QHBoxLayout()
        count_row.addWidget(self.rb_count)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 200)
        self.count_spin.setValue(5)
        self.count_spin.valueChanged.connect(self._update_summary)
        count_row.addWidget(self.count_spin)
        count_row.addWidget(QLabel(tr("split_export.scenes_per_file")))
        count_row.addStretch()
        sl.addLayout(count_row)
        layout.addWidget(split_box)

        defines_box = QGroupBox(tr("export_project.defines_box"))
        dl = QVBoxLayout(defines_box)
        self.cb_characters = QCheckBox(tr("export_project.cb_characters"))
        self.cb_transitions = QCheckBox(tr("export_project.cb_transitions"))
        self.cb_resources = QCheckBox(tr("export_project.cb_resources"))
        for cb in (self.cb_characters, self.cb_transitions, self.cb_resources):
            cb.setChecked(True)
            cb.toggled.connect(self._update_summary)
        dl.addWidget(self.cb_characters)
        dl.addWidget(self.cb_transitions)
        dl.addWidget(self.cb_resources)
        layout.addWidget(defines_box)

        layout.addWidget(QLabel(tr("export_project.summary_label")))
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        layout.addWidget(self.summary, 1)

        note = QLabel(tr("export_project.note"))
        note.setWordWrap(True)
        note.setObjectName("hint_text")
        layout.addWidget(note)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton(tr("split_export.cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        self.btn_export = QPushButton(tr("split_export.export"))
        self.btn_export.setObjectName("btn_primary")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._do_export)
        btn_row.addWidget(self.btn_export)
        layout.addLayout(btn_row)

    def _current_rule(self) -> str:
        if self.rb_label.isChecked():
            return "label"
        if self.rb_scene.isChecked():
            return "scene"
        if self.rb_count.isChecked():
            return "count"
        return "single"

    def _build_options(self) -> ExportOptions:
        return ExportOptions(
            dest_dir=self.target_dir,
            split_rule=self._current_rule(),
            count_per_file=self.count_spin.value(),
            defines=DefinesOptions(
                characters=self.cb_characters.isChecked(),
                custom_transitions=self.cb_transitions.isChecked(),
                resource_defines=self.cb_resources.isChecked(),
            ),
            nvl_style=self.nvl_style,
        )

    def _update_summary(self):
        from core.project_export import collect_export_assets
        rule = self._current_rule()
        if rule == "single":
            script_desc = tr("export_project.summary_single_script")
        else:
            try:
                from core.split_export import split_project
                chunks = split_project(
                    self.project, rule, rm=self.rm, custom_templates=self.custom_templates,
                    count_per_file=self.count_spin.value(), defines_in_first_file=False,
                    nvl_style=self.nvl_style,
                )
                n = len([c for c in chunks if c.scene_names])
            except Exception:
                n = 0
            script_desc = tr("export_project.summary_split_scripts", count=n)

        assets, unresolved = collect_export_assets(self.project, self.rm) if self.rm else ([], [])
        missing = [a for a in assets if a.missing]
        ok = [a for a in assets if not a.missing]

        lines = [script_desc, tr("export_project.summary_defines")]
        lines.append(tr("export_project.summary_assets", count=len(ok)))
        if missing:
            lines.append("")
            lines.append(tr("export_project.summary_missing", count=len(missing)))
            for a in missing[:30]:
                lines.append(f"  - {a.dest_rel_path}  ({a.var_name})")
        if unresolved:
            lines.append("")
            lines.append(tr("export_project.summary_unresolved", count=len(unresolved)))
            for v in unresolved[:30]:
                lines.append(f"  - {v}")
        self.summary.setPlainText("\n".join(lines))
        self.btn_export.setEnabled(bool(self.target_dir))

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, tr("export_project.pick_dir_title"))
        if d:
            self.target_dir = d
            self.dir_lbl.setText(d)
            self.dir_lbl.setObjectName("hint_text_bright")
            self.btn_export.setEnabled(True)

    def _do_export(self):
        try:
            result = export_project(
                self.project, self.rm, self._build_options(),
                custom_templates=self.custom_templates,
            )
        except Exception as e:
            QMessageBox.critical(self, tr("export_project.error_title"), str(e))
            return

        msg = tr("export_project.done_summary",
                 path=self.target_dir, scripts=len(result.script_paths),
                 assets=len(result.copied_assets))
        if result.missing_assets or result.unresolved_vars:
            msg += "\n\n" + tr("export_project.done_warning",
                                missing=len(result.missing_assets),
                                unresolved=len(result.unresolved_vars))
            QMessageBox.warning(self, tr("export_project.title"), msg)
        else:
            QMessageBox.information(self, tr("split_export.done_title"), msg)
        self.accept()
