"""
Настраиваемые горячие клавиши для частых операций (в первую очередь —
быстрое добавление нод нужного типа, чтобы не лезть каждый раз в комбобокс
типа ноды). Хранится в секции "hotkeys" общего editor_config.json.
"""
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Optional

from core.unified_config import load_section, save_section

                                                                         
ACTIONS: "OrderedDict[str, tuple]" = OrderedDict([
    ("add_dialogue",     ("Добавить ноду: 💬 Реплика",           "Ctrl+1")),
    ("add_narration",    ("Добавить ноду: 📖 Повествование",     "Ctrl+2")),
    ("add_show_sprite",  ("Добавить ноду: 🧍 Показать спрайт",   "Ctrl+3")),
    ("add_hide_sprite",  ("Добавить ноду: 🚫 Скрыть спрайт",     "Ctrl+4")),
    ("add_show_bg",      ("Добавить ноду: 🖼 Показать фон",      "Ctrl+5")),
    ("add_pause",        ("Добавить ноду: ⏸ Пауза",              "Ctrl+6")),
    ("add_menu",         ("Добавить ноду: 📋 Меню выбора",       "Ctrl+7")),
    ("duplicate_node",   ("Дублировать текущую ноду",            "Ctrl+D")),
    ("move_node_up",     ("Переместить ноду вверх",               "Ctrl+Up")),
    ("move_node_down",   ("Переместить ноду вниз",                "Ctrl+Down")),
])

DEFAULTS: Dict[str, str] = {k: v[1] for k, v in ACTIONS.items()}


@dataclass
class HotkeyStore:
    bindings: Dict[str, str] = None

    def __post_init__(self):
        if self.bindings is None:
            self.bindings = dict(DEFAULTS)

    @classmethod
    def load(cls, base_dir: str) -> "HotkeyStore":
        data = load_section(base_dir, "hotkeys")
        bindings = dict(DEFAULTS)
        try:
            for k, v in data.get("bindings", {}).items():
                if k in DEFAULTS and isinstance(v, str):
                    bindings[k] = v
        except Exception:
            pass
        return cls(bindings=bindings)

    def save(self, base_dir: str):
        save_section(base_dir, "hotkeys", {"bindings": self.bindings})

    def get(self, action_id: str) -> str:
        return self.bindings.get(action_id, DEFAULTS.get(action_id, ""))

    def set(self, action_id: str, key_sequence: str):
        self.bindings[action_id] = key_sequence

    def reset(self, action_id: str):
        self.bindings[action_id] = DEFAULTS.get(action_id, "")

    def reset_all(self):
        self.bindings = dict(DEFAULTS)

    def find_conflict(self, action_id: str, key_sequence: str) -> Optional[str]:
        """Возвращает action_id другого действия с той же клавишей, если есть."""
        if not key_sequence:
            return None
        for other_id, seq in self.bindings.items():
            if other_id != action_id and seq and seq.strip().lower() == key_sequence.strip().lower():
                return other_id
        return None
