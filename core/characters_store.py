

from dataclasses import asdict 
from typing import List 

from core .models import Character 
from core .unified_config import load_section ,save_section 


def load_global_characters (base_dir :str )->List [Character ]:
    data =load_section (base_dir ,"characters")
    try :
        return [Character (**c )for c in data .get ("characters",[])]
    except Exception :
        return []


def save_global_characters (base_dir :str ,characters :List [Character ]):
    save_section (base_dir ,"characters",{"characters":[asdict (ch )for ch in characters ]})
