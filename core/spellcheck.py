"""
Проверка реплик (диалог/нарратор): технические проверки, которые работают
ВСЕГДА без внешних зависимостей (незакрытые Ren'Py-теги форматирования,
повторы слов, лишние пробелы/знаки препинания), плюс проверка орфографии по
словарю - если в окружении установлена библиотека pyspellchecker
(`pip install pyspellchecker`). Без неё орфография просто не проверяется,
остальные проверки продолжают работать как обычно - ничего не падает.

ВАЖНО про собранный .exe: pyspellchecker хранит словари как файлы данных
внутри пакета (не .py-код) - PyInstaller по умолчанию их не подхватывает,
если явно не добавить как data-файлы в .spec. Раньше в такой ситуации
всё молча "работало" (импорт библиотеки успешен), но ЗАГРУЗКА словаря внутри
_get_checker падала и тоже проглатывалась - проверка орфографии просто
переставала находить что-либо, без единого сообщения об этом. Теперь ошибка
загрузки словаря запоминается (см. get_diagnostics()) и показывается в
интерфейсе явно, а не тонет молча.

Намеренно не используется внешний API (LanguageTool и т.п.): в редакторе нет
гарантированного доступа в сеть, и это не должно быть жёсткой зависимостью
для базовой функциональности.

Для русского языка проверка "известно ли слово" идёт через pymorphy3
(морфологический анализ по словарю OpenCorpora), а не через частотный список
pyspellchecker: у pyspellchecker словарь ru - плоский список слов из корпуса
без словоформ, из-за чего огромная доля нормальных склонений/спряжений
считалась "опечаткой" (и заодно на каждой такой "опечатке" вызывался
медленный candidates() - отсюда и тормоза на больших проектах). pymorphy3
разбирает словоформу целиком, поэтому и точнее, и не гоняет candidates()
на каждое второе слово. pyspellchecker (если установлен) используется как
источник ПОДСКАЗОК для реально неизвестных слов, но не как решающий фактор.
Английский по-прежнему проверяется через pyspellchecker как раньше.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from core.renpy_text_tags import strip_tags
from core.i18n import tr

try:
    from spellchecker import SpellChecker as _PySpellChecker                     
    _HAS_SPELLCHECKER = True
    _IMPORT_ERROR = ""
except Exception as _e:
    _PySpellChecker = None
    _HAS_SPELLCHECKER = False
    _IMPORT_ERROR = str(_e)

try:
    import pymorphy3 as _pymorphy3
    _HAS_PYMORPHY = True
    _PYMORPHY_IMPORT_ERROR = ""
except Exception as _e:
    _pymorphy3 = None
    _HAS_PYMORPHY = False
    _PYMORPHY_IMPORT_ERROR = str(_e)

_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё]+(?:['\-][A-Za-zА-Яа-яЁё]+)*")
_ALLOWED_PUNCT_RUNS = {"...", "?!", "!?", "?!?", "!?!", "!!!", "???"}


@dataclass
class SpellIssue:
    kind: str                                                       
    message: str
    start: int = -1
    end: int = -1
    suggestions: List[str] = field(default_factory=list)
    word: str = ""                                                        


def spellchecker_available() -> bool:
    """True, если доступна хоть какая-то проверка орфографии: pymorphy3 для
    русского (приоритетный движок) ИЛИ pyspellchecker (ru/en). Раньше здесь
    проверялся только импорт pyspellchecker, из-за чего в собранном .exe (где
    словари не подхватились PyInstaller'ом) метод бодро отвечал True, но
    реальных проверок не было."""
    if _HAS_PYMORPHY and _get_morph() is not None:
        return True
    if not _HAS_SPELLCHECKER:
        return False
    return _get_checker("ru") is not None or _get_checker("en") is not None


def get_diagnostics() -> dict:
    """Подробности для интерфейса - почему проверка орфографии недоступна
    (если недоступна), чтобы не проваливаться в тишину, как раньше."""
    result = {
        "import_ok": _HAS_SPELLCHECKER,
        "import_error": _IMPORT_ERROR,
        "pymorphy_import_ok": _HAS_PYMORPHY,
        "pymorphy_import_error": _PYMORPHY_IMPORT_ERROR,
        "pymorphy_ru_ok": _get_morph() is not None,
        "dictionaries": {},
    }
    for lang in ("ru", "en"):
        checker = _get_checker(lang)
        result["dictionaries"][lang] = {
            "ok": checker is not None,
            "error": _checker_errors.get(lang, ""),
        }
    return result


_checkers: Dict[str, object] = {}
_checker_errors: Dict[str, str] = {}
                                                                          
                                                        
_word_cache: Dict[Tuple[str, str], Tuple[bool, Tuple[str, ...]]] = {}

_morph_analyzer = None                                   
_morph_init_done = False


def _get_morph():
    """Ленивая инициализация pymorphy3.MorphAnalyzer - сам разбор словаря
    занимает заметное время (десятые доли секунды на загрузку ~5МБ данных),
    поэтому создаём один раз на процесс и переиспользуем, как и с
    pyspellchecker."""
    global _morph_analyzer, _morph_init_done
    if _morph_init_done:
        return _morph_analyzer
    _morph_init_done = True
    if not _HAS_PYMORPHY:
        return None
    try:
        _morph_analyzer = _pymorphy3.MorphAnalyzer(lang='ru')
    except Exception as e:
        _checker_errors['ru_morph'] = str(e)
        _morph_analyzer = None
    return _morph_analyzer


def _is_known_ru(word_lower: str) -> bool:
    """True, только если word_lower реально есть в словаре pymorphy3.

    Раньше здесь проверялся best.tag на 'UNKN' и score первого разбора.
    Это не работало: у pymorphy3 есть встроенный морфологический
    "угадыватель" (guesser), который для НЕИЗВЕСТНЫХ слов по одному
    окончанию подбирает похожую словоформу и возвращает разбор БЕЗ метки
    UNKN и с высоким score (например "призентация" -> NOUN,femn sing,nomn,
    score=1.0). Из-за этого опечатки вида "призентация", "автомабиль"
    считались нормальными словами, и проверка орфографии их не находила.

    word_is_known() проверяет слово именно по словарю, без угадывания -
    это и есть корректный критерий "известно/неизвестно"."""
    morph = _get_morph()
    if morph is None:
        return True
    return morph.word_is_known(word_lower)


def _get_checker(lang: str):
    if not _HAS_SPELLCHECKER:
        return None
    if lang not in _checkers:
        try:
            _checkers[lang] = _PySpellChecker(language=lang)
        except Exception as e:
            _checkers[lang] = None
            _checker_errors[lang] = str(e)
    return _checkers[lang]


def clear_word_cache():
    _word_cache.clear()


def _detect_lang(text: str) -> str:
    cyr = len(re.findall(r'[А-Яа-яЁё]', text))
    lat = len(re.findall(r'[A-Za-z]', text))
    return 'ru' if cyr >= lat else 'en'


def _check_tags(raw: str) -> List[SpellIssue]:
    """Незакрытые/непарные Ren'Py-теги форматирования, напр. {b}текст без
    закрытия или лишний {/i}. Ловит именно то, что обычный спеллчекер в
    принципе не увидит, но что ломает отображение реплики в игре."""
    issues = []
    stack = []
    for m in re.finditer(r'\{(/?)(\w+)[^}]*\}', raw):
        closing, name = m.group(1), m.group(2)
        if not closing:
            stack.append((name, m.start(), m.end()))
        else:
            if stack and stack[-1][0] == name:
                stack.pop()
            else:
                issues.append(SpellIssue('tag', tr('spell.unpaired_closing_tag', name=name), m.start(), m.end()))
    for name, s, e in stack:
        issues.append(SpellIssue('tag', tr('spell.unclosed_tag', name=name), s, e))
    return issues


def _check_punctuation(clean: str) -> List[SpellIssue]:
    issues = []
    for m in re.finditer(r'  +', clean):
        issues.append(SpellIssue('punctuation', tr('spell.double_space'), m.start(), m.end()))
    for m in re.finditer(r' +([,.!?;:])', clean):
        issues.append(SpellIssue('punctuation', tr('spell.space_before_punct', ch=m.group(1)), m.start(), m.end()))
    for m in re.finditer(r'[,.!?;:]{2,}', clean):
        seg = m.group(0)
        if seg not in _ALLOWED_PUNCT_RUNS:
            issues.append(SpellIssue('punctuation', tr('spell.repeated_punct', seg=seg), m.start(), m.end()))
    return issues


def _check_repeats(clean: str) -> List[SpellIssue]:
    issues = []
    for m in re.finditer(r'\b(\w+)\s+\1\b', clean, re.IGNORECASE | re.UNICODE):
        issues.append(SpellIssue('repeat', tr('spell.repeated_word', word=m.group(1)), m.start(), m.end()))
    return issues


def _lookup_word(checker, lang: str, word_lower: str, use_morph: bool = False) -> Tuple[bool, Tuple[str, ...]]:
    """(is_unknown, suggestions) для одного слова, с кэшем на процесс -
    в прозе одни и те же слова (особенно имена персонажей и частые слова)
    встречаются десятки раз, а словарные запросы не бесплатны; для больших
    проектов кэш даёт заметное ускорение без риска (в отличие от настоящей
    многопроцессности, которая в собранном .exe - источник отдельного класса
    проблем на ровном месте).

    use_morph=True (русский с доступным pymorphy3): решение "известно ли
    слово" принимает морфологический разбор, а не плоский словарь
    pyspellchecker - тот массово ошибался на нормальных словоформах.
    pyspellchecker.candidates(), если библиотека установлена, используется
    только как источник подсказок для слов, которые pymorphy3 не опознал
    (сам по себе кандидатов не считает)."""
    key = (lang, word_lower)
    cached = _word_cache.get(key)
    if cached is not None:
        return cached

    if use_morph:
        if _is_known_ru(word_lower):
            result = (False, ())
            _word_cache[key] = result
            return result
        suggestions: Tuple[str, ...] = ()
        if checker is not None:
            try:
                candidates = checker.candidates(word_lower) or set()
                suggestions = tuple(c for c in candidates if c != word_lower)[:5]
            except Exception:
                pass
        result = (True, suggestions)
        _word_cache[key] = result
        return result

    try:
        unknown = word_lower in checker.unknown([word_lower])
    except Exception:
        _word_cache[key] = (False, ())
        return False, ()
    suggestions: Tuple[str, ...] = ()
    if unknown:
        try:
            candidates = checker.candidates(word_lower) or set()
            suggestions = tuple(c for c in candidates if c != word_lower)[:5]
        except Exception:
            pass
    result = (unknown, suggestions)
    _word_cache[key] = result
    return result


def _check_spelling(clean: str, lang: Optional[str] = None,
                     whitelist: Optional[Set[str]] = None) -> List[SpellIssue]:
    lang = lang or _detect_lang(clean)
    use_morph = lang == 'ru' and _HAS_PYMORPHY and _get_morph() is not None
    checker = _get_checker(lang) if _HAS_SPELLCHECKER else None
    if not use_morph and checker is None:
        return []
    issues = []
    for m in _WORD_RE.finditer(clean):
        word = m.group(0)
        if len(word) < 3 or word.isupper():                                        
            continue
        word_lower = word.lower()
        if whitelist and word_lower in whitelist:
            continue
        is_unknown, suggestions = _lookup_word(checker, lang, word_lower, use_morph)
        if not is_unknown:
            continue
        issues.append(SpellIssue('spelling', tr('spell.possible_typo', word=word),
                                  m.start(), m.end(), list(suggestions), word=word))
    return issues


def check_text(raw_text: str, lang: Optional[str] = None,
                whitelist: Optional[Set[str]] = None) -> List[SpellIssue]:
    """Полная проверка одной реплики. 'tag'-проблемы считаются по позициям в
    ИСХОДНОМ тексте (с тегами), остальные - по очищенному (strip_tags).
    whitelist - набор слов в нижнем регистре, которые никогда не считаются
    опечаткой (см. core.spellcheck_whitelist_store) - обычно туда попадают
    имена персонажей проекта и то, что пользователь явно добавил вручную."""
    if not raw_text:
        return []
    issues = _check_tags(raw_text)
    clean = strip_tags(raw_text)
    issues += _check_repeats(clean)
    issues += _check_punctuation(clean)
    issues += _check_spelling(clean, lang, whitelist)
    return issues
