

import re 
import os 
import bisect 
from collections import Counter 
from dataclasses import dataclass ,field 
from typing import List ,Optional 

POSITIONS =("far","close","normal")





_HEADER_RE =re .compile (
r'^[ \t]*image[ \t]+([a-zA-Z0-9_]+(?:[ \t]+[a-zA-Z0-9_]+)*)[ \t]*=[ \t]*',
re .MULTILINE ,
)
_COMPOSITE_START_RE =re .compile (r'im\.Composite\(')
_LAYER_RE =re .compile (r'\((-?\d+)\s*,\s*(-?\d+)\)\s*,\s*"([^"]+)"')
_SIZE_RE =re .compile (r'^\s*\((\d+)\s*,\s*(\d+)\)\s*,(.*)$',re .DOTALL )


@dataclass 
class SpriteLayerDef :
    offset_x :int 
    offset_y :int 
    rel_path :str 


@dataclass 
class CompositeSprite :
    full_name :str 
    character :str 
    variant_parts :List [str ]
    position :str 
    width :int 
    height :int 
    layers :List [SpriteLayerDef ]=field (default_factory =list )
    source_line :int =0 
    source :str ="custom"

    @property 
    def display_name (self )->str :
        return " ".join (self .variant_parts )if self .variant_parts else "(без вариации)"


def _extract_last_composite (block :str ):

    starts =[m .start ()for m in _COMPOSITE_START_RE .finditer (block )]
    if not starts :
        return None 
    start =starts [-1 ]
    open_paren =block .index ('(',start )
    depth =0 
    j =open_paren 
    while j <len (block ):
        if block [j ]=='(':
            depth +=1 
        elif block [j ]==')':
            depth -=1 
            if depth ==0 :
                break 
        j +=1 
    else :
        return None 

    inner =block [open_paren +1 :j ]
    size_m =_SIZE_RE .match (inner )
    if not size_m :
        return None 
    width ,height =int (size_m .group (1 )),int (size_m .group (2 ))
    rest =size_m .group (3 )
    layers =[(int (ox ),int (oy ),path )for ox ,oy ,path in _LAYER_RE .findall (rest )]
    if not layers :
        return None 
    return width ,height ,layers 


def _strip_sprites_prefix (path :str )->str :

    path =path .replace ('\\','/')
    if path .startswith ('sprites/'):
        return path [len ('sprites/'):]
    return path 


def parse_sprites_rpy (text :str ,source :str ="custom")->List [CompositeSprite ]:

    results :List [CompositeSprite ]=[]
    headers =list (_HEADER_RE .finditer (text ))



    newline_positions =[i for i ,ch in enumerate (text )if ch =='\n']

    for idx ,m in enumerate (headers ):
        full_name =re .sub (r'\s+',' ',m .group (1 )).strip ()
        block_start =m .end ()
        block_end =headers [idx +1 ].start ()if idx +1 <len (headers )else len (text )
        block =text [block_start :block_end ]

        extracted =_extract_last_composite (block )
        if not extracted :
            continue 
        width ,height ,raw_layers =extracted 

        words =full_name .split (' ')
        if not words :
            continue 
        character =words [0 ]
        rest_words =words [1 :]




        first_layer_path =_strip_sprites_prefix (raw_layers [0 ][2 ])
        position ="normal"
        path_parts =first_layer_path .split ('/')
        if path_parts and path_parts [0 ]in POSITIONS :
            position =path_parts [0 ]



        if rest_words and rest_words [-1 ]==position :
            variant_parts =rest_words [:-1 ]
        else :
            variant_parts =rest_words 

        line_no =bisect .bisect_right (newline_positions ,m .start ())+1 

        layers =[
        SpriteLayerDef (offset_x =ox ,offset_y =oy ,rel_path =_strip_sprites_prefix (path ))
        for ox ,oy ,path in raw_layers 
        ]

        results .append (CompositeSprite (
        full_name =full_name ,
        character =character ,
        variant_parts =variant_parts ,
        position =position ,
        width =width ,
        height =height ,
        layers =layers ,
        source_line =line_no ,
        source =source ,
        ))

    return results 


def parse_sprites_rpy_file (path :str ,source :str ="custom")->List [CompositeSprite ]:
    with open (path ,'r',encoding ='utf-8')as f :
        text =f .read ()
    return parse_sprites_rpy (text ,source =source )





























EXCEPTIONS_FILENAME ="exceptions.txt"


def parse_exceptions_file (path :str )->dict :

    result :dict ={}
    if not path or not os .path .isfile (path ):
        return result 
    try :
        with open (path ,'r',encoding ='utf-8')as f :
            lines =f .readlines ()
    except Exception :
        return result 

    for raw_line in lines :
        line =raw_line .strip ()
        if not line or line .startswith ('#'):
            continue 
        if ':'in line :
            character ,_ ,rest =line .partition (':')
        else :
            parts =line .split (None ,1 )
            if len (parts )<2 :
                continue 
            character ,rest =parts [0 ],parts [1 ]
        character =character .strip ()
        if not character :
            continue 
        words ={w .strip ()for w in re .split (r'[,\s]+',rest )if w .strip ()}
        if not words :
            continue 
        result .setdefault (character ,set ()).update (words )
    return result 


def _auto_detect_extra_words (combos :List [List [str ]])->set :

    if not combos :
        return set ()
    lengths =Counter (len (c )for c in combos )
    modal_len =lengths .most_common (1 )[0 ][0 ]
    modal_word_pool =set ()
    for c in combos :
        if len (c )==modal_len :
            modal_word_pool .update (c )
    extra =set ()
    for c in combos :
        if len (c )>modal_len :
            for w in c :
                if w not in modal_word_pool :
                    extra .add (w )
    return extra 


def get_standalone_attr_words (character :str ,combos :List [List [str ]],manual_words =None )->set :

    manual =set (manual_words or ())
    auto =_auto_detect_extra_words (combos )
    return manual |auto 
