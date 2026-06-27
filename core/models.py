from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
import uuid


class NodeType(Enum):
    DIALOGUE = "dialogue"
    NARRATION = "narration"
    SHOW_BG = "show_bg"
    SHOW_SPRITE = "show_sprite"
    HIDE_SPRITE = "hide_sprite"
    PLAY_MUSIC = "play_music"
    PLAY_SOUND = "play_sound"
    STOP_MUSIC = "stop_music"
    SHOW_CG = "show_cg"
    HIDE_CG = "hide_cg"
    LABEL = "label"
    JUMP = "jump"
    MENU = "menu"
    PYTHON = "python"
    PAUSE = "pause"
    RETURN = "return_"
    SCENE = "scene"
    COMMENT = "comment"


@dataclass
class Character:
    name: str
    variable: str
    color: str = "#ffffff"
    image_tag: Optional[str] = None

    def to_renpy(self) -> str:
        return f'define {self.variable} = Character("{self.name}", color="{self.color}")'


@dataclass
class SpritePosition:
    xalign: float = 0.5
    yalign: float = 1.0
    zoom: float = 1.0


PRESET_POSITIONS = {
    "left":         SpritePosition(0.2, 1.0),
    "center-left":  SpritePosition(0.35, 1.0),
    "center":       SpritePosition(0.5, 1.0),
    "center-right": SpritePosition(0.65, 1.0),
    "right":        SpritePosition(0.8, 1.0),
}


@dataclass
class SceneNode:
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    node_type: NodeType = NodeType.DIALOGUE
    character_var: Optional[str] = None
    text: str = ""
    bg_var: Optional[str] = None
    cg_var: Optional[str] = None
    transition: str = "dspr"
    sprite_var: Optional[str] = None
    sprite_expression: Optional[str] = None
    sprite_position: SpritePosition = field(default_factory=SpritePosition)
    sprite_tag: Optional[str] = None
    # Для HIDE_SPRITE: если выбрана не конкретная картинка, а вся папка
    # персонажа ("скрыть кого угодно из этой папки, кто сейчас на сцене"),
    # сюда пишется имя верхней папки (например "us"), а sprite_tag/hide_var
    # остаётся пустым. Конкретный активный тег этого персонажа подбирается
    # на этапе предпросмотра/генерации кода по факту того, что сейчас на сцене.
    hide_group: Optional[str] = None
    music_var: Optional[str] = None
    sound_var: Optional[str] = None
    music_fadeout: int = 0
    music_fadein: int = 0
    audio_loop: bool = False
    label_name: str = ""
    jump_target: str = ""
    pause_duration: float = 0.0
    python_code: str = ""
    menu_prompt: str = ""
    menu_choices: List[tuple] = field(default_factory=list)
    comment_text: str = ""

    def normalized_menu_choices(self):
        """Возвращает menu_choices в едином виде (text, jump, use_call), даже
        если в проекте сохранён старый формат (text, jump) без флага —
        для него use_call по умолчанию False (старое поведение: jump)."""
        result = []
        for ch in self.menu_choices:
            if isinstance(ch, dict):
                text = ch.get("text", "")
                jump = ch.get("jump", "")
                use_call = ch.get("use_call", False)
            elif len(ch) >= 3:
                text, jump, use_call = ch[0], ch[1], ch[2]
            elif len(ch) == 2:
                text, jump, use_call = ch[0], ch[1], False
            else:
                text, jump, use_call = (ch[0] if ch else ""), "", False
            result.append((text, jump, bool(use_call)))
        return result

    @property
    def xalign(self):
        return self.sprite_position.xalign

    @xalign.setter
    def xalign(self, value):
        self.sprite_position.xalign = value

    @property
    def yalign(self):
        return self.sprite_position.yalign

    @yalign.setter
    def yalign(self, value):
        self.sprite_position.yalign = value

    @property
    def zoom(self):
        return self.sprite_position.zoom

    @zoom.setter
    def zoom(self, value):
        self.sprite_position.zoom = value

    @property
    def hide_var(self):
        """Используется GUI-каруселью как 'текущий выбор' для подсветки.
        Если выбрана конкретная картинка — возвращает её var_name (sprite_tag).
        Если выбрана целая папка персонажа — возвращает None, чтобы карусель
        не пыталась подсветить файл (подсветка папки делается отдельно)."""
        return self.sprite_tag

    @hide_var.setter
    def hide_var(self, value):
        self.sprite_tag = value
        if value:
            self.hide_group = None

    @property
    def audio_var(self):
        return self.music_var if self.node_type == NodeType.PLAY_MUSIC else self.sound_var

    @audio_var.setter
    def audio_var(self, value):
        if self.node_type == NodeType.PLAY_SOUND:
            self.sound_var = value
        else:
            self.music_var = value

    @property
    def menu_question(self):
        return self.menu_prompt

    @menu_question.setter
    def menu_question(self, value):
        self.menu_prompt = value

    def preview_text(self) -> str:
        t = self.node_type
        if t == NodeType.DIALOGUE:
            char = self.character_var or "???"
            txt = self.text[:40] + ("…" if len(self.text) > 40 else "")
            return f'💬 {char}: "{txt}"'
        elif t == NodeType.NARRATION:
            txt = self.text[:50] + ("…" if len(self.text) > 50 else "")
            return f'📖 {txt}'
        elif t == NodeType.SHOW_BG:
            return f'🖼 Фон: {self.bg_var or "—"}  [{self.transition}]'
        elif t == NodeType.SCENE:
            return f'🎬 Сцена: {self.bg_var or "—"}  [{self.transition}]'
        elif t == NodeType.SHOW_SPRITE:
            expr = f" ({self.sprite_expression})" if self.sprite_expression else ""
            trans = f"  [{self.transition}]" if self.transition else "  [без перехода]"
            return f'👤 Спрайт: {self.sprite_var or "—"}{expr}{trans}'
        elif t == NodeType.HIDE_SPRITE:
            if self.hide_group:
                return f'👻 Скрыть: персонаж «{self.hide_group}» (все спрайты)'
            return f'👻 Скрыть: {self.sprite_tag or self.sprite_var or "—"}'
        elif t == NodeType.PLAY_MUSIC:
            return f'🎵 Музыка: {self.music_var or "—"}'
        elif t == NodeType.STOP_MUSIC:
            return f'🔇 Стоп музыка'
        elif t == NodeType.PLAY_SOUND:
            return f'🔊 Звук: {self.sound_var or "—"}'
        elif t == NodeType.SHOW_CG:
            return f'🖼 CG: {self.cg_var or "—"}'
        elif t == NodeType.HIDE_CG:
            return f'🗑 Скрыть CG'
        elif t == NodeType.LABEL:
            return f'🏷 Метка: {self.label_name}'
        elif t == NodeType.JUMP:
            return f'➡ Прыжок: {self.jump_target}'
        elif t == NodeType.MENU:
            return f'📋 Меню: {self.menu_prompt[:30]}'
        elif t == NodeType.PYTHON:
            code_short = self.python_code[:40].replace('\n', ' ')
            return f'🐍 Python: {code_short}'
        elif t == NodeType.PAUSE:
            dur = str(self.pause_duration) if self.pause_duration > 0 else "клик"
            return f'⏸ Пауза ({dur})'
        elif t == NodeType.RETURN:
            return '⏹ Return (выход в главное меню / возврат из call)'
        elif t == NodeType.COMMENT:
            return f'# {self.comment_text[:50]}'
        return str(t.value)


@dataclass
class Scene:
    scene_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Сцена 1"
    nodes: List[SceneNode] = field(default_factory=list)


@dataclass
class Project:
    title: str = "Мой проект"
    label_name: str = "start"
    scenes: List[Scene] = field(default_factory=list)
    characters: List[Character] = field(default_factory=list)
    resources_path: str = "resources"

    def get_character_by_var(self, var: str) -> Optional[Character]:
        for c in self.characters:
            if c.variable == var:
                return c
        return None
