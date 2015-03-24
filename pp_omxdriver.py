import pexpect
import re
import signal
import os

from threading import Thread
from time import sleep
from pp_utils import Monitor

"""
 pyomxplayer from https://github.com/jbaiter/pyomxplayer
 extensively modified by KenT

 omxdriver hides the detail of using the omxplayer command  from videoplayer
 This is meant to be used with videoplayer.py
 Its easy to end up with many copies of omxplayer.bin running if this class is not used with care. use pp_videoplayer.py for a safer interface.
 I found overlapping prepare and show did nor completely reduce the gap between tracks.
 Sometimes, in a test of this, one of my videos ran very fast when it was the second video 

 External commands
 ----------------------------
 __init__ just creates the instance and initialises variables (e.g. omx=OMXPlayer())
 play -  plays a track
 pause/unpause   - toggles pause
 control  - sends controls to omxplayer.bin  while track is playing (use stop and pause instead of q and p)
 stop - stops a video that is playing.
 terminate - Stops a video playing. Used when aborting an application.
 kill - kill of omxplayer when it hasn't terminated at the end of a track.
 
 Advanced:
 load  - processes the track up to where it is ready to display, at this time it pauses.
 show  - plays the video from where 'prepare' left off by resuming from the pause.


Signals
----------
 The following signals are produced while a track is playing
         self.start_play_signal = True when a track is ready to be shown
         self.end_play_signal= True when a track has finished due to stop or because it has come to an end
         self.end_play_reason reports the reason for the end
 Also is_running() tests whether the sub-process running omxplayer is present.

"""

class OMXDriver(object):

    _STATUS_REXP = re.compile(r"M:\s*(-?\d*)\s*V:")
    _DONE_REXP = re.compile(r"have a nice day.*")
    # _DURATION_REXP=re.compile(r"Duration:\s(\d*):(\d*):(\d*)\.(\d*),")
    # _DURATION_REXP=re.compile(r"Duration:\s*([\d]{2}:[\d]{2}:[\d]{2}\.[\d]{2}),")
    _DURATION_REXP=re.compile(r"Duration:.*(\d{2}):(\d{2}):(\d{2}\.\d{2}).*,")
    _LAUNCH_CMD = '/usr/bin/omxplayer -s '  # needs changing if user has installed his own version of omxplayer elsewhere

    _DURATION_CMD = '/usr/bin/omxplayer -i '  # needs changing if user has installed his own version of omxplayer elsewhere

    def __init__(self,widget,pp_dir):

        self.widget=widget
        self.pp_dir=pp_dir
        
        self.mon=Monitor()

        self.paused=False

        self._process=None
        
        # PRELOAD add some initilisation to cope with first iteration of preload state machine
        self.start_play_signal=False
        self.end_play_signal=True
        self.end_play_reason='nice_day'
        self.video_position=0
        self.freeze_at_end_required=False

    def control(self,char):
        self._process.send(char)

    def pause(self,reason):
        # print 'paused ' + reason
        self.mon.log(self,'>pause for end of loading or showing')
        if not self.paused:
            self.paused = True
            chars=self._process.send('p')
            if chars != 1:
                pass
                # print 'pause send failed'
        else:
            # print 'pause failed '+ reason
            pass

    def toggle_pause(self,reason):
        # print 'toggle pause ' + reason
        if not self.paused:
            self.paused = True
        else:
            self.paused=False
        chars=self._process.send('p')
        if chars != 1:
            pass
            # print 'pause send failed'


    def unpause(self,reason):
        # print 'un-paused ' + reason
        if self.paused:
            self.paused = False
            self.mon.log(self,'>unpause for show')
            chars=self._process.send('p')
            if chars != 1:
                # print 'unpause send failed'
                pass
        else:
           # print 'Un-pause failed '+reason
            pass

    def play(self, track, options):
        self._pp(track, options,False)

    def load(self, track, options,duration):
        self.duration=1000000*long(duration)-150000   #was 150000
        self._pp(track, options,True)
    
    def show(self,freeze_at_end_required):
        self.freeze_at_end_required=freeze_at_end_required
        # unpause to start playing
        self.unpause(' at show')

    def stop(self):
        self.mon.log(self,'>stop received')
        if self._process is not None:
            #print self.is_running()
            self._process.send('q')
            #print 'quit suceeeded'
        else:
            # print 'quit failed'
            pass

    # kill the subprocess (omxplayer and omxplayer.bin). Used for tidy up on exit.
    def terminate(self,reason):
        self.terminate_reason=reason
        self.stop()
        
    def get_terminate_reason(self):
        return self.terminate_reason
    

   # test of whether _process is running
    def is_running(self):
        return self._process.isalive()

    # kill off omxplayer when it hasn't terminated at the end of a track.
    # send SIGINT (CTRL C) so it has a chance to tidy up daemons and omxplayer.bin
    def kill(self):
        self._process.kill(signal.SIGINT)



# ***********************************
# INTERNAL FUNCTIONS
# ************************************


    def _pp(self, track, options,  pause_before_play):
        self.pause_before_play=pause_before_play
        self.paused=False
        self.start_play_signal = False
        self.end_play_signal=False
        self.end_play_reason='nothing'
        self.xbefore='nothing'
        self.xafter='nothing'
        self.match=''
        self.terminate_reason=''
        track= "'"+ track.replace("'","'\\''") + "'"
        self.omxplayer_cmd = OMXDriver._LAUNCH_CMD + options +" " + track
        self.mon.log(self, "Send command to omxplayer: "+ self.omxplayer_cmd)
        self._process = pexpect.spawn(self.omxplayer_cmd)

        # uncomment to monitor output to and input from omxplayer.bin (read pexpect manual)
        fout= file(self.pp_dir + os.sep + 'pp_logs'  + os.sep +' omxlogfile.log','w')  #uncomment and change sys.stdout to fout to log to a file
        # self._process.logfile_send = sys.stdout  # send just commands to stdout
        self._process.logfile=fout  # send all communications to log file
         
        # start the thread that is going to monitor output from omxplayer.
        # Presumably needs a thread because of blocking of .expect
        self._position_thread = Thread(target=self._get_position)
        self._position_thread.start()

        # moved for PRELOAD as it is too soon to execute here
##        if pause_before_play:
##            print 'PRELOAD - pause before play'
##            self.pause()

    def _get_position(self):

        self.video_position=0.0


        # PRELOAD  - frozen is true when pause has been sent at the end of preload
        self.frozen=False
        self.end_pause=False
        while True:
            index = self._process.expect([OMXDriver._DONE_REXP,
                                          pexpect.TIMEOUT,
                                          pexpect.EOF,
                                          OMXDriver._STATUS_REXP],
                                         timeout=10)
            if index == 1:     # timeout. omxplayer should not do this
                self.end_play_signal=True
                self.xbefore=self._process.before
                self.xafter=self._process.after
                self.match=self._process.match
                self.end_play_reason='timeout'
                break
            
            elif index == 2:       # 2 eof. omxplayer should not send this
                # eof detected
                self.end_play_signal=True
                self.xbefore=self._process.before
                self.xafter=self._process.after
                self.match=self._process.match
                self.end_play_reason='eof'
                break
            
            elif index== 0:    #0 is nice day
                # Have a nice day detected, too late to pause
                # print 'OMXDRIVER - sends have a nice day'
                self.end_play_signal=True
                self.xbefore=self._process.before
                self.xafter=self._process.after
                self.match=self._process.match
                self.end_play_reason='nice_day'
                break
            
            else:
                #  - 3 matches _STATUS_REXP so get time stamp
                self.video_position = float(self._process.match.group(1))

                # if timestamp is near the end then pause 
                if self.freeze_at_end_required is True and self.video_position>self.duration:    #microseconds
                    if self.end_pause is False:
                        # print 'OMXDRIVER - sends pause at end'
                        self.pause(' at end detected')
                        self.end_pause=True
                        self.end_play_signal=True
                        self.end_play_reason='pause_at_end'
                else:
                    # need to do the pausing for preload after first timestamp is received
                    if self.pause_before_play is True and self.frozen is False:
                        self.start_play_signal = True  
                        self.pause('after preload')
                        self.frozen=True

 
            # ????? should sleep be indented
            # sleep is OK here as it is a seperate thread. self.widget.after has funny effects as its not in the main thread.
            sleep(0.05)   # stats output rate seem to be about 170mS.


    def get_duration(self,track):

        self.duration_signal=False
        self.duration_reason=''
        self.measured_duration=0.0
        track= "'"+ track.replace("'","'\\''") + "'"
        duration_cmd = OMXDriver._DURATION_CMD + track
        # self.mon.log(self, "Send command to omxplayer: "  + duration_cmd)
        self._process = pexpect.spawn(duration_cmd)

##        # uncomment next 2 lines to monitor output to and input from omxplayer.bin (read pexpect manual)
##        fout= file('durationlogfile.txt','w')  #uncomment and change sys.stdout to fout to log to a file
##        self._process.logfile=fout  # send all communications to log file
        
        # self._process.logfile_send = sys.stdout  # send just commands to stdout
         
        # start the thread that is going to monitor output from omxplayer.
        # Presumably needs a thread because of blocking of .expect
        self._duration_thread = Thread(target=self._get_duration)
        self._duration_thread.start()

        

    def _get_duration(self):
        while True:
            index = self._process.expect([OMXDriver._DURATION_REXP,
                                          OMXDriver._DONE_REXP,
                                          pexpect.TIMEOUT,
                                          pexpect.EOF],
                                         timeout=10)
            if index == 0:
                #  - 0 matches _DURATION_REXP so get duration
                hour,minute,second= self._process.match.groups()
                # print self._process.match.group(1) + ':'+ self._process.match.group(2) +':' + self._process.match.group(3)
                self.measured_duration=float(3600*hour)+float(60*minute)+float(second)
                # self.duration_signal=True
                self.duration_reason='normal'
                # break

            elif index==1:    # nice day
                self.duration_signal=True
                self.xbefore=self._process.before
                self.xafter=self._process.after
                self.match=self._process.match
                self.duration_reason='nice_day'
                break
                
            elif index == 2:     # timeout. omxplayer should not do this
                self.duration_signal=True
                self.xbefore=self._process.before
                self.xafter=self._process.after
                self.match=self._process.match
                self.duration_reason='timeout'
                break
            
            elif index == 3:       # eof. omxplayer should not send this
                # eof detected
                self.duration_signal=True
                self.xbefore=self._process.before
                self.xafter=self._process.after
                self.match=self._process.match
                self.duration_reason='eof'
                break
            
            else:
  
                # sleep is OK here as it is a seperate thread. self.widget.after has funny effects as its not in the main thread.
                sleep(0.05)   # stats output rate seem to be about 170mS.


