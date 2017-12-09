#! /usr/bin/env python

import os
import ConfigParser


import remi.gui as gui
from remi_plus import OKDialog,AdaptableDialog

# ***************************************
#  OSC CONFIG CLASS
# ***************************************

class OSCConfig(object):

    current_unit_type=''  
    options_file=''


    def read(self):
        self.is_slave='no'
        self.is_master='no'
        # print 'in read',OSCConfig.options_file
        if os.path.exists(OSCConfig.options_file) is True:
            # reads options from options file
            config=ConfigParser.ConfigParser()
            config.read(OSCConfig.options_file)

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


    def create(self):
        #print 'create'
        if not os.path.exists(OSCConfig.options_file):
            #print'not exist'
            config=ConfigParser.ConfigParser()
            
            config.add_section('this-unit')
            config.set('this-unit','ip','')
            config.set('this-unit','name','')                

            config.add_section('slave')
            config.set('slave','enabled','no')            
            config.set('slave','listen-port','')

                
            config.add_section('master')
            config.set('master','enabled','no')
            config.set('master','reply-listen-port','') 
            config.set('master','slave-units-name','')
            config.set('master','slave-units-ip','')                   
           
            with open(self.options_file, 'wb') as config_file:
                config.write(config_file)
       
    
# *************************************
# OSC Web EDITOR CLASS
# ************************************

class OSCWebEditor(AdaptableDialog):
    

    def __init__(self, *args):
        super(OSCWebEditor, self).__init__(width=550,height=600,title='<b>Edit OSC Configuration</b>',
                                           confirm_name='OK',cancel_name='Cancel')

        self.append_field(gui.Label('<b>This Unit</b>',width=250,height=30))
        e_this_unit_name_field = gui.TextInput(width=250,height=30)
        self.append_field_with_label('OSC Name of This Unit:',e_this_unit_name_field,key='e_this_unit_name')       

        e_this_unit_ip_field = gui.TextInput(width=250,height=30)
        self.append_field_with_label('IP of This Unit:',e_this_unit_ip_field,key='e_this_unit_ip')

        #SLAVE
        self.append_field(gui.Label('<b>OSC Slave</b>',width=250,height=30))

        e_slave_enabled_field = gui.TextInput(width=250,height=30)
        self.append_field_with_label('OSC Slave enabled (yes/no):',e_slave_enabled_field,key='e_slave_enabled')  
        
        e_listen_port_field = gui.TextInput(width=250,height=30)
        self.append_field_with_label('Port for listening to commands for this Unit',e_listen_port_field,key='e_listen_port')
        

        # MASTER
        self.append_field(gui.Label('<b>OSC Master</b>',width=250,height=30))
        
        e_master_enabled_field = gui.TextInput(width=250,height=30)
        self.append_field_with_label('OSC Master enabled (yes/no):',e_master_enabled_field,key='e_master_enabled')  
        
        e_reply_listen_port_field = gui.TextInput(width=250,height=30)
        self.append_field_with_label('Listen to replies from Slave Unit on Port:',e_reply_listen_port_field,key='e_reply_listen_port')


        e_slave_units_name_field = gui.TextInput(width=250,height=30)
        self.append_field_with_label('Slave Units OSC Name:',e_slave_units_name_field,key='e_slave_units_name')

        e_slave_units_ip_field = gui.TextInput(width=250,height=30)
        self.append_field_with_label('Slave Units IP:',e_slave_units_ip_field,key='e_slave_units_ip')
        
        return



    def edit(self):

        # print 'edit_options in class'
        config=ConfigParser.ConfigParser()
        config.read(OSCConfig.options_file)


        self.get_field('e_this_unit_name').set_value(config.get('this-unit','name',0))
        self.get_field('e_this_unit_ip').set_value(config.get('this-unit','ip',0))
        
        self.get_field('e_slave_enabled').set_value(config.get('slave','enabled',0))
        self.get_field('e_listen_port').set_value(config.get('slave','listen-port',0))


        self.get_field('e_master_enabled').set_value(config.get('master','enabled',0))
        self.get_field('e_reply_listen_port').set_value(config.get('master','reply-listen-port',0))


        self.get_field('e_slave_units_name').set_value(config.get('master','slave-units-name',0))
        self.get_field('e_slave_units_ip').set_value(config.get('master','slave-units-ip',0))



    def confirm_dialog(self):

        if self.get_field('e_this_unit_name').get_value() =='':
            OKDialog('OSC Config','This Unit OSC Name must not be blank').show(self._base_app_instance)
            return

        slave_enabled = self.get_field('e_slave_enabled').get_value().strip()
        
        if slave_enabled not in ('yes','no'):
            OKDialog('OSC Config','Slave Enabled must be yes or no').show(self._base_app_instance)
            return

        if slave_enabled == 'yes':
            if not self.get_field('e_listen_port').get_value().isdigit():
                OKDialog('OSC Config','Listen Port must be a positive integer').show(self._base_app_instance)
                return

        master_enabled = self.get_field('e_master_enabled').get_value().strip()

        if master_enabled not in ('yes','no'):
            OKDialog('OSC Config','Master Enabled must be yes or no').show(self._base_app_instance)
            return

        if master_enabled == 'yes':
            if not self.get_field('e_reply_listen_port').get_value().isdigit():
                OKDialog('OSC Config','Reply Listen Port must be a positive integer').show(self._base_app_instance)
                return
            
            if self.get_field('e_slave_units_name').get_value() =='':
                OKDialog('OSC Config','Slave Units OSC Name must not be blank').show(self._base_app_instance)
                return

            if self.get_field('e_slave_units_ip').get_value() =='':
                OKDialog('OSC Config','Slave Units IP must not be blank').show(self._base_app_instance)
                return
        self.save()
        self.hide()




    def save(self):

        # save the output of the options edit dialog to file
        config=ConfigParser.ConfigParser()

        config.add_section('this-unit')
        config.set('this-unit','name',self.get_field('e_this_unit_name').get_value())
        config.set('this-unit','ip',self.get_field('e_this_unit_ip').get_value())

        #slave
        config.add_section('slave')
        config.set('slave','enabled',self.get_field('e_slave_enabled').get_value())        
        config.set('slave','listen-port',self.get_field('e_listen_port').get_value())

        config.add_section('master')
        config.set('master','enabled',self.get_field('e_master_enabled').get_value())        
        config.set('master','reply-listen-port',self.get_field('e_reply_listen_port').get_value())
        config.set('master','slave-units-name',self.get_field('e_slave_units_name').get_value())
        config.set('master','slave-units-ip',self.get_field('e_slave_units_ip').get_value())
            
        with open(OSCConfig.options_file, 'wb') as optionsfile:
            config.write(optionsfile)



