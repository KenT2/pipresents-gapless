#! /usr/bin/env python

from Tkinter import Tk, StringVar, Menu,Frame,Label,Button,Scrollbar,Listbox,Entry
from Tkinter import Y,END,TOP,BOTH,LEFT,RIGHT,VERTICAL,SINGLE,NONE,W
import tkFileDialog
import tkMessageBox
import tkSimpleDialog
import os
import sys
import ConfigParser
import shutil
import json
import copy
import string

from pp_edititem import EditItem
from pp_medialist import MediaList
from pp_showlist import ShowList
from pp_utils import Monitor
from pp_options import ed_options
from pp_validate import Validator
from pp_definitions import PPdefinitions

# **************************
# Pi Presents Editor Class
# *************************

class PPEditor(object):

    # ***************************************
    # INIT
    # ***************************************

    def __init__(self):
    
        self.editor_issue="1.2"

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
        self.mon.on()

        if self.command_options['debug']  is  True:
            Monitor.global_enable=True
        else:
            Monitor.global_enable=False

        self.mon.log (self, "Pi Presents Editor is starting")

        self.mon.log (self," OS and separator " + os.name +'  ' + os.sep)
        self.mon.log(self,"sys.path[0] -  location of code: code "+sys.path[0])


        # set up the gui
 
        # root is the Tkinter root widget
        self.root = Tk()
        self.root.title("Editor for Pi Presents")

        # self.root.configure(background='grey')

        self.root.resizable(False,False)

        # define response to main window closing
        self.root.protocol ("WM_DELETE_WINDOW", self.app_exit)

        # bind some display fields
        self.filename = StringVar()
        self.display_selected_track_title = StringVar()
        self.display_show = StringVar()


        # define menu
        menubar = Menu(self.root)

        profilemenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        profilemenu.add_command(label='Open', command = self.open_existing_profile)
        profilemenu.add_command(label='Validate', command = self.validate_profile)
        menubar.add_cascade(label='Profile', menu = profilemenu)

        ptypemenu = Menu(profilemenu, tearoff=0, bg="grey", fg="black")
        ptypemenu.add_command(label='Exhibit', command = self.new_exhibit_profile)
        ptypemenu.add_command(label='Media Show', command = self.new_mediashow_profile)
        ptypemenu.add_command(label='Menu', command = self.new_menu_profile)
        ptypemenu.add_command(label='Presentation', command = self.new_presentation_profile)
        ptypemenu.add_command(label='Interactive', command = self.new_interactive_profile)
        ptypemenu.add_command(label='Live Show', command = self.new_liveshow_profile)
        ptypemenu.add_command(label='RadioButton Show', command = self.new_radiobuttonshow_profile)
        ptypemenu.add_command(label='Hyperlink Show', command = self.new_hyperlinkshow_profile)
        ptypemenu.add_command(label='Blank', command = self.new_blank_profile)
        profilemenu.add_cascade(label='New from Template', menu = ptypemenu)
        
        showmenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        showmenu.add_command(label='Delete', command = self.remove_show)
        showmenu.add_command(label='Edit', command = self.m_edit_show)
        showmenu.add_command(label='Copy To', command = self.copy_show)
        menubar.add_cascade(label='Show', menu = showmenu)

        stypemenu = Menu(showmenu, tearoff=0, bg="grey", fg="black")
        stypemenu.add_command(label='Menu', command = self.add_menu)
        stypemenu.add_command(label='MediaShow', command = self.add_mediashow)
        stypemenu.add_command(label='LiveShow', command = self.add_liveshow)
        stypemenu.add_command(label='HyperlinkShow', command = self.add_hyperlinkshow)
        stypemenu.add_command(label='RadioButtonShow', command = self.add_radiobuttonshow)
        stypemenu.add_command(label='ArtMediaShow', command = self.add_artmediashow)
        stypemenu.add_command(label='ArtLiveShow', command = self.add_artliveshow)
        showmenu.add_cascade(label='Add', menu = stypemenu)
        
        medialistmenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        menubar.add_cascade(label='MediaList', menu = medialistmenu)
        medialistmenu.add_command(label='Add', command = self.add_medialist)
        medialistmenu.add_command(label='Delete', command = self.remove_medialist)
      
        trackmenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        trackmenu.add_command(label='Delete', command = self.remove_track)
        trackmenu.add_command(label='Edit', command = self.m_edit_track)
        trackmenu.add_command(label='Add from Dir', command = self.add_tracks_from_dir)
        trackmenu.add_command(label='Add from File', command = self.add_track_from_file)


        menubar.add_cascade(label='Track', menu = trackmenu)

        typemenu = Menu(trackmenu, tearoff=0, bg="grey", fg="black")
        typemenu.add_command(label='Video', command = self.new_video_track)
        typemenu.add_command(label='Audio', command = self.new_audio_track)
        typemenu.add_command(label='Image', command = self.new_image_track)
        typemenu.add_command(label='Web', command = self.new_web_track)
        typemenu.add_command(label='Message', command = self.new_message_track)
        typemenu.add_command(label='Show', command = self.new_show_track)
        typemenu.add_command(label='Menu Background', command = self.new_menu_background_track)
        typemenu.add_command(label='Child Show', command = self.new_child_show_track)
        trackmenu.add_cascade(label='New', menu = typemenu)

        toolsmenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        menubar.add_cascade(label='Tools', menu = toolsmenu)
        toolsmenu.add_command(label='Update All', command = self.update_all)
        
        optionsmenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        menubar.add_cascade(label='Options', menu = optionsmenu)
        optionsmenu.add_command(label='Edit', command = self.edit_options)

        helpmenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        menubar.add_cascade(label='Help', menu = helpmenu)
        helpmenu.add_command(label='Help', command = self.show_help)
        helpmenu.add_command(label='About', command = self.about)
         
        self.root.config(menu=menubar)

        top_frame=Frame(self.root)
        top_frame.pack(side=TOP)
        bottom_frame=Frame(self.root)
        bottom_frame.pack(side=TOP, fill=BOTH, expand=1)        

        left_frame=Frame(bottom_frame, padx=5)
        left_frame.pack(side=LEFT)
        middle_frame=Frame(bottom_frame,padx=5)
        middle_frame.pack(side=LEFT)              
        right_frame=Frame(bottom_frame,padx=5,pady=10)
        right_frame.pack(side=LEFT)
        updown_frame=Frame(bottom_frame,padx=5)
        updown_frame.pack(side=LEFT)
        
        tracks_title_frame=Frame(right_frame)
        tracks_title_frame.pack(side=TOP)
        tracks_label = Label(tracks_title_frame, text="Tracks in Selected Medialist")
        tracks_label.pack()
        tracks_frame=Frame(right_frame)
        tracks_frame.pack(side=TOP)
        shows_title_frame=Frame(left_frame)
        shows_title_frame.pack(side=TOP)
        shows_label = Label(shows_title_frame, text="Shows")
        shows_label.pack()
        shows_frame=Frame(left_frame)
        shows_frame.pack(side=TOP)
        shows_title_frame=Frame(left_frame)
        shows_title_frame.pack(side=TOP)
        medialists_title_frame=Frame(left_frame)
        medialists_title_frame.pack(side=TOP)
        medialists_label = Label(medialists_title_frame, text="Medialists")
        medialists_label.pack()
        medialists_frame=Frame(left_frame)
        medialists_frame.pack(side=LEFT)
        
        # define buttons 

        add_button = Button(middle_frame, width = 5, height = 2, text='Edit\nShow',
                            fg='black', command = self.m_edit_show, bg="light grey")
        add_button.pack(side=RIGHT)
        
        add_button = Button(updown_frame, width = 5, height = 1, text='Add',
                            fg='black', command = self.add_track_from_file, bg="light grey")
        add_button.pack(side=TOP)
        add_button = Button(updown_frame, width = 5, height = 1, text='Edit',
                            fg='black', command = self.m_edit_track, bg="light grey")
        add_button.pack(side=TOP)
        add_button = Button(updown_frame, width = 5, height = 1, text='Up',
                            fg='black', command = self.move_track_up, bg="light grey")
        add_button.pack(side=TOP)
        add_button = Button(updown_frame, width = 5, height = 1, text='Down',
                            fg='black', command = self.move_track_down, bg="light grey")
        add_button.pack(side=TOP)


        # define display of showlist 
        scrollbar = Scrollbar(shows_frame, orient=VERTICAL)
        self.shows_display = Listbox(shows_frame, selectmode=SINGLE, height=7,
                                     width = 40, bg="white",activestyle=NONE,
                                     fg="black", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.shows_display.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.shows_display.pack(side=LEFT, fill=BOTH, expand=1)
        self.shows_display.bind("<ButtonRelease-1>", self.e_select_show)

    
        # define display of medialists
        scrollbar = Scrollbar(medialists_frame, orient=VERTICAL)
        self.medialists_display = Listbox(medialists_frame, selectmode=SINGLE, height=7,
                                          width = 40, bg="white",activestyle=NONE,
                                          fg="black",yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.medialists_display.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.medialists_display.pack(side=LEFT,  fill=BOTH, expand=1)
        self.medialists_display.bind("<ButtonRelease-1>", self.select_medialist)


        # define display of tracks
        scrollbar = Scrollbar(tracks_frame, orient=VERTICAL)
        self.tracks_display = Listbox(tracks_frame, selectmode=SINGLE, height=15,
                                      width = 40, bg="white",activestyle=NONE,
                                      fg="black",yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tracks_display.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tracks_display.pack(side=LEFT,fill=BOTH, expand=1)
        self.tracks_display.bind("<ButtonRelease-1>", self.e_select_track)


        # initialise editor options class
        self.options=Options(self.pp_dir) # creates options file in code directory if necessary
        
        # initialise variables      
        self.init()
        
        # and enter Tkinter event loop
        self.root.mainloop()        


    # ***************************************
    # INIT AND EXIT
    # ***************************************
    def app_exit(self):
        self.root.destroy()
        exit()


    def init(self):
        self.options.read()
        self.pp_home_dir = self.options.pp_home_dir
        self.initial_media_dir = self.options.initial_media_dir
        self.mon.log(self,"Data Home from options is "+self.pp_home_dir)
        self.mon.log(self,"Initial Media from options is "+self.initial_media_dir)
        self.current_medialist=None
        self.current_showlist=None
        self.current_show=None
        self.shows_display.delete(0,END)
        self.medialists_display.delete(0,END)
        self.tracks_display.delete(0,END)



    # ***************************************
    # MISCELLANEOUS
    # ***************************************

    def edit_options(self):
        """edit the options then read them from file"""
        eo = OptionsDialog(self.root, self.options.options_file,'Edit Options')
        if eo.result is True: self.init()


    def show_help (self):
        tkMessageBox.showinfo("Help","Read 'manual.pdf'")
  

    def about (self):
        tkMessageBox.showinfo("About","Editor for Pi Presents Profiles\n"
                              +"For profile version: " + self.editor_issue + "\nAuthor: Ken Thompson"
                              +"\nWebsite: http://pipresents.wordpress.com/")

    def validate_profile(self):
        val =Validator()
        val.validate_profile(self.root,self.pp_dir,self.pp_home_dir,self.pp_profile_dir,self.editor_issue,True)


    
    # **************
    # PROFILES
    # **************

    def open_existing_profile(self):
        initial_dir=self.pp_home_dir+os.sep+"pp_profiles"
        if os.path.exists(initial_dir) is False:
            self.mon.err(self,"Home directory not found: " + initial_dir + "\n\nHint: Data Home option must end in pp_home")
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


    def new_profile(self,profile):
        d = Edit1Dialog(self.root,"New Profile","Name", "")
        if d .result  is  None:
            return
        name=str(d.result)
        if name == "":
            tkMessageBox.showwarning("New Profile","Name is blank")
            return
        to = self.pp_home_dir + os.sep + "pp_profiles"+ os.sep + name
        if os.path.exists(to) is  True:
            tkMessageBox.showwarning( "New Profile","Profile exists\n(%s)" % to )
            return
        shutil.copytree(profile, to, symlinks=False, ignore=None)
        self.open_profile(to)


        
    def new_exhibit_profile(self):
        profile = self.pp_dir+"/pp_home/pp_profiles/ppt_exhibit"
        self.new_profile(profile)

    def new_interactive_profile(self):
        profile = self.pp_dir+"/pp_home/pp_profiles/ppt_interactive"
        self.new_profile(profile)

    def new_menu_profile(self):
        profile = self.pp_dir+"/pp_home/pp_profiles/ppt_menu"
        self.new_profile(profile)

    def new_presentation_profile(self):
        profile = self.pp_dir+"/pp_home/pp_profiles/ppt_presentation"
        self.new_profile(profile)

    def new_blank_profile(self):
        profile = self.pp_dir+"/pp_home/pp_profiles/ppt_blank"
        self.new_profile(profile)

    def new_mediashow_profile(self):
        profile = self.pp_dir+"/pp_home/pp_profiles/ppt_mediashow"
        self.new_profile(profile)
        
    def new_liveshow_profile(self):
        profile = self.pp_dir+"/pp_home/pp_profiles/ppt_liveshow"
        self.new_profile(profile)

    def new_radiobuttonshow_profile(self):
        profile = self.pp_dir+"/pp_home/pp_profiles/ppt_radiobuttonshow"
        self.new_profile(profile)

    def new_hyperlinkshow_profile(self):
        profile = self.pp_dir+"/pp_home/pp_profiles/ppt_hyperlinkshow"
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
            
    def add_eventshow(self):
        self.add_show(PPdefinitions.new_shows['eventshow'])

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
        
    def add_menu(self):
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
            mediafile=self.add_medialist(name)
            if mediafile != '':
                copied_show['medialist']=mediafile
            self.current_showlist.append(copied_show)
            self.save_showlist(self.pp_profile_dir)
            self.refresh_shows_display()

            
    def remove_show(self):
        if  self.current_showlist is not None and self.current_showlist.length()>0 and self.current_showlist.show_is_selected():
            if tkMessageBox.askokcancel("Delete Show","Delete Show"):
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
        self.shows_display.delete(0,self.shows_display.size())
        for index in range(self.current_showlist.length()):
            self.shows_display.insert(END, self.current_showlist.show(index)['title']+"   ["+self.current_showlist.show(index)['show-ref']+"]")        
        if self.current_showlist.show_is_selected():
            self.shows_display.itemconfig(self.current_showlist.selected_show_index(),fg='red')            
            self.shows_display.see(self.current_showlist.selected_show_index())

            
    def e_select_show(self,event):
        if self.current_showlist is not None and self.current_showlist.length()>0:
            mouse_item_index=int(event.widget.curselection()[0])
            self.current_showlist.select(mouse_item_index)
            self.refresh_shows_display()

    def copy_show(self):
        if  self.current_showlist is not None and self.current_showlist.show_is_selected():
            self.add_show(self.current_showlist.selected_show())

        
    def m_edit_show(self):
        self.edit_show(PPdefinitions.show_types,PPdefinitions.show_field_specs)
        
     

    def edit_show(self,show_types,field_specs):
        if self.current_showlist is not None and self.current_showlist.show_is_selected():
            d=EditItem(self.root,"Edit Show",self.current_showlist.selected_show(),show_types,field_specs,self.show_refs(),
                       self.initial_media_dir,self.pp_home_dir,'show')
            if d.result  is  True:

                self.save_showlist(self.pp_profile_dir)
                self.refresh_shows_display()

 

    # ***************************************
    #   Medialists
    # ***************************************

    def open_medialists(self,profile_dir):
        self.medialists = []
        for this_file in os.listdir(profile_dir):
            if this_file.endswith(".json") and this_file != 'pp_showlist.json':
                self.medialists = self.medialists + [this_file]
        self.medialists_display.delete(0,self.medialists_display.size())
        for index in range (len(self.medialists)):
            self.medialists_display.insert(END, self.medialists[index])
        self.current_medialists_index=-1
        self.current_medialist=None


    def add_medialist(self,name=None):
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
            tkMessageBox.showwarning("Add medialist","Medialist file exists\n(%s)" % path)
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
        # add title to medialists display
        self.medialists_display.insert(END, name)  
        # and set it as the selected medialist
        self.refresh_medialists_display()
        return name


    def remove_medialist(self):
        if self.current_medialist is not None:
            if tkMessageBox.askokcancel("Delete Medialist","Delete Medialist"):
                os.remove(self.pp_profile_dir+ os.sep + self.medialists[self.current_medialists_index])
                self.open_medialists(self.pp_profile_dir)
                self.refresh_medialists_display()
                self.refresh_tracks_display()


    def select_medialist(self,event):
        """
        user clicks on a medialst in a profile so try and select it.
        """
        # needs forgiving int for possible tkinter upgrade
        if len(self.medialists)>0:
            self.current_medialists_index=int(event.widget.curselection()[0])
            self.current_medialist=MediaList('ordered')
            if not self.current_medialist.open_list(self.pp_profile_dir+ os.sep + self.medialists[self.current_medialists_index],self.current_showlist.sissue()):
                self.mon.err(self,"medialist is a different version to showlist: "+ self.medialists[self.current_medialists_index])
                self.app_exit()        
            self.refresh_tracks_display()
            self.refresh_medialists_display()


    def refresh_medialists_display(self):
        self.medialists_display.delete(0,len(self.medialists))
        for index in range (len(self.medialists)):
            self.medialists_display.insert(END, self.medialists[index])
        if self.current_medialist is not None:
            self.medialists_display.itemconfig(self.current_medialists_index,fg='red')
            self.medialists_display.see(self.current_medialists_index)

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
        self.tracks_display.delete(0,self.tracks_display.size())
        if self.current_medialist is not None:
            for index in range(self.current_medialist.length()):
                if self.current_medialist.track(index)['track-ref'] == '':
                    track_ref_string="  ["+self.current_medialist.track(index)['track-ref']+"]"
                else:
                    track_ref_string=""
                self.tracks_display.insert(END, self.current_medialist.track(index)['title']+track_ref_string)        
            if self.current_medialist.track_is_selected():
                self.tracks_display.itemconfig(self.current_medialist.selected_track_index(),fg='red')            
                self.tracks_display.see(self.current_medialist.selected_track_index())
            
    def e_select_track(self,event):
        if self.current_medialist is not None and self.current_medialist.length()>0:
            mouse_item_index=int(event.widget.curselection()[0])
            self.current_medialist.select(mouse_item_index)
            self.refresh_tracks_display()

    def m_edit_track(self):
        self.edit_track(PPdefinitions.track_types,PPdefinitions.track_field_specs)

    def edit_track(self,track_types,field_specs):      
        if self.current_medialist is not None and self.current_medialist.track_is_selected():
            d=EditItem(self.root,"Edit Track",self.current_medialist.selected_track(),track_types,field_specs,
                       self.show_refs(),self.initial_media_dir,self.pp_home_dir,'track')
            if d.result  is  True:
                self.save_medialist()
            self.refresh_tracks_display()

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
 
    def new_menu_background_track(self):
        self.new_track(PPdefinitions.new_tracks['menu-background'],None)

    def new_child_show_track(self):
        self.new_track(PPdefinitions.new_tracks['child-show'],None)

    def remove_track(self):
        if  self.current_medialist is not None and self.current_medialist.length()>0 and self.current_medialist.track_is_selected():
            if tkMessageBox.askokcancel("Delete Track","Delete Track"):
                index= self.current_medialist.selected_track_index()
                self.current_medialist.remove(index)
                self.save_medialist()
                self.refresh_tracks_display()
                
    def add_track_from_file(self):
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

    def add_tracks_from_dir(self):
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
            self.mon.err(self,afile + " - file extension not recognised")



    # *********************************************
    # UPDATE PROFILE
    # **********************************************

    def update_all(self):
        self.init()
        for profile_file in os.listdir(self.pp_home_dir+os.sep+'pp_profiles'):
            # self.mon.log (self,"Updating "+profile_file)
            self.pp_profile_dir = self.pp_home_dir+os.sep+'pp_profiles'+ os.sep + profile_file
            if not os.path.exists(self.pp_profile_dir+os.sep+"pp_showlist.json"):
                tkMessageBox.showwarning("Pi Presents","Not a profile, skipping "+self.pp_profile_dir)
            else:
                self.current_showlist=ShowList()
                # self.mon.log (self,"Checking version "+profile_file)
                self.current_showlist.open_json(self.pp_profile_dir+os.sep+"pp_showlist.json")
                if float(self.current_showlist.sissue())<float(self.editor_issue):
                    self.mon.log(self,"Version of profile "+profile_file+ "  is being updated to "+self.editor_issue)
                    self.update_profile()
                elif (self.command_options['forceupdate']  is  True and float(self.current_showlist.sissue()) == float(self.editor_issue)):
                    self.mon.log(self, "Forced updating of " + profile_file + ' to '+self.editor_issue)
                    self.update_profile()
                elif float(self.current_showlist.sissue())>float(self.editor_issue):
                    tkMessageBox.showwarning("Pi Presents", "Version of profile " +profile_file+ " is greater than editor, skipping")
                else:
                    self.mon.log(self," Profile " + profile_file + " Already up to date ")
        self.init()
        tkMessageBox.showwarning("Pi Presents","All profiles updated")
            
    def update_profile(self):
        # open showlist and update its shows
        # self.mon.log (self,"Updating show ")
        ifile  = open(self.pp_profile_dir + os.sep + "pp_showlist.json", 'rb')
        shows = json.load(ifile)['shows']
        ifile.close()
        replacement_shows=self.update_shows(shows)
        dic={'issue':self.editor_issue,'shows':replacement_shows}
        ofile  = open(self.pp_profile_dir + os.sep + "pp_showlist.json", "wb")
        json.dump(dic,ofile,sort_keys=True,indent=1)

        
        # UPDATE MEDIALISTS AND THEIR TRACKS
        for this_file in os.listdir(self.pp_profile_dir):
            if this_file.endswith(".json") and this_file != 'pp_showlist.json':
                # self.mon.log (self,"Updating medialist " + this_file)
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


    def update_shows(self,old_shows):
        # get correct spec from type of field
        replacement_shows=[]
        for old_show in old_shows:
            show_type=old_show['type']
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

class Edit1Dialog(tkSimpleDialog.Dialog):

    def __init__(self, parent, title, label, default):
        # save the extra args to instance variables
        self.label_1 = label
        self.default_1 = default     
        # and call the base class _init_which uses the args in body
        tkSimpleDialog.Dialog.__init__(self, parent, title)


    def body(self, master):
        Label(master, text=self.label_1).grid(row=0)
        self.field1 = Entry(master)
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


        # create an options file if necessary
        self.options_file = app_dir+os.sep+'pp_editor.cfg'
        if not os.path.exists(self.options_file):
            self.create()


    
    def read(self):
        """reads options from options file to interface"""
        config=ConfigParser.ConfigParser()
        config.read(self.options_file)
        
        self.pp_home_dir =config.get('config','home',0)
        self.initial_media_dir =config.get('config','media',0)    

    def create(self):
        config=ConfigParser.ConfigParser()
        config.add_section('config')
        if os.name == 'nt':
            config.set('config','home',os.path.expanduser('~')+'\pp_home')
            config.set('config','media',os.path.expanduser('~'))
        else:
            config.set('config','home',os.path.expanduser('~')+'/pp_home')
            config.set('config','media',os.path.expanduser('~'))            
            # config.set('config','home','/home/pi/pp_home')
            # config.set('config','media','/home/pi')
        with open(self.options_file, 'wb') as config_file:
            config.write(config_file)



# *************************************
# PP_EDITOR OPTIONS DIALOG CLASS
# ************************************

class OptionsDialog(tkSimpleDialog.Dialog):

    def __init__(self, parent, options_file, title=None, ):
        # instantiate the subclass attributes
        self.options_file=options_file

        # init the super class
        tkSimpleDialog.Dialog.__init__(self, parent, title)


    def body(self, master):
        self.result=False
        config=ConfigParser.ConfigParser()
        config.read(self.options_file)

        Label(master, text="").grid(row=20, sticky=W)
        Label(master, text="Pi Presents Data Home:").grid(row=21, sticky=W)
        self.e_home = Entry(master,width=80)
        self.e_home.grid(row=22)
        self.e_home.insert(0,config.get('config','home',0))

        Label(master, text="").grid(row=30, sticky=W)
        Label(master, text="Inital directory for media:").grid(row=31, sticky=W)
        self.e_media = Entry(master,width=80)
        self.e_media.grid(row=32)
        self.e_media.insert(0,config.get('config','media',0))

        return None    # no initial focus

    def validate(self):
        if os.path.exists(self.e_home.get()) is  False:
            tkMessageBox.showwarning("Pi Presents Editor","Data Home not found")
            return 0
        if os.path.exists(self.e_media.get()) is  False:
            tkMessageBox.showwarning("Pi Presents Editor","Media Directory not found")
            return 0
        return 1

    def apply(self):
        self.save_options()
        self.result=True

    def save_options(self):
        """ save the output of the options edit dialog to file"""
        config=ConfigParser.ConfigParser()
        config.add_section('config')
        config.set('config','home',self.e_home.get())
        config.set('config','media',self.e_media.get())
        with open(self.options_file, 'wb') as optionsfile:
            config.write(optionsfile)
    

# ***************************************
# MAIN
# ***************************************


if __name__  ==  "__main__":
    editor = PPEditor()

