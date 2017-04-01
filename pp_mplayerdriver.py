import pexpect
import re
import os

from threading import Thread
from time import sleep
from pp_utils import Monitor

"""
 pyomxplayer from https://github.com/jbaiter/pyomxplayer
 extensively modified by KenT

 mplayerDriver hides the detail of using the mplayer command  from audioplayer
 This is meant to be used with pp_audioplayer.py
 Its easy to end up with many copies of mplayer running if this class is not used with care.
 use pp_audioplayer.py for a safer interface.


 External commands
 ----------------------------
 __init__ just creates the instance and initialises variables (e.g. mplayer=mplayerDriver())
 play -  plays a track
 pause  - toggles pause
 control  - sends controls to mplayer while a track is playing (use stop and pause instead of q and p)
 stop - stops a video that is playing.
 terminate - Stops a video playing. Used when aborting an application.
 
 Advanced:
 prepare  - processes the track up to where it is ready to display, at this time it pauses.
 show  - plays the video from where 'prepare' left off by resuming from the pause.


Signals
----------
 The following signals are produced while a track is playing
         self.start_play_signal = True when a track is ready to be shown
         self.end_play_signal= True when a track has finished due to stop or because it has come to an end
 Also is_running() tests whether the sub-process running mplayer is alive.

"""

class MplayerDriver(object):

    _STATUS_REXP = re.compile(r"V :\s*([\d.]+).*") 
    _DONE_REXP = re.compile(r"Exiting*")

    _LAUNCH_CMD = 'mplayer  -quiet '

    def __init__(self,widget,pp_dir):

        self.widget=widget
        self.pp_dir=pp_dir
        
        self.mon=Monitor()
        
        self._process=None
        self.paused=False
        self.muted=False

    def control(self,char):
        if self._process is not None:
            self._process.send(char)

    def mute(self):
        if self.muted is False:
            if self._process is not None:
                self._process.send('m') 
                self.muted = True

    def unmute(self):
        if self.muted is True:
            if self._process is not None:
                self._process.send('m') 
                self.muted = False
        

    def pause(self):
        if self._process is not None:
            self._process.send('p')       
            if not self.paused:
                self.paused = True
            else:
                self.paused=False

    def pause_on(self):
        if self.paused is True:
            return
        if self._process is not None:
            self._process.send('p') 
            self.paused = True

    def pause_off(self):
        if self.paused is False:
            return
        if self._process is not None:
            self._process.send('p') 
            self.paused = False


    def play(self, track, options):
        self._pp(track, options,False)

    def prepare(self, track, options):
        self._pp(track, options,True)
    
    def show(self):
        # unpause to start playing
        if self._process is not None:
            self._process.send('p')
            self.paused = False

    def stop(self):
        if self._process is not None:
            self._process.send('q')

    # kill the subprocess (mplayer). Used for tidy up on exit.
    def terminate(self,reason):
        self.terminate_reason=reason
        if self._process<>None:
            self._process.send('q')
        else:
            self.end_play_signal=True
            
        
    def get_terminate_reason(self):
        return self.terminate_reason
    
   # test of whether _process is running
    def is_running(self):
        return self._process.isalive()     

# ***********************************
# INTERNAL FUNCTIONS
# ************************************

    def _pp(self, track, options,  pause_before_play):
        self.paused=False
        self.start_play_signal = False
        self.end_play_signal=False
        self.terminate_reason=''
        track= "'"+ track.replace("'","'\\''") + "'"
        cmd = MplayerDriver._LAUNCH_CMD +' '+options +" " + track
        self.mon.log(self, "Send command to mplayer: "+ cmd)
        self._process = pexpect.spawn(cmd)
        
        # uncomment to monitor output to and input from mplayer (read pexpect manual)
        fout= file(self.pp_dir + os.sep + 'pp_logs'  + os.sep + 'mplayerlogfile.txt','w')  #uncomment and change sys.stdout to fout to log to a file
        # self._process.logfile_send = sys.stdout  # send just commands to stdout
        self._process.logfile=fout  # send all communications to log file

        if pause_before_play:
            self._process.send('p')
            self.paused = True
            
        # start the thread that is going to monitor sys.stdout. Presumably needs a thread because of blocking

        self._position_thread = Thread(target=self._get_position)
        self._position_thread.start()
            
    def _get_position(self):
        # print 'hang'
        # while True:
                # pass
        self.start_play_signal = True  

        self.audio_position=0.0
        
        while True:
            index = self._process.expect([MplayerDriver._DONE_REXP,
                                          pexpect.TIMEOUT,
                                          pexpect.EOF,
                                          MplayerDriver._STATUS_REXP],
                                         timeout=10)
            # mplayer does not produce regular status messages just 'exit' at end 
            if index == 0:   # nice day
                # print 'nice day'
                self.end_play_signal=True
                break        
            else:
                # matches _STATUS_REXP so audio position
                self.audio_position = 0.0

                sleep(0.05)


