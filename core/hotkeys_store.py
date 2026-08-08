"""
Настраиваемые горячие клавиши для частых операций (в первую очередь -
быстрое добавление нод нужного типа, чтобы не лезть каждый раз в комбобокс
типа ноды). Хранится в секции "hotkeys" общего editor_config.json.
"""
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Optional

from core.unified_config import load_section, save_section

                                                                         
_ACTION_KEYS = OrderedDict([
    ("add_dialogue",     ("hotkey.add_dialogue",     "Ctrl+1")),
    ("add_narration",    ("hotkey.add_narration",    "Ctrl+2")),
    ("add_show_sprite",  ("hotkey.add_show_sprite",  "Ctrl+3")),
    ("add_hide_sprite",  ("hotkey.add_hide_sprite",  "Ctrl+4")),
    ("add_show_bg",      ("hotkey.add_show_bg",      "Ctrl+5")),
    ("add_pause",        ("hotkey.add_pause",        "Ctrl+6")),
    ("add_menu",         ("hotkey.add_menu",         "Ctrl+7")),
    ("duplicate_node",   ("hotkey.duplicate_node",   "Ctrl+D")),
    ("move_node_up",     ("hotkey.move_node_up",     "Ctrl+Up")),
    ("move_node_down",   ("hotkey.move_node_down",   "Ctrl+Down")),
])


def _build_actions():
    from core.i18n import tr
    return OrderedDict(
        (action_id, (tr(i18n_key), default_key))
        for action_id, (i18n_key, default_key) in _ACTION_KEYS.items()
    )


class _ActionsProxy:
    """Ведёт себя как ACTIONS (dict-подобный доступ), но перестраивает
    переводы меток при каждом обращении - так тумблер языка в настройках
    сразу отражается в таблице горячих клавиш без перезапуска."""

    def items(self):
        return _build_actions().items()

    def get(self, key, default=None):
        return _build_actions().get(key, default)

    def __getitem__(self, key):
        return _build_actions()[key]

    def __iter__(self):
        return iter(_build_actions())

    def __len__(self):
        return len(_ACTION_KEYS)


ACTIONS = _ActionsProxy()

DEFAULTS: Dict[str, str] = {k: v[1] for k, v in _ACTION_KEYS.items()}


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
