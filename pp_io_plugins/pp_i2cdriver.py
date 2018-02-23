#!/usr/bin/env python
"""
Some of the code here is modified from:
   Pimoroni i2c scrollphat advanced-scrolling example
   Pimoroni i2c fourletterphat countdown example

This module is an example of using I2c. It supports the 
   Pimoroni Scrollhd PHat
   Pimoroni Four Letter Phat
   Pimoroni Automation PHat (ADC only). Use GPIOdriver for other inputs and outputs
   Adafruit MCP4725 DAC Breakout

The Pimoroni ScrollHD and Four Letter devices use the Pimoroni Libraries.
The best way to install these is to use the Pimoroni Dashboard
      https://github.com/pimoroni/automation-hat

The ADC and DAC devices use a simple driver in the file /pipresents/pp_i2cdevices.pi file calling smbus directly
The drivers rely heavily on the Adafruit drivers.

To use pp_i2cdriver.py I2C must be enabled in Preferences>Raspberry Pi Configuration
   

"""
import copy
import os
import ConfigParser
import smbus
import threading
import time
from pp_i2cdevices import MCP4725DAC, ADS1015

class StoppableThread (threading.Thread):
    """Basic Stoppable Thread Wrapper
    Adds event for stopping the execution
    loop and exiting cleanly."""
    
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        # print 'init stoppable thread'
        self.stop_event = threading.Event()
        self.daemon = True

    def start(self):
        if not self.isAlive():
            self.stop_event.clear()
            threading.Thread.start(self)

    def stop(self):
        if self.is_alive():
            self.stop_event.set()
            self.join()


      

class pp_i2cdriver(object):

    # control list items
    NAME=0                # command match - symbolic name for input and output 0 name of device
    TYPE=1                # command match - match parameter type
    METHOD = 2            # what to do when matched
    BRIGHTNESS = 3        # values different between devices
    ROTATE_180 = 4        # yes/no for upside down scroll displays
    DELAY=5               # for scroll float,  seconds
    REPEAT=6              # yes/no repeat scroll until stopped or single scroll
    LEFT_OFFSET=7         # integer, blanks 2D scroll at the beginning of a line
    DIRECTION = 8         # in or out

    TEMPLATE=['','','',1.0,'no','0.06','',17,'']

    # CLASS VARIABLES  (pp_i2cdriver.)
    driver_active=False

    # output command parameters - for accrss by threads
    lines = []       # lines of text for 2D scroll
    analog_input = 0

    # some configuration data for access by threads
    method = ''
    brightness = 0
    rotate_180 = 'no'
    repeat= 'no'
    delay = 0.06
    left_offset = 17
    analog_input = ''

    # devices connected
    fourletter_connected = False
    scrollhd_connected = False
    automationhat_connected = False
    MCP4725DAC_connected = False

    # ADC values
    inputs = dict()


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

        pp_i2cdriver.driver_active = False

        # read pp_i2cdriver.cfg file.
        reason,message=self._read(self.filename,self.filepath)
        if reason =='error':
            return 'error',message
        
        if self.config.has_section('DRIVER') is False:
            return 'error','No DRIVER section in '+self.filepath
        
        # read information from DRIVER section
        pp_i2cdriver.title=self.config.get('DRIVER','title')
  
        pp_i2cdriver.out_names=[]
        for section in self.config.sections():
            if section == 'DRIVER':
                continue
            entry=copy.deepcopy(pp_i2cdriver.TEMPLATE)
            entry[pp_i2cdriver.DIRECTION]=self.config.get(section,'direction')
            entry[pp_i2cdriver.NAME]=self.config.get(section,'name')
            entry[pp_i2cdriver.TYPE]=self.config.get(section,'type')
            entry[pp_i2cdriver.METHOD]=self.config.get(section,'method')

            if entry[pp_i2cdriver.DIRECTION] == 'out':
                if entry[pp_i2cdriver.NAME] == 'scrollhd':
                    entry[pp_i2cdriver.ROTATE_180]=self.config.get(section,'rotate-180')
                    entry[pp_i2cdriver.BRIGHTNESS]=float(self.config.get(section,'brightness'))/100
                     
                    if entry[pp_i2cdriver.METHOD]=='scroll':
                        entry[pp_i2cdriver.DELAY]=float(self.config.get(section,'delay'))/1000
                        entry[pp_i2cdriver.REPEAT]=self.config.get(section,'repeat')
                        entry[pp_i2cdriver.LEFT_OFFSET]=int(self.config.get(section,'left-offset'))
                        
                    elif entry[pp_i2cdriver.METHOD] in ('static','blank'):
                        pass

                    else:
                        return 'error',pp_i2cdriver.title + ' unknown method for '+ entry[pp_i2cdriver.NAME] +' - ' +entry[pp_i2cdriver.METHOD]

                    pp_i2cdriver.out_names.append(copy.deepcopy(entry))


                elif entry[pp_i2cdriver.NAME] == 'fourletter':
                    if entry[pp_i2cdriver.METHOD]in ('string','blank','num-string','countdown','mirror-percentage','mirror-volts'):
                        entry[pp_i2cdriver.BRIGHTNESS]=int(self.config.get(section,'brightness'))
                        pp_i2cdriver.out_names.append(copy.deepcopy(entry))


                elif entry[pp_i2cdriver.NAME] == 'dac':
                    if entry[pp_i2cdriver.METHOD] in ('set','mirror','fade'):
                        pp_i2cdriver.out_names.append(copy.deepcopy(entry))
                    else:
                        return 'error',pp_i2cdriver.title + ' unknown method for '+ entry[pp_i2cdriver.NAME] +' - ' +entry[pp_i2cdriver.METHOD]
                else:
                    return 'error',pp_i2cdriver.title + ' unknown name ' + entry[pp_i2cdriver.NAME]


            elif entry[pp_i2cdriver.DIRECTION] == 'in':
                pass

            else:
                return 'error',pp_i2cdriver.title + ' unknown direction in ' + entry[pp_i2cdriver.NAME]

        # print pp_i2cdriver.out_names
        
        self.tick_timer=None
        #threads for sequencing the dynamic display methods
        self.scrollhd_thread = None
        self.fourletter_thread=None
        self.DAC_thread = None
        
        # which devices are connected
        self.i2c_devices_present()

        #inititlaise dictionary to hold input values
        pp_i2cdriver.inputs['analog1-percentage'] = 0
        pp_i2cdriver.inputs['analog2-percentage'] = 0
        pp_i2cdriver.inputs['analog3-percentage'] = 0
        pp_i2cdriver.inputs['analog1-volts'] = 0
        pp_i2cdriver.inputs['analog2-volts'] = 0
        pp_i2cdriver.inputs['analog3-volts'] = 0
        
        # all ok so indicate the driver is active
        pp_i2cdriver.driver_active=True

        # init must return two arguments
        return 'normal',pp_i2cdriver.title + ' active'


    # start the input loop
    def start(self):
            pp_i2cdriver.ADC1=ADS1015(pp_i2cdriver.bus)
            pp_i2cdriver.ADC2=ADS1015(pp_i2cdriver.bus)
            pp_i2cdriver.ADC3=ADS1015(pp_i2cdriver.bus)
            self.tick_timer=self.widget.after(1,self.loop)

    def loop(self):
        if  pp_i2cdriver.driver_active==True and pp_i2cdriver.automation_connected is True:
            # loop around reading the three analog inputs
            # percent is the percentage of 3.3 volts. For some reason it goes over 100
            percent1,volts1= pp_i2cdriver.ADC1.read_adc(pp_i2cdriver.bus,0)
            pp_i2cdriver.inputs['analog1-percentage']= percent1
            pp_i2cdriver.inputs['analog1-volts']= volts1
            
            percent2,volts2= pp_i2cdriver.ADC2.read_adc(pp_i2cdriver.bus,1)
            pp_i2cdriver.inputs['analog2-percentage'] = percent2
            pp_i2cdriver.inputs['analog2-volts']= volts2
            
            percent3,volts3= pp_i2cdriver.ADC3.read_adc(pp_i2cdriver.bus,2)
            pp_i2cdriver.inputs['analog3-percentage'] = percent3
            pp_i2cdriver.inputs['analog3-volts']= volts3
            
        self.tick_timer=self.widget.after(100,self.loop)

    # allow track plugins (or anyting else) to access analog input values
    def get_input(self,channel):
        if channel in pp_i2cdriver.inputs:
            return True, pp_i2cdriver.inputs[channel]
        else:
            return False, None

    # callable by track plugins to print analog input values
    def print_inputs(self):
        print 'Automation phat analog inputs, percentage of 3.3 volts:',pp_i2cdriver.inputs['analog1-percentage'], pp_i2cdriver.inputs['analog2-percentage'], pp_i2cdriver.inputs['analog3-percentage']
        print 'Automation phat analog inputs, voltage:',round(pp_i2cdriver.inputs['analog1-volts'],2), round(pp_i2cdriver.inputs['analog2-volts'],2), round(pp_i2cdriver.inputs['analog3-volts'],2)
       
    # allow querying of driver state
    def is_active(self):
        return pp_i2cdriver.driver_active


  # called by main program only. Called when PP is closed down               
    def terminate(self):
        if self.tick_timer is not None:
            self.widget.after_cancel(self.tick_timer)
            self.tick_timer=None
        # stop the thread for sequencing
        self.stop_scrollhd()
        # and clear the device
        if pp_i2cdriver.scrollhd_connected is True:
            pp_i2cdriver.scrollphathd.clear()
            pp_i2cdriver.scrollphathd.show()
            
        self.stop_fourletter()
        if pp_i2cdriver.fourletter_connected is True:
            pp_i2cdriver.fourletterphat.clear()
            pp_i2cdriver.fourletterphat.show()
            
        pp_i2cdriver.driver_active = False


    def i2c_devices_present(self):
        pp_i2cdriver.bus = smbus.SMBus(1) # 1 indicates /dev/i2c-1
        bus = pp_i2cdriver.bus
        pp_i2cdriver.fourletter_connected = self.i2c_device_present(0x70,bus)
        if pp_i2cdriver.fourletter_connected is True:
            import fourletterphat
            pp_i2cdriver.fourletterphat = fourletterphat          
        pp_i2cdriver.scrollhd_connected = self.i2c_device_present(0x74,bus)
        if pp_i2cdriver.scrollhd_connected  is True:
            import scrollphathd
            pp_i2cdriver.scrollphathd = scrollphathd
            from scrollphathd.fonts import font5x7
            pp_i2cdriver.font5x7 = font5x7
        pp_i2cdriver.automation_connected = self.i2c_device_present(0x48,bus)
        pp_i2cdriver.DAC_connected = self.i2c_device_present(0x62,bus)




    def i2c_device_present(self,address,bus):
        try:
            bus.read_byte(address)
            return True
        except: 
            return False

# ************************************************
# output interface method
# this can be called from many objects so needs to operate on class variables
# if it is supplying data to the main program
# ************************************************                            
    # execute an output event

    def handle_output_event(self,name,param_type,param_values,req_time):

        # print 'comand is',name,param_type, param_values

        # match command against all out entries in config data
        self.result=''
        for entry in pp_i2cdriver.out_names:
            # does the symbolic name and type match value in the configuration 
            if name == entry[pp_i2cdriver.NAME] and param_type == entry[pp_i2cdriver.TYPE]:
                status,message=self.dispatch_command(name,param_type,param_values,entry)
                if status == 'error':
                    return status,message
        return 'normal',self.result

    

    def dispatch_command(self,name,param_type,param_values,entry):
        # print 'dispatch',name,param_type,param_values
        if name == 'scrollhd':
            if pp_i2cdriver.scrollhd_connected is True:
                status,message=self.do_scrollhd(name,param_type,param_values,entry)
                return status,message
            else:
                return 'error','scrollhd phat not present'
            
        elif name == 'fourletter':
            if pp_i2cdriver.fourletter_connected is True:
                status,message=self.do_fourletter(name,param_type,param_values,entry)
                return status,message
            else:
                return 'error','four letter phat not present'
            
        elif name == 'dac':
            if pp_i2cdriver.DAC_connected is True:
                status,message=self.do_dac(name,param_type,param_values,entry)
                return status,message
            else:
                return 'error','DAC not present'
        else:
            return 'normal','no match for name '+ name

    def do_dac(self,name,param_type,param_values,entry):
        # stop any previous threads
        self.stop_dac()
        pp_i2cdriver.method=entry[pp_i2cdriver.METHOD]
        pp_i2cdriver.dac=MCP4725DAC()
        # choose what to do depending on method
        if entry[pp_i2cdriver.METHOD] == 'set':
            pp_i2cdriver.dac.write_dac_fast(pp_i2cdriver.bus,0x62,int(int(param_values[0])*40.96))
            self.result += pp_i2cdriver.title + ' '+entry[pp_i2cdriver.NAME]+'/'+entry[pp_i2cdriver.TYPE] + ': started ' +entry[pp_i2cdriver.METHOD]
            return 'normal','dac set'
        
        elif entry[pp_i2cdriver.METHOD] == 'mirror':
            pp_i2cdriver.analog_input= param_values[0]
            self.result += pp_i2cdriver.title + ' '+entry[pp_i2cdriver.NAME]+'/'+entry[pp_i2cdriver.TYPE] + ': started ' +entry[pp_i2cdriver.METHOD]
            # create a thread to run the display loop. Thread because it has sleeps
            self.DAC_thread = DACThread()
            # and start the display
            self.DAC_thread.start()
            return 'normal','mirror thread started'
        
        elif entry[pp_i2cdriver.METHOD] == 'fade':
            self.result += pp_i2cdriver.title + ' '+entry[pp_i2cdriver.NAME]+'/'+entry[pp_i2cdriver.TYPE] + ': started ' +entry[pp_i2cdriver.METHOD]
            pp_i2cdriver.dac_fade_start = float(param_values[0])
            pp_i2cdriver.dac_fade_end = float(param_values[1])
            pp_i2cdriver.dac_fade_ticks = 10 *float(param_values[2])    # tick interval is 100mS.
            pp_i2cdriver.dac_fade_delta = (pp_i2cdriver.dac_fade_end - pp_i2cdriver.dac_fade_start)/pp_i2cdriver.dac_fade_ticks

            # create a thread to run the display loop. Thread because it has sleeps
            self.DAC_thread = DACThread()
            # and start the display
            self.DAC_thread.start()
            return 'normal','mirror thread started'
        else:
            return 'error','no match for method ' + entry[pp_i2cdriver.METHOD]

            
    def stop_dac(self):
        # stop any thread if it is running
        if self.DAC_thread is not None and self.DAC_thread.is_alive():
            # print 'stop previous',self.DAC_thread.is_alive()
            self.DAC_thread.stop()
            self.DAC_thread=None
            # print'dead'        


    def do_scrollhd(self,name,param_type,param_values,entry):
        # stop any previous threads
        self.stop_scrollhd()
        pp_i2cdriver.lines=param_values     
        pp_i2cdriver.repeat=entry[pp_i2cdriver.REPEAT]
        
        if entry[pp_i2cdriver.ROTATE_180]== 'yes':
            pp_i2cdriver.scrollphathd.rotate(180)
        else:
            pp_i2cdriver.scrollphathd.rotate(0)
            
        pp_i2cdriver.scrollphathd.set_brightness(entry[pp_i2cdriver.BRIGHTNESS])
        
        # choose what to do depending on method
        if entry[pp_i2cdriver.METHOD] == 'scroll':
            pp_i2cdriver.delay=entry[pp_i2cdriver.DELAY]           
            pp_i2cdriver.repeat=entry[pp_i2cdriver.REPEAT]
            pp_i2cdriver.left_offset=entry[pp_i2cdriver.LEFT_OFFSET]
            self.result += pp_i2cdriver.title + ' '+entry[pp_i2cdriver.NAME]+'/'+entry[pp_i2cdriver.TYPE] + ': started ' +entry[pp_i2cdriver.METHOD]

            # create a thread to run the display loop. Thread because it has sleeps
            self.scrollhd_thread = ScrollhdThread()
            # and start the display
            self.scrollhd_thread.start()
            return 'normal','display started'
        
        elif entry[pp_i2cdriver.METHOD] == 'static':
            pp_i2cdriver.scrollphathd.clear()
            pp_i2cdriver.scrollphathd.write_string(param_values[0], x=0, y=0, font=pp_i2cdriver.font5x7)
            pp_i2cdriver.scrollphathd.scroll_to(0, 0)
            self.result += pp_i2cdriver.title + ' '+entry[pp_i2cdriver.NAME]+'/'+entry[pp_i2cdriver.TYPE] + ': started ' +entry[pp_i2cdriver.METHOD]
            pp_i2cdriver.scrollphathd.show()
            return 'normal','display started'
        
        elif entry[pp_i2cdriver.METHOD] == 'blank':
            pp_i2cdriver.scrollphathd.clear()
            pp_i2cdriver.scrollphathd.write_string('', x=0, y=0, font=pp_i2cdriver.font5x7)
            pp_i2cdriver.scrollphathd.scroll_to(0, 0)
            self.result += pp_i2cdriver.title + ' '+entry[pp_i2cdriver.NAME]+'/'+entry[pp_i2cdriver.TYPE] + ': started ' +entry[pp_i2cdriver.METHOD]
            pp_i2cdriver.scrollphathd.show()
            return 'normal','scrollhd display started'
        else:
            return 'error','no match for method ' + entry[pp_i2cdriver.METHOD]


    def stop_scrollhd(self):
        # stop any scroll if it is running
        if self.scrollhd_thread is not None and self.scrollhd_thread.is_alive():
            # print 'stop previous',self.scrollhd_thread.is_alive()
            self.scrollhd_thread.stop()
            self.scrollhd_thread=None
            # print'dead'


    def do_fourletter(self,name,param_type,param_values,entry):
        # stop any previous fourletter thread
        self.stop_fourletter()
        # print name,param_type,param_values
        pp_i2cdriver.method=entry[pp_i2cdriver.METHOD]
        pp_i2cdriver.fourletterphat.set_brightness(entry[pp_i2cdriver.BRIGHTNESS])
        
        # choose what to do depending on method
        if entry[pp_i2cdriver.METHOD] == 'countdown':
            pp_i2cdriver.initial_count=int(param_values[0])       
            # create a thread to run the display loop. Thread because it has sleeps
            self.result += pp_i2cdriver.title + ' '+entry[pp_i2cdriver.NAME]+'/'+entry[pp_i2cdriver.TYPE] + ': started ' +entry[pp_i2cdriver.METHOD]
            self.fourletter_thread = FourLetterThread()
            # and start the display
            self.fourletter_thread.start()
            return 'normal','display started'

        elif entry[pp_i2cdriver.METHOD] in ('mirror-percentage','mirror-volts'):
            self.result += pp_i2cdriver.title + ' '+entry[pp_i2cdriver.NAME]+'/'+entry[pp_i2cdriver.TYPE] + ': started ' +entry[pp_i2cdriver.METHOD]
            # create a thread to run the display loop. Thread because it has sleeps
            pp_i2cdriver.analog_input = param_values[0]
            self.fourletter_thread = FourLetterThread()
            # and start the display
            self.fourletter_thread.start()
            return 'normal','display started'
        
        elif entry[pp_i2cdriver.METHOD] == 'string':
            # print 'for letter string',param_values[0]
            pp_i2cdriver.fourletterphat.clear()
            pp_i2cdriver.fourletterphat.print_str(param_values[0])
            self.result += pp_i2cdriver.title + ' '+entry[pp_i2cdriver.NAME]+'/'+entry[pp_i2cdriver.TYPE] + ': started ' +entry[pp_i2cdriver.METHOD]
            pp_i2cdriver.fourletterphat.show()
            return 'normal','display started'

        elif entry[pp_i2cdriver.METHOD] == 'num-string':
            pp_i2cdriver.fourletterphat.clear()
            pp_i2cdriver.fourletterphat.print_number_str(param_values[0])
            self.result += pp_i2cdriver.title + ' '+entry[pp_i2cdriver.NAME]+'/'+entry[pp_i2cdriver.TYPE] + ': started ' +entry[pp_i2cdriver.METHOD]
            pp_i2cdriver.fourletterphat.show()
            return 'normal','display started'
        
        elif entry[pp_i2cdriver.METHOD] == 'blank':
            pp_i2cdriver.fourletterphat.clear()
            self.result += pp_i2cdriver.title + ' '+entry[pp_i2cdriver.NAME]+'/'+entry[pp_i2cdriver.TYPE] + ': started ' +entry[pp_i2cdriver.METHOD]
            pp_i2cdriver.fourletterphat.show()
            return 'normal','four letter display started'
        else:
            return 'error','no match for method ' + entry[pp_i2cdriver.METHOD]


    def stop_fourletter(self):
        # stop any sequence if it is running
        if self.fourletter_thread is not None and self.fourletter_thread.is_alive():
            self.fourletter_thread.stop()
            self.fourletter_thread=None
            # print'dead'       

                    
# ***********************************
# reading .cfg file
# ************************************

    def _read(self,filename,filepath):
        # try inside profile
        if os.path.exists(filepath):
            self.config = ConfigParser.ConfigParser()
            self.config.read(filepath)
            # self.mon.log(self,filename + " read from "+ filepath)
            return 'normal',filename+' read'
        else:
            return 'error',filename + ' not found at: '+filepath

# ****************************************

class DACThread(StoppableThread):

    def __init__(self, *args, **kwargs):
        StoppableThread.__init__(self, *args, **kwargs)
        # print 'init fourletter thread'
        
    def run(self):
        if pp_i2cdriver.method== 'mirror':
            while True:
                if pp_i2cdriver.analog_input=='analog1':
                    percent=pp_i2cdriver.inputs['analog1-percentage']
                elif pp_i2cdriver.analog_input=='analog2':
                    percent=pp_i2cdriver.inputs['analog2-percentage']
                elif pp_i2cdriver.analog_input=='analog3':
                    percent=pp_i2cdriver.inputs['analog3-percentage']
                else:
                    percent=0
                DAC_value=percent*4096/100
                # print DAC_value,percent  
                pp_i2cdriver.dac.write_dac_fast(pp_i2cdriver.bus,0x62,int(DAC_value))
                
                if self.stop_event.isSet():
                    return
                time.sleep(0.1)
           
        else:
            # fade
            level= pp_i2cdriver.dac_fade_start
            if pp_i2cdriver.dac_fade_delta >=0:
                while level <= pp_i2cdriver.dac_fade_end:
                    pp_i2cdriver.dac.write_dac_fast(pp_i2cdriver.bus,0x62,int(level*40.96))
                    # print level
                    level+=pp_i2cdriver.dac_fade_delta
                    if self.stop_event.isSet():
                        return
                    time.sleep(0.1)
            else:
                while level >= pp_i2cdriver.dac_fade_end:
                    pp_i2cdriver.dac.write_dac_fast(pp_i2cdriver.bus,0x62,int(level*40.96))
                    # print level
                    level+=pp_i2cdriver.dac_fade_delta
                    if self.stop_event.isSet():
                        return
                    time.sleep(0.1)



class FourLetterThread(StoppableThread):

    def __init__(self, *args, **kwargs):
        StoppableThread.__init__(self, *args, **kwargs)
        # print 'init fourletter thread'
        
    def run(self):
       
        pp_i2cdriver.fourletterphat.clear()
        if pp_i2cdriver.method== 'mirror-volts':
            while True:
                if pp_i2cdriver.analog_input=='analog1':
                    volts=pp_i2cdriver.inputs['analog1-volts']
                elif pp_i2cdriver.analog_input=='analog2':
                    volts=pp_i2cdriver.inputs['analog2-volts']
                elif pp_i2cdriver.analog_input=='analog3':
                    volts=pp_i2cdriver.inputs['analog3-volts']
                else:
                    volts=0
                pp_i2cdriver.fourletterphat.clear()
                pp_i2cdriver.fourletterphat.print_number_str(str(round(volts,2)))
                # pp_i2cdriver.fourletterphat.set_decimal(1, 1)
                pp_i2cdriver.fourletterphat.show()
                if self.stop_event.isSet():
                    return
                time.sleep(0.1)

        if pp_i2cdriver.method== 'mirror-percentage':
            while True:
                if pp_i2cdriver.analog_input=='analog1':
                    percent=pp_i2cdriver.inputs['analog1-percentage']
                elif pp_i2cdriver.analog_input=='analog2':
                    percent=pp_i2cdriver.inputs['analog2-percentage']
                elif pp_i2cdriver.analog_input=='analog3':
                    percent=pp_i2cdriver.inputs['analog3-percentage']
                else:
                    percent=0
                pp_i2cdriver.fourletterphat.clear()
                pp_i2cdriver.fourletterphat.print_number_str(str(percent))
                pp_i2cdriver.fourletterphat.show()
                if self.stop_event.isSet():
                    return
                time.sleep(0.1)
                    
        else:
            # countdown time
            self.ticks_to_go=pp_i2cdriver.initial_count*10-1
            while self.ticks_to_go >0:
                remaining=int(self.ticks_to_go/10)
                curr_minutes = int(remaining / 60.0)
                curr_seconds = int(remaining % 60)
                padded_str = str("{0:02d}".format(curr_minutes)) + str("{0:02d}".format(curr_seconds))
                # print padded_str
                pp_i2cdriver.fourletterphat.clear()
                pp_i2cdriver.fourletterphat.print_str(padded_str)
                pp_i2cdriver.fourletterphat.set_decimal(1, 1)
                pp_i2cdriver.fourletterphat.show()
                self.ticks_to_go -= 1
                if self.stop_event.isSet():
                    return
                time.sleep(0.1)
            

class ScrollhdThread(StoppableThread):

    def __init__(self, *args, **kwargs):
        StoppableThread.__init__(self, *args, **kwargs)
        # print 'init scrollhd thread'
        
    def run(self):
        pp_i2cdriver.scrollphathd.clear()
        while True:
            # print pp_i2cdriver.brightness,pp_i2cdriver.rotate_180,pp_i2cdriver.left_offset,pp_i2cdriver.delay,"\n",pp_i2cdriver.lines

            # Determine how far apart each line should be spaced vertically
            self.line_height = pp_i2cdriver.scrollphathd.DISPLAY_HEIGHT + 2

            # Draw each line in lines to the Scroll pHAT HD buffer
            # scrollphathd.write_string returns the length of the written string in pixels
            # we can use this length to calculate the offset of the next line
            # and will also use it later for the scrolling effect.
            self.lengths = [0] * len(pp_i2cdriver.lines)

            for line, text in enumerate(pp_i2cdriver.lines):
                # print 'text',text,pp_i2cdriver.left_offset,self.line_height,line
                self.lengths[line] = pp_i2cdriver.scrollphathd.write_string(text, x=pp_i2cdriver.left_offset, y=self.line_height * line)
                pp_i2cdriver.left_offset += self.lengths[line]

            # This adds a little bit of horizontal/vertical padding into the buffer at
            # the very bottom right of the last line to keep things wrapping nicely.
            pp_i2cdriver.scrollphathd.set_pixel(pp_i2cdriver.left_offset - 1, (len(pp_i2cdriver.lines) * self.line_height) - 1, 0)


            # print pp_i2cdriver.lines, '\n',self.lengths,'\n',self.line_height
            
            # Reset the animation
            pp_i2cdriver.scrollphathd.scroll_to(0, 0)
            pp_i2cdriver.scrollphathd.show()

            for current_line, line_length in enumerate(self.lengths):
                # Delay a slightly longer time at the start of each line
                time.sleep(pp_i2cdriver.delay*10)
                if self.stop_event.isSet(): return

                # Scroll to the end of the current line
                for x in range(line_length):
                    # print ' move left',x, line_length
                    pp_i2cdriver.scrollphathd.scroll(1, 0)
                    time.sleep(pp_i2cdriver.delay)
                    if self.stop_event.isSet(): return
                    pp_i2cdriver.scrollphathd.show()
                    
                # progress to the next line by scrolling upwards
                if len(pp_i2cdriver.lines)>1:
                    for y in range(self.line_height):
                        # print 'move up',y, self.line_height
                        pp_i2cdriver.scrollphathd.scroll(0, 1)
                        pp_i2cdriver.scrollphathd.show()
                        time.sleep(pp_i2cdriver.delay)
                        if self.stop_event.isSet(): return
            if pp_i2cdriver.repeat == 'no':
                return


if __name__ == '__main__':
    from Tkinter import *

    def button_callback(symbol,source):
        print 'callback',symbol,source
        if symbol=='pp-stop':
            idd.terminate()
            exit()
        pass

    root = Tk()

    w = Label(root, text="pp_i2cdriver.py test harness")
    w.pack()
    
    bus=smbus.SMBus(1)
    dac=MCP4725DAC()
    dac.write_dac(bus,0x62,4095)
    time.sleep(2)
    dac.write_dac_fast(bus,0x62,0)
    time.sleep(2)
    dac.write_dac_fast(bus,0x62,4095)
    time.sleep(2)
    idd=pp_i2cdriver()
    
    reason,message=idd.init('i2c.cfg','/home/pi/pipresents/pp_resources/pp_templates/I2C.cfg',root,button_callback)
    # print reason,message
    if reason != 'error':
        idd.start()
        idd.handle_output_event('fourletter','string',["abcd"],1.24)
        time.sleep(5)
        idd.handle_output_event('fourletter','blank',["abcd"],1.24)
        time.sleep(2)
        idd.handle_output_event('fourletter','num-string',["24.15"],1.24)
        time.sleep(5)
        idd.handle_output_event('scrollhd','scroll',["scroll one long line which goes on and on and on and on......"],1.24)
        time.sleep(30)
        idd.handle_output_event('scrollhd','scroll',["two dimensional scroll","It's like reading a page","maybe not!!!!!"],1.24)
        time.sleep(20)
        idd.handle_output_event('scrollhd','static',["Stop"],1.24)
        time.sleep(2)
        idd.handle_output_event('scrollhd','blank',[],1.24)
        time.sleep(2)
        idd.handle_output_event('fourletter','string',["abcd"],1.24)
        time.sleep(2)
        idd.handle_output_event('fourletter','mirror','analog1',1.24)
        time.sleep(2)       
    # root.mainloop()
