import time
import copy
import datetime
from pp_utils import Monitor

class TimeOfDay(object):

    """
    add to a list of times with
    time, show id, callback  (should go to the calling show I think)

    cancel events with specific tag
    remove a specific event
    terminate tod

    keep time ticker one second tick time
    do callback when time is reached 24 hour clock, just rotates

    needs ticker to run from main program but events to be added/cancelled from a number of instances.

    Its the sequemcer in reverse.
    """
    
    # CLASS VARIABLES

   # fields of the times list
    TIME=0            # time at which trigger is to be generated - seconds from midnight
    TAG=1             # tag used to delete all matching events, usually a show reference.
    CALLBACK = 2      # instance of function to call when event is detected
    SOURCE = 3        # source text
    QUIET = 4        # whether the next show time should be displayed True,false

    TEMPLATE = [0,'',None,'',False]

    times=[]  # list of times of day used to generate callbacks, earliest first
    last_scheduler_time=long(time.time())
    now_seconds=0
    
    # executed by main program and by each object using tod
    def __init__(self):
        self.mon=Monitor()
        self.mon.on()


     # executed once from main program   
    def init(self,pp_dir,pp_home,widget,tod_tick):
       
        # instantiate arguments
        TimeOfDay.widget=widget
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.tod_tick=tod_tick
        # init variables
        self.tick_timer=None
        TimeOfDay.last_poll_time=long(time.time())
        midnight = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        now =datetime.datetime.now()
        TimeOfDay.delta=(now-midnight)
        TimeOfDay.now_seconds= TimeOfDay.delta.seconds


    # called by main program only         
    def poll(self):

        poll_time=long(time.time())
        # is current time greater than last time the sceduler was run
        # run in a loop to catch up because root.after can get behind when images are being rendered etc.
        while poll_time>TimeOfDay.last_scheduler_time:
            self.do_scheduler(poll_time - TimeOfDay.last_scheduler_time)
            TimeOfDay.last_scheduler_time +=1
        # and loop
        self.tick_timer=TimeOfDay.widget.after(self.tod_tick,self.poll)


     # called by main program only           
    def terminate(self):
        if self.tick_timer is not None:
            TimeOfDay.widget.after_cancel(self.tick_timer)
        self.clear_times_list(None)


        
    # execute events at the appropriate time.
    # called by main program only   
    def do_scheduler(self,diff):
        midnight = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        now =datetime.datetime.now()
        TimeOfDay.delta=(now-midnight)
        TimeOfDay.now_seconds= TimeOfDay.delta.seconds-diff
        TimeOfDay.synced=True
        # print 'scheduler time', TimeOfDay.now_seconds, ' diff ', diff
        for index, item in enumerate(TimeOfDay.times):
            # print item[TimeOfDay.TIME]
            if item[TimeOfDay.TIME]  ==  TimeOfDay.now_seconds:
                # print 'event fired'
                self.do_event(item)

    # execute an event
    def do_event(self,event):
        self.mon.log (self,'Event : ' + str(event[TimeOfDay.TIME])+' '+ str(event[TimeOfDay.TAG]) + ' at ' +datetime.datetime.now().ctime())
        # print 'Event : ' + str(event[TimeOfDay.TIME])+' '+ str(event[TimeOfDay.TAG]) + ' at ' +datetime.datetime.now().ctime()
        event[TimeOfDay.CALLBACK]()

    def next_event_time(self):
        # look for next event
        for index, item in enumerate(TimeOfDay.times):
            # print 'trying ',item[TimeOfDay.SOURCE]
            if TimeOfDay.now_seconds < item[TimeOfDay.TIME]:
                break
        else:
            return [TimeOfDay.times[0][TimeOfDay.SOURCE],'tomorrow',TimeOfDay.times[0][TimeOfDay.TAG],TimeOfDay.times[0][TimeOfDay.QUIET]]
        return [item[TimeOfDay.SOURCE],'',item[TimeOfDay.TAG],item[TimeOfDay.QUIET]]


#
# ************************************************
# The methods below can be called from many classes so need to operate on class variables
# ************************************************

    def add_times(self,text,tag,callback,quiet_text):
        if quiet_text == 'time-quiet':
            quiet=True
        else:
            quiet=False
        lines = text.split("\n")
        for line in lines:
            error_text=self.parse_tod_fields(line,tag,callback,quiet)
            if error_text  != '':
                return error_text
        # print TimeOfDay.times
        return ''
   
    def parse_tod_fields(self,line,tag,callback,quiet):
        fields = line.split()
        if len(fields) == 0:
            return ''
        for field in fields:
            self.parse_event_text(field,tag,callback,quiet)
        return ''

    def parse_event_text(self,time_text,tag,callback,quiet):
        if time_text[0] == '+':
            seconds=TimeOfDay.now_seconds+int(time_text.lstrip('+'))
        else:
            fields=time_text.split(':')
            if len(fields)>2:
                secs=int(fields[2])
            else:
                secs=0
                seconds=int(fields[0])*3600+int(fields[1])*60+secs
        self.add_event(seconds,tag,callback,time_text,quiet)
    

    def add_event(self,seconds,tag,callback,source,quiet):
        # seconds since midnight is integer
        # find the place in the list and insert
        # first item in the list is earliest, if two have the same time then last to be added is fired last.
        for index, item in enumerate(TimeOfDay.times):
            if seconds<item[TimeOfDay.TIME]:
                TimeOfDay.times.insert(index,copy.deepcopy(TimeOfDay.TEMPLATE))
                break
        else:
            TimeOfDay.times.append(copy.deepcopy(TimeOfDay.TEMPLATE))
            index=len(TimeOfDay.times)-1
            
        TimeOfDay.times[index][TimeOfDay.CALLBACK]=callback
        TimeOfDay.times[index][TimeOfDay.TIME]=seconds
        TimeOfDay.times[index][TimeOfDay.TAG]=tag
        TimeOfDay.times[index][TimeOfDay.SOURCE]=source
        TimeOfDay.times[index][TimeOfDay.QUIET]=quiet
        self.mon.log (self,'create time of day event ' + source + ' for show '+str(tag) + ' ' + str(quiet))
        # self.print_times()
        return TimeOfDay.times[index]


    def print_times(self):
        print
        for i in TimeOfDay.times:
            print i

    
    # remove an event
    def remove_event(self,event):
        for index, item in enumerate(PPIO.events):
            if event == item:
                del PPIO.events[index]
                return True
        return False


    # clear times list
    def clear_times_list(self,tag):
        self.mon.log(self,'clear time of day list ' + str(tag))
        # empty event list
        if tag is  None:
            TimeOfDay.events=[]
        else:
            self.remove_events(tag)

    # remove all the events with the same tag, usually a show reference
    def remove_events(self,tag):
        left=[]
        for item in TimeOfDay.times:
            if tag != item[TimeOfDay.TAG]:
                left.append(item)
        TimeOfDay.times= left
        # self.print_times()

