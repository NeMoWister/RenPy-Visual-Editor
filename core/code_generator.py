from typing import List ,Dict ,Optional 
from .models import Project ,Scene ,SceneNode ,NodeType ,Character ,nearest_anchor_name 
from .custom_node_templates import CustomNodeTemplateStore 

INDENT ="    "
COMMENT_PREFIX ="#"




_GROUPABLE_TRANSITION_TYPES ={
NodeType .SCENE ,NodeType .SHOW_BG ,NodeType .SHOW_CG ,
NodeType .SHOW_SPRITE ,NodeType .WINDOW ,
}


def _resource_volume (var :str ,rm =None )->Optional [float ]:

    if rm is None or not var :
        return None 
    try :
        return rm .get_volume_by_var (var )
    except Exception :
        return None 


def _fmt_seconds (value )->str :

    value =round (float (value ),1 )
    if value ==int (value ):
        return str (int (value ))
    return f"{value :.1f}"


def _sprite_tag (node :SceneNode ,rm =None )->str :

    if node .sprite_tag :
        return node .sprite_tag 
    if rm is not None and node .sprite_var :
        composite =rm .find_composite_by_name (node .sprite_var )
        if composite is not None :
            return composite .character 
    return node .sprite_var or ""


def _render_atl_lines (atl_script :str ,pad :str )->List [str ]:

    lines =[]
    for line in atl_script .splitlines ():
        lines .append (f"{pad }{INDENT }{line }"if line .strip ()else "")
    return lines 


def _render_sprite_show_lines (node :SceneNode ,pad :str )->List [str ]:

    spr =node .sprite_var or ""
    if not spr :
        return []
    expr =f" {node .sprite_expression }"if node .sprite_expression else ""
    lines =[f"{pad }show {spr }{expr }:"]
    if node .atl_script and node .atl_script .strip ():
        lines .extend (_render_atl_lines (node .atl_script ,pad ))
        return lines 
    pos =node .sprite_position 
    anchor_name =nearest_anchor_name (pos .xalign )
    if pos .zoom !=1.0 :
        lines [0 ]=f"{pad }show {spr }{expr } at {anchor_name }:"
        lines .append (f"{pad }{INDENT }zoom {pos .zoom :.2f}")
    else :
        lines [0 ]=f"{pad }show {spr }{expr } at {anchor_name }"
    return lines 


def _render_sprite_group (nodes :List [SceneNode ],pad :str )->List [str ]:

    lines :List [str ]=[]
    for node in nodes :
        lines .extend (_render_sprite_show_lines (node ,pad ))
    transition =nodes [0 ].transition if nodes else ""
    if transition :
        lines .append (f"{pad }with {transition }")
    return lines 


def _render_node_no_transition (node :SceneNode ,pad :str )->List [str ]:

    t =node .node_type 
    if t ==NodeType .SHOW_SPRITE :
        return _render_sprite_show_lines (node ,pad )
    if t ==NodeType .SCENE :
        bg =node .bg_var or "black"
        if node .atl_script and node .atl_script .strip ():
            return [f"{pad }scene {bg }:"]+_render_atl_lines (node .atl_script ,pad )
        return [f"{pad }scene {bg }"]
    if t ==NodeType .SHOW_BG :
        bg =node .bg_var or "black"
        if node .atl_script and node .atl_script .strip ():
            return [f"{pad }show {bg }:"]+_render_atl_lines (node .atl_script ,pad )
        return [f"{pad }show {bg }"]
    if t ==NodeType .SHOW_CG :
        if not node .cg_var :
            return []
        if node .atl_script and node .atl_script .strip ():
            return [f"{pad }show {node .cg_var }:"]+_render_atl_lines (node .atl_script ,pad )
        return [f"{pad }show {node .cg_var }"]
    if t ==NodeType .WINDOW :
        return [f"{pad }window {node .window_action }"]
    return []


def generate_node (node :SceneNode ,indent :int =1 ,active_sprites :Optional [Dict [str ,str ]]=None ,
rm =None ,custom_templates :Optional [CustomNodeTemplateStore ]=None ,
nvl_state :Optional [Dict [str ,bool ]]=None ,nvl_style :str ="character")->List [str ]:

    pad =INDENT *indent 
    lines =[]
    t =node .node_type 

    if t ==NodeType .COMMENT :
        if node .comment_text :
            lines .append (f"{pad }{COMMENT_PREFIX } {node .comment_text }")
    elif t ==NodeType .LABEL :
        lines .append ("")
        lines .append (f"label {node .label_name }:")
    elif t ==NodeType .SCENE :
        bg =node .bg_var or "black"
        if node .atl_script and node .atl_script .strip ():
            lines .append (f"{pad }scene {bg }:")
            lines .extend (_render_atl_lines (node .atl_script ,pad ))
            if node .transition :
                lines .append (f"{pad }with {node .transition }")
        elif node .transition :
            lines .append (f"{pad }scene {bg } with {node .transition }")
        else :
            lines .append (f"{pad }scene {bg }")
    elif t ==NodeType .SHOW_BG :
        bg =node .bg_var or "black"
        if node .atl_script and node .atl_script .strip ():
            lines .append (f"{pad }show {bg }:")
            lines .extend (_render_atl_lines (node .atl_script ,pad ))
            if node .transition :
                lines .append (f"{pad }with {node .transition }")
        elif node .transition :
            lines .append (f"{pad }show {bg } with {node .transition }")
        else :
            lines .append (f"{pad }show {bg }")
    elif t ==NodeType .SHOW_CG :
        if node .cg_var :
            if node .atl_script and node .atl_script .strip ():
                lines .append (f"{pad }show {node .cg_var }:")
                lines .extend (_render_atl_lines (node .atl_script ,pad ))
                if node .transition :
                    lines .append (f"{pad }with {node .transition }")
            elif node .transition :
                lines .append (f"{pad }show {node .cg_var } with {node .transition }")
            else :
                lines .append (f"{pad }show {node .cg_var }")
    elif t ==NodeType .HIDE_CG :
        if node .cg_var :
            lines .append (f"{pad }hide {node .cg_var } with dissolve")
    elif t ==NodeType .SHOW_SPRITE :


        lines .extend (_render_sprite_group ([node ],pad ))
    elif t ==NodeType .HIDE_SPRITE :
        if node .hide_group and active_sprites is not None :

            tags =[tag for tag ,group in active_sprites .items ()if group ==node .hide_group ]
            for tag in tags :
                lines .append (f"{pad }hide {tag } with dissolve")
        else :
            tag =node .sprite_tag or node .sprite_var or ""
            if not node .sprite_tag and rm is not None and node .sprite_var :
                composite =rm .find_composite_by_name (node .sprite_var )
                if composite is not None :
                    tag =composite .character 
            if tag :
                lines .append (f"{pad }hide {tag } with dissolve")
    elif t ==NodeType .PLAY_MUSIC :
        if node .music_var :
            fadeout =f" fadeout {_fmt_seconds (node .music_fadeout )}"if node .music_fadeout else ""
            fadein =f" fadein {_fmt_seconds (node .music_fadein )}"if node .music_fadein else ""
            vol =_resource_volume (node .music_var ,rm )
            volume =f" volume {vol :.2f}"if vol is not None else ""
            lines .append (f"{pad }play music {node .music_var }{fadeout }{fadein }{volume }")
    elif t ==NodeType .STOP_MUSIC :
        fadeout =f" fadeout {_fmt_seconds (node .music_fadeout )}"if node .music_fadeout else ""
        lines .append (f"{pad }stop music{fadeout }")
    elif t ==NodeType .PLAY_AMBIENCE :
        if node .ambience_var :
            fadeout =f" fadeout {_fmt_seconds (node .ambience_fadeout )}"if node .ambience_fadeout else ""
            fadein =f" fadein {_fmt_seconds (node .ambience_fadein )}"if node .ambience_fadein else ""
            vol =_resource_volume (node .ambience_var ,rm )
            volume =f" volume {vol :.2f}"if vol is not None else ""
            lines .append (f"{pad }play ambience {node .ambience_var }{fadeout }{fadein }{volume }")
    elif t ==NodeType .STOP_AMBIENCE :
        fadeout =f" fadeout {_fmt_seconds (node .ambience_fadeout )}"if node .ambience_fadeout else ""
        lines .append (f"{pad }stop ambience{fadeout }")
    elif t ==NodeType .WINDOW :
        trans =f" with {node .transition }"if node .transition else ""
        lines .append (f"{pad }window {node .window_action }{trans }")
    elif t ==NodeType .WITH_TRANSITION :
        if node .transition :
            lines .append (f"{pad }with {node .transition }")
    elif t ==NodeType .PLAY_SOUND :
        if node .sound_var :
            vol =_resource_volume (node .sound_var ,rm )
            volume =f" volume {vol :.2f}"if vol is not None else ""
            lines .append (f"{pad }play sound {node .sound_var }{volume }")
    elif t ==NodeType .DIALOGUE :
        text =node .text .replace ('"','\\"')
        nvl_on =bool (nvl_state and nvl_state .get ("on"))
        use_character_routing =nvl_on and nvl_style =="character"
        if node .character_var :
            speaker =f"{node .character_var }_nvl"if use_character_routing else node .character_var 
            lines .append (f'{pad }{speaker } "{text }"')
        else :
            speaker ="nvl_narrator "if use_character_routing else ""
            lines .append (f'{pad }{speaker }"{text }"')
    elif t ==NodeType .NARRATION :
        text =node .text .replace ('"','\\"')
        nvl_on =bool (nvl_state and nvl_state .get ("on"))
        speaker ="nvl_narrator "if (nvl_on and nvl_style =="character")else ""
        lines .append (f'{pad }{speaker }"{text }"')
    elif t ==NodeType .NVL_MODE :
        if node .nvl_action =="enter":
            if nvl_state is not None :
                nvl_state ["on"]=True 
            if nvl_style =="function":
                lines .append (f"{pad }$ set_mode_nvl()")
            else :
                lines .append (f"{pad }nvl clear")
        elif node .nvl_action =="clear":
            lines .append (f"{pad }nvl clear")
        elif node .nvl_action =="exit":
            if nvl_state is not None :
                nvl_state ["on"]=False 
            if nvl_style =="function":
                lines .append (f"{pad }$ set_mode_adv()")
    elif t ==NodeType .PAUSE :
        if node .pause_duration >0 :
            lines .append (f"{pad }pause {node .pause_duration :.1f}")
        else :
            lines .append (f"{pad }pause")
    elif t ==NodeType .RETURN :
        lines .append (f"{pad }return")
    elif t ==NodeType .JUMP :
        if node .jump_target :
            lines .append (f"{pad }jump {node .jump_target }")
    elif t ==NodeType .MENU :
        prompt =node .menu_prompt .replace ('"','\\"')
        lines .append (f'{pad }menu:')
        if prompt :
            lines .append (f'{pad }{INDENT }"{prompt }"')
        for ct ,cj ,use_call ,raw_body ,choice_nodes in node .normalized_menu_choices ():
            ct =ct .replace ('"','\\"')
            lines .append (f'{pad }{INDENT }"{ct }":')
            if choice_nodes :






                branch_sprites =dict (active_sprites )if active_sprites is not None else {}
                branch_nvl =dict (nvl_state )if nvl_state is not None else {"on":False }
                wrote_any =False 
                for cn in choice_nodes :
                    sub_lines =generate_node (cn ,indent +2 ,active_sprites =branch_sprites ,
                    rm =rm ,custom_templates =custom_templates ,
                    nvl_state =branch_nvl ,nvl_style =nvl_style )
                    if sub_lines :
                        lines .extend (sub_lines )
                        wrote_any =True 
                    _update_active_sprites (branch_sprites ,cn ,rm =rm )
                if not wrote_any :
                    lines .append (f'{pad }{INDENT }{INDENT }pass')
            elif raw_body and raw_body .strip ():


                for bl in raw_body .splitlines ():
                    lines .append (f'{pad }{INDENT }{INDENT }{bl }'if bl .strip ()else '')
            elif cj :
                kw ="call"if use_call else "jump"
                lines .append (f'{pad }{INDENT }{INDENT }{kw } {cj }')
            else :
                lines .append (f'{pad }{INDENT }{INDENT }pass')
    elif t ==NodeType .PYTHON :
        code_lines =node .python_code .splitlines ()
        if len (code_lines )==1 :
            lines .append (f"{pad }$ {code_lines [0 ]}")
        else :
            lines .append (f"{pad }python:")
            for cl in code_lines :
                lines .append (f"{pad }{INDENT }{cl }"if cl .strip ()else "")
    elif t ==NodeType .RAW :
        for cl in node .python_code .splitlines ():
            lines .append (f"{pad }{cl }"if cl .strip ()else "")
    elif t ==NodeType .CUSTOM :
        lines .extend (_render_custom_node (node ,pad ,custom_templates ))
    return lines 


def _render_custom_node (node :SceneNode ,pad :str ,custom_templates :Optional [CustomNodeTemplateStore ])->List [str ]:

    if custom_templates is None :
        return [f"{pad }{COMMENT_PREFIX } [пользовательская нода: хранилище шаблонов недоступно]"]
    tmpl =custom_templates .get (node .custom_template_id )
    if tmpl is None :
        return [f"{pad }{COMMENT_PREFIX } [пользовательская нода: шаблон '{node .custom_template_id }' не найден]"]
    rendered =custom_templates .render (tmpl ,node .custom_params ,pad =pad )
    if rendered is None :
        return [f"{pad }{COMMENT_PREFIX } [пользовательская нода '{tmpl .name }': Jinja2 не установлен]"]
    lines =[]
    for line in rendered .splitlines ():
        lines .append (line if line .strip ()else "")
    return lines 


def _update_active_sprites (active_sprites :Dict [str ,str ],node :SceneNode ,rm =None ):

    t =node .node_type 
    if t ==NodeType .SCENE :
        active_sprites .clear ()
    elif t ==NodeType .SHOW_SPRITE and node .sprite_var :
        composite =rm .find_composite_by_name (node .sprite_var )if rm is not None else None 
        if composite is not None :
            tag =node .sprite_tag or composite .character 
            top_group =composite .character 
        else :
            tag =node .sprite_tag or node .sprite_var 
            top_group =""
            if rm is not None :
                entry =rm .find_by_var (node .sprite_var )
                if entry :
                    top_group =entry .group_parts ()[0 ]if entry .group_parts ()else ""
        active_sprites [tag ]=top_group 
    elif t ==NodeType .HIDE_SPRITE :
        if node .hide_group :
            for tag in [tg for tg ,grp in active_sprites .items ()if grp ==node .hide_group ]:
                del active_sprites [tag ]
        else :
            tag =_sprite_tag (node ,rm )
            active_sprites .pop (tag ,None )


def _group_with_runs (nodes :List [SceneNode ])->List [List [SceneNode ]]:

    units :List [List [SceneNode ]]=[]
    current :List [SceneNode ]=[]

    def is_groupable (node :SceneNode )->bool :
        if node .node_type not in _GROUPABLE_TRANSITION_TYPES :
            return False 
        if not node .transition :
            return False 
        if node .node_type ==NodeType .SHOW_SPRITE and not node .sprite_var :
            return False 
        return True 

    def flush ():
        if current :
            units .append (list (current ))
            current .clear ()

    for node in nodes :
        if is_groupable (node )and current and current [-1 ].transition ==node .transition :
            current .append (node )
        elif is_groupable (node ):
            flush ()
            current .append (node )
        else :
            flush ()
            units .append ([node ])
    flush ()
    return units 


def _project_uses_nvl (project :Project )->bool :
    def walk (nodes )->bool :
        for node in nodes :
            if node .node_type ==NodeType .NVL_MODE :
                return True 
            if node .node_type ==NodeType .MENU :
                for _t ,_j ,_uc ,_rb ,choice_nodes in node .normalized_menu_choices ():
                    if choice_nodes and walk (choice_nodes ):
                        return True 
        return False 

    return any (walk (scene .nodes )for scene in project .scenes )


def generate_full_script (project :Project ,rm =None ,custom_templates :Optional [CustomNodeTemplateStore ]=None ,
nvl_style :str ="character",include_defines :bool =True )->str :
    lines =[
    f"{COMMENT_PREFIX } Сценарий: {project .title }",
    f"{COMMENT_PREFIX } Сгенерировано RenPy Visual Editor",
    "",
    ]
    if include_defines :
        if project .characters :
            lines .append (f"{COMMENT_PREFIX } ===== Персонажи =====")
            for ch in project .characters :
                lines .append (ch .to_renpy ())
            lines .append ("")

        if rm is not None :
            from core .custom_transitions import load_custom_transitions 
            custom =load_custom_transitions (getattr (rm ,'base_dir',None ))
            if custom :
                lines .append (f"{COMMENT_PREFIX } ===== Кастомные переходы (заданы через диалог перехода) =====")
                for name ,expr in sorted (custom .items ()):
                    lines .append (f"define {name } = {expr }")
                lines .append ("")

        uses_nvl =_project_uses_nvl (project )
        if uses_nvl and project .characters and nvl_style =="character":
            lines .append (f"{COMMENT_PREFIX } ===== NVL-варианты персонажей (для NVL_MODE-нод) =====")
            for ch in project .characters :
                lines .append (ch .to_renpy_nvl ())
            lines .append ("")
        if uses_nvl and nvl_style =="function":
            lines .append (
            f"{COMMENT_PREFIX } NVL/ADV переключаются через $ set_mode_nvl() / $ set_mode_adv() -"
            )
            lines .append (f"{COMMENT_PREFIX } эти функции нужно определить самостоятельно (см. настройки редактора).")
            lines .append ("")

    lines .append (f"label {project .label_name }:")
    lines .append ("")
    nvl_state :Dict [str ,bool ]={"on":False }
    for scene in project .scenes :
        lines .append (f"{INDENT }{COMMENT_PREFIX } --- {scene .name } ---")
        active_sprites :Dict [str ,str ]={}
        for unit in _group_with_runs (scene .nodes ):
            if len (unit )>1 :
                for node in unit :
                    lines .extend (_render_node_no_transition (node ,INDENT ))
                lines .append (f"{INDENT }with {unit [0 ].transition }")
                for node in unit :
                    _update_active_sprites (active_sprites ,node ,rm =rm )
            else :
                node =unit [0 ]
                lines .extend (generate_node (node ,indent =1 ,active_sprites =active_sprites ,rm =rm ,
                custom_templates =custom_templates ,nvl_state =nvl_state ,
                nvl_style =nvl_style ))
                _update_active_sprites (active_sprites ,node ,rm =rm )
        lines .append ("")
    lines .append (f"{INDENT }return")
    lines .append ("")
    return "\n".join (lines )


def generate_defines_only (project :Project ,nvl_style :str ="character",rm =None )->str :
    lines =[f"{COMMENT_PREFIX } ===== Персонажи ====="]
    for ch in project .characters :
        lines .append (ch .to_renpy ())
    lines .append ("")

    if rm is not None :
        from core .custom_transitions import load_custom_transitions 
        custom =load_custom_transitions (getattr (rm ,'base_dir',None ))
        if custom :
            lines .append (f"{COMMENT_PREFIX } ===== Кастомные переходы (заданы через диалог перехода) =====")
            for name ,expr in sorted (custom .items ()):
                lines .append (f"define {name } = {expr }")
            lines .append ("")

    uses_nvl =_project_uses_nvl (project )
    if uses_nvl and project .characters and nvl_style =="character":
        lines .append (f"{COMMENT_PREFIX } ===== NVL-варианты персонажей (для NVL_MODE-нод) =====")
        for ch in project .characters :
            lines .append (ch .to_renpy_nvl ())
        lines .append ("")
    if uses_nvl and nvl_style =="function":
        lines .append (
        f"{COMMENT_PREFIX } NVL/ADV переключаются через $ set_mode_nvl() / $ set_mode_adv() -"
        )
        lines .append (f"{COMMENT_PREFIX } эти функции нужно определить самостоятельно (см. настройки редактора).")
        lines .append ("")
    return "\n".join (lines )
