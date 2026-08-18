
from typing import Optional ,List ,Tuple 

Entry =Tuple [str ,dict ]


class UndoManager :
    def __init__ (self ,max_depth :int =100 ):
        self .max_depth =max_depth 
        self ._undo_stack :List [Entry ]=[]
        self ._redo_stack :List [Entry ]=[]

    def push (self ,snapshot :dict ,label :str ="Изменение"):

        self ._undo_stack .append ((label ,snapshot ))
        if len (self ._undo_stack )>self .max_depth :
            self ._undo_stack .pop (0 )
        self ._redo_stack .clear ()

    def can_undo (self )->bool :
        return bool (self ._undo_stack )

    def can_redo (self )->bool :
        return bool (self ._redo_stack )

    def undo (self ,current_snapshot :dict )->Optional [Entry ]:
        if not self ._undo_stack :
            return None 
        label ,snap =self ._undo_stack .pop ()
        self ._redo_stack .append ((label ,current_snapshot ))
        return label ,snap 

    def redo (self ,current_snapshot :dict )->Optional [Entry ]:
        if not self ._redo_stack :
            return None 
        label ,snap =self ._redo_stack .pop ()
        self ._undo_stack .append ((label ,current_snapshot ))
        return label ,snap 

    def undo_to_depth (self ,current_snapshot :dict ,depth :int )->Optional [dict ]:

        if depth <1 or depth >len (self ._undo_stack ):
            return None 
        snap =current_snapshot 
        for _ in range (depth ):
            result =self .undo (snap )
            if result is None :
                return None 
            _ ,snap =result 
        return snap 

    def history_labels (self )->List [str ]:

        return [label for label ,_ in self ._undo_stack ]

    def clear (self ):
        self ._undo_stack .clear ()
        self ._redo_stack .clear ()
