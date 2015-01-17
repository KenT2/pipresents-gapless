import pexpect
import os
from glob import glob
from os import stat as os_stat
from pp_utils import Monitor
from stat import S_ISFIFO

"""
    based on pyomxplayer from https://github.com/jbaiter/pyomxplayer
    extensively modified by KenT

    uzblDriver hides the detail of using the luakit command  from browserplayer
    This is meant to be used with pp_browserplayer.py
    Its easy to end up with many copies of uzbl running if this class is not used with care.
    use pp_browserplayer.py for a safer interface.


    External commands
    ----------------------------
    __init__ just creates the instance and initialises variables (e.g. bplayer=uzblDriver())
    play -  opens the browser and plays the first track
    control  - sends commands to uzbl while it is open 
    stop - closes the browser.
    terminate - Stops the browser. Used when aborting an application.


    Signals
    ----------
    The following signals are produced while the browser is open
         self.start_play_signal = True when the browser is ready to be used

    is_running() tests whether the sub-process running uzbl is alive.

"""

class UZBLDriver(object):

    def __init__(self,widget):

        self.widget=widget
        
        self.mon=Monitor()

        self._process=None
        self.fifo=''

    def pause(self):
        pass

    def stop(self):
        self.control('exit')


    # kill the subprocess (uzbl). Used for tidy up on exit.
    def terminate(self,reason):
        self.terminate_reason=reason
        if self.exists_fifo():
            self.control('exit')
            # self._process.close(force=True)
    
    def play(self, track, geometry):
        self.start_play_signal = False
        # track= "'"+ track.replace("'","'\\''") + "'"

        cmd='uzbl-browser '  + geometry + '--uri='+track
        self.mon.log(self, "Send command to uzbl: "+ cmd)
        self._process = pexpect.spawn(cmd)       
        # uncomment to monitor output to and input from uzbl (read pexpect manual)
        # fout= file('/home/pi/pipresents/uzbllogfile.txt','w')  #uncomment and change sys.stdout to fout to log to a file
        # self._process.logfile_send = sys.stdout  # send just commands to stdout
        # self._process.logfile=fout  # send all communications to log
        
        # and poll for fifo to be available
        self.get_fifo()

    # poll for fifo to be available
    # when it is set start_play_signal
    # browser player calls is_running at intervals to test if uzbl is ended after an exit command
    def get_fifo(self):
        """
        Look for UZBL's FIFO-file in /tmp.
        Don't give up until it has been found.
        """
        candidates = glob('/tmp/uzbl_fifo_*')
        for fifo_file in candidates:
            if S_ISFIFO(os_stat(fifo_file).st_mode):
                self.mon.log(self, 'Found UZBL fifo  in %s.' % fifo_file)
                self.fifo=fifo_file
                self.start_play_signal=True
                return
        # print 'fifo not found trying again'
        self.widget.after(500,self.get_fifo)


    def exists_fifo(self):
        if os.path.exists(self.fifo):
            return True
        else:
            return False

    # send commands to uzbl via the fifo
    def control(self,data):
        if self.exists_fifo():
            self.mon.log(self,'send command to uzbl:'+ data)
            f = open(self.fifo, 'a')
            f.write('%s\n' % data)
            f.close()
            # self.mon.log(self,'sent command to uzbl:'+ data)

   # test of whether _process is running
    def is_running(self):
        return self._process.isalive()     

   

    


