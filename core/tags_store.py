                       
"""
Теги для фонов и CG: отдельная база категорий тегов (например, "Локация",
"Время суток") — в каждой категории может быть несколько тегов ("пляж",
"лес", "город"). У одного ресурса может быть сразу несколько тегов из
разных (или даже одной) категорий.

Хранится глобально в базовой папке приложения (рядом с .exe или main.py),
как и переопределения имён ресурсов и список персонажей — не привязано к
конкретному проекту.

Формат ключа тега: "<id_категории>:<текст_тега>", например "location:пляж".
Так один и тот же текст тега в разных категориях не конфликтует, а отвязка
тега от категории видна напрямую по ключу.
"""
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

from core.unified_config import load_section, save_section


@dataclass
class TagCategory:
    id: str
    name: str
    tags: List[str] = field(default_factory=list)


class TagsStore:
    def __init__(self):
        self.categories: List[TagCategory] = []
                                                                   
        self.resource_tags: Dict[str, List[str]] = {}

                                                                          

    @classmethod
    def load(cls, base_dir: str) -> "TagsStore":
        store = cls()
        data = load_section(base_dir, "tags")
        try:
            store.categories = [TagCategory(**c) for c in data.get("categories", [])]
            store.resource_tags = {k: list(v) for k, v in data.get("resource_tags", {}).items()}
        except Exception:
            pass
        return store

    def save(self, base_dir: str):
        save_section(base_dir, "tags", {
            "categories": [asdict(c) for c in self.categories],
            "resource_tags": self.resource_tags,
        })

                                                                           

    def get_category(self, category_id: str) -> Optional[TagCategory]:
        for c in self.categories:
            if c.id == category_id:
                return c
        return None

    def add_category(self, name: str) -> TagCategory:
        cat = TagCategory(id=uuid.uuid4().hex[:8], name=name.strip())
        self.categories.append(cat)
        return cat

    def rename_category(self, category_id: str, new_name: str):
        cat = self.get_category(category_id)
        if cat:
            cat.name = new_name.strip()

    def remove_category(self, category_id: str):
        self.categories = [c for c in self.categories if c.id != category_id]
        prefix = f"{category_id}:"
        for var, keys in list(self.resource_tags.items()):
            self.resource_tags[var] = [k for k in keys if not k.startswith(prefix)]
            if not self.resource_tags[var]:
                del self.resource_tags[var]

                                                                           

    def add_tag(self, category_id: str, tag_text: str) -> bool:
        cat = self.get_category(category_id)
        tag_text = tag_text.strip()
        if not cat or not tag_text or tag_text in cat.tags:
            return False
        cat.tags.append(tag_text)
        return True

    def remove_tag(self, category_id: str, tag_text: str):
        cat = self.get_category(category_id)
        if cat and tag_text in cat.tags:
            cat.tags.remove(tag_text)
        key = f"{category_id}:{tag_text}"
        for var, keys in list(self.resource_tags.items()):
            if key in keys:
                keys.remove(key)
                if not keys:
                    del self.resource_tags[var]

                                                                           

    def get_tags_for(self, var_name: str) -> List[str]:
        return list(self.resource_tags.get(var_name, []))

    def set_tags_for(self, var_name: str, keys: List[str]):
        keys = [k for k in keys if k]
        if keys:
            self.resource_tags[var_name] = keys
        elif var_name in self.resource_tags:
            del self.resource_tags[var_name]

    def has_tag_in_category(self, var_name: str, category_id: str) -> bool:
        prefix = f"{category_id}:"
        return any(k.startswith(prefix) for k in self.resource_tags.get(var_name, []))

    def has_tag(self, var_name: str, category_id: str, tag_text: str) -> bool:
        return f"{category_id}:{tag_text}" in self.resource_tags.get(var_name, [])

    def tag_label(self, key: str) -> str:
        """Человекочитаемая подпись ключа тега, например 'Локация: пляж'."""
        if ":" not in key:
            return key
        cat_id, tag_text = key.split(":", 1)
        cat = self.get_category(cat_id)
        return f"{cat.name}: {tag_text}" if cat else key
