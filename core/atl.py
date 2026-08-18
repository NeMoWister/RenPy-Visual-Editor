

import re 
from dataclasses import dataclass ,field 
from typing import List ,Optional ,Dict ,Tuple ,Union 






PROP_KEYS ={
"xalign","yalign","xpos","ypos","xanchor","yanchor",
"xoffset","yoffset","zoom","xzoom","yzoom","rotate","alpha",
"xsize","ysize",
}
TUPLE_KEYS ={"pos","anchor","align","offset","xysize"}
ALL_PROP_KEYS =PROP_KEYS |TUPLE_KEYS 

WARPER_NAMES ={"linear","ease","easein","easeout","ease_in","ease_out",
"easein_quad","easeout_quad"}


@dataclass 
class ATLSet :
    props :Dict [str ,object ]=field (default_factory =dict )


@dataclass 
class ATLInterpolate :
    duration :float 
    warper :str 
    props :Dict [str ,object ]=field (default_factory =dict )


@dataclass 
class ATLPause :
    duration :float 


@dataclass 
class ATLImage :
    text :str 
    transition :Optional [str ]=None 


@dataclass 
class ATLWith :
    transition :str 


@dataclass 
class ATLRepeat :
    count :Optional [int ]=None 


@dataclass 
class ATLBlockStmt :
    block :"ATLBlock"


@dataclass 
class ATLRaw :
    text :str 


ATLStmt =Union [ATLSet ,ATLInterpolate ,ATLPause ,ATLImage ,ATLWith ,
ATLRepeat ,ATLBlockStmt ,ATLRaw ]


@dataclass 
class ATLBlock :
    statements :List [ATLStmt ]=field (default_factory =list )






_PROP_TOKEN_RE =re .compile (r'([a-zA-Z_]+)\s*(\([^)]*\)|[-+]?\d+\.?\d*)')
_NUM_RE =re .compile (r'[-+]?\d+\.?\d*')


def _unquote (s :str )->str :
    s =s .strip ()
    if len (s )>=2 and s [0 ]==s [-1 ]and s [0 ]in ('"',"'"):
        q =s [0 ]
        return s [1 :-1 ].replace ('\\'+q ,q )
    return s 


def _strip_comment (line :str )->str :
    in_q =False 
    for i ,ch in enumerate (line ):
        if ch =='"':
            in_q =not in_q 
        elif ch =='#'and not in_q :
            return line [:i ].rstrip ()
    return line 


def _parse_props_from_tail (tail :str )->Dict [str ,object ]:
    props :Dict [str ,object ]={}
    for m in _PROP_TOKEN_RE .finditer (tail ):
        key ,val =m .group (1 ),m .group (2 )
        if key not in ALL_PROP_KEYS :
            continue 
        if val .startswith ('('):
            nums =[float (x )for x in _NUM_RE .findall (val )]
            if len (nums )>=2 :
                props [key ]=(nums [0 ],nums [1 ])
        else :
            try :
                props [key ]=float (val )
            except ValueError :
                pass 
    return props 


_PAUSE_RE =re .compile (r'^pause\s+([\d.]+)\s*$')
_REPEAT_RE =re .compile (r'^repeat(?:\s+(\d+))?\s*$')
_BLOCK_RE =re .compile (r'^block\s*:\s*$')
_WARPER_RE =re .compile (r'^(\w+)\s+([\d.]+)\s+(.+)$')
_WITH_RE =re .compile (r'^with\s+(\w+)\s*$')
_IMAGE_RE =re .compile (r'^(["\'])(.*)\1(?:\s+with\s+(\w+))?\s*$')


def _parse_atl_line (line :str )->ATLStmt :
    m =_PAUSE_RE .match (line )
    if m :
        return ATLPause (duration =float (m .group (1 )))

    m =_REPEAT_RE .match (line )
    if m :
        return ATLRepeat (count =int (m .group (1 ))if m .group (1 )else None )

    m =_WARPER_RE .match (line )
    if m and m .group (1 )in WARPER_NAMES :
        props =_parse_props_from_tail (m .group (3 ))
        if props :
            return ATLInterpolate (duration =float (m .group (2 )),warper =m .group (1 ),props =props )

    m =_WITH_RE .match (line )
    if m :
        return ATLWith (transition =m .group (1 ))

    m =_IMAGE_RE .match (line )
    if m :
        q =m .group (1 )
        text =m .group (2 ).replace ('\\'+q ,q )
        return ATLImage (text =text ,transition =m .group (3 ))

    props =_parse_props_from_tail (line )
    if props :
        return ATLSet (props =props )

    return ATLRaw (text =line )


def _tokenize_atl (text :str )->List [Tuple [int ,str ]]:
    out =[]
    for raw in text .splitlines ():
        if not raw .strip ():
            continue 
        indent =len (raw )-len (raw .lstrip ())
        stripped =_strip_comment (raw ).strip ()
        if stripped :
            out .append ((indent ,stripped ))
    return out 


def _parse_block (tokens :List [Tuple [int ,str ]],start :int ,end :int ,base_indent :int )->ATLBlock :
    stmts :List [ATLStmt ]=[]
    i =start 
    while i <end :
        indent ,line =tokens [i ]
        if indent <base_indent :
            break 
        if indent >base_indent :

            i +=1 
            continue 
        if _BLOCK_RE .match (line ):
            j =i +1 
            k =j 
            child_base =tokens [j ][0 ]if j <end else base_indent +4 
            while k <end and tokens [k ][0 ]>=child_base :
                k +=1 
            stmts .append (ATLBlockStmt (_parse_block (tokens ,j ,k ,child_base )))
            i =k 
            continue 
        stmts .append (_parse_atl_line (line ))
        i +=1 
    return ATLBlock (statements =stmts )


def parse_atl_text (text :str )->ATLBlock :

    tokens =_tokenize_atl (text or "")
    if not tokens :
        return ATLBlock (statements =[])
    base_indent =tokens [0 ][0 ]
    return _parse_block (tokens ,0 ,len (tokens ),base_indent )






@dataclass 
class Segment :
    t0 :float 
    t1 :float 
    kind :str 
    state_from :Dict [str ,object ]
    state_to :Dict [str ,object ]
    warper :str ="linear"


@dataclass 
class CompiledTimeline :
    segments :List [Segment ]=field (default_factory =list )
    total :float =0.0 
    loop_start :float =0.0 
    loop_end :float =0.0 
    loop_count :Optional [int ]=None 
    has_loop :bool =False 
    initial_state :Dict [str ,object ]=field (default_factory =dict )


def _ease (x :float )->float :
    return x *x *(3 -2 *x )


WARPERS ={
"linear":lambda x :x ,
"ease":_ease ,
"easein":lambda x :x *x ,
"easeout":lambda x :1 -(1 -x )*(1 -x ),
"ease_in":lambda x :x *x ,
"ease_out":lambda x :1 -(1 -x )*(1 -x ),
"easein_quad":lambda x :x *x ,
"easeout_quad":lambda x :1 -(1 -x )*(1 -x ),
}


def compile_block (block :ATLBlock ,base_state :Dict [str ,object ])->CompiledTimeline :
    segments :List [Segment ]=[]
    state =dict (base_state )
    t =0.0 
    loop_marker :Optional [Tuple [float ,Optional [int ]]]=None 

    for stmt in block .statements :
        if isinstance (stmt ,ATLRepeat ):
            loop_marker =(0.0 ,stmt .count )
            continue 

        if isinstance (stmt ,ATLBlockStmt ):
            sub =compile_block (stmt .block ,state )
            for seg in sub .segments :
                segments .append (Segment (seg .t0 +t ,seg .t1 +t ,seg .kind ,
                seg .state_from ,seg .state_to ,seg .warper ))
            if sub .segments :
                state =dict (sub .segments [-1 ].state_to )
            t +=sub .total 
            if sub .has_loop :


                break 
            continue 

        if isinstance (stmt ,ATLPause ):
            segments .append (Segment (t ,t +stmt .duration ,'hold',dict (state ),dict (state )))
            t +=stmt .duration 
            continue 

        if isinstance (stmt ,ATLInterpolate ):
            target =dict (state )
            target .update (stmt .props )
            segments .append (Segment (t ,t +stmt .duration ,'interp',
            dict (state ),dict (target ),stmt .warper ))
            t +=stmt .duration 
            state =target 
            continue 

        if isinstance (stmt ,ATLSet ):
            state =dict (state )
            state .update (stmt .props )
            segments .append (Segment (t ,t ,'hold',dict (state ),dict (state )))
            continue 

        if isinstance (stmt ,ATLImage ):
            state =dict (state )
            state ['__image__']=stmt .text 
            state ['__transition__']=stmt .transition 
            segments .append (Segment (t ,t ,'hold',dict (state ),dict (state )))
            continue 

        if isinstance (stmt ,ATLWith ):
            state =dict (state )
            state ['__transition__']=stmt .transition 
            segments .append (Segment (t ,t ,'hold',dict (state ),dict (state )))
            continue 


        continue 

    total =t 
    has_loop =loop_marker is not None 
    loop_count =loop_marker [1 ]if loop_marker else None 
    return CompiledTimeline (
    segments =segments ,total =total ,loop_start =0.0 ,loop_end =total ,
    loop_count =loop_count ,has_loop =has_loop ,initial_state =base_state ,
    )


def evaluate (tl :CompiledTimeline ,t :float )->Dict [str ,object ]:

    if not tl .segments :
        return dict (tl .initial_state )

    if tl .has_loop :
        loop_len =max (tl .loop_end -tl .loop_start ,1e-6 )
        if tl .loop_count is None :
            if t >tl .loop_end :
                t =tl .loop_start +(t -tl .loop_start )%loop_len 
        else :
            max_t =tl .loop_start +loop_len *tl .loop_count 
            if t >=max_t :
                t =max (max_t -1e-6 ,tl .loop_start )
            elif t >tl .loop_end :
                t =tl .loop_start +(t -tl .loop_start )%loop_len 
    elif t >tl .total :
        t =tl .total 

    chosen =tl .segments [0 ]
    for seg in tl .segments :
        if seg .t0 <=t :
            chosen =seg 
        else :
            break 

    if chosen .kind =='hold'or chosen .t1 <=chosen .t0 :
        return dict (chosen .state_to )

    frac =(t -chosen .t0 )/(chosen .t1 -chosen .t0 )
    frac =max (0.0 ,min (1.0 ,frac ))
    e =WARPERS .get (chosen .warper ,WARPERS ['linear'])(frac )

    result =dict (chosen .state_from )
    for k ,v in chosen .state_to .items ():
        fv =chosen .state_from .get (k ,v )
        if k in ('__image__','__transition__'):
            result [k ]=v if e >=1.0 else fv 
        elif isinstance (v ,tuple )and isinstance (fv ,tuple ):
            result [k ]=(fv [0 ]+(v [0 ]-fv [0 ])*e ,fv [1 ]+(v [1 ]-fv [1 ])*e )
        elif isinstance (v ,(int ,float ))and isinstance (fv ,(int ,float )):
            result [k ]=fv +(v -fv )*e 
        else :
            result [k ]=v 
    return result 






REF_W =1920.0 
REF_H =1080.0 


def resolve_visual (atl_text :str ,t :float ,
base_xalign :float =0.5 ,base_yalign :float =1.0 ,
base_zoom :float =1.0 ,ref_w :float =REF_W ,ref_h :float =REF_H )->dict :

    base_state ={
    "xalign":base_xalign ,"yalign":base_yalign ,"zoom":base_zoom ,
    "alpha":1.0 ,"rotate":0.0 ,"__image__":None ,"__transition__":None ,
    }
    if not atl_text or not atl_text .strip ():
        return {
        "xalign":base_xalign ,"yalign":base_yalign ,"zoom":base_zoom ,
        "alpha":1.0 ,"rotate":0.0 ,"image_text":None ,"image_transition":None ,
        }
    try :
        block =parse_atl_text (atl_text )
        tl =compile_block (block ,base_state )
        st =evaluate (tl ,max (0.0 ,t ))
    except Exception :
        st =base_state 

    xalign =st .get ("xalign",base_xalign )
    yalign =st .get ("yalign",base_yalign )
    zoom =st .get ("zoom",base_zoom )

    if "xzoom"in st or "yzoom"in st :
        zoom =st .get ("xzoom",st .get ("yzoom",zoom ))

    if "pos"in st :
        px ,py =st ["pos"]
        xalign =xalign +px /ref_w 
        yalign =yalign +py /ref_h 
    if "xpos"in st :
        xp =st ["xpos"]
        xalign =xp if abs (xp )<=2.0 else xalign +xp /ref_w 
    if "ypos"in st :
        yp =st ["ypos"]
        yalign =yp if abs (yp )<=2.0 else yalign +yp /ref_h 
    if "offset"in st :
        ox ,oy =st ["offset"]
        xalign =xalign +ox /ref_w 
        yalign =yalign +oy /ref_h 
    if "xoffset"in st :
        xalign =xalign +st ["xoffset"]/ref_w 
    if "yoffset"in st :
        yalign =yalign +st ["yoffset"]/ref_h 

    return {
    "xalign":xalign ,"yalign":yalign ,"zoom":zoom ,
    "alpha":st .get ("alpha",1.0 ),"rotate":st .get ("rotate",0.0 ),
    "image_text":st .get ("__image__"),"image_transition":st .get ("__transition__"),
    }


def quick_final_position (atl_text :str ,base_xalign :float =0.5 ,
base_yalign :float =1.0 ,base_zoom :float =1.0 )->Tuple [float ,float ,float ]:

    if not atl_text or not atl_text .strip ():
        return base_xalign ,base_yalign ,base_zoom 
    try :
        block =parse_atl_text (atl_text )
        base_state ={"xalign":base_xalign ,"yalign":base_yalign ,"zoom":base_zoom }
        tl =compile_block (block ,base_state )
        final =tl .segments [-1 ].state_to if tl .segments else base_state 
    except Exception :
        return base_xalign ,base_yalign ,base_zoom 
    return (final .get ("xalign",base_xalign ),final .get ("yalign",base_yalign ),
    final .get ("zoom",base_zoom ))


def cycle_duration (atl_text :str )->Optional [float ]:

    if not atl_text or not atl_text .strip ():
        return None 
    try :
        block =parse_atl_text (atl_text )
        tl =compile_block (block ,{})
    except Exception :
        return None 
    if tl .has_loop :
        if tl .loop_count is None :
            return tl .loop_end -tl .loop_start if tl .loop_end >tl .loop_start else None 
        return tl .loop_start +(tl .loop_end -tl .loop_start )*tl .loop_count 
    return tl .total if tl .total >0 else None 


def is_animated (atl_text :str )->bool :

    if not atl_text or not atl_text .strip ():
        return False 
    try :
        block =parse_atl_text (atl_text )
        tl =compile_block (block ,{})
    except Exception :
        return False 
    if tl .has_loop :
        return True 
    return any (s .kind =='interp'for s in tl .segments )or any (s .state_to .get ('__image__')is not None for s in tl .segments )


def referenced_images (atl_text :str )->List [str ]:

    names :List [str ]=[]
    seen =set ()

    def walk (block :ATLBlock ):
        for stmt in block .statements :
            if isinstance (stmt ,ATLImage )and stmt .text not in seen :
                seen .add (stmt .text )
                names .append (stmt .text )
            elif isinstance (stmt ,ATLBlockStmt ):
                walk (stmt .block )

    if atl_text and atl_text .strip ():
        try :
            walk (parse_atl_text (atl_text ))
        except Exception :
            pass 
    return names 


def describe (atl_text :str )->List [str ]:

    warnings :List [str ]=[]

    def walk (block :ATLBlock ):
        for stmt in block .statements :
            if isinstance (stmt ,ATLRaw )and stmt .text .strip ():
                warnings .append (stmt .text .strip ())
            elif isinstance (stmt ,ATLBlockStmt ):
                walk (stmt .block )

    if atl_text and atl_text .strip ():
        try :
            walk (parse_atl_text (atl_text ))
        except Exception :
            pass 
    return warnings 
