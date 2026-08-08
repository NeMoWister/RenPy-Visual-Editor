"""
Настраиваемые шаблоны генерации кода - свой стиль отступов и текста строк
для каждого типа ноды. Использует Jinja2 (если установлен); каждый шаблон -
короткий текстовый шаблон, рендерящий ОДНУ ноду в одну или несколько строк
Ren'Py-кода.

Что можно настроить:
- отступы (табы/пробелы, ширина)
- префикс комментария
- Jinja2-шаблон построчного рендеринга для каждого "простого" (негруппируемого)
  типа ноды: диалог, повествование, фон, спрайт (одиночный), CG, музыка,
  звук, метка, прыжок, пауза, return, комментарий, python, вариант меню.

ВАЖНО: группировка нескольких нод под один общий `with переход` (см.
_group_with_runs в code_generator.py) - часть структурной логики генератора
и шаблонами не переопределяется; настраиваются только отступы/комментарии и
построчный вид одиночных (негруппированных) нод.

Если Jinja2 не установлен - сохранённые кастомные шаблоны просто не
применяются (используется поведение по умолчанию, идентичное предыдущим
версиям редактора), в диалоге редактирования шаблонов будет предупреждение.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional

from core.unified_config import load_section, save_section

try:
    import jinja2
    JINJA2_AVAILABLE = True
except ImportError:
    jinja2 = None
    JINJA2_AVAILABLE = False


                                                                      
                                                                     
DEFAULT_TEMPLATES: Dict[str, str] = {
    "dialogue": '{{ pad }}{% if character_var %}{{ character_var }} {% endif %}"{{ text }}"',
    "narration": '{{ pad }}"{{ text }}"',
    "show_bg": '{{ pad }}show {{ bg_var or "black" }}{% if transition %} with {{ transition }}{% endif %}',
    "scene": '{{ pad }}scene {{ bg_var or "black" }}{% if transition %} with {{ transition }}{% endif %}',
    "show_cg": '{% if cg_var %}{{ pad }}show {{ cg_var }}{% if transition %} with {{ transition }}{% endif %}{% endif %}',
    "hide_cg": '{% if cg_var %}{{ pad }}hide {{ cg_var }} with dissolve{% endif %}',
    "play_music": '{% if music_var %}{{ pad }}play music {{ music_var }}{% if music_fadeout %} fadeout {{ music_fadeout_fmt }}{% endif %}{% if music_fadein %} fadein {{ music_fadein_fmt }}{% endif %}{% endif %}',
    "stop_music": '{{ pad }}stop music{% if music_fadeout %} fadeout {{ music_fadeout_fmt }}{% endif %}',
    "play_sound": '{% if sound_var %}{{ pad }}play sound {{ sound_var }}{% endif %}',
    "play_ambience": '{% if ambience_var %}{{ pad }}play ambience {{ ambience_var }}{% if ambience_fadeout %} fadeout {{ ambience_fadeout_fmt }}{% endif %}{% if ambience_fadein %} fadein {{ ambience_fadein_fmt }}{% endif %}{% endif %}',
    "stop_ambience": '{{ pad }}stop ambience{% if ambience_fadeout %} fadeout {{ ambience_fadeout_fmt }}{% endif %}',
    "label": 'label {{ label_name }}:',
    "jump": '{% if jump_target %}{{ pad }}jump {{ jump_target }}{% endif %}',
    "pause": '{% if pause_duration and pause_duration > 0 %}{{ pad }}pause {{ "%.1f"|format(pause_duration) }}{% else %}{{ pad }}pause{% endif %}',
    "return_": '{{ pad }}return',
    "comment": '{% if comment_text %}{{ pad }}{{ comment_prefix }} {{ comment_text }}{% endif %}',
    "python": '{{ pad }}$ {{ python_code }}',
    "menu_choice": '{{ pad }}"{{ choice_text }}":',
}

TEMPLATE_VARS_HELP: Dict[str, str] = {
    "dialogue": "pad, character_var, text",
    "narration": "pad, text",
    "show_bg": "pad, bg_var, transition",
    "scene": "pad, bg_var, transition",
    "show_cg": "pad, cg_var, transition",
    "hide_cg": "pad, cg_var",
    "play_music": "pad, music_var, music_fadeout, music_fadein",
    "stop_music": "pad, music_fadeout",
    "play_sound": "pad, sound_var",
    "play_ambience": "pad, ambience_var, ambience_fadein, ambience_fadeout",
    "stop_ambience": "pad, ambience_fadeout",
    "label": "label_name",
    "jump": "pad, jump_target",
    "pause": "pad, pause_duration",
    "return_": "pad",
    "comment": "pad, comment_text, comment_prefix",
    "python": "pad, python_code (только для однострочного $-кода)",
    "menu_choice": "pad, choice_text",
}

NODE_TYPE_LABELS: Dict[str, str] = {
    "dialogue": "💬 Диалог",
    "narration": "📖 Повествование",
    "show_bg": "🖼 Показать фон",
    "scene": "🎬 scene (со сбросом сцены)",
    "show_cg": "🖼 Показать CG",
    "hide_cg": "🗑 Скрыть CG",
    "play_music": "🎵 Музыка",
    "stop_music": "🔇 Стоп музыка",
    "play_sound": "🔊 Звук",
    "play_ambience": "🌬 Эмбиенс",
    "stop_ambience": "🔇 Стоп эмбиенс",
    "label": "🏷 Метка",
    "jump": "➡ Прыжок",
    "pause": "⏸ Пауза",
    "return_": "⏹ Return",
    "comment": "# Комментарий",
    "python": "🐍 Python (одна строка)",
    "menu_choice": "📋 Строка варианта меню",
}


@dataclass
class CodeTemplateStore:
    indent_unit: str = "spaces"                          
    indent_width: int = 4
    comment_prefix: str = "#"
    templates: Dict[str, str] = field(default_factory=dict)                            

    @classmethod
    def load(cls, base_dir: str) -> "CodeTemplateStore":
        store = cls()
        data = load_section(base_dir, "code_templates")
        try:
            store.indent_unit = data.get("indent_unit", "spaces")
            store.indent_width = int(data.get("indent_width", 4))
            store.comment_prefix = data.get("comment_prefix", "#")
            store.templates = dict(data.get("templates", {}))
        except Exception:
            pass
        return store

    def save(self, base_dir: str):
        save_section(base_dir, "code_templates", {
            "indent_unit": self.indent_unit,
            "indent_width": self.indent_width,
            "comment_prefix": self.comment_prefix,
            "templates": self.templates,
        })

    def indent_str(self) -> str:
        if self.indent_unit == "tab":
            return "\t"
        return " " * max(1, self.indent_width)

    def get_template_text(self, node_type_key: str) -> str:
        return self.templates.get(node_type_key, DEFAULT_TEMPLATES.get(node_type_key, ""))

    def set_template_text(self, node_type_key: str, text: str):
        default = DEFAULT_TEMPLATES.get(node_type_key, "")
        if text.strip() == default.strip():
            self.templates.pop(node_type_key, None)
        else:
            self.templates[node_type_key] = text

    def reset_template(self, node_type_key: str):
        self.templates.pop(node_type_key, None)

    def is_customized(self, node_type_key: str) -> bool:
        return node_type_key in self.templates

    def has_any_customizations(self) -> bool:
        return bool(self.templates) or self.indent_unit != "spaces" or self.indent_width != 4\
            or self.comment_prefix != "#"

    def render(self, node_type_key: str, context: dict) -> Optional[str]:
        """Рендерит одну ноду по её шаблону. Возвращает None, если Jinja2
        недоступен (вызывающая сторона должна использовать поведение по
        умолчанию)."""
        if not JINJA2_AVAILABLE:
            return None
        text = self.get_template_text(node_type_key)
        if not text:
            return None
        ctx = dict(context)
        ctx.setdefault("comment_prefix", self.comment_prefix)
        try:
            tmpl = jinja2.Template(text, undefined=jinja2.Undefined)
            rendered = tmpl.render(**ctx)
        except Exception as e:
            return f"# [ошибка шаблона {node_type_key}: {e}]"
        return rendered

    def preview_error(self, node_type_key: str, context: dict) -> Optional[str]:
        """Возвращает текст ошибки рендера шаблона, если есть (для UI-подсветки)."""
        if not JINJA2_AVAILABLE:
            return "Jinja2 не установлен - установите пакет 'jinja2', чтобы шаблоны применялись."
        text = self.get_template_text(node_type_key)
        try:
            jinja2.Template(text, undefined=jinja2.Undefined).render(**context)
        except Exception as e:
            return str(e)
        return None
