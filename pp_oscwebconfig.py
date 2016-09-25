#! /usr/bin/env python

import os
import ConfigParser


import remi.gui as gui
from remi_plus import OKDialog

# ***************************************
#  OSC CONFIG CLASS
# ***************************************

class OSCConfig(object):

    current_unit_type=''  
    options_file=''


    def read(self):
        # print 'in read',OSCConfig.options_file
        if os.path.exists(OSCConfig.options_file) is True:
            # reads options from options file
            config=ConfigParser.ConfigParser()
            config.read(OSCConfig.options_file)

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
            OSCConfig.current_unit_type=self.this_unit_type
            return True
        else:
            return False



    def create(self):
        # print 'create'
        if not os.path.exists(OSCConfig.options_file):
            config=ConfigParser.ConfigParser()
            config.add_section('this-unit')
            config.set('this-unit','name','')
            config.set('this-unit','type','Select')
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

            with open(OSCConfig.options_file, 'wb') as config_file:
                config.write(config_file)




    def delete(self):
        os.rename(OSCConfig.options_file,OSCConfig.options_file+'.bak')
    
# *************************************
# OSC Web EDITOR CLASS
# ************************************

class OSCWebEditor(gui.GenericDialog):
    

    def __init__(self, *args):
        super(OSCWebEditor, self).__init__(width=500,height=600,title='<b>Edit OSC Configuration</b>')
        self.set_on_confirm_dialog_listener(self,'confirm')
        if  OSCConfig.current_unit_type=='remote':
            e_home_field = gui.TextInput(width=200,height=30)
            self.add_field_with_label('e_home','Pi Presents Data Home:',e_home_field)            

            e_offset_field = gui.TextInput(width=200,height=30)
            self.add_field_with_label('e_offset','Offset for Current Profiles:',e_offset_field)            

        e_type_field = gui.Label('',width=200,height=30)
        self.add_field_with_label('e_type','Type of this Unit:',e_type_field)            

        e_remote_name_field = gui.TextInput(width=200,height=30)
        self.add_field_with_label('e_remote_name','Name of This Unit:',e_remote_name_field)       

        e_remote_ip_field = gui.TextInput(width=200,height=30)
        self.add_field_with_label('e_remote_ip','IP of This Unit:',e_remote_ip_field)    
        
        e_remote_port_field = gui.TextInput(width=200,height=30)
        self.add_field_with_label('e_remote_port','Listening Port of This Unit:',e_remote_port_field)
        

        if  OSCConfig.current_unit_type in ('master','remote','master+slave'):
            e_controlled_units_field = gui.TextInput(width=200,height=30)
            self.add_field_with_label('e_controlled_units','Controlled Units (not used):',e_controlled_units_field)

            e_pipresents_unit_field = gui.TextInput(width=200,height=30)
            self.add_field_with_label('e_pipresents_unit','Name of Controlled Unit:',e_pipresents_unit_field)

            e_pipresents_ip_field = gui.TextInput(width=200,height=30)
            self.add_field_with_label('e_pipresents_ip','IP of Controlled Unit:',e_pipresents_ip_field)

            e_pipresents_port_field = gui.TextInput(width=200,height=30)
            self.add_field_with_label('e_pipresents_port','Listening Port of Controlled Unit:',e_pipresents_port_field)
             
        if  OSCConfig.current_unit_type in('slave','master+slave'):
            e_controlled_by_unit_field = gui.TextInput(width=200,height=30)
            self.add_field_with_label('e_controlled_by_unit','Controlled By Unit:',e_controlled_by_unit_field)

            e_controlled_by_ip_field = gui.TextInput(width=200,height=30)
            self.add_field_with_label('e_controlled_by_ip','IP of Controlled By Unit:',e_controlled_by_ip_field)

            e_controlled_by_port_field = gui.TextInput(width=200,height=30)
            self.add_field_with_label('e_controlled_by_port','Listening Port of Controlled By Unit:',e_controlled_by_port_field)
        return



    def edit(self):

        # print 'edit_options in class'
        config=ConfigParser.ConfigParser()
        config.read(OSCConfig.options_file)

        if OSCConfig.current_unit_type=='remote':      
            self.get_field('e_home').set_value(config.get('paths','home',0))
            self.get_field('e_offset').set_value(config.get('paths','offset',0))

        self.get_field('e_type').set_text(OSCConfig.current_unit_type)
        self.get_field('e_remote_name').set_value(config.get('this-unit','name',0))
        self.get_field('e_remote_ip').set_value(config.get('this-unit','ip',0))
        self.get_field('e_remote_port').set_value(config.get('this-unit','port',0))

        if OSCConfig.current_unit_type in ('master','remote','master+slave'):
            self.get_field('e_controlled_units').set_value(config.get('this-unit','controlled-units',0))
            self.get_field('e_pipresents_unit').set_value(config.get('controlled-unit-1','controlled-unit-name',0))
            self.get_field('e_pipresents_ip').set_value(config.get('controlled-unit-1','controlled-unit-ip',0))
            self.get_field('e_pipresents_port').set_value(config.get('controlled-unit-1','controlled-unit-port',0))

        if OSCConfig.current_unit_type in ('slave','master+slave'):
            self.get_field('e_controlled_by_unit').set_value(config.get('this-unit','controlled-by-name',0))
            self.get_field('e_controlled_by_ip').set_value(config.get('this-unit','controlled-by-ip',0))
            self.get_field('e_controlled_by_port').set_value(config.get('this-unit','controlled-by-port',0))



    def confirm(self):
        if OSCConfig.current_unit_type == 'remote':
            if self.get_field('e_home').get_value().strip() != '':
                if os.path.exists( self.get_field('e_home').get_value()) is  False:
                    OKDialog("Pi Presents Remote","Data Home not found").show(self)
                    return
            if self.get_field('e_offset').get_value().strip() != '':
                if os.path.exists(self.e_home.get()+os.sep+'pp_profiles'+self.get_field('e_offset').get_value()) is  False:
                    OKDialog("Pi Presents Remote","Current Profles directory not found").show(self)
                    return
        # print 'try save'
        self.hide()
        self.save()



    def save(self):
        # print ' in save'
        # save the output of the options edit dialog to file
        config=ConfigParser.ConfigParser()

        config.add_section('paths')
        if OSCConfig.current_unit_type == 'remote':
            config.set('paths','home',self.get_field('e_home').get_value())
            config.set('paths','offset',self.get_field('e_offset').get_value())
        else:
            config.set('paths','home','')
            config.set('paths','offset','')
        
        config.add_section('this-unit')
        config.set('this-unit','name',self.get_field('e_remote_name').get_value())
        config.set('this-unit','ip',self.get_field('e_remote_ip').get_value())
        config.set('this-unit','port',self.get_field('e_remote_port').get_value())
        config.set('this-unit','type',OSCConfig.current_unit_type)

        config.add_section('controlled-unit-1')
        if OSCConfig.current_unit_type in ('master','remote','master+slave'):
            config.set('this-unit','controlled-units',self.get_field('e_controlled_units').get_value())
            config.set('controlled-unit-1','controlled-unit-name',self.get_field('e_pipresents_unit').get_value())
            config.set('controlled-unit-1','controlled-unit-ip',self.get_field('e_pipresents_ip').get_value())
            config.set('controlled-unit-1','controlled-unit-port',self.get_field('e_pipresents_port').get_value())
        else:
            config.set('this-unit','controlled-units','')
            config.set('controlled-unit-1','controlled-unit-name','')
            config.set('controlled-unit-1','controlled-unit-ip','')
            config.set('controlled-unit-1','controlled-unit-port','')

        if OSCConfig.current_unit_type in ('slave','master+slave'):
            config.set('this-unit','controlled-by-name',self.get_field('e_controlled_by_unit').get_value())
            config.set('this-unit','controlled-by-ip',self.get_field('e_controlled_by_ip').get_value())
            config.set('this-unit','controlled-by-port',self.get_field('e_controlled_by_port').get_value())
        else:
            config.set('this-unit','controlled-by-name','')
            config.set('this-unit','controlled-by-ip','')
            config.set('this-unit','controlled-by-port','')
            
        with open(OSCConfig.options_file, 'wb') as optionsfile:
            config.write(optionsfile)



# *************************************
# OSC UNIT TYPE EDITOR CLASS
# ************************************

class OSCUnitType(gui.GenericDialog):

    # define the gui  at initilisation time
    def __init__(self, *args):
        super(OSCUnitType, self).__init__(width=500,height=300,title='<b>Select Unit Type</b>')

        e_current_type_field = gui.Label('',width=200,height=30)
        self.add_field_with_label('e_type','Current Type:',e_current_type_field)
        e_req_type_field = gui.DropDown(width=200, height=30)
        c0 = gui.DropDownItem('Select',width=200, height=20)
        c1 = gui.DropDownItem('master',width=200, height=20)
        c2 = gui.DropDownItem('slave',width=200, height=20)
        c3 = gui.DropDownItem('master + slave',width=200, height=20)
        e_req_type_field.append(c0)
        e_req_type_field.append(c1)
        e_req_type_field.append(c2)
        e_req_type_field.append(c3)
        self.add_field_with_label('e_req_type','Change Type:',e_req_type_field)
        error_field= gui.Label('',width=400, height=30)
        self.add_field('error',error_field)
        e_req_type_field.set_value(OSCConfig.current_unit_type)
        self.set_on_confirm_dialog_listener(self,'confirm')

    # populate the gui just before showing it
    def edit(self,callback):
        self.callback=callback
        self.get_field('error').set_text('')
        self.get_field('e_type').set_text(OSCConfig.current_unit_type)
        self.get_field('e_req_type').set_value(OSCConfig.current_unit_type)


    #called when the user presses the OK button
    def confirm(self):
        req_type=self.get_field('e_req_type').get_value()
        # print 'confirm uts',req_type
        if req_type == 'Select':
            self.get_field('error').set_text('<b>Unit Type not Selected</b>')
            return
        OSCConfig.current_unit_type=req_type
        self.get_field('error').set_text('')
        self.hide()
        self.callback()


