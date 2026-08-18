
import re 
from dataclasses import dataclass ,field 
from typing import Dict ,List 

from core .models import Project ,NodeType 

NARRATOR_KEY ="__narrator__"
NARRATOR_LABEL ="📖 Повествование (без персонажа)"

_WORD_RE =re .compile (r"\S+")


def _strip_renpy_tags (text :str )->str :

    return re .sub (r"\{[^{}]*\}","",text or "")


@dataclass 
class CharacterStat :
    key :str 
    display_name :str 
    lines :int =0 
    words :int =0 
    chars :int =0 
    scenes :set =field (default_factory =set )


def compute_dialogue_stats (project :Project )->List [CharacterStat ]:

    if not project :
        return []

    by_var ={c .variable :c .name for c in project .characters }
    stats :Dict [str ,CharacterStat ]={}

    def _get (key :str ,display_name :str )->CharacterStat :
        if key not in stats :
            stats [key ]=CharacterStat (key =key ,display_name =display_name )
        return stats [key ]

    def walk (nodes ,scene_id :str ):
        for node in nodes :
            if node .node_type ==NodeType .DIALOGUE :
                key =node .character_var or NARRATOR_KEY 
                display =by_var .get (node .character_var ,node .character_var or "???")if node .character_var else "Безымянный (нет персонажа)"
                text =node .text or ""
            elif node .node_type ==NodeType .NARRATION :
                key =NARRATOR_KEY 
                display =NARRATOR_LABEL 
                text =node .text or ""
            elif node .node_type ==NodeType .MENU :
                for _t ,_j ,_uc ,_rb ,choice_nodes in node .normalized_menu_choices ():
                    if choice_nodes :
                        walk (choice_nodes ,scene_id )
                continue 
            else :
                continue 

            clean =_strip_renpy_tags (text )
            stat =_get (key ,display )
            stat .lines +=1 
            stat .words +=len (_WORD_RE .findall (clean ))
            stat .chars +=len (clean )
            stat .scenes .add (scene_id )

    for scene in project .scenes :
        walk (scene .nodes ,scene .scene_id )

    result =list (stats .values ())
    result .sort (key =lambda s :s .lines ,reverse =True )
    return result 


def total_lines (stats :List [CharacterStat ])->int :
    return sum (s .lines for s in stats )
