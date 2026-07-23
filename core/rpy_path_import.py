                       
"""
Импорт имён/путей из произвольных .rpy файлов проекта (не только
sprites.rpy — для составных спрайтов есть отдельный composite_sprite_parser).

Распознаёт три простых, но самых частых паттерна обычного Ren'Py-проекта:

    image bg beach = "bg/beach.png"
    define audio.click = "sfx/click.ogg"
    define alice = Character("Алиса", color="#ff9966")
    music_list = {"theme": "music/theme.ogg", "battle": "music/battle.ogg"}

Сознательно НЕ пытается понять произвольный Python/составные образы вида
ConditionSwitch/im.Composite (это синтаксис, под который заточен
composite_sprite_parser.py) — здесь только однозначные "имя = путь"
присвоения, которые можно безопасно сопоставить с файлами на диске.
Всё, что не подошло по формату, просто пропускается, ничего не падает.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict

IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')
AUDIO_EXTS = ('.mp3', '.ogg', '.wav', '.flac', '.opus')

_IMAGE_RE = re.compile(r'^[ \t]*image[ \t]+([a-zA-Z0-9_ ]+?)[ \t]*=[ \t]*"([^"]+)"', re.MULTILINE)
_DEFINE_RE = re.compile(r'^[ \t]*define[ \t]+([a-zA-Z_][a-zA-Z0-9_.]*)[ \t]*=[ \t]*"([^"]+)"', re.MULTILINE)
_CHARACTER_HEAD_RE = re.compile(r'^[ \t]*define[ \t]+([a-zA-Z_][a-zA-Z0-9_]*)[ \t]*=[ \t]*Character\(', re.MULTILINE)
_MUSIC_LIST_HEAD_RE = re.compile(r'^[ \t]*music_list[ \t]*=[ \t]*\{', re.MULTILINE)
_QUOTED_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')
_COLOR_KW_RE = re.compile(r'color\s*=\s*"([^"]+)"')


@dataclass
class ParsedPathDef:
    var_name: str                                                                  
    game_path: str                                                   
    kind: str                                
    source_line: int = 0
    source_file: str = ""


@dataclass
class ParsedCharacterDef:
    variable: str
    name: str
    color: str = "#ffffff"
    source_line: int = 0
    source_file: str = ""


@dataclass
class ParsedMusicEntry:
    key: str                                                        
    game_path: str
    source_line: int = 0
    source_file: str = ""


def _norm_path(p: str) -> str:
    return p.replace('\\', '/').strip().lstrip('/')


def _looks_like_path(value: str) -> bool:
    v = value.lower()
    return v.endswith(IMAGE_EXTS) or v.endswith(AUDIO_EXTS)


def _extract_balanced(text: str, open_idx: int, open_ch='(', close_ch=')') -> Optional[str]:
    """Возвращает содержимое сбалансированных скобок начиная с open_idx
    (индекс самой открывающей скобки), без них самих. None — если скобки
    в тексте не закрылись (повреждённый/неожиданный синтаксис)."""
    depth = 0
    j = open_idx
    while j < len(text):
        if text[j] == open_ch:
            depth += 1
        elif text[j] == close_ch:
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:j]
        j += 1
    return None


def parse_image_and_define_paths(text: str, source_file: str = "") -> List[ParsedPathDef]:
    """Простые присвоения путей: image X = "путь" / define X = "путь" —
    тот же формат, который сам редактор генерирует (см.
    ResourceManager.generate_define_block), поэтому импорт по сути обратная
    операция к экспорту. Строки, где значение не похоже на путь к
    изображению/аудио (например define version = "1.0"), отбрасываются."""
    results: List[ParsedPathDef] = []

    for m in _IMAGE_RE.finditer(text):
        var = re.sub(r'\s+', ' ', m.group(1)).strip()
        path = _norm_path(m.group(2))
        if _looks_like_path(path):
            line_no = text.count('\n', 0, m.start()) + 1
            results.append(ParsedPathDef(var, path, "image", line_no, source_file))

    for m in _DEFINE_RE.finditer(text):
        var = m.group(1).strip()
        path = _norm_path(m.group(2))
        if _looks_like_path(path):
            line_no = text.count('\n', 0, m.start()) + 1
            results.append(ParsedPathDef(var, path, "define", line_no, source_file))

    return results


def parse_characters(text: str, source_file: str = "") -> List[ParsedCharacterDef]:
    results: List[ParsedCharacterDef] = []
    for m in _CHARACTER_HEAD_RE.finditer(text):
        var = m.group(1)
        open_idx = text.index('(', m.start())
        inner = _extract_balanced(text, open_idx)
        if inner is None:
            continue
        quoted = _QUOTED_RE.findall(inner)
        if not quoted:
            continue
        color_m = _COLOR_KW_RE.search(inner)
        line_no = text.count('\n', 0, m.start()) + 1
        results.append(ParsedCharacterDef(
            variable=var, name=quoted[0],
            color=color_m.group(1) if color_m else "#ffffff",
            source_line=line_no, source_file=source_file,
        ))
    return results


def parse_music_list(text: str, source_file: str = "") -> List[ParsedMusicEntry]:
    results: List[ParsedMusicEntry] = []
    m = _MUSIC_LIST_HEAD_RE.search(text)
    if not m:
        return results
    open_idx = text.index('{', m.start())
    inner = _extract_balanced(text, open_idx, '{', '}')
    if inner is None:
        return results
    line_no = text.count('\n', 0, m.start()) + 1
    for pm in re.finditer(r'"([^"]+)"\s*:\s*"([^"]+)"', inner):
        path = _norm_path(pm.group(2))
        if _looks_like_path(path):
            results.append(ParsedMusicEntry(pm.group(1), path, line_no, source_file))
    return results


@dataclass
class ImportPlanItem:
    """Один предлагаемый к применению пункт импорта пути."""
    rel_path: str                                                               
    category: str
    game_path: str
    old_var: str
    new_var: str
    source_line: int
    source_file: str
    apply: bool = True                                                     


@dataclass
class ImportReport:
    plan: List[ImportPlanItem] = field(default_factory=list)
    unmatched: List[ParsedPathDef] = field(default_factory=list)                            
    characters: List[ParsedCharacterDef] = field(default_factory=list)
    music: List[ParsedMusicEntry] = field(default_factory=list)
    unmatched_music: List[ParsedMusicEntry] = field(default_factory=list)


def build_import_report(rm, path_defs: List[ParsedPathDef],
                         characters: List[ParsedCharacterDef],
                         music_entries: List[ParsedMusicEntry]) -> ImportReport:
    """Сопоставляет распарсенные пути с реально найденными на диске файлами
    (по ResourceManager.resources[*].game_path) и строит план изменений —
    ничего не применяет, только готовит превью для пользователя."""
    report = ImportReport(characters=characters)

                                                                                    
    by_path: Dict[str, list] = {}
    for entries in rm.resources.values():
        for e in entries:
            by_path.setdefault(e.game_path.lower(), []).append(e)

    for pd in path_defs:
        matches = by_path.get(pd.game_path.lower(), [])
        if not matches:
            report.unmatched.append(pd)
            continue
        for e in matches:
            if pd.var_name == e.var_name:
                continue                                    
            report.plan.append(ImportPlanItem(
                rel_path=e.rel_path, category=e.category, game_path=e.game_path,
                old_var=e.var_name, new_var=pd.var_name,
                source_line=pd.source_line, source_file=pd.source_file,
            ))

    music_by_path = {e.game_path.lower(): e for e in rm.get('music')}
    for me in music_entries:
        entry = music_by_path.get(me.game_path.lower())
        if not entry:
            report.unmatched_music.append(me)
            continue
        new_var = f'music_list["{me.key}"]'
        if new_var != entry.var_name:
            report.plan.append(ImportPlanItem(
                rel_path=entry.rel_path, category="music", game_path=entry.game_path,
                old_var=entry.var_name, new_var=new_var,
                source_line=me.source_line, source_file=me.source_file,
            ))
        report.music.append(me)

    return report


def apply_import_report(rm, report: ImportReport) -> int:
    """Записывает отмеченные галкой пункты плана в overrides и сохраняет
    конфиг. Возвращает количество фактически изменённых ресурсов."""
    from core.resource_manager import ResourceConfig
    applied = 0
    for item in report.plan:
        if not item.apply:
            continue
        existing = rm.config.overrides.get(item.rel_path)
        custom_name = existing.custom_name if existing else ""
        rm.config.overrides[item.rel_path] = ResourceConfig(custom_name=custom_name, custom_var=item.new_var)
        applied += 1
    if applied:
        rm.save_config()
    return applied
