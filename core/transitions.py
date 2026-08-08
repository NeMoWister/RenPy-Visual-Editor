                       
"""
Переходы Ren'Py (то, что стоит после "with") - разбор строки перехода
(будь то короткое имя вроде "dissolve" или полное выражение вроде
ImageDissolve("images/mask.jpg", 1.0, ramp=8)) в структурированный
TransitionSpec, который затем "честно" проигрывается в предпросмотре и
презентации (см. ui/transition_compositor.py), плюс обратная сборка спека в
текст Ren'Py-выражения для кодогенерации.

node.transition как хранился простой строкой, так и остаётся - никаких
изменений модели/кодогенерации не требуется: строка теперь может быть либо
голым именем (ищется в BUILTIN_TRANSITIONS), либо произвольным вызовом
конструктора перехода - Ren'Py одинаково понимает оба варианта после "with".
"""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class TransitionKind(Enum):
    NONE = "none"                                                   
    DISSOLVE = "dissolve"
    FADE = "fade"
    PIXELLATE = "pixellate"
    IMAGE_DISSOLVE = "image_dissolve"
    WIPE = "wipe"                          
    PUSH = "push"
    PUNCH = "punch"                                        


DIRECTIONS = ["left", "right", "up", "down"]


@dataclass
class TransitionSpec:
    kind: TransitionKind = TransitionKind.DISSOLVE
    duration: float = 0.5                                                 
    fade_out: float = 0.5
    fade_hold: float = 0.0
    fade_in: float = 0.5
    fade_color: str = "#000000"
    pixellate_steps: int = 5
    mask_path: str = ""                                                    
    ramp: int = 8
    direction: str = "left"
    punch_amount: int = 15
    punch_axis: str = "h"                        
    raw_expr: str = ""                                                                    

    @property
    def total_duration(self) -> float:
        if self.kind == TransitionKind.FADE:
            return max(0.01, self.fade_out + self.fade_hold + self.fade_in)
        if self.kind == TransitionKind.PUNCH:
            return 0.4                                                       
        return max(0.01, self.duration)


                                                                              
                                                            
                                                                              

def _dissolve(duration: float) -> TransitionSpec:
    return TransitionSpec(kind=TransitionKind.DISSOLVE, duration=duration)


def _fade(out_t: float, hold: float, in_t: float, color: str = "#000000") -> TransitionSpec:
    return TransitionSpec(kind=TransitionKind.FADE, fade_out=out_t, fade_hold=hold,
                           fade_in=in_t, fade_color=color)


def _pixellate(duration: float, steps: int) -> TransitionSpec:
    return TransitionSpec(kind=TransitionKind.PIXELLATE, duration=duration, pixellate_steps=steps)


def _wipe(duration: float, direction: str) -> TransitionSpec:
    return TransitionSpec(kind=TransitionKind.WIPE, duration=duration, direction=direction)


def _push(duration: float, direction: str) -> TransitionSpec:
    return TransitionSpec(kind=TransitionKind.PUSH, duration=duration, direction=direction)


def _punch(axis: str) -> TransitionSpec:
    return TransitionSpec(kind=TransitionKind.PUNCH, punch_axis=axis)


                                                                              
                                                                          
                                                                              

BUILTIN_TRANSITIONS: Dict[str, TransitionSpec] = {
    "dissolve": _dissolve(0.5),
    "dissolve2": _dissolve(2),
    "dissolve_fast": _dissolve(0.5),
    "dissolve_long": _dissolve(3.0),
    "dspr": _dissolve(0.2),
    "dis": _dissolve(0.5),
    "hell_dissolve": _dissolve(3.0),

    "fade": _fade(0.5, 0.0, 0.5),
    "fade2": _fade(1.0, 0.0, 1.0),
    "fade3": _fade(1.5, 0.0, 1.5),
    "flash": _fade(0.25, 0.0, 0.75, color="#ffffff"),

    "pixellate": _pixellate(1.0, 5),

                                                                            
                                                                
    "blinds": TransitionSpec(kind=TransitionKind.IMAGE_DISSOLVE, duration=1.0,
                              mask_path="__builtin_blinds__", ramp=8),
    "squares": TransitionSpec(kind=TransitionKind.IMAGE_DISSOLVE, duration=1.0,
                               mask_path="__builtin_squares__", ramp=256),

    "wipeleft": _wipe(1.0, "left"),
    "wiperight": _wipe(1.0, "right"),
    "wipeup": _wipe(1.0, "up"),
    "wipedown": _wipe(1.0, "down"),
    "slideleft": _wipe(1.0, "left"),
    "slideright": _wipe(1.0, "right"),
    "slideup": _wipe(1.0, "up"),
    "slidedown": _wipe(1.0, "down"),
    "slideawayleft": _wipe(1.0, "left"),
    "slideawayright": _wipe(1.0, "right"),
    "slideawayup": _wipe(1.0, "up"),
    "slideawaydown": _wipe(1.0, "down"),
    "irisin": _wipe(1.0, "left"),
    "irisout": _wipe(1.0, "right"),

    "pushleft": _push(1.0, "left"),
    "pushright": _push(1.0, "right"),
    "pushup": _push(1.0, "up"),
    "pushdown": _push(1.0, "down"),

    "vpunch": _punch("v"),
    "hpunch": _punch("h"),
}

TRANSITION_NAMES: List[str] = sorted(BUILTIN_TRANSITIONS.keys())


                                                                              
                                        
                                                                              

_BARE_NAME_RE = re.compile(r'^[A-Za-z_]\w*$')
_CALL_RE = re.compile(r'^([A-Za-z_]\w*)\s*\((.*)\)\s*$', re.DOTALL)


def _split_args(argstr: str) -> List[str]:
    """Разбивает строку аргументов вызова по запятым верхнего уровня, не
    трогая запятые внутри (), [] или "строк"."""
    args, depth, cur, in_str, str_ch = [], 0, "", False, ""
    for ch in argstr:
        if in_str:
            cur += ch
            if ch == str_ch:
                in_str = False
            continue
        if ch in ("'", '"'):
            in_str, str_ch = True, ch
            cur += ch
        elif ch in "([":
            depth += 1
            cur += ch
        elif ch in ")]":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            args.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        args.append(cur.strip())
    return args


def _parse_kwargs(args: List[str]) -> Tuple[List[str], Dict[str, str]]:
    pos, kw = [], {}
    for a in args:
        m = re.match(r'^(\w+)\s*=\s*(.+)$', a)
        if m:
            kw[m.group(1)] = m.group(2).strip()
        else:
            pos.append(a)
    return pos, kw


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def _num(s: str, default: float = 0.0) -> float:
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def parse_transition(text: str) -> Optional[TransitionSpec]:
    """Разбирает содержимое 'with X' (уже без самого слова with) в
    TransitionSpec - либо это известное короткое имя, либо вызов одного из
    конструкторов переходов Ren'Py. None, если текст пуст или не распознан
    (в этом случае считаем переход мгновенным - как сейчас)."""
    if not text or not text.strip():
        return None
    text = text.strip()

    if _BARE_NAME_RE.match(text):
        spec = BUILTIN_TRANSITIONS.get(text)
        if spec:
            return spec
                                                                            
        return None

    m = _CALL_RE.match(text)
    if not m:
        return None
    func, argstr = m.group(1), m.group(2)
    args = _split_args(argstr)
    pos, kw = _parse_kwargs(args)

    try:
        if func == "Dissolve":
            dur = _num(pos[0]) if pos else _num(kw.get("time", "0.5"), 0.5)
            return TransitionSpec(kind=TransitionKind.DISSOLVE, duration=dur, raw_expr=text)
        if func == "Fade":
            out_t = _num(pos[0]) if len(pos) > 0 else _num(kw.get("out_time", "0.5"), 0.5)
            hold = _num(pos[1]) if len(pos) > 1 else _num(kw.get("hold_time", "0.0"), 0.0)
            in_t = _num(pos[2]) if len(pos) > 2 else _num(kw.get("in_time", "0.5"), 0.5)
            color = _unquote(kw.get("color", '"#000000"'))
            return TransitionSpec(kind=TransitionKind.FADE, fade_out=out_t, fade_hold=hold,
                                   fade_in=in_t, fade_color=color, raw_expr=text)
        if func == "Pixellate":
            dur = _num(pos[0]) if len(pos) > 0 else 1.0
            steps = int(_num(pos[1])) if len(pos) > 1 else int(_num(kw.get("steps", "5"), 5))
            return TransitionSpec(kind=TransitionKind.PIXELLATE, duration=dur,
                                   pixellate_steps=max(1, steps), raw_expr=text)
        if func == "ImageDissolve":
            mask = _unquote(pos[0]) if pos else _unquote(kw.get("image", '""'))
            dur = _num(pos[1]) if len(pos) > 1 else _num(kw.get("time", "1.0"), 1.0)
            ramp = int(_num(pos[2])) if len(pos) > 2 else int(_num(kw.get("ramp", "8"), 8))
            return TransitionSpec(kind=TransitionKind.IMAGE_DISSOLVE, duration=dur,
                                   mask_path=mask, ramp=max(1, ramp), raw_expr=text)
        if func == "CropMove":
            dur = _num(pos[0]) if pos else 1.0
            mode = _unquote(pos[1]) if len(pos) > 1 else "wipeleft"
            direction = next((d for d in DIRECTIONS if d in mode.lower()), "left")
            return TransitionSpec(kind=TransitionKind.WIPE, duration=dur,
                                   direction=direction, raw_expr=text)
        if func == "PushMove":
            dur = _num(pos[0]) if pos else 1.0
            mode = _unquote(pos[1]) if len(pos) > 1 else "pushleft"
            direction = next((d for d in DIRECTIONS if d in mode.lower()), "left")
            return TransitionSpec(kind=TransitionKind.PUSH, duration=dur,
                                   direction=direction, raw_expr=text)
    except Exception:
        return None
    return None


def spec_to_expr(spec: TransitionSpec, mask_display_path: Optional[str] = None) -> str:
    """Собирает Ren'Py-выражение перехода из TransitionSpec - используется,
    когда переход настроен через диалог (кастомный/с маской), а не выбран
    готовым именем из списка."""
    k = spec.kind
    if k == TransitionKind.DISSOLVE:
        return f"Dissolve({_fmt(spec.duration)})"
    if k == TransitionKind.FADE:
        color_kw = f', color="{spec.fade_color}"' if spec.fade_color and spec.fade_color.lower() != "#000000" else ""
        return f"Fade({_fmt(spec.fade_out)}, {_fmt(spec.fade_hold)}, {_fmt(spec.fade_in)}{color_kw})"
    if k == TransitionKind.PIXELLATE:
        return f"Pixellate({_fmt(spec.duration)}, {int(spec.pixellate_steps)})"
    if k == TransitionKind.IMAGE_DISSOLVE:
        path = mask_display_path if mask_display_path is not None else spec.mask_path
        return f'ImageDissolve("{path}", {_fmt(spec.duration)}, ramp={int(spec.ramp)})'
    if k == TransitionKind.WIPE:
        return f'CropMove({_fmt(spec.duration)}, "wipe{spec.direction}")'
    if k == TransitionKind.PUSH:
        return f'PushMove({_fmt(spec.duration)}, "push{spec.direction}")'
    if k == TransitionKind.PUNCH:
        return "vpunch" if spec.punch_axis == "v" else "hpunch"
    return "dissolve"


def _fmt(v: float) -> str:
    s = f"{v:.3f}".rstrip('0').rstrip('.')
    return s if s else "0"


def describe_kind(kind: TransitionKind) -> str:
    return {
        TransitionKind.NONE: "instant",
        TransitionKind.DISSOLVE: "Dissolve",
        TransitionKind.FADE: "Fade",
        TransitionKind.PIXELLATE: "Pixellate",
        TransitionKind.IMAGE_DISSOLVE: "ImageDissolve",
        TransitionKind.WIPE: "CropMove (wipe)",
        TransitionKind.PUSH: "PushMove",
        TransitionKind.PUNCH: "Punch (screen shake)",
    }.get(kind, str(kind))
