import os
from pp_show import Show
from pp_controlsmanager import ControlsManager


class ArtShow(Show):
    
    """
        Automatically plays a set of tracks from a medialist. Does gapless and time of day trigger but little else.
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

        # init items that are then initialised in the derived class.
        self.medialist=None
        self.load_delay=2000
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

        # Init variables
        self.duration_timer=None
        self.state='closed'
        self.ending_reason=''
        self.end_trigger_signal=False



    def play(self,end_callback,show_ready_callback, direction_command,level):

        # instantiate the arguments
        self.end_callback=end_callback
        self.show_ready_callback=show_ready_callback
        self.direction_command=direction_command
        self.level=level
        self.mon.log(self,"Starting show: " + self.show_params['show-ref'])

        # check  data files are available.
        self.medialist_file = self.pp_profile + os.sep + self.show_params['medialist']
        if not os.path.exists(self.medialist_file):
            self.mon.err(self,"Medialist file not found: "+ self.medialist_file)
            self.end('error',"Medialist file not found")
               
        # opens the medialist for the show and read it populating the in memory list.
        # medialist object is created in child class in order to choose medialist or livelist there
        # for liveshow initial list will be empty
        if self.medialist.open_list(self.medialist_file,self.showlist.sissue()) is False:
            self.mon.err(self,"Version of medialist different to Pi Presents")
            self.end('error',"Version of medialist different to Pi Presents")

        # get control bindings for this show if top level
        controlsmanager=ControlsManager()
        if self.level == 0:
            self.controls_list=controlsmanager.default_controls()
            # and merge in controls from profile
            self.controls_list=controlsmanager.merge_show_controls(self.controls_list,self.show_params['controls'])

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

        if self.show_ready_callback is not None:
            # get the previous player from calling show - (current because shuffled before use)
            self.current_player=self.show_ready_callback()
            if self.trace: print '************ start of show, getting previous_player from parent show***********',self.current_player

        self.wait_for_trigger()                

# ********************************
# Respond to external events
# ********************************

    def managed_stop(self):
        # if next lower show eor player is running pass down to stop the show/track
        self.stop_command_signal=True
        if self.current_player is not None:
            self.current_player.input_pressed('stop')

                
    # kill or error
    def terminate(self,reason):
        self.terminate_signal=True
        if self.current_player is not None:
            self.current_player.terminate(reason)
        else:
            self.end(reason,' terminated with no shower or player to terminate')

 
   # respond to key presses.
    def input_pressed(self,symbol,edge,source):
        self.mon.log(self,"received key: " + symbol)

        if self.state == 'waiting' and self.show_params['trigger-start-type'] in ('input','input-quiet') and symbol  ==  self.show_params['trigger-start-param']:
            self.start_show()
        
        if self.show_params['disable-controls'] == 'yes':
            return 

       # if at top convert symbolic name to operation otherwise lower down we have received an operation
        # look through list of standard symbols to find match (symbolic-name, function name) operation =lookup (symbol
        if self.level == 0:
            operation=Show.base_lookup_control(self,symbol,self.controls_list)
        else:
            operation=symbol
            
        # print 'operation',operation
        self.do_operation(operation,edge,source)


    def do_operation(self,operation,edge,source):
        # service the standard inputs for this show
        if operation == 'stop':
            # stop the show
            self.user_stop_signal=True
            # if  player is running pass down to stop the track
            if self.current_player is not None:
                self.current_player.input_pressed('stop')

        elif operation  ==  'pause':
            # pass down if show or track running.
            if self.current_player is not None:
                self.current_player.input_pressed(operation)

        elif operation[0:4] == 'omx-' or operation[0:6] == 'mplay-':
            if self.current_player is not None:
                self.current_player.input_pressed(operation)
     



# ***************************
# Sequencing
# ***************************
    def wait_for_trigger(self):
        self.state='waiting'
        text='' # to please landscape.io


        self.mon.log(self,"Waiting for trigger: "+ self.show_params['trigger-start-type'])

        if self.show_params['trigger-start-type'] in ('time','time-quiet'):
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
            # maybe could get messageplayer object and assign it to current_player so closed on track_ready_callback 
            Show.stop_admin_message_display(self)     

    def tod_end_callback(self):
        if self.state == 'playing' and self.show_params['trigger-end-type'] in ('time','duration'):
            self.end_trigger_signal=True
            if self.current_player is not None:
                self.current_player.input_pressed('stop')

    def start_show(self):
        self.state='playing'
        
        # start duration timer
        if self.show_params['trigger-end-type'] == 'duration':
            # print 'set alarm ', self.duration
            self.duration_timer = self.canvas.after(self.duration*1000,self.tod_end_callback)
        self.load_first_track()

    # load the first track of the show
    def load_first_track(self):
        if self.trace: print 'artshow/load_first_track'
        if self.medialist.start() is False:
            # list is empty - display a message for 10 secs and then retry
            Show.display_admin_message(self,self.canvas,None,Show.base_resource(self,'liveshow','m01'),10,self.what_next)
        else:
            # otherwise load the first track
            self.next_player=Show.base_init_selected_player(self,self.medialist.selected_track())
            if self.next_player is None:
                self.mon.err(self,"Unknown Track Type")
                self.terminate_signal=True
                self.what_next()
            else:
                track_file=Show.base_complete_path(self,self.medialist.selected_track()['location'])
                self.next_player.load(track_file,
                                      self.loaded_callback,
                                      enable_menu=False)
                self.wait_for_load() 
            


    # start of the showing loop. Got here from the end of showing.        
    def wait_for_load(self):           
        # wait for load of next track and close of previous to complete
        # state after this is previous=None, current=closed or pause_at_end, next=loaded or load_failed
        # and is a good place to test for ending.
        # if self.trace: self.print_state ('artshow/wait_for_load')
        if self.next_player is not None:
            if self.next_player.get_play_state() == 'load_failed':
                self.mon.err(self,'load failed')
                self.terminate_signal=True
                self.what_next()
            else:
                if self.previous_player is  None  and self.next_player.get_play_state() == 'loaded':
                    if self.trace: print 'artshow/wait_for_load - next is loaded and previous closed'
                    self.canvas.after(10,self.what_next)
                else:
                    self.canvas.after(50,self.wait_for_load)
        else:
            self.canvas.after(200,self.wait_for_load)           

          
    def what_next(self):
        # do we need to end or restart, if so close the current, and unload the next, and wait
        # until next is unloaded and current has closed
        if self.trace: print 'artshow/what_next'
        
        # terminate
        if self.terminate_signal is True:
            self.terminate_signal=False
            self.ending_reason='terminate'
            self.close_current_and_next()

        # used by managed stop for stopping show from other shows 
        elif self.stop_command_signal is True:
            self.stop_command_signal=False
            self.stop_timers()
            self.ending_reason='stop-command'
            self.close_current_and_next()

        # user wants to stop the show 
        elif self.user_stop_signal is True:
            self.user_stop_signal=False
            self.stop_timers()
            self.ending_reason='user-stop'
            self.close_current_and_next()
            
        # end of show time trigger
        elif self.end_trigger_signal is True:
            self.end_trigger_signal=False
            self.ending_reason='end-trigger'
            self.close_current_and_next()

        # has content of list been changed (replaced if it has, used for content of livelist)
        elif self.medialist.replace_if_changed() is True:
            self.ending_reason='change-medialist'
            self.close_current_and_next()

        elif self.medialist.length() == 0:
            self.load_first_track()

        else:
            # otherwise show the next track
            self.show_next_track()

            
    def show_next_track(self):
        if self.trace: print 'artshow/show_next_track - SHUFFLLE'
        self.previous_player=self.current_player
        self.current_player=self.next_player
        self.next_player=None
        if self.trace: print 'AFTER SHUFFLE n-c-p', self.next_player,self.current_player,self.previous_player
        if self.trace: print 'artshow/show_next_track - showing track'
        self.current_player.show(self.track_ready_callback,self.finished_showing,self.closed_after_showing)
        # wait a short time before starting to close track and then loading next
        self.canvas.after(10,self.close_and_load)


    def finished_showing(self,reason,message):
        # showing has finished with 'pause at end', showing the next track will close it after next has started showing
        if self.trace: print 'artshow/finished_showing - pause at end'
        self.mon.log(self,"finished_showing - pause at end of showing with reason: "+reason+ ' and message: '+ message)
        self.wait_for_load()


    def closed_after_showing(self,reason,message):
        # showing has finished with closing of player but track instance is alive for hiding the x_content
        if self.trace: print 'artshow/closed_after_showing - closed after showing'
        self.mon.log(self,"closed_after_showing - Closed after showing with reason: "+reason+ ' and message: '+ message)
        self.wait_for_load()        

        
    # close and load runs as a concurrent thread. Control goes nowhere after completion, success is detected from the states.    
    def close_and_load(self):
        if self.trace: self.print_state ('artshow/close_and_load entered')
        if self.previous_player is not None and self.previous_player.get_play_state() == 'pause_at_end':
            # close the previous player
            if self.trace: print 'artshow/close_and_load -  closing previous '
            self.previous_player.close(self.end_close_previous)
            
        # get the next track and init player
        self.medialist.next('ordered')
        self.next_player=Show.base_init_selected_player(self,self.medialist.selected_track())
        if self.next_player is None:
            self.mon.err(self,"Unknown Track Type: ")
            self.terminate_signal=True
            self.what_next()
        else:
            # and load the next after a wait
            self.canvas.after(self.load_delay,self.load_next)

    def load_next(self):
        # load the next track while current is showing
        track_file=Show.base_complete_path(self,self.medialist.selected_track()['location'])
        if self.trace: print 'artshow/load next', track_file
        self.next_player.load(track_file,
                              self.loaded_callback,
                              enable_menu=False)


    def end_close_previous(self,reason,message):
        self.mon.log(self,"end_close_previous - Previous closed with reason: "+reason+ ' and message: '+ message)
        if self.trace: print'artshow/end_close_previous - previous closed'
        self.previous_player=None    # safer to delete the player here rather than in player as play-state is read elsewhere.

    def loaded_callback(self,status,message):
        if self.trace: print 'artshow/loaded_callback - load complete with status: ',status,'  message: ',message        


    def close_current_and_next(self):
        if self.current_player is not None and self.current_player.get_play_state() == 'pause_at_end':
            if self.trace: print 'artshow/what_next - closing_current from terminate'
            self.current_player.close(None)
        if self.next_player is not None and self.next_player.get_play_state() not in ('unloaded','load_failed'):
            if self.trace: print 'artshow/what_next - unloading next from terminate'
            self.next_player.unload()
        self.wait_for_end()

        
    # previous=None at this point,just wait for loading and closing to complete then end
    def wait_for_end(self):
        # if self.trace: self.print_state('wait_for_end')
        ok_to_end=0
        if self.current_player is None or self.current_player.get_play_state() == 'closed':
            self.current_player=None
            ok_to_end+=1
        if self.next_player is None or self.next_player.get_play_state() in ('unloaded','load_failed'):
            self.next_player=None
            ok_to_end+=1
        if ok_to_end != 2:
            self.canvas.after(50,self.wait_for_end)
        else:
            if self.trace: print 'artshow/wait_for_end - all closed, ok to end or restart ', self.ending_reason

            if self.ending_reason == 'end-trigger':
                self.state='waiting'
                self.wait_for_trigger()
                
            elif self.ending_reason == 'terminate':
                self.end('killed',"show terminated by user")
                    
            elif self.ending_reason in ('stop-command','user-stop'):
                self.end('normal',"show quit by user or stop command")                

            elif self.ending_reason == 'change-medialist':
                self.load_first_track()   
            else:
                self.mon.err(self,"Unhandled ending_reason: ")
                self.end('error',"Unhandled ending_reason")                

    def track_ready_callback(self):
        if self.trace: print 'artshow/track_ready_callback'
        # close the player from the previous track
        if self.previous_player is not None:
            if self.trace: print '********* hiding previous ******',self.previous_player
            self.previous_player.hide()
            if self.previous_player.get_play_state() == 'pause_at_end':
                if self.trace: print '********* closing previous ******',self.previous_player
                self.previous_player.close(self.closed_callback)
            else:
                if self.trace: print '**** previous is none****'
                self.previous_player=None

    def closed_callback(self,status,message):
        if self.trace: print 'artshow/closed_callback '+status+' '+message,self
        # if self.trace: print '**** previous is none****'
        self.previous_player=None


# *********************
# Interface with other shows/players to reduce black gaps
# *********************

    # used by end_shower when a show has finished to get the last track of the called show
    def subshow_ended_callback(self):
        return self.current_player
 
# ***************************
# end of show 
# ***************************

    def end(self,reason,message):
        self.stop_command_signal=False
        self.mon.log(self,"Ending Mediashow: "+ self.show_params['show-ref'])
        self.end_callback(self.show_id,reason,message)
        self=None

    
    def stop_timers(self):
        if self.duration_timer is not None:
            self.canvas.after_cancel(self.duration_timer)
            self.duration_timer=None
        # clear outstanding time of day events for this show
        # self.tod.clear_times_list(id(self))     


# ***************************
# debug 
# ***************************
  
    def print_state(self,when):
        print when,'  n-c-p   -  ',
        if self.next_player is not None:
            print self.next_player.get_play_state(),
        else:
            print 'None',
        if self.current_player is not None:
            print self.current_player.get_play_state(),
        else:
            print 'None',
        if self.previous_player is not None:
            print  self.previous_player.get_play_state(),
        else:
            print 'None' 




        
