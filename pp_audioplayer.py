import os
from pp_mplayerdriver import MplayerDriver
from pp_player import Player

class AudioPlayer(Player):
    """       
            plays an audio track using mplayer against a coloured backgroud and image
            track can be paused and interrupted
    """

# audio mixer matrix settings
    _LEFT = "channels=2:1:0:0:1:1"
    _RIGHT = "channels=2:1:0:1:1:0"
    _STEREO = "channels=2"

# ***************************************
# EXTERNAL COMMANDS
# ***************************************

    def __init__(self,
                 show_id,
                 showlist,
                 root,
                 canvas,
                 show_params,
                 track_params,
                 pp_dir,
                 pp_home,
                 pp_profile,
                 end_callback,
                 command_callback):

        # initialise items common to all players   
        Player.__init__( self,
                         show_id,
                         showlist,
                         root,
                         canvas,
                         show_params,
                         track_params ,
                         pp_dir,
                         pp_home,
                         pp_profile,
                         end_callback,
                         command_callback)


        self.mon.trace(self,'')
        # get duration limit (secs ) from profile
        if self.show_params['type'] in ('liveshow','artliveshow'):
            duration_text=''
        else:
            duration_text= self.track_params['duration']
        if duration_text != '':
            self.duration_limit= 20 * int(duration_text)
        else:
            self.duration_limit=-1
        # print self.duration_limit                   
        # get audio device from profile.
        if  self.track_params['mplayer-audio'] != "":
            self.mplayer_audio= self.track_params['mplayer-audio']
        else:
            self.mplayer_audio= self.show_params['mplayer-audio']
            
        # get audio volume from profile.
        if  self.track_params['mplayer-volume'] != "":
            mplayer_volume= self.track_params['mplayer-volume'].strip()
        else:
            mplayer_volume= self.show_params['mplayer-volume'].strip()
        mplayer_volume_int=int(mplayer_volume)+100    #60 for Jessie
        self.volume_option= '-volume ' + str(mplayer_volume_int)

        # get speaker from profile
        if  self.track_params['audio-speaker'] != "":
            self.audio_speaker= self.track_params['audio-speaker']
        else:
            self.audio_speaker= self.show_params['audio-speaker']

        if self.audio_speaker == 'left':
            self.speaker_option=AudioPlayer._LEFT
        elif self.audio_speaker == 'right':
            self.speaker_option=AudioPlayer._RIGHT
        else:
            self.speaker_option=AudioPlayer._STEREO

        if self.track_params['mplayer-other-options'] != '':
            self.mplayer_other_options= self.track_params['mplayer-other-options']
        else:
            self.mplayer_other_options= self.show_params['mplayer-other-options']

        if self.track_params['pause-timeout'] != '':
            pause_timeout_text= self.track_params['pause-timeout']
        else:
            pause_timeout_text= self.show_params['pause-timeout']

        if pause_timeout_text.isdigit():
            self.pause_timeout= int(pause_timeout_text)
        else:
            self.pause_timeout=0

        # initialise the state and signals      
        self.tick_timer=None
        self.quit_signal=False
        self.play_state='initialised'
        self.waiting=False
        self.pause_timer=None

        
    # LOAD - creates and mplayer instance, loads a track and then pause
    def load(self,track,loaded_callback,enable_menu):
        # instantiate arguments
        self.track=track
        self.loaded_callback=loaded_callback   #callback when loaded

        self.mon.trace(self,'')

        # do common bits of  load
        Player.pre_load(self)
        
        # load the plugin, this may modify self.track and enable the plugin drawign to canvas
        if self.track_params['plugin'] != '':
            status,message=self.load_plugin()
            if status == 'error':
                self.mon.err(self,message)
                self.play_state='load-failed'
                if self.loaded_callback is not  None:
                    self.loaded_callback('error',message)
                    return

        # load the images and text
        status,message=self.load_x_content(enable_menu)
        if status == 'error':
            self.mon.err(self,message)
            self.play_state='load-failed'
            if self.loaded_callback is not  None:
                self.loaded_callback('error',message)
                return

        if track !='' and self.duration_limit!=0 and not os.path.exists(track):
            self.mon.err(self,"Track file not found: "+ track)
            self.play_state='load-failed'
            if self.loaded_callback is not  None:
                self.loaded_callback('error','track file not found: ' + track)
                return

        # just create instance of mplayer don't bother with any pre-load
        self.mplayer=MplayerDriver(self.canvas,self.pp_dir)
        self.play_state='loaded'
        self.mon.log(self,"<Track loaded from show Id: "+ str(self.show_id))
        if self.loaded_callback is not None:
            self.loaded_callback('loaded','audio track loaded')


    def unload(self):
        self.mon.trace(self,'')
        self.mplayer=None
        self.play_state='unloaded'


    
    def show(self,ready_callback,finished_callback,closed_callback):
                       
        # instantiate arguments
        self.ready_callback=ready_callback         # callback when ready to show video
        self.finished_callback=finished_callback         # callback when finished showing
        self.closed_callback=closed_callback
        self.mon.trace(self,'')

        # do animation begin etc. 
        Player.pre_show(self)

        
        # start playing the track.
        self.mon.log(self,">start playing track: "+ str(self.show_id))
        if self.duration_limit != 0:
            self.start_play_state_machine_show()
        else:
            self.mplayer=None
            if self.closed_callback is not None:
                self.closed_callback('normal','end with zero duration')


    # CLOSE - nothing to do in audioplayer - x content is removed by ready callback
    def close(self,closed_callback):
        self.closed_callback=closed_callback
        self.mon.log(self,">close received from show Id: "+ str(self.show_id))
        self.mon.trace(self,'')
        self.start_play_state_machine_close()


    def input_pressed(self,symbol):
        if symbol[0:6] == 'mplay-':
            self.control(symbol[6])
        elif symbol  == 'unmute':
            self.unmute()
        elif symbol  == 'mute':
            self.mute()
        elif symbol == 'pause-on':
            self.pause_on()
        elif symbol == 'pause-off':
            self.pause_off()
        elif symbol == 'pause':
            self.pause()
        elif symbol == 'stop':
            self.stop()


    def mute(self):
        if self.play_state == 'showing' and self.track != '':
            self.mplayer.mute()
            return True
        else:
            self.mon.log(self,"!<mute rejected " + self.play_state)
            return False

    def unmute(self):
        if self.play_state == 'showing' and self.track != '':
            self.mplayer.unmute()
            return True
        else:
            self.mon.log(self,"!<unmute rejected " + self.play_state)
            return False


    # pause on
    def pause_on(self):
        if self.play_state == 'showing' and self.track != '':
            self.mplayer.pause_on()
            if self.mplayer.paused is True and self.pause_timeout>0:
                # kick off the pause teimeout timer
                print "!!pause on"
                self.pause_timer=self.canvas.after(self.pause_timeout*1000,self.pause_timeout_callback)
            return True
        else:
            self.mon.log(self,"!<pause on rejected")
            return False

    # pause off
    def pause_off(self):
        if self.play_state == 'showing' and self.track != '':
            self.mplayer.pause_off()
            if self.mplayer.paused is False:
                print "!!pause off"
                # cancel the pause timer
                if self.pause_timer != None:
                    self.canvas.after_cancel(self.pause_timer)
                    self.pause_timer=None
            return True
        else:
            self.mon.log(self,"!<pause off rejected")
            return False


    # toggle pause
    def pause(self):
        if self.play_state == 'showing' and self.track != '':
            self.mplayer.pause()
            if self.mplayer.paused is True and self.pause_timeout>0:
                # kick off the pause teimeout timer
                print "!!toggle pause on"
                self.pause_timer=self.canvas.after(self.pause_timeout*1000,self.pause_timeout_callback)
            else:
                # cancel the pause timer
                if self.pause_timer != None:
                    print "!!toggle pause off"
                    self.canvas.after_cancel(self.pause_timer)
                    self.pause_timer=None
            return True
        else:
            self.mon.log(self,"!<pause rejected")
            return False

    def pause_timeout_callback(self):
        print "!!callback pause off"
        self.pause_off()
        self.pause_timer=None

        
    # other control when playing, not currently used
    def control(self,char):
        if self.play_state == 'showing' and self.track != ''and char not in ('q'):
            self.mon.log(self,"> send control to mplayer: "+ char)
            self.mplayer.control(char)
            return True
        else:
            self.mon.log(self,"!<control rejected")
            return False

    # respond to normal stop
    def stop(self):
        # cancel the pause timer
        if self.pause_timer != None:
            self.canvas.after_cancel(self.pause_timer)
            self.pause_timer=None
 
        # send signal to stop the track to the state machine
        self.mon.log(self,">stop received")
        if self.play_state in ('starting','showing'):
            self.quit_signal=True

         
      
# ***************************************
#  sequencing
# ***************************************

    """
        self. play_state controls the playing sequence, it has the following values.
         - initialised - _init__ done
         - loaded - mplayer instance created, no pre-load for audio tracks
         - starting - mplayer process is running but is not yet able to receive controls
         - showing - playing a track, controls can be sent
         - closing - mplayer is doing its termination, controls cannot be sent
         - waiting - audio file has finished, witing for duration
         - closed - the mplayer process is closed after a track is played or duration is exceeded
    """

 
    def start_play_state_machine_show(self):

                
        if self.play_state == 'loaded':
            # initialise all the state machine variables
            self.duration_count = 0

            # select the sound device
            if self.mplayer_audio != "":
                if self.mplayer_audio == 'hdmi':
                    os.system("amixer -q -c 0 cset numid=3 2")
                else:
                    os.system("amixer -q -c 0 cset numid=3 1")   
            # play the track               
            options = ' '+ self.mplayer_other_options + ' '+  self.volume_option + ' -af '+ self.speaker_option + ' '
            if self.track != '':
                self.mplayer.play(self.track,options)
                self.mon.log (self,'Playing audio track from show Id: '+ str(self.show_id))
                self.play_state='starting'
            else:
                # no track to play so cannot rely on mplayer starting signal
                self.play_state='showing'
            # and start polling for state changes and count duration
            self.tick_timer=self.canvas.after(50, self.play_state_machine)
        else:
            self.mon.fatal(self,'illegal state in show method ' + self.play_state)
            self.play_state='show-failed'
            if self.finished_callback is not None:
                self.finished_callback('error','illegal state in show method ' + self.play_state)


    def start_play_state_machine_close(self):
        self.quit_signal=True
        # print 'start close state machine close',self.play_state
        self.tick_timer=self.canvas.after(1, self.play_state_machine)



    def play_state_machine(self):
        self.duration_count+=1
        # self.mon.log(self,"      State machine: " + self.play_state)           
        if self.play_state == 'closed':
            # self.mon.log(self,"   State machine: " + self.play_state)
            pass


        elif self.play_state == 'starting':
            # self.mon.log(self,"      State machine: " + self.play_state)
            
            # if mplayer has started and can accept runtime commands change to showing state
            if self.mplayer.start_play_signal is True:
                self.mon.log(self,"            <start play signal received from mplayer")
                self.mplayer.start_play_signal=False
                self.play_state='showing'
                self.mon.log(self,"      State machine: go to showing")
            self.tick_timer=self.canvas.after(50, self.play_state_machine)

        elif self.play_state == 'showing':

            if self.waiting is True:
                # self.mon.log(self,"      State machine: " + self.play_state + ' ' + self.waiting)
                if self.quit_signal is True or (self.duration_limit>0 and self.duration_count>self.duration_limit):
                    self.mon.log(self,"      Service stop required signal or timeout from wait")
                    self.quit_signal=False
                    self.waiting=False
                    self.play_state = 'closed'
                    if self.closed_callback is not None:
                        self.closed_callback('normal','wait is finished')
                else:
                    self.tick_timer=self.canvas.after(50, self.play_state_machine)


            # self.mon.log(self,"      State machine: " + self.play_state)
            # service any queued stop signals
            elif self.quit_signal is True or (self.duration_limit>0 and self.duration_count>self.duration_limit):
                self.mon.log(self,"      Service stop required signal or timeout")
                # self.quit_signal=False
                if self.track != '':
                    self.mplayer.stop()
                    self.play_state = 'closing'
                    self.mon.log(self,"      State machine: closing due to quit or duration with track to play")
                    self.tick_timer=self.canvas.after(50, self.play_state_machine)
                else:
                    self.mon.log(self,"      State machine: closed due to quit or duration with NO track to play")
                    self.play_state='closed'
                    if self.closed_callback is not None:
                        self.closed_callback('normal','user quit or duration NO track to play')

            # mplayer reports it is finishing at end of track so change to ending state
            elif self.track != '' and self.mplayer.end_play_signal:                    
                self.mon.log(self,"            <end play signal received")
                self.mon.log(self,"            <end detected at: " + str(self.mplayer.audio_position))
                self.play_state = 'closing'
                self.tick_timer=self.canvas.after(50, self.play_state_machine)
            else:
                self.tick_timer=self.canvas.after(50, self.play_state_machine)


        elif self.play_state == 'closing':
            # self.mon.log(self,"      State machine: " + self.play_state)
            # if spawned process has closed can change to closed state
            if self.mplayer.is_running()  is False:
                self.mon.log(self,"            <mplayer process is dead")
                # if still need to wait for duration change to waiting state
                if self.duration_limit>0 and self.duration_count<self.duration_limit:
                    self.play_state= 'showing'
                    self.waiting=True
                    self.tick_timer=self.canvas.after(50, self.play_state_machine)
                else:
                    self.play_state = 'closed'
                    if self.closed_callback is not None:
                        self.closed_callback('normal','mplayer dead')

            else:
                self.tick_timer=self.canvas.after(50, self.play_state_machine)
                




                                            




   

