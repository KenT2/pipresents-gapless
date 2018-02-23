# 2/11/2016 - removed requirement for sudo

import time
import copy
import os
import ConfigParser



class pp_exampledriver(object):



# CLASS VARIABLES  (pp_exampledriver.)
    driver_active=False
    message_name = ''
    title=''


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
        
        pp_exampledriver.driver_active = False

        # read exampledriver.cfg file.
        reason,message=self._read(self.filename,self.filepath)
        if reason =='error':
            return 'error',message
        if self.config.has_section('DRIVER') is False:
            return 'error','No DRIVER section in '+self.filepath
        
        #read information from DRIVER section
        pp_exampledriver.title=self.config.get('DRIVER','title')
        self.tick_name = self.config.get('DRIVER','tick-name')
        pp_exampledriver.message_name = self.config.get('DRIVER','message-name')

        self.tick_interval_text = self.config.get('DRIVER','tick-interval')
        
        if self.tick_interval_text.isdigit():
            if int(self.tick_interval_text)>0:
                self.tick_interval=int(self.tick_interval_text)  # in Seconds
            else:
                return 'error','tick-interval is not a positive integer'
        else:
            return 'error','tick-interval is not an integer'

        # all ok so indicate the driver is active
        pp_exampledriver.driver_active=True

        # init eveent timer
        self.tick_timer=None
        return 'normal',pp_exampledriver.title + ' active'

        

    def start(self):
        # generate the event at intervals if driver is active
        if pp_exampledriver.driver_active is True:
            #generate event params - symbolic name,source
            self.event_callback(self.tick_name,pp_exampledriver.title)
            # and set alarm to repeat
            # do not use a loop to wait as PP uses cooperative scheduling
            self.tick_timer=self.widget.after(self.tick_interval*1000,self.start)


    # allow track plugins (or anyting else) to access input values
    def get_input(self,channel):
            return False, None

    # called by main program only                
    def terminate(self):
        if pp_exampledriver.driver_active is True:
            if self.tick_timer is not None:
                self.widget.after_cancel(self.tick_timer)
            pp_exampledriver.driver_active = False



# ************************************************
# output interface method
# this can be called from many classes so need to operate on class variables
# ************************************************                            
    # execute an output event

    def handle_output_event(self,name,param_type,param_values,req_time):

        # does the symbolic name match the name in the configuration
        if name != pp_exampledriver.message_name:
            # just ignore this command
            return 'normal',pp_exampledriver.title + 'Symbolic name not recognised, ignore command: ' + name
        
        #example  only handles message parameter, ignore otherwise
        if param_type != 'message':
            return 'normal',pp_exampledriver.title + ' does not handle: ' + param_type
        
        # its an error if the list of paramters is empty (in this example)
        if param_values == []:
            return 'error',pp_exampledriver.title + ', no parameter values for type ' + param_type

        print 'Output from ' + pp_exampledriver.title + ':' + pp_exampledriver.message_name
        for value in param_values:
            print '     ',value
        
         
        # return a debugging string
        return 'normal',pp_exampledriver.title + ':'+pp_exampledriver.message_name+ ' output required at: ' + str(req_time)+ ' sent at: ' + str(long(time.time()))


    # allow querying of driver state
    def is_active(self):
        return pp_exampledriver.driver_active


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

            
# ***********************************
# test harness
# ************************************
if __name__ == '__main__':
    from Tkinter import *

    def main_event_callback(symbol,source):
        print '\nTick generated with symbolic name '+symbol+' from '+source
        # short circuit going into a PP show and out throught animate command
        status,log_message=idd.handle_output_event('send-message','message',['parameter 1','parameter 2'],str(long(time.time())))
        print 'debug: ',status,log_message



    root = Tk()

    w = Label(root, text="pp_exampledriver.py test harness")
    w.pack()

    idd=pp_exampledriver()
    reason,message=idd.init('exampledriver.cfg','/home/pi/pipresents/pp_resources/pp_templates/exampledriver.cfg',root,main_event_callback)
    print reason,message
    idd.start()
    # start tkinter's event loop
    root.mainloop()

