#! /usr/bin/env python

from Tkinter import Tk, StringVar, Menu,Frame,Label,Button,Scrollbar,Listbox,Entry,Text,OptionMenu
from Tkinter import Y,END,TOP,BOTH,LEFT,RIGHT,VERTICAL,SINGLE,NONE,W
import tkFileDialog
import tkMessageBox
import tkSimpleDialog
import os
import sys
import ConfigParser
import shutil
import copy
import string


from pp_utils import Monitor

# ***************************************
#  OSC CONFIG CLASS
# ***************************************

class OSCConfig(object):


    def read(self,options_file):
        self.options_file = options_file
        if os.path.exists(self.options_file) is True:
            """reads options from options file"""
            config=ConfigParser.ConfigParser()
            config.read(self.options_file)

            # this unit
            self.this_unit_name = config.get('this-unit','name',0)
            self.this_unit_ip=config.get('this-unit','ip',0)
            self.this_unit_port =  config.get('this-unit','port',0)  #listen on this port for messages and for replies from controlled units
            self.this_unit_type = config.get('this-unit','type')

            if self.this_unit_type in ('master','remote','master+slave'):
                this_unit_controlled_units = config.get('this-unit','controlled-units',0)
                # controller1
                self.controlled_unit_1_ip = config.get('controlled-unit-1','controlled-unit-ip',0)
                self.controlled_unit_1_port = config.get('controlled-unit-1','controlled-unit-port',0)            
                self.controlled_unit_1_name = config.get('controlled-unit-1','controlled-unit-name',0)
                
            if self.this_unit_type in ('slave','master+slave'):
                # controlled by
                self.controlled_by_ip = config.get('this-unit','controlled-by-ip',0)
                self.controlled_by_port = config.get('this-unit','controlled-by-port',0)            
                self.controlled_by_name = config.get('this-unit','controlled-by-name',0)
                
            if self.this_unit_type == 'remote':
                self.pp_home_dir =config.get('paths','home',0)
                self.pp_profiles_offset =config.get('paths','offset',0)
            return True
        else:
            return False



    def create(self,options_file):
        self.options_file=options_file
        if not os.path.exists(self.options_file):
            config=ConfigParser.ConfigParser()
            config.add_section('this-unit')
            config.set('this-unit','name','')
            config.set('this-unit','type','')
            config.set('this-unit','ip','')
            config.set('this-unit','port','') 
            
            config.set('this-unit','controlled-by-name','')            
            config.set('this-unit','controlled-by-ip','')
            config.set('this-unit','controlled-by-port','')
            config.set('this-unit','controlled-units','')
            config.add_section('controlled-unit-1')            
            config.set('controlled-unit-1','controlled-unit-name','') 
            config.set('controlled-unit-1','controlled-unit-ip','')
            config.set('controlled-unit-1','controlled-unit-port','')

            config.add_section('paths')
            config.set('paths','offset','')
            if os.name == 'nt':
                config.set('paths','home',os.path.expanduser('~')+'\pp_home')
            else:
                config.set('paths','home',os.path.expanduser('~')+'/pp_home')

            with open(self.options_file, 'wb') as config_file:
                config.write(config_file)


# *************************************
# OCS UNIT TYPE CLASS
# ************************************

class OSCUnitType(tkSimpleDialog.Dialog):

    def __init__(self, parent, current_type):
        # save the extra args to instance variables
        self.current_type = current_type 
        # and call the base class _init_which uses the args in body
        tkSimpleDialog.Dialog.__init__(self, parent, 'OSC Unit Type')


    def body(self, master):
        Label(master, text='Current Type: ').grid(row=0,column=0)
        Label(master, text=self.current_type).grid(row=0,column=1)
        Label(master, text='Change: ').grid(row=1,column=0)
        self.option_val = StringVar(master)    
        self.option_val.set(self.current_type)
        om = OptionMenu (master, self.option_val, 'master','slave','master+slave')
        om.grid(row=1,column=1,sticky=W)
        return om # initial focus on menu

    def apply(self):
        self.result= self.option_val.get()

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

        if self.req_unit_type=='remote':
            Label(master, text="").grid(row=10, sticky=W)
            Label(master, text="Pi Presents Data Home:").grid(row=11, sticky=W)
            self.e_home = Entry(master,width=80)
            self.e_home.grid(row=12)
            self.e_home.insert(0,config.get('paths','home',0))

            Label(master, text="").grid(row=20, sticky=W)
            Label(master, text="Offset for Current Profiles:").grid(row=21, sticky=W)
            self.e_offset = Entry(master,width=80)
            self.e_offset.grid(row=22)
            self.e_offset.insert(0,config.get('paths','offset',0))


        Label(master, text="").grid(row=25, sticky=W)
        Label(master, text="Type of this Unit:").grid(row=26, sticky=W)
        self.e_type = Entry(master,width=80)
        self.e_type.grid(row=27)
        self.e_type.insert(0,self.req_unit_type)
        self.e_type.config(state="readonly",bg='dark grey')

        Label(master, text="").grid(row=30, sticky=W)
        Label(master, text="Name of This Unit:").grid(row=31, sticky=W)
        self.e_remote_name = Entry(master,width=80)
        self.e_remote_name.grid(row=32)
        self.e_remote_name.insert(0,config.get('this-unit','name',0))
        
        Label(master, text="").grid(row=40, sticky=W)
        Label(master, text="IP of This Unit:").grid(row=41, sticky=W)
        self.e_remote_ip = Entry(master,width=80)
        self.e_remote_ip.grid(row=42)
        self.e_remote_ip.insert(0,config.get('this-unit','ip',0))

        Label(master, text="").grid(row=50, sticky=W)
        Label(master, text="Listening Port of This Unit:").grid(row=51, sticky=W)
        self.e_remote_port = Entry(master,width=80)
        self.e_remote_port.grid(row=52)
        self.e_remote_port.insert(0,config.get('this-unit','port',0))

        if self.req_unit_type in ('master','remote','master+slave'):
            Label(master, text="").grid(row=60, sticky=W)
            Label(master, text="Controlled Units (not used):").grid(row=61, sticky=W)
            self.e_controlled_units = Entry(master,width=80)
            self.e_controlled_units.grid(row=62)
            self.e_controlled_units.insert(0,config.get('this-unit','controlled-units',0))

            Label(master, text="").grid(row=70, sticky=W)
            Label(master, text="Name of Controlled Unit:").grid(row=71, sticky=W)
            self.e_pipresents_unit = Entry(master,width=80)
            self.e_pipresents_unit.grid(row=72)
            self.e_pipresents_unit.insert(0,config.get('controlled-unit-1','controlled-unit-name',0))
            
            Label(master, text="").grid(row=80, sticky=W)
            Label(master, text="IP of Controlled Unit:").grid(row=81, sticky=W)
            self.e_pipresents_ip = Entry(master,width=80)
            self.e_pipresents_ip.grid(row=82)
            self.e_pipresents_ip.insert(0,config.get('controlled-unit-1','controlled-unit-ip',0))

            Label(master, text="").grid(row=90, sticky=W)
            Label(master, text="Listening Port of Controlled Unit:").grid(row=91, sticky=W)
            self.e_pipresents_port = Entry(master,width=80)
            self.e_pipresents_port.grid(row=92)
            self.e_pipresents_port.insert(0,config.get('controlled-unit-1','controlled-unit-port',0))


        if self.req_unit_type in('slave','master+slave'):
            Label(master, text="").grid(row=100, sticky=W)
            Label(master, text="Controlled By Unit:").grid(row=101, sticky=W)
            self.e_controlled_by_unit = Entry(master,width=80)
            self.e_controlled_by_unit.grid(row=102)
            self.e_controlled_by_unit.insert(0,config.get('this-unit','controlled-by-name',0))


            Label(master, text="").grid(row=110, sticky=W)
            Label(master, text="IP of Controlled By Unit:").grid(row=111, sticky=W)
            self.e_controlled_by_ip = Entry(master,width=80)
            self.e_controlled_by_ip.grid(row=112)
            self.e_controlled_by_ip.insert(0,config.get('this-unit','controlled-by-ip',0))

            Label(master, text="").grid(row=120, sticky=W)
            Label(master, text="Listening Port of Controlled  By Unit:").grid(row=121, sticky=W)
            self.e_controlled_by_port = Entry(master,width=80)
            self.e_controlled_by_port.grid(row=122)
            self.e_controlled_by_port.insert(0,config.get('this-unit','controlled-by-port',0))

        return None    # no initial focus

    def validate(self):
        if self.req_unit_type == 'remote':
            if self.e_home.get().strip() != '':
                if os.path.exists(self.e_home.get()) is  False:
                    tkMessageBox.showwarning("Pi Presents Remote","Data Home not found")
                    return 0
            if self.e_offset.get().strip() != '':
                if os.path.exists(self.e_home.get()+os.sep+'pp_profiles'+self.e_offset.get()) is  False:
                    tkMessageBox.showwarning("Pi Presents Remote","Current Profles directory not found")
                    return 0
        return 1

    def apply(self):
        self.save_options()
        self.result=True

    def save_options(self):
        """ save the output of the options edit dialog to file"""
        config=ConfigParser.ConfigParser()

        config.add_section('paths')
        if self.req_unit_type == 'remote':
            config.set('paths','home',self.e_home.get())
            config.set('paths','offset',self.e_offset.get())
        else:
            config.set('paths','home','')
            config.set('paths','offset','')
        
        config.add_section('this-unit')
        config.set('this-unit','name',self.e_remote_name.get())
        config.set('this-unit','ip',self.e_remote_ip.get())
        config.set('this-unit','port',self.e_remote_port.get())
        config.set('this-unit','type',self.req_unit_type)

        config.add_section('controlled-unit-1')
        if self.req_unit_type in ('master','remote','master+slave'):
            config.set('this-unit','controlled-units',self.e_controlled_units.get())
            config.set('controlled-unit-1','controlled-unit-name',self.e_pipresents_unit.get())
            config.set('controlled-unit-1','controlled-unit-ip',self.e_pipresents_ip.get())
            config.set('controlled-unit-1','controlled-unit-port',self.e_pipresents_port.get())
        else:
            config.set('this-unit','controlled-units','')
            config.set('controlled-unit-1','controlled-unit-name','')
            config.set('controlled-unit-1','controlled-unit-ip','')
            config.set('controlled-unit-1','controlled-unit-port','')

        if self.req_unit_type in ('slave','master+slave'):
            config.set('this-unit','controlled-by-name',self.e_controlled_by_unit.get())
            config.set('this-unit','controlled-by-ip',self.e_controlled_by_ip.get())
            config.set('this-unit','controlled-by-port',self.e_controlled_by_port.get())
        else:
            config.set('this-unit','controlled-by-name','')
            config.set('this-unit','controlled-by-ip','')
            config.set('this-unit','controlled-by-port','')
            
        with open(self.options_file, 'wb') as optionsfile:
            config.write(optionsfile)
    


