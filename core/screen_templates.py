"""
Готовые шаблоны экранов Ren'Py - отправная точка для WYSIWYG-редактора
экранов (core/screen_model.py, ui/screen_editor_window.py).

Каждая функция возвращает новый Screen (со своим независимым деревом
ScreenElement), который можно сразу открыть в редакторе, а затем изменить.
"""
from .screen_model import Screen, ScreenElement, default_element


def _el(tag: str, **kw) -> ScreenElement:
    el = default_element(tag)
    for k, v in kw.items():
        if k == "props":
            el.properties.update(v)
        else:
            setattr(el, k, v)
    return el


def tpl_main_menu() -> Screen:
    s = Screen(name="main_menu", tag="menu")
    root = _el("fixed")
    bg = _el("add", source='"gui/main_menu.png"')
    box = _el("vbox", props={"xalign": "0.98", "yalign": "0.5", "spacing": "6"})
    box.children = [
        _el("textbutton", text="Начать игру", action="Start()"),
        _el("textbutton", text="Загрузить", action="ShowMenu(\"load\")"),
        _el("textbutton", text="Настройки", action="ShowMenu(\"preferences\")"),
        _el("textbutton", text="О игре", action="ShowMenu(\"about\")"),
        _el("textbutton", text="Выход", action="Quit(confirm=False)"),
    ]
    root.children = [bg, box]
    s.root = root
    s.description = "Главное меню игры с фоном и вертикальным списком кнопок."
    return s


def tpl_say() -> Screen:
    s = Screen(name="say", tag="")
    root = _el("fixed")
    window = _el("window", props={"id": "window"})
    vb = _el("vbox")
    who = _el("text", text="[who]", props={"id": "who", "style": "\"say_label\""})
    what = _el("text", text="[what]", props={"id": "what", "style": "\"say_dialogue\""})
    vb.children = [who, what]
    window.children = [vb]
    root.children = [window]
    s.root = root
    s.description = "Экран реплики персонажа (окно say) - имя + текст."
    return s


def tpl_choice() -> Screen:
    s = Screen(name="choice", tag="choice")
    root = _el("fixed")
    vb = _el("vbox", props={"xalign": "0.5", "yalign": "0.5", "spacing": "8"})
    loop = _el("for", loop_expr="caption in items")
    btn = _el("textbutton", text="[caption.caption]", action="caption.action",
              properties={"style": "\"choice_button\""})
    loop.children = [btn]
    vb.children = [loop]
    root.children = [vb]
    s.root = root
    s.description = "Экран пунктов меню выбора (menu) - кнопка на каждый пункт."
    return s


def tpl_nvl() -> Screen:
    s = Screen(name="nvl", tag="nvl")
    root = _el("fixed")
    window = _el("window", props={"id": "nvl_window", "style": "\"nvl_window\""})
    core = _el("vbox", props={"id": "nvl_core"})
    loop = _el("for", loop_expr="d in dialogue")
    who = _el("text", text="[d.who]", properties={"style": "\"nvl_label\""})
    what = _el("text", text="[d.what]", properties={"style": "\"nvl_dialogue\""})
    loop.children = [who, what]
    menu_use = _el("use", use_target="nvl_menu(items)")
    core.children = [loop, menu_use]
    window.children = [core]
    root.children = [window]
    s.root = root
    s.description = "NVL-режим (роман-стиль) - история реплик в одном окне."
    return s


def tpl_quick_menu() -> Screen:
    s = Screen(name="quick_menu", tag="")
    root = _el("fixed")
    hb = _el("hbox", props={"xalign": "0.98", "yalign": "0.98", "spacing": "6"})
    hb.children = [
        _el("textbutton", text="Назад", action="Rollback()"),
        _el("textbutton", text="Автопрогон", action="Preference(\"auto-forward\", \"toggle\")"),
        _el("textbutton", text="Пропуск", action="Preference(\"skip\", \"toggle\")"),
        _el("textbutton", text="Сохранить", action="ShowMenu(\"save\")"),
        _el("textbutton", text="Меню", action="ShowMenu(\"save\")"),
    ]
    root.children = [hb]
    s.root = root
    s.description = "Быстрое меню поверх реплик (rollback/auto/skip/save)."
    return s


def tpl_navigation() -> Screen:
    s = Screen(name="navigation", tag="")
    root = _el("vbox")
    root.children = [
        _el("textbutton", text="Начать игру", action="Start()"),
        _el("textbutton", text="Загрузить", action="ShowMenu(\"load\")"),
        _el("textbutton", text="Сохранить", action="ShowMenu(\"save\")"),
        _el("textbutton", text="Настройки", action="ShowMenu(\"preferences\")"),
        _el("textbutton", text="О игре", action="ShowMenu(\"about\")"),
        _el("textbutton", text="Выход в главное меню", action="MainMenu()"),
        _el("textbutton", text="Выход", action="Quit(confirm=False)"),
    ]
    s.root = root
    s.description = "Общая навигация, вставляемая через `use navigation` в меню игры."
    return s


def tpl_confirm() -> Screen:
    s = Screen(name="confirm", tag="", parameters="(message, yes_action, no_action)")
    root = _el("fixed")
    frame = _el("frame", props={"xalign": "0.5", "yalign": "0.5"})
    vb = _el("vbox", props={"spacing": "12"})
    msg = _el("text", text="[message!t]")
    hb = _el("hbox", props={"spacing": "20", "xalign": "0.5"})
    yes = _el("textbutton", text="Да", action="yes_action")
    no = _el("textbutton", text="Нет", action="no_action")
    hb.children = [yes, no]
    vb.children = [msg, hb]
    frame.children = [vb]
    root.children = [frame]
    s.root = root
    s.description = "Диалог подтверждения (выход из игры, перезапись сохранения...)."
    return s


def tpl_notify() -> Screen:
    s = Screen(name="notify", tag="notify", zorder="100")
    root = _el("fixed")
    frame = _el("frame", props={"style": "\"notify_frame\"", "yalign": "0.05", "xalign": "0.5"})
    txt = _el("text", text="[message!t]", properties={"style": "\"notify_text\""})
    frame.children = [txt]
    root.children = [frame]
    s.root = root
    s.description = "Всплывающее уведомление в углу экрана."
    return s


def tpl_hud() -> Screen:
    s = Screen(name="hud", tag="hud")
    root = _el("fixed")
    vb = _el("vbox", props={"xalign": "0.02", "yalign": "0.02", "spacing": "4"})
    bar_hp = _el("bar", props={"value": "VariableValue(\"hp\", 100)"})
    bar_mp = _el("bar", props={"value": "VariableValue(\"mp\", 100)"})
    vb.children = [bar_hp, bar_mp]
    root.children = [vb]
    s.root = root
    s.description = "Простой HUD с полосками характеристик персонажа."
    return s


TEMPLATES = {
    "main_menu": ("Главное меню", tpl_main_menu),
    "say": ("Окно реплики (say)", tpl_say),
    "choice": ("Меню выбора (choice)", tpl_choice),
    "nvl": ("NVL-режим", tpl_nvl),
    "quick_menu": ("Быстрое меню", tpl_quick_menu),
    "navigation": ("Навигация игрового меню", tpl_navigation),
    "confirm": ("Подтверждение", tpl_confirm),
    "notify": ("Уведомление", tpl_notify),
    "hud": ("HUD", tpl_hud),
}


def create_from_template(key: str) -> Screen:
    if key not in TEMPLATES:
        raise KeyError(key)
    return TEMPLATES[key][1]()


def blank_screen(name: str = "new_screen") -> Screen:
    s = Screen(name=name)
    s.description = "Пустой экран."
    return s
