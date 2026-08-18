"""
Модель данных для эмулятора экранов Ren'Py (screen language).

Экран (Screen) - это не то же самое, что "сцена" (Scene/SceneNode) в
остальной части редактора: сцены - это последовательность сюжетных нод
(диалоги, показ фонов/спрайтов, музыка...), а экраны (screen) - это
декларативные UI-деревья Ren'Py (главное меню, окно реплики, меню выбора,
NVL-режим, HUD и т.д.), описываемые тегами screen language (frame, hbox,
vbox, button, text, imagebutton...).

Здесь заведена собственная, независимая модель:
    * ScreenTag       - справочник поддерживаемых тегов screen language
                         (контейнеры, виджеты, управляющие конструкции).
    * ScreenElement    - один узел дерева экрана (тег + свойства + дети).
    * Screen           - экран целиком (имя, параметры, modal/zorder, корень).
    * ScreenDocument   - набор экранов одного проекта/файла screens.rpy.

Модель сознательно не пытается быть настоящей VM Ren'Py - это упрощённое,
но достаточно полное представление, которого хватает и для WYSIWYG-рендера
в редакторе, и для генерации валидного .rpy-кода.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional


_id_counter = itertools.count(1)


def _next_id() -> str:
    return f"el{next(_id_counter)}"

@dataclass(frozen=True)
class TagSpec:
    tag: str
    category: str                                                        
    has_text: bool = False                                                 
    has_action: bool = False                                         
    has_child_limit: Optional[int] = None                                    
    label: str = ""                                                 
    default_props: Dict[str, str] = field(default_factory=dict)


TAG_CATALOG: Dict[str, TagSpec] = {}


def _reg(spec: TagSpec) -> None:
    TAG_CATALOG[spec.tag] = spec
    
_reg(TagSpec("frame", "container", label="Frame (рамка)",
             default_props={"padding": "(10, 10)"}))
_reg(TagSpec("window", "container", label="Window (окно)"))
_reg(TagSpec("hbox", "container", label="HBox (горизонтальный ряд)",
             default_props={"spacing": "10"}))
_reg(TagSpec("vbox", "container", label="VBox (вертикальный столбец)",
             default_props={"spacing": "10"}))
_reg(TagSpec("fixed", "container", label="Fixed (свободное позиционирование)"))
_reg(TagSpec("grid", "container", label="Grid (сетка)",
             default_props={"cols": "2", "rows": "2", "spacing": "10"}))
_reg(TagSpec("side", "container", label="Side (компоновка по сторонам)",
             default_props={"spacing": "\"top bottom\""}))
_reg(TagSpec("viewport", "container", label="Viewport (прокручиваемая область)",
             default_props={"scrollbars": "\"vertical\""}))
_reg(TagSpec("imagemap", "container", label="Imagemap (карта-изображение)"))
_reg(TagSpec("draggroup", "container", label="DragGroup (группа drag)"))
_reg(TagSpec("drag", "container", label="Drag (перетаскиваемый элемент)",
             default_props={"draggable": "True"}))
_reg(TagSpec("button", "container", has_action=True, label="Button (кнопка-контейнер)"))
_reg(TagSpec("text", "widget", has_text=True, label="Text (текст)"))
_reg(TagSpec("label", "widget", has_text=True, label="Label (подпись стиля)"))
_reg(TagSpec("textbutton", "widget", has_text=True, has_action=True, label="TextButton (текст-кнопка)"))
_reg(TagSpec("imagebutton", "widget", has_action=True, label="ImageButton (кнопка-картинка)",
             default_props={"idle": "\"gui/button/idle.png\"", "hover": "\"gui/button/hover.png\""}))
_reg(TagSpec("image", "widget", label="Image (картинка)", default_props={"__src": "\"gui/placeholder.png\""}))
_reg(TagSpec("add", "widget", label="Add (добавить displayable)", default_props={"__src": "\"black\""}))
_reg(TagSpec("bar", "widget", label="Bar (полоса значения)",
             default_props={"value": "50", "range": "100"}))
_reg(TagSpec("vbar", "widget", label="VBar (вертикальная полоса)",
             default_props={"value": "50", "range": "100"}))
_reg(TagSpec("input", "widget", label="Input (поле ввода)",
             default_props={"default": "\"\""}))
_reg(TagSpec("null", "widget", label="Null (пустой распорка-виджет)",
             default_props={"width": "10", "height": "10"}))
_reg(TagSpec("key", "control", label="Key (обработчик клавиши)",
             default_props={"__key": "\"K_ESCAPE\"", "action": "Return()"}))
_reg(TagSpec("timer", "control", label="Timer (таймер)",
             default_props={"__seconds": "1.0", "action": "NullAction()", "repeat": "True"}))
_reg(TagSpec("mousearea", "control", label="MouseArea (зона мыши)"))
_reg(TagSpec("has", "control", label="Has (свойства следующего слоя)"))
_reg(TagSpec("use", "logic", label="Use (вставка другого экрана)",
             default_props={"__target": "other_screen"}))
_reg(TagSpec("if", "logic", label="If (условие)", default_props={"__cond": "True"}))
_reg(TagSpec("elif", "logic", label="Elif (иначе если)", default_props={"__cond": "True"}))
_reg(TagSpec("else", "logic", label="Else (иначе)"))
_reg(TagSpec("for", "logic", label="For (цикл)", default_props={"__loop": "item in []"}))
_reg(TagSpec("on", "logic", label="On (обработчик события экрана)",
             default_props={"__event": "\"show\"", "action": "NullAction()"}))

CONTAINER_TAGS = {t for t, s in TAG_CATALOG.items() if s.category in ("container", "logic")}
LEAF_TAGS = {t for t, s in TAG_CATALOG.items() if s.category == "widget"}

COMMON_POSITION_PROPS: List[str] = [
    "pos", "xpos", "ypos", "anchor", "xanchor", "yanchor",
    "align", "xalign", "yalign", "offset", "xoffset", "yoffset",
    "xcenter", "ycenter", "xysize", "xsize", "ysize",
    "xmaximum", "ymaximum", "xminimum", "yminimum", "xfill", "yfill",
    "area", "zoom", "xzoom", "yzoom", "rotate", "rotate_pad", "transform_anchor",
    "alpha", "additive", "blend", "matrixcolor", "subpixel",
    "alt", "style", "at", "id",
]

_TAG_SPECIFIC_PROPS: Dict[str, List[str]] = {
                        
    "frame": ["background", "foreground", "padding", "xpadding", "ypadding",
              "left_padding", "right_padding", "top_padding", "bottom_padding",
              "left_margin", "right_margin", "top_margin", "bottom_margin", "tile"],
    "window": ["background", "padding", "xpadding", "ypadding",
               "left_padding", "right_padding", "top_padding", "bottom_padding"],
    "hbox": ["spacing", "box_wrap", "box_wrap_spacing", "box_reverse",
             "first_spacing", "last_spacing", "fit_first"],
    "vbox": ["spacing", "box_wrap", "box_wrap_spacing", "box_reverse",
             "first_spacing", "last_spacing", "fit_first"],
    "fixed": ["fit_first"],
    "grid": ["cols", "rows", "spacing", "xspacing", "yspacing", "transpose"],
    "side": ["spacing"],
    "viewport": ["mousewheel", "draggable", "arrowkeys", "edgescroll",
                 "xinitial", "yinitial", "scrollbars", "side_spacing",
                 "xadjustment", "yadjustment"],
    "imagemap": ["ground", "hover", "idle", "selected_idle", "selected_hover",
                 "insensitive", "alpha", "cache", "auto"],
    "draggroup": [],
    "drag": ["drag_name", "draggable", "droppable", "dragged", "dropped",
             "drag_offscreen", "drag_raise", "drag_handle", "focus_mask"],
    "button": ["action", "alternate", "selected", "sensitive", "keysym",
               "hovered", "unhovered", "hover_sound", "activate_sound",
               "focus_mask", "keyboard_focus", "tooltip"],
    "text": ["color", "size", "font", "bold", "italic", "underline",
             "strikethrough", "kerning", "line_spacing", "text_align",
             "layout", "min_width", "justify", "first_indent", "rest_indent",
             "antialias", "vertical", "drop_shadow", "drop_shadow_color",
             "hinting", "language", "newline_indent", "outlines",
             "ruby_style", "slow_cps", "slow_abortable", "textalign"],
    "label": ["color", "size", "font", "bold", "italic", "text_align", "style"],
    "textbutton": ["text_color", "text_size", "text_font", "text_bold",
                   "text_italic", "text_align", "text_outlines",
                   "hover_color", "selected_color", "insensitive_color",
                   "idle_color", "action", "alternate", "selected",
                   "sensitive", "keysym", "hover_sound", "activate_sound"],
    "imagebutton": ["idle", "hover", "selected_idle", "selected_hover",
                    "insensitive", "selected_insensitive", "auto",
                    "action", "alternate", "selected", "sensitive"],
    "image": ["xsize", "ysize", "xysize", "zoom", "xzoom", "yzoom", "alpha",
              "rotate", "crop", "corner1", "corner2", "subpixel", "blend"],
    "add": ["xsize", "ysize", "xysize", "zoom", "xzoom", "yzoom", "alpha",
            "rotate", "crop", "corner1", "corner2", "subpixel", "blend"],
    "bar": ["value", "range", "width", "height", "thumb", "thumb_shadow",
            "thumb_offset", "base_bar", "left_bar", "right_bar", "top_bar",
            "bottom_bar", "hovered", "unhovered", "changed", "bar_invert",
            "unscrollable"],
    "vbar": ["value", "range", "width", "height", "thumb", "thumb_shadow",
             "thumb_offset", "base_bar", "top_bar", "bottom_bar", "left_bar",
             "right_bar", "hovered", "unhovered", "changed", "bar_invert",
             "unscrollable"],
    "input": ["default", "length", "allow", "exclude", "prefix", "suffix",
              "changed", "copypaste", "caret_blink", "edit_text", "color", "size"],
    "null": ["width", "height"],
    "key": [],
    "timer": ["repeat"],
    "mousearea": ["hovered", "unhovered", "focus_mask", "area"],
    "has": [],
    "use": [],
    "if": [],
    "elif": [],
    "else": [],
    "for": [],
    "on": [],
}


def property_fields_for(tag: str) -> List[str]:
    """Полный список ИМЁН свойств (без значений), которые Ren'Py понимает
    для данного тега - специфичные для тега + общие позиционные. Пустые
    (незаполненные) поля из этого списка просто не сохраняются в
    el.properties и не появляются в сгенерированном коде."""          
    specific = _TAG_SPECIFIC_PROPS.get(tag, [])
    combined: List[str] = list(specific)
    for p in COMMON_POSITION_PROPS:
        if p not in combined:
            combined.append(p)
    return combined


def default_element(tag: str) -> "ScreenElement":
    spec = TAG_CATALOG[tag]
    props = dict(spec.default_props)
    el = ScreenElement(tag=tag)
    if spec.has_text:
        el.text = "Текст" if tag != "textbutton" else "Кнопка"
    for k, v in props.items():
        if k == "__src":
            el.source = v
        elif k == "__cond":
            el.condition = v
        elif k == "__loop":
            el.loop_expr = v
        elif k == "__target":
            el.use_target = v
        elif k == "__key":
            el.key_name = v
        elif k == "__seconds":
            el.timer_seconds = v
        elif k == "__event":
            el.on_event = v
        else:
            el.properties[k] = v
    return el

@dataclass
class ScreenElement:
    tag: str
    id: str = field(default_factory=_next_id)
    text: str = ""                                                  
    action: str = ""                                                                     
    source: str = ""                                                               
    condition: str = ""                               
    loop_expr: str = ""                                                                
    use_target: str = ""                          
    key_name: str = ""                            
    timer_seconds: str = "1.0"                      
    on_event: str = "\"show\""                   
    properties: Dict[str, str] = field(default_factory=dict)                                
    children: List["ScreenElement"] = field(default_factory=list)
    canvas_x: int = 0
    canvas_y: int = 0
    canvas_w: int = 120
    canvas_h: int = 36

    @property
    def spec(self) -> TagSpec:
        return TAG_CATALOG[self.tag]

    @property
    def is_container(self) -> bool:
        return self.spec.category in ("container", "logic")

    def clone(self) -> "ScreenElement":
        new = ScreenElement(
            tag=self.tag, text=self.text, action=self.action, source=self.source,
            condition=self.condition, loop_expr=self.loop_expr, use_target=self.use_target,
            key_name=self.key_name, timer_seconds=self.timer_seconds, on_event=self.on_event,
            properties=dict(self.properties),
            canvas_x=self.canvas_x, canvas_y=self.canvas_y,
            canvas_w=self.canvas_w, canvas_h=self.canvas_h,
        )
        new.children = [c.clone() for c in self.children]
        return new

    def find(self, el_id: str) -> Optional["ScreenElement"]:
        if self.id == el_id:
            return self
        for c in self.children:
            found = c.find(el_id)
            if found:
                return found
        return None

    def find_parent(self, el_id: str) -> Optional["ScreenElement"]:
        for c in self.children:
            if c.id == el_id:
                return self
            found = c.find_parent(el_id)
            if found:
                return found
        return None

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


SCREEN_KIND_ROOT_TAG = {
    "generic": "fixed",
    "say": "window",
    "choice": "vbox",
    "nvl": "vbox",
    "input": "vbox",
    "confirm": "vbox",
}


@dataclass
class Screen:
    name: str = "new_screen"
    parameters: str = ""                                                                  
    modal: bool = False
    zorder: str = ""                                 
    tag: str = ""                                                                         
    root: ScreenElement = field(default_factory=lambda: default_element("fixed"))
    description: str = ""

    def clone(self) -> "Screen":
        s = Screen(name=self.name, parameters=self.parameters, modal=self.modal,
                   zorder=self.zorder, tag=self.tag, description=self.description)
        s.root = self.root.clone()
        return s


@dataclass
class ScreenDocument:
    """Набор экранов, которые редактируются/экспортируются вместе (обычно
    соответствует одному screens.rpy)."""          
    screens: List[Screen] = field(default_factory=list)

    def add(self, screen: Screen) -> None:
        self.screens.append(screen)

    def remove(self, name: str) -> None:
        self.screens = [s for s in self.screens if s.name != name]

    def get(self, name: str) -> Optional[Screen]:
        for s in self.screens:
            if s.name == name:
                return s
        return None

    def unique_name(self, base: str) -> str:
        existing = {s.name for s in self.screens}
        if base not in existing:
            return base
        for i in itertools.count(2):
            candidate = f"{base}_{i}"
            if candidate not in existing:
                return candidate
