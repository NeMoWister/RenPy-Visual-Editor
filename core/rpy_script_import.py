                       
"""
Импорт .rpy-сценария обратно в набор SceneNode - обратная операция к
code_generator.py.

Поддерживаемые конструкции:
  label name:
  scene bg_var [at позиция] [with переход]   (в т.ч. с переходом на ОТДЕЛЬНОЙ
                                                следующей строке)
  show var [at позиция] [with переход]       - фон/CG/спрайт; позиция -
      именованная (left/cleft/center/cright/right/fleft/fright/centre) или
      ATL-блок xalign/yalign/zoom
  hide tag [with переход]
  window show|hide [with переход]
  with переход                                - самостоятельный эффект на
                                                 весь экран (не привязан к
                                                 show/scene/hide)
  play music/sound/ambience var [fadein N] [fadeout N] [loop]
  stop music/ambience [fadeout N]
  Var "текст" / "текст"                       - диалог / нарратор
  menu: / "вариант": / jump / call
  pause [N] / pause(N) / $ renpy.pause(N)
  return
  # комментарий
  $ python_code / python: блок

ВАЖНО про многострочный "with": в реальных проектах переход почти всегда
пишут на следующей строке отдельно от scene/show/hide/window:
    scene bg forest
    with dissolve
а несколько подряд идущих show без своего "with" могут разделять один
"with" на всех:
    show a at left
    show b at right
    with dissolve
Парсер копит такие узлы в очередь ("ожидающие перехода") и применяет
переход к ним всем, когда встречает одиночную строку "with X". Если
очередь пуста - это самостоятельная инструкция with (WITH_TRANSITION).

Всё непознанное (условия if/elif, кастомные ATL-анимации с linear/ease и
т.п., произвольные вызовы) складывается в RAW-узел ДОСЛОВНО - текст
сохраняется с относительным отступом внутри себя, на экспорте просто
переносится обратно как есть, без оборачивания в "$ "/"python:".
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from core.models import (
    SceneNode, NodeType, Scene, SpritePosition, NAMED_SPRITE_POSITIONS
)

                                                                              


def _strip_trailing_comment(line: str) -> str:
    """Убирает строчный комментарий вне кавычек (комментарий ВНУТРИ строки,
    после какого-то кода - не строки, целиком состоящие из комментария,
    те обрабатываются отдельно, см. _tokenize)."""
    in_q = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_q = not in_q
        elif ch == '#' and not in_q:
            return line[:i].rstrip()
    return line


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        q = s[0]
        return s[1:-1].replace('\\' + q, q)
    return s


_TRANSITION_RE = re.compile(r'\bwith\s+(\w+)\s*$')
_AT_RE = re.compile(r'\bat\s+(\w+)\s*$')
_FADE_RE = re.compile(r'fadein\s+([\d.]+)')
_FADEOUT_RE = re.compile(r'fadeout\s+([\d.]+)')
_STANDALONE_WITH_RE = re.compile(r'^with\s+(\w+)\s*$')
_ATL_LINE_RE = re.compile(r'^(xalign|yalign|zoom)\s+([\d.]+)\s*$')

                                                                           
                                                   
_PENDING_TRANSITION_TYPES = {
    NodeType.SCENE, NodeType.SHOW_BG, NodeType.SHOW_CG,
    NodeType.SHOW_SPRITE, NodeType.HIDE_SPRITE, NodeType.WINDOW,
}


def _parse_with(tail: str) -> Tuple[str, str]:
    """Возвращает (tail_без_with, transition_name) - для INLINE 'with X' на
    той же строке, что и сама команда."""
    m = _TRANSITION_RE.search(tail)
    if m:
        return tail[:m.start()].strip(), m.group(1)
    return tail.strip(), ""


def _parse_at(tail: str) -> Tuple[str, Optional[SpritePosition]]:
    """Возвращает (tail_без_at, SpritePosition|None) - для INLINE 'at имя'.
    Распознаёт только однословные имена позиций (left/cleft/center/...).
    Если 'at' есть, но имя не из известного набора - позиция всё равно
    считается заданной (центр по умолчанию), а кусок 'at X' убирается из
    хвоста, чтобы не испортить имя переменной спрайта."""
    m = _AT_RE.search(tail)
    if not m:
        return tail, None
    name = m.group(1).lower()
    pos = NAMED_SPRITE_POSITIONS.get(name, SpritePosition(0.5, 1.0))
    return tail[:m.start()].strip(), pos


                                                                               


@dataclass
class LineToken:
    raw: str
    stripped: str                                                     
    indent: int
    lineno: int
    is_comment: bool = False                                       


def _tokenize(text: str) -> List[LineToken]:
    tokens = []
    for i, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        lstripped = raw.lstrip()
        if lstripped.startswith('#'):
                                                                      
                                    
            tokens.append(LineToken(raw, lstripped.rstrip(), indent, i, is_comment=True))
            continue
        stripped = _strip_trailing_comment(raw).strip()
        if stripped:
            tokens.append(LineToken(raw, stripped, indent, i))
    return tokens


def _dedent_block(tokens: List[LineToken], start: int, end: int, base_indent: int) -> List[str]:
    """Возвращает исходные строки tokens[start:end] с вычтенным base_indent
    символов отступа (если он есть у строки) - относительная вложенность
    внутри блока сохраняется, поэтому при повторном добавлении текущего
    pad на экспорте получается корректный результат без накопления
    лишних отступов."""
    lines = []
    for tok in tokens[start:end]:
        raw = tok.raw.rstrip('\n')
        if len(raw) >= base_indent and raw[:base_indent].strip() == '':
            lines.append(raw[base_indent:])
        else:
            lines.append(raw.strip())
    return lines


                                                                               


@dataclass
class ScriptImportReport:
    scenes: List[Scene] = field(default_factory=list)
    unrecognized: List[Tuple[int, str]] = field(default_factory=list)                  
                                                                      
                                                                           
                                                            
    needs_resource: List[Tuple[int, str, str]] = field(default_factory=list)
    total_nodes: int = 0
    total_lines: int = 0

    @property
    def recognized_pct(self) -> float:
        if not self.total_nodes:
            return 100.0
        raw_nodes = sum(
            1 for sc in self.scenes
            for n in sc.nodes
            if n.node_type == NodeType.RAW
        )
        return 100.0 * (self.total_nodes - raw_nodes) / self.total_nodes


                                                                              


class RpyScriptParser:
    def __init__(self, rm=None):
        """rm - ResourceManager (необязательно): нужен для различения
        фонов/CG/спрайтов по var_name (иначе show foo → bg_var = foo)."""
        self.rm = rm
        self._bg_vars: set = set()
        self._cg_vars: set = set()
        self._sprite_vars: set = set()
        if rm:
            self._bg_vars = {e.var_name for e in rm.get('bg')}
            self._cg_vars = {e.var_name for e in rm.get('cg')}
            self._sprite_vars = {e.var_name for e in rm.get('sprites')}
            if rm.composite_sprites:
                for cs in rm.composite_sprites:
                    self._sprite_vars.add(cs.character)

    def parse(self, text: str, source_name: str = "") -> ScriptImportReport:
        report = ScriptImportReport()
        self._tokens = _tokenize(text)
        report.total_lines = len(self._tokens)
        self._report = report

        default_scene = Scene(name=source_name or "Импорт")
        report.scenes.append(default_scene)
        self._current_scene = default_scene
                                                                          
        self._pending: List[SceneNode] = []

        i = 0
        n = len(self._tokens)
        while i < n:
            i = self._parse_one(i)

        report.scenes = [sc for sc in report.scenes if sc.nodes]
        report.total_nodes = sum(len(sc.nodes) for sc in report.scenes)
        return report

                                                                          

    def _parse_one(self, i: int) -> int:
        tokens = self._tokens
        tok = tokens[i]
        s = tok.stripped

        if tok.is_comment:
            self._flush_pending()
            text_c = s.lstrip('#').strip()
            self._add(SceneNode(node_type=NodeType.COMMENT, comment_text=text_c))
            return i + 1

                                                                         
        m = re.match(r'^label\s+(\w+)\s*:', s)
        if m:
            self._flush_pending()
            lname = m.group(1)
            if self._current_scene.nodes:
                new_scene = Scene(name=lname)
                self._report.scenes.append(new_scene)
                self._current_scene = new_scene
            else:
                self._current_scene.name = lname
            self._add(SceneNode(node_type=NodeType.LABEL, label_name=lname))
            return i + 1

                                                                         
        if s == 'nvl clear':
            self._flush_pending()
            self._add(SceneNode(node_type=NodeType.NVL_MODE, nvl_action='clear'))
            return i + 1

                                                                         
        if s == 'return':
            self._flush_pending()
            self._add(SceneNode(node_type=NodeType.RETURN))
            return i + 1

                                                                           
        m = re.match(r'^pause(?:\s+([\d.]+))?\s*$', s)
        if not m:
            m = re.match(r'^pause\s*\(\s*([\d.]+)?\s*\)\s*$', s)
        if m:
            self._flush_pending()
            dur = float(m.group(1)) if m.group(1) else 0.0
            self._add(SceneNode(node_type=NodeType.PAUSE, pause_duration=dur))
            return i + 1

                                                                         
        m = re.match(r'^(jump|call)\s+(\w+)\s*$', s)
        if m:
            self._flush_pending()
            kw, target = m.group(1), m.group(2)
            self._add(SceneNode(node_type=NodeType.JUMP, jump_target=target, python_code=kw))
            return i + 1

                                                                        
        m = re.match(r'^window\s+(show|hide)\s*(.*)$', s)
        if m:
            action, tail = m.group(1), m.group(2)
            tail, trans = _parse_with(tail)
            node = SceneNode(node_type=NodeType.WINDOW, window_action=action, transition=trans)
            self._add(node)
            if not trans:
                self._pending.append(node)
            else:
                self._pending.clear()
            return i + 1

                                                                        
        m = _STANDALONE_WITH_RE.match(s)
        if m:
            trans = m.group(1)
            if self._pending:
                for pn in self._pending:
                    pn.transition = trans
                self._pending.clear()
            else:
                self._add(SceneNode(node_type=NodeType.WITH_TRANSITION, transition=trans))
            return i + 1

                                                                          
        m = re.match(r'^stop\s+(music|ambience)\s*(.*)', s)
        if m:
            self._flush_pending()
            channel, tail = m.group(1), m.group(2)
            fo_m = _FADEOUT_RE.search(tail)
            fo = float(fo_m.group(1)) if fo_m else 0
            if channel == 'music':
                self._add(SceneNode(node_type=NodeType.STOP_MUSIC, music_fadeout=fo))
            else:
                self._add(SceneNode(node_type=NodeType.STOP_AMBIENCE, ambience_fadeout=fo))
            return i + 1

                                                                          
        m = re.match(r'^play\s+(music|sound|ambience)\s+(.+)', s)
        if m:
            self._flush_pending()
            channel, tail = m.group(1), m.group(2)
            fi_m = _FADE_RE.search(tail)
            fo_m = _FADEOUT_RE.search(tail)
            var = re.split(r'\s+(fadein|fadeout|noloop|loop)\b', tail)[0].strip()
            if channel == 'music':
                self._add(SceneNode(
                    node_type=NodeType.PLAY_MUSIC, music_var=var,
                    music_fadein=float(fi_m.group(1)) if fi_m else 0,
                    music_fadeout=float(fo_m.group(1)) if fo_m else 0,
                    audio_loop='loop' in tail and 'noloop' not in tail,
                ))
            elif channel == 'ambience':
                self._add(SceneNode(
                    node_type=NodeType.PLAY_AMBIENCE, ambience_var=var,
                    ambience_fadein=float(fi_m.group(1)) if fi_m else 0,
                    ambience_fadeout=float(fo_m.group(1)) if fo_m else 0,
                ))
            else:
                self._add(SceneNode(node_type=NodeType.PLAY_SOUND, sound_var=var))
            return i + 1

                                                                         
        m = re.match(r'^\$\s*(.*)', s)
        if m:
            code = m.group(1).rstrip()
            pm = re.match(r'^renpy\.pause\(\s*([\d.]+)?\s*\)\s*$', code)
            nvl_m = re.match(r'^set_mode_(nvl|adv)\(\s*\)\s*$', code)
            self._flush_pending()
            if pm:
                dur = float(pm.group(1)) if pm.group(1) else 0.0
                self._add(SceneNode(node_type=NodeType.PAUSE, pause_duration=dur))
            elif nvl_m:
                action = 'enter' if nvl_m.group(1) == 'nvl' else 'exit'
                self._add(SceneNode(node_type=NodeType.NVL_MODE, nvl_action=action))
            else:
                self._add(SceneNode(node_type=NodeType.PYTHON, python_code=code))
            return i + 1

                                                                          
        if s == 'python:':
            self._flush_pending()
            end = self._block_end(i + 1, tok.indent)
            lines = _dedent_block(self._tokens, i + 1, end, tok.indent + 4)
            self._add(SceneNode(node_type=NodeType.PYTHON, python_code='\n'.join(lines)))
            return end

                                                                         
        m = re.match(r'^scene\s+(.*)', s)
        if m:
            return self._parse_scene_or_show(i, NodeType.SCENE, m.group(1).strip())
        m = re.match(r'^show\s+(.*)', s)
        if m:
            return self._parse_scene_or_show(i, None, m.group(1).strip())

                                                                         
        m = re.match(r'^hide\s+(.*)', s)
        if m:
            tail = m.group(1).strip()
            tail, trans = _parse_with(tail)
            node = SceneNode(node_type=NodeType.HIDE_SPRITE, sprite_tag=tail.strip(), transition=trans)
            self._add(node)
            if not trans:
                self._pending.append(node)
            else:
                self._pending.clear()
            return i + 1

                                                                        
        if s == 'menu:' or re.match(r'^menu\s*:', s):
            self._flush_pending()
            return self._parse_menu(i + 1, tok.indent)

                                                                       
        node = self._try_parse_dialogue(s)
        if node is not None:
            self._flush_pending()
            self._add(node)
            return i + 1

                                                                          
        self._flush_pending()
        end = self._block_end(i + 1, tok.indent)
        lines = _dedent_block(self._tokens, i, end, tok.indent)
        self._report.unrecognized.append((tok.lineno, s))
        self._add(SceneNode(node_type=NodeType.RAW, python_code='\n'.join(lines)))
        return end

                                                                          

    def _add(self, node: SceneNode):
        self._current_scene.nodes.append(node)

    def _flush_pending(self):
        self._pending.clear()

    def _block_end(self, i: int, base_indent: int) -> int:
        """Индекс первого токена с indent <= base_indent, начиная с i -
        конец тела блока, начавшегося на отступе base_indent."""
        tokens = self._tokens
        while i < len(tokens) and tokens[i].indent > base_indent:
            i += 1
        return i

    def _parse_scene_or_show(self, i: int, forced_type: Optional[NodeType], tail: str) -> int:
        tokens = self._tokens
        tok = tokens[i]
        tok_idx = i                                               

        has_colon = tail.endswith(':')
        if has_colon:
            tail = tail[:-1].rstrip()

        tail, trans = _parse_with(tail)
        tail, pos = _parse_at(tail)
        var = tail.strip()

        block_start = i + 1
        block_end = block_start
        if has_colon and block_start < len(tokens) and tokens[block_start].indent > tok.indent:
            block_end = self._block_end(block_start, tok.indent)

        block_tokens = tokens[block_start:block_end]
        is_simple_atl = all(_ATL_LINE_RE.match(t.stripped) for t in block_tokens) if block_tokens else True

        end_index = block_end
        trailing_with_consumed = False
                                                                         
                                                                   
                                                                        
                                                                     
                                                                      
                                                                        
                            
        if has_colon and end_index < len(tokens) and tokens[end_index].indent == tok.indent:
            wm = _STANDALONE_WITH_RE.match(tokens[end_index].stripped)
            if wm:
                if not trans:
                    trans = wm.group(1)
                end_index += 1
                trailing_with_consumed = True

        if has_colon and not is_simple_atl:
            lines = _dedent_block(tokens, i, end_index, tok.indent)
            self._report.unrecognized.append((tok.lineno, tok.stripped))
            self._add(SceneNode(node_type=NodeType.RAW, python_code='\n'.join(lines)))
            return end_index

        for bt in block_tokens:
            am = _ATL_LINE_RE.match(bt.stripped)
            if am:
                pos = pos or SpritePosition(0.5, 1.0)
                val = float(am.group(2))
                if am.group(1) == 'xalign':
                    pos.xalign = val
                elif am.group(1) == 'yalign':
                    pos.yalign = val
                else:
                    pos.zoom = val

        node_type = forced_type
        unresolved_var = False
        if node_type is None:
            if var in self._bg_vars:
                node_type = NodeType.SHOW_BG
            elif var in self._cg_vars:
                node_type = NodeType.SHOW_CG
            elif var in self._sprite_vars:
                node_type = NodeType.SHOW_SPRITE
            elif var.startswith('bg ') or var.startswith('cg '):
                node_type = NodeType.SHOW_BG if var.split()[0] == 'bg' else NodeType.SHOW_CG
            else:
                                                                       
                                                                               
                                                                               
                controlling_word = var.split()[0] if var.split() else ""
                has_matching_sprite = controlling_word and any(
                    sv == controlling_word or sv.startswith(controlling_word + " ")
                    for sv in self._sprite_vars
                )
                if has_matching_sprite or (pos is not None and not has_colon):
                                                                         
                    node_type = NodeType.SHOW_SPRITE
                elif not has_colon:
                                                                               
                                                                             
                                                                              
                                                                              
                                                                        
                    node_type = NodeType.SHOW_SPRITE
                    unresolved_var = True
                else:
                                                                       
                                                                       
                    node_type = None                             

        if node_type is None:
                                                                         
            lines = _dedent_block(tokens, tok_idx, end_index, tok.indent)
            self._report.unrecognized.append((tok.lineno, tok.stripped))
            self._add(SceneNode(node_type=NodeType.RAW, python_code='\n'.join(lines)))
            return end_index
        elif node_type in (NodeType.SCENE, NodeType.SHOW_BG, NodeType.SHOW_CG):
            kwargs = {"bg_var": var} if node_type != NodeType.SHOW_CG else {"cg_var": var}
            node = SceneNode(node_type=node_type, transition=trans, **kwargs)
        else:
            node = SceneNode(
                node_type=NodeType.SHOW_SPRITE, sprite_var=var, transition=trans,
                sprite_position=pos or SpritePosition(0.5, 1.0),
            )
        if unresolved_var:
            node.import_warning = (
                f"Ресурс «{var}» не найден в менеджере ресурсов - добавьте файл "
                f"и пересканируйте ресурсы, либо поправьте ссылку вручную."
            )
            self._report.needs_resource.append((tok.lineno, tok.stripped, var))

        self._add(node)
        if not trailing_with_consumed and not trans:
            self._pending.append(node)
        elif not trailing_with_consumed:
            self._pending.clear()
        return end_index

    def _parse_menu(self, i: int, parent_indent: int) -> int:
        tokens = self._tokens
        node = SceneNode(node_type=NodeType.MENU)
        choices = []
        prompt_set = False

        while i < len(tokens) and tokens[i].indent > parent_indent:
            tok = tokens[i]
            s = tok.stripped

                                                                   
            if s.startswith('"') and s.endswith('"') and not prompt_set:
                is_prompt = i + 1 < len(tokens) and tokens[i + 1].stripped.startswith('"')
                if is_prompt:
                    node.menu_prompt = _unquote(s)
                    prompt_set = True
                    i += 1
                    continue

            m = re.match(r'^"(.*)":\s*$', s)
            if m:
                choice_text = m.group(1).replace('\\"', '"')
                choice_indent = tok.indent

                body_start = i + 1
                i += 1
                while i < len(tokens) and tokens[i].indent > choice_indent:
                    i += 1
                body_end = i

                stripped_body = [t for t in tokens[body_start:body_end] if t.stripped]

                jump_target = ""
                use_call = False
                branch_nodes: List[SceneNode] = []

                if len(stripped_body) == 1:
                    jm = re.match(r'^(jump|call)\s+(\w+)\s*$', stripped_body[0].stripped)
                    if jm:
                        use_call = jm.group(1) == 'call'
                        jump_target = jm.group(2)

                if not jump_target and stripped_body:
                                                                               
                                                                            
                                                                     
                    branch_nodes = self._parse_choice_body(body_start, body_end)

                choices.append({
                    "text": choice_text, "jump": jump_target, "use_call": use_call,
                    "raw_body": "", "nodes": branch_nodes,
                })
                continue

            i += 1

        node.menu_choices = choices
        self._add(node)
        return i

    def _parse_choice_body(self, start: int, end: int) -> List[SceneNode]:
        """Парсит диапазон токенов [start, end) - тело варианта меню - тем же
        построчным диспетчером (_parse_one), что и основной сценарий, отдавая
        настоящий список нод вместо сырого текста. Временно подменяет
        "текущую сцену" на изолированный контейнер и восстанавливает её
        после разбора, даже если внутри тела попался неожиданный label."""
        branch_scene = Scene(name="__menu_branch__", nodes=[])
        prev_scene = self._current_scene
        prev_pending = self._pending
        self._current_scene = branch_scene
        self._pending = []
        try:
            i = start
            while i < end:
                i = self._parse_one(i)
        finally:
            self._current_scene = prev_scene
            self._pending = prev_pending
        return branch_scene.nodes

    def _try_parse_dialogue(self, s: str) -> Optional[SceneNode]:
        if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
            return SceneNode(node_type=NodeType.NARRATION, text=_unquote(s))
        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s+(["\'])(.*)\2$', s)
        if m:
            var, q, text = m.group(1), m.group(2), m.group(3).replace('\\' + m.group(2), m.group(2))
            return SceneNode(node_type=NodeType.DIALOGUE, character_var=var, text=text)
        return None


def parse_script(text: str, source_name: str = "", rm=None) -> ScriptImportReport:
    return RpyScriptParser(rm=rm).parse(text, source_name)
