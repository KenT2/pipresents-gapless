import signal
import os
import dbus
import subprocess
from threading import Thread
from time import sleep,time
from pp_utils import Monitor

"""
12/6/2016 - rewrite to use dbus

 omxdriver hides the detail of using the omxplayer command  from videoplayer
 This is meant to be used with videoplayer.py
 Its easy to end up with many copies of omxplayer.bin running if this class is not used with care. use pp_videoplayer.py for a safer interface.

 External commands
 ----------------------------
 __init__ just creates the instance and initialises variables (e.g. omx=OMXDriver())
  load  - processes the track up to where it is ready to display, at this time it pauses.
 show  - plays the video from where 'prepare' left off by resuming from the pause.
 play -  plays a track (not used by gapless)
 pause/unpause   -  pause on/off
 toggle_pause  - toggles pause
 control  - sends controls to omxplayer.bin  while track is playing (use stop and pause instead of q and p)
 stop - stops a video that is playing.
 terminate - Stops a video playing. Used when aborting an application.
 kill - kill of omxplayer when it hasn't terminated at the end of a track.
 
Signals
----------
 The following signals are produced while a track is playing
         self.start_play_signal = True when a track is ready to be shown
         self.end_play_signal= True when a track has finished due to stop or because it has come to an end
         self.end_play_reason reports the reason for the end
 Also is_running() tests whether the sub-process running omxplayer is present.

"""

class OMXDriver(object):
    _LAUNCH_CMD = '/usr/bin/omxplayer --no-keys '  # needs changing if user has installed his own version of omxplayer elsewhere
    KEY_MAP =   { '-': 17, '+': 18, '=': 18} # add more keys here, see popcornmix/omxplayer github

    def __init__(self,widget,pp_dir):

        self.widget=widget
        self.pp_dir=pp_dir
        
        self.mon=Monitor()

        self.start_play_signal=False
        self.end_play_signal=False
        self.end_play_reason='nothing'
        self.duration=0
        self.video_position=0
        
        self.pause_at_end_required=False
        self.paused_at_end=False
        
        self.pause_before_play_required=True
        self.paused_at_start=False

        self.paused=False      

        self.terminate_reason=''

        #  dbus and subprocess
        self._process=None
        self.__iface_root=None
        self.__iface_props = None
        self.__iface_player = None

        # legacy
        self.xbefore=''
        self.xafter=''



    def load(self, track, options,caller):
        self.caller=caller
        track= "'"+ track.replace("'","'\\''") + "'"

        self.dbus_user = os.environ["USER"]

        self.dbus_name = "org.mpris.MediaPlayer2.omxplayer"+str(int(time()*10))
        
        self.omxplayer_cmd = OMXDriver._LAUNCH_CMD + options + " --dbus_name '"+ self.dbus_name + "' " + track
        # print self.dbus_user, self.dbus_name
        # print self.omxplayer_cmd
        self.mon.log(self, "Send command to omxplayer: "+ self.omxplayer_cmd)
        self._process=subprocess.Popen(self.omxplayer_cmd,shell=True,stdout=file('/dev/null','wa'),stderr=file('/dev/null','wa'))
        # stdout=file('/dev/null','wa'),stderr=file('/dev/null','wa')
        self.pid=self._process.pid

        # wait for omxplayer to start
        tries=0
        while tries<400:
            # print 'trying',tries
            success=self.__dbus_connect()
            tries+=1
            sleep (0.1)
            if success is True: break
            
        if success is False:
            self.end_play_signal=True
            self.end_play_reason='Failed to connect to omxplayer DBus'
            return

        self.mon.log(self,'connected to omxplayer dbus ' + str(success))
            
        self.start_play_signal = True
        if self.pause_before_play_required is True and self.paused_at_start is False:
            self.pause('after load')
            self.paused_at_start=True

        # get duration of the track in microsecs
        sucess,duration=self.get_duration()
        if success is False:
            self.duration=0
            self.end_play_signal=True
            self.end_play_reason='Failed to read duration - Not connected to omxplayer DBus'
        else:
            self.duration=duration-350000
            
            # start the thread that is going to monitor output from omxplayer.
            self._position_thread = Thread(target=self._monitor_status)
            self._position_thread.start()


    def _monitor_status(self):
        
        while True:
            retcode=self._process.poll()

            # print 'in loop', self.pid, retcode
            if retcode is not None:
                # print 'process not running', retcode, self.pid
                # process is not running because quit or natural end
                self.end_play_signal=True
                self.end_play_reason='nice_day'
                break
            else:
                # test position ony when prsecc is running, could have race condition
                if self.paused_at_end is False:
                    # test position only when not paused for the end, in case process is dead
                    success, video_position = self.get_position()
                    if success is False:
                        pass # failure can happen because track has ended and process ended. Don't change video position
                    else:
                        self.video_position=video_position
                        # if timestamp is near the end then pause
                        if self.pause_at_end_required is True and self.video_position>self.duration:    #microseconds
                            self.pause(' at end of track')
                            self.paused_at_end=True
                            self.end_play_signal=True
                            self.end_play_reason='pause_at_end'
            sleep(0.05)                        


    
    def show(self,freeze_at_end_required):
        self.pause_at_end_required=freeze_at_end_required
        # unpause to start playing
        self.unpause(' to start showing')

        
    def control(self,char):

        val = OMXDriver.KEY_MAP[char]
        self.mon.log(self,'>control received and sent to omxplayer ' + str(self.pid))
        if self.is_running():
            try:
                self.__iface_player.Action(dbus.Int32(val))
            except dbus.exceptions.DBusException:
                self.mon.warn(self,'Failed to send control - dbus exception')
                return
        else:
            self.mon.warn(self,'Failed to send control - process not running')
            return
        

    def pause(self,reason):
        self.mon.log(self,'pause received '+reason)
        if not self.paused:
            self.paused = True
            self.mon.log(self,'not paused so send pause '+reason)
            if self.is_running():
                try:
                    self.__iface_player.Pause()
                except dbus.exceptions.DBusException:
                    self.mon.warn(self,'Failed to send pause - dbus exception')
                    return
            else:
                self.mon.warn(self,'Failed to send pause - process not running')
                return



    def toggle_pause(self,reason):
        self.mon.log(self,'toggle pause received '+ reason)
        if not self.paused:
            self.paused = True
        else:
            self.paused=False
        if self.is_running():
            try:
                self.__iface_player.Pause()
            except dbus.exceptions.DBusException:
                self.mon.warn(self,'Failed to toggle pause - dbus exception')
                return
        else:
            self.mon.warn(self,'Failed to toggle pause - process not running')
            return



    def unpause(self,reason):
        self.mon.log(self,'Unpause received '+ reason)
        if self.paused:
            self.paused = False
            self.mon.log(self,'Is paused so Track unpaused '+ reason)
            if self.is_running():
                try:
                    self.__iface_player.Pause()
                except dbus.exceptions.DBusException:
                    self.mon.warn(self,'Failed to send pause - dbus exception')
                    return
            else:
                self.mon.warn(self,'Failed to send pause - process not running')
                return


    def stop(self):
        self.mon.log(self,'>stop received and quit sent to omxplayer ' + str(self.pid))
        if self.is_running():
            try:
                self.__iface_root.Quit()
            except dbus.exceptions.DBusException:
                self.mon.warn(self,'Failed to quit - dbus exception')
                return
        else:
            self.mon.warn(self,'Failed to quit - process not running')
            return


    # kill the subprocess (omxplayer and omxplayer.bin). Used for tidy up on exit.
    def terminate(self,reason):
        self.terminate_reason=reason
        self.stop()
        
    def get_terminate_reason(self):
        return self.terminate_reason
    

   # test of whether _process is running
    def is_running(self):
        retcode=self._process.poll()
        # print 'is alive', retcode
        if retcode is None:
            return True
        else:
            return False



    # kill off omxplayer when it hasn't terminated at the end of a track.
    # send SIGINT (CTRL C) so it has a chance to tidy up daemons and omxplayer.bin
    def kill(self):
        if self.is_running():
            self._process.send_signal(signal.SIGINT)


    def get_position(self):
        """Return the current position"""
        if self.is_running():
            try:
                micros = self.__iface_props.Position()
                return True,micros
            except dbus.exceptions.DBusException:
                 return False,-1               
        else:
            return False,-1

    def get_duration(self):
        """Return the total length of the playing media"""
        if self.is_running():
            try:
                micros = self.__iface_props.Duration()
                return True,micros
            except dbus.exceptions.DBusException:
                return False,-1
        else:
            return False,-1




    # *********************
    # connect to dbus
    # *********************
    def __dbus_connect(self):
        # read the omxplayer dbus data from files generated by omxplayer
        bus_address_filename = "/tmp/omxplayerdbus.{}".format(self.dbus_user)
        bus_pid_filename = "/tmp/omxplayerdbus.{}.pid".format(self.dbus_user)
        try:
            with open(bus_address_filename, "r") as f:
                bus_address = f.read().rstrip()
            with open(bus_pid_filename, "r") as f:
                bus_pid = f.read().rstrip()
        except IOError:
            self.mon.trace(self,"Waiting for D-Bus session for user {}. Is omxplayer running under this user?".format(self.dbus_user))
            return False

        # looks like this saves some file opens as vars are used instead of files above
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = bus_address
        os.environ["DBUS_SESSION_BUS_PID"] = bus_pid
        session_bus = dbus.SessionBus()
        try:
            omx_object = session_bus.get_object(self.dbus_name, "/org/mpris/MediaPlayer2", introspect=False)
            self.__iface_root = dbus.Interface(omx_object, "org.mpris.MediaPlayer2")
            self.__iface_props = dbus.Interface(omx_object, "org.freedesktop.DBus.Properties")
            self.__iface_player = dbus.Interface(omx_object, "org.mpris.MediaPlayer2.Player")
        except dbus.exceptions.DBusException as ex:
            self.mon.trace(self,"Waiting for dbus connection to omxplayer: {}".format(ex.get_dbus_message()))
            return False
        return True

