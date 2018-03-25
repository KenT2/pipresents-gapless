# dec 2015 - hide terminal output if --manager option.
# 28/1/2016  - additional filter and log output for statistics

import string
import time
import datetime
import sys
import os
import gc
import tkMessageBox
from Tkinter import NW,N,W,CENTER,LEFT,RIGHT
# from pympler.tracker import SummaryTracker
# from pympler import summary, muppy
# import types

def calculate_text_position(x_text,y_text,x1,y1,centre_x,centre_y,width,height,justify_text):
    if x_text == '':
        x=x1+centre_x
    else:
        x = int(x_text)+x1
        
    if y_text == '':
        y=y1+centre_y 
    else:
        y=int(y_text)+y1

    if x_text == '' and y_text=='':
        anchor=CENTER
    elif x_text == '' and y_text!='':
        anchor = N
    elif x_text != '' and y_text=='':
        anchor = W
    else:
        anchor= NW

    if justify_text=='left':
        justify=LEFT
    elif justify_text=='right':
        justify=RIGHT
    else:
        justify=CENTER
    return x,y,anchor,justify


def parse_rectangle(text):
    if text.strip() == '':
        return 'error','No points in rectangle: '+text,0,0,0,0
    if '+' in text:
        # parse  x+y+width*height
        fields=text.split('+')
        if len(fields) != 3:
            return 'error','Do not understand rectangle: '+ text,0,0,0,0
        dimensions=fields[2].split('*')
        if len(dimensions)!=2:
            return 'error','Do not understand rectangle: '+text,0,0,0,0
        
        if not fields[0].isdigit():
            return 'error','x1 is not a positive integer: '+ text,0,0,0,0
        else:
            x1=int(fields[0])
        
        if not fields[1].isdigit():
            return 'error','y1 is not a positive integer: '+ text,0,0,0,0
        else:
            y1=int(fields[1])
            
        if not dimensions[0].isdigit():
            return 'error','width is not a positive integer: '+text,0,0,0,0
        else:
            width=int(dimensions[0])
            
        if not dimensions[1].isdigit():
            return 'error','height is not a positive integer: '+text,0,0,0,0
        else:
            height=int(dimensions[1])

        return 'normal','',x1,y1,x1+width,y1+height
    
    else:
        fields=text.split()
        if len(fields) == 4:
            # rectangle is specified
            if not (fields[0].isdigit() and fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit()):
                return 'error','coordinates are not positive integers ' +text,0,0,0,0
            return 'normal','',int(fields[0]),int(fields[1]),int(fields[2]),int(fields[3])
        else:
            # error
            return 'error','illegal rectangle: '+ text,0,0,0,0

def calculate_relative_path(file_path,pp_home_dir,pp_profile_dir):
        # is media in the profile
        # print 'pp_profile dir ',pp_profile_dir
        in_profile=False
        if pp_profile_dir in file_path:
            in_profile=True
            
        if in_profile is True:
            # deal with media in profile @
            relpath = os.path.relpath(file_path,pp_profile_dir)
            # print "@ relative path ",relpath
            common = os.path.commonprefix([file_path,pp_profile_dir])
            # print "@ common ",common
            if common == pp_profile_dir:
                location = "@" + os.sep + relpath
                location = string.replace(location,'\\','/')
                # print '@location ',location
                # print
                return location
            else:
                # print '@absolute ',file_path
                return file_path            
        else:
            # deal with media in pp_home  +     
            relpath = os.path.relpath(file_path,pp_home_dir)
            # print "+ relative path ",relpath
            common = os.path.commonprefix([file_path,pp_home_dir])
            # print "+ common ",common
            if common == pp_home_dir:
                location = "+" + os.sep + relpath
                location = string.replace(location,'\\','/')
                # print '+location ', location
                # print
                return location
            else:
                # print '+ absolute ',file_path
                # print
                return file_path

 

class StopWatch(object):
    
    global_enable=False

    def __init__(self):
        self.enable=False

    def on(self):
        self.enable=True

    def off(self):
        self.enable=False
    
    def start(self):
        if StopWatch.global_enable and self.enable:
            self.sstart=time.clock()

    def split(self,text):
        if StopWatch.global_enable and self.enable:
            self.end=time.clock()
            print text + " " + str(self.end-self.sstart) + " secs"
            self.sstart=time.clock()
        
    def stop(self,text):
        if StopWatch.global_enable and self.enable:
            self.end=time.clock()
            print text + " " + str(self.end-self.sstart) + " secs"



class Monitor(object):

    delimiter=';'

    m_fatal =1    # fatal erros caused by PiPresents, could be a consequence of an 'error'
    m_err = 2  # PP cannot continue because of an error caused by user in profile or command
    m_warn =4  # warning that something is not quite right but PP recovers gracefully
    m_log =8  # log of interest to profile developers
    m_trace =16 # trace for software development
    m_trace_instance =32 # trace with id of instances of player and showers
    m_leak = 64 # memory leak monitoring
    m_stats = 128  #statistics
    m_sched = 256 #  time of day scheduler

    classes  = []
    
    log_level=0              
    log_path=""            # set in pipresents
    ofile=None
    stats_file=None
    start_time= time.time()
    tracker=None
    show_count=0
    track_count=0


# called at start by pipresents
    def init(self):
        # Monitor.tracker = SummaryTracker()
        if Monitor.ofile is None:
            bufsize=0
            Monitor.ofile=open(Monitor.log_path+ os.sep+'pp_logs' + os.sep + 'pp_log.txt','w',bufsize)
        Monitor.log_level=0     # set in pipresents
        Monitor.manager=False  #set in pipresents
        Monitor.classes  = []
        Monitor.enable_in_code = False  # enables use of self.mon.set_log_level(nn) in classes
        
        # statistics file, open for appending so its not deleted
        if Monitor.stats_file is None:
            Monitor.stats_file=open(Monitor.log_path+ os.sep+'pp_logs' + os.sep + 'pp_stats.txt','a',bufsize)
            sep='"'+Monitor.delimiter+'"'
            if Monitor.stats_file.tell()==0:
                Monitor.stats_file.write('"'+'Date'+sep+'Time'+sep+'Show Type'+sep+'Show Ref'+ sep +'Show Title'+sep
                                     +'Command'+sep+'Track Type'+sep+'Track Ref'+sep+'Track Title'+sep+'Location"\n')

    def leak_diff(self):
        Monitor.tracker.print_diff()

    def leak_summary(self):
        all_objects = muppy.get_objects()
        sum1 = summary.summarize(all_objects)
        summary.print_(sum1)   


    def leak_anal(self):
        all_objects = muppy.get_objects()
        my_types = muppy.filter(all_objects, Type=ImagePlayer)
        print len(my_types)                                    
        for t in my_types:
            print t,sys.getrefcount(t)
            # ,gc.get_referrers(t) 

    # CONTROL

    def __init__(self):
        # default value for individual class logging
        self.this_class_level= Monitor.m_fatal|Monitor.m_err|Monitor.m_warn

    def set_log_level(self,level):
        self.this_class_level = level


    # PRINTING
  
    def newline(self,num):
        if Monitor.manager is False:
            if Monitor.log_level & ~ (Monitor.m_warn|Monitor.m_err|Monitor.m_fatal|Monitor.m_sched) != 0:
                for i in range(0,num):
                    print

    def fatal(self,caller,text):
        r_class=caller.__class__.__name__
        r_func = sys._getframe(1).f_code.co_name
        r_line =  str(sys._getframe(1).f_lineno)
        if self.enabled(r_class,Monitor.m_fatal) is True: 
            print "%.2f" % (time.time()-Monitor.start_time), " System Error: ",r_class+"/"+ r_func + "/"+ r_line + ": ", text
            Monitor.ofile.write (" SYSTEM ERROR: " + r_class +"/"+ r_func + "/"+ r_line + ": " + text + "\n")
        if Monitor.manager is False:
            tkMessageBox.showwarning(r_class ,'System Error:\n'+text)

    def err(self,caller,text):
        r_class=caller.__class__.__name__
        if self.enabled(r_class,Monitor.m_err) is True:        
            print "%.2f" % (time.time()-Monitor.start_time), " Profile Error: ",r_class+": ", text
            Monitor.ofile.write (" ERROR: " + self.pretty_inst(caller)+ ":  " + text + "\n")
        if Monitor.manager is False:
            tkMessageBox.showwarning(r_class ,'Profile Error:\n'+text)
                                        
    def warn(self,caller,text):
        r_class=caller.__class__.__name__
        if self.enabled(r_class,Monitor.m_warn) is True:     
            print "%.2f" % (time.time()-Monitor.start_time), " Warning: ",self.pretty_inst(caller) +": ", text
            Monitor.ofile.write (" WARNING: " + self.pretty_inst(caller)+ ":  " + text + "\n")

    def sched(self,caller,pipresents_time,text):
        r_class=caller.__class__.__name__
        if self.enabled(r_class,Monitor.m_sched) is True:
            if pipresents_time is None:
                ptime='       '
            else:
                ptime=str(pipresents_time)
            print ptime +" "+r_class+": " + text
            # print "%.2f" % (time.time()-Monitor.start_time) +" "+self.pretty_inst(caller)+": " + text
            Monitor.ofile.write (time.strftime("%Y-%m-%d %H:%M") + " " + self.pretty_inst(caller)+": " + text+"\n")



    def log(self,caller,text):
        r_class=caller.__class__.__name__
        if self.enabled(r_class,Monitor.m_log) is True:
            print "%.2f" % (time.time()-Monitor.start_time) +" "+r_class+": " + text
            # print "%.2f" % (time.time()-Monitor.start_time) +" "+self.pretty_inst(caller)+": " + text
            Monitor.ofile.write (str(time.time()-Monitor.start_time) + " " + self.pretty_inst(caller)+": " + text+"\n")

    def start_stats(self,profile):
            self.stats((""),(""),(""),("start"),(""),(""),(""),(profile))
            
    def stats(self,*args):
        if (Monitor.m_stats & Monitor.log_level) != 0:
            # this ref, this name, action, type, ref, name, location
            arg_string=''
            for arg in args:
                arg_string+= Monitor.delimiter+'"'+arg + '"'
            current_datetime = datetime.datetime.now()
            Monitor.stats_file.write ('"'+current_datetime.strftime('%Y-%m-%d')+ '"'+Monitor.delimiter+'"'+ current_datetime.strftime('%H:%M:%S') + '"'+ arg_string+"\n")  

            
    def trace(self,caller,text):
        r_class=caller.__class__.__name__
        r_class = type(caller).__name__
        r_func = sys._getframe(1).f_code.co_name
        r_line =  str(sys._getframe(1).f_lineno)
        r_id = 'id='+str(id(caller))
        r_longid = caller
        # self.print_info(r_class,Monitor.m_trace)
        if self.enabled(r_class,Monitor.m_trace) is True:
            print  self.pretty_inst(caller)+'/'+r_func, text
            Monitor.ofile.write ( self.pretty_inst(caller)+" /" + r_func +" " + text+"\n")

    def print_info(self,r_class,mask):
        print  'called from', r_class
        print 'Global Log level',Monitor.log_level
        print 'Global enable in code', Monitor.enable_in_code
        print 'in code log level',self.this_class_level
        print 'Trace mask',mask
             
    def enabled(self,r_class,report):
        enabled_in_code=(report & self.this_class_level) != 0 and Monitor.enable_in_code is True
        
        globally_enabled=(report & Monitor.log_level) !=0 and r_class in Monitor.classes
        
        if enabled_in_code is True or globally_enabled is True:
            return True
        else:
            return False

    def pretty_inst(self,inst):
        if inst is None:
            return 'None'
        else:
            return inst.__class__.__name__ + '_' + str(id(inst))
  
    def finish(self):
        Monitor.ofile.close()
        Monitor.stats_file.close()

##    def id(self,caller):
##        return self.pretty_inst(caller)

