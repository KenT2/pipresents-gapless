import os
import ConfigParser
from pp_utils import Monitor

class KbdDriver(object):

    config=None

    def __init__(self):
        self.mon=Monitor()

    # sets up tkinter keyboard events such that any key press
    # does a callback to 'callback' with the event object and a symbolic name.
    def bind_keys(self,widget,callback):
        for option in KbdDriver.config.items('keys'):
            condition=option[0]
            symbolic_name=option[1]
            # print condition,symbolic_name
            widget.bind(condition, lambda event, name=symbolic_name: self.specific_key(callback,name))

        # bind all the normal keys that return a printing character such that x produces pp-key-x
        widget.bind("<Key>", lambda event : self.normal_key(callback,event))


    def specific_key(self,callback,name):
        callback(name,'KBD')

    # alphanumeric keys- convert to symbolic by adding pp-key-
    def normal_key(self,callback,event):
        key=event.char
        if key != '':
            callback('pp-key-'+key,'KBD')



     # read the key bindings from keys.cfg
    def read(self,pp_dir,pp_home,pp_profile):
        if KbdDriver.config is None:
            # try inside profile
            tryfile=pp_profile+os.sep+'keys.cfg'
            # self.mon.log(self,"Trying keys.cfg in profile at: "+ tryfile)
            if os.path.exists(tryfile):
                filename=tryfile
            else:
                # try inside pp_home
                # self.mon.log(self,"keys.cfg not found at "+ tryfile+ " trying pp_home")
                tryfile=pp_home+os.sep+"keys.cfg"
                if os.path.exists(tryfile):
                    filename=tryfile
                else:
                    # try inside pipresents
                    # self.mon.log(self,"keys.cfg not found at "+ tryfile + " trying inside pipresents")
                    tryfile=pp_dir+os.sep+'pp_config'+os.sep+"keys.cfg"
                    if os.path.exists(tryfile):
                        filename=tryfile
                    else:
                        self.mon.log(self,"keys.cfg not found at "+ tryfile)
                        self.mon.err(self,"keys.cfg not found")
                        return False   
            KbdDriver.config = ConfigParser.ConfigParser()
            KbdDriver.config.optionxform=str
            KbdDriver.config.read(filename)
            self.mon.log(self,"keys.cfg read from "+ filename)
            if KbdDriver.config.has_section('keys') is False:
                self.mon.err(self,"no [keys] section in keys.cfg")
                return False
            return True

    def has_section(self,section):
        if KbdDriver.config.has_section(section) is False:
            return False



   
