                       
"""
Движок отображения HTML-документов в QTextBrowser.

Руководство пользователя хранится как готовая HTML-строка
(USER_GUIDE_HTML в help_content.py) - никаких самописных парсеров Markdown.
Картинки вставлены как плейсхолдеры {{key}}, которые заменяются на
data:image/png;base64,... из HELP_IMAGES перед setHtml().

API совместим со старой версией: MarkdownView(html, images) +
set_markdown(html, images), чтобы help_dialog.py не пришлось переписывать.

Синтаксис картинок в HTML:
    <img src="{{key}}">               - натуральный размер
    <img src="{{key}}" width="100%">  - растянуть на ширину окна
    <img src="{{key}}" width="480">   - фиксированная ширина в пикселях

ВАЖНО про высоту картинок:
QTextBrowser (rich-text движок Qt) при указании только width НЕ пересчитывает
height пропорционально - картинка остаётся с исходной пиксельной высотой,
а по ширине просто сжимается/растягивается. Из-за этого под картинкой
появляются "пустые" строки (реально это недостающая по высоте картинка)
и сама картинка выглядит нецентрированной/искажённой.
Поэтому render_html() ПОСЛЕ подстановки data URI дополнительно простав-
ляет каждому <img> явные width И height в пикселях, рассчитанные из
реального размера PNG (см. _fix_image_dimensions()), с сохранением
пропорций. width="100%" трактуется как CONTAINER_WIDTH_PX.
"""
import base64
import re
import struct
from typing import Dict, Optional

from PyQt6.QtWidgets import QTextBrowser

                                                                      
                                                                         
                           
CONTAINER_WIDTH_PX = 900
                                                                      
                                                                      
MAX_NATURAL_WIDTH_PX = 900


PALETTE = {
    "background": "#1e1e24",
    "text": "#cccccc",
    "heading": "#ffffff",
    "muted": "#9a9a9a",
    "accent": "#ff8c3d",
    "rule": "#3a3a46",
    "heading_rule": "#ff8c3d",
    "border": "#3a3a46",
    "code_bg": "#1a1a21",
    "code_fg": "#ffb060",
    "table_header_bg": "#232330",
    "table_row_bg": "#22222a",
    "quote_bg": "#25252d",
    "link": "#ff8c3d",
}

BASE_FONT_SIZE_PT = 10.5
CODE_FONT_FAMILIES = "Consolas, 'Courier New', monospace"

                                                                  
                                                                       
                                                                           
                                                            
_PLACEHOLDER_RE = re.compile(r'\{\{(?P<key>[a-zA-Z_][a-zA-Z0-9_]*)\}\}')


def _build_stylesheet() -> str:
    p = PALETTE
    return f"""
<style>
body {{
    color: {p['text']};
    background: {p['background']};
    font-family: 'Segoe UI', 'DejaVu Sans', sans-serif;
    font-size: {BASE_FONT_SIZE_PT}pt;
    line-height: 1.45;
}}
h1, h2, h3, h4 {{
    color: {p['heading']};
    font-weight: bold;
    margin-top: 18px;
    margin-bottom: 6px;
}}
h1 {{
    font-size: 18pt;
    border-bottom: 2px solid {p['heading_rule']};
    padding-bottom: 4px;
}}
h2 {{
    font-size: 15pt;
    border-bottom: 1px solid {p['rule']};
    padding-bottom: 4px;
}}
h3 {{ font-size: 12.5pt; }}
h4 {{ font-size: 11pt; }}
p {{ margin: 6px 0; }}
a {{ color: {p['link']}; }}
strong {{ color: {p['heading']}; font-weight: bold; }}
em {{ font-style: italic; }}
code {{
    font-family: {CODE_FONT_FAMILIES};
    background: {p['code_bg']};
    color: {p['code_fg']};
    padding: 1px 4px;
}}
pre {{
    background: {p['code_bg']};
    color: {p['text']};
    font-family: {CODE_FONT_FAMILIES};
    font-size: 9.5pt;
    padding: 10px;
    border: 1px solid {p['border']};
    margin: 8px 0;
    white-space: pre-wrap;
}}
pre code {{
    background: transparent;
    color: {p['text']};
    padding: 0;
}}
blockquote {{
    background: {p['quote_bg']};
    color: {p['muted']};
    font-style: italic;
    border-left: 3px solid {p['accent']};
    margin: 10px 0;
    padding: 8px 16px;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;
    background: {p['border']};
}}
th {{
    background: {p['table_header_bg']};
    color: {p['heading']};
    font-weight: bold;
    padding: 6px 10px;
    border: 1px solid {p['border']};
    text-align: left;
}}
td {{
    background: {p['table_row_bg']};
    color: {p['text']};
    padding: 6px 10px;
    border: 1px solid {p['border']};
}}
ul, ol {{
    margin: 6px 0;
    padding-left: 24px;
}}
li {{ margin: 2px 0; }}
hr {{
    border: none;
    border-top: 1px solid {p['rule']};
    margin: 12px 0;
}}
img {{ border: 1px solid {p['border']}; }}
</style>
"""


def _png_size(data_uri: str) -> Optional[tuple]:
    """Возвращает (width, height) PNG-картинки из data URI, либо None."""
    prefix = "base64,"
    idx = data_uri.find(prefix)
    if idx == -1:
        return None
    b64 = data_uri[idx + len(prefix):]
    try:
        raw = base64.b64decode(b64[:64])                              
        if len(raw) < 24:
            return None
        w, h = struct.unpack(">II", raw[16:24])
        return (w, h)
    except Exception:
        return None


                                                                              
_IMG_TAG_RE = re.compile(r'<img\b([^>]*)>', re.IGNORECASE)
_ATTR_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')


def _fix_image_dimensions(html: str) -> str:
    """Проставляет каждому <img> явные width/height в пикселях, сохраняя
    пропорции исходной картинки. Без этого QTextBrowser не умеет
    пересчитывать height при заданном только width, что приводит к
    "пустым" строкам под картинкой и нецентрированной/искажённой вёрстке.
    """
    def _fix_one(m: re.Match) -> str:
        attrs_str = m.group(1)
        attrs = dict(_ATTR_RE.findall(attrs_str))
        src = attrs.get("src", "")
        size = _png_size(src) if src.startswith("data:image") else None
        if size is None:
            return m.group(0)
        nat_w, nat_h = size
        if nat_w <= 0 or nat_h <= 0:
            return m.group(0)

        width_attr = attrs.get("width")
        if width_attr is None:
                                                                 
            disp_w = min(nat_w, MAX_NATURAL_WIDTH_PX)
        elif width_attr.strip().endswith("%"):
            disp_w = CONTAINER_WIDTH_PX
        else:
            try:
                disp_w = int(float(width_attr))
            except ValueError:
                disp_w = min(nat_w, MAX_NATURAL_WIDTH_PX)

        disp_h = round(disp_w * nat_h / nat_w)

                                                                      
                                                           
        rest = _ATTR_RE.sub(
            lambda am: "" if am.group(1).lower() in ("width", "height")
            else am.group(0),
            attrs_str,
        ).strip()
        return f'<img {rest} width="{disp_w}" height="{disp_h}">'.replace(
            "<img  ", "<img "
        )

    return _IMG_TAG_RE.sub(_fix_one, html)


                                                                       
                                                                          
                                                                        
                                                                      
                                                             
_P_ONLY_IMG_RE = re.compile(
    r'<p\b([^>]*)>\s*(<img\b[^>]*>)\s*</p>', re.IGNORECASE
)
_STYLE_ATTR_RE = re.compile(r'style\s*=\s*"([^"]*)"', re.IGNORECASE)


def _tighten_image_paragraphs(html: str) -> str:
    def _fix_one(m: re.Match) -> str:
        p_attrs, img_tag = m.group(1), m.group(2)
        style_m = _STYLE_ATTR_RE.search(p_attrs)
        if style_m:
            style = style_m.group(1).rstrip(";")
            new_style = f'{style};line-height:1;'
            p_attrs = (p_attrs[:style_m.start()] +
                       f'style="{new_style}"' +
                       p_attrs[style_m.end():])
        else:
            p_attrs = f'{p_attrs} style="line-height:1;"'
        return f'<p{p_attrs}>{img_tag}</p>'

    return _P_ONLY_IMG_RE.sub(_fix_one, html)


def render_html(body_html: str, images: Dict[str, str]) -> str:
    """Заменяет плейсхолдеры {{key}} на data:image/...;base64,... и
    оборачивает body в HTML-документ с тёмной темой."""
    def _sub(m: re.Match) -> str:
        key = m.group('key')
        data_uri = images.get(key)
        if not data_uri:
            return (f'<span style="background:#2a1a00;color:#ffb060;'
                    f'font-style:italic;padding:2px 6px;">'
                    f'[изображение не найдено: {key}]</span>')
        return data_uri

    body = _PLACEHOLDER_RE.sub(_sub, body_html)
    body = _fix_image_dimensions(body)
    body = _tighten_image_paragraphs(body)
    return (
        '<!DOCTYPE html>\n'
        '<html><head><meta charset="utf-8">'
        f'{_build_stylesheet()}'
        '</head><body>\n'
        f'{body}\n'
        '</body></html>\n'
    )


class MarkdownView(QTextBrowser):
    """QTextBrowser, отображающий HTML с тёмной темой.

    Имя класса сохранено для совместимости с help_dialog.py; на самом
    деле это просто HTML-вьювер. Первый аргумент конструктора - HTML
    (а не Markdown), но имя метода set_markdown() оставлено прежним
    по той же причине.
    """

    def __init__(self, html: str = "",
                 images: Optional[Dict[str, str]] = None, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.setReadOnly(True)
        if html:
            self.set_markdown(html, images or {})

    def set_markdown(self, html: str,
                     images: Optional[Dict[str, str]] = None):
        """Загружает HTML в QTextBrowser. Имя метода сохранено для
        совместимости со старым API; фактически это set_html()."""
        self.setHtml(render_html(html, images or {}))
