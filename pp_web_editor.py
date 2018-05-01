#! /usr/bin/env python

import os
import sys
import ConfigParser
import shutil
import copy
import string
import json
import remi.gui as gui
from remi import start, App
from pp_network import Network
from pp_options import web_ed_options


from remi_plus import OKDialog, OKCancelDialog,AdaptableDialog,FileSelectionDialog,InputDialog,ReportDialog
from pp_web_edititem import WebEditItem, ColourMap
from pp_utils import calculate_relative_path
from pp_medialist import MediaList
from pp_showlist import ShowList
from pp_web_validate import Validator
from pp_definitions import PPdefinitions
from pp_oscwebconfig import OSCConfig,OSCWebEditor


class PPWebEditor(App):

    def __init__(self, *args):
        # print 'DOING _INIT do not use'
        super(PPWebEditor, self).__init__(*args)
     
    def main(self):
        # print 'DOING MAIN executed once when server starts'
        # ***************************************
        # INIT
        # ***************************************
        self.editor_issue="1.3.5"
        self.force_update= False

        # get directory holding the code
        self.editor_dir=sys.path[0]

        ColourMap().init()
        
        # initialise editor options OSC config class, and OSC editors
        self.eo=Options()
        self.eo.init_options(self.editor_dir)
        self.osc_config=OSCConfig()
      
        # initialise variables
        self.init() 

        # BUILD THE GUI
        # frames
        root = gui.Widget(width=770,height=500, margin='0px auto') #the margin 0px auto centers the main container
        bottom_frame=gui.Widget(width=770,height=400)#1
        bottom_frame.set_layout_orientation(gui.Widget.LAYOUT_HORIZONTAL)       
        # bottom_frame.style['display'] = 'block'
        # bottom_frame.style['overflow'] = 'auto'
        
        left_frame=gui.Widget(width=300,height=400)#1
        # left_frame.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)
        left_frame.style['margin']='10px'
        
        middle_frame=gui.VBox(width=50,height=250)#1
        middle_frame.style['margin']='10px'
        
        right_frame=gui.Widget(width=300,height=400)#1
        
        updown_frame=gui.VBox(width=50,height=400)#1
        updown_frame.style['margin']='10px'
  

        #menu
        menubar=gui.MenuBar(width='100%', height='30px')
        menu = gui.Menu(width='100%', height='30px')

    
        #profile menu
        profile_menu = gui.MenuItem('Profile',width=80, height=30)
        profile_open_menu = gui.MenuItem('Open',width=120, height=30)
        profile_open_menu.set_on_click_listener(self.open_existing_profile)
        profile_validate_menu = gui.MenuItem('Validate',width=120, height=30)
        profile_validate_menu.set_on_click_listener(self.validate_profile)
        profile_copy_to_menu = gui.MenuItem( 'Copy To',width=120, height=30)
        profile_copy_to_menu.set_on_click_listener(self.copy_profile)
        profile_delete_menu = gui.MenuItem( 'Delete',width=120, height=30)
        profile_delete_menu.set_on_click_listener(self.delete_profile)
        profile_new_menu = gui.MenuItem('New',width=120, height=30)
        profile_menu.append(profile_open_menu)
        profile_menu.append(profile_validate_menu)
        profile_menu.append(profile_copy_to_menu)
        profile_menu.append(profile_delete_menu)
        profile_menu.append(profile_new_menu)

        pmenu = gui.MenuItem('Exhibit',width=150, height=30)
        pmenu.set_on_click_listener(self.new_exhibit_profile)
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Media Show',width=150, height=30)
        pmenu.set_on_click_listener(self.new_mediashow_profile)
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Art Media Show',width=150, height=30)
        pmenu.set_on_click_listener(self.new_artmediashow_profile)
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Menu',width=150, height=30)
        pmenu.set_on_click_listener(self.new_menu_profile)
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Presentation',width=150, height=30)
        pmenu.set_on_click_listener(self.new_presentation_profile)
        profile_new_menu.append(pmenu)        
        pmenu = gui.MenuItem('Interactive',width=150, height=30)
        pmenu.set_on_click_listener(self.new_interactive_profile)
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Live Show',width=150, height=30)
        pmenu.set_on_click_listener(self.new_liveshow_profile)
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('Art Live Show',width=150, height=30)
        pmenu.set_on_click_listener(self.new_artliveshow_profile)
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem('RadioButton Show',width=150, height=30)
        pmenu.set_on_click_listener(self.new_radiobuttonshow_profile)
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem( 'Hyperlink Show',width=150, height=30)
        pmenu.set_on_click_listener(self.new_hyperlinkshow_profile)
        profile_new_menu.append(pmenu)
        pmenu = gui.MenuItem( 'Blank',width=150, height=30)
        pmenu.set_on_click_listener(self.new_blank_profile)
        profile_new_menu.append(pmenu)
        
        # shows menu              
        show_menu = gui.MenuItem( 'Show',width=80, height=30)
        show_delete_menu = gui.MenuItem('Delete',width=120, height=30)
        show_delete_menu.set_on_click_listener(self.remove_show)    
        show_edit_menu = gui.MenuItem('Edit',width=120, height=30)
        show_edit_menu.set_on_click_listener(self.m_edit_show)
        show_copy_to_menu = gui.MenuItem( 'Copy To',width=120, height=30)
        show_copy_to_menu.set_on_click_listener(self.copy_show)
        show_add_menu = gui.MenuItem( 'Add',width=120, height=30)
        show_menu.append(show_delete_menu)
        show_menu.append(show_edit_menu)
        show_menu.append(show_copy_to_menu)
        show_menu.append(show_add_menu)


        pmenu = gui.MenuItem('Menu',width=150, height=30)
        pmenu.set_on_click_listener(self.add_menushow)
        show_add_menu.append(pmenu)
        
        pmenu = gui.MenuItem( 'Media Show',width=150, height=30)
        pmenu.set_on_click_listener(self.add_mediashow)
        show_add_menu.append(pmenu)
        
        pmenu = gui.MenuItem('Live Show',width=150, height=30)
        pmenu.set_on_click_listener(self.add_liveshow)
        show_add_menu.append(pmenu)

        pmenu = gui.MenuItem('Hyperlink Show',width=150, height=30)
        pmenu.set_on_click_listener(self.add_hyperlinkshow)
        show_add_menu.append(pmenu)

        pmenu = gui.MenuItem('RadioButton Show',width=150, height=30)
        pmenu.set_on_click_listener(self.add_radiobuttonshow)
        show_add_menu.append(pmenu)

        pmenu = gui.MenuItem( 'Art Mediashow Show',width=150, height=30)
        pmenu.set_on_click_listener(self.add_artmediashow)
        show_add_menu.append(pmenu)

        pmenu = gui.MenuItem( 'Art Liveshow Show',width=150, height=30)
        pmenu.set_on_click_listener(self.add_artliveshow)
        show_add_menu.append(pmenu)

        # medialists menu
        medialist_menu = gui.MenuItem( 'Medialist',width=80, height=30)
        
        medialist_delete_menu = gui.MenuItem( 'Delete',width=120, height=30)
        medialist_delete_menu.set_on_click_listener(self.remove_medialist)

        
        medialist_add_menu = gui.MenuItem( 'Add',width=120, height=30)
        medialist_add_menu.set_on_click_listener(self.menu_add_medialist)
        
        medialist_copy_to_menu = gui.MenuItem('Copy To',width=120, height=30)
        medialist_copy_to_menu.set_on_click_listener(self.copy_medialist)
        
        medialist_menu.append(medialist_add_menu)
        medialist_menu.append(medialist_delete_menu)
        medialist_menu.append(medialist_copy_to_menu)

        # tracks menu
        track_menu = gui.MenuItem('Track',width=80, height=30)

        track_delete_menu = gui.MenuItem('Delete',width=120, height=30)
        track_delete_menu.set_on_click_listener(self.remove_track)
        track_copy_menu = gui.MenuItem('Copy',width=120, height=30)
        track_copy_menu.set_on_click_listener(self.copy_track)
        track_edit_menu = gui.MenuItem( 'Edit',width=120, height=30)
        track_edit_menu.set_on_click_listener(self.m_edit_track)
        track_add_from_dir_menu = gui.MenuItem('Add Directory',width=120, height=30)
        track_add_from_dir_menu.set_on_click_listener(self.add_tracks_from_dir)
        track_add_from_file_menu = gui.MenuItem('Add File',width=120, height=30)
        track_add_from_file_menu.set_on_click_listener(self.add_track_from_file)
        track_new_menu = gui.MenuItem('New',width=120, height=30)

        track_new_video_menu = gui.MenuItem('Video',width=120, height=30)
        track_new_video_menu.set_on_click_listener(self.new_video_track)
        track_new_audio_menu = gui.MenuItem('Audio',width=120,height=30)
        track_new_audio_menu.set_on_click_listener(self.new_audio_track)
        track_new_image_menu = gui.MenuItem( 'Image',width=120, height=30)
        track_new_image_menu.set_on_click_listener(self.new_image_track)
        track_new_web_menu = gui.MenuItem( 'Web',width=120, height=30)
        track_new_web_menu.set_on_click_listener(self.new_web_track)
        track_new_message_menu = gui.MenuItem('Message',width=120, height=30)
        track_new_message_menu.set_on_click_listener(self.new_message_track)
        track_new_show_menu = gui.MenuItem('Show',width=120, height=30)
        track_new_show_menu.set_on_click_listener(self.new_show_track)
        track_new_menu_menu = gui.MenuItem('Menu',width=120, height=30)
        track_new_menu_menu.set_on_click_listener(self.new_menu_track)

        track_new_menu.append(track_new_video_menu)
        track_new_menu.append(track_new_audio_menu)
        track_new_menu.append(track_new_image_menu)
        track_new_menu.append(track_new_web_menu)        
        track_new_menu.append(track_new_message_menu)
        track_new_menu.append(track_new_show_menu)
        track_new_menu.append(track_new_menu_menu)
        
        track_menu.append(track_delete_menu)
        track_menu.append(track_copy_menu)
        track_menu.append(track_edit_menu)
        track_menu.append(track_add_from_dir_menu)
        track_menu.append(track_add_from_file_menu)
        track_menu.append(track_new_menu)


      
        options_menu = gui.MenuItem('Options',width=80, height=30)
        options_edit_menu=gui.MenuItem('Edit',width=80, height=30)
        options_edit_menu.set_on_click_listener(self.edit_options)
        options_menu.append(options_edit_menu)

        # osc menu
        osc_menu = gui.MenuItem( 'OSC',width=80, height=30)  
        osc_create_menu = gui.MenuItem( 'Create',width=120, height=30)
        osc_create_menu.set_on_click_listener(self.create_osc)
        osc_edit_menu = gui.MenuItem( 'Edit',width=120, height=30)
        osc_edit_menu.set_on_click_listener(self.edit_osc)
        osc_menu.append(osc_create_menu)
        osc_menu.append(osc_edit_menu)


        config_menu=gui.MenuItem( 'Config',width=80, height=30)
        config_menu.append(osc_menu)
        
        # help menu
        help_menu = gui.MenuItem( 'Help',width=80, height=30)
        help_text_menu = gui.MenuItem( 'Help',width=80, height=30)
        help_text_menu.set_on_click_listener(self.show_help)
        about_menu = gui.MenuItem( 'About',width=80, height=30)
        about_menu.set_on_click_listener(self.show_about)
        help_menu.append(help_text_menu)
        help_menu.append(about_menu)

        update_menu = gui.MenuItem('Update',width=80, height=30)
        update_all_menu = gui.MenuItem('Update All',width=80, height=30)
        update_all_menu.set_on_click_listener(self.m_update_all)
        update_menu.append(update_all_menu)
        


        menu.append(profile_menu)
        menu.append(show_menu)
        menu.append(medialist_menu)
        menu.append(track_menu)      
        menu.append(config_menu)
        menu.append(options_menu)
        menu.append(update_menu)
        menu.append(help_menu)

        menubar.append(menu)
        
        #shows and medialists
        shows_label=gui.Label('<b>Shows</b>',width=300, height=20)
        shows_label.style['margin']='5px'
        self.shows_display= gui.ListView(width=300, height=150)
        self.shows_display.set_on_selection_listener(self.show_selected)
        
        medialists_label=gui.Label('<b>Medialists</b>',width=300, height=25)
        medialists_label.style['margin']='5px'
        self.medialists_display= gui.ListView(width=300, height=150)
        self.medialists_display.set_on_selection_listener(self.medialist_selected)

        left_frame.append(shows_label)
        left_frame.append(self.shows_display)         
        left_frame.append(medialists_label)
        left_frame.append(self.medialists_display)

        #edit show button
        edit_show = gui.Button('Edit\nShow',width=50, height=50)
        edit_show.set_on_click_listener(self.m_edit_show)
        middle_frame.append(edit_show)

        #tracks
        tracks_label=gui.Label('<b>Tracks in Selected Medialist</b>',width=300, height=20)
        tracks_label.style['margin']='5px'
        self.tracks_display= gui.ListView(width=300, height=350)
        self.tracks_display.set_on_selection_listener(self.track_selected)

        right_frame.append(tracks_label)
        right_frame.append(self.tracks_display)  

        #tracks buttons
        add_track = gui.Button('Add',width=50, height=50)
        add_track.set_on_click_listener(self.add_track_from_file)
        updown_frame.append(add_track)
        
        edit_track = gui.Button('Edit',width=50, height=50)
        edit_track.set_on_click_listener(self.m_edit_track)
        updown_frame.append(edit_track)        

        up_track = gui.Button('Up',width=50, height=50)
        up_track.set_on_click_listener(self.move_track_up)
        updown_frame.append(up_track)

        down_track = gui.Button('Down',width=50, height=50)
        down_track.set_on_click_listener(self.move_track_down)
        updown_frame.append(down_track)

        delete_track = gui.Button('Del',width=50, height=50)
        delete_track.set_on_click_listener(self.remove_track)
        updown_frame.append(delete_track)

        root.append(menubar)
        self.profile_name_field=gui.Label('<br>')
        root.append(self.profile_name_field)

        bottom_frame.append(left_frame)
        bottom_frame.append(middle_frame)
        bottom_frame.append(right_frame)
        bottom_frame.append(updown_frame)
        root.append(bottom_frame)
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

    def show_help (self,widget):
        OKDialog("Help","Please Read 'manual.pdf'",width=400,height=200).show(self)

  
    def show_about (self,widget):
        OKDialog("About","Web Editor for Pi Presents Profiles<br>"
                              +"For profiles of version: " + self.editor_issue + "<br>Author: Ken Thompson"
                              +"<br>Website: http://pipresents.wordpress.com/<br>",width=400,height=200).show(self)

    def validate_profile(self,widget):
        if self.current_showlist != None:
            val =Validator('Validation Result')
            val.show(self)
            val.validate_profile(self.editor_dir,self.pp_home_dir,self.pp_profile_dir,self.editor_issue,True)


    # **************
    # OPTIONS
    # **************


    def edit_options(self,widget):
        self.eo.edit(self.edit_options_callback)
        self.eo.show(self)

    def edit_options_callback(self):
        self.eo.read_options()
        self.init()
        self.empty_lists()
        



    # **************
    # OSC CONFIGURATION
    # **************

    def create_osc(self,widget):
        if self.pp_profile_dir=='':
            OKDialog('Create OSC','Profile must be open to create an OSC configuration file').show(self)
            return
        # print 'create',OSCConfig.options_file
        if self.osc_config.read() is False:
            iodir=self.pp_profile_dir+os.sep+'pp_io_config'
            if not os.path.exists(iodir):
                os.makedirs(iodir)
            self.osc_config.create()
            OKDialog('Create OSC','OSC Configuration File created').show(self)
        else:
            OKDialog('Create OSC','OSC Configuration File already exists').show(self)

    def edit_osc(self,widget):
        if self.pp_profile_dir=='':
            OKDialog('Edit OSC','Profile must be open to edit an OSC configuration file').show(self)
            return
        # print 'edit',OSCConfig.options_file
        if self.osc_config.read() is False:
            OKDialog('Create OSC','Create an OSC Configuration File first').show(self)
            return
        self.osc_editor=OSCWebEditor()
        self.osc_editor.edit()
        self.osc_editor.show(self)



    
    # **************
    # PROFILES
    # **************

    def open_existing_profile(self,widget):
        initial_dir=self.pp_home_dir+os.sep+"pp_profiles"+self.pp_profiles_offset
        if os.path.exists(initial_dir) is False:
            OKDialog('Open Profile',"Profiles directory not found: " + initial_dir + "<br><br>Hint: Data Home option must end in pp_home").show(self)
            return
        open_existing_profile_dialog = FileSelectionDialog('Open Profile','Select profile',False, initial_dir,allow_folder_selection=True,
                                                           allow_file_selection=False, 
                                                           callback=self.open_existing_profile_dialog_confirm) #width=600,height=200,
        # open_existing_profile_dialog.set_on_confirm_value_listener(self.open_existing_profile_dialog_confirm)
        open_existing_profile_dialog.show(self)


    def open_existing_profile_dialog_confirm(self,filelist):
        # print 'file list',filelist
        if len(filelist)==0:
            OKDialog('Open Profile',"Nothing Selected").show(self)
            return
        # print 'filelist[0]',filelist[0]
        self.open_profile(filelist[0])
        

    def open_profile(self,dir_path):
        if self.editor_version()!= self.definitions_version():
            OKDialog('Open Profile','Incorrect version of Editor: '+ self.editor_issue +'<br>Definitions are: '+ PPdefinitions.DEFINITIONS_VERSION_STRING).show(self)
            return
        showlist_file = dir_path + os.sep + "pp_showlist.json"
        #print 'open profile',showlist_file
        if os.path.exists(showlist_file) is False:
            OKDialog('Open Profile',"Not a Profile: " + dir_path).show(self)
            return
        self.pp_profile_dir = dir_path
        self.pp_select_offset=os.path.relpath(self.pp_profile_dir,self.pp_home_dir+os.sep+"pp_profiles"+self.pp_profiles_offset)
        # print self.pp_select_offset
        OSCConfig.options_file=self.pp_profile_dir+ os.sep+'pp_io_config'+os.sep+'osc.cfg'
        self.osc_config_file=self.pp_profile_dir+os.sep+'pp_io_config'+os.sep+'osc.cfg'

        self.open_showlist(self.pp_profile_dir)

        if self.current_showlist.profile_version() == self.definitions_version() and self.force_update is False:
            self.profile_finish_open()
            return
        
        if self.current_showlist.profile_version()> self.definitions_version():
            OKDialog('Open Profile',"ERROR, Version of profile is greater than Pi Presents").show(self)
            return
            
        OKCancelDialog('Open Profile',"Version of Profile is earlier then Pi Presents<br>OK to Update?",self.profile_update_confirm).show(self)


    def profile_update_confirm(self,result):
        if result is False:
            return
        self.update_profile()
        self.profile_finish_open()
        OKDialog('Open Profile','Profile has been updated to '+ PPdefinitions.DEFINITIONS_VERSION_STRING).show(self)

    def profile_finish_open(self):
        self.current_medialist=None
        self.current_showlist=None
        self.current_show=None
        self.open_showlist(self.pp_profile_dir)        
        self.refresh_shows_display()        
        self.open_medialists(self.pp_profile_dir)
        self.refresh_tracks_display()
        self.profile_name_field.set_text('<b>'+self.pp_profile_dir+'</b>')


    def new_profile(self,profile):
        d = InputDialog("New Profile","Name",width=400,height=200,callback=self.new_profile_confirm)
        self.new_profile_template=profile

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


        
    def new_exhibit_profile(self,widget):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_exhibit_1p3'
        self.new_profile(profile)

    def new_interactive_profile(self,widget):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_interactive_1p3'
        self.new_profile(profile)

    def new_menu_profile(self,widget):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_menu_1p3'
        self.new_profile(profile)

    def new_presentation_profile(self,widget):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_presentation_1p3'
        self.new_profile(profile)

    def new_blank_profile(self,widget):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep +"ppt_blank_1p3"
        self.new_profile(profile)

    def new_mediashow_profile(self,widget):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_mediashow_1p3'
        self.new_profile(profile)
        
    def new_liveshow_profile(self,widget):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_liveshow_1p3'
        self.new_profile(profile)

    def new_artmediashow_profile(self,widget):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_artmediashow_1p3'
        self.new_profile(profile)
        
    def new_artliveshow_profile(self,widget):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_artliveshow_1p3'
        self.new_profile(profile)

    def new_radiobuttonshow_profile(self,widget):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_radiobuttonshow_1p3'
        self.new_profile(profile)

    def new_hyperlinkshow_profile(self,widget):
        profile = self.editor_dir+os.sep+'pp_resources'+os.sep+'pp_templates'+os.sep + 'ppt_hyperlinkshow_1p3'
        self.new_profile(profile)


    def delete_profile(self,widget,to_file=''):
        if self.pp_profile_dir != '':
            OKCancelDialog('Delete Profile','Delete Open Profile?',self.delete_profile_confirm).show(self)


    def delete_profile_confirm(self,result):

        if result is False:
            return
        shutil.rmtree(self.pp_profile_dir)
        self.pp_profile_dir=''
        self.current_showlist=None
        self.current_show=None
        self.current_medialist=None
        self.shows_display.empty()
        self.medialists_display.empty()
        self.tracks_display.empty()

    def copy_profile(self,widget,to_file=''):
        if self.pp_profile_dir != '':
            if to_file is '':
                d = InputDialog("Copy Profile","To File",width=400,height=200,callback=self.copy_profile_confirm)
                d.show(self)
            else:
                self.copy_profile_confirm(to_file)

    def copy_profile_confirm(self,to_file):
        # print self.from_file,to_file
        if to_file == "":
            OKDialog("Copy Profile","Name is blank").show(self)
            return ''
        to_dir = self.pp_home_dir + os.sep + "pp_profiles"+ self.pp_profiles_offset+os.sep+to_file
        self.copy_profile_dir(self.pp_profile_dir,to_dir)


    def copy_profile_dir(self,from_dir,to_dir):
       
        if os.path.exists(to_dir) is  True:
            OKDialog("Copy Profile","Profile already exists " + to_dir).show(self)
            return
        if os.path.exists(from_dir) is  False:
            OKDialog("Copy Profile","Profile not found " + from_dir).show(self)
            return
        shutil.copytree(from_dir,to_dir)



    # ***************************************
    # Shows
    # ***************************************

    def open_showlist(self,profile_dir):
        showlist_file = profile_dir + os.sep + "pp_showlist.json"
        self.current_showlist=ShowList()
        self.current_showlist.open_json(showlist_file)


    def save_showlist(self,showlist_dir):
        if self.current_showlist is not None:
            showlist_file = showlist_dir + os.sep + "pp_showlist.json"
            self.current_showlist.save_list(showlist_file)
            
    def add_mediashow(self,widget):
        self.add_show(PPdefinitions.new_shows['mediashow'])

    def add_liveshow(self,widget):
        self.add_show(PPdefinitions.new_shows['liveshow'])

    def add_radiobuttonshow(self,widget):
        self.add_show(PPdefinitions.new_shows['radiobuttonshow'])

    def add_hyperlinkshow(self,widget):
        self.add_show(PPdefinitions.new_shows['hyperlinkshow'])

    def add_artliveshow(self,widget):
        self.add_show(PPdefinitions.new_shows['artliveshow'])

    def add_artmediashow(self,widget):
        self.add_show(PPdefinitions.new_shows['artmediashow'])
        
    def add_menushow(self,widget):
        self.add_show(PPdefinitions.new_shows['menu'])

    def add_start(self,widget):  
        self.add_show(PPdefinitions.new_shows['start'])


    def add_show(self,default):
        # append it to the showlist and then add the medialist
        if self.current_showlist is not None:
            self.default_show=default
            d = InputDialog("Add Show","Show Reference",width=400,height=200,callback=self.add_show_confirm)
            d.show(self)

    def add_show_confirm(self,name):
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
        if mediafile != '':
            copied_show['medialist']=mediafile
        self.current_showlist.append(copied_show)
        self.save_showlist(self.pp_profile_dir)
        self.refresh_shows_display()
        if copied_show['type']=='menu':
            self.open_medialist_by_name(mediafile)
            self.new_track(PPdefinitions.new_tracks['menu'],None)

            
    def remove_show(self,widget):
        if  self.current_showlist is not None and self.current_showlist.length()>0 and self.current_showlist.show_is_selected():
            show=self.current_showlist.selected_show()
            OKCancelDialog("Delete Show","Delete "+ show['title']+ " Are you sure?",self.remove_show_confirm).show(self)

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
            obj = gui.ListItem(value,width=300, height=20)
            self.shows_display.append(obj,key=key)
            key+=1
        if self.current_showlist.show_is_selected():
            self.shows_display.select_by_key(self.current_showlist.selected_show_index())            
            # self.shows_display.show()

            
    def show_selected(self,widget,event):
        if self.current_showlist is not None and self.current_showlist.length()>0:
            mouse_item_index=self.shows_display.get_key()
            self.current_showlist.select(mouse_item_index)
            self.refresh_shows_display()
            if 'medialist' in self.current_showlist.selected_show():
                medialist=self.current_showlist.selected_show()['medialist']
                if medialist !='':
                    if os.path.exists(self.pp_profile_dir+os.sep+medialist):
                        self.open_medialist_by_name(medialist)
                    else:
                        #deal with hanging medialist in show
                        self.open_medialist_by_name('')
                        OKDialog('Select Show','Medialist in specified in the Show does not exist').show(self)
            else:
                #deal with start show that does not have a medialist
                    self.open_medialist_by_name('')
                    
    def copy_show(self,widget):
        if  self.current_showlist is not None and self.current_showlist.show_is_selected():
            self.add_show(self.current_showlist.selected_show())

        
    def m_edit_show(self,widget):
        self.edit_show(PPdefinitions.show_types,PPdefinitions.show_field_specs)
        

    def edit_show(self,show_types,field_specs):
        if self.current_showlist is not None and self.current_showlist.show_is_selected():
            self.edit_show_dialog=WebEditItem("Edit Show",self.current_showlist.selected_show(),show_types,field_specs,self.show_refs(),
                       self.initial_media_dir,self.pp_home_dir,self.pp_profile_dir,'show',self.finished_edit_show)
            self.edit_show_dialog.show(self)
            show_type=self.current_showlist.selected_show()['type']
            if show_type=='start':
                self.edit_show_dialog.show_tab('sched')
            else:
                self.edit_show_dialog.show_tab('show')
                
    def finished_edit_show(self):
        self.save_showlist(self.pp_profile_dir)
        self.refresh_shows_display()



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
        self.medialists_display.empty()
        key=0
        for index in range (len(self.medialists)):
            obj = gui.ListItem(self.medialists[index],width=300, height=20)
            self.medialists_display.append(obj, key=key)
            key+=1
        self.current_medialists_index=-1
        self.current_medialist=None

    def menu_add_medialist(self,widget):
        self.add_medialist(name=None)
    

    def add_medialist(self,name=None):
        if self.current_showlist != None:
            if name is None:
                d = InputDialog("Add Medialist","File Name",width=400,height=200,callback=self.add_medialist_confirm)
                d.show(self)
            else:
                medialist_name=self.add_medialist_confirm(name)
                return medialist_name
            

    def add_medialist_confirm(self,name):
        if name == "":
            OKDialog("Add Medialist","Name is blank").show(self)
            return  ''
        if not name.endswith(".json"):
            name=name+(".json")

        path = self.pp_profile_dir + os.sep + name
        if os.path.exists(path) is  True:
            OKDialog("Add Medialist","Medialist file exists<br>" + path).show(self)
            return ''
        nfile = open(path,'wb')
        nfile.write("{")
        nfile.write("\"issue\":  \""+PPdefinitions.DEFINITIONS_VERSION_STRING+"\",\n")
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


    def copy_medialist(self,widget,to_file=None):
        if self.current_showlist != None:
            if self.current_medialist is not None:
                #from_file= self.current_medialist
                self.from_file= self.medialists[self.current_medialists_index]
                if to_file is None:
                    d = InputDialog("Copy Medialist","File",width=400,height=200,callback=self.copy_medialist_confirm)
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


    def remove_medialist(self,widget):
        if self.current_medialist is not None:
            name = self.medialists[self.current_medialists_index]
            OKCancelDialog("Delete Medialist","Delete "+ name + " Are you sure?",self.remove_medialist_confirm).show(self)

    def remove_medialist_confirm(self,result):
        if result is True:
            os.remove(self.pp_profile_dir+ os.sep + self.medialists[self.current_medialists_index])
            self.open_medialists(self.pp_profile_dir)
            self.refresh_medialists_display()
            self.refresh_tracks_display()


    def open_medialist_by_name(self,name):
        if name=='':
            self.current_medialist=None
            self.refresh_tracks_display()
            self.refresh_medialists_display()
        else:
            self.current_medialist=MediaList('ordered')
            if not self.current_medialist.open_list(self.pp_profile_dir+ os.sep + name,self.definitions_version()):
                OKDialog(self,"medialist is a different version to showlist: "+ str(self.medialists[self.current_medialists_index])).show(self)
                return
            self.refresh_tracks_display()
            self.refresh_medialists_display()
            self.medialists_display.select_by_value(name)
            self.current_medialists_index = self.medialists_display.get_key()


    def medialist_selected(self,widget,key):
        """
        user clicks on a medialst in a profile so try and select it.
        """
        # print 'selected',type(self.medialists_display.get_key()),self.medialists_display.get_key()
        if len(self.medialists)>0:
            self.current_medialists_index=self.medialists_display.get_key()
            self.current_medialist=MediaList('ordered')
            if not self.current_medialist.open_list(self.pp_profile_dir+ os.sep + self.medialists[self.current_medialists_index],self.definitions_version()):
                OKDialog(self,"medialist is a different version to showlist: "+ str(self.medialists[self.current_medialists_index])).show(self)
                return
            self.refresh_tracks_display()
            self.refresh_medialists_display()
            self.current_showlist.deselect_all()
            self.refresh_shows_display()

    def refresh_medialists_display(self):
        # print 'refresh medialists'
        self.medialists_display.empty()
        key=0
        for index in range (len(self.medialists)):
            obj = gui.ListItem(self.medialists[index],width=300, height=20)
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
        # print medialist_file
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
                obj = gui.ListItem(self.current_medialist.track(index)['title']+track_ref_string,width=300, height=20)
                self.tracks_display.append(obj,key=key)
                key+=1                
            if self.current_medialist.track_is_selected():
                self.tracks_display.select_by_key(self.current_medialist.selected_track_index())  

            
    def  track_selected(self,widget,key):
        # print 'track sel', type(self.tracks_display.get_key())
        if self.current_medialist is not None and self.current_medialist.length()>0:
            mouse_item_index=self.tracks_display.get_key()
            self.current_medialist.select(mouse_item_index)
            self.refresh_tracks_display()

    def m_edit_track(self,widget):
        self.edit_track(PPdefinitions.track_types,PPdefinitions.track_field_specs)

    def edit_track(self,track_types,field_specs):      
        if self.current_medialist is not None and self.current_medialist.track_is_selected():
            self.edit_track_dialog=WebEditItem("Edit Track",self.current_medialist.selected_track(),track_types,field_specs,
                       self.show_refs(),self.initial_media_dir,self.pp_home_dir,self.pp_profile_dir,'track',self.finished_edit_track)
            self.edit_track_dialog.show(self)
            self.edit_track_dialog.show_tab('track')

    def finished_edit_track(self):
        self.refresh_tracks_display()
        self.save_medialist()        
            
    def move_track_up(self,widget):
        if self.current_medialist is not None and self.current_medialist.track_is_selected():
            self.current_medialist.move_up()
            self.refresh_tracks_display()
            self.save_medialist()

    def move_track_down(self,widget):
        if self.current_medialist is not None and self.current_medialist.track_is_selected():
            self.current_medialist.move_down()
            self.refresh_tracks_display()
            self.save_medialist()

    def copy_track(self,widget):
        if self.current_medialist is not None and self.current_medialist.track_is_selected():
            self.current_medialist.copy()
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

    def new_message_track(self,widget):
        self.new_track(PPdefinitions.new_tracks['message'],None)
            
    def new_video_track(self,widget):
        self.new_track(PPdefinitions.new_tracks['video'],None)
  
    def new_audio_track(self,widget):
        self.new_track(PPdefinitions.new_tracks['audio'],None)

    def new_web_track(self,widget):
        self.new_track(PPdefinitions.new_tracks['web'],None)
        
    def new_image_track(self,widget):
        self.new_track(PPdefinitions.new_tracks['image'],None)

    def new_show_track(self,widget):
        self.new_track(PPdefinitions.new_tracks['show'],None)

    def new_menu_track(self,widget):
        # print 'new menu track'
        self.new_track(PPdefinitions.new_tracks['menu'],None)
 
    def remove_track(self,widget):
        if  self.current_medialist is not None and self.current_medialist.length()>0 and self.current_medialist.track_is_selected():
            track = self.current_medialist.selected_track()
            OKCancelDialog("Delete Track",'Delete '+ track['title']+  " Are you sure?",self.remove_track_confirm).show(self)

    def remove_track_confirm(self,result):
        # print 'confirm',result
        if result is True:
            index= self.current_medialist.selected_track_index()
            self.current_medialist.remove(index)
            self.save_medialist()
            self.refresh_tracks_display()
            
    def add_track_from_file(self,widget):
        if self.current_medialist is None:
            return
        add_track_from_file_dialog = FileSelectionDialog('Add Track', 'Select Tracks',
                                                         multiple_selection =True,
                                                         allow_folder_selection=False,
                                                         selection_folder =self.eo.initial_media_dir,
                                                         callback=self.add_track_from_file_dialog_confirm) #600,200,
        add_track_from_file_dialog.show(self)


    def add_track_from_file_dialog_confirm(self,filelist):
        if len(filelist)==0:
            OKDialog('Add Track',"Nothing Selected").show(self)
            return
        for file_path in filelist:
            file_path=os.path.normpath(file_path)
            # print "file path ", file_path
            self.add_track(file_path)
        self.save_medialist()

    def add_tracks_from_dir(self,widget):
        if self.current_medialist is None: return
        add_tracks_from_dir_dialog = FileSelectionDialog('Add Directory', 'Select Directory',
                                    multiple_selection = False, allow_file_selection=False,
                                    selection_folder = self.eo.initial_media_dir,callback=self.add_tracks_from_dir_dialog_confirm)
        add_tracks_from_dir_dialog.show(self)


    def add_tracks_from_dir_dialog_confirm(self,result):
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


    def add_track(self,file_path):
        location=calculate_relative_path(file_path,self.pp_home_dir,self.pp_profile_dir)
        (root,title)=os.path.split(file_path)
        (root,ext)= os.path.splitext(file_path)
        if ext.lower() in PPdefinitions.IMAGE_FILES:
            self.new_track(PPdefinitions.new_tracks['image'],{'title':title,'track-ref':'','location':location})
        elif ext.lower() in PPdefinitions.VIDEO_FILES:
            self.new_track(PPdefinitions.new_tracks['video'],{'title':title,'track-ref':'','location':location})
        elif ext.lower() in PPdefinitions.AUDIO_FILES:
            self.new_track(PPdefinitions.new_tracks['audio'],{'title':title,'track-ref':'','location':location})
        elif ext.lower() in PPdefinitions.WEB_FILES:
            self.new_track(PPdefinitions.new_tracks['web'],{'title':title,'track-ref':'','location':location})
        else:
            OKDialog('Add Track',file_path + " - cannot determine track type, use menu track>new").show(self)




# *********************************************
# UPDATE PROFILE
# **********************************************

    def editor_version(self):
        vitems=self.editor_issue.split('.')
        if len(vitems)==2:
            # cope with 2 digit version numbers before 1.3.2
            return 1000*int(vitems[0])+100*int(vitems[1])
        else:
            return 1000*int(vitems[0])+100*int(vitems[1])+int(vitems[2])

    def definitions_version(self):
        # don't need to cope with earlier as this editor will be used only with 1.3.2 or later of defs
        # cope with earlier pp_definitions which does not have a version number
        # just make it 1.3.2 as thr first one to have a version in defs.
        #if not hasattr(PPdefinitions,'DEFINITIONS_VERSION_STRING'):
        #    return 1302
        #else:
        return PPdefinitions().definitions_version()


    def show_versions(self,widget):
        print 'editor', self.editor_version()
        print 'definitions', self.definitions_version()
        if self.current_showlist is not None:
            print 'profile', self.current_showlist.profile_version()
        else:
            print 'not open'


    def m_update_all(self,widget):
          all_dir=self.pp_home_dir+os.sep+'pp_profiles'+self.pp_profiles_offset
          OKCancelDialog('Update All','OK to update all profiles in <br>'+ all_dir,self.update_all_confirm).show(self)

    def update_all_confirm(self,result):
        if result is True:
            self.update_all()
          
    def update_all(self):
        self.report=ReportDialog('Update Report')
        self.report.append_line("Update to Version " + PPdefinitions.DEFINITIONS_VERSION_STRING)
        self.init()

        profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'+self.pp_profiles_offset
        for profile_file in os.listdir(profiles_dir):
            self.pp_profile_dir = profiles_dir + os.sep + profile_file
            if not os.path.exists(self.pp_profile_dir+os.sep+"pp_showlist.json"):
                self.report.append_line(profile_file+ ' - Not a profile')
            else:
                self.pp_select_offset=profile_file
                self.current_showlist=ShowList()
                self.current_showlist.open_json(self.pp_profile_dir+os.sep+"pp_showlist.json")
                if self.current_showlist.profile_version() < self.definitions_version() or self.force_update is True:
                    self.update_profile()
                    self.report.append_line(profile_file + ' - UPDATED')
                elif self.current_showlist.profile_version()>self.definitions_version():
                    self.report.append_line(profile_file + ' - Version of profile is later than Pi Presents')
                elif self.current_showlist.profile_version() == self.definitions_version():
                    self.report.append_line(profile_file + ' - Profile is up to date')
        self.init()
        self.report.show(self)
        

    def backup_profile(self):
        # make a backup directory for profiles at this level
        backup_dir=self.pp_home_dir+os.sep+'pp_profiles.bak'+os.sep+self.pp_profiles_offset+os.sep+self.pp_select_offset
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        #make a directory for this profile
        # if not os.path.exists(backup_dir):
            # os.makedirs(backup_dir+os.sep+self.profile_name)
                
        for this_file in os.listdir(self.pp_profile_dir):
            if this_file.endswith(".json") and this_file !='schedule.json':
                from_file=self.pp_profile_dir+os.sep+this_file
                to_file=backup_dir+os.sep+this_file
                # print 'backup',from_file,to_file
                shutil.copy(from_file,to_file)


    def move_io_config(self):
        if not os.path.exists(self.pp_profile_dir+os.sep+'pp_io_config'):
            os.makedirs(self.pp_profile_dir+os.sep+'pp_io_config')
        # print 'io',self.pp_profile_dir,self.pp_profile_dir+os.sep+'pp_io_config'
        if os.path.exists(self.pp_profile_dir+os.sep+'gpio.cfg'):
            os.rename(self.pp_profile_dir+os.sep+'gpio.cfg',self.pp_profile_dir+os.sep+'pp_io_config'+os.sep+'gpio.cfg')
        if os.path.exists(self.pp_profile_dir+os.sep+'keys.cfg'):
            os.rename(self.pp_profile_dir+os.sep+'keys.cfg',self.pp_profile_dir+os.sep+'pp_io_config'+os.sep+'keys.cfg')                          
        if os.path.exists(self.pp_profile_dir+os.sep+'screen.cfg'):
            os.rename(self.pp_profile_dir+os.sep+'screen.cfg',self.pp_profile_dir+os.sep+'pp_io_config'+os.sep+'screen.cfg')                        
        if os.path.exists(self.pp_profile_dir+os.sep+'osc.cfg'):
            os.rename(self.pp_profile_dir+os.sep+'osc.cfg',self.pp_profile_dir+os.sep+'pp_io_config'+os.sep+'osc.cfg')  
        
           
    def update_profile(self):
        self.profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'+self.pp_profiles_offset
        # sef.pp_profile_dir already set
        self.profile_name=self.pp_profile_dir.split(os.sep)[-1]
        self.backup_profile()
        self.update_medialists()   # medialists and their tracks
        self.update_shows()         #shows in showlist, also creates menu tracks and moves io_config for 1.2>1.3
        

        

    def update_shows(self):
        # open showlist into a list of dictionaries
        # self.mon.log (self,"Updating show ")
        ifile  = open(self.pp_profile_dir + os.sep + "pp_showlist.json", 'rb')
        sdict = json.load(ifile)
        ifile.close()
        shows = sdict['shows']
        if 'issue' in sdict:
            profile_version_string= sdict['issue']
        else:
            profile_version_string="1.0"
                
        vitems=profile_version_string.split('.')
        if len(vitems)==2:
            # cope with 2 digit version numbers before 1.3.2
            profile_version = 1000*int(vitems[0])+100*int(vitems[1])
        else:
            profile_version = 1000*int(vitems[0])+100*int(vitems[1])+int(vitems[2])

        #special 1.2 to 1.3 move io configs to pp_io_config
        
        if profile_version == 1200:
            self.move_io_config()

        # special 1.2>1.3 create menu medialists with menu track from show
        #go through shows - if type = menu and version is greater copy its medialist to a new medialist with  name = <show-ref>-menu1p3.json
        for show in shows:
            #create a new medialist medialist != show-ref as menus can't now share medialists
            if show['type']=='menu' and profile_version == 1200:
                to_file=show['show-ref']+'-menu1p3.json'
                from_file = show['medialist']
                if to_file != from_file:
                    self.copy_medialist_file(from_file,to_file)
                else:
                    # self.mon.warn(self, 'medialist file' + to_file + ' already exists, must exit with incomplete update')
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
        dic={'issue':PPdefinitions.DEFINITIONS_VERSION_STRING,'shows':replacement_shows}
        ofile  = open(self.pp_profile_dir + os.sep + "pp_showlist.json", "wb")
        json.dump(dic,ofile,sort_keys=True,indent=1)
        return True


    def transfer_show_params(self,show,tracks,track_ref,fields):
        # find the menu track in medialist
        # 1.2 - 1.3 menu only
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
        for this_file in os.listdir(self.pp_profile_dir):
            if this_file.endswith(".json") and this_file not in  ('pp_showlist.json','schedule.json'):
                # self.mon.log (self,"Updating medialist " + this_file)
                # open a medialist and update its tracks
                ifile  = open(self.pp_profile_dir + os.sep + this_file, 'rb')
                tracks = json.load(ifile)['tracks']
                ifile.close()
                replacement_tracks=self.update_tracks(tracks)
                dic={'issue':PPdefinitions.DEFINITIONS_VERSION_STRING,'tracks':replacement_tracks}
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
            


# ****************************************
# OPTIONS
# ****************************************

class Options(AdaptableDialog):

    def __init__(self, *args):
        super(Options, self).__init__(title='<b>Edit Options</b>',width=450,height=300,confirm_name='Ok',cancel_name='Cancel')

        # build the gui in _init as it is subclassed
        home_dir_field= gui.TextInput(width=250, height=30)
        self.append_field_with_label('Pi Presents Data Home:',home_dir_field,key='home_dir')
        media_dir_field= gui.TextInput(width=250, height=30)
        self.append_field_with_label('Inital directory for Media:',media_dir_field,key='media_dir')
        offset_field= gui.TextInput(width=250, height=30)
        self.append_field_with_label('Offset for Current Profiles:',offset_field,key='offset')
        error_field= gui.Label('',width=400, height=30)
        self.append_field(error_field,'error')



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

    def confirm_dialog(self):
        text=''

        home_dir=self.get_field('home_dir').get_value()
        media_dir=self.get_field('media_dir').get_value()
        offset=self.get_field('offset').get_value()
        # print 'confirm',home_dir
        
        if os.path.exists(home_dir) is  False:
            OKDialog('Editor Options','Data Home directory not found ' + home_dir).show(self._base_app_instance)
            text="<b>Data Home directory not found "+home_dir+ "</b>"
            self.get_field('error').set_text(text)
            return

        if os.path.exists(media_dir) is  False:
            OKDialog('Editor Options','Media directory not found ' + media_dir).show(self._base_app_instance)
            text="<b>Media directory not found " + media_dir + "</b>"
            self.get_field('error').set_text(text)
            return

        path=home_dir+os.sep+'pp_profiles'+ offset
        if os.path.exists(path) is  False:
            OKDialog('Editor Options','Current Profiles Directory not found '+path).show(self._base_app_instance)
            text="<b> Current Profiles Directory not found "+path+ "</b>"
            self.get_field('error').set_text(text)
            return
        
        self.get_field('error').set_text('')
        # print 'options hide'
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

    # get command options
    command_options=web_ed_options()

    native = command_options['native']
    remote = command_options['remote']

    mode='local'
    if native is True:
        mode='native'
    if remote is True:
        mode= 'remote'
    
    # get directory holding the code
    editor_dir=sys.path[0]
    # print editor_dir
    if not os.path.exists(editor_dir+os.sep+"pp_web_editor.py"):
        print "Bad Application Directory"
        exit()
    network=Network()
    if mode == 'remote':
        # wait for network to be available
        print 'Waiting for Network'
        success=network.wait_for_network(10)
        if success is False:
            print 'Failed to connect to network after 10 seconds'     
            exit()   


    # check pp_web.cfg
    editor_options_file_path=editor_dir+os.sep+'pp_config'+os.sep+'pp_web.cfg'
    if not os.path.exists(editor_options_file_path):
        print 'pp_web.cfg not found at ' + editor_options_file_path
        # tkMessageBox.showwarning("Pi Presents Web Editor",'pp_web.cfg not found at ' + editor_options_file_path)
        exit()

    print 'Found pp_web.cfg in ', editor_options_file_path

    network.read_config(editor_options_file_path)
    if mode == 'remote':
        # get interface and IP details of preferred interface
        interface,ip = network.get_preferred_ip()
        print 'Network details ' + network.unit + ' ' + interface + ' ' + ip


    start_browser=False
    if mode =='local':
        ip= '127.0.0.1'
        start_browser=True

    if mode == 'native':
        start(PPWebEditor, standalone=True)
        exit()    
    else:
        # start the web server to serve the Web Editor App
        start(PPWebEditor,address=ip, port=network.editor_port,username=network.editor_username,password=network.editor_password,
          multiple_instance=True,enable_file_cache=True, debug=False,
          update_interval=0.3, start_browser=start_browser)
        exit()


