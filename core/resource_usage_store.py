
from typing import Dict ,List 

from core .unified_config import load_section ,save_section 

MAX_RECENT =12 


class ResourceUsageStore :
    def __init__ (self ):
        self .enabled :bool =True 
        self .favorites :Dict [str ,List [str ]]={}
        self .recent :Dict [str ,List [str ]]={}

    @classmethod 
    def load (cls ,base_dir :str )->"ResourceUsageStore":
        store =cls ()
        data =load_section (base_dir ,"resource_usage")
        try :
            store .enabled =bool (data .get ("enabled",True ))
            store .favorites ={k :list (v )for k ,v in data .get ("favorites",{}).items ()}
            store .recent ={k :list (v )for k ,v in data .get ("recent",{}).items ()}
        except Exception :
            pass 
        return store 

    def save (self ,base_dir :str ):
        save_section (base_dir ,"resource_usage",{
        "enabled":self .enabled ,
        "favorites":self .favorites ,
        "recent":self .recent ,
        })



    def is_favorite (self ,category :str ,var_name :str )->bool :
        return var_name in self .favorites .get (category ,[])

    def toggle_favorite (self ,category :str ,var_name :str )->bool :

        lst =self .favorites .setdefault (category ,[])
        if var_name in lst :
            lst .remove (var_name )
            return False 
        lst .append (var_name )
        return True 



    def touch_recent (self ,category :str ,var_name :str ):

        lst =self .recent .setdefault (category ,[])
        if var_name in lst :
            lst .remove (var_name )
        lst .insert (0 ,var_name )
        del lst [MAX_RECENT :]

    def get_recent (self ,category :str )->List [str ]:
        return list (self .recent .get (category ,[]))

    def get_favorites (self ,category :str )->List [str ]:
        return list (self .favorites .get (category ,[]))
