from PyQt6 .QtWidgets import (
QDialog ,QVBoxLayout ,QHBoxLayout ,QLabel ,QTableWidget ,QTableWidgetItem ,
QDialogButtonBox ,QHeaderView ,QGroupBox 
)
from PyQt6 .QtCore import Qt 

from core .timing_estimator import TimingStats 
from core .i18n import tr 


def _fmt_seconds (s :float )->str :
    s =max (0 ,int (round (s )))
    m ,sec =divmod (s ,60 )
    h ,m =divmod (m ,60 )
    if h :
        return tr ("timing.unit_hms",h =h ,m =m ,s =sec )
    if m :
        return tr ("timing.unit_ms",m =m ,s =sec )
    return tr ("timing.unit_s",s =sec )


class TimingReportDialog (QDialog ):


    def __init__ (self ,stats :TimingStats ,parent =None ):
        super ().__init__ (parent )
        self .setWindowTitle (tr ("timing.title"))
        self .setMinimumSize (620 ,560 )
        layout =QVBoxLayout (self )

        if stats .truncated :
            warn =QLabel (f"⚠ {stats .truncation_reason }")
            warn .setWordWrap (True )
            warn .setObjectName ("warning_hint")
            layout .addWidget (warn )

        summary =QLabel (
        tr ("timing.summary",lines =stats .total_lines ,
        total =_fmt_seconds (stats .total_seconds ),
        avg =stats .average_seconds_per_line )
        )
        summary .setTextFormat (Qt .TextFormat .RichText )
        summary .setStyleSheet ("font-size:13px; padding:4px 0;")
        layout .addWidget (summary )

        note =QLabel (tr ("timing.note"))
        note .setWordWrap (True )
        note .setObjectName ("hint_text")
        layout .addWidget (note )

        char_box =QGroupBox (tr ("timing.by_character"))
        char_l =QVBoxLayout (char_box )
        char_table =QTableWidget ()
        char_table .setColumnCount (3 )
        char_table .setHorizontalHeaderLabels ([tr ("timing.col_character"),tr ("timing.col_lines"),tr ("timing.col_time")])
        char_table .horizontalHeader ().setSectionResizeMode (0 ,QHeaderView .ResizeMode .Stretch )
        rows =sorted (stats .per_character_seconds .items (),key =lambda kv :-kv [1 ])
        char_table .setRowCount (len (rows ))
        for r ,(name ,secs )in enumerate (rows ):
            char_table .setItem (r ,0 ,QTableWidgetItem (name ))
            char_table .setItem (r ,1 ,QTableWidgetItem (str (stats .per_character_lines .get (name ,0 ))))
            char_table .setItem (r ,2 ,QTableWidgetItem (_fmt_seconds (secs )))
        char_table .setMaximumHeight (160 )
        char_l .addWidget (char_table )
        layout .addWidget (char_box )

        scene_box =QGroupBox (tr ("timing.by_scene"))
        scene_l =QVBoxLayout (scene_box )
        scene_table =QTableWidget ()
        scene_table .setColumnCount (2 )
        scene_table .setHorizontalHeaderLabels ([tr ("timing.col_scene"),tr ("timing.col_time")])
        scene_table .horizontalHeader ().setSectionResizeMode (0 ,QHeaderView .ResizeMode .Stretch )
        srows =sorted (stats .per_scene_seconds .items (),key =lambda kv :-kv [1 ])
        scene_table .setRowCount (len (srows ))
        for r ,(name ,secs )in enumerate (srows ):
            scene_table .setItem (r ,0 ,QTableWidgetItem (name ))
            scene_table .setItem (r ,1 ,QTableWidgetItem (_fmt_seconds (secs )))
        scene_table .setMaximumHeight (140 )
        scene_l .addWidget (scene_table )
        layout .addWidget (scene_box )

        longest_box =QGroupBox (tr ("timing.longest_lines"))
        longest_l =QVBoxLayout (longest_box )
        longest_table =QTableWidget ()
        longest_table .setColumnCount (3 )
        longest_table .setHorizontalHeaderLabels ([tr ("timing.col_character"),tr ("timing.col_text"),tr ("timing.col_time")])
        longest_table .horizontalHeader ().setSectionResizeMode (1 ,QHeaderView .ResizeMode .Stretch )
        longest_table .setRowCount (len (stats .longest_lines ))
        for r ,(name ,text ,secs )in enumerate (stats .longest_lines ):
            longest_table .setItem (r ,0 ,QTableWidgetItem (name ))
            longest_table .setItem (r ,1 ,QTableWidgetItem (text ))
            longest_table .setItem (r ,2 ,QTableWidgetItem (_fmt_seconds (secs )))
        longest_l .addWidget (longest_table )
        layout .addWidget (longest_box ,1 )

        buttons =QDialogButtonBox (QDialogButtonBox .StandardButton .Close )
        buttons .rejected .connect (self .reject )
        close_btn =buttons .button (QDialogButtonBox .StandardButton .Close )
        if close_btn is not None :
            close_btn .clicked .connect (self .reject )
        layout .addWidget (buttons )
