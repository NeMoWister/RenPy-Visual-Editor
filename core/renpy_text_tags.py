"""
Разбор текстовых тегов Ren'Py ({i}, {b}, {u}, {color=...}, {size=...},
{alpha=...}, {w}, {nw}, {fast}) в список стилизованных "кусков" текста и
список событий тайминга — используется и в статичном превью (панель
предпросмотра сцены), и в режиме презентации (там же — для посимвольной
печати текста и покадровой обработки вложенных тегов).

Незнакомые/неподдерживаемые теги (например {a=...}, {rb}, кастомные теги
проекта) молча игнорируются — их текст-содержимое остаётся, а сам тег не
влияет на стиль (безопасный fallback вместо падения парсера).
"""
import re
from dataclasses import dataclass, replace
from typing import List, Optional, Tuple

_TOKEN_RE = re.compile(r"(\{[^{}]*\})")
_TAG_RE = re.compile(r"^\{(/?)([a-zA-Z]+)(?:=([^}]*))?\}$")


@dataclass
class TextStyle:
    italic: bool = False
    bold: bool = False
    underline: bool = False
    color: Optional[str] = None
    size_delta: int = 0
    alpha: float = 1.0


@dataclass
class TextRun:
    text: str
    style: TextStyle


@dataclass
class TextEvent:
    kind: str                                         
    pos: int                                                                           
    duration: Optional[float] = None                


                                                      
_PAIRED_TAGS = {"i", "b", "u", "color", "size", "alpha"}
                                                    
_EVENT_TAGS = {"w", "nw", "fast"}


def _apply_open_tag(style: TextStyle, name: str, value: Optional[str]) -> TextStyle:
    s = replace(style)
    if name == "i":
        s.italic = True
    elif name == "b":
        s.bold = True
    elif name == "u":
        s.underline = True
    elif name == "color" and value:
        s.color = value if value.startswith("#") else f"#{value}"
    elif name == "size" and value:
        try:
            s.size_delta = int(value) if value.startswith(("+", "-")) else int(value) - 14
        except ValueError:
            pass
    elif name == "alpha" and value:
        try:
            s.alpha = max(0.0, min(1.0, float(value)))
        except ValueError:
            pass
    return s


def parse_renpy_text(raw: str) -> Tuple[List[TextRun], List[TextEvent]]:
    """Разбирает сырой текст с тегами Ren'Py в список TextRun (стилизованные
    куски видимого текста) и список TextEvent (позиции {w}/{nw}/{fast} в
    потоке видимых символов)."""
    runs: List[TextRun] = []
    events: List[TextEvent] = []
    style_stack: List[TextStyle] = [TextStyle()]
    visible_pos = 0

    for token in _TOKEN_RE.split(raw or ""):
        if not token:
            continue
        if token.startswith("{") and token.endswith("}"):
            m = _TAG_RE.match(token)
            if not m:
                continue
            closing, name, value = m.group(1) == "/", m.group(2).lower(), m.group(3)
            if name in _EVENT_TAGS and not closing:
                dur = None
                if name == "w" and value:
                    try:
                        dur = float(value)
                    except ValueError:
                        dur = None
                events.append(TextEvent(kind=name, pos=visible_pos, duration=dur))
            elif name in _PAIRED_TAGS:
                if closing:
                    if len(style_stack) > 1:
                        style_stack.pop()
                else:
                    style_stack.append(_apply_open_tag(style_stack[-1], name, value))
                                                                                 
        else:
            if token:
                runs.append(TextRun(text=token, style=style_stack[-1]))
                visible_pos += len(token)

    return runs, events


def visible_length(runs: List[TextRun]) -> int:
    return sum(len(r.text) for r in runs)


def truncate_runs(runs: List[TextRun], n: int) -> List[TextRun]:
    """Возвращает только первые n видимых символов (для покадровой печати)."""
    if n <= 0:
        return []
    result = []
    remaining = n
    for r in runs:
        if remaining <= 0:
            break
        if len(r.text) <= remaining:
            result.append(r)
            remaining -= len(r.text)
        else:
            result.append(TextRun(text=r.text[:remaining], style=r.style))
            remaining = 0
    return result


def _style_to_css(style: TextStyle, base_size: int) -> str:
    parts = []
    if style.color:
        if style.alpha < 1.0 and re.match(r"^#[0-9a-fA-F]{6}$", style.color):
            r, g, b = (int(style.color[i:i + 2], 16) for i in (1, 3, 5))
            parts.append(f"color: rgba({r},{g},{b},{style.alpha:.2f})")
        else:
            parts.append(f"color: {style.color}")
    elif style.alpha < 1.0:
        parts.append(f"color: rgba(230,230,230,{style.alpha:.2f})")
    size = max(6, base_size + style.size_delta)
    parts.append(f"font-size: {size}px")
    return ";".join(parts)


def runs_to_html(runs: List[TextRun], base_size: int = 15) -> str:
    """Рендерит список TextRun в простой HTML для QTextDocument/rich-text
    QLabel (используется и статичным превью, и диалоговым окном
    презентации)."""
    parts = []
    for r in runs:
        text = (r.text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace("\n", "<br/>"))
        css = _style_to_css(r.style, base_size)
        open_tags, close_tags = "", ""
        if r.style.bold:
            open_tags += "<b>"
            close_tags = "</b>" + close_tags
        if r.style.italic:
            open_tags += "<i>"
            close_tags = "</i>" + close_tags
        if r.style.underline:
            open_tags += "<u>"
            close_tags = "</u>" + close_tags
        parts.append(f'<span style="{css}">{open_tags}{text}{close_tags}</span>')
    return "".join(parts)


def strip_tags(raw: str) -> str:
    """Просто убирает все теги, оставляя видимый текст (для мест, где рич-
    рендеринг не нужен — списки, статистика, backlog и т.п.)."""
    runs, _ = parse_renpy_text(raw)
    return "".join(r.text for r in runs)
