
import re 
from dataclasses import dataclass 
from typing import List 

from core .models import Project ,NodeType ,SceneNode 


@dataclass 
class FindMatch :
    scene_name :str 
    node :SceneNode 
    field_label :str 
    snippet :str 


def _pattern (query :str ,case_sensitive :bool ,whole_word :bool )->re .Pattern :
    escaped =re .escape (query )
    if whole_word :
        escaped =r"\b"+escaped +r"\b"
    flags =0 if case_sensitive else re .IGNORECASE 
    return re .compile (escaped ,flags )


def _snippet (text :str ,match :re .Match ,radius :int =30 )->str :
    start =max (0 ,match .start ()-radius )
    end =min (len (text ),match .end ()+radius )
    prefix ="…"if start >0 else ""
    suffix ="…"if end <len (text )else ""
    return prefix +text [start :end ]+suffix 


def _iter_text_fields (node :SceneNode ,include_comments :bool ):

    fields =[]
    if node .node_type in (NodeType .DIALOGUE ,NodeType .NARRATION ):
        fields .append (("Реплика",node .text ))
    if node .node_type ==NodeType .MENU :
        fields .append (("Вопрос меню",node .menu_prompt ))
        for i ,choice in enumerate (node .normalized_menu_choices ()):
            fields .append ((f"Вариант меню #{i +1 }",choice [0 ]))
    if include_comments and node .node_type ==NodeType .COMMENT :
        fields .append (("Комментарий",node .comment_text ))
    return fields 


def find_matches (project :Project ,query :str ,case_sensitive :bool =False ,
whole_word :bool =False ,include_comments :bool =False )->List [FindMatch ]:
    if not project or not query :
        return []
    pattern =_pattern (query ,case_sensitive ,whole_word )
    results :List [FindMatch ]=[]
    for scene in project .scenes :
        for node in scene .nodes :
            for label ,text in _iter_text_fields (node ,include_comments ):
                if not text :
                    continue 
                m =pattern .search (text )
                if m :
                    results .append (FindMatch (scene .name ,node ,label ,_snippet (text ,m )))
    return results 


def apply_replace_all (project :Project ,query :str ,replacement :str ,case_sensitive :bool =False ,
whole_word :bool =False ,include_comments :bool =False )->int :

    if not project or not query :
        return 0 
    pattern =_pattern (query ,case_sensitive ,whole_word )
    total =0 

    for scene in project .scenes :
        for node in scene .nodes :
            if node .node_type in (NodeType .DIALOGUE ,NodeType .NARRATION ):
                new_text ,n =pattern .subn (replacement ,node .text or "")
                if n :
                    node .text =new_text 
                    total +=n 

            if node .node_type ==NodeType .MENU :
                new_prompt ,n =pattern .subn (replacement ,node .menu_prompt or "")
                if n :
                    node .menu_prompt =new_prompt 
                    total +=n 

                new_choices =[]
                for text ,jump ,use_call ,raw_body ,nodes in node .normalized_menu_choices ():
                    new_choice_text ,n2 =pattern .subn (replacement ,text or "")
                    if n2 :
                        total +=n2 
                    new_choices .append ({
                    "text":new_choice_text ,"jump":jump ,"use_call":use_call ,
                    "raw_body":raw_body ,"nodes":nodes ,
                    })
                node .menu_choices =new_choices 

            if include_comments and node .node_type ==NodeType .COMMENT :
                new_comment ,n =pattern .subn (replacement ,node .comment_text or "")
                if n :
                    node .comment_text =new_comment 
                    total +=n 

    return total 
