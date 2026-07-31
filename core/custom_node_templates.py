"""
Пользовательские шаблоны нод - способ добавить в редактор СВОЙ тип ноды
(например, «Новая глава»), который в сцене выглядит и ведёт себя как
обычная нода со своими полями-параметрами, а при генерации кода
превращается в нестандартный Ren'Py/Python вызов вроде:

    $ new_chapter(3, u"Название сохранения")

Шаблон описывает:
  - имя и описание (для выбора в списке типов нод)
  - список параметров (имя, подпись, тип: строка/число/bool, значение по
    умолчанию) - по ним строится форма редактирования ноды
  - Jinja2-шаблон кода, использующий {{ имя_параметра }} и {{ pad }}
    (текущий отступ)

ВАЖНО: применение шаблона создаёт НОВУЮ ноду (NodeType.CUSTOM) с своим
node_id и собственными значениями параметров - редактирование шаблона
позже не трогает уже вставленные ноды похожего типа (у каждой свои
параметры), а меняет только то, как они будут сгенерированы в код.
"""
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.unified_config import load_section, save_section

try:
    import jinja2
    JINJA2_AVAILABLE = True
except ImportError:
    jinja2 = None
    JINJA2_AVAILABLE = False


PARAM_TYPES = ["str", "int", "float", "bool"]
PARAM_TYPE_LABELS = {"str": "Строка", "int": "Целое число", "float": "Дробное число", "bool": "Да/нет"}


@dataclass
class ParamDef:
    name: str                                                                    
    label: str = ""                                                 
    param_type: str = "str"                              
    default: Any = ""

    def coerce(self, value: Any) -> Any:
        try:
            if self.param_type == "int":
                return int(value)
            if self.param_type == "float":
                return float(value)
            if self.param_type == "bool":
                if isinstance(value, str):
                    return value.strip().lower() in ("1", "true", "yes", "да", "истина")
                return bool(value)
            return str(value)
        except (ValueError, TypeError):
            return self.default


@dataclass
class CustomNodeTemplate:
    template_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Новый шаблон"
    description: str = ""
    code_template: str = '{{ pad }}$ my_function({{ my_param }})'
    params: List[ParamDef] = field(default_factory=list)

    def default_params(self) -> Dict[str, Any]:
        return {p.name: p.default for p in self.params}

    def to_dict(self) -> dict:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "code_template": self.code_template,
            "params": [
                {"name": p.name, "label": p.label, "param_type": p.param_type, "default": p.default}
                for p in self.params
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CustomNodeTemplate":
        params = [
            ParamDef(name=p.get("name", ""), label=p.get("label", ""),
                      param_type=p.get("param_type", "str"), default=p.get("default", ""))
            for p in d.get("params", [])
        ]
        return cls(
            template_id=d.get("template_id") or str(uuid.uuid4())[:8],
            name=d.get("name", "Новый шаблон"),
            description=d.get("description", ""),
            code_template=d.get("code_template", ""),
            params=params,
        )


class CustomNodeTemplateStore:
    def __init__(self):
        self.templates: List[CustomNodeTemplate] = []

    @classmethod
    def load(cls, base_dir: str) -> "CustomNodeTemplateStore":
        store = cls()
        data = load_section(base_dir, "custom_node_templates")
        try:
            store.templates = [CustomNodeTemplate.from_dict(d) for d in data.get("templates", [])]
        except Exception:
            store.templates = []
        return store

    def save(self, base_dir: str):
        save_section(base_dir, "custom_node_templates", {
            "templates": [t.to_dict() for t in self.templates],
        })

    def get(self, template_id: str) -> Optional[CustomNodeTemplate]:
        for t in self.templates:
            if t.template_id == template_id:
                return t
        return None

    def add(self, template: CustomNodeTemplate):
        self.templates.append(template)

    def remove(self, template_id: str):
        self.templates = [t for t in self.templates if t.template_id != template_id]

    def render(self, template: CustomNodeTemplate, params: Dict[str, Any], pad: str = "") -> Optional[str]:
        """Рендерит код для КОНКРЕТНОЙ ноды (её собственные значения params).
        Возвращает None, если Jinja2 не установлен."""
        if not JINJA2_AVAILABLE:
            return None
        ctx = dict(template.default_params())
        ctx.update(params or {})
        ctx["pad"] = pad
        try:
            return jinja2.Template(template.code_template, undefined=jinja2.Undefined).render(**ctx)
        except Exception as e:
            return f"{pad}# [ошибка шаблона '{template.name}': {e}]"

    def preview(self, template: CustomNodeTemplate, pad: str = "    ") -> str:
        """Предпросмотр с параметрами по умолчанию (для диалога редактирования)."""
        if not JINJA2_AVAILABLE:
            return "(предпросмотр недоступен без пакета jinja2 - установите: pip install jinja2)"
        rendered = self.render(template, template.default_params(), pad=pad)
        return rendered if rendered is not None else ""
