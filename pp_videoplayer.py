from pp_omxdriver import OMXDriver
from pp_utils import Monitor
from pp_player import Player

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
                         end_callback):

        # this must be true when using the test harness
        self.testing=False

        self.trace=True
        #self.trace=False

        self.mon=Monitor()
        self.mon.on()

        
        #initialise items common to all players   
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
                        end_callback)
        
        if self.trace: print '    Videoplayer/init ',self

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
            self.omx_volume= "--vol "+ str(int(self.omx_volume)*100) + ' '

        if self.track_params['omx-window'] != '':
            self.omx_window= self.track_params['omx-window']
        else:
            self.omx_window= self.show_params['omx-window']

        if self.track_params['omx-other-options'] != '':
            self.omx_other_options= self.track_params['omx-other-options']
        else:
            self.omx_other_options= self.show_params['omx-other-options']

        if self.track_params['pause-at-end'] != '':
            pause_at_end_text= self.track_params['pause-at-end']
        else:
            pause_at_end_text= self.show_params['pause-at-end']

        if pause_at_end_text=='yes':
            self.pause_at_end_required=True
        else:
            self.pause_at_end_required=False
            

        if self.track_params['seamless-loop']=='yes':
            self.seamless_loop=' --loop '
        else:
            self.seamless_loop=''
            
            
        #set up video window
        status,message,command,has_window,x1,y1,x2,y2= self.parse_window(self.omx_window)
        if status =='error':
            self.mon.err(self,'omx window error: ' + message + ' in ' + self.omx_window)
            self.end( 'error',message)
        else:
            if has_window==True:
                self.omx_window_processed= '--win " '+ str(x1) +  ' ' + str(y1) + ' ' + str(x2) + ' ' + str(y2) + ' " '
            else:
                self.omx_window_processed=''

 
        #initialise video playing state and signals
        self.quit_signal=False
        self.unload_signal=False
        self.play_state='initialised'
        

    # LOAD - creates and omxplayer instance, loads a track and then pause
    def load(self,track,loaded_callback,enable_menu):  
        #instantiate arguments
        self.track=track
        self.loaded_callback=loaded_callback   #callback when loaded
        self.enable_menu=enable_menu

        if self.trace: print '    Videoplayer/load ',self

        # load the plugin, this may modify self.track and enable the plugin drawign to canvas
        if self.track_params['plugin'] != '':
            status,message=self.load_plugin()
            if status == 'error':
                self.mon.err(self,message)
                self.end('error',message)
                self=None

        # load the images and text
        status,message=self.load_x_content()
        if status == 'error':
            self.mon.err(self,message)
            self.end('error',message)
            self=None

        # get the duration of the track
        duration=float(self.track_params['duration'])
        if duration==0:
            # create an  instance of omxdriver to obtain the duration
            self.omx_dur=OMXDriver(self.canvas)
            self.omx_dur.get_duration(self.track)
            self._wait_for_duration(self._load_after_get_duration)
        else:
            # othewise we have duration so start the loading part of state machine.
            self.mon.log(self,">load track received from show Id: "+ str(self.show_id))
            # create an  instance of omxdriver
            self.omx=OMXDriver(self.canvas)
            self.start_state_machine_load(self.track,duration)


    def _get_duration(self,track):
        self.omx_dur.get_duration(track)

    def _wait_for_duration(self,measured_callback):
        if self.omx_dur.duration_signal==True:
            #self.omx_dur.kill()
            measured_callback(self.omx_dur.measured_duration, self.omx_dur.duration_reason)
        else:
            self.root.after(100,lambda arg=measured_callback: self._wait_for_duration(arg))

    # continue the loading after the get_duration callback 
    def _load_after_get_duration(self,duration,status):
        # print 'got duration from track',duration,status,self.omx_dur.duration_reason
        self.omx_dur=None
        if duration<=0:
            self.mon.err(self,'Track does not provide duration, must be in track parameters')
            self.end('error','duration of track required')
        else:        
            self.mon.log(self,">load track received from show Id: "+ str(self.show_id) + ' using duration from track')
            # create an  instance of omxdriver
            self.omx=OMXDriver(self.canvas)
            self.start_state_machine_load(self.track,duration)



     # SHOW - show a track      
    def show(self,
                     ready_callback,
                     finished_callback,
                     closed_callback,
                     enable_menu=False):
                         
        #instantiate arguments
        self.ready_callback=ready_callback         # callback when ready to show video
        self.finished_callback=finished_callback         # callback when finished showing
        self.closed_callback=closed_callback
        self.enable_menu = enable_menu

        if self.trace: print '    Videoplayer/show ',self

        self.show_x_content()

        # hide previous and do animation end etc.
        if self.ready_callback != None:
            self.ready_callback()

        # show the currrent x contnet and do start animation
        Player.pre_show(self)


        #start show state machine
        self.start_state_machine_show()


    # UNLOAD - abort a load when omplayer is loading or loaded
    def unload(self):
        if self.trace: print '    Videoplayer/unload ',self
        self.mon.log(self,">unload received from show Id: "+ str(self.show_id))
        self.start_state_machine_unload()


    # CLOSE - quits omxplayer from 'pause at end' state
    def close(self,closed_callback):
        if self.trace: print '    Videoplayer/close ',self
        self.mon.log(self,">close received from show Id: "+ str(self.show_id))
        self.closed_callback=closed_callback
        self.start_state_machine_close()



    def input_pressed(self,symbol):
        if symbol[0:4]=='omx-':
            self.control(symbol[4])
            
        elif symbol =='pause':
            self.pause()

        elif symbol=='stop':
            self.stop()


    # respond to normal stop
    def stop(self):
        # send signal to stop the track to the state machine
        self.mon.log(self,">stop received from show Id: "+ str(self.show_id))
        if self.play_state == 'pause_at_end':
            #showing already complete so quit omxplayer and kick off state machine
            self.play_state='showing'
            self.quit_signal=True
            self.tick_timer=self.canvas.after(0, self.show_state_machine)
        elif self.play_state == 'showing':
          # just quit omxplayer as state machine is already running
          self.quit_signal=True
        else:
          self.mon.log(self,"!<stop rejected")


    #toggle pause
    def pause(self):
        self.mon.log(self,">toggle pause received from show Id: "+ str(self.show_id))
        if self.play_state =='showing':
            self.omx.toggle_pause('user')
            return True
        else:
            self.mon.log(self,"!<pause rejected " + self.play_state)
            return False
        
    # other control when playing
    def control(self,char):
        if self.play_state=='showing' and char not in ('q'):
            self.mon.log(self,"> send control to omx: "+ char)
            self.omx.control(char)
            return True
        else:
            self.mon.log(self,"!<control rejected")
            return False



# ***********************
# state machine
# **********************

    """

    STATES OF STATE MACHINE
    Threre are ongoing states and states that are set just before callback

    >Create an instance of the class
    <On return - state = initialised   -  - init has been completed
    < after a fatal error at any time in the lifetime of a track end-callback is called
        On getting end_callback abort Pi Presents because its not worth continuing. Should happen in debug only.

    >load
         Ongoing - state=loading - load received, waiting for load to complete   
    < loaded_callback with status = normal
         state=loaded - load has completed and video paused before first frame      
    <loaded_callback with status=error
        state= load_failed - omxplayer process has been killed because of failure to load   

    On getting the loaded_callback with status=normal the track can be shown using show
    On getting the loaded_callback with status=load_failed omxplayer has been killed. Calling program needs to recover somehow.
    load will take the track;s duration from the track paramters. If duration is 0 omxplayer is interogated to find the duration of the track.
    Duration obtained from track should always cause pause_at_end. if not please tell me aas the fudge factor may need adjusting.
    Duration set in track parameters can be shorter than the track's real duration. If so videplayer will pause_at end.
    Duration set in track parameters can be longer than the track's real duration. If so videplayer complete the track and will close.

    >show
        show assumes a track has been loaded and is paused.
       Ongoing - state=showing - video is showing
    <finished_callback with status = pause_at_end
            state=pause_at_end - video has reached near the end and has paused
    <finished_callback with status=nice_day, eof, or timeout
            state==finished - video has ended omxplayer has terminated.
            eof and timeout are error conditions and shoudl not happen. vidoeplayer recovers from these and continues.

    On getting finished_callback with status=pause_at end a new track can be shown and then use close to quit completed track
    On getting finished_callback with status= timeout eof or nice_day omxplayer closing should not be attempted as it is already closed/
    

    >close
       Ongoing state - closing - omxplayer processes are dieing due to quit sent
    <closed_callback with status= normal - omxplayer is dead, can close the instance.

    >unload
        Ongoing states - start_unload and unloading - omxplayer processes are dieing due to quit sent.
        when unloading is complete state=unloaded
        I have not added a callback to unload. its easy to add one if you want.
    
    """


    def start_state_machine_load(self,track,duration):
        self.duration=duration
        self.track=track
        #initialise all the state machine variables
        self.loading_count=0     #initialise loading timeout counter
        self.play_state='loading'
        
        #load the selected track
        options= ' --no-osd ' + self.omx_audio+ " " + self.omx_volume + ' ' + self.omx_window_processed + ' ' + self.seamless_loop + ' ' + self.omx_other_options +" "
        self.omx.load(track,options,self.duration)
        self.mon.log (self,'Loading track '+ self.track + 'with options ' + options + 'from show Id: '+ str(self.show_id))
        
        # and start polling for state changes
        self.tick_timer=self.canvas.after(50, self.load_state_machine)

    def start_state_machine_unload(self):
        # print 'videoplayer - starting unload',self.play_state
        if self.play_state in('closed','initialised','unloaded'):
            # omxplayer already closed
            self.play_state='unloaded'
            # print ' closed so no need to unload'
        else:
            if self.play_state == 'loaded':
                #load already complete so set unload signal and kick off state machine
                self.play_state='start_unload'
                self.unloading_count=0
                self.unload_signal=True
                self.tick_timer=self.canvas.after(50, self.load_state_machine)
            elif self.play_state == 'loading':
                # wait for load to complete before unloading - ???? must do this because does not respond to quit when loading
                # state machine will go to start_unloading state and stop omxplayer
                self.unload_signal=True
            else:
                self.mon.err(self,'illegal state in unload method ' + self.play_state)
                self.end('error','illegal state in unload method')           
            
    def start_state_machine_show(self):
        if self.play_state=='loaded':
            # print 'start show state machine ' + self.play_state
            self.play_state='showing'
            self.quit_signal=False     # signal that user has pressed stop
            #show the track and content
            self.omx.show(self.pause_at_end_required)
            self.mon.log (self,'>showing track from show Id: '+ str(self.show_id))

            # and start polling for state changes
            self.tick_timer=self.canvas.after(0, self.show_state_machine)
        else:
            self.mon.err(self,'illegal state in show method ' + self.play_state)
            self.end('error','illegal state in show method')                
     

    def start_state_machine_close(self):
        if self.play_state == 'pause_at_end':
            self.play_state='showing'
            self.quit_signal=True
            self.tick_timer=self.canvas.after(0, self.show_state_machine)
        else:
            self.mon.err(self,'illegal state in close method' + self.play_state)
            self.end('error','illegal state in close method')    

    def load_state_machine(self):
        # print 'vidoeplayer state is'+self.play_state
        if self.play_state=='loading':
            # if omxdriver says loaded then can finish normally
            # self.mon.log(self,"      State machine: " + self.play_state)
            if self.omx.end_play_signal==True:
                # got nice day, eof or timeout before the first timestamp
                self.mon.warn(self,self.track)
                self.mon.warn(self,"            <loading  - omxplayer ended before starting track with reason: " + self.omx.end_play_reason + ' at ' +str(self.omx.video_position))
                self.mon.warn(self,'pexpect.before  is'+self.omx.xbefore)
                self.omx.kill()
                self.mon.warn(self,'omxplayer now  terminated ')
                self.play_state = 'load_failed'
                self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                if self.loaded_callback != None:
                    self.loaded_callback('error','omxplayer ended before loading track')      
            else:
                # end play signal false  - continue waiting for first timestamp
                self.loading_count+=1
                # video has loaded
                if self.omx.start_play_signal==True:
                    self.mon.log(self,"            <loading complete from show Id: "+ str(self.show_id))
                    if self.unload_signal==True:
                        # print'unload sig=true so send stop and go to start_unload'
                        # need to unload, kick off state machine in 'start_unload' state
                        # print 'seen unload signal, sending stop'
                        self.play_state='start_unload'
                        self.unloading_count=0
                        self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                        self.tick_timer=self.canvas.after(200, self.load_state_machine)
                    else:
                        self.play_state = 'loaded'
                        self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                        if self.loaded_callback != None:
                            self.loaded_callback('normal','video loaded')
                else:
                    #start play signal false - continue to wait
                    if self.loading_count>20:  #4 seconds
                        # deal with omxplayer crashing while  loading and hence not receive start_play_signal
                        self.mon.warn(self,self.track)
                        self.mon.warn(self,"            <loading - omxplayer crashed when loading  track with: " + self.omx.end_play_reason + ' at ' + str(self.omx.video_position))
                        self.mon.warn(self,'pexpect.before  is'+self.omx.xbefore)
                        self.omx.kill()
                        self.mon.warn(self,'omxplayer now  terminated ')
                        self.play_state = 'load_failed'
                        self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                        if self.loaded_callback != None:
                            self.loaded_callback('error','omxplayer counted out when loading track')
                    else:
                        self.tick_timer=self.canvas.after(200, self.load_state_machine)


        elif self.play_state == 'start_unload':
            # omxplayer reports it is terminating
            # self.mon.log(self,"      State machine: " + self.play_state)
      
            # deal with unload signal
            if self.unload_signal==True:
                self.unload_signal=False
                self.omx.stop()
                
            if self.omx.end_play_signal==True:
                self.omx.end_play_signal=False
                self.mon.log(self,"            <end play signal received with reason: " + self.omx.end_play_reason + ' at: ' + str(self.omx.video_position))
                
                #omxplayer has been closed 
                if self.omx.end_play_reason == 'nice_day':
                    # no problem with omxplayer
                    self.play_state='unloading'
                    self.unloading_count=0
                    self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                    self.tick_timer=self.canvas.after(50, self.load_state_machine)
                else:
                    # problem with omxplayer    
                    if self.omx.end_play_reason in ('eof','timeout'):
                        self.mon.warn(self,self.track)
                        self.mon.warn(self,"            <start_unload - end detected at: " + str(self.omx.video_position))
                        self.mon.warn(self,"            <pexpect reports: "+self.omx.end_play_reason)
                        self.mon.warn(self,'pexpect.before  is'+self.omx.xbefore)
                        self.play_state='unloading'
                        self.unloading_count=0
                        self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                        self.tick_timer=self.canvas.after(50, self.load_state_machine)
                    else:
                        # unexpected reason
                        self.mon.err(self,'unexpected reason at unload '+self.omx.end_play_reason)
                        self.end('error','unexpected reason at unload')
            else:
                # end play signal false
                self.tick_timer=self.canvas.after(50, self.load_state_machine)       

        elif self.play_state=='unloading':
            # wait for unloading to complete
            # self.mon.log(self,"      State machine: " + self.play_state)
            
            # if spawned process has closed can change to closed state
            if self.omx.is_running() ==False:
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
                    self.mon.warn(self,'pexpect.before  is'+self.omx.xbefore)
                    self.mon.warn(self,'omxplayer should now  be killed ')
                    self.omx.kill()
                    self.play_state='unloaded'
                    self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                else:
                    self.tick_timer=self.canvas.after(200, self.load_state_machine)
        else:
                self.mon.err(self,'illegal state in load state machine' + self.play_state)
                self.end('error','load state machine in illegal state')



    def show_state_machine(self):
        # print 'show state is'+self.play_state
        if self.play_state == 'showing':
            # service any queued stop signals by sending quit to omxplayer
            # self.mon.log(self,"      State machine: " + self.play_state)
            if self.quit_signal==True:
                self.quit_signal=False
                self.mon.log(self,"      Send stop to omxdriver")
                self.omx.stop()

            # omxplayer reports it is terminating
            if self.omx.end_play_signal==True:
                self.omx.end_play_signal=False
                self.mon.log(self,"            <end play signal received with reason: " + self.omx.end_play_reason + ' at: ' + str(self.omx.video_position))
                # paused at end of track so return so calling prog can release the pause
                if self.omx.end_play_reason == 'pause_at_end':
                    self.play_state='pause_at_end'
                    self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                    if self.finished_callback != None:
                        self.finished_callback('pause_at_end','pause at end')

                else:
                    #otherwise omxplayer has been closed so there has been no chance to pause
                    if self.omx.end_play_reason == 'nice_day':
                        # no problem with omxplayer
                        self.play_state='closing'
                        self.closing_count=0
                        #print 'hide in closing'
                        #self.hide_x_content()
                        self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                        self.tick_timer=self.canvas.after(50, self.show_state_machine)
                        
                    elif self.omx.end_play_reason in ('eof','timeout'):
                        # problem with omxplayer
                        #print 'hide in problem'
                        #self.hide_x_content()
                        self.play_state='closing'
                        self.closing_count=0
                        self.mon.warn(self,self.track)
                        self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                        self.mon.warn(self,"            <showing - end detected at: " + str(self.omx.video_position))
                        self.mon.warn(self,"            <pexpect reports: "+self.omx.end_play_reason)
                        self.mon.warn(self,'pexpect.before  is'+self.omx.xbefore)
                        self.tick_timer=self.canvas.after(50, self.show_state_machine)
                    else:
                        # unexpected reason
                        self.mon.err(self,'unexpected reason at end of show '+self.omx.end_play_reason)
                        self.end('error','unexpected reason')
            else:
                # end play signal false
                self.tick_timer=self.canvas.after(50, self.show_state_machine)       


        elif self.play_state=='closing':
            # wait for closing to complete
            # self.mon.log(self,"      State machine: " + self.play_state)
            if self.omx.is_running() ==False:
                # if spawned process has closed can change to closed state
                self.mon.log(self,"            <omx process is dead")
                self.play_state = 'closed'
                self.omx=None
                self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                if self.closed_callback != None:
                   self.closed_callback('normal','omxplayer closed')
            else:
                # process still running
                self.closing_count+=1
                if self.closing_count>10:
                    # deal with omxplayer not terminating at the end of a track
                    self.mon.warn(self,self.track)
                    self.mon.warn(self,"            <closing - omxplayer failed to close at: " + str(self.omx.video_position))
                    self.mon.warn(self,'pexpect.before  is'+self.omx.xbefore)
                    self.mon.warn(self,'omxplayer should now  be killed ')
                    self.omx.kill()
                    self.play_state = 'closed'
                    self.omx=None
                    self.mon.log(self,"      Entering state : " + self.play_state + ' from show Id: '+ str(self.show_id))
                    if self.closed_callback != None:
                         self.closed_callback('normal','closed omxplayer after sigint')
                else:
                    self.tick_timer=self.canvas.after(200, self.show_state_machine)
                    
        else:
                self.mon.err(self,'unknown state in show state machine' + self.play_state)
                self.end('error','show state machine in unknown state')


    def parse_window(self,line):
        
            fields = line.split()
            # check there is a command field
            if len(fields) < 1:
                    return 'error','no type field','',False,0,0,0,0
                
            # deal with original which has 1
            if fields[0]=='original':
                if len(fields)  !=  1:
                        return 'error','number of fields for original','',False,0,0,0,0    
                return 'normal','',fields[0],False,0,0,0,0


            #deal with warp which has 1 or 5  arguments
            # check basic syntax
            if  fields[0]  != 'warp':
                    return 'error','not a valid type','',False,0,0,0,0
            if len(fields) not in (1,5):
                    return 'error','wrong number of coordinates for warp','',False,0,0,0,0

            # deal with window coordinates    
            if len(fields) == 5:
                #window is specified
                if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                    return 'error','coordinates are not positive integers','',False,0,0,0,0
                has_window=True
                return 'normal','',fields[0],has_window,int(fields[1]),int(fields[2]),int(fields[3]),int(fields[4])
            else:
                # fullscreen
                has_window=True
                return 'normal','',fields[0],has_window,0,0,self.canvas['width'],self.canvas['height']
