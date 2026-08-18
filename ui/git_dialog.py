
from PyQt6 .QtWidgets import (
QDialog ,QVBoxLayout ,QHBoxLayout ,QLabel ,QPushButton ,QListWidget ,
QListWidgetItem ,QTextEdit ,QLineEdit ,QMessageBox ,QTabWidget ,QWidget ,
QSplitter ,QFileDialog ,QCheckBox ,QGroupBox ,QProgressDialog 
)
from PyQt6 .QtCore import Qt ,QThread ,pyqtSignal 
import os 

from core import git_manager as git 
from core .git_credentials_store import GitCredentials 
from ui .git_graph_widget import GitGraphWidget ,wrap_in_scroll_area 
from ui .git_scene_commit_dialog import GitScenePartialCommitDialog 
from core .i18n import tr 


class _GitOpWorker (QThread ):

    done =pyqtSignal (bool ,str )

    def __init__ (self ,fn ,parent =None ):
        super ().__init__ (parent )
        self .fn =fn 

    def run (self ):
        try :
            ok ,out =self .fn ()
        except Exception as e :
            ok ,out =False ,tr ("git.unexpected_error",error =e )
        self .done .emit (ok ,out )


class _GitCommitProgressWorker (QThread ):

    done =pyqtSignal (bool ,str )
    progress =pyqtSignal (int ,int )

    def __init__ (self ,repo_dir :str ,message :str ,parent =None ):
        super ().__init__ (parent )
        self .repo_dir =repo_dir 
        self .message =message 

    def run (self ):
        try :
            ok ,out =git .commit_all_with_progress (
            self .repo_dir ,self .message ,
            on_progress =lambda done ,total :self .progress .emit (done ,total ),
            )
        except Exception as e :
            ok ,out =False ,tr ("git.unexpected_error",error =e )
        self .done .emit (ok ,out )


class GitPanelDialog (QDialog ):
    def _run_with_progress (self ,fn ,busy_text :str )->"tuple[bool, str]":

        progress =QProgressDialog (busy_text ,None ,0 ,0 ,self )
        progress .setWindowTitle (tr ("git.dialog_title"))
        progress .setWindowModality (Qt .WindowModality .WindowModal )
        progress .setMinimumDuration (300 )
        progress .setCancelButton (None )

        result ={}
        worker =_GitOpWorker (fn ,self )

        def on_done (ok ,out ):
            result ["ok"]=ok 
            result ["out"]=out 
            progress .close ()

        worker .done .connect (on_done )
        worker .start ()
        progress .exec ()
        worker .wait ()
        return result .get ("ok",False ),result .get ("out","")

    def _run_commit_with_progress (self ,message :str )->"tuple[bool, str]":

        progress =QProgressDialog (tr ("git.progress_prepare"),None ,0 ,0 ,self )
        progress .setWindowTitle (tr ("git.commit_progress_title"))
        progress .setWindowModality (Qt .WindowModality .WindowModal )
        progress .setMinimumDuration (300 )
        progress .setCancelButton (None )

        result ={}
        worker =_GitCommitProgressWorker (self .repo_dir ,message ,self )

        def on_progress (done ,total ):
            if total :
                progress .setMaximum (total )
                progress .setValue (done )
                progress .setLabelText (tr ("git.progress_adding",done =done ,total =total ))
            else :
                progress .setLabelText (tr ("git.progress_committing"))

        def on_done (ok ,out ):
            result ["ok"]=ok 
            result ["out"]=out 
            progress .close ()

        worker .progress .connect (on_progress )
        worker .done .connect (on_done )
        worker .start ()
        progress .exec ()
        worker .wait ()
        return result .get ("ok",False ),result .get ("out","")

    def __init__ (self ,repo_dir :str ,base_dir :str ,parent =None ,project_file :str =""):
        super ().__init__ (parent )
        self .repo_dir =repo_dir 
        self .base_dir =base_dir 
        self .project_file =project_file 
        self .creds =GitCredentials .load (base_dir )
        if self .creds .git_exe_path :
            git .set_manual_git_path (self .creds .git_exe_path )
        self .setWindowTitle (tr ("git.panel_title"))
        self .setMinimumSize (860 ,620 )
        self ._setup_ui ()
        self ._refresh_all ()

    def _setup_ui (self ):
        layout =QVBoxLayout (self )

        self .repo_lbl =QLabel (tr ("git.repo_label",path =self .repo_dir ))
        self .repo_lbl .setObjectName ("hint_text")
        layout .addWidget (self .repo_lbl )

        self ._git_ok =git .is_git_available ()
        if not self ._git_ok :
            warn =QLabel (tr ("git.not_found_warning"))
            warn .setWordWrap (True )
            warn .setObjectName ("warning_banner")
            warn .setStyleSheet ("padding:8px;")
            layout .addWidget (warn )

            path_row =QHBoxLayout ()
            self .git_path_edit =QLineEdit (self .creds .git_exe_path )
            self .git_path_edit .setPlaceholderText (tr ("git.path_placeholder"))
            path_row .addWidget (self .git_path_edit ,1 )
            btn_browse =QPushButton (tr ("git.browse"))
            btn_browse .clicked .connect (self ._browse_git_path )
            path_row .addWidget (btn_browse )
            btn_apply =QPushButton (tr ("git.apply_and_check"))
            btn_apply .setObjectName ("btn_primary")
            btn_apply .clicked .connect (self ._apply_git_path )
            path_row .addWidget (btn_apply )
            layout .addLayout (path_row )

        tabs =QTabWidget ()
        layout .addWidget (tabs ,1 )

        commit_tab =QWidget ()
        tabs .addTab (commit_tab ,tr ("git.tab_snapshots"))
        self ._setup_commit_tab (commit_tab )

        graph_tab =QWidget ()
        tabs .addTab (graph_tab ,tr ("git.tab_graph"))
        self ._setup_graph_tab (graph_tab )

        tags_tab =QWidget ()
        tabs .addTab (tags_tab ,tr ("git.tab_tags"))
        self ._setup_tags_tab (tags_tab )

        remote_tab =QWidget ()
        tabs .addTab (remote_tab ,tr ("git.tab_github"))
        self ._setup_remote_tab (remote_tab )

        lfs_tab =QWidget ()
        tabs .addTab (lfs_tab ,tr ("git.tab_lfs"))
        self ._setup_lfs_tab (lfs_tab )

        tabs .setEnabled (self ._git_ok )

        bottom =QHBoxLayout ()
        bottom .addStretch ()
        btn_close =QPushButton (tr ("git.close"))
        btn_close .clicked .connect (self .accept )
        bottom .addWidget (btn_close )
        layout .addLayout (bottom )



    def _setup_commit_tab (self ,tab :QWidget ):
        layout =QVBoxLayout (tab )

        self .init_row =QHBoxLayout ()
        self .init_lbl =QLabel ()
        self .init_lbl .setWordWrap (True )
        self .init_row .addWidget (self .init_lbl ,1 )
        self .btn_init =QPushButton (tr ("git.init_repo_here"))
        self .btn_init .clicked .connect (self ._on_init )
        self .init_row .addWidget (self .btn_init )
        self .btn_gitignore =QPushButton (tr ("git.update_gitignore"))
        self .btn_gitignore .setToolTip (tr ("git.gitignore_tooltip"))
        self .btn_gitignore .clicked .connect (self ._on_update_gitignore )
        self .init_row .addWidget (self .btn_gitignore )
        layout .addLayout (self .init_row )

        split =QSplitter (Qt .Orientation .Vertical )

        top =QWidget ()
        top_l =QVBoxLayout (top )
        top_l .addWidget (QLabel (tr ("git.unsaved_changes_label")))
        self .status_list =QListWidget ()
        self .status_list .setMaximumHeight (120 )
        top_l .addWidget (self .status_list )

        commit_row =QHBoxLayout ()
        self .commit_msg_edit =QLineEdit ()
        self .commit_msg_edit .setPlaceholderText (tr ("git.commit_msg_placeholder"))
        commit_row .addWidget (self .commit_msg_edit ,1 )
        btn_commit =QPushButton (tr ("git.make_snapshot"))
        btn_commit .setObjectName ("btn_primary")
        btn_commit .clicked .connect (self ._on_commit )
        commit_row .addWidget (btn_commit )
        top_l .addLayout (commit_row )

        btn_partial_row =QHBoxLayout ()
        btn_partial_row .addStretch ()
        btn_partial =QPushButton (tr ("git.commit_by_scenes"))
        btn_partial .setToolTip (tr ("git.commit_by_scenes_tooltip"))
        btn_partial .clicked .connect (self ._on_partial_commit )
        btn_partial_row .addWidget (btn_partial )
        top_l .addLayout (btn_partial_row )

        bottom =QWidget ()
        bottom_l =QVBoxLayout (bottom )
        bottom_l .addWidget (QLabel (tr ("git.history_label")))
        self .log_list =QListWidget ()
        bottom_l .addWidget (self .log_list ,1 )

        log_btn_row =QHBoxLayout ()
        btn_diff =QPushButton (tr ("git.show_diff"))
        btn_diff .clicked .connect (self ._on_show_diff )
        log_btn_row .addWidget (btn_diff )
        btn_restore =QPushButton (tr ("git.restore_version"))
        btn_restore .clicked .connect (self ._on_restore )
        log_btn_row .addWidget (btn_restore )
        bottom_l .addLayout (log_btn_row )

        split .addWidget (top )
        split .addWidget (bottom )
        split .setSizes ([220 ,320 ])
        layout .addWidget (split ,1 )

    def _setup_graph_tab (self ,tab :QWidget ):
        layout =QVBoxLayout (tab )
        layout .addWidget (QLabel (tr ("git.graph_hint")))
        self .graph_widget =GitGraphWidget ()
        self .graph_widget .commit_selected .connect (self ._on_graph_commit_selected )
        layout .addWidget (wrap_in_scroll_area (self .graph_widget ),1 )

        btn_row =QHBoxLayout ()
        btn_row .addStretch ()
        btn_diff =QPushButton (tr ("git.show_selected_diff"))
        btn_diff .clicked .connect (self ._on_graph_show_diff )
        btn_row .addWidget (btn_diff )
        layout .addLayout (btn_row )

    def _on_graph_commit_selected (self ,commit_hash :str ):
        self ._graph_selected_hash =commit_hash 

    def _on_graph_show_diff (self ):
        commit_hash =getattr (self ,"_graph_selected_hash",None )
        if not commit_hash :
            QMessageBox .information (self ,tr ("git.nothing_selected_title"),tr ("git.click_commit_in_graph"))
            return 
        diff_text =git .diff_commit (self .repo_dir ,commit_hash )
        dlg =QDialog (self )
        dlg .setWindowTitle (tr ("git.commit_diff_title"))
        dlg .resize (760 ,560 )
        l =QVBoxLayout (dlg )
        view =QTextEdit ()
        view .setReadOnly (True )
        view .setObjectName ("code_box")
        view .setStyleSheet ("font-size:11px;")
        view .setPlainText (diff_text )
        l .addWidget (view )
        dlg .exec ()

    def _setup_tags_tab (self ,tab :QWidget ):
        layout =QVBoxLayout (tab )
        layout .addWidget (QLabel (tr ("git.tags_hint")))
        self .tags_list =QListWidget ()
        layout .addWidget (self .tags_list ,1 )

        form =QHBoxLayout ()
        self .tag_name_edit =QLineEdit ()
        self .tag_name_edit .setPlaceholderText (tr ("git.tag_name_placeholder"))
        form .addWidget (self .tag_name_edit )
        self .tag_msg_edit =QLineEdit ()
        self .tag_msg_edit .setPlaceholderText (tr ("git.tag_msg_placeholder"))
        form .addWidget (self .tag_msg_edit ,1 )
        layout .addLayout (form )

        btn_row =QHBoxLayout ()
        btn_create =QPushButton (tr ("git.create_tag_head"))
        btn_create .setObjectName ("btn_primary")
        btn_create .clicked .connect (self ._on_create_tag )
        btn_row .addWidget (btn_create )
        btn_delete =QPushButton (tr ("git.delete_selected"))
        btn_delete .clicked .connect (self ._on_delete_tag )
        btn_row .addWidget (btn_delete )
        btn_push_one =QPushButton (tr ("git.push_selected"))
        btn_push_one .clicked .connect (self ._on_push_tag )
        btn_row .addWidget (btn_push_one )
        btn_push_all =QPushButton (tr ("git.push_all_tags"))
        btn_push_all .clicked .connect (self ._on_push_all_tags )
        btn_row .addWidget (btn_push_all )
        layout .addLayout (btn_row )

    def _selected_tag (self )->str :
        item =self .tags_list .currentItem ()
        return item .data (1000 )if item else ""

    def _on_create_tag (self ):
        name =self .tag_name_edit .text ().strip ()
        if not name :
            QMessageBox .information (self ,tr ("git.enter_name_title"),tr ("git.enter_tag_name"))
            return 
        ok ,out =git .create_tag (self .repo_dir ,name ,self .tag_msg_edit .text ().strip ())
        if not ok :
            QMessageBox .warning (self ,tr ("git.tag_create_failed"),out )
        else :
            self .tag_name_edit .clear ()
            self .tag_msg_edit .clear ()
        self ._refresh_all ()

    def _on_delete_tag (self ):
        name =self ._selected_tag ()
        if not name :
            return 
        confirm =QMessageBox .question (self ,tr ("git.delete_tag_title"),tr ("git.delete_tag_confirm",name =name ))
        if confirm !=QMessageBox .StandardButton .Yes :
            return 
        ok ,out =git .delete_tag (self .repo_dir ,name )
        if not ok :
            QMessageBox .warning (self ,tr ("git.error_title"),out )
        self ._refresh_all ()

    def _on_push_tag (self ):
        name =self ._selected_tag ()
        if not name :
            QMessageBox .information (self ,tr ("git.nothing_selected_title"),tr ("git.select_tag_in_list"))
            return 
        ok ,out =git .push_tag (self .repo_dir ,name ,token =self .creds .token or None )
        if not ok :
            QMessageBox .warning (self ,tr ("git.tag_push_failed"),out )
        else :
            QMessageBox .information (self ,tr ("git.done_title"),out or tr ("git.tag_pushed"))

    def _on_push_all_tags (self ):
        ok ,out =git .push_all_tags (self .repo_dir ,token =self .creds .token or None )
        if not ok :
            QMessageBox .warning (self ,tr ("git.tags_push_failed"),out )
        else :
            QMessageBox .information (self ,tr ("git.done_title"),out or tr ("git.tags_pushed"))

    def _setup_lfs_tab (self ,tab :QWidget ):
        layout =QVBoxLayout (tab )
        self .lfs_status_lbl =QLabel ()
        self .lfs_status_lbl .setWordWrap (True )
        layout .addWidget (self .lfs_status_lbl )

        info =QLabel (tr ("git.lfs_info"))
        info .setWordWrap (True )
        info .setObjectName ("hint_text")
        layout .addWidget (info )

        patterns_box =QGroupBox (tr ("git.file_types_box"))
        pl =QVBoxLayout (patterns_box )
        self .lfs_checks ={}
        for pattern in git .LFS_RECOMMENDED_PATTERNS :
            cb =QCheckBox (pattern )
            self .lfs_checks [pattern ]=cb 
            pl .addWidget (cb )
        layout .addWidget (patterns_box )

        btn_row =QHBoxLayout ()
        btn_apply =QPushButton (tr ("git.lfs_apply"))
        btn_apply .setObjectName ("btn_primary")
        btn_apply .clicked .connect (self ._on_lfs_apply )
        btn_row .addWidget (btn_apply )
        btn_row .addStretch ()
        layout .addLayout (btn_row )

        layout .addWidget (QLabel (tr ("git.lfs_status_label")))
        self .lfs_status_view =QTextEdit ()
        self .lfs_status_view .setReadOnly (True )
        self .lfs_status_view .setStyleSheet (
        "font-family: Consolas, monospace; font-size:11px; background:#1a1a21; color:#ccc;")
        layout .addWidget (self .lfs_status_view ,1 )

    def _on_lfs_apply (self ):
        selected =[p for p ,cb in self .lfs_checks .items ()if cb .isChecked ()]
        if not selected :
            QMessageBox .information (self ,tr ("git.nothing_to_do_title"),tr ("git.select_file_type"))
            return 
        ok ,out =git .lfs_track (self .repo_dir ,selected )
        if not ok :
            QMessageBox .warning (self ,tr ("git.failed_title"),out )
        else :
            QMessageBox .information (
            self ,tr ("git.done_title"),
            tr ("git.lfs_applied_note",out =out )
            )
        self ._refresh_lfs ()

    def _refresh_lfs (self ):
        available =git .is_lfs_available ()
        if not available :
            self .lfs_status_lbl .setText (tr ("git.lfs_not_found"))
            self .lfs_status_lbl .setObjectName ("warning_hint")
        else :
            self .lfs_status_lbl .setText (tr ("git.lfs_installed"))
            self .lfs_status_lbl .setObjectName ("success_hint")
        tracked =set (git .lfs_tracked_patterns (self .repo_dir ))if git .is_repo (self .repo_dir )else set ()
        for pattern ,cb in self .lfs_checks .items ():
            cb .blockSignals (True )
            cb .setChecked (pattern in tracked )
            cb .blockSignals (False )
        if git .is_repo (self .repo_dir ):
            self .lfs_status_view .setPlainText (git .lfs_status (self .repo_dir )if available else "")

    def _browse_git_path (self ):
        filt =f"git.exe (git.exe);;{tr ('git.all_files')} (*)"if os .name =="nt"else f"{tr ('git.all_files')} (*)"
        path ,_ =QFileDialog .getOpenFileName (self ,tr ("git.pick_git_exe_title"),"",filt )
        if path :
            self .git_path_edit .setText (path )

    def _apply_git_path (self ):
        path =self .git_path_edit .text ().strip ()
        git .set_manual_git_path (path )
        if git .is_git_available ():
            self .creds .git_exe_path =path 
            self .creds .save (self .base_dir )
            QMessageBox .information (self ,tr ("git.done_title"),tr ("git.found_and_connected"))
            self .close ()
            new_dlg =GitPanelDialog (self .repo_dir ,self .base_dir ,self .parent ())
            new_dlg .exec ()
        else :
            QMessageBox .warning (self ,tr ("git.failed_title"),tr ("git.not_starting_at_path",path =path ))

    def _on_update_gitignore (self ):
        ok ,added =git .merge_recommended_gitignore (self .repo_dir )
        if not ok :
            QMessageBox .critical (self ,tr ("git.error_title"),tr ("git.gitignore_write_failed"))
        elif added ==0 :
            QMessageBox .information (self ,tr ("git.done_title"),tr ("git.gitignore_already_ok"))
        else :
            QMessageBox .information (self ,tr ("git.done_title"),tr ("git.gitignore_lines_added",count =added ))
        self ._refresh_all ()

    def _on_init (self ):
        ok ,out =git .init_repo (self .repo_dir )
        if not ok :
            QMessageBox .critical (self ,tr ("git.error_title"),out )
        self ._refresh_all ()

    def _on_commit (self ):
        msg =self .commit_msg_edit .text ().strip ()or tr ("git.default_commit_msg")
        ok ,out =self ._run_commit_with_progress (msg )
        if not ok :
            QMessageBox .warning (self ,tr ("git.snapshot_failed"),out or tr ("git.no_changes_to_snapshot"))
        else :
            self .commit_msg_edit .clear ()
        self ._refresh_all ()

    def _on_partial_commit (self ):
        if not self .project_file :
            QMessageBox .information (
            self ,tr ("git.unavailable_title"),
            tr ("git.no_project_file")
            )
            return 
        abs_path =os .path .join (self .repo_dir ,self .project_file )
        if not os .path .isfile (abs_path ):
            QMessageBox .warning (self ,tr ("git.file_not_found_title"),tr ("git.project_file_not_found",path =abs_path ))
            return 
        dlg =GitScenePartialCommitDialog (self .repo_dir ,abs_path ,self .project_file ,self )
        dlg .exec ()
        self ._refresh_all ()

    def _selected_commit (self ):
        row =self .log_list .currentRow ()
        if row <0 :
            return None 
        item =self .log_list .item (row )
        return item .data (1000 )if item else None 

    def _on_show_diff (self ):
        commit_hash =self ._selected_commit ()
        if not commit_hash :
            return 
        diff_text =git .diff_commit (self .repo_dir ,commit_hash )
        dlg =QDialog (self )
        dlg .setWindowTitle (tr ("git.snapshot_diff_title"))
        dlg .resize (760 ,560 )
        l =QVBoxLayout (dlg )
        view =QTextEdit ()
        view .setReadOnly (True )
        view .setObjectName ("code_box")
        view .setStyleSheet ("font-size:11px;")
        view .setPlainText (diff_text )
        l .addWidget (view )
        dlg .exec ()

    def _on_restore (self ):
        commit_hash =self ._selected_commit ()
        if not commit_hash :
            return 
        item =self .log_list .item (self .log_list .currentRow ())
        confirm =QMessageBox .question (
        self ,tr ("git.restore_version_title"),
        tr ("git.restore_confirm",name =item .text ()),
        QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No ,
        )
        if confirm !=QMessageBox .StandardButton .Yes :
            return 
        ok ,out =git .restore_to_commit (self .repo_dir ,commit_hash )
        if not ok :
            QMessageBox .critical (self ,tr ("git.error_title"),out )
        else :
            QMessageBox .information (
            self ,tr ("git.done_title"),
            tr ("git.restored_note")
            )
        self ._refresh_all ()



    def _setup_remote_tab (self ,tab :QWidget ):
        layout =QVBoxLayout (tab )

        info =QLabel (tr ("git.token_info"))
        info .setWordWrap (True )
        info .setObjectName ("hint_text")
        layout .addWidget (info )

        layout .addWidget (QLabel (tr ("git.remote_url_label")))
        self .remote_url_edit =QLineEdit (self .creds .github_url )
        layout .addWidget (self .remote_url_edit )

        layout .addWidget (QLabel (tr ("git.token_label")))
        self .token_edit =QLineEdit (self .creds .token )
        self .token_edit .setEchoMode (QLineEdit .EchoMode .Password )
        layout .addWidget (self .token_edit )

        btn_save_remote =QPushButton (tr ("git.save_and_link_remote"))
        btn_save_remote .clicked .connect (self ._on_save_remote )
        layout .addWidget (btn_save_remote )

        self .remote_status_lbl =QLabel ()
        self .remote_status_lbl .setObjectName ("hint_text")
        layout .addWidget (self .remote_status_lbl )

        btn_row =QHBoxLayout ()
        btn_push =QPushButton (tr ("git.push"))
        btn_push .setObjectName ("btn_primary")
        btn_push .clicked .connect (self ._on_push )
        btn_row .addWidget (btn_push )
        btn_pull =QPushButton (tr ("git.pull"))
        btn_pull .clicked .connect (self ._on_pull )
        btn_row .addWidget (btn_pull )
        layout .addLayout (btn_row )

        self .remote_log =QTextEdit ()
        self .remote_log .setReadOnly (True )
        self .remote_log .setObjectName ("code_box")
        self .remote_log .setStyleSheet ("font-size:11px;")
        layout .addWidget (self .remote_log ,1 )

    def _on_save_remote (self ):
        self .creds .github_url =self .remote_url_edit .text ().strip ()
        self .creds .token =self .token_edit .text ().strip ()
        self .creds .save (self .base_dir )
        if self .creds .github_url and git .is_repo (self .repo_dir ):
            ok ,out =git .set_remote_url (self .repo_dir ,self .creds .github_url )
            self .remote_log .append (out or ("OK"if ok else tr ("git.error_title")))
        self ._refresh_remote_status ()

    def _on_push (self ):
        ok ,out =git .push (self .repo_dir ,token =self .creds .token or None )
        self .remote_log .append (("[push] "+out )if out else "[push] OK")
        if not ok :
            QMessageBox .warning (self ,tr ("git.push_failed"),out )

    def _on_pull (self ):
        ok ,out =git .pull (self .repo_dir ,token =self .creds .token or None )
        self .remote_log .append (("[pull] "+out )if out else "[pull] OK")
        if not ok :
            QMessageBox .warning (self ,tr ("git.pull_failed"),out )
        else :
            QMessageBox .information (self ,tr ("git.done_title"),tr ("git.pull_done_note"))
        self ._refresh_all ()

    def _refresh_remote_status (self ):
        url =git .get_remote_url (self .repo_dir )if self ._git_ok and git .is_repo (self .repo_dir )else None 
        self .remote_status_lbl .setText (tr ("git.current_remote",url =url or tr ('git.not_configured')))



    def _refresh_all (self ):
        if not self ._git_ok :
            return 
        repo_exists =git .is_repo (self .repo_dir )
        self .btn_init .setEnabled (not repo_exists )
        self .init_lbl .setText (
        tr ("git.repo_initialized")if repo_exists 
        else tr ("git.repo_not_initialized")
        )

        self .status_list .clear ()
        self .log_list .clear ()
        if not repo_exists :
            self ._refresh_remote_status ()
            return 

        for st in git .get_status (self .repo_dir ):
            self .status_list .addItem (QListWidgetItem (f"[{st .code }] {st .path }"))

        for c in git .get_log (self .repo_dir ):
            item =QListWidgetItem (f"{c .date }  {c .short_hash }  {c .message }")
            item .setData (1000 ,c .commit_hash )
            self .log_list .addItem (item )

        self .graph_widget .set_commits (git .get_log_graph (self .repo_dir ))

        self .tags_list .clear ()
        for t in git .list_tags (self .repo_dir ):
            item =QListWidgetItem (f"{t .name }   {t .date }   {t .commit_hash [:8 ]}   {t .message }")
            item .setData (1000 ,t .name )
            self .tags_list .addItem (item )

        self ._refresh_lfs ()

        self ._refresh_remote_status ()
