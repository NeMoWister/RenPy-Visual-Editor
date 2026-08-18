
import os ,json ,re 
from typing import Dict ,List ,Optional 
from dataclasses import dataclass ,field ,asdict 
from core .composite_sprite_parser import (
CompositeSprite ,parse_sprites_rpy_file ,get_standalone_attr_words ,
parse_exceptions_file ,EXCEPTIONS_FILENAME ,
)
from core .unified_config import load_section ,save_section 

IMAGE_EXTS ={'.png','.jpg','.jpeg','.webp','.bmp','.gif'}
AUDIO_EXTS ={'.mp3','.ogg','.wav','.flac','.opus'}


SOURCES =("default","custom")


def filename_to_var (filename :str )->str :
    name =os .path .splitext (filename )[0 ]
    name =re .sub (r'[^a-zA-Z0-9_]','_',name )
    if name and name [0 ].isdigit ():
        name ='_'+name 
    return name .lower ()


@dataclass 
class AttrGroup :

    words :List [str ]
    optional :bool =False 


@dataclass 
class ResourceEntry :
    var_name :str 
    rel_path :str 
    abs_path :str 
    filename :str 
    display_name :str 
    category :str 
    group_path :str =""
    source :str ="custom"
    game_path :str =""

    def group_parts (self )->List [str ]:
        return [p for p in self .group_path .split ('/')if p ]


@dataclass 
class ResourceConfig :
    custom_name :str =""
    custom_var :str =""
    volume :Optional [float ]=None 


@dataclass 
class ResourcesConfig :
    resources_path :str ="resources"
    overrides :Dict [str ,ResourceConfig ]=field (default_factory =dict )


class ResourceManager :
    CATEGORIES ={
    'bg':('Фоны (BG)',IMAGE_EXTS ),
    'cg':('CG',IMAGE_EXTS ),
    'sprites':('Спрайты',IMAGE_EXTS ),
    'music':('Музыка',AUDIO_EXTS ),
    'sounds':('Звуки',AUDIO_EXTS ),
    'ambience':('Эмбиенс',AUDIO_EXTS ),
    }
    RENPY_PREFIX ={
    'bg':'bg','cg':'cg','sprites':'',
    'music':'','sounds':'sfx_','ambience':'ambience_',
    }


    NESTED_CATEGORIES ={'sprites'}

    def __init__ (self ,base_dir :str ):
        self .base_dir =base_dir 
        self .config =self ._load_config ()
        self .resources :Dict [str ,List [ResourceEntry ]]={cat :[]for cat in self .CATEGORIES }
        self .composite_sprites :List [CompositeSprite ]=[]
        self .composite_exceptions :Dict [str ,set ]={}

    def _load_config (self )->ResourcesConfig :
        data =load_section (self .base_dir ,"resources")
        if data :
            try :
                cfg =ResourcesConfig ()
                cfg .resources_path =data .get ('resources_path','resources')
                for k ,v in data .get ('overrides',{}).items ():
                    cfg .overrides [k ]=ResourceConfig (**v )
                return cfg 
            except Exception :
                pass 
        return ResourcesConfig ()

    def save_config (self ):
        data ={
        'resources_path':self .config .resources_path ,
        'overrides':{k :asdict (v )for k ,v in self .config .overrides .items ()}
        }
        save_section (self .base_dir ,"resources",data )

    def export_overrides (self ,path :str ):

        data ={
        'overrides':{k :asdict (v )for k ,v in self .config .overrides .items ()}
        }
        with open (path ,'w',encoding ='utf-8')as f :
            json .dump (data ,f ,ensure_ascii =False ,indent =2 )

    def import_overrides (self ,path :str ,merge :bool =True )->int :

        with open (path ,'r',encoding ='utf-8')as f :
            data =json .load (f )
        loaded ={k :ResourceConfig (**v )for k ,v in data .get ('overrides',{}).items ()}
        if not merge :
            self .config .overrides .clear ()
        self .config .overrides .update (loaded )
        return len (loaded )

    def get_resources_root (self )->str :
        if os .path .isabs (self .config .resources_path ):
            return self .config .resources_path 
        return os .path .join (self .base_dir ,self .config .resources_path )

    def get_source_root (self ,source :str )->str :

        return os .path .join (self .get_resources_root (),source )

    def import_local_file (self ,category :str ,src_path :str )->Optional ['ResourceEntry']:

        if category not in self .CATEGORIES :
            return None 
        _ ,exts =self .CATEGORIES [category ]
        ext =os .path .splitext (src_path )[1 ].lower ()
        if ext not in exts :
            return None 

        dest_dir =os .path .join (self .get_source_root ("custom"),category )
        os .makedirs (dest_dir ,exist_ok =True )

        base_name =os .path .basename (src_path )
        stem ,ext =os .path .splitext (base_name )
        dest_name =base_name 
        counter =2 
        while os .path .exists (os .path .join (dest_dir ,dest_name )):
            dest_name =f"{stem }_{counter }{ext }"
            counter +=1 

        dest_path =os .path .join (dest_dir ,dest_name )
        try :
            import shutil 
            shutil .copy2 (src_path ,dest_path )
        except OSError as e :
            print (f"Не удалось скопировать файл ресурса: {e }")
            return None 

        self .scan ()
        for entry in self .resources .get (category ,[]):
            if os .path .normcase (os .path .normpath (entry .abs_path ))==os .path .normcase (os .path .normpath (dest_path )):
                return entry 
        return None 

    def scan (self ):
        for cat ,(_ ,exts )in self .CATEGORIES .items ():
            self .resources [cat ]=[]
            for source in SOURCES :
                source_root =self .get_source_root (source )
                cat_dir =os .path .join (source_root ,cat )
                if not os .path .isdir (cat_dir ):
                    os .makedirs (cat_dir ,exist_ok =True )
                    continue 
                if cat in self .NESTED_CATEGORIES :
                    self ._scan_nested (cat ,cat_dir ,exts ,source )
                else :
                    self ._scan_flat (cat ,cat_dir ,exts ,source )
        self ._scan_sprite_definitions ()

    def _scan_sprite_definitions (self ):

        self .composite_sprites =[]
        self .composite_exceptions :Dict [str ,set ]={}
        used_rel_paths_by_source ={"default":set (),"custom":set ()}

        def entry_rel_path (e :ResourceEntry )->str :
            return f"{e .group_path }/{e .filename }"if e .group_path else e .filename 

        for source in SOURCES :
            sprites_dir =os .path .join (self .get_source_root (source ),'sprites')
            rpy_path =os .path .join (sprites_dir ,'sprites.rpy')
            if not os .path .isfile (rpy_path ):
                continue 
            try :
                composites =parse_sprites_rpy_file (rpy_path ,source =source )
            except Exception :
                composites =[]
            self .composite_sprites .extend (composites )
            for cs in composites :
                for layer in cs .layers :
                    used_rel_paths_by_source [source ].add (layer .rel_path .replace ('\\','/'))




            exceptions_path =os .path .join (sprites_dir ,EXCEPTIONS_FILENAME )
            try :
                exceptions =parse_exceptions_file (exceptions_path )
            except Exception :
                exceptions ={}
            for character ,words in exceptions .items ():
                self .composite_exceptions .setdefault (character ,set ()).update (words )

        filtered =[]
        for e in self .resources ['sprites']:
            used =used_rel_paths_by_source .get (e .source ,set ())
            if entry_rel_path (e )not in used :
                filtered .append (e )
        self .resources ['sprites']=filtered 


    def _scan_flat (self ,cat :str ,cat_dir :str ,exts :set ,source :str ):
        for fn in sorted (os .listdir (cat_dir )):
            full =os .path .join (cat_dir ,fn )
            if not os .path .isfile (full ):
                continue 
            ext =os .path .splitext (fn )[1 ].lower ()
            if ext not in exts :
                continue 
            self .resources [cat ].append (self ._make_entry (cat ,cat_dir ,fn ,group_path ="",source =source ))

    def _scan_nested (self ,cat :str ,cat_dir :str ,exts :set ,source :str ):

        for dirpath ,dirnames ,filenames in os .walk (cat_dir ):
            dirnames .sort ()
            group_path =os .path .relpath (dirpath ,cat_dir ).replace ('\\','/')
            if group_path =='.':
                group_path =""
            for fn in sorted (filenames ):
                ext =os .path .splitext (fn )[1 ].lower ()
                if ext not in exts :
                    continue 
                if fn .lower ()=='sprites.rpy':
                    continue 
                self .resources [cat ].append (self ._make_entry (cat ,dirpath ,fn ,group_path =group_path ,source =source ))

    def _make_entry (self ,cat :str ,dir_abs :str ,fn :str ,group_path :str ,source :str )->ResourceEntry :
        abs_path =os .path .join (dir_abs ,fn )





        game_path =os .path .relpath (abs_path ,self .get_source_root (source )).replace ('\\','/')
        rel_path =f"{source }/{game_path }"
        override =self .config .overrides .get (rel_path ,ResourceConfig ())

        if override .custom_var :
            base_var =override .custom_var 
        else :
            base_var =self ._auto_var (cat ,fn ,group_path )

        display =override .custom_name if override .custom_name else os .path .splitext (fn )[0 ]
        return ResourceEntry (
        var_name =base_var ,rel_path =rel_path ,abs_path =abs_path ,
        filename =fn ,display_name =display ,category =cat ,group_path =group_path ,
        source =source ,game_path =game_path ,
        )

    def _auto_var (self ,cat :str ,fn :str ,group_path :str )->str :

        name =filename_to_var (fn )
        if cat in ('bg','cg'):
            return f"{self .RENPY_PREFIX [cat ]} {name }"
        if cat =='music':
            return f'music_list["{name }"]'
        if cat =='sprites':
            parts =[p for p in group_path .split ('/')if p and p !='.']
            name_parts =[filename_to_var (p )for p in parts ]+[name ]
            return "_".join (name_parts )

        return self .RENPY_PREFIX .get (cat ,'')+name 

    def get (self ,category :str )->List [ResourceEntry ]:
        return self .resources .get (category ,[])

    def get_folders (self ,category :str ,parent_path :str ="")->List [str ]:

        if category not in self .NESTED_CATEGORIES :
            return []
        seen =set ()
        for e in self .resources .get (category ,[]):
            parts =e .group_parts ()
            parent_parts =[p for p in parent_path .split ('/')if p ]
            if parts [:len (parent_parts )]!=parent_parts :
                continue 
            if len (parts )>len (parent_parts ):
                seen .add (parts [len (parent_parts )])
        return sorted (seen )

    def get_entries_in_folder (self ,category :str ,folder_path :str ="")->List [ResourceEntry ]:

        if category not in self .NESTED_CATEGORIES :
            return self .resources .get (category ,[])
        folder_parts =[p for p in folder_path .split ('/')if p ]
        return [e for e in self .resources .get (category ,[])if e .group_parts ()==folder_parts ]

    def find_by_var (self ,var :str )->Optional [ResourceEntry ]:
        for entries in self .resources .values ():
            for e in entries :
                if e .var_name ==var :
                    return e 
        return None 

    def get_composite_characters (self )->List [str ]:

        return sorted (set (cs .character for cs in self .composite_sprites ))

    def get_composite_positions (self ,character :str )->List [str ]:

        order =["far","close","normal"]
        present =set (cs .position for cs in self .composite_sprites if cs .character ==character )
        return [p for p in order if p in present ]

    def get_composite_sprites (self ,character :str ,position :str )->List [CompositeSprite ]:

        result =[
        cs for cs in self .composite_sprites 
        if cs .character ==character and cs .position ==position 
        ]
        result .sort (key =lambda cs :cs .display_name )
        return result 

    def find_composite_by_name (self ,full_name :str )->Optional [CompositeSprite ]:
        for cs in self .composite_sprites :
            if cs .full_name ==full_name :
                return cs 
        return None 

    def _standalone_attr_words (self ,character :str )->set :

        combos =[cs .variant_parts for cs in self .composite_sprites if cs .character ==character ]
        manual_words =self .composite_exceptions .get (character )
        return get_standalone_attr_words (character ,combos ,manual_words )

    def get_composite_attr_groups (self ,character :str ,position :str )->List [AttrGroup ]:

        sprites =[cs for cs in self .composite_sprites 
        if cs .character ==character and cs .position ==position ]
        extra_words =self ._standalone_attr_words (character )

        core_combos =[[w for w in cs .variant_parts if w not in extra_words ]for cs in sprites ]
        max_len =max ((len (c )for c in core_combos ),default =0 )
        per_index :List [set ]=[set ()for _ in range (max_len )]
        for c in core_combos :
            for i ,word in enumerate (c ):
                per_index [i ].add (word )
        groups =[AttrGroup (words =sorted (s ),optional =False )for s in per_index ]

        extra_present =sorted ({w for cs in sprites for w in cs .variant_parts if w in extra_words })
        if extra_present :
            groups .append (AttrGroup (words =extra_present ,optional =True ))
        return groups 

    def find_composite_by_attr_selection (self ,character :str ,position :str ,
    selected :List [Optional [str ]],
    groups :List [AttrGroup ])->Optional [CompositeSprite ]:

        for word ,group in zip (selected ,groups ):
            if word is None and not group .optional :
                return None 
        chosen ={w for w in selected if w is not None }
        for cs in self .composite_sprites :
            if cs .character ==character and cs .position ==position and set (cs .variant_parts )==chosen :
                return cs 
        return None 

    def find_composite_with_word (self ,character :str ,position :str ,word :str )->Optional [CompositeSprite ]:

        for cs in self .composite_sprites :
            if cs .character ==character and cs .position ==position and word in cs .variant_parts :
                return cs 
        return None 

    def get_compatible_words (self ,character :str ,position :str ,groups :List [AttrGroup ],
    selected_attrs :List [Optional [str ]],group_index :int )->set :

        if group_index >=len (groups ):
            return set ()
        words_in_group =set (groups [group_index ].words )
        others_selected =[w for gi ,w in enumerate (selected_attrs )if gi !=group_index and w is not None ]
        if not others_selected :
            return words_in_group 
        compatible =set ()
        for cs in self .composite_sprites :
            if cs .character !=character or cs .position !=position :
                continue 
            vp =set (cs .variant_parts )
            if all (w in vp for w in others_selected ):
                for word in words_in_group :
                    if word in vp :
                        compatible .add (word )
        return compatible 

    def resolve_layer_path (self ,rel_path :str ,source :str ="custom")->str :

        return os .path .join (self .get_source_root (source ),'sprites',rel_path )

    def set_override (self ,rel_path :str ,name :str ="",var :str ="",volume :Optional [float ]=None ):

        existing =self .config .overrides .get (rel_path )
        if volume is None and existing is not None :
            volume =existing .volume 
        self .config .overrides [rel_path ]=ResourceConfig (custom_name =name ,custom_var =var ,volume =volume )
        self .save_config ()

    def get_volume (self ,rel_path :str )->Optional [float ]:
        cfg =self .config .overrides .get (rel_path )
        return cfg .volume if cfg else None 

    def set_volume (self ,rel_path :str ,volume :Optional [float ]):

        existing =self .config .overrides .get (rel_path ,ResourceConfig ())
        existing .volume =volume 
        if existing .custom_name or existing .custom_var or existing .volume is not None :
            self .config .overrides [rel_path ]=existing 
        elif rel_path in self .config .overrides :
            del self .config .overrides [rel_path ]
        self .save_config ()

    def get_volume_by_var (self ,var_name :str )->Optional [float ]:

        entry =self .find_by_var (var_name )
        if entry is None :
            return None 
        return self .get_volume (entry .rel_path )

    def generate_define_block (self )->str :
        lines =["# ===== Определения ресурсов =====",""]
        for cat ,entries in self .resources .items ():






            if cat =='music':
                continue 
            custom_entries =[e for e in entries if e .source =="custom"]
            if not custom_entries :
                continue 
            label ,_ =self .CATEGORIES [cat ]
            lines .append (f"# {label }")
            for e in custom_entries :
                if cat in ('bg','cg','sprites'):
                    lines .append (f'image {e .var_name } = "{e .game_path }"')
                else :
                    lines .append (f'define {e .var_name } = "{e .game_path }"')
            lines .append ("")
        if self .composite_sprites :
            lines .append ("# Составные спрайты (персонаж/позиция/эмоция) уже определены")
            lines .append ("# в sprites.rpy - убедитесь, что этот файл подключён к проекту")
            lines .append ("# Ren'Py, отдельных image здесь не нужно (для default и custom")
            lines .append ("# источников одинаково).")
            lines .append ("")

        return "\n".join (lines )
