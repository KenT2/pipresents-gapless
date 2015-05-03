import time
import copy
import os
import ConfigParser
from pp_utils import Monitor


class GPIODriver(object):
    """
    GPIODriver provides GPIO facilties for Pi presents
     - configures and binds GPIO pins from data in gpio.cfg
     - reads and debounces inputs pins, provides callbacks on state changes which generate input events
    - changes the stae of output pins as required by calling programs
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
    
# dynamic data
    COUNT=10          # variable - count of the number of times the input has been 0 (limited to threshold)
    PRESSED = 11      # variable - debounced state 
    LAST = 12       # varible - last state - used to detect edge
    REPEAT_COUNT = 13

    
    TEMPLATE = ['',   # pin
                '',              # direction
                '',              # name
                '','','','',       #input names
                0,             # repeat
                0,             # threshold
                '',             #pull
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


# CLASS VARIABLES  (GPIODriver.)
    shutdown_index=0  #index of shutdown pin
    pins=[]
    options=None
    gpio_enabled=False


    # executed by main program and by each object using gpio
    def __init__(self):
        self.mon=Monitor()



     # executed once from main program   
    def init(self,pp_dir,pp_home,pp_profile,widget,button_tick,button_callback=None):
        
        # instantiate arguments
        self.widget=widget
        self.pp_dir=pp_dir
        self.pp_profile=pp_profile
        self.pp_home=pp_home
        self.button_tick=button_tick
        self.button_callback=button_callback

        GPIODriver.shutdown_index=0

        # read gpio.cfg file.
        reason,message=self.read(self.pp_dir,self.pp_home,self.pp_profile)
        if reason =='error':
            return 'error',message

        if os.geteuid() !=0:
            self.mon.err(self,'GPIO requires Pi Presents to be run as root\nhint: sudo pipresents.py .... ')
            return 'error','GPIO without sudo'

        import RPi.GPIO as GPIO
        self.GPIO = GPIO
        
        # construct the GPIO control list from the configuration
        for index, pin_def in enumerate(GPIODriver.PINLIST):
            pin=copy.deepcopy(GPIODriver.TEMPLATE)
            pin_bits = pin_def.split('-')
            pin_num=pin_bits[1:]
            pin[GPIODriver.PIN]=int(pin_num[0])
            if self.config.has_section(pin_def) is False:
                self.mon.warn(self, "no pin definition for "+ pin_def)
                pin[GPIODriver.DIRECTION]='None'            
            else:
                # unused pin
                if self.config.get(pin_def,'direction') == 'none':
                    pin[GPIODriver.DIRECTION]='none'
                else:
                    pin[GPIODriver.DIRECTION]=self.config.get(pin_def,'direction')
                    if pin[GPIODriver.DIRECTION] == 'in':
                        # input pin
                        pin[GPIODriver.RISING_NAME]=self.config.get(pin_def,'rising-name')
                        pin[GPIODriver.FALLING_NAME]=self.config.get(pin_def,'falling-name')
                        pin[GPIODriver.ONE_NAME]=self.config.get(pin_def,'one-name')
                        pin[GPIODriver.ZERO_NAME]=self.config.get(pin_def,'zero-name')
                        if pin[GPIODriver.FALLING_NAME] == 'pp-shutdown':
                            GPIODriver.shutdown_index=index
                        if self.config.get(pin_def,'repeat') != '':
                            pin[GPIODriver.REPEAT]=int(self.config.get(pin_def,'repeat'))
                        else:
                            pin[GPIODriver.REPEAT]=-1
                        pin[GPIODriver.THRESHOLD]=int(self.config.get(pin_def,'threshold'))
                        if self.config.get(pin_def,'pull-up-down') == 'up':
                            pin[GPIODriver.PULL]=GPIO.PUD_UP
                        elif self.config.get(pin_def,'pull-up-down') == 'down':
                            pin[GPIODriver.PULL]=GPIO.PUD_DOWN
                        else:
                            pin[GPIODriver.PULL]=GPIO.PUD_OFF
                    else:
                        # output pin
                        pin[GPIODriver.NAME]=self.config.get(pin_def,'name')
 
            # print pin            
            GPIODriver.pins.append(copy.deepcopy(pin))

        # setup GPIO
        self.GPIO.setwarnings(True)        
        self.GPIO.setmode(self.GPIO.BOARD)


        # set up the GPIO inputs and outputs
        for index, pin in enumerate(GPIODriver.pins):
            num = pin[GPIODriver.PIN]
            if pin[GPIODriver.DIRECTION] == 'in':
                self.GPIO.setup(num,self.GPIO.IN,pull_up_down=pin[GPIODriver.PULL])
            elif  pin[GPIODriver.DIRECTION] == 'out':
                self.GPIO.setup(num,self.GPIO.OUT)
                self.GPIO.setup(num,False)
        self.reset_input_state()
        
        GPIODriver.gpio_enabled=True

        # init timer
        self.button_tick_timer=None
        return 'normal','GPIO initialised'

    # called by main program only         
    def poll(self):
        # loop to look at the buttons
        self.do_buttons()
        self.button_tick_timer=self.widget.after(self.button_tick,self.poll)


    # called by main program only                
    def terminate(self):
        if GPIODriver.gpio_enabled is True:
            if self.button_tick_timer is not None:
                self.widget.after_cancel(self.button_tick_timer)
            self.reset_outputs()
            self.GPIO.cleanup()


# ************************************************
# gpio input functions
# called by main program only
# ************************************************
    
    def reset_input_state(self):
        for pin in GPIODriver.pins:
            pin[GPIODriver.COUNT]=0
            pin[GPIODriver.PRESSED]=False
            pin[GPIODriver.LAST]=False
            pin[GPIODriver.REPEAT_COUNT]=pin[GPIODriver.REPEAT]

    # index is of the pins array, provided by the callback ***** needs to be name
    def shutdown_pressed(self):
        if GPIODriver.shutdown_index != 0:
            return GPIODriver.pins[GPIODriver.shutdown_index][GPIODriver.PRESSED]
        else:
            return False

    def do_buttons(self):
        for index, pin in enumerate(GPIODriver.pins):
            if pin[GPIODriver.DIRECTION] == 'in':
                # debounce
                if self.GPIO.input(pin[GPIODriver.PIN]) == 0:
                    if pin[GPIODriver.COUNT]<pin[GPIODriver.THRESHOLD]:
                        pin[GPIODriver.COUNT]+=1
                        if pin[GPIODriver.COUNT] == pin[GPIODriver.THRESHOLD]:
                            pin[GPIODriver.PRESSED]=True
                else: # input us 1
                    if pin[GPIODriver.COUNT]>0:
                        pin[GPIODriver.COUNT]-=1
                        if pin[GPIODriver.COUNT] == 0:
                            pin[GPIODriver.PRESSED]=False
     
                # detect edges
                # falling edge
                if pin[GPIODriver.PRESSED] is True and pin[GPIODriver.LAST] is False:
                    pin[GPIODriver.LAST]=pin[GPIODriver.PRESSED]
                    pin[GPIODriver.REPEAT_COUNT]=pin[GPIODriver.REPEAT]
                    if  pin[GPIODriver.FALLING_NAME] != '' and self.button_callback  is not  None:
                        self.button_callback(pin[GPIODriver.FALLING_NAME],"GPIO")
               # rising edge
                if pin[GPIODriver.PRESSED] is False and pin[GPIODriver.LAST] is True:
                    pin[GPIODriver.LAST]=pin[GPIODriver.PRESSED]
                    pin[GPIODriver.REPEAT_COUNT]=pin[GPIODriver.REPEAT]
                    if  pin[GPIODriver.RISING_NAME] != '' and self.button_callback  is not  None:
                        self.button_callback(pin[GPIODriver.RISING_NAME],"GPIO")

                # do state callbacks
                if pin[GPIODriver.REPEAT_COUNT] == 0:
                    if pin[GPIODriver.ZERO_NAME] != '' and pin[GPIODriver.PRESSED] is True and self.button_callback is not None:
                        self.button_callback(pin[GPIODriver.ZERO_NAME],"GPIO")
                    if pin[GPIODriver.ONE_NAME] != '' and pin[GPIODriver.PRESSED] is False and self.button_callback is not None:
                        self.button_callback(pin[GPIODriver.ONE_NAME],"GPIO")
                    pin[GPIODriver.REPEAT_COUNT]=pin[GPIODriver.REPEAT]
                else:
                    if pin[GPIODriver.REPEAT] != -1:
                        pin[GPIODriver.REPEAT_COUNT]-=1

                    

    # execute an output event
    def handle_output_event(self,name,param_type,param_values,req_time):
        if GPIODriver.gpio_enabled is False:
            return 'normal','gpio not enabled'
        
        #gpio only handles state parameters
        if param_type != 'state':
            return 'error','gpio does not handle: ' + param_type
        to_state=param_values[0]
        if to_state== 'on':
            state=True
        else:
            state=False
            
        pin= self.output_pin_of(name)
        if pin  == -1:
            return 'error','Not an output for gpio: ' + name
        
        self.mon.log (self,'pin P1-'+ str(pin)+ ' set  '+ str(state) + ' required at: ' + str(req_time)+ ' sent at: ' + str(long(time.time())))
        # print 'pin P1-'+ str(pin)+ ' set  '+ str(state) + ' required: ' + str(req_time)+ ' actual: ' + str(long(time.time()))
        self.GPIO.output(pin,state)
        return 'normal','gpio handled OK'


# ************************************************
# gpio output interface methods
# these can be called from many classes so need to operate on class variables
# ************************************************

    def reset_outputs(self):
        if GPIODriver.gpio_enabled is True:
            self.mon.log(self,'reset outputs')
            for index, pin in enumerate(GPIODriver.pins):
                num = pin[GPIODriver.PIN]
                if pin[GPIODriver.DIRECTION] == 'out':
                    self.GPIO.output(num,False)



# ************************************************
# internal functions
# these can be called from many classes so need to operate on class variables
# ************************************************


    def output_pin_of(self,name):
        for pin in GPIODriver.pins:
            # print " in list" + pin[GPIODriver.NAME] + str(pin[GPIODriver.PIN] )
            if pin[GPIODriver.NAME] == name and pin[GPIODriver.DIRECTION] == 'out':
                return pin[GPIODriver.PIN]
        return -1



# ***********************************
# reading gpio.cfg
# ************************************

    def read(self,pp_dir,pp_home,pp_profile):
        # try inside profile
        filename=pp_profile+os.sep+'pp_io_config'+os.sep+'gpio.cfg'
        if os.path.exists(filename):
            self.config = ConfigParser.ConfigParser()
            self.config.read(filename)
            self.mon.log(self,"gpio.cfg read from "+ filename)
            return 'normal','gpio.cfg read'
        else:
            return 'normal','gpio.cfg not found in profile: '+filename


