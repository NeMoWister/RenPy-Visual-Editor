                       
"""
Парсер составных спрайтов Ren'Py вида:

    image cs normal stethoscope far = ConditionSwitch(
    "persistent.sprite_time=='sunset'", im.MatrixColor( im.Composite(...), im.matrix.tint(...) ),
    "persistent.sprite_time=='night'",  im.MatrixColor( im.Composite(...), im.matrix.tint(...) ),
    True, im.Composite((630,1080), (0,0), "sprites/far/cs/cs_1_body.png", (0,0), "sprites/far/cs/cs_1_stethoscope.png", (0,0), "sprites/far/cs/cs_1_normal.png") )

а также более простой вариант без условной логики:

    image un night = im.MatrixColor(
    im.Composite((900,1080), (0,0), "sprites/normal/un/un_1_body.png", (0,0), "sprites/normal/un/un_1_pioneer.png", (0,0), "sprites/normal/un/un_1_shy.png"), im.matrix.tint(0.63, 0.78, 0.82) )

Условная логика (persistent.sprite_time, im.matrix.tint) для предпросмотра и
редактора игнорируется - нас интересует только финальный набор слоёв-картинок:
берём ПОСЛЕДНИЙ найденный im.Composite(...) в блоке (для ConditionSwitch это
безусловная ветка True, идущая последней по соглашению; для одиночного
im.MatrixColor это единственный Composite).
"""
import re
import os
import bisect
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

POSITIONS = ("far", "close", "normal")                                                       
                                                                              
_HEADER_RE = re.compile(
    r'^[ \t]*image[ \t]+([a-zA-Z0-9_]+(?:[ \t]+[a-zA-Z0-9_]+)*)[ \t]*=[ \t]*',
    re.MULTILINE,
)
_COMPOSITE_START_RE = re.compile(r'im\.Composite\(')
_LAYER_RE = re.compile(r'\((-?\d+)\s*,\s*(-?\d+)\)\s*,\s*"([^"]+)"')
_SIZE_RE = re.compile(r'^\s*\((\d+)\s*,\s*(\d+)\)\s*,(.*)$', re.DOTALL)


@dataclass
class SpriteLayerDef:
    offset_x: int
    offset_y: int
    rel_path: str                                                                         


@dataclass
class CompositeSprite:
    full_name: str                                                                      
    character: str                                            
    variant_parts: List[str]                                                                    
    position: str                                            
    width: int
    height: int
    layers: List[SpriteLayerDef] = field(default_factory=list)
    source_line: int = 0                                                                           
    source: str = "custom"                                                                      

    @property
    def display_name(self) -> str:
        return " ".join(self.variant_parts) if self.variant_parts else "(без вариации)"


def _extract_last_composite(block: str):
    """Возвращает (width, height, [(ox,oy,path), ...]) для последнего
    im.Composite(...) в блоке, с корректной балансировкой скобок (внутри
    Composite могут быть произвольные вложенные конструкции)."""
    starts = [m.start() for m in _COMPOSITE_START_RE.finditer(block)]
    if not starts:
        return None
    start = starts[-1]
    open_paren = block.index('(', start)
    depth = 0
    j = open_paren
    while j < len(block):
        if block[j] == '(':
            depth += 1
        elif block[j] == ')':
            depth -= 1
            if depth == 0:
                break
        j += 1
    else:
        return None                                                                    

    inner = block[open_paren + 1:j]
    size_m = _SIZE_RE.match(inner)
    if not size_m:
        return None
    width, height = int(size_m.group(1)), int(size_m.group(2))
    rest = size_m.group(3)
    layers = [(int(ox), int(oy), path) for ox, oy, path in _LAYER_RE.findall(rest)]
    if not layers:
        return None
    return width, height, layers


def _strip_sprites_prefix(path: str) -> str:
    """Composite-пути в .rpy записаны от корня игры, например
    "sprites/far/cs/cs_1_body.png". Нам нужен путь относительно папки
    resources/sprites/, то есть "far/cs/cs_1_body.png"."""
    path = path.replace('\\', '/')
    if path.startswith('sprites/'):
        return path[len('sprites/'):]
    return path


def parse_sprites_rpy(text: str, source: str = "custom") -> List[CompositeSprite]:
    """Разбирает содержимое sprites.rpy и возвращает список составных
    спрайтов. Пропускает (не вызывает исключение) блоки, которые не удалось
    распознать - чтобы один неожиданный фрагмент не ронял парсинг всего файла.
    source помечает, из какой корневой папки ресурсов (default/custom) этот
    sprites.rpy был прочитан - нужно, чтобы resolve_layer_path знал, где
    искать сами файлы слоёв."""
    results: List[CompositeSprite] = []
    headers = list(_HEADER_RE.finditer(text))
    # позиции переводов строк - для O(log n) вычисления номера строки вместо
    # O(n) text.count(...) на каждый заголовок (критично для файлов с
    # десятками тысяч объявлений, иначе парсинг скатывается в O(n^2))
    newline_positions = [i for i, ch in enumerate(text) if ch == '\n']

    for idx, m in enumerate(headers):
        full_name = re.sub(r'\s+', ' ', m.group(1)).strip()
        block_start = m.end()
        block_end = headers[idx + 1].start() if idx + 1 < len(headers) else len(text)
        block = text[block_start:block_end]

        extracted = _extract_last_composite(block)
        if not extracted:
            continue
        width, height, raw_layers = extracted

        words = full_name.split(' ')
        if not words:
            continue
        character = words[0]
        rest_words = words[1:]
                                           
        first_layer_path = _strip_sprites_prefix(raw_layers[0][2])
        position = "normal"
        path_parts = first_layer_path.split('/')
        if path_parts and path_parts[0] in POSITIONS:
            position = path_parts[0]                                                         
        if rest_words and rest_words[-1] == position:
            variant_parts = rest_words[:-1]
        else:
            variant_parts = rest_words

        line_no = bisect.bisect_right(newline_positions, m.start()) + 1

        layers = [
            SpriteLayerDef(offset_x=ox, offset_y=oy, rel_path=_strip_sprites_prefix(path))
            for ox, oy, path in raw_layers
        ]

        results.append(CompositeSprite(
            full_name=full_name,
            character=character,
            variant_parts=variant_parts,
            position=position,
            width=width,
            height=height,
            layers=layers,
            source_line=line_no,
            source=source,
        ))

    return results


def parse_sprites_rpy_file(path: str, source: str = "custom") -> List[CompositeSprite]:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    return parse_sprites_rpy(text, source=source)


# ---------------------------------------------------------------------------
# "Отдельные" (standalone) атрибуты-исключения.
#
# Обычно атрибуты одного персонажа выстраиваются в фиксированном порядке
# (эмоция, потом одежда...), и колонка в UI редактора вычисляется по позиции
# слова внутри variant_parts. Но иногда встречается ДОПОЛНИТЕЛЬНЫЙ,
# необязательный аксессуар, вставленный ПОСЕРЕДИНЕ имени, который сбивает
# эту позиционную логику - например:
#
#   image mt grin panama pioneer far = ...      <- panama лишний, эмоция(0)/одежда(1) сдвинуты
#   image mt grin pioneer far = ...              <- а тут его нет вообще
#
# Если такое слово не выделить в собственный (необязательный) атрибут, оно
# либо ломает вычисление колонок по индексу, либо смешивается с чужой
# группой. Есть два способа его найти:
#
#   1. Явная подсказка в файле exceptions.txt, лежащем РЯДОМ с sprites.rpy
#      (см. parse_exceptions_file ниже) - персонаж -> набор слов, которые
#      ВСЕГДА должны становиться собственным отдельным атрибутом, даже если
#      автоопределение (см. ниже) почему-то не сработает.
#   2. Автоопределение (_auto_detect_extra_words): если для персонажа есть
#      "типичная" (самая частая) длина variant_parts, а слово встречается
#      ТОЛЬКО в более длинных комбинациях и никогда не входит в комбинации
#      типичной длины - оно считается необязательным дополнительным
#      атрибутом (аксессуаром), а не частью обычной позиционной цепочки.


EXCEPTIONS_FILENAME = "exceptions.txt"


def parse_exceptions_file(path: str) -> dict:
    """Читает exceptions.txt (лежит рядом с sprites.rpy, в той же папке
    sprites/): персонаж -> набор слов, которые всегда должны становиться
    собственным отдельным (необязательным) атрибутом.

    Формат - по одной записи на строку, гибкий:
        mt: panama
        mz: glasses, sunglasses
        dv panama accessory

    Разделитель между именем персонажа и словами - ":" если есть, иначе
    просто пробел. Слова между собой можно разделять запятой и/или
    пробелами. Пустые строки и строки, начинающиеся с "#", игнорируются.
    Если файла нет - возвращается пустой словарь (это нормально, значит
    для проекта используется только автоопределение)."""
    result: dict = {}
    if not path or not os.path.isfile(path):
        return result
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return result

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            character, _, rest = line.partition(':')
        else:
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            character, rest = parts[0], parts[1]
        character = character.strip()
        if not character:
            continue
        words = {w.strip() for w in re.split(r'[,\s]+', rest) if w.strip()}
        if not words:
            continue
        result.setdefault(character, set()).update(words)
    return result


def _auto_detect_extra_words(combos: List[List[str]]) -> set:
    """См. описание выше - то же самое, но по эвристике: слово считается
    отдельным необязательным атрибутом, если оно попадается ТОЛЬКО в
    комбинациях длиннее типичной (самой частой) длины и ни разу не входит
    ни в одну комбинацию типичной длины."""
    if not combos:
        return set()
    lengths = Counter(len(c) for c in combos)
    modal_len = lengths.most_common(1)[0][0]
    modal_word_pool = set()
    for c in combos:
        if len(c) == modal_len:
            modal_word_pool.update(c)
    extra = set()
    for c in combos:
        if len(c) > modal_len:
            for w in c:
                if w not in modal_word_pool:
                    extra.add(w)
    return extra


def get_standalone_attr_words(character: str, combos: List[List[str]], manual_words=None) -> set:
    """Объединяет ручные исключения из exceptions.txt (manual_words) с
    автоопределёнными - слова из этого множества всегда должны показываться
    как собственный, независимый (необязательный) атрибут, а не мешаться в
    позиционную группировку остальных атрибутов персонажа."""
    manual = set(manual_words or ())
    auto = _auto_detect_extra_words(combos)
    return manual | auto
