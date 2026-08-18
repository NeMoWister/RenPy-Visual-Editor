
from dataclasses import dataclass ,field 
from typing import Dict ,List ,Tuple 

from core .models import Project ,SceneNode ,NodeType 
from core .renpy_text_tags import strip_tags 

TOP_LONGEST_LINES =10 



CHARS_PER_SECOND_READING =1.0 /0.045 


def estimate_line_seconds (raw_text :str )->float :

    clean =strip_tags (raw_text or "")
    return min (6.0 ,max (1.2 ,len (clean )*0.045 ))


@dataclass 
class TimingStats :
    total_lines :int =0 
    total_seconds :float =0.0 
    per_character_seconds :Dict [str ,float ]=field (default_factory =dict )
    per_character_lines :Dict [str ,int ]=field (default_factory =dict )
    per_scene_seconds :Dict [str ,float ]=field (default_factory =dict )
    longest_lines :List [Tuple [str ,str ,float ]]=field (default_factory =list )
    truncated :bool =False 
    truncation_reason :str =""

    @property 
    def average_seconds_per_line (self )->float :
        return self .total_seconds /self .total_lines if self .total_lines else 0.0 


def _char_label (project :Project ,node :SceneNode )->str :
    if node .node_type ==NodeType .NARRATION or not node .character_var :
        return "(рассказчик)"
    ch =project .get_character_by_var (node .character_var )
    return ch .name if ch else node .character_var 


def _account_line (stats :TimingStats ,project :Project ,node :SceneNode ,scene_name :str ):
    secs =estimate_line_seconds (node .text )
    label =_char_label (project ,node )
    stats .total_lines +=1 
    stats .total_seconds +=secs 
    stats .per_character_seconds [label ]=stats .per_character_seconds .get (label ,0.0 )+secs 
    stats .per_character_lines [label ]=stats .per_character_lines .get (label ,0 )+1 
    stats .per_scene_seconds [scene_name ]=stats .per_scene_seconds .get (scene_name ,0.0 )+secs 
    stats .longest_lines .append ((label ,(strip_tags (node .text )or "")[:70 ],secs ))


def _walk_branch_nodes (nodes :List [SceneNode ],stats :TimingStats ,project :Project ,scene_name :str ):

    for node in nodes :
        t =node .node_type 
        if t in (NodeType .DIALOGUE ,NodeType .NARRATION ):
            _account_line (stats ,project ,node ,scene_name )
        elif t ==NodeType .PAUSE :
            stats .total_seconds +=max (0.0 ,node .pause_duration or 0.0 )
        elif t ==NodeType .MENU :
            for _text ,_jump ,_use_call ,_raw_body ,nodes_ in node .normalized_menu_choices ():
                if nodes_ :
                    _walk_branch_nodes (nodes_ ,stats ,project ,scene_name )


def estimate_timing (project :Project )->TimingStats :

    stats =TimingStats ()

    for scene in project .scenes :
        _walk_branch_nodes (scene .nodes ,stats ,project ,scene .name )

    stats .longest_lines .sort (key =lambda x :-x [2 ])
    stats .longest_lines =stats .longest_lines [:TOP_LONGEST_LINES ]
    return stats 
