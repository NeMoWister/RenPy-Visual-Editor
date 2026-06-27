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
редактора игнорируется — нас интересует только финальный набор слоёв-картинок:
берём ПОСЛЕДНИЙ найденный im.Composite(...) в блоке (для ConditionSwitch это
безусловная ветка True, идущая последней по соглашению; для одиночного
im.MatrixColor это единственный Composite).
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

POSITIONS = ("far", "close", "normal")

_HEADER_RE = re.compile(
    r'^[ \t]*image[ \t]+([a-zA-Z0-9_]+(?:[ \t]+[a-zA-Z0-9_]+)*)[ \t]*=[ \t]*'
    r'(?:ConditionSwitch\(|im\.MatrixColor\([ \t]*)[ \t]*$',
    re.MULTILINE,
)
_COMPOSITE_START_RE = re.compile(r'im\.Composite\(')
_LAYER_RE = re.compile(r'\((-?\d+)\s*,\s*(-?\d+)\)\s*,\s*"([^"]+)"')
_SIZE_RE = re.compile(r'^\s*\((\d+)\s*,\s*(\d+)\)\s*,(.*)$', re.DOTALL)


@dataclass
class SpriteLayerDef:
    offset_x: int
    offset_y: int
    rel_path: str  # путь относительно resources/sprites/, например "far/cs/cs_1_body.png"


@dataclass
class CompositeSprite:
    full_name: str               # имя как в файле, например "cs normal stethoscope far"
    character: str               # первое слово, например "cs"
    variant_parts: List[str]     # средние слова без позиции, например ["normal", "stethoscope"]
    position: str                # "far" | "close" | "normal"
    width: int
    height: int
    layers: List[SpriteLayerDef] = field(default_factory=list)
    source_line: int = 0         # номер строки в sprites.rpy (для диагностики/повторной генерации)
    source: str = "custom"       # "default" | "custom" — из какого sprites.rpy спрайт распознан

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
        return None  # не нашли закрывающую скобку — повреждённый/неожиданный синтаксис

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
    распознать — чтобы один неожиданный фрагмент не ронял парсинг всего файла.
    source помечает, из какой корневой папки ресурсов (default/custom) этот
    sprites.rpy был прочитан — нужно, чтобы resolve_layer_path знал, где
    искать сами файлы слоёв."""
    results: List[CompositeSprite] = []
    headers = list(_HEADER_RE.finditer(text))

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

        # Позиция определяется по реальному пути первого слоя (надёжнее, чем
        # угадывать по последнему слову имени — слова вроде "body"/"red" не
        # являются позицией, хотя стоят на похожем месте).
        first_layer_path = _strip_sprites_prefix(raw_layers[0][2])
        position = "normal"
        path_parts = first_layer_path.split('/')
        if path_parts and path_parts[0] in POSITIONS:
            position = path_parts[0]

        # Если последнее слово имени совпадает с найденной позицией — это и
        # есть суффикс позиции, убираем его из "состава" (variant_parts).
        if rest_words and rest_words[-1] == position:
            variant_parts = rest_words[:-1]
        else:
            variant_parts = rest_words

        line_no = text.count('\n', 0, m.start()) + 1

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
