import evdev
from select import select
import time
import copy
import os
import ConfigParser
from pp_utils import Monitor


class pp_inputdevicedriver(object):
    """
    pp_inputdevicedriver interfaces with the Linux generic input devices, for example USB keybads or remotes
    that is, ones that have a file in /dev/input
     - configures and binds key codes from specified .cfg file
     - reads input events from /dev/input and decodes them using evdev, provides callbacks on state changes which generate input events
    """
 
# constants for buttons

# cofiguration from gpio.cfg
    KEY_CODE=0                # pin on RPi board GPIO connector e.g. P1-11
    DIRECTION = 1 # IN/OUT/NONE (None is not used)
    RELEASED_NAME=2             # symbolic name for released callback
    PRESSED_NAME=3      # symbolic name of pressed callback
    UP_NAME=4     # symbolic name for up state callback
    DOWN_NAME = 5   # symbolic name for down state callback
    REPEAT =  6   # repeat interval for state callbacks (mS)


# dynamic data
    PRESSED = 7     # variable - debounced state 
    LAST = 8      # varible - last state - used to detect edge
    REPEAT_COUNT = 9

    
    TEMPLATE = ['',   # key code
                '',              # direction
                '','','','',       #input names
                0,             # repeat
                False,False,0]   #dynamics - pressed,last,repeat count
    




# CLASS VARIABLES  (pp_inputdevicedriver.)
    driver_active=False
    title=''
    KEYCODELIST=[]   # list of keycodes read from .cfg file
    key_codes=[] #dynamic list constructed from .cfg file and other dynamic variables
    device_refs=[]  # list of references to devices obtained by matching devide name against /dev/input


    # executed by main program and by each object using gpio
    def __init__(self):
        self.mon=Monitor()



     # executed once from main program   
    def init(self,filename,filepath,widget,button_callback=None):
        
        # instantiate arguments
        self.widget=widget
        self.filename=filename
        self.filepath=filepath
        self.button_callback=button_callback

        pp_inputdevicedriver.driver_active=False 

        # read .cfg file.
        reason,message=self._read(self.filename,self.filepath)
        if reason =='error':
            return 'error',message
        if self.config.has_section('DRIVER') is False:
            return 'error','no DRIVER section in '+ self.filename           

        #read information from DRIVER section
        pp_inputdevicedriver.title=self.config.get('DRIVER','title')
        self.button_tick=int(self.config.get('DRIVER','tick-interval'))  # in mS
        keycode_text=self.config.get('DRIVER','key-codes')
        pp_inputdevicedriver.KEYCODELIST = keycode_text.split(',')
        
        # construct the key_code control list from the configuration
        for index, key_code_def in enumerate(pp_inputdevicedriver.KEYCODELIST):
            if self.config.has_section(key_code_def) is False:
                self.mon.warn(self, "no key code definition for "+ key_code_def)
                continue          
            else:
                entry=copy.deepcopy(pp_inputdevicedriver.TEMPLATE)
                # unused pin
                entry[pp_inputdevicedriver.KEY_CODE]=key_code_def
                if self.config.get(key_code_def,'direction') == 'none':
                    entry[pp_inputdevicedriver.DIRECTION]='none'
                else:
                    entry[pp_inputdevicedriver.DIRECTION]=self.config.get(key_code_def,'direction')
                    if entry[pp_inputdevicedriver.DIRECTION] == 'in':
                        # input pin
                        entry[pp_inputdevicedriver.RELEASED_NAME]=self.config.get(key_code_def,'released-name')
                        entry[pp_inputdevicedriver.PRESSED_NAME]=self.config.get(key_code_def,'pressed-name')
                        entry[pp_inputdevicedriver.UP_NAME]=self.config.get(key_code_def,'up-name')
                        entry[pp_inputdevicedriver.DOWN_NAME]=self.config.get(key_code_def,'down-name')

                        if self.config.get(key_code_def,'repeat') != '':
                            entry[pp_inputdevicedriver.REPEAT]=int(self.config.get(key_code_def,'repeat'))
                        else:
                            entry[pp_inputdevicedriver.REPEAT]=-1
 
            # add entry to working list of key_codes  (list of lists [0] of sublist is key code       
            pp_inputdevicedriver.key_codes.append(copy.deepcopy(entry))

            
        # find the input device
        device_name=self.config.get('DRIVER','device-name')
        
        pp_inputdevicedriver.device_refs=self.find_devices(device_name)
        if pp_inputdevicedriver.device_refs==[]:
            return 'warn','Cannot find device: '+device_name + ' for '+ pp_inputdevicedriver.title

        pp_inputdevicedriver.driver_active=True

        # init timer
        self.button_tick_timer=None
        self.mon.log(self,pp_inputdevicedriver.title+' active')
        return 'normal',pp_inputdevicedriver.title+' active'



    def find_devices(self,name):
        devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
        matching=[]
        # print '\nMatching devices references: '
        for device in devices:
            if name in device.name:
                # print '     Ref:',device.fn, ' Name: ',device.name
                device_ref = evdev.InputDevice(device.fn)
                matching.append(device_ref)
        return matching


    # called by main program only         
    def start(self):
        # poll for events then update all the buttons once
        self.do_buttons()
        self.button_tick_timer=self.widget.after(self.button_tick,self.start)

    # allow track plugins (or anyting else) to access input values
    def get_input(self,channel):
            return False, None



    # called by main program only                
    def terminate(self):
        if pp_inputdevicedriver.driver_active is True:
            if self.button_tick_timer is not None:
                self.widget.after_cancel(self.button_tick_timer)
            pp_inputdevicedriver.driver_active = False


# ************************************************
# inputdevice functions
# called by main program only
# ************************************************
    
    def reset_input_state(self):
        for entry in pp_inputdevicedriver.key_codes:
            entry[pp_inputdevicedriver.PRESSED]=False
            entry[pp_inputdevicedriver.LAST]=False
            entry[pp_inputdevicedriver.REPEAT_COUNT]=entry[pp_inputdevicedriver.REPEAT]


    def is_active(self):
        return pp_inputdevicedriver.driver_active

    def do_buttons(self):

        # get and process new events from remote
        self.get_events(pp_inputdevicedriver.device_refs)

        # do the things that are done every tick
        for index, entry in enumerate(pp_inputdevicedriver.key_codes):
            if entry[pp_inputdevicedriver.DIRECTION] == 'in':

                # detect falling edge
                if entry[pp_inputdevicedriver.PRESSED] is True and entry[pp_inputdevicedriver.LAST] is False:
                    entry[pp_inputdevicedriver.LAST]=entry[pp_inputdevicedriver.PRESSED]
                    entry[pp_inputdevicedriver.REPEAT_COUNT]=entry[pp_inputdevicedriver.REPEAT]
                    if  entry[pp_inputdevicedriver.PRESSED_NAME] != '' and self.button_callback  is not  None:
                        self.button_callback(entry[pp_inputdevicedriver.PRESSED_NAME],pp_inputdevicedriver.title)
               # detect rising edge
                if entry[pp_inputdevicedriver.PRESSED] is False and entry[pp_inputdevicedriver.LAST] is True:
                    entry[pp_inputdevicedriver.LAST]=entry[pp_inputdevicedriver.PRESSED]
                    entry[pp_inputdevicedriver.REPEAT_COUNT]=entry[pp_inputdevicedriver.REPEAT]
                    if  entry[pp_inputdevicedriver.RELEASED_NAME] != '' and self.button_callback  is not  None:
                        self.button_callback(entry[pp_inputdevicedriver.RELEASED_NAME],pp_inputdevicedriver.title)

                # do state callbacks
                if entry[pp_inputdevicedriver.REPEAT_COUNT] == 0:
                    if entry[pp_inputdevicedriver.DOWN_NAME] != '' and entry[pp_inputdevicedriver.PRESSED] is True and self.button_callback is not None:
                        self.button_callback(entry[pp_inputdevicedriver.DOWN_NAME],pp_inputdevicedriver.title)
                    if entry[pp_inputdevicedriver.UP_NAME] != '' and entry[pp_inputdevicedriver.PRESSED] is False and self.button_callback is not None:
                        self.button_callback(entry[pp_inputdevicedriver.UP_NAME],pp_inputdevicedriver.title)
                    entry[pp_inputdevicedriver.REPEAT_COUNT]=entry[pp_inputdevicedriver.REPEAT]
                else:
                    if entry[pp_inputdevicedriver.REPEAT] != -1:
                        entry[pp_inputdevicedriver.REPEAT_COUNT]-=1


    def find_event_entry(self,event_code):
        for entry in pp_inputdevicedriver.key_codes:
            if entry[pp_inputdevicedriver.KEY_CODE]==event_code:
                # print entry
                return entry
        return None

        
    def get_events(self,matching):
        # some input devices have more than one logical input device so use select to poll all of the devices
        r,w,x = select(matching, [], [],0)
        if r==[] and w==[] and x==[]:
            # print 'no event'
            return
        self.process_events(r)

    def process_events(self,r):
        for re in r:
            for event in re.read():
                # print '\nEvent Rxd: ',event,'\n',evdev.categorize(event)
                if event.type == evdev.ecodes.EV_KEY:
                    # print 'Key Event Rxd: ',event
                    key_event = evdev.categorize(event)
                    self.process_event(key_event.keycode,key_event.keystate)



    def process_event(self,event_code,button_state):              
        event_entry=self.find_event_entry(event_code)
        if event_entry is None or event_entry[pp_inputdevicedriver.DIRECTION] != 'in':
            self.mon.warn(self,'input event key code not in list of key codes or direction not in')
        else:
            if button_state==1:
                # print event_code, 'Pressed'
                event_entry[pp_inputdevicedriver.PRESSED] = True 
            elif button_state==0:
                # print event_code, 'Released'
                event_entry[pp_inputdevicedriver.PRESSED] = False             
            else:
                # ignore other button states
                pass
                # print 'unknown state: ',button_state



# ***********************************
# output events
# ************************************

    # execute an output event
    def handle_output_event(self,name,param_type,param_values,req_time):
        return 'normal',pp_inputdevicedriver.title + ' does not accept outputs'
        
    def reset_outputs(self):
        return


# ***********************************
# reading .cfg file
# ************************************

    def _read(self,filename,filepath):
        # try inside profile
        if os.path.exists(filepath):
            self.config = ConfigParser.ConfigParser()
            self.config.read(filepath)
            self.mon.log(self,filename + " read from "+ filepath)
            return 'normal',filename+' read'
        else:
            return 'error',filename + ' not found at: '+filepath


if __name__ == '__main__':
    from Tkinter import *

    def button_callback(symbol,source):
        print 'callback',symbol,source
        if symbol=='pp-stop':
            idd.terminate()
            exit()
        pass

    root = Tk()

    w = Label(root, text="pp_inputdriver.py test harness")
    w.pack()

    idd=pp_inputdevicedriver()
    reason,message=idd.init('inputdevice.cfg','/home/pi/pipresents/pp_resources/pp_templates/inputdevice.cfg',root,button_callback)
    print reason,message
    idd.start()
    root.mainloop()
