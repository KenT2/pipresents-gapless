import copy
import time
import string
import os
from datetime import datetime, timedelta
import json
from pp_utils import Monitor


class TimeOfDay(object):

    # CLASS VARIABLES

    # change this for another language
    DAYS_OF_WEEK=['monday','tuesday','wednesday','thursday','friday','saturday','sunday']

    """
        TimeOfDay.events is a dictionary the keys being show-refs.
        Each dictionary entry is a list of time_elements sorted by descending time
        Each time element is a list with the fields:
        0 - command
        1 - time, seconds since midnight

    """
    events={}  # list of times of day used to generate callbacks, earliest first

    last_scheduler_time=long(time.time())
    now_seconds=0
    root = None                 # for root.after
    
    # executed by main program and by each object using tod
    def __init__(self):
        self.mon=Monitor()


     # executed once from main program  only 
    def init(self,pp_dir,pp_home,pp_profile,root,callback):
       
        # instantiate arguments
        TimeOfDay.root=root
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile
        self.callback=callback

        # init variables
        # if testing is True then time now can be set by line 58 ish.
        self.testing=False
        self.tod_tick=500
        self.tick_timer=None
        TimeOfDay.last_poll_time=long(time.time())

        # read the schedule
        self.schedule=self.open_schedule()
        
        #create the initial events list
        if self.testing:
            now = datetime(day = 31, month =8, year=2014,hour=10, minute=0, second=0)
            self.sim_now=now
            print 'initial SIMULATED time',now.ctime()
        else:
            now = datetime.now()
            # print 'initial REAL time',now.ctime()
        midnight = now.replace(hour=0, minute=0, second=0)
        delta=(now-midnight)
        now_seconds= delta.seconds
        self.build_schedule_for_today(self.schedule,now)
        # self.print_todays_schedule()
        self.build_events_lists(now_seconds)
        # self.print_events_lists()
        # and start any show that should be running at start up time
        self.catchup=True


    # called by main program only         
    def poll(self):
        poll_time=long(time.time())
        # print 'poll',poll_time
        # is current time greater than last time the sceduler was run
        # run in a loop to catch up because root.after can get behind when images are being rendered etc.
        # poll time can be the same twice as poll is run at half second intervals.
        while TimeOfDay.last_scheduler_time<=poll_time:
            self.do_scheduler(poll_time - TimeOfDay.last_scheduler_time)
            TimeOfDay.last_scheduler_time +=1
        # and loop
        self.tick_timer=TimeOfDay.root.after(self.tod_tick,self.poll)


     # called by main program only           
    def terminate(self):
        if self.tick_timer is not None:
            TimeOfDay.root.after_cancel(self.tick_timer)
        self.clear_events_lists()


        
    # execute events at the appropriate time.
    # called by main program only   
    def do_scheduler(self,diff):
        if self.testing:
            self.sim_now += timedelta(seconds=1)
            now = self.sim_now
            print 'simulated time',now.ctime()
        else:
            now =datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # if its midnight then build the events lists for the new day
        delta=(now-midnight)
        now_seconds= delta.seconds-diff
        if delta.seconds == 0:
            # print 'midnight'
            self.build_schedule_for_today(self.schedule,now)
            self.print_todays_schedule()
            self.build_events_lists(now_seconds)
            self.print_events_lists()
        TimeOfDay.synced=True
        # print 'scheduler time', now_seconds, ' diff ', diff
        
      
        for show_ref in TimeOfDay.events:
            times = TimeOfDay.events[show_ref]
            if self.catchup is True:  
                # go through the list rembering show state until the first future event is found.
                # then if last command was to start the show send it
                show_running=False
                last_start_element=[]
                for time_element in reversed(times):
                    # print 'time from events', time_element[1]
                    if time_element[1]  >=  now_seconds:
                        break
                    if time_element[0] == 'open':
                        last_start_element=time_element
                        show_running=True
                    elif time_element[0]=='close':
                        show_running=False
                if show_running is True:
                    # print 'catch up', show_ref
                    self.do_event(show_ref,last_start_element,midnight)

            # print show_ref
            # now send a command if time matches
            for time_element in reversed(times):
                # print 'time from events', time_element[1]
                if time_element[1]  ==  now_seconds:
                    # print 'event fired'
                    self.do_event(show_ref,time_element,midnight)
        self.catchup=False

    # execute an event
    def do_event(self,show_ref,time_element,midnight):
        delta=datetime.now() - midnight
        self.mon.log (self,'Event : '  + time_element[0] +  ' ' +  show_ref + ' required ' + str(timedelta(seconds=time_element[1])) + ' late by ' + str(delta.seconds - time_element[1]))
        # print 'Event : ' + show_ref + ' ' + time_element[0] + ' required '+ str(timedelta(seconds=time_element[1])) + ' late by ' + str(delta.seconds - time_element[1])
        self.callback(time_element[0]  + ' ' + show_ref)


#
# ************************************************
# The methods below can be called from many classes so need to operate on class variables
# ************************************************

    # clear events list
    def clear_events_lists(self):
        self.mon.log(self,'clear time of day  events list ')
        # empty event list
        TimeOfDay.events={}


# ***********************************
# Preparing schedule and todays events
# ************************************

    def open_schedule(self):
        # look for the schedule.json file
        # try inside profile
        tryfile=self.pp_profile+os.sep+"schedule.json"
        # self.mon.log(self,"Trying schedule.json in profile at: "+ tryfile)
        if os.path.exists(tryfile):
            filename=tryfile
        else:
            # try inside pp_home
            # self.mon.log(self,"schedule.json not found at "+ tryfile+ " trying pp_home")
            tryfile=self.pp_home+os.sep+"schedule.json"
            if os.path.exists(tryfile):
                filename=tryfile
            else:
                # try inside pipresents
                # self.mon.log(self,"schedule.json not found at "+ tryfile + " trying inside pipresents")
                tryfile=self.pp_dir+os.sep+'pp_home'+os.sep+"schedule.json"
                if os.path.exists(tryfile):
                    filename=tryfile
                else:
                    self.mon.log(self,"schedule.json not found at "+ tryfile)
                    self.mon.err(self,"schedule.json not found  at "+ tryfile)
                    return False
        ifile  = open(filename, 'rb')
        schedule= json.load(ifile)
        ifile.close()
        self.mon.log(self,"schedule.json read from "+ filename)
        return schedule


    def build_schedule_for_today(self,schedule,now):
        this_day=now
        # print this_day.year, this_day.month, this_day.day, TimeOfDay.DAYS_OF_WEEK[ this_day.weekday()]
        """
        self.todays_schedule is a dictionary the keys being show-refs.
        Each dictionary entry is a list of time_elements
        Each time element is a list with the fields:
        0 - command
        1 - time hour:min[:sec]

        """
        self.todays_schedule={}
        # start the schedule with what is required everyday by default
        if 'everyday' in schedule:
            everyday=schedule['everyday']
            for day in everyday:
                #print day['day']
                for show in day['shows']:
                    self.todays_schedule[show['show-ref']]=copy.deepcopy(show['times'])
            # print '\nafter everyday'
            # print self.todays_schedule
            # self.print_todays_schedule()
  

        #override times for shows that have the required day of week
        if 'weekdays' in schedule:
            weekdays=schedule['weekdays']
            for day in  weekdays:
                #print day['day']
                if day['day'] == TimeOfDay.DAYS_OF_WEEK[ this_day.weekday()]:
                    # print 'weekday matched', day['day']
                    for show in day['shows']:
                        self.todays_schedule[show['show-ref']]=copy.deepcopy(show['times'])
            #print '\nafter weekday',todays_schedule                           
                       
        if 'monthdays' in schedule:
            monthdays=schedule['monthdays']
            for day in  monthdays:
                if int(day['day']) == this_day.day:
                    # print 'month matched', day['day']
                    for show in day['shows']:
                        self.todays_schedule[show['show-ref']]=copy.deepcopy(show['times'])
            #print '\nafter weekday',todays_schedule
            
        if 'specialdays' in schedule:
            specialdays= schedule['specialdays']
            for day in  specialdays:
                sdate=datetime.strptime(day['day'],'%Y-%m-%d')
                if sdate.year == this_day.year and sdate.month==this_day.month and sdate.day == this_day.day:
                    # print 'special matched', day['day']
                    for show in day['shows']:
                        self.todays_schedule[show['show-ref']]=copy.deepcopy(show['times'])



    def build_events_lists(self,now_seconds):
        # builds events dictionary from todays_schedule by
        # converting times in todays schedule from hour:min:sec to secs from midnight
        # and sorts them earliest last
        TimeOfDay.events={}
        for show_ref in self.todays_schedule:
            # print show_ref
            times = self.todays_schedule[show_ref]
            for time_element in times:
                time_element[1]=self.parse_event_time(time_element[1],now_seconds)
            sorted_times=sorted(times,key = lambda time_element: time_element[1],reverse=True)
            TimeOfDay.events[show_ref]=sorted_times
            # print times


    def parse_event_time(self,time_text,now_seconds):
        if time_text[0] == '+':
            seconds=now_seconds+int(time_text.lstrip('+'))
        else:
            fields=time_text.split(':')
            if len(fields)>2:
                secs=int(fields[2])
            else:
                secs=0
            seconds=int(fields[0])*3600+int(fields[1])*60+secs
        return seconds

# *********************
# print for debug
# *********************

    def print_schedule(self,frequencies):
    
        if 'everyday' in frequencies:
            self.print_frequency( frequencies,'everyday')
        if 'weekdays' in frequencies:
            self.print_frequency(frequencies,'weekdays')
        if 'monthdays' in frequencies:
            self.print_frequency(frequencies,'monthdays')
        if 'specialdays' in frequencies:
            self.print_frequency(frequencies,'specialdays')

    def print_frequency(self,frequencies,key):
        frequency=frequencies[key]
        print '\n',key
        for day in frequency:
            print '  ',day['day']
            shows = day['shows']
            for show in shows:
                print '      ',show['show-ref']
                for time_pair in show['times']:
                    print '               ' ,time_pair['start'],time_pair['exit']

                    
    def print_todays_schedule(self):
        print '\nschedule for today'
        for key in self.todays_schedule:
            print key
            for show in self.todays_schedule[key]:
                print show               

    def print_events_lists(self):
        print '\nevents list for today'
        for key in self.events:
            print key
            for show in self.events[key]:
                print show
                

    def save_schedule(self,filename):
        """ save a schedule """
        if filename=="":
            return False
        if os.name=='nt':
            filename = string.replace(filename,'/','\\')
        else:
            filename = string.replace(filename,'\\','/')
        ofile  = open(filename, "wb")
        json.dump(self.schedule,ofile,sort_keys= False,indent=1)
        ofile.close()
        return
            

