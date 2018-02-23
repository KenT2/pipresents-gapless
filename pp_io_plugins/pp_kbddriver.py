import os
import ConfigParser
from pp_utils import Monitor

class pp_kbddriver(object):

    # CLASS VARIABLES  (pp_gpiodriver.)
    driver_active=False
    title=''

    config=None

    def __init__(self):
        self.mon=Monitor()

    def init(self,filename,filepath,widget,callback=None):

        # instantiate arguments
        self.widget=widget
        self.filename=filename
        self.filepath=filepath
        self.callback=callback
        pp_kbddriver.driver_active = False
        # print filename,filepath
        # read .cfg file.
        reason,message=self._read(self.filename,self.filepath)
        if reason =='error':
            return 'error',message
        if self.config.has_section('DRIVER') is False:
            return 'error','No DRIVER section in '+self.filepath
        
        #read information from DRIVER section
        pp_kbddriver.title=self.config.get('DRIVER','title')
        self.bind_printing = self.config.get('DRIVER','bind-printing')

        # and bind the keys
        self._bind_keys(widget,callback)
        pp_kbddriver.driver_active = True
        return 'normal', pp_kbddriver.title + 'Initialised'

    def start (self):
        return

    # allow track plugins (or anyting else) to access analog input values
    def get_input(self,channel):
            return False, None


    def terminate(self):
        pp_kbddriver.driver_active = False
        return

    def is_active(self):
        return pp_kbddriver.driver_active

    def handle_output_event(self,name,param_type,param_values,req_time):
        return 'normal','no output methods'


    # sets up tkinter keyboard events such that any key press
    # does a callback to 'callback' with the event object and a symbolic name.
    def _bind_keys(self,widget,callback):

        # bind all the normal keys that return a printing character such that x produces pp-key-x
        if self.bind_printing =='yes':
            widget.bind("<Key>", lambda event : self._normal_key(callback,event))
            
        for option in self.config.items('keys'):
            condition=option[0]
            symbolic_name=option[1]
            # print condition,symbolic_name
            # print condition,symbolic_name
            widget.bind(condition, lambda event, name=symbolic_name: self._specific_key(callback,name))


    def _specific_key(self,callback,name):
        callback(name,pp_kbddriver.title)

    # alphanumeric keys- convert to symbolic by adding pp-key-
    def _normal_key(self,callback,event):
        key=event.char
        if key != '':
            callback('pp-key-'+key,pp_kbddriver.title)


    # read the key bindings from keys.cfg
    def _read(self,filename,filepath):
        if os.path.exists(filepath):
            self.config = ConfigParser.ConfigParser()
            self.config.optionxform = str
            self.config.read(filepath)
            return 'normal',filename+' read'
        else:
            return 'error',filename+' not found at: '+filepath






   
