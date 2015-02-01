from pp_show import Show
from pp_controlsmanager import ControlsManager
from pp_screendriver import ScreenDriver

class GapShow(Show):
    """
    this is the parent class of mediashow and liveshow
    The two derived clases just select the appropriate medialist from pp_medialist and pp_livelist
    the parents control the monitoring
    """

# *******************
# External interface
# ********************

    def __init__(self,
                 show_id,
                 show_params,
                 root,
                 canvas,
                 showlist,
                 pp_dir,
                 pp_home,
                 pp_profile,
                 command_callback):


        # init the common bits
        Show.base__init__(self,
                          show_id,
                          show_params,
                          root,
                          canvas,
                          showlist,
                          pp_dir,
                          pp_home,
                          pp_profile,
                          command_callback)

        # instatiatate the screen driver - used only to access enable and hide click areas
        self.sr=ScreenDriver()

        self.controlsmanager=ControlsManager()

        # Init variables special to this show
        self.poll_for_interval_timer=None
        self.interval_timer_signal=False
        self.waiting_for_interval=False
        self.interval_timer=None
        self.duration_timer=None

        self.end_trigger_signal=False
        self.next_track_signal=False
        self.previous_track_signal=False
        self.play_child_signal = False
        
        self.req_next='nil'
        self.state='closed'

        self.count=0
        self.interval=0
        self.duration=0
        

    def play(self,end_callback,show_ready_callback, direction_command,level,controls_list):
        self.mon.newline(3)
        self.mon.trace(self, self.show_params['show-ref'])
             
        Show.base_play(self,end_callback,show_ready_callback,direction_command, level,controls_list)

        # get the previous shower and player from calling show
       # Show.base_get_previous_player_from_parent(self)



        # unpack end trigger 
        if self.show_params['trigger-end-type'] == 'duration':
            self.duration = int(self.show_params['trigger-end-param'])
        if self.show_params['trigger-end-type'] == 'count':
            self.count = int(self.show_params['trigger-end-param'])
        if self.show_params['trigger-end-type'] == 'interval':
            self.interval = int (self.show_params['trigger-end-param'])

        # initial direction
        self.direction='forward'

      
        # and delete eggtimer started by the parent
        if self.previous_shower is not None:
            self.previous_shower.delete_eggtimer()

        # and start the show
        self.wait_for_trigger()


# ********************************
# Respond to external events
# ********************************

    # exit received from another concurrent show
    def exit(self):
        Show.base_exit(self)

    # terminate Pi Presents
    def terminate(self):
        Show.base_terminate(self)


   # respond to input events
    def input_pressed(self,symbol,edge,source):
        Show.base_input_pressed(self,symbol,edge,source)


    def input_pressed_this_show(self,symbol,edge,source):
        #  check symbol against mediashow triggers
        if self.state == 'waiting' and self.show_params['trigger-start-type'] in ('input','input-quiet') and symbol  ==  self.show_params['trigger-start-param']:
            Show.delete_admin_message(self)
            self.start_show()
            
        elif self.state == 'playing' and self.show_params['trigger-end-type'] == 'input' and symbol == self.show_params['trigger-end-param']:
            self.end_trigger_signal=True
            if self.shower is not None:
                self.shower.input_pressed('stop','','end trigger')
            elif self.current_player is not None:
                self.current_player.input_pressed('stop')
                
        elif self.state == 'playing' and self.show_params['trigger-next-type'] == 'input' and symbol == self.show_params['trigger-next-param']:
            self.next()
        else:
            # event is not a trigger so must be internal operation
            operation=self.base_lookup_control(symbol,self.controls_list)
            self.do_operation(operation,edge,source)


    # overrides base
    # service the standard operations for this show
    def do_operation(self,operation,edge,source):
        # print 'do_operation ',operation
        self.mon.trace(self, operation)
        if operation == 'exit':
            self.exit()
            
        elif operation == 'stop':
            if self.level != 0 :
                # not at top so stop the show
                self.user_stop_signal=True
                # and stop the track first
                if self.current_player is not None:
                    self.current_player.input_pressed('stop')
            else:
                # at top, just stop track if running
                if self.current_player is not None:
                    self.current_player.input_pressed('stop')                    

        elif operation == 'up' and self.state == 'playing':
            self.previous()
            
        elif operation == 'down' and self.state == 'playing':
            self.next()

        elif operation == 'play':
            # use 'play' to start child if state=playing or to trigger the show if waiting for trigger
            if self.state == 'playing':
                if self.show_params['child-track-ref'] != '':
                    # set a signal because must stop current track before running child show
                    self.play_child_signal=True
                    self.child_track_ref=self.show_params['child-track-ref']
                    # and stop the current track if its running
                    if self.current_player is not None:
                        self.current_player.input_pressed('stop')
            else:
                if self.state == 'waiting':
                    Show.delete_admin_message(self)
                    self.start_show()

        elif operation == 'pause':
            if self.current_player is not None:
                self.current_player.input_pressed('pause')

        elif operation in ('no-command','null'):
            return
                
        # if the operation is omxplayer mplayer or uzbl runtime control then pass it to player if running
        elif operation[0:4] == 'omx-' or operation[0:6] == 'mplay-'or operation[0:5] == 'uzbl-':
            if self.current_player is not None:
                self.current_player.input_pressed(operation)


    def next(self):
        # stop track if running and set signal
        self.next_track_signal=True
        if self.shower is not None:
            self.shower.input_pressed('stop')
        else:
            if self.current_player is not None:
                self.current_player.input_pressed('stop')


    def previous(self):
        self.previous_track_signal=True
        if self.shower is not None:
            self.shower.input_pressed('stop')
        else:
            if self.current_player is not None:
                self.current_player.input_pressed('stop')


# ***************************
# Show sequencing
# ***************************  
        
    # wait for trigger sets the state to waiting so that events can do a start show.


    def wait_for_trigger(self):
        text=''  # to keep landscape.io happy
        
        self.state='waiting'

        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Waiting for trigger: "+ self.show_params['trigger-start-type'])

  
        if self.show_params['trigger-start-type'] == "input":
            
            #close the previous track to display admin message
            Show.base_shuffle(self)
            self.track_ready_callback()
            text= Show.base_resource(self,'mediashow','m02')
            Show.display_admin_message(self,text)


        elif self.show_params['trigger-start-type'] == "input-quiet":
            #close the previous track to display blank screen
            Show.base_shuffle(self)
            self.track_ready_callback()
            text = Show.base_resource(self,'mediashow','m10')
            Show.display_admin_message(self,text)

        elif self.show_params['trigger-start-type'] == "input-persist":
            #wait for trigger while displaying previous track
            pass

        elif self.show_params['trigger-start-type'] == "start":
            # don't close the previous track to give seamless repeat of the show
            self.start_show()
            
        else:
            self.mon.err(self,"Unknown trigger: "+ self.show_params['trigger-start-type'])
            self.end('error',"Unknown trigger type")


    # timer for repeat=interval
    def end_interval_timer(self):
        self.interval_timer_signal=True
        # print 'INTERVAL TIMER ended'
        
        
    def end_duration_timer(self):
        if self.state == 'playing' and self.show_params['trigger-end-type'] == 'duration':
            # print '!!!!!!!!!!!!!!!! DURATION UP'
            self.end_trigger_signal=True
            if self.shower is not None:
                self.shower.input_pressed('stop','','tod-end')
            elif self.current_player is not None:
                self.current_player.input_pressed('stop')


    def start_show(self):
        # starts the show or any repeat having waited for trigger first.
        self.state='playing'

        # initialise end criteria
        self.track_count=0
        
        # start interval timer
        if self.show_params['trigger-end-type'] == "interval" and self.interval != 0:
            self.interval_timer_signal = False
            self.interval_timer=self.canvas.after(int(self.show_params['trigger-end-param'])*1000,self.end_interval_timer)
            
        # start duration timer
        if self.show_params['trigger-end-type'] == 'duration' and self.duration != 0:
            # print 'set alarm ', self.duration
            self.duration_timer = self.canvas.after(self.duration*1000,self.end_duration_timer)
        
        # and play the first track unless commanded otherwise
        if self.direction == 'backward':
            if self.medialist.finish() is False:
                # list is empty - display a message for 5 secs and then retry
                Show.display_admin_message(self,Show.base_resource(self,'mediashow','m11'))
                self.canvas.after(5000,self.remove_list_empty_message)
            else:
                self.start_load_show_loop(self.medialist.selected_track())
        else:
            if self.medialist.start() is False:
                # list is empty - display a message for 5 secs and then retry
                Show.display_admin_message(self,Show.base_resource(self,'mediashow','m11'))
                self.canvas.after(5000,self.remove_list_empty_message)
            else:
                self.start_load_show_loop(self.medialist.selected_track())


    def remove_list_empty_message(self):
        Show.delete_admin_message(self)
        self.start_show()


# ***************************
# Track load/show loop
# ***************************  

    # track playing loop starts here
    def start_load_show_loop(self,selected_track):
        # shuffle players
        Show.base_shuffle(self)
        
        self.delete_eggtimer()

        # is child track required
        if self.show_params['child-track-ref'] != '':
            self.enable_child=True
        else:
            self.enable_child=False

        # get control bindings for this show
        # needs to be done for each track as track can override the show controls
        if self.show_params['disable-controls'] == 'yes':
            self.controls_list=[]
        else:
            reason,message,self.controls_list= self.controlsmanager.get_controls(self.show_params['controls'])
            if reason=='error':
                self.mon.err(self,message)
                self.end('error',"error in controls")
                return

            # print 'controls',reason,self.show_params['controls'],self.controls_list

        # load the track or show
        # params - track,enable_menu
        Show.base_load_track_or_show(self,selected_track,self.what_next_after_load,self.end_shower,self.enable_child)
        

    # track has loaded so show it.
    # private to Show
    # >>> def loaded_callback(self,status,message):



    # track has loaded so show it.
    def what_next_after_load(self,status,message):
        self.mon.trace(self,' - load complete with status: ' + status +'  message: ' +message)
        if self.current_player.play_state == 'load-failed':
            self.req_next = 'error'
            self.what_next_after_showing()

        else:
            if self.terminate_signal is True or self.exit_signal is True or self.user_stop_signal is True:
                self.what_next_after_showing()
            else:
                self.mon.trace(self, ' - showing track')
                self.current_player.show(self.track_ready_callback,self.finished_showing,self.closed_after_showing)


    def finished_showing(self,reason,message):
        self.sr.hide_click_areas(self.controls_list)
        if self.current_player.play_state == 'show-failed':
            self.req_next = 'error'
        else:
            self.req_next='finished-player'
        # showing has finished with 'pause at end', showing the next track will close it after next has started showing
        self.mon.trace(self, ' - pause at end ')
        self.mon.log(self,"pause at end of showing track with reason: "+reason+ ' and message: '+ message)
        self.what_next_after_showing()


    def closed_after_showing(self,reason,message):
        self.sr.hide_click_areas(self.controls_list)
        if self.current_player.play_state == 'show-failed':
            self.req_next = 'error'
        else:
            self.req_next='closed-player'
        # showing has finished with closing of player but track instance is alive for hiding the x_content
        self.mon.trace(self,' - closed')
        self.mon.log(self,"Closed after showing track with reason: "+reason+ ' and message: '+ message)
        self.what_next_after_showing()

        
    # subshow or child show has ended
    def end_shower(self,show_id,reason,message):
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ': Returned from shower with ' + reason +' ' + message)
        self.sr.hide_click_areas(self.controls_list)
        self.req_next=reason
        Show.base_end_shower(self)
        self.what_next_after_showing()

    def pretty_what_next_after_showing_state(self):
        state = '\n* terminate signal ' + str(self.terminate_signal)
        state += '\n* exit signal ' +  str(self.exit_signal)
        state += '\n* user stop  signal ' + str(self.user_stop_signal)
        state += '\n* previous track  signal ' + str(self.previous_track_signal)
        state += '\n* next track  signal ' + str(self.next_track_signal)
        state += '\n* req_next ' + self.req_next
        state +=  '\n * direction ' + self.direction
        return state +'\n'
        

    def what_next_after_showing(self):

        self.track_count+=1

        # first of all deal with conditions that do not require the next track to be shown
        # some of the conditions can happen at any time, others only when a track is closed or at pause_at_end
        self.mon.trace(self,self.pretty_what_next_after_showing_state())

        
        # need to terminate
        if self.terminate_signal is True:
            self.terminate_signal=False
            self.stop_timers()
            # set what to do after closed or unloaded
            self.ending_reason='killed'
            Show.base_close_or_unload(self)

        elif self.req_next== 'error':
            self.stop_timers()
            self.req_next=''
            # set what to do after closed or unloaded
            self.ending_reason='error'
            Show.base_close_or_unload(self)

        # used for exiting show from other shows, time of day, external etc.
        elif self.exit_signal is True:
            self.exit_signal=False
            self.stop_timers()
            self.ending_reason='exit'
            Show.base_close_or_unload(self)

       # repeat=interval and last track has finished so waiting for interval timer
       # note: if medialist finishes after interval is up then this route is used to start trigger. 
        elif self.waiting_for_interval is True:
            # set by alarm clock started in start_show
            if self.interval_timer_signal is True:
                self.interval_timer_signal=False
                self.waiting_for_interval=False
                # print 'RECEIVED INTERNAL TIMER SIGNAL - STARTING SHOW'
                self.wait_for_trigger()
            else:
                self.poll_for_interval_timer=self.canvas.after(1000,self.what_next_after_showing)
  

        # user wants to stop the show
        elif self.user_stop_signal is True:
            self.user_stop_signal=False
            self.stop_timers()
            self.ending_reason='user-stop'
            Show.base_close_or_unload(self)

        # has content of list been changed (replaced if it has, used for content of livelist)
        elif self.medialist.replace_if_changed() is True:
            self.ending_reason='change-medialist'
            Show.base_close_or_unload(self)


        # otherwise consider operation that might show the next track          
        else:
            # setup default direction for if statement
            self.direction='forward'

            # end trigger from input or count
            if self.end_trigger_signal is True or (self.show_params['trigger-end-type']== 'count' and self.track_count == self.count):
                self.end_trigger_signal=False
                # repeat so test start trigger
                if self.show_params['repeat'] == 'repeat':
                    self.stop_timers()
                    self.state='waiting'
                    # print 'END TRIGGER restart'
                    self.wait_for_trigger()
                else:
                    # single run so exit show
                    if self.level == 0:
                        self.end('normal',"End of Single Run")
                    else:
                        self.end('do-next',"End of single run - Return from Sub Show")
                    

            # user wants to play child
            elif self.play_child_signal is True:
                self.play_child_signal=False
                index = self.medialist.index_of_track(self.child_track_ref)
                if index >=0:
                    # don't use select the track as need to preserve mediashow sequence.
                    child_track=self.medialist.track(index)
                    self.display_eggtimer(Show.base_resource(self,'mediashow','m07'))
                    self.start_load_show_loop(child_track)
                else:
                    self.mon.err(self,"Child not found in medialist: "+ self.child_track_ref)
                    self.ending_reason='error'
                    Show.base_close_or_unload(self)
                    # self.end('error',"child not found in medialist")

            # skip to next track on user input or after subshow
            elif self.next_track_signal is True or self.req_next == 'do-next':
                self.req_next='nil'
                self.next_track_signal=False
                if self.medialist.at_end() is True:
                    # medialist_at_end can give false positive for shuffle
                    if  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'repeat':
                        # self.state='waiting'
                        self.wait_for_trigger()
                    elif  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run':
                        if self.level != 0:
                            self.direction='forward'
                            self.end('do-next',"Return from Sub Show")
                        else:
                            # end of single run and at top - exit the show
                            self.stop_timers()
                            self.ending_reason='user-stop'
                            Show.base_close_or_unload(self)
                    else:
                        # shuffling  - just do next track
                        self.direction='forward'
                        self.medialist.next(self.show_params['sequence'])
                        self.start_load_show_loop(self.medialist.selected_track())      
                else:
                    # not at end just do next track
                    self.medialist.next(self.show_params['sequence'])
                    self.start_load_show_loop(self.medialist.selected_track())
                
            # skip to previous track on user input or after subshow
            elif self.previous_track_signal is True or self.req_next == 'do-previous':
                self.req_next='nil'
                self.previous_track_signal=False
                # medialist_at_start can give false positive for shuffle
                if self.medialist.at_start() is True:
                    # print 'AT START'
                    if  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'repeat':
                        # self.state='waiting'
                        self.direction='backward'
                        self.wait_for_trigger()
                    elif  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run':
                        if self.level != 0:
                            self.direction='backward'
                            self.end('do-previous',"Return from Sub Show")
                        else:
                            # end of single run and at top - exit the show
                            self.stop_timers()
                            self.ending_reason='user-stop'
                            Show.base_close_or_unload(self)
                    else:
                        # shuffling  - just do previous track
                        self.direction='backward'
                        self.medialist.previous(self.show_params['sequence'])
                        self.start_load_show_loop(self.medialist.selected_track())               
                else:
                    # not at end just do next track
                    self.medialist.previous(self.show_params['sequence'])              
                    self.start_load_show_loop(self.medialist.selected_track())


            # AT END OF MEDIALIST
            elif self.medialist.at_end() is True:
                # print 'MEDIALIST AT END'

                # interval>0
                if self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'repeat' and self.show_params['trigger-end-type']== 'interval' and int(self.show_params['trigger-end-param'])>0:
                    self.waiting_for_interval=True
                    # print 'WAITING FOR INTERVAL'
                    # Note: f medialist gets to its end after the interval timer has gone  off (interval_timer_signal=True) this route is taken
                    self.poll_for_interval_timer=self.canvas.after(200,self.what_next_after_showing) 

                # interval=0   
                #elif self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'repeat' and self.show_params['trigger-end-type']== 'interval' and int(self.show_params['trigger-end-param']) == 0:
                    #self.medialist.next(self.show_params['sequence'])
                    # self.start_load_show_loop(self.medialist.selected_track())
                    
                # repeat so go back to start
                elif self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'repeat':
                    # self.state='waiting'
                    self.wait_for_trigger()

                # single run
                elif self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run':
                    # if not at top return to parent
                    if self.level !=0:
                        self.end('normal',"End of Single Run")
                    else:
                        # at top so close the show
                        self.stop_timers()
                        self.ending_reason='user-stop'
                        Show.base_close_or_unload(self)
                        

                # shuffling so there is no end condition, get out of end test
                elif self.show_params['sequence'] == "shuffle":
                    self.medialist.next(self.show_params['sequence'])
                    self.start_load_show_loop(self.medialist.selected_track())
                    
                else:
                    self.mon.err(self,"Unhandled playing event: "+self.show_params['sequence'] +' with ' + self.show_params['repeat']+" of "+ self.show_params['trigger-end-param'])
                    self.end('error',"Unhandled playing event")
                
            elif self.medialist.at_end() is False:
                self.medialist.next(self.show_params['sequence'])
                self.start_load_show_loop(self.medialist.selected_track())
                      
            else:
                # unhandled state
                self.mon.err(self,"Unhandled playing event: ")

   
   
# *********************
# Interface with other shows/players to reduce black gaps
# *********************

    # called just before a track is shown to remove the  previous track from the screen
    # and if necessary close it
    def track_ready_callback(self,enable_show_background):
        self.delete_eggtimer()

        if self.show_params['disable-controls'] != 'yes':        
            #merge controls from the track
            controls_text=self.current_player.get_links()
            reason,message,track_controls=self.controlsmanager.parse_controls(controls_text)
            if reason == 'error':
                self.mon.err(self,message + " in track: "+ self.current_player.track_params['track-ref'])
                self.req_next='error'
                self.what_next_after_showing()
            self.controlsmanager.merge_controls(self.controls_list,track_controls)


        
        # enable the click-area that are in the list of controls
        self.sr.enable_click_areas(self.controls_list)
        Show.base_track_ready_callback(self,enable_show_background)

   
    # callback from begining of a subshow, provide previous player to called show        
    def subshow_ready_callback(self):
        return Show.base_subshow_ready_callback(self)


# *********************
# End the show
# *********************
    def end(self,reason,message):
        Show.base_end(self,reason,message)



    def stop_timers(self):
        # clear outstanding time of day events for this show
        # self.tod.clear_times_list(id(self))

        if self.poll_for_interval_timer is not None:
            self.canvas.after_cancel(self.poll_for_interval_timer)
            self.poll_for_interval_timer=None
            
        if self.interval_timer is not None:
            self.canvas.after_cancel(self.interval_timer)
            self.interval_timer=None
            
        if self.duration_timer is not None:
            self.canvas.after_cancel(self.duration_timer)
            self.duration_timer=None





