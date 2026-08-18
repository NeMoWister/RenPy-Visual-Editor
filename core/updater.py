

import json 
import re 
import urllib .request 
from typing import Optional ,Dict 

from version import APP_VERSION 


GITHUB_OWNER ="NeMoWister"
GITHUB_REPO ="RenPy-Visual-Editor"


API_URL_TEMPLATE ="https://api.github.com/repos/{owner}/{repo}/releases/latest"
USER_AGENT ="RenPyVisualScriptEditor-Updater"


def _parse_version (v :str ):
    v =(v or "").strip ().lstrip ("vV")
    parts =re .findall (r"\d+",v )
    return tuple (int (p )for p in parts )if parts else (0 ,)


def is_newer (remote_version :str ,local_version :str =APP_VERSION )->bool :
    return _parse_version (remote_version )>_parse_version (local_version )


def is_configured ()->bool :
    return bool (GITHUB_OWNER and GITHUB_REPO )


def fetch_latest_release (timeout :float =5.0 )->Optional [Dict ]:

    if not is_configured ():
        return None 

    url =API_URL_TEMPLATE .format (owner =GITHUB_OWNER ,repo =GITHUB_REPO )
    req =urllib .request .Request (url ,headers ={
    "Accept":"application/vnd.github+json",
    "User-Agent":USER_AGENT ,
    })
    try :
        with urllib .request .urlopen (req ,timeout =timeout )as resp :
            data =json .loads (resp .read ().decode ("utf-8"))
    except Exception :
        return None 

    tag =data .get ("tag_name")or ""
    if not tag :
        return None 


    page_url =data .get ("html_url","")
    download_url =page_url 
    for asset in data .get ("assets",[]):
        name =asset .get ("name","")
        if name .lower ().endswith (".exe"):
            download_url =asset .get ("browser_download_url",page_url )
            break 

    return {
    "version":tag ,
    "page_url":page_url ,
    "download_url":download_url ,
    "notes":(data .get ("body")or "").strip (),
    "published_at":data .get ("published_at",""),
    }


def check_for_update (timeout :float =5.0 )->Optional [Dict ]:

    release =fetch_latest_release (timeout =timeout )
    if not release :
        return None 
    if is_newer (release ["version"],APP_VERSION ):
        return release 
    return None 
