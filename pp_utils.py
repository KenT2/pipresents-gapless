import time
import sys
import os
import tkMessageBox
import Tkinter as tk
import PIL.Image
import PIL.ImageTk
import pp_paths

#class Enum(object):
# see http://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python
#    Numbers = enum('ZERO', ONE', 'TWO', 'THREE')
#    Numbers.names[THREE] = 3
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['names'] = reverse
    return type('Enum', (), enums)


def load_gif(name):
    name += '.gif'
    icon = os.path.join(pp_paths.pp_resource_dir, name)
    return tk.PhotoImage(file=icon)


def load_png(name):
    name += '.png'
    path = os.path.join(pp_paths.pp_resource_dir, name)
    img = PIL.Image.open(path)
    return PIL.ImageTk.PhotoImage(img)


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

    m_fatal =  1  # fatal erros caused by PiPresents, could be a consequence of an 'error'
    m_err   =  2  # PP cannot continue because of an error caused by user in profile or command
    m_warn  =  4  # warning that something is not quite right but PP recovers gracefully
    m_log   =  8  # log of interest to profile developers
    m_trace = 16  # trace for software development
    m_trace_instance =32 # trace with id of instances of player and showers
    m_leak  = 64  # memory leak monitoring

    classes  = []
    
    log_level=0
    log_path=""            # set in pipresents
    ofile=None
    start_time= time.time()


# called at start by pipresents
    def init(self):
        if Monitor.ofile is None:
            bufsize=0
            Monitor.ofile=open(Monitor.log_path+ os.sep+'pp_logs' + os.sep + 'pp_log.txt','w',bufsize)
        Monitor.log_level=0
        Monitor.classes  = []
        Monitor.enable_in_code = False  # enables use of self.mon.set_log_level(nn) in classes


    # CONTROL

    def __init__(self):
        # default value for individual class logging
        self.this_class_level= Monitor.m_fatal|Monitor.m_err|Monitor.m_warn

    def set_log_level(self,level):
        self.this_class_level = level


    # PRINTING
  
    def newline(self,num):
        if Monitor.log_level & ~ (Monitor.m_warn|Monitor.m_err|Monitor.m_fatal) != 0:
            for i in range(0,num):
                print

    def fatal(self,caller,text):
        r_class=caller.__class__.__name__
        r_func = sys._getframe(1).f_code.co_name
        r_line =  str(sys._getframe(1).f_lineno)
        if self.enabled(r_class,Monitor.m_fatal) is True: 
            print "[fatal] %.2f" % (time.time()-Monitor.start_time), " System Error: ",r_class+"/"+ r_func + "/"+ r_line + ": ", text
            Monitor.ofile.write (" SYSTEM ERROR: " + r_class +"/"+ r_func + "/"+ r_line + ": " + text + "\n")
        tkMessageBox.showwarning(r_class ,'System Error:\n'+text)

    def err(self,caller,text):
        r_class=caller.__class__.__name__
        if self.enabled(r_class,Monitor.m_err) is True:        
            print "[err]   %.2f" % (time.time()-Monitor.start_time), " Profile Error: ",r_class+": ", text
            Monitor.ofile.write (" ERROR: " + self.pretty_inst(caller)+ ":  " + text + "\n")
        tkMessageBox.showwarning(r_class ,'Profile Error:\n'+text)
                                        
    def warn(self,caller,text):
        r_class=caller.__class__.__name__
        if self.enabled(r_class,Monitor.m_warn) is True:     
            print "[warn]   %.2f" % (time.time()-Monitor.start_time), " Warning: ",self.pretty_inst(caller) +": ", text
            Monitor.ofile.write (" WARNING: " + self.pretty_inst(caller)+ ":  " + text + "\n")

    def log(self,caller,text):
        r_class=caller.__class__.__name__
        if self.enabled(r_class,Monitor.m_log) is True:
            print "[log]    %.2f" % (time.time()-Monitor.start_time) +" "+r_class+": " + text
            # print "%.2f" % (time.time()-Monitor.start_time) +" "+self.pretty_inst(caller)+": " + text
            Monitor.ofile.write (str(time.time()-Monitor.start_time) + " " + self.pretty_inst(caller)+": " + text+"\n")

    def trace(self,caller,text):
        r_class=caller.__class__.__name__
        r_class = type(caller).__name__
        r_func = sys._getframe(1).f_code.co_name
        r_line =  str(sys._getframe(1).f_lineno)
        r_id = 'id='+str(id(caller))
        r_longid = caller
        # self.print_info(r_class,Monitor.m_trace)
        if self.enabled(r_class,Monitor.m_trace) is True:
            print  "[trace] " + self.pretty_inst(caller)+'/'+r_func, text
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

##    def id(self,caller):
##        return self.pretty_inst(caller)

