
import re 
from dataclasses import dataclass ,field 
from typing import Dict ,List ,Optional 


_HEADER_RE =re .compile (
r'^([ \t]*)layeredimage[ \t]+([a-zA-Z0-9_]+(?:[ \t]+[a-zA-Z0-9_]+)*)[ \t]*:[ \t]*$',
re .MULTILINE ,
)
_GROUP_RE =re .compile (r'^group[ \t]+([a-zA-Z0-9_]+)\b(.*):[ \t]*$')
_ATTRIBUTE_RE =re .compile (r'^attribute[ \t]+([a-zA-Z0-9_]+)\b(.*?)[ \t]*:?[ \t]*$')
_PREFIX_RE =re .compile (r'prefix[ \t]+"([^"]+)"')
_STRING_RE =re .compile (r'"([^"]+)"')


@dataclass 
class LayeredAttribute :
    name :str 
    default :bool 
    rel_path :Optional [str ]=None 
    variants :List [str ]=field (default_factory =list )


@dataclass 
class LayeredGroup :
    name :str 
    prefix :str 
    attributes :List [LayeredAttribute ]=field (default_factory =list )


@dataclass 
class LayeredSprite :
    full_name :str 
    character :str 
    variant_parts :List [str ]
    groups :Dict [str ,LayeredGroup ]=field (default_factory =dict )
    source_line :int =0 
    source :str ="custom"
    from_rpy :bool =True 

    @property 
    def display_name (self )->str :
        return " ".join (self .variant_parts )if self .variant_parts else "(без вариации)"


def _indent_of (line :str )->int :
    return len (line )-len (line .lstrip (' \t'))


def _split_block (lines :List [str ],start :int ,base_indent :int )->int :

    i =start 
    while i <len (lines ):
        line =lines [i ]
        if line .strip ()and _indent_of (line )<=base_indent :
            break 
        i +=1 
    return i 


def _parse_group_body (lines :List [str ],start :int ,end :int ,group_indent :int )->List [LayeredAttribute ]:
    attrs :List [LayeredAttribute ]=[]
    i =start 

    attr_indent =None 
    while i <end :
        line =lines [i ]
        stripped =line .strip ()
        if not stripped :
            i +=1 
            continue 
        indent =_indent_of (line )
        if attr_indent is None :
            attr_indent =indent 
        if indent !=attr_indent :
            i +=1 
            continue 
        m =_ATTRIBUTE_RE .match (stripped )
        if not m :

            i +=1 
            continue 
        name =m .group (1 )
        rest =m .group (2 )
        default =bool (re .search (r'\bdefault\b',rest ))
        explicit_path =None 
        strings_on_line =_STRING_RE .findall (rest )
        if strings_on_line :
            explicit_path =strings_on_line [0 ]
        block_end =_split_block (lines ,i +1 ,indent )
        if explicit_path is None and stripped .endswith (':'):

            sub_strings =[]
            for j in range (i +1 ,block_end ):
                sub_strings .extend (_STRING_RE .findall (lines [j ]))
            if sub_strings :
                explicit_path =sub_strings [0 ]
        attrs .append (LayeredAttribute (name =name ,default =default ,rel_path =explicit_path ))
        i =block_end 
    return attrs 


def parse_layeredimage_rpy (text :str ,source :str ="custom")->List [LayeredSprite ]:
    results :List [LayeredSprite ]=[]
    lines =text .splitlines ()
    headers =list (_HEADER_RE .finditer (text ))

    for m in headers :
        full_name =re .sub (r'\s+',' ',m .group (2 )).strip ()
        base_indent =len (m .group (1 ))
        header_line_no =text .count ('\n',0 ,m .start ())
        start_line =header_line_no +1 
        end_line =_split_block (lines ,start_line ,base_indent )

        words =full_name .split (' ')
        character =words [0 ]
        variant_parts =words [1 :]

        groups :Dict [str ,LayeredGroup ]={}
        i =start_line 
        block_indent =None 
        while i <end_line :
            line =lines [i ]
            stripped =line .strip ()
            if not stripped :
                i +=1 
                continue 
            indent =_indent_of (line )
            if block_indent is None :
                block_indent =indent 
            if indent !=block_indent :


                i +=1 
                continue 

            gm =_GROUP_RE .match (stripped )
            if gm :
                group_name =gm .group (1 )
                group_rest =gm .group (2 )
                prefix_m =_PREFIX_RE .search (group_rest )
                prefix =prefix_m .group (1 )if prefix_m else group_name 
                group_end =_split_block (lines ,i +1 ,indent )
                attrs =_parse_group_body (lines ,i +1 ,group_end ,indent )


                if group_name in groups :
                    groups [group_name ].attributes .extend (attrs )
                else :
                    groups [group_name ]=LayeredGroup (name =group_name ,prefix =prefix ,attributes =attrs )
                i =group_end 
                continue 

            if stripped .endswith (':'):

                i =_split_block (lines ,i +1 ,indent )
                continue 


            i +=1 

        results .append (LayeredSprite (
        full_name =full_name ,
        character =character ,
        variant_parts =variant_parts ,
        groups =groups ,
        source_line =header_line_no +1 ,
        source =source ,
        ))

    return results 


def parse_layeredimage_rpy_file (path :str ,source :str ="custom")->List [LayeredSprite ]:
    with open (path ,'r',encoding ='utf-8')as f :
        text =f .read ()
    return parse_layeredimage_rpy (text ,source =source )
