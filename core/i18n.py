"""
Простой менеджер интернационализации (i18n).

Все переводы хранятся в одном файле - core/translations.py, в виде словаря:

    TRANSLATIONS = {
        "menu.file": {"ru": "Файл", "en": "File"},
        ...
    }

Чтобы добавить новый язык, достаточно добавить соответствующий ключ
("de", "fr", ...) в записи core/translations.py - никакой другой код
менять не нужно. Новый язык автоматически появится в тумблере настроек
(см. AVAILABLE_LANGUAGES ниже - он строится из данных самого словаря).

Использование в UI-коде:

    from core.i18n import tr

    label = QLabel(tr("dialog.title"))

Если для текущего языка перевода нет - используется русский (ru) как
язык по умолчанию, а если нет и его - возвращается сам ключ (чтобы сразу
было видно в интерфейсе, что перевод не добавлен).

Строки с подстановкой параметров:

    tr("autosave.interval", seconds=30)  ->  "Каждые {seconds} секунд"
    формируется через str.format(**kwargs).
"""
from core.translations import TRANSLATIONS

DEFAULT_LANGUAGE = "ru"
FALLBACK_LANGUAGE = "ru"
                                             
                                                             
LANGUAGE_NAMES = {
    "ru": "Русский",
    "en": "English",
}


class Translator:
    """Хранит текущий выбранный язык и отдаёт переводы по ключу."""

    def __init__(self, language: str = DEFAULT_LANGUAGE):
        self._language = language if language in self.available_languages() else DEFAULT_LANGUAGE

    def available_languages(self) -> list:
        """Список кодов языков, реально присутствующих в TRANSLATIONS."""
        codes = set()
        for entry in TRANSLATIONS.values():
            codes.update(entry.keys())
        if not codes:
            codes = {DEFAULT_LANGUAGE}
                                              
        ordered = sorted(codes, key=lambda c: (c != DEFAULT_LANGUAGE, LANGUAGE_NAMES.get(c, c)))
        return ordered

    def get_language(self) -> str:
        return self._language

    def set_language(self, language: str):
        if language in self.available_languages():
            self._language = language

    def tr(self, translation_key: str, **kwargs) -> str:
        entry = TRANSLATIONS.get(translation_key)
        if entry is None:
                                                               
                                                                    
            return translation_key
        text = entry.get(self._language) or entry.get(FALLBACK_LANGUAGE) or translation_key
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text
                                       
_translator = Translator()


def init_translator(language: str):
    """Вызывается один раз при старте приложения (main.py) с языком из настроек."""
    global _translator
    _translator = Translator(language)


def set_language(language: str):
    _translator.set_language(language)


def get_language() -> str:
    return _translator.get_language()


def available_languages() -> list:
    return _translator.available_languages()


def language_display_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


def tr(translation_key: str, **kwargs) -> str:
    return _translator.tr(translation_key, **kwargs)


def plural(count: int, forms: dict) -> str:
    """Возвращает нужную форму слова в зависимости от числа и текущего языка.

    forms - словарь вида:
        {
            "ru": ("место", "места", "мест"),   # 1, 2-4, 5+ (с учётом искл. 11-14)
            "en": ("place", "places"),           # 1, other
        }
    Если для текущего языка форм нет - используется ru, а если нет и её -
    просто возвращается str(count).
    """
    lang = get_language()
    lang_forms = forms.get(lang) or forms.get(FALLBACK_LANGUAGE)
    if not lang_forms:
        return str(count)
    if len(lang_forms) >= 3:
        n = abs(count) % 100
        n1 = n % 10
        if 11 <= n <= 14:
            return lang_forms[2]
        if n1 == 1:
            return lang_forms[0]
        if 2 <= n1 <= 4:
            return lang_forms[1]
        return lang_forms[2]
                                                             
    return lang_forms[0] if count == 1 else lang_forms[1]
