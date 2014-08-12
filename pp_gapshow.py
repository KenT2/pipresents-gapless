from pp_show import Show


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
                 pp_profile):

        # initi things that will be reinitialised by derived classes
        self.medialist=None
        Show.__init__(self)

        # init the common bits
        Show.base__init__(self,
                          show_id,
                          show_params,
                          root,
                          canvas,
                          showlist,
                          pp_dir,
                          pp_home,
                          pp_profile)


        # Init variables special to this show
        self.poll_for_interval_timer=None
        self.interval_timer_signal=False
        self.waiting_for_interval=False
        self.interval_timer=None
        
        self.poll_for_continue_timer=None
        self.duration_timer=None

        self.end_trigger_signal=False
        self.next_track_signal=False
        self.previous_track_signal=False
        self.play_child_signal = False
        
        self.req_next='nil'
        self.state='closed'
        self.ending_reason=''
        

    def play(self,end_callback,show_ready_callback, direction_command,level):
        if self.trace: print '\n\nGAPSHOW/play ',self.show_params['show-ref']
        Show.base_play(self,end_callback,show_ready_callback,direction_command, level)

        # set up the time of day triggers for the show
        if self.show_params['trigger-start-type']in('time','time-quiet'):
            error_text=self.tod.add_times(self.show_params['trigger-start-param'],id(self),self.tod_start_callback,self.show_params['trigger-start-type'])
            if error_text != '':
                self.mon.err(self,error_text)
                self.end('error',error_text)

        if self.show_params['trigger-end-type'] == 'time':
            error_text=self.tod.add_times(self.show_params['trigger-end-param'],id(self),self.tod_end_callback,'n/a')
            if error_text != '':
                self.mon.err(self,error_text)
                self.end('error',error_text)
                
        if self.show_params['trigger-end-type'] == 'duration':
            error_text=self.calculate_duration(self.show_params['trigger-end-param'])
            if error_text != '':
                self.mon.err(self,error_text)
                self.end('error',error_text)

        # get the previous shower and player from calling show
        Show.base_get_previous_player_from_parent(self)
        # and delete eggtimer started by the parent
        if self.previous_shower is not None:
            self.previous_shower.delete_eggtimer()

        # and start the show
        self.wait_for_trigger()


# ********************************
# Respond to external events
# ********************************

    # stop received from another concurrent show
    def managed_stop(self):
        Show.base_managed_stop(self)

    # terminate Pi Presents
    def terminate(self,reason):
        Show.base_terminate(self,reason)


   # respond to input events
    def input_pressed(self,symbol,edge,source):
        self.mon.log(self, self.show_params['show-ref']+ ' '+ str(self.show_id)+": received input: " + symbol)

        
        #  check symbol against mediashow triggers, triggers can be used at top or lower level
        # and not affected by disable-controls

        if self.state == 'waiting' and self.show_params['trigger-start-type'] in ('input','input-quiet')and symbol  ==  self.show_params['trigger-start-param']:
            self.start_show()
        elif self.state == 'playing' and self.show_params['trigger-next-type'] == 'input' and symbol == self.show_params['trigger-next-param']:
            self.next()

       # internal operations are triggered only when disable-controls is  'no'
        if self.show_params['disable-controls'] == 'yes':
            return

        print self.level,symbol

        # if at top (level=0convert symbolic name to operation otherwise lower down we have received an operation
        # look through list of symbolic names to find match (symbolic-name, function name) operation =lookup (symbol
        if self.level == 0:
            operation=Show.base_lookup_control(self,symbol,self.controls_list)
        else:
            operation=symbol
            
        print 'operation',operation
        self.do_operation(operation,edge,source)


    # service the standard operations for this show
    def do_operation(self,operation,edge,source):
        if self.shower is not None:
            # if sub/child show is running pass down operation to lower level
            self.shower.input_pressed(operation,edge,source) 
        else:        
            # control this show and its tracks
            # print 'do_operation ',operation,self.level
            if self.trace: print 'gapshow/input_pressed ',operation
            if operation == 'stop':
                if self.level != 0 and self.show_params['progress'] == 'auto':
                    # not at top and auto so stop the show
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
                    if self.show_params['has-child'] == 'yes':
                        # set a signal because must stop current track befroe running child show
                        self.play_child_signal=True
                        self.child_track_ref='pp-child-show'
                        # and stop the current track if its running
                        if self.current_player is not None:
                            self.current_player.input_pressed('stop')
                else:
                    if self.state == 'waiting':
                        Show.stop_admin_message_display(self)

            elif operation == 'pause':
                if self.current_player is not None:
                    self.current_player.input_pressed('pause')
                    
            # if the operation is omxplayer or mplayer runtime control then pass it to player if running
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
            # blank screen waiting for trigger if auto, otherwise display something
            if self.show_params['progress'] == "manual":
                text= Show.base_resource(self,'mediashow','m01')
            else:
                text= Show.base_resource(self,'mediashow','m02')
            Show.display_admin_message(self,self.canvas,'text',text,0,self.start_show)


        elif self.show_params['trigger-start-type'] == "input-quiet":
            # blank screen waiting for trigger
            text = Show.base_resource(self,'mediashow','m10')
            Show.display_admin_message(self,self.canvas,'text',text,0,self.start_show)

        elif self.show_params['trigger-start-type'] in ('time','time-quiet'):
            # show next show notice
            # 0  - SOURCE,  1 - 'tomorrow',  2 - TAG,  3 - QUIET
            # if next show is this one display text
            next_show=self.tod.next_event_time()
            if next_show[3] is False:
                if next_show[1] == 'tomorrow':
                    text = Show.base_resource(self,'mediashow','m09')
                else:
                    text = Show.base_resource(self,'mediashow','m08')                     
                text=text.replace('%tt',next_show[0])
                Show.display_admin_message(self,self.canvas,'text',text,0,self.start_show)  
            
        elif self.show_params['trigger-start-type'] == "start":
            self.start_show()
            
        else:
            self.mon.err(self,"Unknown trigger: "+ self.show_params['trigger-start-type'])
            self.end('error',"Unknown trigger type")

    # callbacks from time of day scheduler
    def tod_start_callback(self):
        if self.state == 'waiting' and self.show_params['trigger-start-type']in('time','time-quiet'):
            Show.stop_admin_message_display(self)

    def tod_end_callback(self):
        if self.state == 'playing' and self.show_params['trigger-end-type'] in ('time','duration'):
            self.end_trigger_signal=True
            if self.shower is not None:
                self.shower.input_pressed('stop','','tod-end')
            elif self.current_player is not None:
                self.current_player.input_pressed('stop')

    # timer for repeat=interval
    def end_interval_timer(self):
        self.interval_timer_signal=True



    def start_show(self):
        self.state='playing'
        self.direction='forward'
        # start interval timer
        if self.show_params['repeat'] == "interval" and self.show_params['repeat-interval'] != 0:
            self.interval_timer_signal=False
            self.interval_timer=self.canvas.after(int(self.show_params['repeat-interval'])*1000,self.end_interval_timer)
            
        # start duration timer
        if self.show_params['trigger-end-type'] == 'duration':
            # print 'set alarm ', self.duration
            self.duration_timer = self.canvas.after(self.duration*1000,self.tod_end_callback)
        
        # and play the first track unless commanded otherwise
        if self.direction == 'backward':
            if self.medialist.finish() is False:
                # list is empty - display a message for 10 secs and then retry
                Show.display_admin_message(self,self.canvas,None,Show.base_resource(self,'liveshow','m01'),10,self.what_next_after_showing)
            else:
                self.start_load_show_loop(self.medialist.selected_track())
        else:
            if self.medialist.start() is False:
                # list is empty - display a message for 10 secs and then retry
                Show.display_admin_message(self,self.canvas,None,Show.base_resource(self,'liveshow','m01'),10,self.what_next_after_showing)
            else:
                self.start_load_show_loop(self.medialist.selected_track())


# ***************************
# Track load/show loop
# ***************************  

    # track playing loop starts here
    def start_load_show_loop(self,selected_track):
        # shuffle players
        Show.base_shuffle(self)
        
        self.delete_eggtimer()
        if self.show_params['progress'] == "manual":
            self.display_eggtimer(Show.base_resource(self,'mediashow','m04'))

        # is menu required
        if self.show_params['has-child'] == "yes":
            self.enable_child=True
        else:
            self.enable_child=False

        # load the track or show
        # params - track,enable_menu
        Show.base_load_track_or_show(self,selected_track,self.what_next_after_load,self.end_shower,self.enable_child)
        

    # track has loaded so show it.
    # private to Show
    # >>> def loaded_callback(self,status,message):



    # track has loaded so show it.
    def what_next_after_load(self,status,message):
        if self.trace: print 'show/what_next_after_load - load complete with status: ',status,'  message: ',message
        if self.current_player.play_state == 'load_failed':
            self.mon.err(self,'load failed')
            self.terminate_signal=True
            self.what_next_after_showing()
        else:
            if self.terminate_signal is True or self.stop_command_signal is True or self.user_stop_signal is True:
                self.what_next_after_showing()
            else:
                if self.trace: print 'show/whatnext_after_show- showing track'
                self.current_player.show(self.track_ready_callback,self.finished_showing,self.closed_after_showing)


    def finished_showing(self,reason,message):
        self.req_next='finished-player'
        # showing has finished with 'pause at end', showing the next track will close it after next has started showing
        if self.trace: print 'gapshow/finished_showing - pause at end',self.current_player
        self.mon.log(self,"pause at end of showing track with reason: "+reason+ ' and message: '+ message)
        self.what_next_after_showing()


    def closed_after_showing(self,reason,message):
        self.req_next='closed-player'
        # showing has finished with closing of player but track instance is alive for hiding the x_content
        if self.trace: print 'gapshow/closed_after_showing - closed',self.current_player
        self.mon.log(self,"Closed after showing track with reason: "+reason+ ' and message: '+ message)
        self.what_next_after_showing()

        
    # subshow or child show has ended
    def end_shower(self,show_id,reason,message):
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ': Returned from shower with ' + reason +' ' + message)
        Show.base_end_shower(self)

        if self.show_params['progress'] == "manual":
            self.display_eggtimer(Show.base_resource(self,'mediashow','m06'))
        self.req_next=reason
        self.what_next_after_showing()

    def print_what_next_after_showing_state(self):
        print '* terminate signal', self.terminate_signal
        print '* stop command signal', self.stop_command_signal   
        print '* user stop  signal', self.user_stop_signal
        print '* previous track  signal', self.previous_track_signal
        print '* next track  signal', self.next_track_signal
        print '* req_next from subshow', self.req_next
        print '* direction ?old', self.direction
        

    def what_next_after_showing(self):

        # first of all deal with conditions that do not require the next track to be shown
        # some of the conditions can happen at any time, others only when a track is closed or at pause_at_end
        if self.trace: print 'gapshow/what_next_after_showing '
        if self.trace: self.print_what_next_after_showing_state()
        # need to terminate
        if self.terminate_signal is True:
            self.terminate_signal=False
            self.stop_timers()
            # what to do when closed or unloaded
            self.ending_reason='terminate'
            Show.base_close_or_unload(self)


       # repeat=interval and last track has finished so waiting for interval timer
        elif self.waiting_for_interval is True:
            # set by alarm clock started in start_show
            if self.interval_timer_signal is True:
                self.interval_timer_signal=False
                self.waiting_for_interval=False
                self.start_show()
            else:
                self.poll_for_interval_timer=self.canvas.after(1000,self.what_next_after_showing)
  

        # used by managed_stop for stopping show from other shows. 
        elif self.stop_command_signal is True:
            self.stop_command_signal=False
            self.stop_timers()
            self.ending_reason='stop-command'
            Show.base_close_or_unload(self)

        # user wants to stop the show
        elif self.user_stop_signal is True:
            self.user_stop_signal=False
            self.stop_timers()
            self.ending_reason='user-stop'
            Show.base_close_or_unload(self)

        # track has finished and we are on manual progress so wait for user command (next/prev_track_signal)            
        elif self.show_params['progress'] == "manual" and not (self.play_child_signal or self.next_track_signal or self.previous_track_signal):
            self.delete_eggtimer()
            if self.show_params['trigger-next-type'] == 'input':
                self.display_eggtimer(Show.base_resource(self,'mediashow','m03'))
            self.poll_for_continue_timer=self.canvas.after(2000,self.what_next_after_showing)           


        # otherwise show the next track          
        else:
            # setup direction for if statement
            self.direction='forward'

            # end of show time trigger
            if self.end_trigger_signal is True:
                self.end_trigger_signal=False
                self.stop_timers()
                self.state='waiting'
                self.wait_for_trigger()

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
                    self.mon.err(self,"Child show not found in medialist: "+ self.show_params['pp-child-show'])
                    self.end('error',"child show not found in medialist")

            # skip to next track on user input or after subshow
            elif self.next_track_signal is True or self.req_next == 'do-next':
                self.req_next='nil'
                self.next_track_signal=False
                if self.medialist.at_end() is True:
                    if  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'oneshot':
                        self.state='waiting'
                        self.wait_for_trigger()
                    elif  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run' and self.level != 0:
                        self.end('do-next',"Return from Sub Show")
                    else:
                        self.medialist.next(self.show_params['sequence'])
                        self.start_load_show_loop(self.medialist.selected_track())               
                else:
                    # print 'not at end'
                    self.medialist.next(self.show_params['sequence'])
                    self.start_load_show_loop(self.medialist.selected_track())
                
            # skip to previous track on user input or after subshow
            elif self.previous_track_signal is True or self.req_next == 'do-previous':
                self.req_next='nil'
                self.previous_track_signal=False
                self.direction='backward'
                if self.medialist.at_start() is True:
                    if  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'oneshot':
                        self.state='waiting'
                        self.wait_for_trigger()
                    elif  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run' and self.level != 0:
                        self.end('do-previous',"Return from Sub Show")
                    else:
                        self.medialist.previous(self.show_params['sequence'])
                        self.start_load_show_loop(self.medialist.selected_track())               
                else:
                    self.medialist.previous(self.show_params['sequence'])              
                    self.start_load_show_loop(self.medialist.selected_track())


            # track is finished and we are on auto        
            elif self.show_params['progress'] == "auto":

                if self.medialist.at_end() is True:

                    # oneshot    
                    if self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'oneshot':
                        self.state='waiting'
                        self.wait_for_trigger()

                    # single run
                    elif self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run' and self.level == 0:
                        self.end('normal',"End of Single Run")

                    elif self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run' and self.level != 0:
                        self.end('do-next',"End of single run - Return from Sub Show")

                    # repeat=interval>0
                    elif self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'interval' and int(self.show_params['repeat-interval'])>0:
                        self.waiting_for_interval=True
                        self.poll_for_interval_timer=self.canvas.after(200,self.what_next_after_showing) 

                    # repeat=interval=0   
                    elif self.show_params['repeat'] == 'interval' and int(self.show_params['repeat-interval']) == 0:
                        self.medialist.next(self.show_params['sequence'])
                        self.start_load_show_loop(self.medialist.selected_track())

                    # shuffling so there is no end condition, get out of end test
                    elif self.show_params['sequence'] == "shuffle":
                        self.medialist.next(self.show_params['sequence'])
                        self.start_load_show_loop(self.medialist.selected_track())
                        
                    else:
                        self.mon.err(self,"Unhandled playing event: "+self.show_params['sequence'] +' with ' + self.show_params['repeat']+" of "+ self.show_params['repeat-interval'])
                        self.end('error',"Unhandled playing event")
                    
                else:
                    # not at end so play the next track
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
    def track_ready_callback(self):
        self.delete_eggtimer()
        Show.base_track_ready_callback(self)

   
    # callback from begining of a subshow, provide previous player to called show        
    def subshow_ready_callback(self):
        return Show.base_subshow_ready_callback(self)


    # called by end_shower of a parent show  to get the last track of the subshow
    def subshow_ended_callback(self):
        return Show.base_subshow_ended_callback(self)



# *********************
# End the show
# *********************
    def end(self,reason,message):
        Show.base_end(self,reason,message)



    def stop_timers(self):
        # clear outstanding time of day events for this show
        # self.tod.clear_times_list(id(self))
        if self.poll_for_continue_timer is not None:
            self.canvas.after_cancel(self.poll_for_continue_timer)
            self.poll_for_continue_timer=None
            
        if self.poll_for_interval_timer is not None:
            self.canvas.after_cancel(self.poll_for_interval_timer)
            self.poll_for_interval_timer=None
            
        if self.interval_timer is not None:
            self.canvas.after_cancel(self.interval_timer)
            self.interval_timer=None
            
        if self.duration_timer is not None:
            self.canvas.after_cancel(self.duration_timer)
            self.duration_timer=None





