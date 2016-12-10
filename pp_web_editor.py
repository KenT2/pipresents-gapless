#! /usr/bin/env python

"""
14/11/2016 - automatically find the ip address of the Pi
1/12/2016 - wait for network before proceeding (for standalone use)
"""

import os
import sys
import ConfigParser
import shutil
import copy
import string
import remi.gui as gui
from remi import start, App
from pp_network import Network

from remi_plus import OKDialog, OKCancelDialog
from pp_web_edititem import WebEditItem, ColourMap

from pp_medialist import MediaList
from pp_showlist import ShowList
from pp_web_validate import Validator
from pp_definitions import PPdefinitions
from pp_oscwebconfig import OSCConfig,OSCWebEditor, OSCUnitType


class PPWebEditor(App):

    def __init__(self, *args):
        # print 'DOIING _INIT do not use'
        super(PPWebEditor, self).__init__(*args)
        

    def main(self):
        # print 'DOING MAIN executed once when server starts'
        # ***************************************
        # INIT
        # ***************************************
        self.editor_issue="1.3"

        # get directory holding the code
        self.editor_dir=sys.path[0]

        ColourMap().init()
        
        # initialise editor options OSC config class, and OSC editors
        self.eo=Options()
        self.eo.init_options(self.editor_dir)
        self.osc_config=OSCConfig()
        self.osc_ute= OSCUnitType()

        
        # initialise variables
        self.init() 

        # BUILD THE GUI
        # frames
        root = gui.Widget(width=900,height=500) #1
        root.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)         
        top_frame=gui.Widget(width=900,height=40)#1
        top_frame.set_layout_orientation(gui.Widget.LAYOUT_HORIZONTAL)
        bottom_frame=gui.Widget(width=900,height=300)#1
        bottom_frame.set_layout_orientation(gui.Widget.LAYOUT_HORIZONTAL)       
        root.append(top_frame)
        root.append(bottom_frame)

        left_frame=gui.Widget(width=350,height=400)#1
        left_frame.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)
        left_frame.style['margin']='10px'
        middle_frame=gui.VBox(width=50,height=300)#1
        middle_frame.style['margin']='10px'
        # middle_frame.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)   
        right_frame=gui.Widget(width=350,height=400)#1
        right_frame.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)   
        updown_frame=gui.VBox(width=50,height=300)#1
        updown_frame.style['margin']='10px'
        # updown_frame.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)   

        bottom_frame.append(left_frame)
        bottom_frame.append(middle_frame)
        bottom_frame.append(right_frame)
        bottom_frame.append(updown_frame)

        #menu
        menu = gui.Menu(width=700, height=30)
        top_frame.append(menu)

        #profile menu
        profile_menu = gui.MenuItem('Profile',width=80, height=30)
        profile_open_menu = gui.MenuItem('Open',width=120, height=30)
        profile_open_menu.set_on_click_listener(self,'open_existing_profile')
        profile_validate_menu = gui.MenuItem('Validate',width=120, height=30)
        profile_validate_menu.set_on_click_listener(self, 'validate_profile')
        profile_new_menu = gui.MenuItem('New',width=120, height=30)
        profile_menu.append(profile_open_menu)
        profile_menu.append(profile_validate_menu)
        profile_menu.append(profile_new_menu)

        pmenu = gui.MenuItem('Exhibit',width=150, height=30)
        pmenu.set_on_click_listener(self, 'new_exhibit_profile')
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Media Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'new_mediashow_profile')
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Art Media Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'new_artmediashow_profile')
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Menu',width=150, height=30)
        pmenu.set_on_click_listener(self, 'new_menu_profile')
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Presentation',width=150, height=30)
        pmenu.set_on_click_listener(self, 'new_presentation_profile')
        profile_new_menu.append(pmenu)        
        pmenu = gui.MenuItem('Interactive',width=150, height=30)
        pmenu.set_on_click_listener(self, 'new_interactive_profile')
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Live Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'new_liveshow_profile')
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Art Live Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'new_artliveshow_profile')
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('RadioButton Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'new_radiobuttonshow_profile')
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem( 'Hyperlink Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'new_hyperlinkshow_profile')
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem( 'Blank',width=150, height=30)
        pmenu.set_on_click_listener(self, 'new_blank_profile')
        profile_new_menu.append(pmenu)
        
        # shows menu              
        show_menu = gui.MenuItem( 'Show',width=80, height=30)
        show_delete_menu = gui.MenuItem('Delete',width=120, height=30)
        show_delete_menu.set_on_click_listener(self, 'remove_show')    
        show_edit_menu = gui.MenuItem('Edit',width=120, height=30)
        show_edit_menu.set_on_click_listener(self, 'm_edit_show')
        show_copy_to_menu = gui.MenuItem( 'Copy To',width=120, height=30)
        show_copy_to_menu.set_on_click_listener(self, 'copy_show')
        show_add_menu = gui.MenuItem( 'Add',width=120, height=30)
        show_menu.append(show_delete_menu)
        show_menu.append(show_edit_menu)
        show_menu.append(show_copy_to_menu)
        show_menu.append(show_add_menu)


        pmenu = gui.MenuItem('Menu',width=150, height=30)
        pmenu.set_on_click_listener(self, 'add_menushow')
        show_add_menu.append(pmenu)
        
        pmenu = gui.MenuItem( 'Media Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'add_mediashow')
        show_add_menu.append(pmenu)
        
        pmenu = gui.MenuItem('Live Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'add_liveshow')
        show_add_menu.append(pmenu)

        pmenu = gui.MenuItem('Hyperlink Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'add_hyperlinkshow')
        show_add_menu.append(pmenu)

        pmenu = gui.MenuItem('RadioButton Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'add_radiobuttonshow')
        show_add_menu.append(pmenu)

        pmenu = gui.MenuItem( 'Art Mediashow Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'add_artmediashow')
        show_add_menu.append(pmenu)

        pmenu = gui.MenuItem( 'Art Liveshow Show',width=150, height=30)
        pmenu.set_on_click_listener(self, 'add_artliveshow')
        show_add_menu.append(pmenu)

        # medialists menu
        medialist_menu = gui.MenuItem( 'Medialist',width=80, height=30)
        
        medialist_delete_menu = gui.MenuItem( 'Delete',width=120, height=30)
        medialist_delete_menu.set_on_click_listener(self, 'remove_medialist')

        
        medialist_add_menu = gui.MenuItem( 'Add',width=120, height=30)
        medialist_add_menu.set_on_click_listener(self, 'add_medialist')
        
        medialist_copy_to_menu = gui.MenuItem('Copy To',width=120, height=30)
        medialist_copy_to_menu.set_on_click_listener(self, 'copy_medialist')
        
        medialist_menu.append(medialist_add_menu)
        medialist_menu.append(medialist_delete_menu)
        medialist_menu.append(medialist_copy_to_menu)

        # tracks menu
        track_menu = gui.MenuItem('Track',width=80, height=30)

        track_delete_menu = gui.MenuItem('Delete',width=120, height=30)
        track_delete_menu.set_on_click_listener(self, 'remove_track')
        track_edit_menu = gui.MenuItem( 'Edit',width=120, height=30)
        track_edit_menu.set_on_click_listener(self, 'm_edit_track')
        track_add_from_dir_menu = gui.MenuItem('Add Directory',width=120, height=30)
        track_add_from_dir_menu.set_on_click_listener(self, 'add_tracks_from_dir')
        track_add_from_file_menu = gui.MenuItem('Add File',width=120, height=30)
        track_add_from_file_menu.set_on_click_listener(self, 'add_track_from_file')
        track_new_menu = gui.MenuItem('New',width=120, height=30)

        track_new_video_menu = gui.MenuItem('Video',width=120, height=30)
        track_new_video_menu.set_on_click_listener(self, 'new_video_track')
        track_new_audio_menu = gui.MenuItem('Audio',width=120,height=30)
        track_new_audio_menu.set_on_click_listener(self, 'new_audio_track')
        track_new_image_menu = gui.MenuItem( 'Image',width=120, height=30)
        track_new_image_menu.set_on_click_listener(self, 'new_image_track')
        track_new_web_menu = gui.MenuItem( 'Web',width=120, height=30)
        track_new_web_menu.set_on_click_listener(self, 'new_web_track')
        track_new_message_menu = gui.MenuItem('Message',width=120, height=30)
        track_new_message_menu.set_on_click_listener(self, 'new_message_track')
        track_new_show_menu = gui.MenuItem('Show',width=120, height=30)
        track_new_show_menu.set_on_click_listener(self, 'new_show_track')
        track_new_menu_menu = gui.MenuItem('Menu',width=120, height=30)
        track_new_menu_menu.set_on_click_listener(self, 'new_menu_track')

        track_new_menu.append(track_new_video_menu)
        track_new_menu.append(track_new_audio_menu)
        track_new_menu.append(track_new_image_menu)
        track_new_menu.append(track_new_web_menu)        
        track_new_menu.append(track_new_message_menu)
        track_new_menu.append(track_new_show_menu)
        track_new_menu.append(track_new_menu_menu)
        
        track_menu.append(track_delete_menu)
        track_menu.append(track_edit_menu)
        track_menu.append(track_add_from_dir_menu)
        track_menu.append(track_add_from_file_menu)
        track_menu.append(track_new_menu)


      
        options_menu = gui.MenuItem('Options',width=80, height=30)
        options_edit_menu=gui.MenuItem('Edit',width=80, height=30)
        options_edit_menu.set_on_click_listener(self, 'edit_options')
        options_menu.append(options_edit_menu)

        # osc menu
        osc_menu = gui.MenuItem( 'OSC',width=80, height=30)  
        osc_create_menu = gui.MenuItem( 'Create',width=120, height=30)
        osc_create_menu.set_on_click_listener(self, 'create_osc')
        osc_edit_menu = gui.MenuItem( 'Edit',width=120, height=30)
        osc_edit_menu.set_on_click_listener(self, 'edit_osc')
        osc_delete_menu = gui.MenuItem( 'Delete',width=120, height=30)
        osc_delete_menu.set_on_click_listener(self, 'delete_osc')
        osc_menu.append(osc_create_menu)
        osc_menu.append(osc_edit_menu)
        osc_menu.append(osc_delete_menu)
        
        # help menu
        help_menu = gui.MenuItem( 'Help',width=80, height=30)
        help_text_menu = gui.MenuItem( 'Help',width=80, height=30)
        help_text_menu.set_on_click_listener(self, 'show_help')
        about_menu = gui.MenuItem( 'About',width=80, height=30)
        about_menu.set_on_click_listener(self, 'show_about')
        help_menu.append(help_text_menu)
        help_menu.append(about_menu)

        menu.append(profile_menu)
        menu.append(show_menu)
        menu.append(medialist_menu)
        menu.append(track_menu)
        menu.append(osc_menu)
        menu.append(options_menu)
        menu.append(help_menu)


        
        #shows and medialists
        shows_label=gui.Label('<b>Shows</b>',width=300, height=20)
        shows_label.style['margin']='5px'
        self.shows_display= gui.ListView(width=350, height=150)
        self.shows_display.set_on_selection_listener(self,'show_selected')
        
        medialists_label=gui.Label('<b>Medialists</b>',width=300, height=20)
        medialists_label.style['margin']='5px'
        self.medialists_display= gui.ListView(width=350, height=150)
        self.medialists_display.set_on_selection_listener(self,'medialist_selected')

        left_frame.append(shows_label)
        left_frame.append(self.shows_display)         
        left_frame.append(medialists_label)
        left_frame.append(self.medialists_display)

        #edit show button
        edit_show = gui.Button('Edit\nShow',width=50, height=50)
        edit_show.set_on_click_listener(self, 'm_edit_show')
        middle_frame.append(edit_show)

        #tracks
        tracks_label=gui.Label('<b>Tracks in Selected Medialist</b>',width=300, height=20)
        tracks_label.style['margin']='5px'
        self.tracks_display= gui.ListView(width=350, height=300)
        self.tracks_display.set_on_selection_listener(self,'track_selected')

        right_frame.append(tracks_label)
        right_frame.append(self.tracks_display)  

        #tracks buttons
        add_track = gui.Button('Add',width=50, height=50)
        add_track.set_on_click_listener(self, 'add_track_from_file')
        updown_frame.append(add_track)
        
        edit_track = gui.Button('Edit',width=50, height=50)
        edit_track.set_on_click_listener(self, 'm_edit_track')
        updown_frame.append(edit_track)        

        up_track = gui.Button('Up',width=50, height=50)
        up_track.set_on_click_listener(self, 'move_track_up')
        updown_frame.append(up_track)

        down_track = gui.Button('Down',width=50, height=50)
        down_track.set_on_click_listener(self, 'move_track_down')
        updown_frame.append(down_track)
        return root

        
    def init(self):
        # print 'init'
        self.eo.read_options()
        self.pp_home_dir = self.eo.pp_home_dir
        self.pp_profiles_offset = self.eo.pp_profiles_offset
        self.initial_media_dir = self.eo.initial_media_dir
        self.pp_profile_dir=''
        self.current_medialist=None
        self.current_showlist=None
        self.current_show=None

    def empty_lists(self):
        # print 'empty lists'
        self.shows_display.empty()
        self.medialists_display.empty()
        self.tracks_display.empty()

    def show_help (self):
        OKDialog("Help","Please Read 'manual.pdf'",width=400,height=200).show(self)

  
    def show_about (self):
        OKDialog("About","Web Editor for Pi Presents Profiles<br>"
                              +"For profiles of version: " + self.editor_issue + "<br>Author: Ken Thompson"
                              +"<br>Website: http://pipresents.wordpress.com/<br>",width=400,height=200).show(self)

    def validate_profile(self):
        if self.current_showlist != None:
            val =Validator('Validation Result')
            val.show(self)
            val.validate_profile(self.editor_dir,self.pp_home_dir,self.pp_profile_dir,self.editor_issue,True)


    # **************
    # OPTIONS
    # **************


    def edit_options(self):
        self.eo.edit(self.edit_options_callback)
        self.eo.show(self)

    def edit_options_callback(self):
        # self.eo.show(self)
        self.eo.read_options()
        self.init()
        self.empty_lists()
        



    # **************
    # OSC CONFIGURATION
    # **************

    def create_osc(self):
        if self.pp_profile_dir=='':
            return
        # print 'create',OSCConfig.options_file
        if self.osc_config.read() is False:
            iodir=self.pp_profile_dir+os.sep+'pp_io_config'
            if not os.path.exists(iodir):
                os.makedirs(iodir)
            self.osc_config.create()

    def edit_osc(self):
        # print 'edit',OSCConfig.options_file
        if self.osc_config.read() is False:
            # print 'no config file'
            return
        self.osc_ute.edit(self.edit_osc_callback)
        self.osc_ute.show(self)

    def edit_osc_callback(self):
        # self.osc_ute.hide()
        # print 'edit callback', OSCConfig.current_unit_type
        self.osc_editor=OSCWebEditor()
        if OSCConfig.current_unit_type != '':
            self.osc_editor.edit()
            self.osc_editor.show(self)
   
    def delete_osc(self):
        if self.osc_config.read() is False:
            return
        self.osc_config.delete()
        



    
    # **************
    # PROFILES
    # **************

    def open_existing_profile(self):
        initial_dir=self.pp_home_dir+os.sep+"pp_profiles"+self.pp_profiles_offset
        if os.path.exists(initial_dir) is False:
            OKDialog('Open Profile',"Profiles directory not found: " + initial_dir + "<br><br>Hint: Data Home option must end in pp_home").show(self)
            return
        open_existing_profile_dialog = gui.FileSelectionDialog('Open Profile','Select profile',False, initial_dir) #width=600,height=200,
        open_existing_profile_dialog.set_on_confirm_value_listener(self, 'open_existing_profile_dialog_confirm')
        open_existing_profile_dialog.show(self)


    def open_existing_profile_dialog_confirm(self, filelist):
        if len(filelist)==0:
            OKDialog('Open Profile',"Nothing Selected").show(self)
            return
        # print 'filelist',filelist[0]
        self.open_profile(filelist[0])
        

    def open_profile(self,dir_path):
        showlist_file = dir_path + os.sep + "pp_showlist.json"
        #print 'open profile',showlist_file
        if os.path.exists(showlist_file) is False:
            OKDialog('Open Profile',"Not a Profile: " + dir_path).show(self)
            return
        self.pp_profile_dir = dir_path
        OSCConfig.options_file=self.pp_profile_dir+ os.sep+'pp_io_config'+os.sep+'osc.cfg'
        # print 'profile direcotry',self.pp_profile_dir
        # self.root.title("Editor for Pi Presents - "+ self.pp_profile_dir)
        if self.open_showlist(self.pp_profile_dir) is False:
            self.init()
            self.empty_lists()
            return
        
        self.open_medialists(self.pp_profile_dir)
        self.refresh_tracks_display()
        self.osc_config_file=self.pp_profile_dir+os.sep+'pp_io_config'+os.sep+'osc.cfg'


    def new_profile(self,profile):
        d = gui.InputDialog("New Profile","Name",width=400,height=250)
        self.new_profile_template=profile
        d.set_on_confirm_value_listener(self, 'new_profile_confirm')
        d.show(self)

    def new_profile_confirm(self,name):
        if name == "":
            OKDialog("New Profile","Name is blank").show(self)
            return
        to = self.pp_home_dir + os.sep + "pp_profiles"+ self.pp_profiles_offset + os.sep + name
        if os.path.exists(to) is  True:
            OKDialog( "New Profile","Profile exists\n(%s)" % to ).show(self)
            return
        shutil.copytree(self.new_profile_template, to, symlinks=False, ignore=None)
        self.open_profile(to)


        
    def new_exhibit_profile(self):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_exhibit_1p3'
        self.new_profile(profile)

    def new_interactive_profile(self):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_interactive_1p3'
        self.new_profile(profile)

    def new_menu_profile(self):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_menu_1p3'
        self.new_profile(profile)

    def new_presentation_profile(self):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_presentation_1p3'
        self.new_profile(profile)

    def new_blank_profile(self):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep +"ppt_blank_1p3"
        self.new_profile(profile)

    def new_mediashow_profile(self):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_mediashow_1p3'
        self.new_profile(profile)
        
    def new_liveshow_profile(self):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_liveshow_1p3'
        self.new_profile(profile)

    def new_artmediashow_profile(self):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_artmediashow_1p3'
        self.new_profile(profile)
        
    def new_artliveshow_profile(self):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_artliveshow_1p3'
        self.new_profile(profile)

    def new_radiobuttonshow_profile(self):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_radiobuttonshow_1p3'
        self.new_profile(profile)

    def new_hyperlinkshow_profile(self):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_hyperlinkshow_1p3'
        self.new_profile(profile)


    # ***************************************
    # Shows
    # ***************************************

# !!!!! changed app_exit to return
    def open_showlist(self,profile_dir):
        showlist_file = profile_dir + os.sep + "pp_showlist.json"
        if os.path.exists(showlist_file) is False:
            OKDialog('Open Profile',"showlist file not found at " + profile_dir + "<br><br>Hint: Have you opened the profile directory?").show(self)
            return False
        self.current_showlist=ShowList()
        self.current_showlist.open_json(showlist_file)
        if float(self.current_showlist.sissue())<float(self.editor_issue):
            self.update_profile()
            OKDialog('Open Profile',"Version of profile has been updated to "+self.editor_issue+", please re-open").show(self)
            return False
        if float(self.current_showlist.sissue())>float(self.editor_issue):
            OKDialog('Open Profile',"Version of profile is greater than editor").show(self)
            return False
        self.refresh_shows_display()
        return True


    def save_showlist(self,showlist_dir):
        if self.current_showlist is not None:
            showlist_file = showlist_dir + os.sep + "pp_showlist.json"
            self.current_showlist.save_list(showlist_file)
            
    def add_mediashow(self):
        self.add_show(PPdefinitions.new_shows['mediashow'])

    def add_liveshow(self):
        self.add_show(PPdefinitions.new_shows['liveshow'])

    def add_radiobuttonshow(self):
        self.add_show(PPdefinitions.new_shows['radiobuttonshow'])

    def add_hyperlinkshow(self):
        self.add_show(PPdefinitions.new_shows['hyperlinkshow'])

    def add_artliveshow(self):
        self.add_show(PPdefinitions.new_shows['artliveshow'])

    def add_artmediashow(self):
        self.add_show(PPdefinitions.new_shows['artmediashow'])
        
    def add_menushow(self):
        self.add_show(PPdefinitions.new_shows['menu'])

    def add_start(self):  
        self.add_show(PPdefinitions.new_shows['start'])


    def add_show(self,default):
        # append it to the showlist and then add the medialist
        if self.current_showlist is not None:
            self.default_show=default
            d = gui.InputDialog("Add Show","Show Reference",width=400,height=250)
            d.set_on_confirm_value_listener(self, 'add_show_confirm')
            d.show(self)

    def add_show_confirm(self,name):
        # print 'show name',name
        if name == "":
            OKDialog("Add Show","Name is blank").show(self)
            return             
        if self.current_showlist.index_of_show(name) != -1:
            OKDialog("Add Show","A Show with this name already exists").show(self)
            return
        # print 'copy show template',self.default_show,name
        copied_show=self.current_showlist.copy(self.default_show,name)
        # print 'add mediafile from show',name
        mediafile=self.add_medialist(name)
        # print 'mediafile added',mediafile
        if mediafile != '':
            copied_show['medialist']=mediafile
        self.current_showlist.append(copied_show)
        self.save_showlist(self.pp_profile_dir)
        self.refresh_shows_display()

            
    def remove_show(self):
        if  self.current_showlist is not None and self.current_showlist.length()>0 and self.current_showlist.show_is_selected():
            OKCancelDialog("Delete Show","Are you sure?",self.remove_show_confirm).show(self)

    def remove_show_confirm(self,result):
        if result is True:
            index= self.current_showlist.selected_show_index()
            self.current_showlist.remove(index)
            self.save_showlist(self.pp_profile_dir)
            self.refresh_shows_display()


    def show_refs(self):
        _show_refs=[]
        for index in range(self.current_showlist.length()):
            if self.current_showlist.show(index)['show-ref'] != "start":
                _show_refs.append(copy.deepcopy(self.current_showlist.show(index)['show-ref']))
        return _show_refs
 
    def refresh_shows_display(self):
        self.shows_display.empty()
        key=0
        for index in range(self.current_showlist.length()):
            value= self.current_showlist.show(index)['title']+"   ["+self.current_showlist.show(index)['show-ref']+"]"
            obj = gui.ListItem(value,width=340, height=20)
            self.shows_display.append(obj,key=key)
            key+=1
        if self.current_showlist.show_is_selected():
            self.shows_display.select_by_key(self.current_showlist.selected_show_index())            
            # self.shows_display.show()

            
    def show_selected(self,event):
        if self.current_showlist is not None and self.current_showlist.length()>0:
            mouse_item_index=self.shows_display.get_key()
            self.current_showlist.select(mouse_item_index)
            self.refresh_shows_display()

    def copy_show(self):
        if  self.current_showlist is not None and self.current_showlist.show_is_selected():
            self.add_show(self.current_showlist.selected_show())

        
    def m_edit_show(self):
        self.edit_show(PPdefinitions.show_types,PPdefinitions.show_field_specs)
        

    def edit_show(self,show_types,field_specs):
        if self.current_showlist is not None and self.current_showlist.show_is_selected():
            self.edit_show_dialog=WebEditItem("Edit Show",self.current_showlist.selected_show(),show_types,field_specs,self.show_refs(),
                       self.initial_media_dir,self.pp_home_dir,'show',self.finished_edit_show)
            self.edit_show_dialog.show(self)
            self.edit_show_dialog.show_tab('show')

    def finished_edit_show(self):
        self.save_showlist(self.pp_profile_dir)
        self.refresh_shows_display()



    # ***************************************
    #   Medialists
    # ***************************************

    def open_medialists(self,profile_dir):
        self.medialists = []
        for this_file in os.listdir(profile_dir):
            if this_file.endswith(".json") and this_file not in ('pp_showlist.json','schedule.json'):
                self.medialists = self.medialists + [this_file]
        self.medialists_display.empty()
        key=0
        for index in range (len(self.medialists)):
            obj = gui.ListItem(self.medialists[index],width=340, height=20)
            self.medialists_display.append(obj, key=key)
            key+=1
        self.current_medialists_index=-1
        self.current_medialist=None


    def add_medialist(self,name=None):
        if self.current_showlist != None:
            if name is None:
                d = gui.InputDialog("Add Medialist","File",width=400,height=250)
                d.set_on_confirm_value_listener(self, 'add_medialist_confirm')
                d.show(self)
            else:
                medialist_name=self.add_medialist_confirm(name)
                return medialist_name

    def add_medialist_confirm(self,name):
        # print 'add medialist',name
        if name == "":
            OKDialog("Add Medialist","Name is blank").show(self)
            return  ''           
        if self.current_showlist.index_of_show(name) != -1:
            OKDialog("Add Medialist","A medialist with this name already exists").show(self)
            return ''
        if not name.endswith(".json"):
            name=name+(".json")
               
        path = self.pp_profile_dir + os.sep + name
        if os.path.exists(path) is  True:
            OKDialog("Add Medialist","Medialist file exists<br>(%s)" % path).show(self)
            return ''
        nfile = open(path,'wb')
        nfile.write("{")
        nfile.write("\"issue\":  \""+self.editor_issue+"\",\n")
        nfile.write("\"tracks\": [")
        nfile.write("]")
        nfile.write("}")
        nfile.close()
        # append it to the list
        self.medialists.append(copy.deepcopy(name))
        # print 'medialists',self.medialists
        # add title to medialists display
        # self.medialists_display.insert(END, name)  
        # and set it as the selected medialist
        self.refresh_medialists_display()
        # print 'returning medilaist name',name
        return name


    def copy_medialist(self,to_file=None):
        if self.current_showlist != None:
            if self.current_medialist is not None:
                #from_file= self.current_medialist
                self.from_file= self.medialists[self.current_medialists_index]
                if to_file is None:
                    d = gui.InputDialog("Copy Medialist","File",width=400,height=250)
                d.set_on_confirm_value_listener(self, 'copy_medialist_confirm')
                d.show(self)
            else:
                self.copy_medialist_confirm(to_file)

    def copy_medialist_confirm(self,to_file):
        # print self.from_file,to_file
        if to_file == "":
            OKDialog("Copy Medialist","Name is blank").show(self)
            return ''

        success_file = self.copy_medialist_file(self.from_file,to_file)
        if success_file =='':
            return ''

        # append it to the list
        self.medialists.append(copy.deepcopy(success_file))
        # add title to medialists display
        # self.medialists_display.insert(END, success_file)
        # and reset  selected medialist
        self.current_medialist=None
        self.refresh_medialists_display()
        self.refresh_tracks_display()
        return success_file


    def copy_medialist_file(self,from_file,to_file):
        if not to_file.endswith(".json"):
            to_file+=(".json")
                
        to_path = self.pp_profile_dir + os.sep + to_file
        if os.path.exists(to_path) is  True:
            OKDialog("Copy Medialist","Medialist file exists\n(%s)" % to_path).show(self)
            return ''
        
        from_path= self.pp_profile_dir + os.sep + from_file
        if os.path.exists(from_path) is  False:
            OKDialog("Copy Medialist","Medialist file not found\n(%s)" % from_path).show(self)
            return ''

        shutil.copy(from_path,to_path)
        return to_file


    def remove_medialist(self):
        if self.current_medialist is not None:
            OKCancelDialog("Delete Medialist","Are you sure?",self.remove_medialist_confirm).show(self)

    def remove_medialist_confirm(self,result):
        if result is True:
            os.remove(self.pp_profile_dir+ os.sep + self.medialists[self.current_medialists_index])
            self.open_medialists(self.pp_profile_dir)
            self.refresh_medialists_display()
            self.refresh_tracks_display()


# removed appexit
    def medialist_selected(self,key):
        """
        user clicks on a medialst in a profile so try and select it.
        """
        # print 'selected',type(self.medialists_display.get_key()),self.medialists_display.get_key()
        if len(self.medialists)>0:
            self.current_medialists_index=self.medialists_display.get_key()

            self.current_medialist=MediaList('ordered')
            if not self.current_medialist.open_list(self.pp_profile_dir+ os.sep + self.medialists[self.current_medialists_index],self.current_showlist.sissue()):
                OKDialog(self,"medialist is a different version to showlist: "+ self.medialists[self.current_medialists_index]).show(self)
                #self.app_exit()
                return
            self.refresh_tracks_display()
            self.refresh_medialists_display()


    def refresh_medialists_display(self):
        # print 'refresh medialists'
        self.medialists_display.empty()
        key=0
        for index in range (len(self.medialists)):
            obj = gui.ListItem(self.medialists[index],width=340, height=20)
            self.medialists_display.append(obj,key=key)
            key+=1
                    
        if self.current_medialist is not None:
            self.medialists_display.select_by_key(self.current_medialists_index)
            # self.medialists_display.show(self)

  

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
          
    def refresh_tracks_display(self):
        self.tracks_display.empty()
        if self.current_medialist is not None:
            key=0
            for index in range(self.current_medialist.length()):
                if self.current_medialist.track(index)['track-ref'] != '':
                    track_ref_string="  ["+self.current_medialist.track(index)['track-ref']+"]"
                else:
                    track_ref_string=""
                obj = gui.ListItem(self.current_medialist.track(index)['title']+track_ref_string,width=340, height=20)
                self.tracks_display.append(obj,key=key)
                key+=1                
            if self.current_medialist.track_is_selected():
                self.tracks_display.select_by_key(self.current_medialist.selected_track_index())  

            
    def  track_selected(self,key):
        # print 'track sel', type(self.tracks_display.get_key())
        if self.current_medialist is not None and self.current_medialist.length()>0:
            mouse_item_index=self.tracks_display.get_key()
            self.current_medialist.select(mouse_item_index)
            self.refresh_tracks_display()

    def m_edit_track(self):
        self.edit_track(PPdefinitions.track_types,PPdefinitions.track_field_specs)

    def edit_track(self,track_types,field_specs):      
        if self.current_medialist is not None and self.current_medialist.track_is_selected():
            self.edit_track_dialog=WebEditItem("Edit Track",self.current_medialist.selected_track(),track_types,field_specs,
                       self.show_refs(),self.initial_media_dir,self.pp_home_dir,'track',self.finished_edit_track)
            self.edit_track_dialog.show(self)
            self.edit_track_dialog.show_tab('track')

    def finished_edit_track(self):
        self.refresh_tracks_display()
        self.save_medialist()        
            
    def move_track_up(self):
        if self.current_medialist is not None and self.current_medialist.track_is_selected():
            self.current_medialist.move_up()
            self.refresh_tracks_display()
            self.save_medialist()

    def move_track_down(self):
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

    def new_message_track(self):
        self.new_track(PPdefinitions.new_tracks['message'],None)
            
    def new_video_track(self):
        self.new_track(PPdefinitions.new_tracks['video'],None)
  
    def new_audio_track(self):
        self.new_track(PPdefinitions.new_tracks['audio'],None)

    def new_web_track(self):
        self.new_track(PPdefinitions.new_tracks['web'],None)
        
    def new_image_track(self):
        self.new_track(PPdefinitions.new_tracks['image'],None)

    def new_show_track(self):
        self.new_track(PPdefinitions.new_tracks['show'],None)

    def new_menu_track(self):
        # print 'new menu track'
        self.new_track(PPdefinitions.new_tracks['menu'],None)
 
    def remove_track(self):
        if  self.current_medialist is not None and self.current_medialist.length()>0 and self.current_medialist.track_is_selected():
            OKCancelDialog("Delete Track","Are you sure?",self.remove_track_confirm).show(self)

    def remove_track_confirm(self,result):
        # print 'confirm',result
        if result is True:
            index= self.current_medialist.selected_track_index()
            self.current_medialist.remove(index)
            self.save_medialist()
            self.refresh_tracks_display()
            
    def add_track_from_file(self):
        if self.current_medialist is None:
            return
        add_track_from_file_dialog = gui.FileSelectionDialog('Add Track', 'Select Tracks',True, self.eo.initial_media_dir)#600,200,
        add_track_from_file_dialog.set_on_confirm_value_listener(self, 'add_track_from_file_dialog_confirm')
        add_track_from_file_dialog.show(self)


    def add_track_from_file_dialog_confirm(self, filelist):
        if len(filelist)==0:
            OKDialog('Add Track',"Nothing Selected").show(self)
            return
        for file_path in filelist:
            file_path=os.path.normpath(file_path)
            # print "file path ", file_path
            self.add_track(file_path)
        self.save_medialist()

    def add_tracks_from_dir(self):
        if self.current_medialist is None: return
        add_tracks_from_dir_dialog = gui.FileSelectionDialog('Add Directory', 'Select Directory',
                                    multiple_selection = False, allow_file_selection=False, selection_folder = self.eo.initial_media_dir)
        add_tracks_from_dir_dialog.set_on_confirm_value_listener(self, 'add_tracks_from_dir_dialog_confirm')
        add_tracks_from_dir_dialog.show(self)


    def add_tracks_from_dir_dialog_confirm(self, result):
        image_specs =[PPdefinitions.IMAGE_FILES,PPdefinitions.VIDEO_FILES,PPdefinitions.AUDIO_FILES,
                      PPdefinitions.WEB_FILES,('All files', '*')]
        # last one is ignored in finding files in directory, for dialog box only
        if len(result) == 0:
            OKDialog('Add Tracks',"Nothing Selected").show(self)
            return
        directory=result[0]
        # make list of exts we recognise
        exts = []
        for image_spec in image_specs[:-1]:
            image_list=image_spec[1:]
            for ext in image_list:
                exts.append(copy.deepcopy(ext))
        for this_file in os.listdir(directory):
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
            OKDialog('Add Track',afile + " - cannot determine track type, use menu track>new").show(self)




# ****************************************
# OPTIONS
# ****************************************

class Options(gui.GenericDialog):

    def __init__(self, *args):
        super(Options, self).__init__(title='<b>Edit Options</b>',width=500,height=300,autohide_ok=False)

        # build the gui in _init as it is subclassed
        home_dir_field= gui.TextInput(width=200, height=30)
        self.add_field_with_label('home_dir','Pi Presents Data Home:',home_dir_field)
        # home_dir_field.set_on_change_listener(self, 'validate_home')
        media_dir_field= gui.TextInput(width=200, height=30)
        self.add_field_with_label('media_dir','Inital directory for Media:',media_dir_field)
        # media_dir_field.set_on_change_listener(self, 'validate_media')
        offset_field= gui.TextInput(width=200, height=30)
        self.add_field_with_label('offset','Offset for Current Profiles:',offset_field)
        # offset_field.set_on_change_listener(self, 'validate_offset')
        error_field= gui.Label('',width=400, height=30)
        self.add_field('error',error_field)
        self.set_on_confirm_dialog_listener(self,'eo_confirm')


    def init_options(self,app_dir):
        # define options for Editor
        self.pp_home_dir = ''
        self.pp_profiles_offset = ''
        self.initial_media_dir = ''
        
        # create an options file if necessary
        self.options_file = app_dir+os.sep+'pp_config'+ os.sep + 'pp_editor.cfg'
        if not os.path.exists(self.options_file):
            self.create_options()


    def create_options(self):
        config=ConfigParser.ConfigParser()
        config.add_section('config')
        if os.name == 'nt':
            config.set('config','home',os.path.expanduser('~')+'\pp_home')
            config.set('config','media',os.path.expanduser('~'))
            config.set('config','offset','')
        else:
            config.set('config','home',os.path.expanduser('~')+'/pp_home')
            config.set('config','media',os.path.expanduser('~'))
            config.set('config','offset','')
        with open(self.options_file, 'wb') as config_file:
            config.write(config_file)


    def read_options(self):
        # print 'read options'
        """reads options from options file to interface"""
        config=ConfigParser.ConfigParser()
        config.read(self.options_file)
        
        self.pp_home_dir =config.get('config','home',0)
        self.pp_profiles_offset =config.get('config','offset',0)
        self.initial_media_dir =config.get('config','media',0)


    def edit(self,callback):
        self.callback=callback
        self.read_options()
        # print 'edit_options in class'
        self.get_field('home_dir').set_value(self.pp_home_dir)
        self.get_field('media_dir').set_value(self.initial_media_dir)       
        self.get_field('offset').set_value(self.pp_profiles_offset)
        self.get_field('error').set_text('')

    def eo_confirm(self):
        text=''

        home_dir=self.get_field('home_dir').get_value()
        media_dir=self.get_field('media_dir').get_value()
        offset=self.get_field('offset').get_value()
        # print 'confirm',home_dir
        
        if os.path.exists(home_dir) is  False:
            text="<b>Data Home directory not found "+home_dir+ "</b>"
            self.get_field('error').set_text(text)
            return

        if os.path.exists(media_dir) is  False:
            text="<b>Media directory not found " + media_dir + "</b>"
            self.get_field('error').set_text(text)
            return

        path=home_dir+os.sep+'pp_profiles'+ offset
        if os.path.exists(path) is  False:
            text="<b> Current Profiles Directory not found "+path+ "</b>"
            self.get_field('error').set_text(text)
            return
        
        self.get_field('error').set_text('')
        self.hide()
        
        config=ConfigParser.ConfigParser()
        config.add_section('config')
        config.set('config','home',home_dir)
        config.set('config','media',media_dir)
        config.set('config','offset',offset)
        with open(self.options_file, 'wb') as optionsfile:
            config.write(optionsfile)
        self.callback()
    


#
# ***************************************
# MAIN
# ***************************************


if __name__  ==  "__main__":

    # get directory holding the code
    editor_dir=sys.path[0]
    # print editor_dir
    if not os.path.exists(editor_dir+os.sep+"pp_web_editor.py"):
        print "Bad Application Directory"
        exit()

    # wait for network to be available
    network=Network()
    print 'Waiting for Network'
    success=network.wait_for_network(10)
    if success is False:
        print 'Failed to connect to network after 10 seconds'     
        exit()   


    # check pp_web.cfg
    editor_options_file_path=editor_dir+os.sep+'pp_config'+os.sep+'pp_web.cfg'
    if not os.path.exists(editor_options_file_path):
        print 'pp_web.cfg not found at ' + editor_options_file_path
        tkMessageBox.showwarning("Pi Presents Web Editor",'pp_web.cfg not found at ' + editor_options_file_path)
        exit()

    print 'Found pp_web.cfg in ', editor_options_file_path

    # get interface and IP details of preferred interface
    network.read_config(editor_options_file_path)
    interface,ip = network.get_preferred_ip()
    print 'Network details ' + network.unit + ' ' + interface + ' ' + ip


    # setting up remi debug level 
    #       2=all debug messages   1=error messages   0=no messages
    import remi.server
    remi.server.DEBUG_MODE = 0

    # start the web server to serve the Web Editor App
    start(PPWebEditor,address=ip, port=network.editor_port,username=network.editor_username,password=network.editor_password,
          multiple_instance=True,enable_file_cache=True,
          update_interval=0.1, start_browser=False)



    
