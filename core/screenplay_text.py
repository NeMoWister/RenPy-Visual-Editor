
import re 
from dataclasses import dataclass 
from typing import List ,Tuple ,Optional 

from core .models import Project ,NodeType 

ANCHOR_RE =re .compile (r"\{#([a-zA-Z0-9_-]+)(?::(\d+))?\}\s*$")


def _character_display (project :Project ,var :str )->str :
    if not var :
        return ""
    ch =project .get_character_by_var (var )
    return ch .name if ch else var 


def export_screenplay (project :Project )->str :
    lines :List [str ]=[]
    lines .append (f"# {project .title } - текст для вычитки")
    lines .append ("# Правьте только текст реплик. Строки в [квадратных скобках] - служебная")
    lines .append ("# информация (фон/музыка/переходы), при импорте они игнорируются.")
    lines .append ("# Хвостовые метки вида {#abcd1234} не трогайте - по ним подтягиваются правки обратно.")
    lines .append ("")

    for scene in project .scenes :
        lines .append (f"=== СЦЕНА: {scene .name } ===")
        lines .append ("")
        for node in scene .nodes :
            t =node .node_type 
            if t ==NodeType .SCENE or t ==NodeType .SHOW_BG :
                if node .bg_var :
                    lines .append (f"[фон: {node .bg_var }]")
            elif t ==NodeType .SHOW_CG :
                if node .cg_var :
                    lines .append (f"[CG: {node .cg_var }]")
            elif t ==NodeType .PLAY_MUSIC :
                if node .music_var :
                    lines .append (f"[музыка: {node .music_var }]")
            elif t ==NodeType .LABEL :
                lines .append (f"[метка: {node .label_name }]")
            elif t ==NodeType .DIALOGUE :
                char =_character_display (project ,node .character_var )or "???"
                text =(node .text or "").replace ("\n"," ")
                lines .append (f"{char }: {text }  {{#{node .node_id }}}")
            elif t ==NodeType .NARRATION :
                text =(node .text or "").replace ("\n"," ")
                lines .append (f": {text }  {{#{node .node_id }}}")
            elif t ==NodeType .MENU :
                if node .menu_prompt :
                    lines .append (f"[МЕНЮ] {node .menu_prompt }  {{#{node .node_id }}}")
                else :
                    lines .append (f"[МЕНЮ]  {{#{node .node_id }}}")
                for i ,(ct ,cj ,use_call ,raw_body ,_nodes )in enumerate (node .normalized_menu_choices ()):
                    lines .append (f"  - {ct }  {{#{node .node_id }:{i }}}")
            lines .append ("")
        lines .append ("")

    return "\n".join (lines )


@dataclass 
class ImportResult :
    updated :int =0 
    unmatched :List [str ]=None 

    def __post_init__ (self ):
        if self .unmatched is None :
            self .unmatched =[]


def _index_project (project :Project ):

    by_id ={}
    for scene in project .scenes :
        for node in scene .nodes :
            by_id [node .node_id ]=node 
    return by_id 


def parse_screenplay (text :str )->List [Tuple [str ,Optional [int ],str ]]:

    results =[]
    for raw_line in text .splitlines ():
        line =raw_line .rstrip ()
        if not line :
            continue 
        m =ANCHOR_RE .search (line )
        if not m :
            continue 
        node_id =m .group (1 )
        choice_idx =int (m .group (2 ))if m .group (2 )is not None else None 
        content =line [:m .start ()].rstrip ()

        if choice_idx is not None :
            content =re .sub (r"^\s*-\s*","",content )
        elif content .startswith (":"):
            content =content [1 :].strip ()
        elif content .startswith ("[МЕНЮ]"):
            content =content [len ("[МЕНЮ]"):].strip ()
        else :
            colon =content .find (":")
            if colon !=-1 :
                content =content [colon +1 :].strip ()
            else :
                content =content .strip ()

        results .append ((node_id ,choice_idx ,content ))
    return results 


def apply_screenplay_import (project :Project ,text :str )->ImportResult :

    result =ImportResult ()
    by_id =_index_project (project )

    for node_id ,choice_idx ,new_text in parse_screenplay (text ):
        node =by_id .get (node_id )
        if node is None :
            result .unmatched .append (node_id )
            continue 

        if choice_idx is None :
            if node .node_type ==NodeType .DIALOGUE or node .node_type ==NodeType .NARRATION :
                if node .text !=new_text :
                    node .text =new_text 
                    result .updated +=1 
            elif node .node_type ==NodeType .MENU :
                if node .menu_prompt !=new_text :
                    node .menu_prompt =new_text 
                    result .updated +=1 
        else :
            if node .node_type ==NodeType .MENU :
                choices =node .normalized_menu_choices ()
                if 0 <=choice_idx <len (choices ):
                    ct ,cj ,use_call ,raw_body ,nodes =choices [choice_idx ]
                    if ct !=new_text :
                        choices [choice_idx ]=(new_text ,cj ,use_call ,raw_body ,nodes )
                        node .menu_choices =[
                        {"text":t ,"jump":j ,"use_call":uc ,"raw_body":rb ,"nodes":nds }
                        for t ,j ,uc ,rb ,nds in choices 
                        ]
                        result .updated +=1 

    return result 
