"""
Пользовательский белый список слов для проверки орфографии - слова здесь
никогда не помечаются как опечатка, даже если их нет в словаре
pyspellchecker (который для русского и так довольно скромный: часто
бракует нормальные слова, особенно редкие формы/имена/термины).
"""
from dataclasses import dataclass, field
from typing import List

from core.unified_config import load_section, save_section


@dataclass
class SpellcheckWhitelist:
    words: List[str] = field(default_factory=list)

    @classmethod
    def load(cls, base_dir: str) -> "SpellcheckWhitelist":
        data = load_section(base_dir, "spellcheck_whitelist")
        return cls(words=list(data.get("words", [])))

    def save(self, base_dir: str):
        save_section(base_dir, "spellcheck_whitelist", {"words": self.words})

    def as_set(self) -> set:
        return {w.strip().lower() for w in self.words if w.strip()}

    def add(self, word: str, base_dir: str):
        word = word.strip()
        if not word:
            return
        if word.lower() not in self.as_set():
            self.words.append(word)
            self.save(base_dir)
