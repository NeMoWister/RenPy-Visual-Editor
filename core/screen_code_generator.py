
from typing import List 

from .screen_model import Screen ,ScreenDocument ,ScreenElement 

INDENT ="    "


def _prop_line (props :dict )->str :
    if not props :
        return ""
    parts =[]
    for k ,v in props .items ():
        if v is None or v =="":
            continue 
        parts .append (f"{k } {v }")
    return (" "+" ".join (parts ))if parts else ""


def _render_element (el :ScreenElement ,pad :str ,lines :List [str ])->None :
    tag =el .tag 

    if tag =="text"or tag =="label":
        text =el .text .replace ('"','\\"')
        lines .append (f'{pad }{tag } "{text }"{_prop_line (el .properties )}')
        return 

    if tag =="textbutton":
        text =el .text .replace ('"','\\"')
        action =f" action {el .action }"if el .action else ""
        header =f'{pad }textbutton "{text }"{action }{_prop_line (el .properties )}'
        if el .children :
            lines .append (header +":")
            for c in el .children :
                _render_element (c ,pad +INDENT ,lines )
        else :
            lines .append (header )
        return 

    if tag =="imagebutton":
        action =f" action {el .action }"if el .action else ""
        lines .append (f'{pad }imagebutton{action }{_prop_line (el .properties )}')
        return 

    if tag =="image":
        src =el .source or '"black"'
        lines .append (f'{pad }image {src }{_prop_line (el .properties )}')
        return 

    if tag =="add":
        src =el .source or '"black"'
        lines .append (f'{pad }add {src }{_prop_line (el .properties )}')
        return 

    if tag =="bar"or tag =="vbar":
        lines .append (f'{pad }{tag }{_prop_line (el .properties )}')
        return 

    if tag =="input":
        lines .append (f'{pad }input{_prop_line (el .properties )}')
        return 

    if tag =="null":
        lines .append (f'{pad }null{_prop_line (el .properties )}')
        return 

    if tag =="key":
        action =el .action or "Return()"
        lines .append (f'{pad }key {el .key_name or chr (34 )+"K_ESCAPE"+chr (34 )} action {action }')
        return 

    if tag =="timer":
        action =el .action or "NullAction()"
        lines .append (f'{pad }timer {el .timer_seconds or "1.0"} action {action }{_prop_line (el .properties )}')
        return 

    if tag =="mousearea":
        lines .append (f'{pad }mousearea{_prop_line (el .properties )}')
        for c in el .children :
            _render_element (c ,pad +INDENT ,lines )
        return 

    if tag =="has":
        lines .append (f'{pad }has {el .properties .get ("__what","vbox")}')
        return 

    if tag =="use":
        lines .append (f'{pad }use {el .use_target or "other_screen"}')
        return 

    if tag =="on":
        action =el .action or "NullAction()"
        lines .append (f'{pad }on {el .on_event or chr (34 )+"show"+chr (34 )} action {action }')
        return 

    if tag =="if":
        cond =el .condition or "True"
        lines .append (f'{pad }if {cond }:')
        for c in el .children :
            _render_element (c ,pad +INDENT ,lines )
        return 

    if tag =="elif":
        cond =el .condition or "True"
        lines .append (f'{pad }elif {cond }:')
        for c in el .children :
            _render_element (c ,pad +INDENT ,lines )
        return 

    if tag =="else":
        lines .append (f'{pad }else:')
        for c in el .children :
            _render_element (c ,pad +INDENT ,lines )
        return 

    if tag =="for":
        loop =el .loop_expr or "item in []"
        lines .append (f'{pad }for {loop }:')
        for c in el .children :
            _render_element (c ,pad +INDENT ,lines )
        return 

    if tag =="button":
        action =f" action {el .action }"if el .action else ""
        header =f'{pad }button{action }{_prop_line (el .properties )}'
        lines .append (header +":")
        for c in el .children :
            _render_element (c ,pad +INDENT ,lines )
        return 



    header =f"{pad }{tag }{_prop_line (el .properties )}"
    if el .children :
        lines .append (header +":")
        for c in el .children :
            _render_element (c ,pad +INDENT ,lines )
    else :
        lines .append (header )


def generate_screen (screen :Screen )->str :
    lines :List [str ]=[]
    header =f"screen {screen .name }{screen .parameters }:"
    lines .append (header )
    pad =INDENT 
    if screen .tag :
        lines .append (f'{pad }tag {screen .tag }')
    if screen .modal :
        lines .append (f'{pad }modal True')
    if screen .zorder :
        lines .append (f'{pad }zorder {screen .zorder }')
    body_start =len (lines )
    for c in screen .root .children :
        _render_element (c ,pad ,lines )
    if len (lines )==body_start and not screen .tag and not screen .modal and not screen .zorder :
        lines .append (f'{pad }pass')
    return "\n".join (lines )


def generate_document (document :ScreenDocument )->str :
    return "\n\n".join (generate_screen (s )for s in document .screens )
