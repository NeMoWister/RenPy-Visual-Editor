

from typing import Dict ,Optional 

from core .unified_config import load_section ,save_section 

SECTION ="custom_transitions"


def load_custom_transitions (base_dir :str )->Dict [str ,str ]:

    if not base_dir :
        return {}
    data =load_section (base_dir ,SECTION )
    return {str (k ):str (v )for k ,v in data .items ()}if isinstance (data ,dict )else {}


def save_custom_transition (base_dir :str ,name :str ,expr :str ):
    if not base_dir or not name :
        return 
    data =load_custom_transitions (base_dir )
    data [name ]=expr 
    save_section (base_dir ,SECTION ,data )


def delete_custom_transition (base_dir :str ,name :str ):
    if not base_dir or not name :
        return 
    data =load_custom_transitions (base_dir )
    if name in data :
        del data [name ]
        save_section (base_dir ,SECTION ,data )


def suggest_name (base_dir :str ,hint :str )->str :

    from core .transitions import BUILTIN_TRANSITIONS 
    import re 
    base =re .sub (r'[^a-zA-Z0-9_]+','_',hint ).strip ('_').lower ()or "custom_transition"
    existing =set (BUILTIN_TRANSITIONS .keys ())|set (load_custom_transitions (base_dir ).keys ())
    if base not in existing :
        return base 
    i =2 
    while f"{base }_{i }"in existing :
        i +=1 
    return f"{base }_{i }"


def resolve (text :str ,base_dir :Optional [str ])->str :

    if not text or not base_dir :
        return text 
    custom =load_custom_transitions (base_dir )
    return custom .get (text ,text )
