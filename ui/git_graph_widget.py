
from typing import List ,Optional 

from PyQt6 .QtWidgets import QWidget ,QScrollArea 
from PyQt6 .QtGui import QPainter ,QColor ,QPen ,QFont 
from PyQt6 .QtCore import Qt ,QRectF ,pyqtSignal 

from core .git_manager import GraphCommit 

ROW_H =30 
LANE_W =18 
DOT_R =5 
LEFT_MARGIN =12 
TEXT_GAP =10 

LANE_COLORS =[
QColor ("#ff8c3d"),QColor ("#5aa0ff"),QColor ("#6fd68f"),QColor ("#e0679c"),
QColor ("#c9a3ff"),QColor ("#ffd166"),QColor ("#4dd0e1"),QColor ("#f28b82"),
]


class GitGraphWidget (QWidget ):
    commit_selected =pyqtSignal (str )

    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .commits :List [GraphCommit ]=[]
        self ._hash_to_row ={}
        self ._graph_width =LEFT_MARGIN *2 +LANE_W 
        self .selected_hash :Optional [str ]=None 
        self .setMouseTracking (True )
        self ._mono =QFont ("Consolas",9 )
        self ._font =QFont ()
        self ._font .setPointSize (9 )

    def set_commits (self ,commits :List [GraphCommit ]):
        self .commits =commits 
        self ._hash_to_row ={c .commit_hash :i for i ,c in enumerate (commits )}
        max_lane =max ((c .lane for c in commits ),default =0 )
        self ._graph_width =LEFT_MARGIN *2 +(max_lane +1 )*LANE_W 
        self .setMinimumWidth (self ._graph_width +480 )
        self .setFixedHeight (max (ROW_H ,len (commits )*ROW_H )+12 )
        self .update ()

    def _lane_color (self ,lane :int )->QColor :
        return LANE_COLORS [lane %len (LANE_COLORS )]

    def _dot_pos (self ,row :int ,lane :int ):
        x =LEFT_MARGIN +lane *LANE_W 
        y =row *ROW_H +ROW_H //2 +6 
        return x ,y 

    def paintEvent (self ,event ):
        p =QPainter (self )
        p .setRenderHint (QPainter .RenderHint .Antialiasing ,True )
        p .fillRect (self .rect (),QColor ("#17171c"))

        for row ,c in enumerate (self .commits ):
            x ,y =self ._dot_pos (row ,c .lane )
            for parent_hash in c .parents :
                prow =self ._hash_to_row .get (parent_hash )
                if prow is None :
                    continue 
                pc =self .commits [prow ]
                px ,py =self ._dot_pos (prow ,pc .lane )
                pen =QPen (self ._lane_color (pc .lane ))
                pen .setWidth (2 )
                p .setPen (pen )
                if pc .lane ==c .lane :
                    p .drawLine (x ,y ,px ,py )
                else :
                    mid_y =y +(ROW_H //2 )
                    p .drawLine (x ,y ,x ,mid_y )
                    p .drawLine (x ,mid_y ,px ,mid_y )
                    p .drawLine (px ,mid_y ,px ,py )

        for row ,c in enumerate (self .commits ):
            x ,y =self ._dot_pos (row ,c .lane )
            color =self ._lane_color (c .lane )
            if c .commit_hash ==self .selected_hash :
                p .setBrush (QColor ("#ffffff"))
                p .setPen (QPen (color ,2 ))
                p .drawEllipse (QRectF (x -DOT_R -2 ,y -DOT_R -2 ,(DOT_R +2 )*2 ,(DOT_R +2 )*2 ))
            p .setBrush (color )
            p .setPen (Qt .PenStyle .NoPen )
            p .drawEllipse (QRectF (x -DOT_R ,y -DOT_R ,DOT_R *2 ,DOT_R *2 ))

        text_x =self ._graph_width +TEXT_GAP 
        for row ,c in enumerate (self .commits ):
            y_top =row *ROW_H 
            if c .commit_hash ==self .selected_hash :
                p .fillRect (QRectF (0 ,y_top ,self .width (),ROW_H ),QColor (255 ,255 ,255 ,18 ))

            p .setFont (self ._mono )
            p .setPen (QColor ("#888"))
            p .drawText (QRectF (text_x ,y_top ,64 ,ROW_H ),Qt .AlignmentFlag .AlignVCenter ,c .short_hash )

            bx =text_x +68 
            p .setFont (self ._font )
            for ref in c .refs :
                is_head =ref .startswith ("HEAD")
                label =ref .replace ("HEAD -> ","")
                color =QColor ("#ffb84d")if is_head else QColor ("#4a90d9")
                w =p .fontMetrics ().horizontalAdvance (label )+12 
                badge_rect =QRectF (bx ,y_top +6 ,w ,ROW_H -12 )
                p .setPen (Qt .PenStyle .NoPen )
                p .setBrush (color )
                p .drawRoundedRect (badge_rect ,4 ,4 )
                p .setPen (QColor ("#111"))
                p .drawText (badge_rect ,Qt .AlignmentFlag .AlignCenter ,label )
                bx +=w +6 

            p .setPen (QColor ("#eee"))
            msg_rect =QRectF (bx +(4 if c .refs else 0 ),y_top ,self .width ()-bx -160 ,ROW_H )
            p .drawText (msg_rect ,Qt .AlignmentFlag .AlignVCenter ,
            p .fontMetrics ().elidedText (c .message ,Qt .TextElideMode .ElideRight ,int (msg_rect .width ())))

            p .setPen (QColor ("#777"))
            meta_rect =QRectF (self .width ()-150 ,y_top ,140 ,ROW_H )
            p .drawText (meta_rect ,Qt .AlignmentFlag .AlignVCenter |Qt .AlignmentFlag .AlignRight ,
            f"{c .date }  {c .author }"[:28 ])

        p .end ()

    def mousePressEvent (self ,event ):
        row =int (event .position ().y ()//ROW_H )
        if 0 <=row <len (self .commits ):
            self .selected_hash =self .commits [row ].commit_hash 
            self .update ()
            self .commit_selected .emit (self .selected_hash )

    def select_hash (self ,commit_hash :Optional [str ]):
        self .selected_hash =commit_hash 
        self .update ()


def wrap_in_scroll_area (widget :GitGraphWidget )->QScrollArea :
    scroll =QScrollArea ()
    scroll .setWidgetResizable (True )
    scroll .setWidget (widget )
    return scroll 
