#! /usr/bin/env python

from Tkinter import Tk, StringVar, Menu,Frame,Label,Button,Scrollbar,Listbox,Entry
from Tkinter import Y,END,TOP,BOTH,LEFT,RIGHT,VERTICAL,SINGLE,NONE,W
import ttk
import Tkinter as tk
import tkFileDialog
import tkMessageBox
import ttkSimpleDialog as ttkSimpleDialog
import os
import sys
import ConfigParser
import shutil
import json
import copy
import string
import pp_paths

from pp_edititem import EditItem
from pp_medialist import MediaList
from pp_showlist import ShowList
from pp_utils import Monitor
from pp_options import ed_options
from pp_validate import Validator
from pp_definitions import PPdefinitions
from pp_oscconfig import OSCConfig,OSCEditor, OSCUnitType
from tkconversions import *
from ttkStatusBar import StatusBar

# **************************
# Pi Presents Editor Class
# *************************

class PPEditor(object):

    # ***************************************
    # INIT
    # ***************************************

    def __init__(self):
    
        self.editor_issue="1.3"

        # get command options
        self.command_options=ed_options()

        # get directory holding the code
        self.pp_dir=sys.path[0]
            
        if not os.path.exists(self.pp_dir+os.sep+"pp_editor.py"):
            tkMessageBox.showwarning("Pi Presents","Bad Application Directory")
            exit()
            
          
        # Initialise logging
        Monitor.log_path=self.pp_dir
        self.mon=Monitor()
        self.mon.init()
        
        Monitor.classes  = ['PPEditor','EditItem','Validator']

        Monitor.log_level = int(self.command_options['debug'])

        self.mon.log (self, "Pi Presents Editor is starting")
        self.mon.log (self," OS and separator " + os.name +'  ' + os.sep)
        self.mon.log(self,"sys.path[0] -  location of code: code "+sys.path[0])


        # set up the gui
 
        # root is the Tkinter root widget
        self.root = tk.Tk()
        self.root.title("Editor for Pi Presents")

        style = ttkStyle()
        style.theme_use('clam')

        self.root.resizable(True,True)

        # define response to main window closing
        self.root.protocol ("WM_DELETE_WINDOW", self.app_exit)

        # bind some display fields
        self.filename = tk.StringVar()
        self.display_selected_track_title = tk.StringVar()
        self.display_show = tk.StringVar()


        # define menu
        menubar = ttkMenu(self.root)
        self.root['menu'] = menubar # needed for keyboard navigation to work properly

        # Profile menu
        profilemenu = menubar.add_submenu('Profile', 0, accelerator='Alt-p')
        profilemenu.add_command('Open...',        0, self.open_existing_profile)
        profilemenu.add_command('Validate',       0, self.e_validate_profile)

        ptypemenu = profilemenu.add_submenu('New from Template', 0)
        ptypemenu.add_command('Exhibit',          0, self.new_exhibit_profile)
        ptypemenu.add_command('Media Show',       0, self.new_mediashow_profile)
        ptypemenu.add_command('Art Media Show',   0, self.new_artmediashow_profile)
        ptypemenu.add_command('Menu',             1, self.new_menu_profile)
        ptypemenu.add_command('Presentation',     0, self.new_presentation_profile)
        ptypemenu.add_command('Interactive',      0, self.new_interactive_profile)
        ptypemenu.add_command('Live Show',        0, self.new_liveshow_profile)
        ptypemenu.add_command('Art Live Show',    2, self.new_artliveshow_profile)
        ptypemenu.add_command('RadioButton Show', 0, self.new_radiobuttonshow_profile)
        ptypemenu.add_command('Hyperlink Show',   0, self.new_hyperlinkshow_profile)
        ptypemenu.add_command('Blank',            0, self.new_blank_profile)
        
        # Show menu
        showmenu = menubar.add_submenu('Show', 0, accelerator='Alt-s')
        showmenu_item = ttkMenu(None)
        showmenu_item.add_command('Delete (and medialist)',   0, self.e_remove_show_and_medialist)
        showmenu_item.add_command('Delete (leave medialist)', 2, self.e_remove_show)
        showmenu_item.add_command('Edit',                     0, self.m_edit_show)
        showmenu_item.add_command('Copy To...',               0, self.copy_show)
        showmenu.add_section(showmenu_item, "", use_sep=False)

        showmenu_add = ttkMenu(None)
        showmenu_add.add_command('Add...', underline=None, command=None, state=DISABLED)
        showmenu_add.add_command('  Media Show',      2, self.add_mediashow)
        showmenu_add.add_command('  Art Media Show',  2, self.add_artmediashow)
        showmenu_add.add_command('  Menu',            3, self.add_menushow)
        showmenu_add.add_command('  Live Show',       2, self.add_liveshow)
        showmenu_add.add_command('  Art Live Show',   4, self.add_artliveshow)
        showmenu_add.add_command('  Hyperlink Show',  2, self.add_hyperlinkshow)
        showmenu_add.add_command('  RadioButton Show',2, self.add_radiobuttonshow)
        showmenu.add_section(showmenu_add, "", use_sep=True)
        
        # Medialist menu
        medialistmenu = menubar.add_submenu('MediaList', 0, accelerator='Alt-m')
        medialistmenu_item = ttkMenu(None)
        medialistmenu_add  = ttkMenu(None)
        medialistmenu_item.add_command('Delete',       0, self.e_remove_medialist)
        medialistmenu_item.add_command('Copy To...',   0, self.copy_medialist)
        medialistmenu_add.add_command('Add',           0, self.e_add_medialist)
        medialistmenu.add_section(medialistmenu_item, "", use_sep=False)
        medialistmenu.add_section(medialistmenu_add,  "", use_sep=False)

        # Track menu
        trackmenu = menubar.add_submenu('Track', 0, accelerator='Alt-t')
        trackmenu_item = ttkMenu(None)
        trackmenu_item.add_command('Delete',           0, self.remove_track)
        trackmenu_item.add_command('Edit',             0, self.m_edit_track)
        trackmenu.add_section(trackmenu_item, "", use_sep=False)

        trackmenu_add = ttkMenu(None)
        trackmenu_add.add_command('Add...',         underline=None, command=None, state=DISABLED)
        trackmenu_add.add_command('  From Dir...',     7, self.add_tracks_from_dir)
        trackmenu_add.add_command('  From File...',    7, self.add_track_from_file)
        trackmenu_add.add_command('  Video',           2, self.new_video_track)
        trackmenu_add.add_command('  Audio',           2, self.new_audio_track)
        trackmenu_add.add_command('  Image',           2, self.new_image_track)
        trackmenu_add.add_command('  Web',             2, self.new_web_track)
        trackmenu_add.add_command('  Message',         2, self.new_message_track)
        trackmenu_add.add_command('  Show',            2, self.new_show_track)
        trackmenu_add.add_command('  Menu Background', 7, self.new_menu_track)
        trackmenu.add_section(trackmenu_add, "", use_sep=True)

        # Tools and options menus
        toolsmenu = menubar.add_submenu('Tools', 3, accelerator='Alt-l')
        toolsmenu.add_command('Update All',      0, self.update_all)
        
        optionsmenu = menubar.add_submenu('Options', 0, accelerator='Alt-o')
        optionsmenu.add_command('Edit',          0, self.edit_options)

        helpmenu = menubar.add_submenu('Help', 0, accelerator='Alt-h')
        helpmenu.add_command('Help',             0, self.show_help)
        helpmenu.add_command('About',            0, self.about)         
        self.root.config(menu=menubar)

        # define frames

        root_frame=ttkFrame(self.root)
        root_frame.pack(fill=BOTH, expand=True)

        # top = menu, bottom = main frame for content
        top_frame=ttkFrame(root_frame)
        top_frame.pack(side=TOP, fill=X, expand=False)
        bottom_frame=ttkFrame(root_frame)

        bottom_frame.pack(side=TOP, fill=BOTH, expand=1)        

        # left   = shows list, media list
        # middle = show buttons
        # right  = tracks list
        # updown = track buttons
        left_frame=ttkFrame(bottom_frame, padx=5)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True)
        notebook = ttk.Notebook(left_frame)
        shows_tab=ttkFrame(notebook)
        medialist_tab = ttkFrame(notebook)
        notebook.add(shows_tab, text="Shows")
        notebook.add(medialist_tab, text="Medialists")
        notebook.pack(side=LEFT, fill=BOTH, expand=True)
        self.notebook = notebook
        
        #middle_frame=ttkFrame(bottom_frame,padx=5)
        #middle_frame.pack(side=LEFT, fill=BOTH, expand=False)
        right_frame=ttkFrame(bottom_frame,padx=5,pady=10)
        right_frame.pack(side=LEFT, fill=BOTH, expand=True)
        updown_frame=ttkFrame(bottom_frame,padx=5)
        updown_frame.pack(side=LEFT)
        
        #ttk.Style().configure("TFrame", background="green")
        #ttk.Style().configure("TButton", background="red")

        tracks_title_frame=ttkFrame(right_frame, padding=4)
        tracks_title_frame.pack(side=TOP, fill=X, expand=False)
        self.tracks_label = ttk.Label(tracks_title_frame, text="Tracks in Selected Medialist")
        self.tracks_label.configure(justify=CENTER)
        self.tracks_label.pack(side=TOP, fill=X, expand=False)
        tracks_frame=ttkFrame(right_frame, padding=0)
        tracks_frame.pack(side=TOP, fill=BOTH, expand=True)
        
        shows_frame=ttkFrame(shows_tab, padding=0)
        shows_frame.pack(side=TOP, fill=BOTH, expand=True)
        medialists_frame=ttkFrame(medialist_tab, padding=0)
        medialists_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        self.root.config(menu=menubar)

        # define buttons 

        add_button = ttkButton(shows_tab, width = 5, height = 2, text='Edit',
                            fg='black', command = self.m_edit_show, bg="light grey")
        add_button.pack(side=BOTTOM)
        
        add_button = ttkButton(updown_frame, width = 5, height = 1, text='Add',
                            fg='black', command = self.add_track_from_file, bg="light grey")
        add_button.pack(side=TOP)
        add_button = ttkButton(updown_frame, width = 5, height = 1, text='Edit',
                            fg='black', command = self.m_edit_track, bg="light grey")
        add_button.pack(side=TOP)
        add_button = ttkButton(updown_frame, width = 5, height = 1, text='Up',
                            fg='black', command = self.move_track_up, bg="light grey")
        add_button.pack(side=TOP)
        add_button = ttkButton(updown_frame, width = 5, height = 1, text='Down',
                            fg='black', command = self.move_track_down, bg="light grey")
        add_button.pack(side=TOP)
        add_button = ttkButton(updown_frame, width = 5, height = 1, text='Del',
                              fg='black', command = self.remove_track, bg="light grey")
        add_button.pack(side=TOP, pady=20)

        # define display of showlist 
        scrollbar = ttk.Scrollbar(shows_frame, orient=tk.VERTICAL)
        self.shows_display = ttkListbox(shows_frame, selectmode=SINGLE, height=7,
                                    width = 40, yscrollcommand=scrollbar.set,
                                    on_item_popup=showmenu, off_item_popup=showmenu_add)
        scrollbar.config(command=self.shows_display.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.shows_display.pack(side=LEFT, fill=BOTH, expand=1)
        self.shows_display.bind("<<TreeviewSelect>>", self.e_select_show)
        self.shows_display.bind("<Double-Button-1>", self.m_edit_show)
        self.shows_display.bind("<space>", self.m_edit_show)
        self.shows_display.bind("<Delete>", self.e_remove_show_and_medialist)
        self.shows_display.bind("+", lambda e: showsmenu_add.tk_popup(e.x_root, e.y_root))
    
        # define display of medialists
        scrollbar = ttk.Scrollbar(medialists_frame, orient=tk.VERTICAL)
        self.medialists_display = ttkListbox(medialists_frame, selectmode=SINGLE, height=7,
                                    width = 40, yscrollcommand=scrollbar.set,
                                    on_item_popup=medialistmenu, off_item_popup=medialistmenu_add,
                                    columns=('show'))
        scrollbar.config(command=self.medialists_display.yview)
        self.medialists_display.column('#0')
        self.medialists_display.heading('#0', text="Filename")
        self.medialists_display.column('show', width=75, stretch=False)
        self.medialists_display.heading('show', text="Show")
        scrollbar.pack(side=RIGHT, fill=Y)
        self.medialists_display.pack(side=LEFT,  fill=BOTH, expand=1)
        self.medialists_display.bind("<<TreeviewSelect>>", self.e_select_medialist)
        self.medialists_display.bind("<Delete>", self.e_remove_medialist)
        self.medialists_display.bind("+", lambda e: medialist_add.tk_popup(e.x_root, e.y_root))

        # define display of tracks
        scrollbar = ttk.Scrollbar(tracks_frame, orient=tk.VERTICAL)
        self.tracks_display = ttkListbox(tracks_frame, selectmode=SINGLE, height=15,
                                    width = 40, yscrollcommand=scrollbar.set,
                                    on_item_popup=trackmenu, off_item_popup=trackmenu_add)
        scrollbar.config(command=self.tracks_display.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tracks_display.pack(side=LEFT,fill=BOTH, expand=1)
        self.tracks_display.bind("<<TreeviewSelect>>", self.e_select_track)
        self.tracks_display.bind("<Double-Button-1>", self.m_edit_track)
        self.tracks_display.bind("<space>", self.m_edit_track)
        self.tracks_display.bind("<Delete>", self.remove_track)
        self.tracks_display.bind("<Control-Up>", self.track_OnCtrlUp)
        self.tracks_display.bind("<Control-Down>", self.track_OnCtrlDown)
        self.tracks_display.bind("+", lambda e: trackmenu_add.tk_popup(e.x_root, e.y_root))

        # define window sizer
        sz = ttk.Sizegrip(root_frame)
        sz.pack(side=RIGHT)
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(0, weight=1)

        # define status bar
        self.status = StatusBar(root_frame)
        self.status.set("Click here to validate. Double click to validate and show report.")
        self.status.pack(side=BOTTOM, fill=X)
        self.status.bind("<Button-1>", self.e_validate_profile)
        self.status.bind("<Double-Button-1>", self.e_validate_profile_with_results)

        # initialise editor options class and OSC config class
        self.options=Options(self.pp_dir) # creates options file in code directory if necessary
        self.osc_config=OSCConfig()

        self.root.bind("<Escape>", self.escape_keypressed)
        self.root.bind("<Control-t>", self.switch_tabs)
        
        # initialise variables
        self.init()
        
        # and enter Tkinter event loop
        self.root.mainloop()


    # ***************************************
    # INIT AND EXIT
    # ***************************************
    def escape_keypressed(self, event=None):
        # possibly with somewhat annoying prompt here... or not.
        self.app_exit()

    def set_window_geometry(self):
        try:
            option = self.options.geometry.replace('x', ',').replace('+', ',')
            w,h,x,y = tuple(int(x) for x in option[:].split(','))
            ws = self.root.winfo_screenwidth()
            hs = self.root.winfo_screenheight()
            w = min(ws, w)
            h = min(hs, h)
            # if the location goes off screen, center the window
            if x + w > ws: x = (ws-w)/2
            if y + w > hs: y = (hs-h)/2
            self.root.geometry("{0}x{1}+{2}+{3}".format(w, h, x, y))
        except:
            pass

    def save_window_geometry(self):
        self.options.geometry = self.root.geometry()
        self.options.save()
        pass

    def app_exit(self):
        self.save_window_geometry()
        self.root.destroy()
        exit()

    def init(self):
        self.options.read()
        self.set_window_geometry()

        # get home path from -o option (kept separate from self.options.pp_home_dir)
        # or fall back to self.options.pp_home_dir
        if self.command_options['home'] != '':
            self.pp_home_dir = pp_paths.get_home(self.command_options['home'])
            if self.pp_home_dir is None:
                self.end('error','Failed to find pp_home')
        else:
            self.pp_home_dir = self.options.pp_home_dir

        # get profile path from -p option
        # pp_profile_dir is the full path to the directory that contains 
        # pp_showlist.json and other files for the profile
        if self.command_options['profile'] != '':
            self.pp_profile_dir = pp_paths.get_profile_dir(self.pp_home_dir, self.command_options['profile'])
            if self.pp_profile_dir is None:
                self.end('error','Failed to find profile')
        else:
            self.pp_profile_dir=''

        self.pp_profiles_offset = self.options.pp_profiles_offset
        self.initial_media_dir = self.options.initial_media_dir
        self.mon.log(self,"Data Home from options is "+self.pp_home_dir)
        self.mon.log(self,"Current Profiles Offset from options is "+self.pp_profiles_offset)
        self.mon.log(self,"Initial Media from options is "+self.initial_media_dir)
        self.osc_config_file = ''
        self.current_medialist=None
        self.current_showlist=None
        self.current_show=None
        self.shows_display.delete(0,END)
        self.medialists_display.delete(0,END)
        self.tracks_display.delete(0,END)
        # if we were given a profile on the command line, open it
        if self.command_options['profile'] != '':
            self.open_profile(self.pp_profile_dir)


    # ***************************************
    # MISCELLANEOUS
    # ***************************************

    def edit_options(self, event=None):
        """edit the options then read them from file"""
        eo = OptionsDialog(self.root, self.options, 'Edit Options')
        if eo.result is True: self.init()

    def show_help (self, event=None):
        tkMessageBox.showinfo("Help","Read 'manual.pdf'")

    def about (self, event=None):
        tkMessageBox.showinfo("About","Editor for Pi Presents Profiles\n"
                              +"For profile version: " + self.editor_issue + "\nAuthor: Ken Thompson"
                              +"\nWebsite: http://pipresents.wordpress.com/")

    def e_validate_profile(self, event=None):
        self.validate_profile(False)

    def e_validate_profile_with_results(self, event=None):
        self.validate_profile(True)

    def validate_profile(self, show_results=False):
        val =Validator()
        self.status.set("{0}", "Validating...")
        val.validate_profile(self.root,self.pp_dir,self.pp_home_dir,
            self.pp_profile_dir,self.editor_issue,show_results)
        errors, warnings = val.get_results()
        if errors == 1: error_text = "1 error"
        else:           error_text = "{0} errors".format(errors)
        if warnings == 1: warn_text = "1 warning"
        else:             warn_text = "{0} warnings".format(warnings)
        if errors > 0:
            self.status.set_error("{0}, {1}. Double click for details.", error_text, warn_text)
        elif warnings > 0:
            self.status.set_warning("{0}, {1}. Double click for details.", error_text, warn_text)
        else:
            self.status.set_info("{0}, {1}.", error_text, warn_text)

    def switch_tabs(self, event=None):
        seleccted_tab = self.notebook.select()
        index = self.notebook.tabs().index(seleccted_tab)
        if index == 0: 
            self.notebook.select(1)
            self.medialists_display.focus_set()
        else: 
            self.notebook.select(0)
            self.shows_display.focus_set()


    # **************
    # OSC CONFIGURATION
    # **************

    def create_osc(self):
        if self.pp_profile_dir=='':
            return
        if self.osc_config.read(self.osc_config_file) is False:
            iodir=self.pp_profile_dir+os.sep+'pp_io_config'
            if not os.path.exists(iodir):
                os.makedirs(iodir)
            self.osc_config.create(self.osc_config_file)

    def edit_osc(self):
        if self.osc_config.read(self.osc_config_file) is False:
            # print 'no config file'
            return
        osc_ut=OSCUnitType(self.root,self.osc_config.this_unit_type)
        self.req_unit_type=osc_ut.result
        if self.req_unit_type != None:
            # print self.req_unit_type
            eosc = OSCEditor(self.root, self.osc_config_file,self.req_unit_type,'Edit OSC Configuration')
            
    def delete_osc(self):
        if self.osc_config.read(self.osc_config_file) is False:
            return
        os.rename(self.osc_config_file,self.osc_config_file+'.bak')


    # **************
    # PROFILES
    # **************

    def open_existing_profile(self, event=None):
        initial_dir=self.pp_home_dir+os.sep+"pp_profiles"+self.pp_profiles_offset
        if os.path.exists(initial_dir) is False:
            self.mon.err(self,"Profiles directory not found: " + initial_dir + "\n\nHint: Data Home option must end in pp_home")
            return
        dir_path=tkFileDialog.askdirectory(initialdir=initial_dir)
        # dir_path="C:\Users\Ken\pp_home\pp_profiles\\ttt"
        if len(dir_path)>0:
            self.open_profile(dir_path)

    def open_profile(self,dir_path):
        showlist_file = dir_path + os.sep + "pp_showlist.json"
        if os.path.exists(showlist_file) is False:
            self.mon.err(self,"Not a Profile: " + dir_path + "\n\nHint: Have you opened the profile directory?")
            return
        self.pp_profile_dir = dir_path
        self.root.title("Editor for Pi Presents - "+ self.pp_profile_dir)
        if self.open_showlist(self.pp_profile_dir) is False:
            self.init()
            return
        self.open_medialists(self.pp_profile_dir)
        self.refresh_tracks_display()
        self.osc_config_file=self.pp_profile_dir+os.sep+'pp_io_config'+os.sep+'osc.cfg'
        # select the first item in the shows list and focus the keyboard to the list
        item = self.shows_display.select(0)
        self.highlight_shows_display()
        self.shows_display.focus_set()

    def new_profile(self,profile):
        d = Edit1Dialog(self.root,"New Profile","Name", "")
        if d .result  is  None:
            return
        name=str(d.result)
        if name == "":
            tkMessageBox.showwarning("New Profile","Name is blank")
            return
        to = self.pp_home_dir + os.sep + "pp_profiles"+ self.pp_profiles_offset + os.sep + name
        if os.path.exists(to) is  True:
            tkMessageBox.showwarning( "New Profile","Profile exists\n(%s)" % to )
            return
        shutil.copytree(profile, to, symlinks=False, ignore=None)
        self.open_profile(to)

    def new_exhibit_profile(self, event=None):
        profile = self.pp_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_exhibit_1p3'
        self.new_profile(profile)

    def new_interactive_profile(self, event=None):
        profile = self.pp_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_interactive_1p3'
        self.new_profile(profile)

    def new_menu_profile(self, event=None):
        profile = self.pp_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_menu_1p3'
        self.new_profile(profile)

    def new_presentation_profile(self, event=None):
        profile = self.pp_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_presentation_1p3'
        self.new_profile(profile)

    def new_blank_profile(self, event=None):
        profile = self.pp_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep +"ppt_blank_1p3"
        self.new_profile(profile)

    def new_mediashow_profile(self, event=None):
        profile = self.pp_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_mediashow_1p3'
        self.new_profile(profile)
        
    def new_liveshow_profile(self, event=None):
        profile = self.pp_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_liveshow_1p3'
        self.new_profile(profile)

    def new_artmediashow_profile(self, event=None):
        profile = self.pp_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_artmediashow_1p3'
        self.new_profile(profile)
        
    def new_artliveshow_profile(self, event=None):
        profile = self.pp_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_artliveshow_1p3'
        self.new_profile(profile)

    def new_radiobuttonshow_profile(self, event=None):
        profile = self.pp_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_radiobuttonshow_1p3'
        self.new_profile(profile)

    def new_hyperlinkshow_profile(self, event=None):
        profile = self.pp_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_hyperlinkshow_1p3'
        self.new_profile(profile)


    # ***************************************
    # Shows
    # ***************************************

    def open_showlist(self,profile_dir):
        showlist_file = profile_dir + os.sep + "pp_showlist.json"
        if os.path.exists(showlist_file) is False:
            self.mon.err(self,"showlist file not found at " + profile_dir + "\n\nHint: Have you opened the profile directory?")
            self.app_exit()
        self.current_showlist=ShowList()
        self.current_showlist.open_json(showlist_file)
        if float(self.current_showlist.sissue())<float(self.editor_issue) or  (self.command_options['forceupdate']  is  True and float(self.current_showlist.sissue()) == float(self.editor_issue)):
            self.update_profile()
            self.mon.err(self,"Version of profile has been updated to "+self.editor_issue+", please re-open")
            return False
        if float(self.current_showlist.sissue())>float(self.editor_issue):
            self.mon.err(self,"Version of profile is greater than editor, must exit")
            self.app_exit()
        self.refresh_shows_display()
        return True

    def save_showlist(self,showlist_dir):
        if self.current_showlist is not None:
            showlist_file = showlist_dir + os.sep + "pp_showlist.json"
            self.current_showlist.save_list(showlist_file)

    def add_mediashow(self, event=None):
        self.add_show(PPdefinitions.new_shows['mediashow'])

    def add_liveshow(self, event=None):
        self.add_show(PPdefinitions.new_shows['liveshow'])

    def add_radiobuttonshow(self, event=None):
        self.add_show(PPdefinitions.new_shows['radiobuttonshow'])

    def add_hyperlinkshow(self, event=None):
        self.add_show(PPdefinitions.new_shows['hyperlinkshow'])

    def add_artliveshow(self, event=None):
        self.add_show(PPdefinitions.new_shows['artliveshow'])

    def add_artmediashow(self, event=None):
        self.add_show(PPdefinitions.new_shows['artmediashow'])
        
    def add_menushow(self, event=None):
        self.add_show(PPdefinitions.new_shows['menu'])

    def add_start(self):  
        self.add_show(PPdefinitions.new_shows['start'])

    def add_show(self,default):
        # append it to the showlist and then add the medialist
        if self.current_showlist is not None:
            d = Edit1Dialog(self.root,"AddShow","Show Reference", "")
            if d.result  is  None:
                return
            name=str(d.result)
            if name == "":
                tkMessageBox.showwarning("Add Show","Name is blank")
                return
                                         
            if self.current_showlist.index_of_show(name) != -1:
                tkMessageBox.showwarning("Add Show","A Show with this name already exists")
                return            
            copied_show=self.current_showlist.copy(default,name)
            mediafile=self.add_medialist(name, True)
            if mediafile != '':
                copied_show['medialist']=mediafile
            self.current_showlist.append(copied_show)
            # select the show just added
            index = self.current_showlist.length()-1
            self.save_showlist(self.pp_profile_dir)
            self.current_showlist.select(index)
            self.refresh_shows_display()

    def e_remove_show_and_medialist(self, event=None):
        if self.current_showlist is None:             return
        if self.current_showlist.length() == 0:       return
        if not self.current_showlist.show_is_selected(): return
        showlist = self.current_showlist
        show = showlist.selected_show()
        medialist = show['medialist']
        if medialist == '': medialist = "(none)"
        msg = "Do you want to delete these?\n  Show: {0}\n  Medialist: {1}".format(show['title'],  medialist)
        if tkMessageBox.askokcancel("Delete Show and Medialist", msg):
            self.remove_medialist()
            self.remove_show(showlist.selected_show_index())
            
    def e_remove_show(self, event=None):
        if self.current_showlist is None:             return
        if self.current_showlist.length() == 0:       return
        if not self.current_showlist.show_is_selected(): return
        showlist = self.current_showlist
        show = showlist.selected_show()
        msg = "Do you want to delete this?\n  Show: {0}".format(show['title'])
        if tkMessageBox.askokcancel("Delete Show", msg):
            self.remove_show(showlist.selected_show_index())
            
    def remove_show(self, index):
                self.current_showlist.remove(index)
                self.save_showlist(self.pp_profile_dir)
                # highlight the next (or previous item on the list)
                if index >= self.current_showlist.length(): 
                    index = self.current_showlist.length() - 1
                self.current_showlist.select(index)
                self.refresh_shows_display()

    def show_refs(self):
        _show_refs=[]
        for index in range(self.current_showlist.length()):
            if self.current_showlist.show(index)['show-ref'] != "start":
                _show_refs.append(copy.deepcopy(self.current_showlist.show(index)['show-ref']))
        return _show_refs
 
    def refresh_shows_display(self):
        self.shows_display.delete(0,self.shows_display.size())
        for index in range(self.current_showlist.length()):
            self.shows_display.insert(END, self.current_showlist.show(index)['title']+"   ["+self.current_showlist.show(index)['show-ref']+"]")        
        self.highlight_shows_display()
        if self.options.autovalidate: self.validate_profile()

    def highlight_shows_display(self):
        ctl = self.shows_display
        if self.current_showlist.show_is_selected():
            index = self.current_showlist.selected_show_index()
            ctl.select(index)
        if len(ctl.selection()) > 0:
            iid = ctl.selection()[0]
            ctl.focus(iid)
            ctl.see(ctl.curselection()[0])

    def e_select_show(self,event):
        if len(self.shows_display.selection()) == 0:
            self.select_show(None)
            return
        if self.current_showlist<>None and self.current_showlist.length()>0:
            mouse_item_index=int(event.widget.curselection()[0])
            self.select_show(mouse_item_index)

    def select_show(self, index):
        selected_show = self.current_showlist.selected_show_index()
        if selected_show == index: return
        if index is None: index = -1
        self.current_showlist.select(index)
        if index == -1: 
            # a medialist has been selected that doesn't have a corresponding show
            if len(self.shows_display.selection()) == 0: return
            self.shows_display.selection_clear()
            return
        self.highlight_shows_display()
        # select the related medialist
        show = self.current_showlist.selected_show()
        medialist_index = -1
        if 'medialist' in show:
            medialist = show['medialist']
            medialist_index = self.medialists_display.indexof(medialist)
        self.select_medialist(medialist_index)

    def copy_show(self, event=None):
        if  self.current_showlist is not None and self.current_showlist.show_is_selected():
            self.add_show(self.current_showlist.selected_show())
        
    def m_edit_show(self, *args, **kwargs):
        self.edit_show(PPdefinitions.show_types,PPdefinitions.show_field_specs)

    def edit_show(self,show_types,field_specs):
        if self.current_showlist is not None and self.current_showlist.show_is_selected():
            field_content = self.current_showlist.selected_show()
            # auto-upgrade show to include plugin so it appears in editor box
            if not 'plugin' in field_content and field_content['show-ref'] == 'start':
                field_content['plugin'] = ''
            d=EditItem(self.root,"Edit Show",self.current_showlist.selected_show(),show_types,field_specs,self.show_refs(),
                       self.initial_media_dir,self.pp_home_dir,'show')
            if d.result  is  True:
                self.save_showlist(self.pp_profile_dir)
                self.refresh_shows_display()
            self.shows_display.focus_set() # retain focus on the list after editing
 

    # ***************************************
    #   Medialists
    # ***************************************

    def open_medialists(self,profile_dir):
        self.medialists = []
        files = os.listdir(profile_dir)
        if files: files.sort()
        for this_file in files:
            if this_file.endswith(".json") and this_file not in ('pp_showlist.json','schedule.json'):
                self.medialists = self.medialists + [this_file]
        self.medialists_display.delete(0,self.medialists_display.size())
        for item in self.medialists:
            showname = self.get_showname_for_medialist(item)
            self.medialists_display.insert(END, item, iid=item, values=(showname))
        self.current_medialists_index=-1
        self.current_medialist=None

    def open_medialist(self, name):
        medialist = MediaList('ordered')
        if not medialist.open_list(self.pp_profile_dir + os.sep + name, self.current_showlist.sissue()):
            self.mon.err(self,"The medialist and the showlist are different versions: \n  Medialist: " + name)
            self.app_exit()        
        return medialist

    def e_add_medialist(self, event=None):
        d = Edit1Dialog(self.root,"Add Medialist", "File", "")
        if d.result:
            name=str(d.result)
            if name=="":
                tkMessageBox.showwarning("Add Medialist", "The name cannot be blank.")
                return ''
            self.add_medialist(name, False)

    def add_medialist(self, name, link_to_show):
        if name is None:
            d = Edit1Dialog(self.root,"Add Medialist","File", "")
            if d.result  is  None:
                return ''
            name=str(d.result)
            if name == "":
                tkMessageBox.showwarning("Add medialist","Name is blank")
                return ''
            
        if not name.endswith(".json"):
            name=name+(".json")
                
        path = self.pp_profile_dir + os.sep + name
        if os.path.exists(path) is  True:
            msg = "The medialist file already exists:\n  {0}".format(path)
            if link_to_show:
                msg += "\n\nDo you want the show to use it anyway?"
                if tkMessageBox.askyesno("Add Medialist", msg):
                    return name
                else: return ''
            else:
                tkMessageBox.showwarning("Add Medialist", msg + "\n\n  Aborting")
        nfile = open(path,'wb')
        nfile.write("{")
        nfile.write("\"issue\":  \""+self.editor_issue+"\",\n")
        nfile.write("\"tracks\": [")
        nfile.write("]")
        nfile.write("}")
        nfile.close()
        # append it to the list
        self.medialists.append(copy.deepcopy(name))
        # add title to medialists display
        showname = self.get_showname_for_medialist(item)
        self.medialists_display.insert(END, item, iid=item, values=(showname))
        # and set it as the selected medialist
        self.medialists_display.select(name)
        #self.refresh_medialists_display()
        return name

    def e_remove_medialist(self, event=None):
        if self.current_medialist is not None:
            name = self.medialists[self.current_medialists_index]
            if tkMessageBox.askokcancel("Delete Medialist","Do you want to delete this?\n  Medialist: " + name):
                self.remove_medialist()

    def remove_medialist(self):
        name = self.medialists[self.current_medialists_index]
        os.remove(self.pp_profile_dir+ os.sep + name)
        self.medialists.remove(name)
        #self.open_medialists(self.pp_profile_dir)
        # highlight the next (or previous item on the list)
        index = self.current_medialists_index
        if index >= len(self.medialists): 
            index = len(self.medialists) - 1
        self.current_medialists_index = index
        self.current_medialist = self.open_medialist(self.medialists[index])
        self.refresh_medialists_display()
        self.refresh_tracks_display()

    def copy_medialist(self,to_file=None):
        if self.current_medialist is not None:
            #from_file= self.current_medialist 
            from_file= self.medialists[self.current_medialists_index]
            if to_file is None:
                d = Edit1Dialog(self.root,"Copy Medialist","File", "")
                if d.result  is  None:
                    return ''
                to_file=str(d.result)
                if to_file == "":
                    tkMessageBox.showwarning("Copy medialist","Name is blank")
                    return ''
                
            success_file = self.copy_medialist_file(from_file,to_file)
            if success_file =='':
                return ''

            # append it to the list
            self.medialists.append(copy.deepcopy(success_file))
            # add title to medialists display
            self.medialists_display.insert(END, success_file)
            # and reset  selected medialist
            self.current_medialist=None
            self.refresh_medialists_display()
            self.refresh_tracks_display()
            return success_file
        else:
            return ''

    def copy_medialist_file(self,from_file,to_file):
        if not to_file.endswith(".json"):
            to_file+=(".json")
                
        to_path = self.pp_profile_dir + os.sep + to_file
        if os.path.exists(to_path) is  True:
            tkMessageBox.showwarning("Copy medialist","Medialist file exists\n(%s)" % to_path)
            return ''
        
        from_path= self.pp_profile_dir + os.sep + from_file
        if os.path.exists(from_path) is  False:
            tkMessageBox.showwarning("Copy medialist","Medialist file not found\n(%s)" % from_path)
            return ''

        shutil.copy(from_path,to_path)
        return to_file

    def remove_medialist(self):
        if self.current_medialist is not None:
            if tkMessageBox.askokcancel("Delete Medialist","Delete Medialist"):
                os.remove(self.pp_profile_dir+ os.sep + self.medialists[self.current_medialists_index])
                self.open_medialists(self.pp_profile_dir)
                self.refresh_medialists_display()
                self.refresh_tracks_display()

    def e_select_medialist(self, event=None):
        if len(self.medialists_display.selection()) == 0:
            self.select_medialist(None)
            return
        selection = event.widget.curselection()
        if selection:
            mouse_item_index=int(selection[0])
            self.select_medialist(mouse_item_index)

    def select_medialist(self,index):
        selected_medialist = self.current_medialists_index
        if selected_medialist == index: return
        if index is None: index = -1
        self.current_medialists_index = index
        self.current_medialist = self.open_medialist(self.medialists[index])
        if index == -1:
            # if a show has been selected that doesn't have corresponding medialist
            if len(self.medialists_display.selection()) == 0: return
            self.current_medialist = None
            self.medialists_display.selection_clear()
            self.refresh_tracks_display()
            return
        self.refresh_tracks_display()
        self.highlight_medialist_display()
        # select the related show
        if self.current_medialist:
            showname = self.get_showname_for_medialist(self.current_medialist.filename)
            if showname:
                index = self.show_refs().index(showname)+1
                self.select_show(index)
                self.shows_display.select(index)
            else:
                self.select_show(None)

    def refresh_medialists_display(self):
        self.medialists_display.delete(0,END)
        for item in self.medialists:
            showname = self.get_showname_for_medialist(item)
            self.medialists_display.insert(END, item, iid=item, values=(showname))
        self.highlight_medialist_display()

    def get_showname_for_medialist(self, medialist):
        showname = ''
        if self.current_showlist is not None and self.current_showlist.length() > 0:
            for show in self.current_showlist.shows():
                if 'medialist' in show:
                    filename = show['medialist']
                    if filename == medialist:
                        showname = show['show-ref']
        return showname

    def highlight_medialist_display(self):
        ctl = self.medialists_display
        if self.current_medialist is not None:
            index = self.current_medialists_index
            ctl.select(index)
            ctl.see(index)
        if len(ctl.selection()) > 0:
            iid = ctl.selection()[0]
            ctl.focus(iid)
            ctl.see(ctl.curselection()[0])

    def save_medialist(self):
        basefile=self.medialists[self.current_medialists_index]
        # print type(basefile)
        # basefile=str(basefile)
        # print type(basefile)
        medialist_file = self.pp_profile_dir+ os.sep + basefile
        self.current_medialist.save_list(medialist_file)
  
          
    # ***************************************
    #   Tracks
    # ***************************************
          
    def refresh_tracks_display(self, clear_tracks=True):
        if len(self.medialists) > 0 and self.current_medialists_index >= 0:
            medialist = self.medialists[self.current_medialists_index]
        else:
            medialist = "(no medialist selected)"
        self.tracks_label['text'] = "Tracks in %s" % medialist 
        if clear_tracks:
            self.tracks_display.delete(0, self.tracks_display.size())
            if self.current_medialist is not None:
                for index in range(self.current_medialist.length()):
                    if self.current_medialist.track(index)['track-ref'] != "":
                        track_ref_string="  ["+self.current_medialist.track(index)['track-ref']+"]"
                    else:
                        track_ref_string=""
                    self.tracks_display.insert(END, self.current_medialist.track(index)['title']+track_ref_string)        
                if self.tracks_display.size() > 0:
                    self.tracks_display.select(0)
                self.highlight_tracks_display()
        if self.options.autovalidate: self.validate_profile()

    def highlight_tracks_display(self):
        ctl = self.tracks_display
        if self.current_medialist.track_is_selected():
            index = self.current_medialist.selected_track_index()
            ctl.select(index)
        # ensure we have focus so we can use the keyboard to navigate
        if len(ctl.selection()) > 0:
            iid = ctl.selection()[0]
            ctl.focus(iid)
            ctl.see(ctl.curselection()[0])
            
    def e_select_track(self,event):
        if self.current_medialist is not None and self.current_medialist.length()>0:
            selection = event.widget.curselection()
            if len(selection) > 0:
                    mouse_item_index=int(selection[0])
                    self.current_medialist.select(mouse_item_index)
                    self.refresh_tracks_display(clear_tracks = False)

    def m_edit_track(self, *args, **kwargs):
        self.edit_track(PPdefinitions.track_types,PPdefinitions.track_field_specs)

    def edit_track(self,track_types,field_specs):      
        if self.current_medialist is not None and self.current_medialist.track_is_selected():
            d=EditItem(self.root,"Edit Track",self.current_medialist.selected_track(),track_types,field_specs,
                       self.show_refs(),self.initial_media_dir,self.pp_home_dir,'track')
            if d.result  is  True:
                self.save_medialist()
            self.highlight_tracks_display()
            self.tracks_display.focus_set() # retain focus on the list after editing

    def track_OnCtrlUp(self, event=None):
        self.move_track_up()
        return "break"

    def track_OnCtrlDown(self, event=None):
        self.move_track_down()
        return "break" # prevent widget from processing another Down event

    def move_track_up(self, event=None):
        if self.current_medialist is not None and self.current_medialist.track_is_selected():
            self.current_medialist.move_up()
            self.refresh_tracks_display()
            self.save_medialist()

    def move_track_down(self, event=None):
        if self.current_medialist is not None and self.current_medialist.track_is_selected():
            self.current_medialist.move_down()
            self.refresh_tracks_display()
            self.save_medialist()
        
    def new_track(self,fields,values):
        if self.current_medialist is not None:
            # print '\nfields ', fields
            # print '\nvalues ', values
            new_track=copy.deepcopy(fields)
            # print ',\new track ',new_track
            self.current_medialist.append(new_track)
            # print '\nbefore values ',self.current_medialist.print_list()
            if values is not None:
                self.current_medialist.update(self.current_medialist.length()-1,values)
            self.current_medialist.select(self.current_medialist.length()-1)
            self.refresh_tracks_display()
            self.save_medialist()

    def new_message_track(self, event=None):
        self.new_track(PPdefinitions.new_tracks['message'],None)
            
    def new_video_track(self, event=None):
        self.new_track(PPdefinitions.new_tracks['video'],None)
  
    def new_audio_track(self, event=None):
        self.new_track(PPdefinitions.new_tracks['audio'],None)

    def new_web_track(self, event=None):
        self.new_track(PPdefinitions.new_tracks['web'],None)
        
    def new_image_track(self, event=None):
        self.new_track(PPdefinitions.new_tracks['image'],None)

    def new_show_track(self, event=None):
        self.new_track(PPdefinitions.new_tracks['show'],None)

    def new_menu_track(self, event=None):
        self.new_track(PPdefinitions.new_tracks['menu'],None)
 
    def remove_track(self, *args, **kwargs):
        if  self.current_medialist is not None and self.current_medialist.length()>0 and self.current_medialist.track_is_selected():
            track = self.current_medialist.selected_track()
            msg = "Do you want to delete this?\n  Track: {0}".format(track['title'])
            if tkMessageBox.askokcancel("Delete Track", msg):
                index= self.current_medialist.selected_track_index()
                self.current_medialist.remove(index)
                self.save_medialist()
                # highlight the next (or previous) item in the list
                if index >= self.current_medialist.length():
                    index = self.current_medialist.length() - 1
                self.current_medialist.select(index)
                self.refresh_tracks_display()
                
    def add_track_from_file(self, event=None):
        if self.current_medialist is None: return
        # print "initial directory ", self.options.initial_media_dir
        files_path=tkFileDialog.askopenfilename(initialdir=self.options.initial_media_dir, multiple=True)
        # fix for tkinter bug
        files_path =  self.root.tk.splitlist(files_path)
        for file_path in files_path:
            file_path=os.path.normpath(file_path)
            # print "file path ", file_path
            self.add_track(file_path)
        self.save_medialist()

    def add_tracks_from_dir(self, event=None):
        if self.current_medialist is None: return
        image_specs =[PPdefinitions.IMAGE_FILES,PPdefinitions.VIDEO_FILES,PPdefinitions.AUDIO_FILES,
                      PPdefinitions.WEB_FILES,('All files', '*')]
        # last one is ignored in finding files in directory, for dialog box only
        directory=tkFileDialog.askdirectory(initialdir=self.options.initial_media_dir)
        # deal with tuple returned on Cancel
        if len(directory) == 0: return
        # make list of exts we recognise
        exts = []
        for image_spec in image_specs[:-1]:
            image_list=image_spec[1:]
            for ext in image_list:
                exts.append(copy.deepcopy(ext))
        files = os.listdir(directory)
        if files: files.sort()
        for this_file in files:
            (root_file,ext_file)= os.path.splitext(this_file)
            if ext_file.lower() in exts:
                file_path=directory+os.sep+this_file
                # print "file path before ", file_path
                file_path=os.path.normpath(file_path)
                # print "file path after ", file_path
                self.add_track(file_path)
        self.save_medialist()

    def add_track(self,afile):
        relpath = os.path.relpath(afile,self.pp_home_dir)
        # print "relative path ",relpath
        common = os.path.commonprefix([afile,self.pp_home_dir])
        # print "common ",common
        if common.endswith("pp_home")  is  False:
            location = afile
        else:
            location = "+" + os.sep + relpath
            location = string.replace(location,'\\','/')
            # print "location ",location
        (root,title)=os.path.split(afile)
        (root,ext)= os.path.splitext(afile)
        if ext.lower() in PPdefinitions.IMAGE_FILES:
            self.new_track(PPdefinitions.new_tracks['image'],{'title':title,'track-ref':'','location':location})
        elif ext.lower() in PPdefinitions.VIDEO_FILES:
            self.new_track(PPdefinitions.new_tracks['video'],{'title':title,'track-ref':'','location':location})
        elif ext.lower() in PPdefinitions.AUDIO_FILES:
            self.new_track(PPdefinitions.new_tracks['audio'],{'title':title,'track-ref':'','location':location})
        elif ext.lower() in PPdefinitions.WEB_FILES:
            self.new_track(PPdefinitions.new_tracks['web'],{'title':title,'track-ref':'','location':location})
        else:
            self.mon.err(self,afile + " - cannot determine track type, use menu track>new")


    # *********************************************
    # UPDATE PROFILE
    # **********************************************

    def update_all(self, event=None):
        self.init()
        files = os.listdir(self.pp_home_dir+os.sep+'pp_profiles'+self.pp_profiles_offset)
        if files: files.sort()
        for profile_file in files:
            # self.mon.log (self,"Updating "+profile_file)
            self.pp_profile_dir = self.pp_home_dir+os.sep+'pp_profiles'+self.pp_profiles_offset + os.sep + profile_file
            if not os.path.exists(self.pp_profile_dir+os.sep+"pp_showlist.json"):
                tkMessageBox.showwarning("Pi Presents","Not a profile, skipping "+self.pp_profile_dir)
            else:
                self.current_showlist=ShowList()
                self.current_showlist.open_json(self.pp_profile_dir+os.sep+"pp_showlist.json")
                self.mon.log (self,"Version of profile "+ profile_file + ' is ' + self.current_showlist.sissue())
                if float(self.current_showlist.sissue())<float(self.editor_issue):
                    self.mon.log(self,"Version of profile "+profile_file+ "  is being updated to "+self.editor_issue)
                    self.update_profile()
                elif (self.command_options['forceupdate']  is  True and float(self.current_showlist.sissue()) == float(self.editor_issue)):
                    self.mon.log(self, "Forced updating of " + profile_file + ' to '+self.editor_issue)
                    self.update_profile()
                elif float(self.current_showlist.sissue())>float(self.editor_issue):
                    tkMessageBox.showwarning("Pi Presents", "Version of profile " +profile_file+ " is greater than editor, skipping")
                else:
                    self.mon.log(self," Skipping Profile " + profile_file + " It is already up to date ")
        self.init()
        tkMessageBox.showwarning("Pi Presents","All profiles updated")
            
    def update_profile(self):

        self.update_medialists()   # medialists and their tracks
        self.update_shows()         #shows in showlist, also creates menu tracks for 1.2>1.3

    def update_shows(self):
        # open showlist into a list of dictionaries
        self.mon.log (self,"Updating show ")
        ifile  = open(self.pp_profile_dir + os.sep + "pp_showlist.json", 'rb')
        shows = json.load(ifile)['shows']
        ifile.close()

        # special 1.2>1.3 create menu medialists with menu track from show
        #go through shows - if type = menu and version is greater copy its medialist to a new medialist with  name = <show-ref>-menu1p3.json
        for show in shows:
            #create a new medialist medialist != show-ref as menus can't now share medialists
            if show['type']=='menu' and float(self.current_showlist.sissue())<float(self.editor_issue):
                to_file=show['show-ref']+'-menu1p3.json'
                from_file = show['medialist']
                if to_file != from_file:
                    self.copy_medialist_file(from_file,to_file)
                else:
                    self.mon.warn(self, 'medialist file' + to_file + ' already exists, must exit with incomplete update')
                    return False

                #update the reference to the medialist
                show['medialist']=to_file
                
                #delete show fields so they are recreated with new default content
                del show['controls']
                
                # open the  medialist and add the menu track then populate some of its fields from the show
                ifile  = open(self.pp_profile_dir + os.sep + to_file, 'rb')
                tracks = json.load(ifile)['tracks']
                ifile.close()
                
                new_track=copy.deepcopy(PPdefinitions.new_tracks['menu'])
                tracks.append(copy.deepcopy(new_track))

                # copy menu parameters from menu show to menu track and init values of some              
                self.transfer_show_params(show,tracks,'menu-track',("entry-colour","entry-font", "entry-select-colour", 
                                                                    "hint-colour", "hint-font", "hint-text", "hint-x","hint-y",
                                                                    "menu-bullet", "menu-columns", "menu-direction", "menu-guidelines",
                                                                    "menu-horizontal-padding", "menu-horizontal-separation", "menu-icon-height", "menu-icon-mode",
                                                                    "menu-icon-width", "menu-rows", "menu-strip", "menu-strip-padding",  "menu-text-height", "menu-text-mode", "menu-text-width",
                                                                     "menu-vertical-padding", "menu-vertical-separation",
                                                                    "menu-window"))
                                          
                # and save the medialist
                dic={'issue':self.editor_issue,'tracks':tracks}
                ofile  = open(self.pp_profile_dir + os.sep + to_file, "wb")
                json.dump(dic,ofile,sort_keys=True,indent=1)
                # end for show in shows

        #update the fields in  all shows
        replacement_shows=self.update_shows_in_showlist(shows)
        dic={'issue':self.editor_issue,'shows':replacement_shows}
        ofile  = open(self.pp_profile_dir + os.sep + "pp_showlist.json", "wb")
        json.dump(dic,ofile,sort_keys=True,indent=1)
        return True

    def transfer_show_params(self,show,tracks,track_ref,fields):
        # find the menu track in medialist
        for index,track in enumerate(tracks):
            if track['track-ref']== 'menu-track':
                break
            
        #update some fields with new default content
        tracks[index]['links']=PPdefinitions.new_tracks['menu']['links']

        #transfer values from show to track
        for field in fields:
            tracks[index][field]=show[field]
            # print show[field], tracks[index][field]
            pass

    def update_medialists(self):
        # UPDATE MEDIALISTS AND THEIR TRACKS
        files = os.listdir(self.pp_profile_dir)
        if files: files.sort()
        for this_file in files:
            if this_file.endswith(".json") and this_file not in  ('pp_showlist.json','schedule.json'):
                self.mon.log (self,"Updating medialist " + this_file)
                # open a medialist and update its tracks
                ifile  = open(self.pp_profile_dir + os.sep + this_file, 'rb')
                tracks = json.load(ifile)['tracks']
                ifile.close()
                replacement_tracks=self.update_tracks(tracks)
                dic={'issue':self.editor_issue,'tracks':replacement_tracks}
                ofile  = open(self.pp_profile_dir + os.sep + this_file, "wb")
                json.dump(dic,ofile,sort_keys=True,indent=1)       

    def update_tracks(self,old_tracks):
        # get correct spec from type of field
        replacement_tracks=[]
        for old_track in old_tracks:
            # print '\nold track ',old_track
            track_type=old_track['type']
            #update if new tracks has the track type otherwise skip
            if track_type in PPdefinitions.new_tracks:
                spec_fields=PPdefinitions.new_tracks[track_type]
                left_overs=dict()
                # go through track and delete fields not in spec
                for key in old_track.keys():
                    if key in spec_fields:
                        left_overs[key]=old_track[key]
                # print '\n leftovers',left_overs
                replacement_track=copy.deepcopy(PPdefinitions.new_tracks[track_type])
                # print '\n before update', replacement_track
                replacement_track.update(left_overs)
                # print '\nafter update',replacement_track
                replacement_tracks.append(copy.deepcopy(replacement_track))
        return replacement_tracks

    def update_shows_in_showlist(self,old_shows):
        # get correct spec from type of field
        replacement_shows=[]
        for old_show in old_shows:
            show_type=old_show['type']
            ## menu to menushow
            spec_fields=PPdefinitions.new_shows[show_type]
            left_overs=dict()
            # go through track and delete fields not in spec
            for key in old_show.keys():
                if key in spec_fields:
                    left_overs[key]=old_show[key]
            # print '\n leftovers',left_overs
            replacement_show=copy.deepcopy(PPdefinitions.new_shows[show_type])
            replacement_show.update(left_overs)
            replacement_shows.append(copy.deepcopy(replacement_show))
        return replacement_shows                

 
# *************************************
# EDIT 1 DIALOG CLASS
# ************************************

class Edit1Dialog(ttkSimpleDialog.Dialog):

    def __init__(self, parent, title, label, default):
        # save the extra args to instance variables
        self.label_1 = label
        self.default_1 = default     
        # and call the base class _init_which uses the args in body
        ttkSimpleDialog.Dialog.__init__(self, parent, title)


    def body(self, master):
        ttk.Label(master, text=self.label_1).grid(row=0)
        self.field1 = ttk.Entry(master)
        self.field1.grid(row=0, column=1)
        self.field1.insert(0,self.default_1)
        return self.field1 # initial focus on title


    def apply(self):
        self.result= self.field1.get()
        return self.result


# ***************************************
# pp_editor OPTIONS CLASS
# ***************************************

class Options(object):

    def __init__(self,app_dir):

        # define options for Editor
        self.pp_home_dir =""   # home directory containing profile to be edited.
        self.initial_media_dir =""   # initial directory for open playlist      
        self.debug = False  # print debug information to terminal

        user_home_dir = os.path.expanduser('~')
        self.defaults = {
            'home': user_home_dir+os.sep+'pp_home',
            'media': user_home_dir,
            'offset': '',
            'autovalidate': 'false',
            'geometry': 'none'
            }
        self.pp_profiles_offset = self.defaults['offset']
        self.autovalidate = self.defaults['autovalidate']
        self.geometry = self.defaults['geometry']
        self.config=ConfigParser.ConfigParser(self.defaults)
        # create an options file if necessary
        self.options_file = app_dir+os.sep+'pp_config'+ os.sep + 'pp_editor.cfg'
        if not os.path.exists(self.options_file):
            self.create()
    
    def read(self):
        """reads options from options file to interface"""
        config = self.config
        config.read(self.options_file)
        if config.has_section('config'):
            self.pp_home_dir       = config.get(       'config', 'home', 0)
            self.initial_media_dir = config.get(       'config', 'media', 0)
            self.pp_profiles_offset= config.get(       'config', 'offset')
            self.autovalidate      = config.getboolean('config', 'autovalidate')
            self.geometry          = config.get(       'config', 'geometry')
        else:
            self.create()

    def create(self):
        config=self.config
        config.add_section('config')
        config.set('config', 'home',         self.defaults['home'])
        config.set('config', 'offset',       self.defaults['offset'])
        config.set('config', 'media',        self.defaults['media'])
        config.set('config', 'autovalidate', self.defaults['autovalidate'])
        with open(self.options_file, 'wb') as config_file:
            config.write(config_file)

    def save(self):
        """ save the output of the options edit dialog to file"""
        config=self.config
        config.set('config', 'home',         self.pp_home_dir)
        config.set('config', 'offset',       self.pp_profiles_offset)
        config.set('config', 'media',        self.initial_media_dir)
        config.set('config', 'autovalidate', self.autovalidate)
        config.set('config', 'geometry',     self.geometry)
        with open(self.options_file, 'wb') as optionsfile:
            config.write(optionsfile)


# *************************************
# PP_EDITOR OPTIONS DIALOG CLASS
# ************************************

class OptionsDialog(ttkSimpleDialog.Dialog):

    def __init__(self, parent, options, title=None, ):
        # instantiate the subclass attributes
        self.options_file=options.options_file
        self.options = options

        # init the super class
        ttkSimpleDialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        self.result=False
        config=ConfigParser.ConfigParser(self.options.defaults)
        config.read(self.options_file)

        ttk.Label(master, text="").grid(row=20, sticky=W)
        ttk.Label(master, text="Pi Presents Data Home:").grid(row=21, sticky=W)
        self.e_home = ttk.Entry(master,width=80)
        self.e_home.grid(row=22)
        self.e_home.insert(0,config.get('config','home',0))

        ttk.Label(master, text="").grid(row=30, sticky=W)
        ttk.Label(master, text="Inital directory for media:").grid(row=31, sticky=W)
        self.e_media = ttk.Entry(master,width=80)
        self.e_media.grid(row=32)
        self.e_media.insert(0,config.get('config','media',0))

        ttk.Label(master, text="").grid(row=40, sticky=W)
        ttk.Label(master, text="Offset for Current Profiles:").grid(row=41, sticky=W)
        self.e_offset = ttk.Entry(master,width=80)
        self.e_offset.grid(row=42)
        self.e_offset.insert(0,config.get('config','offset',0))
        
        ttk.Label(master, text="").grid(row=50, sticky=W)
        self.autovalidate = tk.StringVar()
        self.e_autovalidate = ttk.Checkbutton(master, text="Auto validate", variable = self.autovalidate,
            onvalue="true", offvalue="false")
        self.e_autovalidate.grid(row=51, sticky=W)
        self.autovalidate.set(config.get('config', 'autovalidate'))

        return None    # no initial focus

    def validate(self):
        if os.path.exists(self.e_home.get()) is  False:
            tkMessageBox.showwarning("Pi Presents Editor","Data Home not found")
            return 0
        if os.path.exists(self.e_media.get()) is  False:
            tkMessageBox.showwarning("Pi Presents Editor","Media Directory not found")
            return 0
        if os.path.exists(self.e_home.get()+os.sep+'pp_profiles'+self.e_offset.get()) is  False:
            tkMessageBox.showwarning("Pi Presents Editor","Current Profles directory not found")
            return 0
        return 1

    def apply(self):
        self.save_options()
        self.result=True

    def save_options(self):
        self.options.pp_home_dir = self.e_home.get()
        self.options.initial_media_dir = self.e_media.get()
        self.options.pp_profiles_offset = self.e_offset.get()
        self.options.autovalidate = self.autovalidate.get()
        self.options.save()
        self.result=True
    

# ***************************************
# MAIN
# ***************************************


if __name__  ==  "__main__":
    editor = PPEditor()

