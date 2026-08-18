
import os 
from typing import List ,Optional 

from core .layeredimage_parser import LayeredAttribute ,LayeredGroup ,LayeredSprite 

IMAGE_EXTS ={'.png','.jpg','.jpeg','.webp','.bmp','.gif'}


def _list_dirs_and_files (path :str ):
    dirs ,files =[],[]
    for entry in sorted (os .listdir (path )):
        full =os .path .join (path ,entry )
        if os .path .isdir (full ):
            dirs .append (entry )
        elif os .path .splitext (entry )[1 ].lower ()in IMAGE_EXTS :
            files .append (entry )
    return dirs ,files 


def build_layered_from_folder (character :str ,char_dir :str ,sprites_root :str ,source :str )->Optional [LayeredSprite ]:

    group_dirs ,_root_files =_list_dirs_and_files (char_dir )
    if not group_dirs :
        return None 

    groups ={}
    for group_name in group_dirs :
        group_dir =os .path .join (char_dir ,group_name )
        attr_dirs ,attr_files =_list_dirs_and_files (group_dir )

        attributes :List [LayeredAttribute ]=[]
        for fn in attr_files :
            attr_name =os .path .splitext (fn )[0 ]
            rel_path =os .path .relpath (os .path .join (group_dir ,fn ),sprites_root ).replace ('\\','/')
            attributes .append (LayeredAttribute (name =attr_name ,default =False ,rel_path =rel_path ))

        for sub in attr_dirs :
            sub_dir =os .path .join (group_dir ,sub )
            _sub_dirs ,sub_files =_list_dirs_and_files (sub_dir )
            if not sub_files :
                continue 
            variant_paths =[
            os .path .relpath (os .path .join (sub_dir ,fn ),sprites_root ).replace ('\\','/')
            for fn in sub_files 
            ]
            attributes .append (LayeredAttribute (
            name =sub ,default =False ,
            rel_path =variant_paths [0 ],
            variants =variant_paths [1 :],
            ))

        if not attributes :
            continue 
        attributes .sort (key =lambda a :a .name )


        preferred ={'ok','neutral','normal','default','idle'}
        default_attr =next ((a for a in attributes if a .name .lower ()in preferred ),attributes [0 ])
        default_attr .default =True 

        groups [group_name ]=LayeredGroup (name =group_name ,prefix =group_name ,attributes =attributes )

    if not groups :
        return None 

    return LayeredSprite (
    full_name =character ,
    character =character ,
    variant_parts =[],
    groups =groups ,
    source_line =0 ,
    source =source ,
    from_rpy =False ,
    )
