


MODE_FULL ="full"
MODE_SHORT ="short"

_bg_mode =MODE_FULL 
_show_mode =MODE_FULL 
_cg_mode =MODE_FULL 


def set_bg_label_mode (mode :str ):
    global _bg_mode 
    _bg_mode =mode if mode in (MODE_FULL ,MODE_SHORT )else MODE_FULL 


def get_bg_label_mode ()->str :
    return _bg_mode 


def set_show_label_mode (mode :str ):
    global _show_mode 
    _show_mode =mode if mode in (MODE_FULL ,MODE_SHORT )else MODE_FULL 


def get_show_label_mode ()->str :
    return _show_mode 


def set_cg_label_mode (mode :str ):
    global _cg_mode 
    _cg_mode =mode if mode in (MODE_FULL ,MODE_SHORT )else MODE_FULL 


def get_cg_label_mode ()->str :
    return _cg_mode 


def apply_settings (app_settings ):

    set_bg_label_mode (getattr (app_settings ,"bg_label_mode",MODE_FULL ))
    set_show_label_mode (getattr (app_settings ,"show_label_mode",MODE_FULL ))
    set_cg_label_mode (getattr (app_settings ,"cg_label_mode",MODE_FULL ))


def short_name (resource_var :str )->str :

    if not resource_var :
        return resource_var 
    return resource_var .replace ("\\","/").rsplit ("/",1 )[-1 ]


def display_label (resource_var :str ,mode :str )->str :
    if mode ==MODE_SHORT :
        return short_name (resource_var )
    return resource_var 
