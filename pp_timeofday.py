import copy
import time
import string
import os
from datetime import datetime, timedelta,time
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
        self.testing=False
        self.tod_tick=500
        self.tick_timer=None
        TimeOfDay.now = datetime.now().replace(microsecond=0)
        # read the schedule
        self.schedule=self.open_schedule()

        #create the initial events list
        if 'simulate-time' in self.schedule and self.schedule['simulate-time']=='yes':
            year= int(self.schedule['sim-year'])
            month= int(self.schedule['sim-month'])
            day = int(self.schedule['sim-day'])
            hour= int(self.schedule['sim-hour'])
            minute= int(self.schedule['sim-minute'])
            second= int(self.schedule['sim-second'])
            TimeOfDay.now = datetime(day = day, month =month, year=year,hour=hour, minute=minute, second=second)
            self.testing=True
            print '\nInitial SIMULATED time',TimeOfDay.now.ctime()
        else:
            #get the current date/time only this once
            TimeOfDay.now = datetime.now().replace(microsecond=0)
            # print '\nInitial REAL time',TimeOfDay.now.ctime()
            self.testing=False
        TimeOfDay.last_now = TimeOfDay.now - timedelta(seconds=1)           
        self.build_schedule_for_today(self.schedule)
        if self.testing:
            self.print_todays_schedule()
        self.build_events_lists()
        # self.print_events_lists()
        # and do exitpipresents or start any show that should be running at start up time
        self.do_catchup()


    def do_catchup(self):
            TimeOfDay.scheduler_time=TimeOfDay.now.time()
            # shutdown or exit if current time is later than time in event list
            for show_ref in TimeOfDay.events:
                if show_ref == 'pp_core':
                    times = TimeOfDay.events[show_ref]
                    for time_element in reversed(times):
                        # print 'now', TimeOfDay.scheduler_time, 'time from events', time_element[1], time_element[0]
                        # got past current time can give up and execute exitpipresents or closedown
                        if   TimeOfDay.scheduler_time >= time_element[1]:
                            self.do_event(show_ref,time_element)
                            return 'exiting'

                    
            # do the catchup for each real show in turn
            for show_ref in TimeOfDay.events:
                 if show_ref != 'pp_core':
                    # print '\n*****',show_ref
                    times = TimeOfDay.events[show_ref]
                    # go through the event list for a show rembering show state until the first future event is found.
                    # then if last command was to start the show send it
                    show_running=False
                    last_start_element=[]
                    for time_element in reversed(times):
                        # print 'now', now_seconds, 'time from events', time_element[1], time_element[0]
                        # got past current time can give up catch up
                        if time_element[1]  >=  TimeOfDay.scheduler_time:
                            # print ' gone past time - break'
                            break
                        if time_element[0] == 'open':
                            last_start_element=time_element
                            # print 'open - show-running= true' 
                            show_running=True
                        elif time_element[0]=='close':
                            # print 'close - show-running= false' 
                            show_running=False
                    if show_running is True:
                        if self.testing:
                            print 'End of Catch Up Search doing', show_ref,last_start_element
                        self.do_event(show_ref,last_start_element)

##                    # print 'catchup time match', show_ref
##                    # now do the inital real time command if time now matches event time
##                    for time_element in reversed(times):
##                        if time_element[1]  ==  TimeOfDay.scheduler_time:
##                            print ' do event  - catchup', TimeOfDay.scheduler_time, 'time from events', time_element[1], time_element[0]
##                            self.do_event(show_ref,time_element)
            return 'not exiting'        

    # called by main program only         
    def poll(self):
        if self.testing:
            poll_time=TimeOfDay.now
        else:
            poll_time=datetime.now()
        # print 'poll time: ',poll_time.time(),'scheduler time: ',TimeOfDay.now.time()
        # if poll_time != TimeOfDay.now : print 'times different ',poll_time.time(),TimeOfDay.now.time()
        # is current time greater than last time the scheduler was run
        # run in a loop to catch up because root.after can get behind when images are being rendered etc.
        # poll time can be the same twice as poll is run at half second intervals.
        catchup_time=0
        while TimeOfDay.now<=poll_time:
            if  TimeOfDay.now-TimeOfDay.last_now != timedelta(seconds=1):
                print 'POLL TIME FAILED', TimeOfDay.last_now, TimeOfDay.now
            #if catchup_time != 0:
               # print 'scheduler behind by: ',catchup_time, TimeOfDay.now.time(),poll_time.time()
            self.do_scheduler()
            TimeOfDay.last_now=TimeOfDay.now
            catchup_time+=1
            TimeOfDay.now = TimeOfDay.now + timedelta(seconds=1)
        # and loop
        if self.testing:
            self.tick_timer=TimeOfDay.root.after(1000,self.poll)
        else:
            self.tick_timer=TimeOfDay.root.after(self.tod_tick,self.poll)


     # called by main program only           
    def terminate(self):
        if self.tick_timer is not None:
            TimeOfDay.root.after_cancel(self.tick_timer)
        self.clear_events_lists()


        
    # execute events at the appropriate time.
    # called by main program only   
    def do_scheduler(self):
        # if its midnight then build the events lists for the new day
        TimeOfDay.scheduler_time=TimeOfDay.now.time()
        if  TimeOfDay.scheduler_time == time(hour=0,minute=0,second=0):
            if self.testing:
                print 'Its midnight,  today is now', TimeOfDay.now.ctime()
            self.build_schedule_for_today(self.schedule)
            if self.testing:
                self.print_todays_schedule()
            self.build_events_lists()
            # self.print_events_lists()

        # print TimeOfDay.scheduler_time
        for show_ref in TimeOfDay.events:      
            # print 'scheduler time match', show_ref
            times = TimeOfDay.events[show_ref]
            # now send a command if time matches
            for time_element in reversed(times):
                # print time_element[1],TimeOfDay.scheduler_time
                if time_element[1]  ==  TimeOfDay.scheduler_time:
                    self.do_event(show_ref,time_element)


    # execute an event
    def do_event(self,show_ref,time_element):
        self.mon.log (self,'Event : '  + time_element[0] +  ' ' +  show_ref + ' required at: ' + time_element[1].isoformat())
        if self.testing:
            print 'Event : ' +  time_element[0] + ' ' + show_ref + ' required at: '+ time_element[1].isoformat()
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
# Preparing schedule and todays event list
# ************************************

    def open_schedule(self):
        # look for the schedule.json file
        # try inside profile
        filename=self.pp_profile+os.sep+"schedule.json"
        ifile  = open(filename, 'rb')
        schedule= json.load(ifile)
        ifile.close()
        self.mon.log(self,"schedule.json read from "+ filename)
        return schedule

    def build_schedule_for_today(self,schedule):
        # print this_day.year, this_day.month, this_day.day, TimeOfDay.DAYS_OF_WEEK[ this_day.weekday()]
        """
        self.todays_schedule is a dictionary the keys being show-refs.
        Each dictionary entry is a list of time_elements
        Each time element is a list with the fields:
        0 - command
        1 - time hour:min[:sec]

        """
        self.todays_schedule={}
        for show in schedule['shows']:
            show_ref=show['show-ref']
            if 'everyday' in show:
                day=show['everyday']
                # print day['day']
                times=day['times']
                for time in times:
                    self.todays_schedule[show['show-ref']]=copy.deepcopy(day['times'])
                # print '\nafter everyday'
                # self.print_todays_schedule()
      

            if 'weekday' in show:
                day=show['weekday']
                # print day['day']
                if  TimeOfDay.DAYS_OF_WEEK[ TimeOfDay.now.weekday()] in day['day'] :
                    # print 'weekday matched', TimeOfDay.DAYS_OF_WEEK[ TimeOfDay.now.weekday()]
                    times=day['times']
                    for time in times:
                        self.todays_schedule[show['show-ref']]=copy.deepcopy(day['times'])
                # print '\nafter weekday'
                # self.print_todays_schedule()


            if 'monthday' in show:
                day=show['monthday']
                # print day['day']
                if  TimeOfDay.now.day in map(int,day['day']):
                    # print 'monthday matched', day['day']
                    times=day['times']
                    for time in times:
                        self.todays_schedule[show['show-ref']]=copy.deepcopy(day['times'])
                # print '\nafter monthday'
                # self.print_todays_schedule()
                     
            if 'specialday' in show:
                days=show['specialday']
               # print days['day']
                for day in days['day']:
                    sdate=datetime.strptime(day,'%Y-%m-%d')
                    if sdate.year == TimeOfDay.now.year and sdate.month==TimeOfDay.now.month and sdate.day == TimeOfDay.now.day:
                        # print 'special matched', day
                        times=days['times']
                        # for time in times:
                        self.todays_schedule[show['show-ref']]=copy.deepcopy(days['times'])
                # print '\nafter specialday'
                # self.print_todays_schedule()                          
                

    def build_events_lists(self):
        # builds events dictionary from todays_schedule by
        # converting times in todays schedule from hour:min:sec to datetime
        # and sorts them earliest last
        TimeOfDay.events={}
        for show_ref in self.todays_schedule:
            # print show_ref
            times = self.todays_schedule[show_ref]
            for time_element in times:
                time_element[1]=self.parse_event_time(time_element[1])
            sorted_times=sorted(times,key = lambda time_element: time_element[1],reverse=True)
            TimeOfDay.events[show_ref]=sorted_times
            # print times


    def parse_event_time(self,time_text):
        fields=time_text.split(':')
        if len(fields)>2:
            secs=int(fields[2])
        else:
            secs=0
        hours=int(fields[0])
        mins=int(fields[1])
        return time(hour=hours,minute=mins,second=secs)


# *********************
# print for debug
# *********************
                    
    def print_todays_schedule(self):
        print '\nSchedule For '+ TimeOfDay.now.ctime()
        for key in self.todays_schedule:
            print '  '+key
            for show in self.todays_schedule[key]:
                print '    '+show[0]+ ':   '+show[1]
            print

    def print_events_lists(self):
        print '\nevents list for today'
        for key in self.events:
            print '\n',key
            for show in self.events[key]:
                print show[0],show[1].isoformat()
                

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
            

