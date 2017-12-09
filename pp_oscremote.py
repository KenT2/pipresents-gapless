#! /usr/bin/env python

"""
Heavily modified from the examples here, with thanks:
sending OSC with pyOSC
https://trac.v2.nl/wiki/pyOSC
example by www.ixi-audio.net based on pyOSC documentation
"""

from Tkinter import Tk, StringVar, Menu,Frame,Label,Button,Scrollbar,Listbox,Entry,Text
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



from pp_utils import Monitor
from pp_options import remote_options
from pp_oscconfig import OSCConfig,OSCEditor
from pp_showlist import ShowList

import OSC_plus as OSC
import time, threading

class OSCRemote(object):

    def __init__(self):
    
        self.editor_issue="1.3"

        # get command options
        self.command_options=remote_options()

        # get directory holding the code
        self.pp_dir=sys.path[0]
            
        if not os.path.exists(self.pp_dir+os.sep+"pp_oscremote.py"):
            tkMessageBox.showwarning("Pi Presents","Bad Application Directory")
            exit()
            
          
        # Initialise logging
        Monitor.log_path=self.pp_dir
        self.mon=Monitor()
        self.mon.init()
        
        Monitor.classes  = ['OSCRemote','OSCConfig','OSCEditor']

        Monitor.log_level = int(self.command_options['debug'])

        self.mon.log (self, "Pi Presents Remote is starting")
        self.mon.log (self," OS and separator " + os.name +'  ' + os.sep)
        self.mon.log(self,"sys.path[0] -  location of code: code "+sys.path[0])

        self.root = Tk()

        # OSC config class
        self.osc_config=OSCConfig()
        self.osc_config_file = self.pp_dir + os.sep + 'pp_config' + os.sep + 'pp_oscremote.cfg'
        self.read_create_osc()

        self.setup_gui()

        if self.osc_config.this_unit_ip =='':
            self.mon.err(self,'IP of own unit must be provided in oscremote.cfg')

      
        self.init()


        #and start the system
        self.root.after(1000,self.run_app)
        self.root.mainloop()


    def init(self):
        #self.osc_config_file = self.pp_dir + os.sep + 'pp_config' + os.sep + 'pp_oscremote.cfg'
        #self.read_create_osc()
          
        self.pp_home_dir = self.command_options['home']+'/pp_home'
        self.mon.log(self,"Data Home from options is "+self.pp_home_dir)
        self.pp_profile_dir=''

        self.current_showlist=None
        self.current_show=None
        self.current_show_ref=''
        self.shows_display.delete(0,END)
        self.results.set('')
        self.desc.set('Listening to replies from Slave on: ' + self.osc_config.this_unit_ip + ':' + self.osc_config.reply_listen_port)
        
    def add_status(self,text):
        self.status_display.insert(END,text+'\n')
        self.status_display.see(END)

    def run_app(self):

        self.output_client=None
        self.output_reply_server=None
        self.output_reply_thread=None

        if self.osc_config.master_enabled !='yes':
            self.mon.err(self,'OSC Master is not enabled in oscremote.cfg')
            return

        if self.osc_config.reply_listen_port =='':
            self.mon.err(self,'Reply Listen port is not set in oscremote.cfg')
            return
        
               
        self.prefix='/pipresents'
        self.this_unit='/' + self.osc_config.this_unit_name
        self.add_status("This unit's OSC address is: "+self.this_unit)
        self.slave_unit='/'+self.osc_config.slave_units_name
        self.add_status('Slave unit OSC address is: '+self.slave_unit)
       
        #connect client sending commands to slave unit then start server to listen for replies
        self.output_client=self.init_client()
        self.add_status('Listening for replies from slave on: '+self.osc_config.this_unit_ip + ':' + self.osc_config.reply_listen_port)
        self.output_reply_server=self.init_server(self.osc_config.this_unit_ip,self.osc_config.reply_listen_port,self.output_client)
        self.add_output_reply_handlers()
        self.output_reply_thread=self.start_server(self.output_reply_server)


# ***************************************
#  RESPOND TO BUTTONS
# ***************************************

    def open_show(self):
        self.msg_path= '/core/open '
        self.msg_arg_text= self.current_show_ref
        self.display_msg_text()


    def close_show(self):
        self.msg_path= '/core/close '
        self.msg_arg_text=self.current_show_ref
        self.display_msg_text()


    def exit_pipresents(self):
        self.msg_path= '/core/exitpipresents'
        self.msg_arg_text=''
        self.display_msg_text()

    
    def play_event(self):
        self.msg_path= '/core/event'
        self.msg_arg_text = 'pp-play'
        self.display_msg_text()


    def pause_event(self):
        self.msg_path= '/core/event'
        self.msg_arg_text='pp-pause'
        self.display_msg_text()
        pass

    def stop_event(self):
        self.msg_path= '/core/event'
        self.msg_arg_text='pp-stop'
        self.display_msg_text()
        pass
    
    def up_event(self):
        self.msg_path= '/core/event'
        self.msg_arg_text='pp-up'
        self.display_msg_text()


    def down_event(self):
        self.msg_path= '/core/event'
        self.msg_arg_text='pp-down'
        self.display_msg_text()


    def animate(self):
        self.msg_path= '/core/animate'
        self.msg_arg_text=''
        self.display_msg_text()

    def display_control(self):
        self.msg_path= '/core/monitor'
        self.msg_arg_text=''
        self.display_msg_text()

    def loopback(self):
        self.msg_path= '/system/loopback'
        self.msg_arg_text=''
        self.display_msg_text()        


    def server_info(self):
        self.msg_path= '/system/server-info'
        self.msg_arg_text=''
        self.display_msg_text()         


    # and put the created text in the results box in the gui
    def display_msg_text(self):
        self.results.set(self.prefix+self.slave_unit+self.msg_path+' '+self.msg_arg_text)


    #respond to the Send button
    # parses the message string into fields and sends - NO error checking
    def send_message(self):
        if self.slave_unit =='/':
            self.mon.err(self,'slave unit OSC name not set')
            return
        if self.osc_config.slave_units_ip=='':
            self.mon.err(self,'slave unit IP not set')
            return
        msg_text=self.results.get()
        if msg_text=='':
            return
        fields=msg_text.split()
        osc_address = fields[0]
        arg_list=fields[1:]
        dest=(self.osc_config.slave_units_ip,int(self.osc_config.reply_listen_port))
        self.add_status('Send message:'+msg_text+ ' to '+ str(dest))
        self.mon.log(self,'send message: ' + msg_text )
        self.sendto(self.output_client,dest,osc_address,arg_list)


    # ***************************************
    # OSC CLIENT TO SEND MESSAGES
    # ***************************************

    def init_client(self):
       return OSC.OSCClient()


    def sendto(self,client,dest, address,arg_list):
        msg = OSC.OSCMessage()
        msg.setAddress(address)
        for arg in arg_list:
            msg.append(arg)
        try:
            client.sendto(msg,dest) 
        except Exception as e:
            self.mon.err(self,'error in client when sending OSC command: '+ str(e))
   


    def disconnect_client(self,client):
        if client != None:
            client.close()
            return


    # ***************************************
    # OSC SERVER TO LISTEN TO REPLIES
    # ***************************************

    def init_server(self,ip,port_text,client):
        self.mon.log(self,'Start Server: '+ip+':'+port_text)
        return OSC.OSCServer((ip,int(port_text)),client)

    def start_server(self,server):
        st = threading.Thread( target = server.serve_forever )
        st.start()
        return st

    def close_server(self,server,st):
        if server != None:
            server.close()
        self.mon.log(self, 'Waiting for Server-thread to finish')
        if st != None:
            st.join() ##!!!
        self.mon.log(self,'server thread closed')


    def add_output_reply_handlers(self):
        self.output_reply_server.addMsgHandler('default', self.no_match_handler)     
        self.output_reply_server.addMsgHandler(self.prefix+"/system/loopback-reply", self.loopback_reply_handler)
        self.output_reply_server.addMsgHandler(self.prefix+"/system/server-info-reply", self.server_info_reply_handler)

    def no_match_handler(self,addr, tags, stuff, source):
        text= "No handler for message from %s" % OSC.getUrlStr(source)+'\n'
        text+= "     %s" % addr+ self.pretty_list(stuff,'')
        self.add_status(text+'\n')

        
    def loopback_reply_handler(self,addr, tags, stuff, source):
        self.add_status('Loopback reply  received from: '+  OSC.getUrlStr(source))


    def server_info_reply_handler(self,addr, tags, stuff, source):
        unit=stuff[0]
        commands=stuff[1:]
        self.add_status('Server Information from: '+  OSC.getUrlStr(source))
        self.add_status('OSC name: '+  unit)
        self.add_status('Commands:\n'+self.pretty_list(commands,'\n'))
                        

    def pretty_list(self,fields, separator):
        text=' '
        for field in fields:
            text += str(field) + separator
        return text


    # ***************************************
    # INIT EXIT MISC
    # ***************************************

    def e_edit_osc(self):
        self.disconnect_client(self.output_client)
        self.output_client=None
        self.close_server(self.output_reply_server,self.output_reply_thread)
        self.output_reply_server=None
        self.output_reply_thread=None
        self.edit_osc()
        self.read_create_osc()
        self.init()
        self.add_status('\n\n\nRESTART')
        self.run_app()


    def app_exit(self):
        self.disconnect_client(self.output_client)
        self.close_server(self.output_reply_server,self.output_reply_thread)
        if self.root is not None:
            self.root.destroy()
        self.mon.finish()
        sys.exit() 


    def show_help (self):
        tkMessageBox.showinfo("Help","Read 'manual.pdf'")
  

    def about (self):
        tkMessageBox.showinfo("About","Simple Remote Control for Pi Presents\n"
                              +"Author: Ken Thompson"
                              +"\nWebsite: http://pipresents.wordpress.com/")


    def setup_gui(self):
        # set up the gui
 
        # root is the Tkinter root widget
        self.root.title("OSC Remote Control for Pi Presents")
        

        # self.root.configure(background='grey')

        self.root.resizable(False,False)

        # define response to main window closing
        self.root.protocol ("WM_DELETE_WINDOW", self.app_exit)

        # bind some display fields
        self.desc=StringVar()
        self.filename = StringVar()
        self.display_show = StringVar()
        self.results = StringVar()
        self.status = StringVar()

        # define menu
        menubar = Menu(self.root)

        profilemenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        profilemenu.add_command(label='Select', command = self.open_existing_profile)
        menubar.add_cascade(label='Profile', menu = profilemenu)

        osc_configmenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        menubar.add_cascade(label='Options', menu = osc_configmenu)
        osc_configmenu.add_command(label='Edit', command = self.e_edit_osc)

        helpmenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        menubar.add_cascade(label='Help', menu = helpmenu)
        helpmenu.add_command(label='Help', command = self.show_help)
        helpmenu.add_command(label='About', command = self.about)
         
        self.root.config(menu=menubar)



        #top frame
        top_frame=Frame(self.root,padx=5,pady=5)
        top_frame.pack(side=TOP)


        # output info frame
        info_frame=Frame(top_frame,padx=5,pady=5)
        info_frame.pack(side=TOP, fill=BOTH, expand=1)
        info_name = Label(info_frame, text="Master's Name: "+self.osc_config.this_unit_name,font="arial 12 bold")
        info_name.pack(side=TOP)
        info_reply_address = Label(info_frame, textvariable=self.desc,font="arial 12 bold")
        info_reply_address.pack(side=TOP)

        
        results_label = Label(top_frame, text="Message to Send",font="arial 12 bold")
        results_label.pack(side=LEFT)
        results_display=Entry(top_frame, textvariable=self.results, width=70)
        results_display.pack(side=LEFT,fill=BOTH, expand=1)
        send_button = Button(top_frame, width = 5, height = 1, text='Send',
                            fg='black', command = self.send_message, bg="light grey")
        send_button.pack(side=RIGHT)

        #bottom frame
        bottom_frame=Frame(self.root,padx=5,pady=5)
        bottom_frame.pack(side=TOP, fill=BOTH, expand=1) 
        left_frame=Frame(bottom_frame, padx=5)
        left_frame.pack(side=LEFT)            
        right_frame=Frame(bottom_frame,padx=5,pady=5)
        right_frame.pack(side=LEFT)

        suplabel_frame=Frame(right_frame,pady=5)
        suplabel_frame.pack(side=TOP)
        commands_label = Label(suplabel_frame, text="Show Control",font="arial 12 bold")
        commands_label.pack()
                            
        supervisor_frame=Frame(right_frame,pady=5)
        supervisor_frame.pack(side=TOP)

        # supervisor buttons 
        add_button = Button(supervisor_frame, width = 5, height = 1, text='Open\nShow',
                            fg='black', command = self.open_show, bg="light grey")
        add_button.pack(side=LEFT)
        add_button = Button(supervisor_frame, width = 5, height = 1, text='Close\nShow',
                            fg='black', command = self.close_show, bg="light grey")
        add_button.pack(side=LEFT)
        add_button = Button(supervisor_frame, width = 10, height = 1, text='Exit\nPi Presents',
                            fg='black', command = self.exit_pipresents, bg="light grey")
        add_button.pack(side=LEFT)

        # events buttons        
        oplabel_frame=Frame(right_frame,pady=5)
        oplabel_frame.pack(side=TOP)
        operations_label = Label(oplabel_frame, text="Input Events",
                                 font="arial 12 bold")
        operations_label.pack()
        
        operations_frame=Frame(right_frame,pady=5)
        operations_frame.pack(side=TOP)
                              
        add_button = Button(operations_frame, width = 5, height = 1, text='Play',
                            fg='black', command = self.play_event, bg="light grey")
        add_button.pack(side=LEFT)   
        add_button = Button(operations_frame, width = 5, height = 1, text='Pause',
                            fg='black', command = self.pause_event, bg="light grey")
        add_button.pack(side=LEFT)
        add_button = Button(operations_frame, width = 5, height = 1, text='Stop',
                            fg='black', command = self.stop_event, bg="light grey")
        add_button.pack(side=LEFT)
        add_button = Button(operations_frame, width = 5, height = 1, text='Up',
                            fg='black', command = self.up_event, bg="light grey")
        add_button.pack(side=LEFT)
        add_button = Button(operations_frame, width = 5, height = 1, text='Down',
                            fg='black', command = self.down_event, bg="light grey")
        add_button.pack(side=LEFT)


        # animate buttons        
        others_label_frame=Frame(right_frame,pady=5)
        others_label_frame.pack(side=TOP)
        others_label = Label(others_label_frame, text="Others",
                                 font="arial 12 bold")
        others_label.pack()
        
        others_frame=Frame(right_frame,pady=5)
        others_frame.pack(side=TOP)
                              
        add_button = Button(others_frame, width = 5, height = 1, text='Animate',
                            fg='black', command = self.animate, bg="light grey")
        add_button.pack(side=LEFT)  

        add_button = Button(others_frame, width = 8, height = 1, text='Monitor on/off',
                            fg='black', command = self.display_control, bg="light grey")
        add_button.pack(side=LEFT) 

        
        # system buttons        
        systemlabel_frame=Frame(right_frame,pady=5)
        systemlabel_frame.pack(side=TOP)
        system_label = Label(systemlabel_frame, text="System",
                                 font="arial 12 bold")
        system_label.pack()
        
        system_frame=Frame(right_frame,pady=5)
        system_frame.pack(side=TOP)
                              
        add_button = Button(system_frame, width = 5, height = 1, text='Loopback',
                            fg='black', command = self.loopback, bg="light grey")
        add_button.pack(side=LEFT)   
        add_button = Button(system_frame, width = 10, height = 1, text='Server Info',
                            fg='black', command = self.server_info, bg="light grey")
        add_button.pack(side=LEFT)



        # define display of showlist
        shows_title_frame=Frame(left_frame)
        shows_title_frame.pack(side=TOP)
        shows_label = Label(shows_title_frame, text="Shows")
        shows_label.pack()
        shows_frame=Frame(left_frame)
        shows_frame.pack(side=TOP)
        scrollbar = Scrollbar(shows_frame, orient=VERTICAL)
        self.shows_display = Listbox(shows_frame, selectmode=SINGLE, height=12,
                                     width = 40, bg="white",activestyle=NONE,
                                     fg="black", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.shows_display.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.shows_display.pack(side=LEFT, fill=BOTH, expand=1)
        self.shows_display.bind("<ButtonRelease-1>", self.e_select_show)


        # status_frame      
        status_frame=Frame(self.root,padx=5,pady=5)
        status_frame.pack(side=TOP, fill=BOTH, expand=1)
        status_label = Label(status_frame, text="Status",font="arial 12 bold")
        status_label.pack(side=LEFT)
        scrollbar = Scrollbar(status_frame, orient=VERTICAL)
        self.status_display=Text(status_frame,height=10, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.status_display.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.status_display.pack(side=LEFT,fill=BOTH, expand=1)


    # ***************************************
    # SHOWLIST
    # ***************************************

    def open_existing_profile(self):
        initial_dir=self.pp_home_dir+os.sep+"pp_profiles"
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
        self.root.title("Remote for Pi Presents - "+ self.pp_profile_dir)
        self.open_showlist(self.pp_profile_dir)

    def open_showlist(self,profile_dir):
        showlist_file = profile_dir + os.sep + "pp_showlist.json"
        if os.path.exists(showlist_file) is False:
            self.mon.err(self,"showlist file not found at " + profile_dir + "\n\nHint: Have you opened the profile directory?")
            self.app_exit()
        self.current_showlist=ShowList()
        self.current_showlist.open_json(showlist_file)
        # if float(self.current_showlist.sissue()) != float(self.editor_issue):
            # self.mon.err(self,"Version of profile does not match Remote: "+self.editor_issue)
            # self.app_exit()
        self.refresh_shows_display()


    def refresh_shows_display(self):
        self.shows_display.delete(0,self.shows_display.size())
        for index in range(self.current_showlist.length()):
            self.shows_display.insert(END, self.current_showlist.show(index)['title']+"   ["+self.current_showlist.show(index)['show-ref']+"]")        
        if self.current_showlist.show_is_selected():
            self.shows_display.itemconfig(self.current_showlist.selected_show_index(),fg='red')            
            self.shows_display.see(self.current_showlist.selected_show_index())

    def e_select_show(self,event):
        # print 'select show', self.current_showlist.length()
        if self.current_showlist is not None and self.current_showlist.length()>0:
            mouse_item_index=int(event.widget.curselection()[0])
            self.current_showlist.select(mouse_item_index)
            self.current_show_ref=self.current_showlist.selected_show()['show-ref']
            self.refresh_shows_display()
        else:
            self.current_show_ref=''


# ***************************************
#  OSC CONFIGURATION
# ***************************************

    def read_create_osc(self):
        if self.osc_config.read(self.osc_config_file) is False:
            self.osc_config.create(self.osc_config_file,'master')
            eosc = OSCEditor(self.root, self.osc_config_file,'remote','Create OSC Remote Configuration')
            self.osc_config.read(self.osc_config_file)


    def edit_osc(self):
        if self.osc_config.read(self.osc_config_file) is False:
            self.osc_config.create(self.osc_config_file)
        eosc = OSCEditor(self.root, self.osc_config_file,'remote','Edit OSC Reomote Configuration')


if __name__ == '__main__':

    oc = OSCRemote()

