# 2/11/2016 - removed requirement for sudo

import time
import copy
import os
import ConfigParser
from pp_utils import Monitor


class pp_gpiodriver(object):
    """
    pp_gpiodriver provides GPIO facilties for Pi presents
     - configures and binds GPIO pins from data in .cfg file 
     - reads and debounces inputs pins, provides callbacks on state changes which generate input events
    - changes the state of output pins as required by calling programs
    """
 
 
# constants for buttons

# cofiguration from gpio.cfg
    PIN=0                # pin on RPi board GPIO connector e.g. P1-11
    DIRECTION = 1 # IN/OUT/NONE (None is not used)
    NAME = 2      # symbolic name for output
    RISING_NAME=3             # symbolic name for rising edge callback
    FALLING_NAME=4      # symbolic name of falling edge callback
    ONE_NAME=5     # symbolic name for one state callback
    ZERO_NAME = 6   # symbolic name for zero state callback
    REPEAT =  7   # repeat interval for state callbacks (mS)
    THRESHOLD = 8       # threshold of debounce count for state change to be considered
    PULL = 9                  # pull up or down or none
    LINKED_NAME = 10     # output pin that follows the input
    LINKED_INVERT = 11   # invert the linked pin

    
# dynamic data
    COUNT=12          # variable - count of the number of times the input has been 0 (limited to threshold)
    PRESSED = 13     # variable - debounced state 
    LAST = 14      # varible - last state - used to detect edge
    REPEAT_COUNT = 15

    
    TEMPLATE = ['',   # pin
                '',              # direction
                '',              # name
                '','','','',       #input names
                0,             # repeat
                0,             # threshold
                '',             #pull
                -1,             #linked pin
                False,          # linked invert
                0,False,False,0]   #dynamics
    
# for A and B
#    PINLIST = ('P1-03','P1-05','P1-07','P1-08',
#               'P1-10','P1-11','P1-12','P1-13','P1-15','P1-16','P1-18','P1-19',
#               'P1-21','P1-22','P1-23','P1-24','P1-26')

# for A+ and B+ seems to work for A and B
    PINLIST = ('P1-03','P1-05','P1-07','P1-08',
               'P1-10','P1-11','P1-12','P1-13','P1-15','P1-16','P1-18','P1-19',
               'P1-21','P1-22','P1-23','P1-24','P1-26','P1-29',
                'P1-31','P1-32','P1-33','P1-35','P1-36','P1-37','P1-38','P1-40')


# CLASS VARIABLES  (pp_gpiodriver.)
    pins=[]
    driver_active=False
    title=''
    


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
        pp_gpiodriver.driver_active = False

        # read gpio.cfg file.
        reason,message=self._read(self.filename,self.filepath)
        if reason =='error':
            return 'error',message
        if self.config.has_section('DRIVER') is False:
            return 'error','No DRIVER section in '+self.filepath
        
        #read information from DRIVER section
        pp_gpiodriver.title=self.config.get('DRIVER','title')
        button_tick_text = self.config.get('DRIVER','tick-interval')
        if button_tick_text.isdigit():
            if int(button_tick_text)>0:
                self.button_tick=int(button_tick_text)  # in mS
            else:
                return 'error','tick-interval is not a positive integer'
        else:
            return 'error','tick-interval is not an integer'            

        import RPi.GPIO as GPIO
        self.GPIO = GPIO
        
        # construct the GPIO control list from the configuration
        for index, pin_def in enumerate(pp_gpiodriver.PINLIST):
            pin=copy.deepcopy(pp_gpiodriver.TEMPLATE)
            pin_bits = pin_def.split('-')
            pin_num=pin_bits[1:]
            pin[pp_gpiodriver.PIN]=int(pin_num[0])
            if self.config.has_section(pin_def) is False:
                self.mon.warn(self, "no pin definition for "+ pin_def)
                pin[pp_gpiodriver.DIRECTION]='None'            
            else:
                # unused pin
                if self.config.get(pin_def,'direction') == 'none':
                    pin[pp_gpiodriver.DIRECTION]='none'
                else:
                    pin[pp_gpiodriver.DIRECTION]=self.config.get(pin_def,'direction')
                    if pin[pp_gpiodriver.DIRECTION] == 'in':
                        # input pin
                        pin[pp_gpiodriver.RISING_NAME]=self.config.get(pin_def,'rising-name')
                        pin[pp_gpiodriver.FALLING_NAME]=self.config.get(pin_def,'falling-name')
                        pin[pp_gpiodriver.ONE_NAME]=self.config.get(pin_def,'one-name')
                        pin[pp_gpiodriver.ZERO_NAME]=self.config.get(pin_def,'zero-name')

                        if self.config.has_option(pin_def,'linked-output'):
                            # print self.config.get(pin_def,'linked-output')
                            pin[pp_gpiodriver.LINKED_NAME]=self.config.get(pin_def,'linked-output')
                            if  self.config.get(pin_def,'linked-invert') == 'yes':
                                pin[pp_gpiodriver.LINKED_INVERT]=True
                            else:
                                pin[pp_gpiodriver.LINKED_INVERT]=False
                        else:
                            pin[pp_gpiodriver.LINKED_NAME]= ''
                            pin[pp_gpiodriver.LINKED_INVERT]=False
                                               
                        if pin[pp_gpiodriver.FALLING_NAME] == 'pp-shutdown':
                            pp_gpiodriver.shutdown_index=index
                        if self.config.get(pin_def,'repeat') != '':
                            pin[pp_gpiodriver.REPEAT]=int(self.config.get(pin_def,'repeat'))
                        else:
                            pin[pp_gpiodriver.REPEAT]=-1
                        pin[pp_gpiodriver.THRESHOLD]=int(self.config.get(pin_def,'threshold'))
                        
                        if self.config.get(pin_def,'pull-up-down') == 'up':
                            pin[pp_gpiodriver.PULL]=GPIO.PUD_UP
                        elif self.config.get(pin_def,'pull-up-down') == 'down':
                            pin[pp_gpiodriver.PULL]=GPIO.PUD_DOWN
                        else:
                            pin[pp_gpiodriver.PULL]=GPIO.PUD_OFF
                    else:
                        # output pin
                        pin[pp_gpiodriver.NAME]=self.config.get(pin_def,'name')
            
            pp_gpiodriver.pins.append(copy.deepcopy(pin))

        # setup GPIO
        self.GPIO.setwarnings(True)        
        self.GPIO.setmode(self.GPIO.BOARD)


        # set up the GPIO inputs and outputs
        for index, pin in enumerate(pp_gpiodriver.pins):
            num = pin[pp_gpiodriver.PIN]
            if pin[pp_gpiodriver.DIRECTION] == 'in':
                self.GPIO.setup(num,self.GPIO.IN,pull_up_down=pin[pp_gpiodriver.PULL])
            elif  pin[pp_gpiodriver.DIRECTION] == 'out':
                self.GPIO.setup(num,self.GPIO.OUT)
                self.GPIO.setup(num,False)
        self._reset_input_state()
        
        pp_gpiodriver.driver_active=True

        # init timer
        self.button_tick_timer=None
        return 'normal',pp_gpiodriver.title + ' active'

    # called by main program only         
    def start(self):
        # loop to look at the buttons
        self._do_buttons()
        self.button_tick_timer=self.widget.after(self.button_tick,self.start)


    # called by main program only                
    def terminate(self):
        if pp_gpiodriver.driver_active is True:
            if self.button_tick_timer is not None:
                self.widget.after_cancel(self.button_tick_timer)
            self._reset_outputs()
            self.GPIO.cleanup()
            pp_gpiodriver.driver_active=False


# ************************************************
# gpio input functions
# called by main program only
# ************************************************
    
    def _reset_input_state(self):
        for pin in pp_gpiodriver.pins:
            pin[pp_gpiodriver.COUNT]=0
            pin[pp_gpiodriver.PRESSED]=False
            pin[pp_gpiodriver.LAST]=False
            pin[pp_gpiodriver.REPEAT_COUNT]=pin[pp_gpiodriver.REPEAT]


    def _do_buttons(self):
        for index, pin in enumerate(pp_gpiodriver.pins):
            if pin[pp_gpiodriver.DIRECTION] == 'in':

                # linked pin
                if pin[pp_gpiodriver.LINKED_NAME] != '':
                    link_pin=self._output_pin_of(pin[pp_gpiodriver.LINKED_NAME])
                    if link_pin!=-1:
                        self.GPIO.output(link_pin,self.GPIO.input(pin[pp_gpiodriver.PIN]) ^ pin[pp_gpiodriver.LINKED_INVERT])
                    
                # debounce
                if self.GPIO.input(pin[pp_gpiodriver.PIN]) == 0:
                    if pin[pp_gpiodriver.COUNT]<pin[pp_gpiodriver.THRESHOLD]:
                        pin[pp_gpiodriver.COUNT]+=1
                        if pin[pp_gpiodriver.COUNT] == pin[pp_gpiodriver.THRESHOLD]:
                            pin[pp_gpiodriver.PRESSED]=True
                else: # input us 1
                    if pin[pp_gpiodriver.COUNT]>0:
                        pin[pp_gpiodriver.COUNT]-=1
                        if pin[pp_gpiodriver.COUNT] == 0:
                            pin[pp_gpiodriver.PRESSED]=False
     
                # detect edges
                # falling edge
                if pin[pp_gpiodriver.PRESSED] is True and pin[pp_gpiodriver.LAST] is False:
                    pin[pp_gpiodriver.LAST]=pin[pp_gpiodriver.PRESSED]
                    pin[pp_gpiodriver.REPEAT_COUNT]=pin[pp_gpiodriver.REPEAT]
                    if  pin[pp_gpiodriver.FALLING_NAME] != '' and self.button_callback  is not  None:
                        self.button_callback(pin[pp_gpiodriver.FALLING_NAME],pp_gpiodriver.title)
               # rising edge
                if pin[pp_gpiodriver.PRESSED] is False and pin[pp_gpiodriver.LAST] is True:
                    pin[pp_gpiodriver.LAST]=pin[pp_gpiodriver.PRESSED]
                    pin[pp_gpiodriver.REPEAT_COUNT]=pin[pp_gpiodriver.REPEAT]
                    if  pin[pp_gpiodriver.RISING_NAME] != '' and self.button_callback  is not  None:
                        self.button_callback(pin[pp_gpiodriver.RISING_NAME],pp_gpiodriver.title)

                # do state callbacks
                if pin[pp_gpiodriver.REPEAT_COUNT] == 0:
                    if pin[pp_gpiodriver.ZERO_NAME] != '' and pin[pp_gpiodriver.PRESSED] is True and self.button_callback is not None:
                        self.button_callback(pin[pp_gpiodriver.ZERO_NAME],pp_gpiodriver.title)
                    if pin[pp_gpiodriver.ONE_NAME] != '' and pin[pp_gpiodriver.PRESSED] is False and self.button_callback is not None:
                        self.button_callback(pin[pp_gpiodriver.ONE_NAME],pp_gpiodriver.title)
                    pin[pp_gpiodriver.REPEAT_COUNT]=pin[pp_gpiodriver.REPEAT]
                else:
                    if pin[pp_gpiodriver.REPEAT] != -1:
                        pin[pp_gpiodriver.REPEAT_COUNT]-=1

    def get_input(self,channel):
            return False, None



# ************************************************
# gpio output interface methods
# these can be called from many classes so need to operate on class variables
# ************************************************                            

    # execute an output event

    def handle_output_event(self,name,param_type,param_values,req_time):
        # print 'GPIO handle',name,param_type,param_values
        # does the symbolic name match any output pin
        pin= self._output_pin_of(name)
        if pin  == -1:
            return 'normal',pp_gpiodriver.title + 'Symbolic name not recognised: ' + name
        
        #gpio only handles state parameters, ignore otherwise
        if param_type != 'state':
            return 'normal',pp_gpiodriver.title + ' does not handle: ' + param_type
        
        to_state=param_values[0]
        if to_state not in ('on','off'):
            return 'error',pp_gpiodriver.title + ', illegal parameter value for ' + param_type +': ' + to_state

        if to_state== 'on':
            state=True
        else:
            state=False
            
        # print 'pin P1-'+ str(pin)+ ' set  '+ str(state) + ' required: ' + str(req_time)+ ' actual: ' + str(long(time.time()))
        self.GPIO.output(pin,state)
        return 'normal',pp_gpiodriver.title + ' pin P1-'+ str(pin)+ ' set  '+ str(state) + ' required at: ' + str(req_time)+ ' sent at: ' + str(long(time.time()))


    def _reset_outputs(self):
        if pp_gpiodriver.driver_active is True:
            for index, pin in enumerate(pp_gpiodriver.pins):
                num = pin[pp_gpiodriver.PIN]
                if pin[pp_gpiodriver.DIRECTION] == 'out':
                    self.GPIO.output(num,False)


    def is_active(self):
        return pp_gpiodriver.driver_active

# ************************************************
# internal functions
# these can be called from many classes so need to operate on class variables
# ************************************************


    def _output_pin_of(self,name):
        for pin in pp_gpiodriver.pins:
            # print " in list" + pin[pp_gpiodriver.NAME] + str(pin[pp_gpiodriver.PIN] )
            if pin[pp_gpiodriver.NAME] == name and pin[pp_gpiodriver.DIRECTION] == 'out':
                # print " linked pin " + pin[pp_gpiodriver.NAME] + ' ' + str(pin[pp_gpiodriver.PIN] )
                return pin[pp_gpiodriver.PIN]
        return -1



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

    def button_callback(symbol,source):
        print 'callback',symbol,source
        if symbol=='pp-stop':
            idd.terminate()
            exit()
        pass

    root = Tk()

    w = Label(root, text="pp_inputdriver.py test harness")
    w.pack()

    idd=pp_gpiodriver()
    reason,message=idd.init('gpio.cfg','/home/pi/pipresents/pp_resources/pp_templates/gpio.cfg',root,button_callback)
    print reason,message
    idd.start()
    root.mainloop()

