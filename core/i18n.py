
from core .translations import TRANSLATIONS 

DEFAULT_LANGUAGE ="ru"
FALLBACK_LANGUAGE ="ru"




LANGUAGE_NAMES ={
"ru":"Русский",
"en":"English",
}


class Translator :


    def __init__ (self ,language :str =DEFAULT_LANGUAGE ):
        self ._language =language if language in self .available_languages ()else DEFAULT_LANGUAGE 

    def available_languages (self )->list :

        codes =set ()
        for entry in TRANSLATIONS .values ():
            codes .update (entry .keys ())
        if not codes :
            codes ={DEFAULT_LANGUAGE }

        ordered =sorted (codes ,key =lambda c :(c !=DEFAULT_LANGUAGE ,LANGUAGE_NAMES .get (c ,c )))
        return ordered 

    def get_language (self )->str :
        return self ._language 

    def set_language (self ,language :str ):
        if language in self .available_languages ():
            self ._language =language 

    def tr (self ,translation_key :str ,**kwargs )->str :
        entry =TRANSLATIONS .get (translation_key )
        if entry is None :


            return translation_key 
        text =entry .get (self ._language )or entry .get (FALLBACK_LANGUAGE )or translation_key 
        if kwargs :
            try :
                return text .format (**kwargs )
            except (KeyError ,IndexError ):
                return text 
        return text 



_translator =Translator ()


def init_translator (language :str ):

    global _translator 
    _translator =Translator (language )


def set_language (language :str ):
    _translator .set_language (language )


def get_language ()->str :
    return _translator .get_language ()


def available_languages ()->list :
    return _translator .available_languages ()


def language_display_name (code :str )->str :
    return LANGUAGE_NAMES .get (code ,code )


def tr (translation_key :str ,**kwargs )->str :
    return _translator .tr (translation_key ,**kwargs )


def plural (count :int ,forms :dict )->str :

    lang =get_language ()
    lang_forms =forms .get (lang )or forms .get (FALLBACK_LANGUAGE )
    if not lang_forms :
        return str (count )
    if len (lang_forms )>=3 :
        n =abs (count )%100 
        n1 =n %10 
        if 11 <=n <=14 :
            return lang_forms [2 ]
        if n1 ==1 :
            return lang_forms [0 ]
        if 2 <=n1 <=4 :
            return lang_forms [1 ]
        return lang_forms [2 ]

    return lang_forms [0 ]if count ==1 else lang_forms [1 ]
