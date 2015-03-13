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
import OSC
import time, threading

from pp_utils import Monitor
from pp_options import remote_options
from pp_oscconfig import OSCConfig,OSCEditor
from pp_showlist import ShowList



class myOSCServer(OSC.OSCServer):
    allow_reuse_address=True
    print_tracebacks = True   

class OSCMonitor(object):

    def __init__(self):
    
        self.editor_issue="1.3"

        # get command options
        self.command_options=remote_options()

        # get directory holding the code
        self.pp_dir=sys.path[0]
            
        if not os.path.exists(self.pp_dir+os.sep+"pipresents.py"):
            tkMessageBox.showwarning("Pi Presents","Bad Application Directory")
            exit()
            
          
        # Initialise logging
        Monitor.log_path=self.pp_dir
        self.mon=Monitor()
        self.mon.init()
        
        Monitor.classes  = ['OSCMonitor','OSCConfig','OSCEditor']

        Monitor.log_level = int(self.command_options['debug'])

        self.mon.log (self, "Pi Presents Monitor is starting")
        self.mon.log (self," OS and separator " + os.name +'  ' + os.sep)
        self.mon.log(self,"sys.path[0] -  location of code: code "+sys.path[0])

        self.setup_gui()

        # initialise OSC config class
        self.osc_config=OSCConfig()

        self.init()

        #and start the system
        self.root.after(1000,self.run_app)
        self.root.mainloop()


    def init(self):
        # read the options and allow their editing
        self.osc_config_file = self.pp_dir + os.sep + 'pp_config' + os.sep + 'pp_oscmonitor.cfg'
        self.read_create_osc()


    def add_status(self,text):
        self.status_display.insert(END,text+'\n')
        self.status_display.see(END)

    def run_app(self):
        self.client=None
        self.server=None
        self.st=None
        
        # initialise OSC variables
        self.prefix='/pipresents'
        self.this_unit='/' + self.osc_config.this_unit_name
        self.add_status('this unit is: '+self.this_unit)
        self.controlled_by_unit='/'+self.osc_config.controlled_by_name
        self.add_status('controlled by unit : '+self.controlled_by_unit)
       
        #connect client for replies then start server to listen for commands
        self.client = OSC.OSCClient()
        self.add_status('connecting to controlled by unit: '+self.osc_config.controlled_by_ip+':'+self.osc_config.controlled_by_port +' '+self.osc_config.controlled_by_name)
        self.client.connect((self.osc_config.controlled_by_ip,int(self.osc_config.controlled_by_port)))
        self.add_status('listening for commands on:'+self.osc_config.this_unit_ip+':'+self.osc_config.this_unit_port)
        self.init_server(self.osc_config.this_unit_ip,self.osc_config.this_unit_port,self.client)
        self.add_initial_handlers()
        self.start_server()



    # ***************************************
    # OSC CLIENT TO SEND REPLIES
    # ***************************************

    def disconnect_client(self):
        if self.client != None:
            self.client.close()
        return


    # ***************************************
    # OSC SERVER TO LISTEN TO COMMANDS
    # ***************************************

    def init_server(self,ip,port_text,client):
        self.add_status('Init Server: '+ip+':'+port_text)
        self.server = myOSCServer((ip,int(port_text)),client)

    def start_server(self):
        self.add_status('Start Server')
        self.st = threading.Thread( target = self.server.serve_forever )
        self.st.start()

    def close_server(self):
        if self.server != None:
            self.server.close()
        self.mon.log(self, 'Waiting for Server-thread to finish')
        if self.st != None:
            self.st.join() ##!!!
        self.mon.log(self,'server thread closed')


    def add_initial_handlers(self):
        pass
        self.server.addMsgHandler('default', self.no_match_handler)
        self.server.addMsgHandler(self.prefix+self.this_unit+"/system/server-info", self.server_info_handler)
        self.server.addMsgHandler(self.prefix+self.this_unit+"/system/loopback", self.loopback_handler)


    def no_match_handler(self,addr, tags, stuff, source):
        text= "Message from %s" % OSC.getUrlStr(source)+'\n'
        text+= "     %s" % addr+ self.pretty_list(stuff)
        self.add_status(text+'\n')


    def server_info_handler(self,addr, tags, stuff, source):
        msg = OSC.OSCMessage(self.prefix+self.controlled_by_unit+'/system/server-info-reply')
        msg.append('Unit: '+ self.osc_config.this_unit_name)
        self.add_status('Server Info Request from %s:' % OSC.getUrlStr(source))           
        return msg


    def loopback_handler(self,addr, tags, stuff, source):
         # send a reply to the client.
        msg = OSC.OSCMessage(self.prefix+self.controlled_by_unit+'/system/loopback-reply')
        self.add_status('Loopback Request from %s:' % OSC.getUrlStr(source))
        return msg      



    def pretty_list(self,fields):
        text=' '
        for field in fields:
            text += str(field) + ' '
        return text


    # ***************************************
    # INIT EXIT MISC
    # ***************************************


    def e_edit_osc(self):
        self.disconnect_client()
        self.close_server()
        self.edit_osc()
        self.init()
        self.add_status('\n\n\nRESTART')
        self.run_app()


    def app_exit(self):
        self.disconnect_client()
        self.close_server()
        if self.root is not None:
            self.root.destroy()
        self.mon.finish()
        sys.exit() 


    def show_help (self):
        tkMessageBox.showinfo("Help","Read 'manual.pdf'")
  

    def about (self):
        tkMessageBox.showinfo("About","Simple Remote Monitor for Pi Presents\n"
                              +"Author: Ken Thompson"
                              +"\nWebsite: http://pipresents.wordpress.com/")


    def setup_gui(self):
        # set up the gui
 
        # root is the Tkinter root widget
        self.root = Tk()
        self.root.title("Remote Monitor for Pi Presents")

        # self.root.configure(background='grey')

        self.root.resizable(False,False)

        # define response to main window closing
        self.root.protocol ("WM_DELETE_WINDOW", self.app_exit)

        # bind some display fields
        self.filename = StringVar()
        self.display_show = StringVar()
        self.results = StringVar()
        self.status = StringVar()

        # define menu
        menubar = Menu(self.root)

        toolsmenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        menubar.add_cascade(label='Tools', menu = toolsmenu)

        osc_configmenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        menubar.add_cascade(label='Options', menu = osc_configmenu)
        osc_configmenu.add_command(label='Edit', command = self.e_edit_osc)

        helpmenu = Menu(menubar, tearoff=0, bg="grey", fg="black")
        menubar.add_cascade(label='Help', menu = helpmenu)
        helpmenu.add_command(label='Help', command = self.show_help)
        helpmenu.add_command(label='About', command = self.about)
         
        self.root.config(menu=menubar)

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
#  OSC CONFIGURATION
# ***************************************

    def read_create_osc(self):
        if self.osc_config.read(self.osc_config_file) is False:
            self.osc_config.create(self.osc_config_file)
            eosc = OSCEditor(self.root, self.osc_config_file,'slave','Create OSC Monitor Configuration')
            self.osc_config.read(self.osc_config_file)


    def edit_osc(self):
        if self.osc_config.read(self.osc_config_file) is False:
            self.osc_config.create(self.osc_config_file)
        eosc = OSCEditor(self.root, self.osc_config_file,'slave','Edit OSC Monitor Configuration')


if __name__ == '__main__':

    oc = OSCMonitor()

