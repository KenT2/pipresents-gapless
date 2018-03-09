#enhanced keyboard driver
import copy
import os
import ConfigParser


class pp_kbddriver_plus(object):

    # control list items
    NAME=0                # symbolic name for input and output
    DIRECTION = 1         # in/out
    MATCH = 2             # for input the character/string to match (no EOL)
    MODE= 3               # for input the match mode any-char,char,any-line,line

    TEMPLATE=['','','','']

# CLASS VARIABLES  (pp_kbddriver_plus.)
    driver_active=False
    title=''          # usd for error reporting and logging
    tick_interval=''     # mS between polls of the serial input

    match_mode=''     # char or line, whether input characters are matched for each character or a complete line

    inputs={}

    # executed by main program and by each object using the driver
    def __init__(self):
        pass

     # executed once from main program   
    def init(self,filename,filepath,widget,event_callback=None):
        
        # instantiate arguments
        self.widget=widget
        self.filename=filename
        self.filepath=filepath
        self.event_callback=event_callback

        pp_kbddriver_plus.driver_active = False

        # read pp_kbddriver_plus.cfg file.
        reason,message=self._read(self.filename,self.filepath)
        if reason =='error':
            return 'error',message
        if self.config.has_section('DRIVER') is False:
            return 'error','No DRIVER section in '+self.filepath
        
        # all the below are used by another instance of pp_kbddriver_plus so must reference class variables
        # read information from DRIVER section
        pp_kbddriver_plus.title=self.config.get('DRIVER','title')
        pp_kbddriver_plus.bind_printing = self.config.get('DRIVER','bind-printing')
        
        # construct the control list from the config file
        pp_kbddriver_plus.in_names=[]
        pp_kbddriver_plus.out_names=[]
        for section in self.config.sections():
            if section == 'DRIVER':
                continue
            entry=copy.deepcopy(pp_kbddriver_plus.TEMPLATE)
            entry[pp_kbddriver_plus.NAME]=self.config.get(section,'name')
            entry[pp_kbddriver_plus.DIRECTION]=self.config.get(section,'direction')
            if entry[pp_kbddriver_plus.DIRECTION] == 'none':
                continue
            elif entry[pp_kbddriver_plus.DIRECTION] == 'in':
                entry[pp_kbddriver_plus.MODE]=self.config.get(section,'mode')
                if entry[pp_kbddriver_plus.MODE] in ('specific-character','specific-line'):
                    entry[pp_kbddriver_plus.MATCH]=self.config.get(section,'match')
                pp_kbddriver_plus.in_names.append(copy.deepcopy(entry))
            else:
                return 'error',pp_kbddriver_plus.title + ' direction not in or out'
        # print pp_kbddriver_plus.in_names

        # bind the keys
        self._bind_keys(widget,self._key_received)
        
        # all ok so indicate the driver is active
        pp_kbddriver_plus.driver_active=True

        # init must return two arguments
        return 'normal',pp_kbddriver_plus.title + ' active'



    # sets up tkinter keyboard events such that any key press
    # does a callback to _key_received() with the event object
    def _bind_keys(self,widget,callback):

        # bind all the normal keys that return a printing character such that x produces pp-key-x (but fileterd in _key_received)
        widget.bind("<Key>", lambda event,match='<Key>',name='': self._key_received(event,match,name))
        # print 'bind printing'

        # Bind <Return> so that eol detection works, <Return> cannot be used to trigger an input event
        # if you wnt that use keys.cfg
        widget.bind("<Return>", lambda event,match='<Return>',name='': self._key_received(event,match,name))
        # print 'bind Return to make eol work'
            
        # go through entries and bind all specific-character matches to _key_received
        for entry in pp_kbddriver_plus.in_names:
            if entry[pp_kbddriver_plus.MODE] == 'specific-character':
                match = entry[pp_kbddriver_plus.MATCH]
                name = entry[pp_kbddriver_plus.NAME]
                widget.bind(match, lambda event, match=match,name=name: self._key_received(event,match,name))
                # print 'bind specific-char', match,name


    # start method must be defined. If not using inputs just pass 
    def start(self):
        pp_kbddriver_plus.inputs['current-character']=''
        pp_kbddriver_plus.inputs['current-line']=''
        pp_kbddriver_plus.inputs['previous-line']=''

        
    def _key_received(self,event,match,name):
        # generate the events with symbolic names if driver is active
        if pp_kbddriver_plus.driver_active is True:
            char=event.char
            # print 'received ',char,match,name

            # if char is eol then match the line and start a new line
            if match =='<Return>':
                # do match of line
                # print 'do match line',pp_kbddriver_plus.inputs['current-line']
                self.match_line(pp_kbddriver_plus.inputs['current-line'])
                # shuffle and empty the buffer
                pp_kbddriver_plus.inputs['previous-line'] = pp_kbddriver_plus.inputs['current-line']
                pp_kbddriver_plus.inputs['current-line']=''
                pp_kbddriver_plus.inputs['current-character']=''
                if name !='':
                    # print 'bound <Return> key'
                    if self.event_callback  is not  None:
                        self.event_callback(name,pp_kbddriver_plus.title)                
            else:
                # process a character
                if char == '' and match == '<Key>':
                    # unbound special key
                    # print 'unbound special key ', match
                    pass
                else:
                    # a character has been received
                    pp_kbddriver_plus.inputs['current-character']=char
                    pp_kbddriver_plus.inputs['current-line']+=char
                    # print pp_kbddriver_plus.inputs['current-character'],pp_kbddriver_plus.inputs['current-line']
                    if match == '<Key>' and char != '' and self.bind_printing =='yes':
                        # print 'printable key, bind-printing is yes',char,match
                        # printable character without overiding section
                        if self.event_callback  is not  None:
                            self.event_callback('pp-key-'+ char,pp_kbddriver_plus.title)
                    else:
                        if name != '':
                            # print 'bound non-printable character',char,name
                            if self.event_callback  is not  None:
                                self.event_callback(name,pp_kbddriver_plus.title)
                            
                    # look through entries for any-character
                    for entry in pp_kbddriver_plus.in_names:
                        if entry[pp_kbddriver_plus.MODE] == 'any-character':
                            # print 'match any character', char, 'current line is ',pp_kbddriver_plus.inputs['current-line']
                            if self.event_callback  is not  None:
                                    self.event_callback(entry[pp_kbddriver_plus.NAME],pp_kbddriver_plus.title)                        
                
                    

    def match_line(self,line):
        for entry in pp_kbddriver_plus.in_names:
            if entry[pp_kbddriver_plus.MODE] == 'any-line':
                # print 'match any line',line
                if self.event_callback  is not  None:
                        self.event_callback(entry[pp_kbddriver_plus.NAME],pp_kbddriver_plus.title)

            if entry[pp_kbddriver_plus.MODE] == 'specific-line' and line == entry[pp_kbddriver_plus.MATCH]:
                # print 'match specific line', line
                if self.event_callback  is not  None:
                        self.event_callback(entry[pp_kbddriver_plus.NAME],pp_kbddriver_plus.title)



    # allow track plugins (or anything else) to access analog input values
    def get_input(self,key):
        if key in pp_kbddriver_plus.inputs:
            return True, pp_kbddriver_plus.inputs[key]
        else:
            return False, None


    # allow querying of driver state
    def is_active(self):
        return pp_kbddriver_plus.driver_active


    # called by main program only. Called when PP is closed down               
    def terminate(self):
            pp_kbddriver_plus.driver_active = False



# ************************************************
# output interface method
# this can be called from many objects so needs to operate on class variables
# ************************************************                            
    # execute an output event

    def handle_output_event(self,name,param_type,param_values,req_time):
        return 'normal','no output methods'



# ***********************************
# reading .cfg file
# ************************************

    def _read(self,filename,filepath):
        if os.path.exists(filepath):
            self.config = ConfigParser.ConfigParser()
            self.config.read(filepath)
            return 'normal',filename+' read'
        else:
            return 'error',filename+' not found at: '+filepath




if __name__ == '__main__':
    from Tkinter import *

    def key_callback(symbol,source):
        print 'callback',symbol,source,'\n'
        if symbol=='pp-stop':
            idd.terminate()
            exit()
        pass

    root = Tk()

    w = Label(root, text="pp_kbddriver_plus.py test harness")
    w.pack()

    idd=pp_kbddriver_plus()
    
    reason,message=idd.init('pp_kbddriver_plus.cfg','/home/pi/pipresents/pp_io_config/keys_plus.cfg',root,key_callback)
    print reason,message
    if reason != 'error':
        idd.start()
        root.mainloop()
