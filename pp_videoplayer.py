# -*- coding: utf-8 -*-
import os
from pp_omxdriver import OMXDriver
from pp_player import Player
from pp_utils import parse_rectangle

class VideoPlayer(Player):
    """
    plays a track using omxplayer
    _init_ iniitalises state and checks resources are available.
    use the returned instance reference in all other calls.
    At the end of the path (when closed) do not re-use, make instance= None and start again.
    States - 'initialised' when done successfully
    Initialisation is immediate so just returns with error code.
    """
    
    def __init__(self,
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
        # print ' !!!!!!!!!!!videoplayer init'
        self.mon.trace(self,'')

        # get player parameters
        if self.track_params['omx-audio'] != "":
            self.omx_audio= self.track_params['omx-audio']
        else:
            self.omx_audio= self.show_params['omx-audio']
        if self.omx_audio != "": self.omx_audio= "-o "+ self.omx_audio
        
        if self.track_params['omx-volume'] != "":
            self.omx_volume= self.track_params['omx-volume']
        else:
            self.omx_volume= self.show_params['omx-volume']
        if self.omx_volume != "":
            self.omx_volume= int(self.omx_volume)*100

        if self.track_params['omx-window'] != '':
            self.omx_window= self.track_params['omx-window']
        else:
            self.omx_window= self.show_params['omx-window']

        if self.track_params['omx-other-options'] != '':
            self.omx_other_options= self.track_params['omx-other-options']
        else:
            self.omx_other_options= self.show_params['omx-other-options']

        if self.track_params['freeze-at-start'] != '':
            self.freeze_at_start= self.track_params['freeze-at-start']
        else:
            self.freeze_at_start= self.show_params['freeze-at-start']

        if self.track_params['freeze-at-end'] != '':
            freeze_at_end_text= self.track_params['freeze-at-end']
        else:
            freeze_at_end_text= self.show_params['freeze-at-end']


        if freeze_at_end_text == 'yes':
            self.freeze_at_end_required=True
        else:
            self.freeze_at_end_required=False
            

        if self.track_params['seamless-loop'] == 'yes':
            self.seamless_loop=' --loop '
        else:
            self.seamless_loop=''

        if self.track_params['pause-timeout'] != '':
            pause_timeout_text= self.track_params['pause-timeout']
        else:
            pause_timeout_text= self.show_params['pause-timeout']

        if pause_timeout_text.isdigit():
            self.pause_timeout= int(pause_timeout_text)
        else:
            self.pause_timeout=0
            
            
        # initialise video playing state and signals
        self.quit_signal=False
        self.unload_signal=False
        self.play_state='initialised'
        self.frozen_at_end=False
        self.pause_timer=None

    # LOAD - creates and omxplayer instance, loads a track and then pause
    def load(self,track,loaded_callback,enable_menu):  
        # instantiate arguments
        self.track=track
        self.loaded_callback=loaded_callback   #callback when loaded
        # print '!!!!!!!!!!! videoplayer load',self.track
        self.mon.log(self,"Load track received from show Id: "+ str(self.show_id) + ' ' +self.track)
        self.mon.trace(self,'')

        # do common bits of  load
        Player.pre_load(self)           

        # set up video window
        status,message,command,has_window,x1,y1,x2,y2= self.parse_video_window(self.omx_window)
        if status  == 'error':
            self.mon.err(self,'omx window error: ' + message + ' in ' + self.omx_window)
            self.play_state='load-failed'
            if self.loaded_callback is not  None:
                self.loaded_callback('error','omx window error: ' + message + ' in ' + self.omx_window)
                return
        else:
            if has_window is True:
                self.omx_window_processed= '--win " '+ str(x1) +  ' ' + str(y1) + ' ' + str(x2) + ' ' + str(y2) + ' " '
            else:
                self.omx_window_processed=''

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


        if not os.path.exists(track):
            self.mon.err(self,"Track file not found: "+ track)
            self.play_state='load-failed'
            if self.loaded_callback is not  None:
                self.loaded_callback('error','track file not found: '+ track)
                return

        self.omx=OMXDriver(self.canvas,self.pp_dir)
        self.start_state_machine_load(self.track)



     # SHOW - show a track      
    def show(self,ready_callback,finished_callback,closed_callback):
        # print "!!!! videoplayer show"             
        # instantiate arguments
        self.ready_callback=ready_callback         # callback when ready to show video
        self.finished_callback=finished_callback         # callback when finished showing
        self.closed_callback=closed_callback

        self.mon.trace(self,'')

        #  do animation at start etc.
        Player.pre_show(self)

        # start show state machine
        self.start_state_machine_show()


    # UNLOAD - abort a load when omplayer is loading or loaded
    def unload(self):
        self.mon.trace(self,'')
        
        self.mon.log(self,">unload received from show Id: "+ str(self.show_id))
        self.start_state_machine_unload()


    # CLOSE - quits omxplayer from 'pause at end' state
    def close(self,closed_callback):
        self.mon.trace(self,'')
        self.mon.log(self,">close received from show Id: "+ str(self.show_id))
        self.closed_callback=closed_callback
        self.start_state_machine_close()



    def input_pressed(self,symbol):
        if symbol[0:4] == 'omx-':
            self.control(symbol[4])
        elif symbol  == 'pause':
            self.pause()
        elif symbol  == 'go':
            self.go()
        elif symbol  == 'unmute':
            self.unmute()
        elif symbol  == 'mute':
            self.mute()
        elif symbol  == 'pause-on':
            self.pause_on()    
        elif symbol  == 'pause-off':
            self.pause_off()
        elif symbol == 'stop':
            self.stop()


    # respond to normal stop
    def stop(self):
        self.mon.log(self,">stop received from show Id: "+ str(self.show_id))
        # cancel the pause timer
        if self.pause_timer != None:
            self.canvas.after_cancel(self.pause_timer)
            self.pause_timer=None
 
        # send signal to freeze the track - causes either pause or quit depends on freeze at end
        if self.freeze_at_end_required is True:
            if self.play_state == 'showing' and self.frozen_at_end is False:
                self.frozen_at_end=True
                # pause the track
                self.omx.pause('freeze at end from user stop')
                self.quit_signal=True
                # and return to show so it can end  the track and the video in track ready callback
##                if self.finished_callback is not None:
##                    # print 'finished from stop'
##                    self.finished_callback('pause_at_end','pause at end')
            else:
                self.mon.log(self,"!<stop rejected")
        else:
            # freeze not required and its showing just stop the video
            if self.play_state=='showing':
                self.quit_signal=True
            else:
                self.mon.log(self,"!<stop rejected")                

    def mute(self):
        self.mon.log(self,">mute received from show Id: "+ str(self.show_id))
        if self.play_state  == 'showing' and self.frozen_at_end is False and self.omx.paused_at_start == 'done':
            self.omx.mute()
            return True
        else:
            self.mon.log(self,"!<mute rejected " + self.play_state)
            return False

    def unmute(self):
        self.mon.log(self,">unmute received from show Id: "+ str(self.show_id))
        if self.play_state  == 'showing' and self.frozen_at_end is False and self.omx.paused_at_start == 'done':
            self.omx.unmute()
            return True
        else:
            self.mon.log(self,"!<unmute rejected " + self.play_state)
            return False

    # toggle pause
    def pause(self):
        self.mon.log(self,">toggle pause received from show Id: "+ str(self.show_id))
        if self.play_state  == 'showing' and self.frozen_at_end is False and self.omx.paused_at_start == 'done':
            self.omx.toggle_pause('user')
            if self.omx.paused is True and self.pause_timeout>0:
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
            self.mon.log(self,"!<pause rejected " + self.play_state)
            return False

    def pause_timeout_callback(self):
        print "!!callback pause off"
        self.pause_off()
        self.pause_timer=None

    # pause on
    def pause_on(self):
        self.mon.log(self,">pause on received from show Id: "+ str(self.show_id))
        if self.play_state  == 'showing' and self.frozen_at_end is False and self.omx.paused_at_start == 'done':
            self.omx.pause_on()
            if self.omx.paused is True and self.pause_timeout>0:
                # kick off the pause teimeout timer
                print "!!pause on"
                self.pause_timer=self.canvas.after(self.pause_timeout*1000,self.pause_timeout_callback)
            return True
        else:
            self.mon.log(self,"!<pause on rejected " + self.play_state)
            return False

    # pause off
    def pause_off(self):
        self.mon.log(self,">pause off received from show Id: "+ str(self.show_id))
        if self.play_state  == 'showing' and self.frozen_at_end is False and self.omx.paused_at_start == 'done':
            self.omx.pause_off()
            if self.omx.paused is False:
                print "!!pause off"
                # cancel the pause timer
                if self.pause_timer != None:
                    self.canvas.after_cancel(self.pause_timer)
                    self.pause_timer=None
            return True
        else:
            self.mon.log(self,"!<pause off rejected " + self.play_state)
            return False

    # go after freeze at start
    def go(self):
        self.mon.log(self,">go received from show Id: "+ str(self.show_id))
        if self.play_state  == 'showing' and self.omx.paused_at_start == 'True':
            self.omx.go()
            return True
        else:
            self.mon.log(self,"!<go rejected " + self.play_state)
            return False
        
    # other control when playing
    def control(self,char):
        if self.play_state == 'showing' and self.frozen_at_end is False and self.omx.paused_at_start == 'done' and char not in ('q'):
            self.mon.log(self,"> send control to omx: "+ char)
            self.omx.control(char)
            return True
        else:
            self.mon.log(self,"!<control rejected")
            return False



# ***********************
# track showing state machine
# **********************

    """
    STATES OF STATE MACHINE
    Threre are ongoing states and states that are set just before callback

    >init - Create an instance of the class
    <On return - state = initialised   -  - init has been completed, do not generate errors here

    >load
        Fatal errors should be detected in load. If so  loaded_callback is called with 'load-failed'
         Ongoing - state=loading - load called, waiting for load to complete   
    < loaded_callback with status = normal
         state=loaded - load has completed and video paused before first frame      
    <loaded_callback with status=error
        state= load-failed - omxplayer process has been killed because of failure to load   

    On getting the loaded_callback with status=normal the track can be shown using show
    Duration obtained from track should always cause pause_at_end. if not please tell me as the fudge factor may need adjusting.


    >show
        show assumes a track has been loaded and is paused.
       Ongoing - state=showing - video is showing 
    <finished_callback with status = pause_at_end
            state=showing but frozen_at_end is True
    <closed_callback with status= normal
            state = closed - video has ended omxplayer has terminated.


    On getting finished_callback with status=pause_at end a new track can be shown and then use close to quit the video when new track is ready
    On getting closed_callback with status=  nice_day omxplayer closing should not be attempted as it is already closed
    Do not generate user errors in Show. Only generate system erros such as illegal state abd then use end()

    >close
       Ongoing state - closing - omxplayer processes are dying due to quit sent
    <closed_callback with status= normal - omxplayer is dead, can close the track instance.

    >unload
        Ongoing states - start_unload and unloading - omxplayer processes are dying due to quit sent.
        when unloading is complete state=unloaded
        I have not added a callback to unload. its easy to add one if you want.

    closed is needed because wait_for end in pp_show polls for closed and does not use closed_callback
    
    """


    def start_state_machine_load(self,track):
        self.track=track
        # initialise all the state machine variables
        self.loading_count=0     # initialise loading timeout counter
        self.play_state='loading'
        
        # load the selected track
        options= ' --no-osd ' + self.omx_audio+ ' --vol -6000 ' + self.omx_window_processed + ' ' + self.seamless_loop + ' ' + self.omx_other_options +" "
        self.omx.load(track,self.freeze_at_start,options,self.mon.pretty_inst(self))
        # self.mon.log (self,'Send load command track '+ self.track + 'with options ' + options + 'from show Id: '+ str(self.show_id))
        # print 'omx.load started ',self.track
        # and start polling for state changes
        self.tick_timer=self.canvas.after(50, self.load_state_machine)

    def start_state_machine_unload(self):
        # print 'videoplayer - starting unload',self.play_state
        if self.play_state in('closed','initialised','unloaded'):
            # omxplayer already closed
            self.play_state='unloaded'
            # print ' closed so no need to unload'
        else:
            if self.play_state  ==  'loaded':
                # load already complete so set unload signal and kick off state machine
                self.play_state='start_unload'
                self.unloading_count=0
                self.unload_signal=True
                self.tick_timer=self.canvas.after(50, self.load_state_machine)
            elif self.play_state == 'loading':
                # wait for load to complete before unloading - ???? must do this because does not respond to quit when loading
                # state machine will go to start_unloading state and stop omxplayer
                self.unload_signal=True
            else:
                self.mon.err(self,'illegal state in unload method: ' + self.play_state)
                self.end('error','illegal state in unload method: '+ self.play_state)           
            
    def start_state_machine_show(self):
        if self.play_state == 'loaded':
            # print '\nstart show state machine ' + self.play_state
            self.play_state='showing'
            self.freeze_signal=False     # signal that user has pressed stop
            self.must_quit_signal=False
            # show the track and content
            self.omx.show(self.freeze_at_end_required,self.omx_volume)
            self.mon.log (self,'>showing track from show Id: '+ str(self.show_id))

            # and start polling for state changes
            # print 'start show state machine show'
            self.tick_timer=self.canvas.after(0, self.show_state_machine)
        else:
            self.mon.fatal(self,'illegal state in show method ' + self.play_state)
            self.play_state='show-failed'
            if self.finished_callback is not None:
                self.finished_callback('error','illegal state in show method: ' + self.play_state)
             

    def start_state_machine_close(self):
        self.quit_signal=True
        # print 'start close state machine close'
        self.tick_timer=self.canvas.after(0, self.show_state_machine)


    def load_state_machine(self):
        # print 'vidoeplayer state is'+self.play_state
        if self.play_state == 'loading':
            # if omxdriver says loaded then can finish normally
            # self.mon.log(self,"      State machine: " + self.play_state)
            if self.omx.end_play_signal is True:
                # got nice day before the first timestamp
                self.mon.warn(self,self.track)
                self.mon.warn(self,"loading  - omxplayer ended before starting track with reason: " + self.omx.end_play_reason + ' at ' +str(self.omx.video_position))
                self.omx.kill()
                self.mon.err(self,'omxplayer ended before loading track')
                self.play_state = 'load-failed'
                self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                if self.loaded_callback is not  None:
                    self.loaded_callback('error','omxplayer ended before loading track')      
            else:
                # end play signal false  - continue waiting for first timestamp
                self.loading_count+=1
                # video has loaded
                if self.omx.start_play_signal is True:
                    self.mon.log(self,"Loading complete from show Id: "+ str(self.show_id)+ ' ' +self.track)
                    self.mon.log(self,'Got video duration from track, frezing at: '+ str(self.omx.duration)+ ' microsecs.')
                    
                    if self.unload_signal is True:
                        # print'unload sig=true state= start_unload'
                        # need to unload, kick off state machine in 'start_unload' state
                        self.play_state='start_unload'
                        self.unloading_count=0
                        self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                        self.tick_timer=self.canvas.after(200, self.load_state_machine)
                    else:
                        self.play_state = 'loaded'
                        self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                        if self.loaded_callback is not None:
                            # print 'callback when loaded'
                            self.loaded_callback('normal','video loaded')
                else:
                    # start play signal false - continue to wait
                    if self.loading_count>400:  #40 seconds
                        # deal with omxplayer crashing while  loading and hence not receive start_play_signal
                        self.mon.warn(self,self.track)
                        self.mon.warn(self,"loading - videoplayer counted out: " + self.omx.end_play_reason + ' at ' + str(self.omx.video_position))
                        self.omx.kill()
                        self.mon.warn(self,'videoplayer counted out when loading track ')
                        self.play_state = 'load-failed'
                        self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                        if self.loaded_callback is not None:
                            self.loaded_callback('error','omxplayer counted out when loading track')
                    else:
                        self.tick_timer=self.canvas.after(100, self.load_state_machine) #200


        elif self.play_state == 'start_unload':
            # omxplayer reports it is terminating
            # self.mon.log(self,"      State machine: " + self.play_state)
      
            # deal with unload signal
            if self.unload_signal is True:
                self.unload_signal=False
                self.omx.stop()
                
            if self.omx.end_play_signal is True:
                self.omx.end_play_signal=False
                self.mon.log(self,"            <end play signal received with reason: " + self.omx.end_play_reason + ' at: ' + str(self.omx.video_position))
                
                # omxplayer has been closed 
                if self.omx.end_play_reason == 'nice_day':
                    # no problem with omxplayer
                    self.play_state='unloading'
                    self.unloading_count=0
                    self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                    self.tick_timer=self.canvas.after(50, self.load_state_machine)
                else:
                    # unexpected reason
                    self.mon.err(self,'unexpected reason at unload: '+self.omx.end_play_reason)
                    self.end('error','unexpected reason at unload: '+self.omx.end_play_reason)
            else:
                # end play signal false
                self.tick_timer=self.canvas.after(50, self.load_state_machine)       

        elif self.play_state == 'unloading':
            # wait for unloading to complete
            self.mon.log(self,"      State machine: " + self.play_state)
            
            # if spawned process has closed can change to closed state
            if self.omx.is_running()  is False:
                self.mon.log(self,"            <omx process is dead")
                self.play_state='unloaded'
                self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
            else:
                # process still running
                self.unloading_count+=1
                if self.unloading_count>10:
                    # deal with omxplayer not terminating at the end of a track
                    self.mon.warn(self,self.track)
                    self.mon.warn(self,"            <unloading - omxplayer failed to close at: " + str(self.omx.video_position))
                    self.mon.warn(self,'omxplayer should now  be killed ')
                    self.omx.kill()
                    self.play_state='unloaded'
                    self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                else:
                    self.tick_timer=self.canvas.after(200, self.load_state_machine)
        else:
            self.mon.err(self,'illegal state in load state machine: ' + self.play_state)
            self.end('error','load state machine in illegal state: '+ self.play_state)



    def show_state_machine(self):
        # print self.play_state
        # if self.play_state != 'showing': print 'show state is '+self.play_state
        if self.play_state == 'showing':
            # service any queued stop signals by sending quit to omxplayer
            # self.mon.log(self,"      State machine: " + self.play_state)
            if self.quit_signal is True:
                self.quit_signal=False
                self.mon.log(self,"      quit video - Send stop to omxdriver")
                self.omx.stop()
                self.tick_timer=self.canvas.after(50, self.show_state_machine)

            # omxplayer reports it is terminating
            elif self.omx.end_play_signal is True:
                self.omx.end_play_signal=False
                self.mon.log(self,"end play signal received with reason: " + self.omx.end_play_reason + ' at: ' + str(self.omx.video_position))
                # paused at end of track so return so calling prog can release the pause
                if self.omx.end_play_reason == 'pause_at_end':
                    self.frozen_at_end=True
                    if self.finished_callback is not None:
                        self.finished_callback('pause_at_end','pause at end')

                elif self.omx.end_play_reason == 'nice_day':
                    # no problem with omxplayer
                    self.play_state='closing'
                    self.closing_count=0
                    self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                    self.tick_timer=self.canvas.after(50, self.show_state_machine)
                else:
                    # unexpected reason
                    self.mon.err(self,'unexpected reason at end of show '+self.omx.end_play_reason)
                    self.play_state='show-failed'
                    if self.finished_callback is not None:
                        self.finished_callback('error','unexpected reason at end of show: '+ self.omx.end_play_reason)

            else:
                # nothing to do just try again
                # print 'showing - try again'
                self.tick_timer=self.canvas.after(50, self.show_state_machine)       


        elif self.play_state == 'closing':
            # wait for closing to complete
            self.mon.log(self,"      State machine: " + self.play_state)
            if self.omx.is_running()  is False:
                # if spawned process has closed can change to closed state
                self.mon.log(self,"            <omx process is dead")
                self.play_state = 'closed'
                # print 'process dead going to closed'
                self.omx=None
                self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                if self.closed_callback is not  None:
                    self.closed_callback('normal','omxplayer closed')
            else:
                # process still running
                self.closing_count+=1
                # print 'closing - waiting for process to die',self.closing_count
                if self.closing_count>10:
                    # deal with omxplayer not terminating at the end of a track
                    # self.mon.warn(self,self.track)
                    # self.mon.warn(self,"omxplayer failed to close at: " + str(self.omx.video_position))
                    self.mon.warn(self,'failed to close - omxplayer now being killed with SIGINT')
                    self.omx.kill()
                    # print 'closing - precess will not die so ita been killed with SIGINT'
                    self.play_state = 'closed'
                    self.omx=None
                    self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                    if self.closed_callback is not None:
                        self.closed_callback('normal','closed omxplayer after sigint')
                else:
                    self.tick_timer=self.canvas.after(200, self.show_state_machine)

        elif self.play_state=='closed':
            # needed because wait_for_end polls the state and does not use callback
            self.mon.log(self,"      State machine: " + self.play_state)    
            self.tick_timer=self.canvas.after(200, self.show_state_machine)            

        else:
            self.mon.err(self,'unknown state in show/close state machine ' + self.play_state)
            self.play_state='show-failed'
            if self.finished_callback is not None:
                self.finished_callback('error','show state machine in unknown state: '+ self.play_state)


    def parse_video_window(self,line):
        fields = line.split()
        # check there is a command field
        if len(fields) < 1:
            return 'error','no type field: '+line,'',False,0,0,0,0
            
        # deal with original which has 1
        if fields[0] == 'original':
            if len(fields)  !=  1:
                return 'error','number of fields for original: '+line,'',False,0,0,0,0    
            return 'normal','',fields[0],False,0,0,0,0


        # deal with warp which has 1 or 5  arguments
        # check basic syntax
        if  fields[0]  != 'warp':
            return 'error','not a valid type: '+fields[0],'',False,0,0,0,0
        if len(fields) not in (1,2,5):
            return 'error','wrong number of coordinates for warp: '+ line,'',False,0,0,0,0

        # deal with window coordinates    
        if len(fields) == 1:
            # fullscreen
            has_window=True
            return 'normal','',fields[0],has_window,self.show_canvas_x1,self.show_canvas_y1,self.show_canvas_x2,self.show_canvas_y2
        else:
            # window is specified
            status,message,x1,y1,x2,y2=parse_rectangle(' '.join(fields[1:]))
            if status == 'error':                                   
                return 'error',message,'',False,0,0,0,0
            else:
                has_window=True
                return 'normal','',fields[0],has_window,self.show_canvas_x1+x1,self.show_canvas_y1+y1,self.show_canvas_x1+x2,self.show_canvas_y1+y2


