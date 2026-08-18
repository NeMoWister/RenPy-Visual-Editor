

from dataclasses import dataclass ,field 
from typing import Optional ,List ,Dict 
from .models import Scene ,SceneNode ,NodeType ,SpritePosition 
from .composite_sprite_parser import CompositeSprite 


@dataclass 
class ActiveSprite :
    var :str 
    expression :Optional [str ]
    position :SpritePosition 
    tag :str 
    group_path :str =""
    composite :Optional [CompositeSprite ]=None 
    atl_script :str =""

    def top_group (self )->str :

        if self .composite is not None :
            return self .composite .character 
        return self .group_path .split ('/')[0 ]if self .group_path else ""


@dataclass 
class SceneState :
    bg_var :Optional [str ]=None 
    cg_var :Optional [str ]=None 
    sprites :Dict [str ,ActiveSprite ]=field (default_factory =dict )
    char_var :Optional [str ]=None 
    text :str =""
    nvl_mode :bool =False 
    bg_atl_script :str =""

    def sprite_list (self )->List [ActiveSprite ]:
        return list (self .sprites .values ())


def compute_state_up_to (scene :Scene ,node_index :int ,rm =None )->SceneState :

    state =SceneState ()
    if node_index <0 :
        return state 

    last_index =min (node_index ,len (scene .nodes )-1 )
    for i in range (last_index +1 ):
        node =scene .nodes [i ]
        _apply_node (state ,node ,is_current =(i ==last_index ),rm =rm )
    return state 


def _resolve_sprite_tag (node :SceneNode ,rm )->tuple :

    composite =rm .find_composite_by_name (node .sprite_var )if (rm is not None and node .sprite_var )else None 
    if composite is not None :
        tag =node .sprite_tag or composite .character 
        return tag ,composite 
    tag =node .sprite_tag or node .sprite_var 
    return tag ,None 


def _apply_node (state :SceneState ,node :SceneNode ,is_current :bool ,rm =None ):
    t =node .node_type 

    if t in (NodeType .SHOW_BG ,NodeType .SCENE ):
        state .bg_var =node .bg_var or None 



        state .cg_var =None 
        state .bg_atl_script =node .atl_script or ""

        if t ==NodeType .SCENE :
            state .sprites .clear ()
    elif t ==NodeType .SHOW_CG :
        state .cg_var =node .cg_var or None 
        state .bg_atl_script =node .atl_script or ""
    elif t ==NodeType .HIDE_CG :
        state .cg_var =None 
        state .bg_atl_script =""
    elif t ==NodeType .SHOW_SPRITE :
        if node .sprite_var :
            tag ,composite =_resolve_sprite_tag (node ,rm )
            group_path =""
            if composite is None and rm is not None :
                entry =rm .find_by_var (node .sprite_var )
                if entry :
                    group_path =entry .group_path 
            state .sprites [tag ]=ActiveSprite (
            var =node .sprite_var ,
            expression =node .sprite_expression ,
            position =SpritePosition (
            xalign =node .sprite_position .xalign ,
            yalign =node .sprite_position .yalign ,
            zoom =node .sprite_position .zoom ,
            ),
            tag =tag ,
            group_path =group_path ,
            composite =composite ,
            atl_script =node .atl_script or "",
            )
    elif t ==NodeType .HIDE_SPRITE :
        if node .hide_group :




            to_remove =[tag for tag ,sp in state .sprites .items ()if sp .top_group ()==node .hide_group ]
            for tag in to_remove :
                del state .sprites [tag ]
        else :
            tag ,_composite =_resolve_sprite_tag (node ,rm )
            if tag and tag in state .sprites :
                del state .sprites [tag ]
    elif t ==NodeType .NVL_MODE :
        if node .nvl_action =="enter":
            state .nvl_mode =True 
        elif node .nvl_action =="exit":
            state .nvl_mode =False 


    if is_current :
        if t ==NodeType .DIALOGUE :
            state .char_var =node .character_var or None 
            state .text =node .text 
        elif t ==NodeType .NARRATION :
            state .char_var =None 
            state .text =node .text 
        else :



            if t not in (NodeType .SHOW_BG ,NodeType .SHOW_CG ,NodeType .SCENE ,
            NodeType .SHOW_SPRITE ,NodeType .HIDE_SPRITE ,
            NodeType .HIDE_CG ):
                state .char_var =None 
                state .text =""
