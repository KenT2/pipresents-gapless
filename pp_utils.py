import time
import tkMessageBox

class StopWatch:
    
    global_enable=False

    def __init__(self):
        self.enable=False

    def on(self):
        self.enable=True

    def off(self):
        self.enable=False
    
    def start(self):
        if StopWatch.global_enable and self.enable: self.sstart=time.clock()

    def split(self,text):
        if StopWatch.global_enable and self.enable:
            self.end=time.clock()
            print text + " " + str(self.end-self.sstart) + " secs"
            self.sstart=time.clock()
        
    def stop(self,text):
        if StopWatch.global_enable and self.enable:
            self.end=time.clock()
            print text + " " + str(self.end-self.sstart) + " secs"


class Monitor:
    # 0  - errors only
    # 1  - errors and warnings
    # 2  - everything
    
    global_enable=0
    log_path=""
    ofile=None
    start_time= time.time()
    warnings=0
    fatals=0

    def __init__(self):
        if Monitor.ofile==None:
            bufsize=0
            Monitor.ofile=open(Monitor.log_path+"/pp_log.log","w",bufsize)          
        self.enable=False


    def on(self):
        self.enable=True
        
    def off(self):
        self.enable=False

    def err(self,caller,text):
        print "%.2f" % (time.time()-Monitor.start_time), " ERROR: ",caller.__class__.__name__," ", text
        Monitor.ofile.write (" ERROR: " + caller.__class__.__name__ + ":  " + text + "\n")
        tkMessageBox.showwarning(
                                caller.__class__.__name__ ,
                                text
                                        )
                                        
    def warn(self,caller,text):
        if Monitor.global_enable >0 and self.enable:
            print "%.2f" % (time.time()-Monitor.start_time), " WARNING: ",caller.__class__.__name__," ", text
            Monitor.ofile.write (" WARNING: " + caller.__class__.__name__ + ":  " + text + "\n")


    def log(self,caller,text):
        if Monitor.global_enable >1  and self.enable:
             print "%.2f" % (time.time()-Monitor.start_time), " ",caller.__class__.__name__," ", text
             Monitor.ofile.write (str(time.time()-Monitor.start_time) + " " + caller.__class__.__name__ +": " + text+"\n")
             
  
    def finish(self):
        Monitor.ofile.close()
        pass
