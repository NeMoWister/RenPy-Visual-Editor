

import sys 
import os 


def get_base_dir ()->str :
    if getattr (sys ,'frozen',False ):
        return os .path .dirname (os .path .abspath (sys .executable ))

    return os .path .dirname (os .path .dirname (os .path .abspath (__file__ )))


def is_frozen ()->bool :
    return bool (getattr (sys ,'frozen',False ))
