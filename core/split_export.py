
import re 
from dataclasses import dataclass ,field 
from typing import List ,Optional 

from core .models import Project ,Scene ,NodeType 
from core .code_generator import (
INDENT ,COMMENT_PREFIX ,generate_node ,_group_with_runs ,
_update_active_sprites ,_render_node_no_transition ,CustomNodeTemplateStore ,
_project_uses_nvl ,
)

SPLIT_RULES =("scene","label","count")


@dataclass 
class ExportChunk :
    filename :str 
    code :str 
    scene_names :List [str ]=field (default_factory =list )


def _safe_filename (name :str ,fallback :str )->str :
    cleaned =re .sub (r'[^a-zA-Z0-9_\-А-Яа-яЁё]+','_',(name or "").strip ())
    cleaned =cleaned .strip ('_')
    return (cleaned or fallback )[:80 ]


def _generate_group_code (project :Project ,scenes :List [Scene ],rm =None ,
custom_templates :Optional [CustomNodeTemplateStore ]=None ,
label_name :str ="",next_label_name :Optional [str ]=None ,
header_comment :str ="",skip_label_header :bool =False ,
nvl_style :str ="character")->str :
    lines =[]
    if header_comment :
        lines .append (header_comment )
        lines .append ("")
    if not skip_label_header :
        lines .append (f"label {label_name }:")
        lines .append ("")
    for scene in scenes :
        lines .append (f"{INDENT }{COMMENT_PREFIX } --- {scene .name } ---")
        active_sprites ={}
        nvl_state ={"on":False }
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
    if next_label_name :






        lines .append (f"{INDENT }jump {next_label_name }")
    else :
        lines .append (f"{INDENT }return")
    lines .append ("")
    return "\n".join (lines )


def _defines_header (project :Project ,nvl_style :str ="character")->str :
    if not project .characters :
        return ""
    lines =[f"{COMMENT_PREFIX } ===== Персонажи ====="]
    for ch in project .characters :
        lines .append (ch .to_renpy ())
    if _project_uses_nvl (project )and nvl_style =="character":
        lines .append ("")
        lines .append (f"{COMMENT_PREFIX } ===== NVL-варианты персонажей (для NVL_MODE-нод) =====")
        for ch in project .characters :
            lines .append (ch .to_renpy_nvl ())
    lines .append ("")
    return "\n".join (lines )


def _scene_starts_label (scene :Scene )->bool :
    return bool (scene .nodes )and scene .nodes [0 ].node_type ==NodeType .LABEL 


def split_project (project :Project ,rule :str ,rm =None ,
custom_templates :Optional [CustomNodeTemplateStore ]=None ,
count_per_file :int =5 ,defines_in_first_file :bool =True ,
nvl_style :str ="character")->List [ExportChunk ]:

    if rule not in SPLIT_RULES :
        raise ValueError (f"Неизвестное правило разбиения: {rule !r }")
    if not project .scenes :
        return []

    groups :List [List [Scene ]]=[]
    if rule =="scene":
        groups =[[s ]for s in project .scenes ]
    elif rule =="count":
        n =max (1 ,count_per_file )
        groups =[project .scenes [i :i +n ]for i in range (0 ,len (project .scenes ),n )]
    elif rule =="label":
        current :List [Scene ]=[]
        for scene in project .scenes :
            if _scene_starts_label (scene )and current :
                groups .append (current )
                current =[]
            current .append (scene )
        if current :
            groups .append (current )

    n_groups =len (groups )



    labels :List [str ]=[]
    for gi ,group in enumerate (groups ):
        if gi ==0 :
            labels .append (project .label_name )
        elif _scene_starts_label (group [0 ]):
            labels .append (group [0 ].nodes [0 ].label_name )
        else :
            labels .append (f"_export_part{gi +1 }")

    chunks :List [ExportChunk ]=[]
    used_names =set ()
    for gi ,group in enumerate (groups ):
        is_first =gi ==0 
        label_name =labels [gi ]
        next_label =labels [gi +1 ]if gi +1 <n_groups else None 

        header =_defines_header (project ,nvl_style =nvl_style )if (is_first and defines_in_first_file )else ""
        own_label =_scene_starts_label (group [0 ])and group [0 ].nodes [0 ].label_name ==label_name 
        code =_generate_group_code (project ,group ,rm =rm ,custom_templates =custom_templates ,
        label_name =label_name ,next_label_name =next_label ,
        header_comment =header .rstrip ("\n")if header else "",
        skip_label_header =own_label ,nvl_style =nvl_style )

        if rule =="label"and _scene_starts_label (group [0 ]):
            base_name =group [0 ].nodes [0 ].label_name 
        elif rule =="count":
            base_name =f"part_{gi +1 :02d}"
        else :
            base_name =group [0 ].name 

        fname =_safe_filename (base_name ,f"chunk_{gi +1 :02d}")+".rpy"
        final_name =fname 
        suffix =2 
        while final_name in used_names :
            final_name =f"{fname [:-4 ]}_{suffix }.rpy"
            suffix +=1 
        used_names .add (final_name )

        chunks .append (ExportChunk (filename =final_name ,code =code ,
        scene_names =[s .name for s in group ]))

    if not defines_in_first_file and project .characters :
        defines_code =_defines_header (project ,nvl_style =nvl_style )
        chunks .insert (0 ,ExportChunk (filename ="00_characters.rpy",code =defines_code ,scene_names =[]))

    return chunks 
