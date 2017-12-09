#! /usr/bin/env python

from Tkinter import Tk, StringVar,Frame,Label,Button,Scrollbar,Listbox,Entry,Text,OptionMenu
from Tkinter import Y,END,BOTH,LEFT,RIGHT,VERTICAL,SINGLE,NONE,W
import tkMessageBox
import tkSimpleDialog
import os
import ConfigParser

# ***************************************
#  OSC CONFIG CLASS
# ***************************************

# read is used by oscdriver
# everything is used by oscmonitor.py and oscremote.py

class OSCConfig(object):


    def read(self,options_file):
        self.options_file = options_file
        self.is_slave='no'
        self.is_master='no'
        
        if os.path.exists(self.options_file) is True:
            """reads options from options file"""
            config=ConfigParser.ConfigParser()
            config.read(self.options_file)

            # this unit
            self.this_unit_name = config.get('this-unit','name',0)
            self.this_unit_ip = config.get('this-unit','ip',0)

            self.slave_enabled= config.get('slave','enabled',0)
            self.listen_port =  config.get('slave','listen-port',0)  #listen on this port for messages

            self.master_enabled= config.get('master','enabled',0)                                  
            self.reply_listen_port = config.get('master','reply-listen-port',0)           
            self.slave_units_name = config.get('master','slave-units-name',0)
            self.slave_units_ip = config.get('master','slave-units-ip',0)
            return True
        else:
            return False



    def create(self,options_file,mode):
        self.options_file=options_file
        if not os.path.exists(self.options_file):
            config=ConfigParser.ConfigParser()
            
            config.add_section('this-unit')
            config.set('this-unit','ip','')
            if mode== 'master':            
                config.set('this-unit','name','remote')
            else:
                config.set('this-unit','name','monitor')                

            config.add_section('slave')
            
            if mode== 'slave':
                config.set('slave','enabled','yes')            
                config.set('slave','listen-port','9001')
            else:
                config.set('slave','enabled','no')            
                config.set('slave','listen-port','')            
            config.add_section('master')
            
            if mode== 'master':
                config.set('master','enabled','yes')
                config.set('master','reply-listen-port','9001') 
                config.set('master','slave-units-name','pipresents')
                config.set('master','slave-units-ip','raspberrypi')                   
            else:
                config.set('master','enabled','no')                
                config.set('master','reply-listen-port','') 
                config.set('master','slave-units-name','')
                config.set('master','slave-units-ip','')               
         
            with open(self.options_file, 'wb') as config_file:
                config.write(config_file)



# *************************************
# OCS EDITOR CLASS
# ************************************

class OSCEditor(tkSimpleDialog.Dialog):

    def __init__(self, parent, options_file, req_unit_type, title=None, ):
        self.options_file=options_file
        self.req_unit_type=req_unit_type

        # init the super class
        tkSimpleDialog.Dialog.__init__(self, parent, title)


    def body(self, master):
        self.result=False
        config=ConfigParser.ConfigParser()
        config.read(self.options_file)

        Label(master, text="").grid(row=30, sticky=W)
        Label(master, text="OSC Name of This Unit:").grid(row=31, sticky=W)
        self.e_this_unit_name = Entry(master,width=80)
        self.e_this_unit_name.grid(row=32)
        self.e_this_unit_name.insert(0,config.get('this-unit','name',0))
        

        Label(master, text="").grid(row=40, sticky=W)
        Label(master, text="IP of This Unit:").grid(row=41, sticky=W)
        self.e_this_unit_ip = Entry(master,width=80)
        self.e_this_unit_ip.grid(row=42)
        self.e_this_unit_ip.insert(0,config.get('this-unit','ip',0))

        Label(master, text="").grid(row=45, sticky=W)
        Label(master, text="OSC Slave Enabled (yes/no):").grid(row=46, sticky=W)
        self.e_slave_enabled = Entry(master,width=80)
        self.e_slave_enabled.grid(row=47)
        self.e_slave_enabled.insert(0,config.get('slave','enabled',0))

        Label(master, text="").grid(row=50, sticky=W)
        Label(master, text="Port for listening to commands for this Unit:").grid(row=51, sticky=W)
        self.e_listen_port = Entry(master,width=80)
        self.e_listen_port.grid(row=52)
        self.e_listen_port.insert(0,config.get('slave','listen-port',0))
        
        Label(master, text="").grid(row=55, sticky=W)
        Label(master, text="OSC Master Enabled (yes/no):").grid(row=56, sticky=W)
        self.e_master_enabled = Entry(master,width=80)
        self.e_master_enabled.grid(row=57)
        self.e_master_enabled.insert(0,config.get('master','enabled',0))
        

        Label(master, text="").grid(row=70, sticky=W)
        Label(master, text="Listen to replies from Slave Unit on Port:").grid(row=71, sticky=W)
        self.e_reply_listen_port = Entry(master,width=80)
        self.e_reply_listen_port.grid(row=72)
        self.e_reply_listen_port.insert(0,config.get('master','reply-listen-port',0))


        Label(master, text="").grid(row=80, sticky=W)
        Label(master, text="Slave Unit OSC Name (1 only):").grid(row=81, sticky=W)
        self.e_slave_units_name = Entry(master,width=80)
        self.e_slave_units_name.grid(row=82)
        self.e_slave_units_name.insert(0,config.get('master','slave-units-name',0))

        Label(master, text="").grid(row=90, sticky=W)
        Label(master, text="Slave Unit IP (1 only):").grid(row=91, sticky=W)
        self.e_slave_units_ip = Entry(master,width=80)
        self.e_slave_units_ip.grid(row=92)
        self.e_slave_units_ip.insert(0,config.get('master','slave-units-ip',0))

        return None    # no initial focus
    

    def validate(self):
        return 1

    def apply(self):
        self.save_options()
        self.result=True

    def save_options(self):
        """ save the output of the options edit dialog to file"""
        config=ConfigParser.ConfigParser()


        config.add_section('this-unit')
        config.set('this-unit','name',self.e_this_unit_name.get())
        config.set('this-unit','ip',self.e_this_unit_ip.get())


        config.add_section('slave')
        config.set('slave','enabled',self.e_slave_enabled.get())        
        config.set('slave','listen-port',self.e_listen_port.get())

        config.add_section('master')
        config.set('master','enabled',self.e_master_enabled.get()) 
        config.set('master','reply-listen-port',self.e_reply_listen_port.get())
        config.set('master','slave-units-name',self.e_slave_units_name.get())
        config.set('master','slave-units-ip',self.e_slave_units_ip.get())
        with open(self.options_file, 'wb') as optionsfile:
            config.write(optionsfile)
    


