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
    def init(self,pp_dir,pp_home,pp_profile,showlist,root,callback):
       
        # instantiate arguments
        TimeOfDay.root=root
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile
        self.showlist=showlist
        self.callback=callback

        # init variables
        self.testing=False
        self.tod_tick=500
        self.tick_timer=None
        # set time of day for if no schedule
        TimeOfDay.now = datetime.now().replace(microsecond=0)
        
        #  read and error check the schedule
        reason,message,schedule_enabled=self.read_schedule()
        if reason == 'error':
            return 'error',message,False
        
        if schedule_enabled is False:
            return 'normal','',False

        #create the initial events list
        if self.simulate_time is True:
            year= int(self.sim_year)
            month= int(self.sim_month)
            day = int(self.sim_day)
            hour= int(self.sim_hour)
            minute= int(self.sim_minute)
            second= int(self.sim_second)
            TimeOfDay.now = datetime(day = day, month =month, year=year,hour=hour, minute=minute, second=second)
            self.testing=True
            print '\nInitial SIMULATED time',TimeOfDay.now.ctime()
            self.mon.sched(self,TimeOfDay.now,'Testing is ON, Initial SIMULATED time ' + str(TimeOfDay.now.ctime()))
        else:
            #get the current date/time only this once
            TimeOfDay.now = datetime.now().replace(microsecond=0)
            self.mon.sched(self,TimeOfDay.now,'Testing is OFF, Initial REAL time ' + str(TimeOfDay.now.ctime()))
            # print '\nInitial REAL time',TimeOfDay.now.ctime()
            self.testing=False
        # print 'init',TimeOfDay.now
        TimeOfDay.last_now = TimeOfDay.now - timedelta(seconds=1)           
        reason,message=self.build_schedule_for_today()
        if reason == 'error':
            return 'error',message,False
        self.mon.sched(self,TimeOfDay.now,self.pretty_todays_schedule())
        if self.testing:
            self.print_todays_schedule()
        self.build_events_lists()
        if self.testing:
            self.print_events_lists()
        # and do exitpipresents or start any show that should be running at start up time
        self.do_catchup()
        return 'normal','',True


    def do_catchup(self):
            TimeOfDay.scheduler_time=TimeOfDay.now.time()
                    
            # do the catchup for each real show in turn
            # nothing required for start show, all previous events are just ignored.
            for show_ref in TimeOfDay.events:
                 if show_ref != 'start':
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
                        #if self.testing:
                            # print 'End of Catch Up Search', show_ref,last_start_element
                        self.mon.sched(self,TimeOfDay.now,'Catch up for show: ' + show_ref +' requires '+ last_start_element[0] + ' ' +str(last_start_element[1]))
                        self.do_event(show_ref,last_start_element)

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
            # print 'poll',TimeOfDay.now, timedelta(seconds=1)
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
            # if self.testing:
                # print 'Its midnight,  today is now', TimeOfDay.now.ctime()
            self.mon.sched(self,TimeOfDay.now,'Its midnight,  today is now ' + str(TimeOfDay.now.ctime()))
            reason,message=self.build_schedule_for_today()
            if reason=='error':
                self.mon.err(self,'system error- illegal time at midnight')
                return
            self.mon.sched(self,TimeOfDay.now,self.pretty_todays_schedule())
            # if self.testing:
                # self.print_todays_schedule()
            self.build_events_lists()
            # self.mon.sched(self,TimeOfDay.now,self.pretty_events_lists())
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
        self.mon.sched (self,TimeOfDay.now,' ToD Scheduler : '  + time_element[0] +  ' ' +  show_ref + ' required at: ' + time_element[1].isoformat())
        # if self.testing:
            # print 'Event : ' +  time_element[0] + ' ' + show_ref + ' required at: '+ time_element[1].isoformat()
        if show_ref != 'start':
            self.callback(time_element[0]  + ' ' + show_ref)
        else:
            self.callback(time_element[0])            


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

    def read_schedule(self):
        # get schedule from showlist
        index = self.showlist.index_of_start_show()
        self.showlist.select(index)
        starter_show=self.showlist.selected_show()
        
        sched_enabled=starter_show['sched-enable']
        if sched_enabled != 'yes':
            return 'normal','',False
        
        if starter_show['simulate-time'] == 'yes':
            self.simulate_time= True
            
            self.sim_second=starter_show['sim-second']
            if not self.sim_second.isdigit():
                return 'error','Simulate time -  second is not a positive integer '+self.sim_second,False
            if int(self.sim_second)>59:
                return 'error','Simulate time - second is out of range '+self.sim_second,False          

            self.sim_minute=starter_show['sim-minute']
            if not self.sim_minute.isdigit():
                return 'error','Simulate time - minute is not a positive integer '+self.sim_minute,False
            if int(self.sim_minute)>59:
                return 'error','Simulate time -  minute is out of range '+self.sim_minute,False

            self.sim_hour=starter_show['sim-hour']
            if not self.sim_hour.isdigit():
                return 'error','Simulate time - hour is not a positive integer '+self.sim_hour,False
            if int(self.sim_hour)>23:
                return 'error','Simulate time -  hour is out of range '+self.sim_hour,False

            self.sim_day=starter_show['sim-day']
            if not self.sim_day.isdigit():
                return 'error','Simulate time - day is not a positive integer '+self.sim_day,False
            if int(self.sim_day)>31:
                return 'error','Simulate time -  day is out of range '+self.sim_day,False        

            self.sim_month=starter_show['sim-month']
            if not self.sim_month.isdigit():
                return 'error','Simulate time - month is not a positive integer '+self.sim_month,False
            if int(self.sim_month)>12:
                return 'error','Simulate time -  month is out of range '+self.sim_month,False     

            self.sim_year=starter_show['sim-year']
            if not self.sim_year.isdigit():
                return 'error','Simulate time - year is not a positive integer '+self.sim_year,False
            if int(self.sim_year)<2018:
                return 'error','Simulate time -  year is out of range '+self.sim_year,False     
        else:
            self.simulate_time=False

        return 'normal','',True
    

        

        

    def build_schedule_for_today(self):
        # print this_day.year, this_day.month, this_day.day, TimeOfDay.DAYS_OF_WEEK[ this_day.weekday()]
        """
        self.todays_schedule is a dictionary the keys being show-refs.
        Each dictionary entry is a list of time_elements
        Each time element is a list with the fields:
        0 - command
        1 - time hour:min[:sec]

        """
        self.todays_schedule={}
        for index in range(self.showlist.length()):
            show= self.showlist.show(index)
            show_type=show['type']
            show_ref=show['show-ref']
            # print 'looping build ',show_type,show_ref,self.showlist.length()
            if 'sched-everyday' in show:
                text=show['sched-everyday']
                lines=text.splitlines()
                while len(lines) != 0:
                    status,message,day_lines,lines=self.get_one_day(lines,show_ref)
                    if status == 'error':
                        return 'error',message                    
                    status,message,days_list,times_list=self.parse_day(day_lines,'everyday',show_ref,show_type)
                    if status == 'error':
                        return 'error',message
                    #print 'everyday ',status,message,days_list,times_list
                    self.todays_schedule[show['show-ref']]=copy.deepcopy(times_list)
                    
                # print '\nafter everyday'
                # self.print_todays_schedule()
      

            if 'sched-weekday' in show:
                text=show['sched-weekday']
                lines=text.splitlines()
                while len(lines) != 0:
                    status,message,day_lines,lines=self.get_one_day(lines,show_ref)
                    if status == 'error':
                        return 'error',message
                    status,message,days_list,times_list=self.parse_day(day_lines,'weekday',show_ref,show_type)
                    if status == 'error':
                        return 'error',message
                    #print 'weekday ',status,message,days_list,times_list
                    # is current day of the week in list of days in schedule
                    if  TimeOfDay.DAYS_OF_WEEK[ TimeOfDay.now.weekday()] in days_list:
                        self.todays_schedule[show['show-ref']]=copy.deepcopy(times_list)
                        
                #print '\nafter weekday'
                #self.print_todays_schedule()
  

            if 'sched-monthday' in show:
                text=show['sched-monthday']
                lines=text.splitlines()
                while len(lines) != 0:
                    status,message,day_lines,lines=self.get_one_day(lines,show_ref)
                    # print 'in monthday',day_lines
                    if status == 'error':
                        return 'error',message
                    status,message,days_list,times_list=self.parse_day(day_lines,'monthday',show_ref,show_type)
                    if status == 'error':
                        return 'error',message
                    #print 'monthday ',status,message,days_list,times_list                
                    if  TimeOfDay.now.day in map(int,days_list):
                        self.todays_schedule[show['show-ref']]=copy.deepcopy(times_list)

                #print '\nafter monthday'
                #self.print_todays_schedule()
                     
            if 'sched-specialday' in show:

                text=show['sched-specialday']
                lines=text.splitlines()
                while len(lines) != 0:
                    status,message,day_lines,lines=self.get_one_day(lines,show_ref)
                    if status == 'error':
                        return 'error',message
                  
                    status,message,days_list,times_list=self.parse_day(day_lines,'specialday',show_ref,show_type)
                    if status == 'error':
                        return 'error',message
                    # print 'specialday ',status,message,days_list,times_list                
                    for day in days_list:
                        sdate=datetime.strptime(day,'%Y-%m-%d')
                        if sdate.year == TimeOfDay.now.year and sdate.month==TimeOfDay.now.month and sdate.day == TimeOfDay.now.day:
                            self.todays_schedule[show['show-ref']]=copy.deepcopy(times_list)

                #print '\nafter specialday'
                #self.print_todays_schedule()
        return 'normal',''

    def get_one_day(self,lines,show_ref):
        this_day=[]
        left_over=[]
        #print 'get one day',lines
        # check first line is day and move tt output
        #print lines[0]
        if not lines[0].startswith('day'):
            return 'error','first line of section is not day ' + lines[0] + ' '+ show_ref,[],[]
        this_day=[lines[0]]
        #print ' this day',this_day
        left_over=lines[1:]
        # print 'left over',left_over
        x_left_over=lines[1:]
        for line in x_left_over:
            #print 'in loop',line
            if line.startswith('day'):
                # print 'one day day',this_day,left_over
                return 'normal','',this_day,left_over
            this_day.append(line)
            left_over=left_over[1:]
        # print 'one day end',this_day,left_over
        return 'normal','',this_day,left_over
                
    def parse_day(self,lines,section,show_ref,show_type):
        # text
        # day monday
        # open 1:42
        # close 1:45
        # returns status,message,list of days,list of time lines
        print 'lines ',len(lines), section
        if section == 'everyday':
            status,message,days_list=self.parse_everyday(lines[0],show_ref)
        elif section == 'weekday':
            status,message,days_list=self.parse_weekday(lines[0],show_ref)
        elif section == 'monthday':
            # print 'parse_day',lines
            status,message,days_list=self.parse_monthday(lines[0],show_ref)
        elif section == 'specialday':
            status,message,days_list=self.parse_specialday(lines[0],show_ref)
        else:
            return 'error','illegal section name '+section + ' '+ show_ref,[],[]
        if status == 'error':
            return 'error',message,[],[]
        if len(lines) >1:
            time_lines=lines[1:]
            status,message,times_list=self.parse_time_lines(time_lines,show_ref,show_type)
            if status =='error':
                return 'error',message,[],[]
        else:
            times_list=[]
        return 'normal','',days_list,times_list

    def parse_everyday(self,line,show_ref):
        words=line.split()
        if words[0]!='day':
            return 'error','day line does not contain day  '+ line + ' ' + show_ref,[]
        if words[1] != 'everyday':
            return 'error','everday line does not contain everyday  '+ show_ref,[]
        return 'normal','',['everyday']
       

    def parse_weekday(self,line,show_ref):
        words=line.split()
        if words[0]!='day':
            return 'error','day line does not contain day  ' + line + ' ' + show_ref,[]
        days=words[1:]
        for day in days:
            if day not in TimeOfDay.DAYS_OF_WEEK:
                return 'error','weekday line has illegal day '+ day + ' '+ show_ref,[]
        return 'normal','',days

    def parse_monthday(self,line,show_ref):
        words=line.split()
        if words[0]!='day':
            return 'error','day line does not contain day  '+ show_ref,[]
        days=words[1:]
        for day in days:
            if not day.isdigit():
                return 'error','monthday line has illegal day '+ day + ' '+ show_ref,[]                
            if int(day) <1 or int(day)>31:
                return 'error','monthday line has out of range day '+ line+ ' '+ show_ref,[]
        return 'normal','',days

    def parse_specialday(self,line,show_ref):
        words=line.split()
        if words[0]!='day':
            return 'error','day line does not contain day  '+ show_ref,[]
        days=words[1:]
        for day in days:
            status,message=self.parse_date(day,show_ref)
            if status == 'error':
                return 'error',message,''              
        return 'normal','',days

   
    def parse_time_lines(self,lines,show_ref,show_type):
        # lines - list of  lines each with text 'command time'
        # returns list of lists each being [command, time]
        time_lines=[]
        for line in lines:
            # split line into time,command
            words=line.split()
            if len(words)<2:
                return 'error','time line has wrong length '+ line+ ' '+ show_ref,[]
            status,message,time_item=self.parse_time(words[0],show_ref)
            if status== 'error':
                return 'error',message,[]

            if show_type=='start':
                command = ' '.join(words[1:])
                time_lines.append([command,time_item])                
            else:
                if words[1] not in ('open','close'):
                    return 'error','illegal command in '+ line+ ' '+ show_ref,[]
                time_lines.append([words[1],time_item])
        return 'normal','',time_lines



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

    def parse_time(self,item,show_ref):        
        fields=item.split(':')
        if len(fields) == 0:
            return 'error','Time field is empty '+ item + ' ' + show_ref, item
        if len(fields)>3:
            return 'error','Too many fields in ' + item + ' ' + show_ref, item
        if len(fields) == 1:
            seconds=fields[0]
            minutes='0'
            hours='0'
        if len(fields) == 2:
            seconds=fields[1]
            minutes=fields[0]
            hours='0'
        if len(fields) == 3:
            seconds=fields[2]
            minutes=fields[1]
            hours=fields[0]
        if not seconds.isdigit() or not  minutes.isdigit() or  not hours.isdigit():
            return 'error','Fields of  '+ item + ' are not positive integers ' + show_ref,item     
        if int(minutes)>59:
            return 'error','Minutes of  '+ item + ' is out of range '+ show_ref,item
        if int(seconds)>59:
            return 'error','Seconds of  '+ item + ' is out of range ' +show_ref,item
        if int(hours)>23:
            return 'error','Hours of  '+ item + ' is out of range '+ show_ref,item           
        return 'normal','',item


    def parse_date(self,item,show_ref):
        fields=item.split('-')
        if len(fields) == 0:
            return 'error','Date field is empty '+item  + ' '+ show_ref
        if len(fields)!=3:
            return 'error','Too many or few fields in date ' + item  + ' ' + show_ref
        year=fields[0]
        month=fields[1]
        day = fields[2]
        if not year.isdigit() or not  month.isdigit() or  not day.isdigit():
            return 'error','Fields of  '+ item + ' are not positive integers ' + show_ref    
        if int(year)<2018:
            return 'error','Year of  '+ item + ' is out of range '+ show_ref + year
        if int(month)>12:
            return 'error','Month of  '+ item + ' is out of range ' +show_ref
        if int(day)>31:
            return 'error','Day of  '+ item + ' is out of range '+ show_ref
        return 'normal',''
        
# *********************
# print for debug
# *********************

    def pretty_todays_schedule(self):
        op='Schedule For ' + TimeOfDay.now.ctime() + '\n'
        for key in self.todays_schedule:
            op += '  '+ key + '\n'
            for show in self.todays_schedule[key]:
                op += '    '+show[0]+ ':   '+ str(show[1])+ '\n'
            op +='\n'
        return op

    def pretty_events_lists(self):
        op = ' Task list for today'
        for key in self.events:
            op += '\n' + key
            for show in self.events[key]:
                op += '\n    ' + show[0] + ' ' + str(show[1].isoformat())
        return op

                    
    def print_todays_schedule(self):
        print '\nSchedule For '+ TimeOfDay.now.ctime()
        for key in self.todays_schedule:
            print '  '+key
            for show in self.todays_schedule[key]:
                print '    '+show[0]+ ':   '+show[1]
            print

    def print_events_lists(self):
        print '\nTask list for today'
        for key in self.events:
            print '\n',key
            for show in self.events[key]:
                print show[0],show[1].isoformat()
        print
                

            

