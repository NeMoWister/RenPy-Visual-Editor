"""
Диалог «Шаблоны пользовательских нод» - создание/редактирование своих типов
нод (см. core/custom_node_templates.py). У диалога есть встроенная
документация (вкладка «Справка»).
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QTextEdit, QSplitter, QWidget, QMessageBox,
    QTabWidget, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.custom_node_templates import (
    CustomNodeTemplateStore, CustomNodeTemplate, ParamDef,
    PARAM_TYPES, PARAM_TYPE_LABELS, JINJA2_AVAILABLE,
)
from core.i18n import tr

DOC_TEXT = """
<h2>Шаблоны пользовательских нод</h2>

<p>Эта функция позволяет добавить в редактор <b>свой тип ноды</b> для вызовов,
которых нет в стандартном наборе Ren'Py-команд редактора - например, вызов
собственной функции движка вроде смены дня/главы:</p>

<pre>$ new_chapter(3, u"Название сохранения")</pre>

<h3>Как это работает</h3>
<ol>
<li>Здесь вы создаёте <b>шаблон</b>: имя, описание, список параметров
(с типом и значением по умолчанию) и Jinja2-шаблон кода.</li>
<li>В редакторе ноды выбираете тип «🧬 Пользовательская нода...», затем - ваш
шаблон из списка. Появится форма с полями для параметров ЭТОЙ конкретной ноды.</li>
<li>При генерации кода нода рендерится по шаблону со своими значениями
параметров.</li>
</ol>

<p><b>Важно:</b> применение шаблона создаёт ОТДЕЛЬНУЮ новую ноду со своими
собственными значениями параметров. Изменение шаблона позже НЕ переписывает
задним числом уже вставленные ноды - оно влияет только на то, как они будут
сгенерированы в код при следующей генерации (их параметры хранятся отдельно
в каждой ноде).</p>

<h3>Шаблон кода (Jinja2)</h3>
<p>Используйте <code>{{ имя_параметра }}</code> для подстановки значения и
<code>{{ pad }}</code> для текущего отступа (устанавливается автоматически по
уровню вложенности сцены). Пример:</p>

<pre>{{ pad }}$ new_chapter({{ chapter_number }}, u"{{ save_name }}")</pre>

<p>Можно использовать условия и другие конструкции Jinja2, например:</p>
<pre>{{ pad }}$ new_chapter({{ chapter_number }}{% if save_name %}, u"{{ save_name }}"{% endif %})</pre>

<h3>Параметры</h3>
<ul>
<li><b>Имя</b> - как параметр называется внутри шаблона ({{ имя }}). Только
латиница/цифры/подчёркивание, без пробелов.</li>
<li><b>Подпись</b> - как поле подписано в форме редактирования ноды.</li>
<li><b>Тип</b> - Строка / Целое число / Дробное число / Да-нет. Влияет на то,
каким виджетом параметр редактируется и как подставляется в шаблон.</li>
<li><b>По умолчанию</b> - значение для новой ноды этого типа.</li>
</ul>

<h3>Требования</h3>
<p>Для рендеринга шаблонов нужен пакет <code>jinja2</code>
(<code>pip install jinja2</code>). Без него ноды сохраняются и импортируются
нормально, но при генерации кода вместо содержимого подставится
предупреждающий комментарий.</p>
"""


class ParamRow(QWidget):
    def __init__(self, param: ParamDef, on_change, on_remove):
        super().__init__()
        self.on_change = on_change
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.name_edit = QLineEdit(param.name)
        self.name_edit.setPlaceholderText(tr("custom_nodes.name_param_placeholder"))
        self.name_edit.setFixedWidth(140)
        self.name_edit.textChanged.connect(on_change)
        layout.addWidget(self.name_edit)

        self.label_edit = QLineEdit(param.label)
        self.label_edit.setPlaceholderText(tr("custom_nodes.label_in_form_placeholder"))
        self.label_edit.textChanged.connect(on_change)
        layout.addWidget(self.label_edit)

        self.type_combo = QComboBox()
        for pt in PARAM_TYPES:
            self.type_combo.addItem(PARAM_TYPE_LABELS[pt], pt)
        idx = PARAM_TYPES.index(param.param_type) if param.param_type in PARAM_TYPES else 0
        self.type_combo.setCurrentIndex(idx)
        self.type_combo.currentIndexChanged.connect(on_change)
        layout.addWidget(self.type_combo)

        self.default_edit = QLineEdit(str(param.default))
        self.default_edit.setPlaceholderText(tr("custom_nodes.default_value_placeholder"))
        self.default_edit.textChanged.connect(on_change)
        layout.addWidget(self.default_edit)

        btn_remove = QPushButton("X")
        btn_remove.setFixedWidth(60)
        btn_remove.clicked.connect(lambda: on_remove(self))
        layout.addWidget(btn_remove)

    def to_param(self) -> ParamDef:
        pt = self.type_combo.currentData()
        default_raw = self.default_edit.text()
        temp = ParamDef(name=self.name_edit.text().strip(), label=self.label_edit.text().strip(),
                         param_type=pt, default=default_raw)
        temp.default = temp.coerce(default_raw)
        return temp


class CustomNodeTemplatesDialog(QDialog):
    templates_changed = pyqtSignal()

    def __init__(self, store: CustomNodeTemplateStore, base_dir: str, parent=None):
        super().__init__(parent)
        self.store = store
        self.base_dir = base_dir
        self.current: CustomNodeTemplate = None
        self.param_rows = []
        self.setWindowTitle(tr("custom_nodes.title"))
        self.setMinimumSize(880, 620)
        self._setup_ui()
        self._reload_list()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        tabs = QTabWidget()
        outer.addWidget(tabs, 1)

        editor_tab = QWidget()
        tabs.addTab(editor_tab, tr("custom_nodes.tab_templates"))
        self._setup_editor_tab(editor_tab)

        help_tab = QWidget()
        tabs.addTab(help_tab, tr("custom_nodes.tab_help"))
        help_layout = QVBoxLayout(help_tab)
        help_scroll = QScrollArea()
        help_scroll.setWidgetResizable(True)
        help_label = QLabel(DOC_TEXT)
        help_label.setWordWrap(True)
        help_label.setTextFormat(Qt.TextFormat.RichText)
        help_label.setStyleSheet("padding:12px;")
        help_scroll.setWidget(help_label)
        help_layout.addWidget(help_scroll)

        bottom = QHBoxLayout()
        bottom.addStretch()
        btn_close = QPushButton(tr("custom_nodes.close"))
        btn_close.clicked.connect(self.accept)
        bottom.addWidget(btn_close)
        outer.addLayout(bottom)

    def _setup_editor_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)

        if not JINJA2_AVAILABLE:
            warn = QLabel(tr("custom_nodes.no_jinja2"))
            warn.setWordWrap(True)
            warn.setObjectName("warning_banner")
            warn.setStyleSheet("padding:6px;")
            layout.addWidget(warn)

        split = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.addWidget(QLabel(tr("custom_nodes.templates_label")))
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_select)
        left_l.addWidget(self.list_widget, 1)
        list_btns = QHBoxLayout()
        btn_add = QPushButton(tr("custom_nodes.new"))
        btn_add.clicked.connect(self._add_template)
        list_btns.addWidget(btn_add)
        btn_del = QPushButton(tr("custom_nodes.delete"))
        btn_del.clicked.connect(self._delete_template)
        list_btns.addWidget(btn_del)
        left_l.addLayout(list_btns)

        right = QWidget()
        right_l = QVBoxLayout(right)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel(tr("custom_nodes.name_label")))
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_field_changed)
        name_row.addWidget(self.name_edit)
        right_l.addLayout(name_row)

        right_l.addWidget(QLabel(tr("custom_nodes.desc_label")))
        self.desc_edit = QLineEdit()
        self.desc_edit.textChanged.connect(self._on_field_changed)
        right_l.addWidget(self.desc_edit)

        right_l.addWidget(QLabel(tr("custom_nodes.params_label")))
        self.params_container = QVBoxLayout()
        right_l.addLayout(self.params_container)
        btn_add_param = QPushButton(tr("custom_nodes.add_param"))
        btn_add_param.clicked.connect(self._add_param_row)
        right_l.addWidget(btn_add_param)

        right_l.addWidget(QLabel(tr("custom_nodes.jinja_template_label")))
        self.code_edit = QTextEdit()
        self.code_edit.setStyleSheet("font-family: monospace; font-size:12px;")
        self.code_edit.textChanged.connect(self._on_field_changed)
        right_l.addWidget(self.code_edit)

        right_l.addWidget(QLabel(tr("custom_nodes.preview_label")))
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setMaximumHeight(90)
        self.preview_edit.setObjectName("code_box")
        self.preview_edit.setStyleSheet("font-size:12px;")
        right_l.addWidget(self.preview_edit)

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([260, 560])
        layout.addWidget(split, 1)

        self._set_editor_enabled(False)

    def _set_editor_enabled(self, enabled: bool):
        for w in (self.name_edit, self.desc_edit, self.code_edit):
            w.setEnabled(enabled)

    def _reload_list(self):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for t in self.store.templates:
            self.list_widget.addItem(QListWidgetItem(t.name))
        self.list_widget.blockSignals(False)
        if self.store.templates:
            self.list_widget.setCurrentRow(0)
        else:
            self.current = None
            self._set_editor_enabled(False)

    def _add_template(self):
        t = CustomNodeTemplate(name=tr("custom_nodes.new_template_name", n=len(self.store.templates) + 1))
        self.store.add(t)
        self._reload_list()
        self.list_widget.setCurrentRow(len(self.store.templates) - 1)
        self._save_and_notify()

    def _delete_template(self):
        if self.current is None:
            return
        confirm = QMessageBox.question(
            self, tr("custom_nodes.delete_template_title"),
            tr("custom_nodes.delete_template_confirm", name=self.current.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.store.remove(self.current.template_id)
        self._save_and_notify()
        self._reload_list()

    def _on_select(self, row: int):
        if row < 0 or row >= len(self.store.templates):
            self.current = None
            self._set_editor_enabled(False)
            return
        self.current = self.store.templates[row]
        self._set_editor_enabled(True)
        self.name_edit.blockSignals(True)
        self.desc_edit.blockSignals(True)
        self.code_edit.blockSignals(True)
        self.name_edit.setText(self.current.name)
        self.desc_edit.setText(self.current.description)
        self.code_edit.setPlainText(self.current.code_template)
        self.name_edit.blockSignals(False)
        self.desc_edit.blockSignals(False)
        self.code_edit.blockSignals(False)
        self._reload_param_rows()
        self._update_preview()

    def _reload_param_rows(self):
        while self.params_container.count():
            item = self.params_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.param_rows = []
        if not self.current:
            return
        for p in self.current.params:
            self._make_param_row(p)

    def _make_param_row(self, param: ParamDef):
        row = ParamRow(param, self._on_field_changed, self._remove_param_row)
        self.param_rows.append(row)
        self.params_container.addWidget(row)

    def _add_param_row(self):
        if not self.current:
            return
        self._make_param_row(ParamDef(name=f"param{len(self.param_rows) + 1}"))
        self._on_field_changed()

    def _remove_param_row(self, row: ParamRow):
        self.param_rows.remove(row)
        row.hide()
        self.params_container.removeWidget(row)
        row.deleteLater()
        self._on_field_changed()

    def _on_field_changed(self):
        if not self.current:
            return
        self.current.name = self.name_edit.text().strip() or self.current.name
        self.current.description = self.desc_edit.text()
        self.current.code_template = self.code_edit.toPlainText()
        self.current.params = [r.to_param() for r in self.param_rows if r.name_edit.text().strip()]

        row = self.list_widget.currentRow()
        if row >= 0:
            item = self.list_widget.item(row)
            if item and item.text() != self.current.name:
                item.setText(self.current.name)

        self._update_preview()
        self._save_and_notify()

    def _update_preview(self):
        if not self.current:
            self.preview_edit.clear()
            return
        self.preview_edit.setPlainText(self.store.preview(self.current, pad="    "))

    def _save_and_notify(self):
        self.store.save(self.base_dir)
        self.templates_changed.emit()

    def closeEvent(self, event):
        self._save_and_notify()
        super().closeEvent(event)
