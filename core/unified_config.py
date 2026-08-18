

import json 
import os 
import threading 

CONFIG_FILENAME ="editor_config.json"




_LEGACY_FILES ={
"app_settings.json":"app_settings",
"characters_config.json":"characters",
"tags_config.json":"tags",
"resources_config.json":"resources",
}

_lock =threading .Lock ()


def _config_path (base_dir :str )->str :
    return os .path .join (base_dir ,CONFIG_FILENAME )


def _migrate_legacy (base_dir :str )->dict :
    merged ={}
    found =False 
    for filename ,section in _LEGACY_FILES .items ():
        legacy_path =os .path .join (base_dir ,filename )
        if os .path .isfile (legacy_path ):
            try :
                with open (legacy_path ,'r',encoding ='utf-8')as f :
                    merged [section ]=json .load (f )
                found =True 
            except Exception :
                pass 
    if found :
        save_all (base_dir ,merged )
    return merged 


def load_all (base_dir :str )->dict :
    path =_config_path (base_dir )
    if os .path .isfile (path ):
        try :
            with open (path ,'r',encoding ='utf-8')as f :
                return json .load (f )
        except Exception :
            return {}
    return _migrate_legacy (base_dir )


def save_all (base_dir :str ,data :dict ):
    path =_config_path (base_dir )
    try :
        with open (path ,'w',encoding ='utf-8')as f :
            json .dump (data ,f ,ensure_ascii =False ,indent =2 )
    except Exception :
        pass 


def load_section (base_dir :str ,section :str )->dict :
    return load_all (base_dir ).get (section ,{})or {}


def save_section (base_dir :str ,section :str ,value ):
    with _lock :
        data =load_all (base_dir )
        data [section ]=value 
        save_all (base_dir ,data )
