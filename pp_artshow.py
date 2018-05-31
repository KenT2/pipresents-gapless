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

        # delay in mS before next track is loaded after showing a track.
        # can be inceeased if animation is required
        self.load_delay = 5

        # Init variables for this show
        self.end_medialist_signal=False
        self.end_medialist_warning=False
        self.next_track_signal=False
        self.state='closed'
        self.req_next=''
        self.next_player=None


    def play(self,end_callback,show_ready_callback, parent_kickback_signal,level,controls_list):
        self.mon.trace(self,self.show_params['show-ref'])
        Show.base_play(self,end_callback,show_ready_callback,parent_kickback_signal, level,controls_list)

        if self.medialist.anon_length()==0 and self.show_params['type'] not in ('liveshow','artliveshow'):
            self.mon.err(self,'No anonymous tracks in medialist ')
            self.end('error','No anonymous tracks in medialist ')

        # get the previous shower and player from calling show
        # Show.base_get_previous_player_from_parent(self)

        # and delete eggtimer started by the parent
        if self.previous_shower is not None:
            self.previous_shower.delete_eggtimer()
            
        self.wait_for_trigger()   

   

# ********************************
# Respond to external events
# ********************************

    def exit(self):
        # set signal to stop the show when all  sub-shows and players have ended
        self.exit_signal=True
        # then stop track.
        if self.current_player is not None:
            self.current_player.input_pressed('stop')
        else:
            self.end('normal','ended by exit')

                
    # kill or error
    def terminate(self):
        self.terminate_signal=True
        if self.current_player is not None:
            self.ending_reason='killed'
            self.close_current_and_next()
        else:
            self.end('killed',' terminated with no shower or player to terminate')

 
   # respond to key presses.
    def handle_input_event(self,symbol):
        Show.base_handle_input_event(self,symbol)



    def handle_input_event_this_show(self,symbol):
        operation=self.base_lookup_control(symbol,self.controls_list)
        self.do_operation(operation)


    def do_trigger_or_link(self,symbol,edge,source):
        pass

    # service the standard operations for this show
    def do_operation(self,operation):
        self.mon.trace(self,operation)
        # service the standard inputs for this show
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

        elif operation == 'down':
            self.next()

        elif operation  in ('pause','pause-on','pause-off','mute','unmute','go'):
            # pass down if show or track running.
            if self.current_player is not None:
                self.current_player.input_pressed(operation)

        elif operation  in ('no-command','null'):
            return
        
        elif operation[0:4] == 'omx-' or operation[0:6] == 'mplay-':
            if self.current_player is not None:
                self.current_player.input_pressed(operation)
     

    def next(self):
        # stop track if running and set signal
        self.next_track_signal=True
        if self.current_player is not None:
            self.current_player.input_pressed('stop')


# ***************************
# Sequencing
# ***************************
    def wait_for_trigger(self):
        self.start_show()            

    def start_show(self):
        self.load_first_track()

        
    # load the first track of the show
    def load_first_track(self):
        self.mon.trace(self,'')
        self.medialist.create_new_livelist()
        self.medialist.use_new_livelist()
        if self.medialist.start() is False:
            # print 'FIRST EMPTY'
            # list is empty - display a message for 5 secs and then retry
            Show.display_admin_message(self,self.show_params['empty-text'])
            self.canvas.after(5000,self.remove_list_empty_message)
        else:
            # otherwise load the first track
            # print "!!!!! artshow init first"
            # print 'after wait EMPTY'
            self.next_player=Show.base_init_selected_player(self,self.medialist.selected_track())
            if self.next_player is None:
                self.mon.err(self,"Track Type cannot be played by this show: "+self.medialist.selected_track()['type'])
                self.req_next='error'
                self.what_next()
            else:
                # messageplayer passes the text not a file name
                if self.medialist.selected_track()['type'] == 'message':
                    track_file=self.medialist.selected_track()['text']
                else:
                    track_file=Show.base_complete_path(self,self.medialist.selected_track()['location'])
                # print "!!!!! artshow load first ",track_file
                self.next_player.load(track_file,
                                      self.loaded_callback,
                                      enable_menu=False)
                self.wait_for_load() 
            

    def remove_list_empty_message(self):
        Show.delete_admin_message(self)
        self.load_first_track()


    # start of the showing loop. Got here from the end of showing.        
    def wait_for_load(self):           
        # wait for load of next track and close of previous to complete
        # state after this is previous=None, current=closed or pause_at_end, next=loaded or load_failed
        # and is a good place to test for ending.
        # self.mon.trace(self,'')
        if self.next_player is not None:
            if self.next_player.get_play_state() == 'load-failed':
                self.req_next='error'
                self.what_next()
            else:
                if self.previous_player is  None  and self.next_player.get_play_state() == 'loaded':
                    self.mon.trace(self,' - next is loaded and previous closed')
                    self.canvas.after(10,self.what_next)
                else:
                    self.canvas.after(50,self.wait_for_load)
        else:
            self.canvas.after(200,self.wait_for_load)           

          
    def what_next(self):
        # do we need to end or restart, if so close the current, and unload the next, and wait
        # until next is unloaded and current has closed
        self.mon.trace(self,'')
        
        # terminate
        if self.terminate_signal is True:
            self.terminate_signal=False
            self.ending_reason='killed'
            self.close_current_and_next()

        elif self.req_next== 'error':
            self.req_next=''
            # set what to do after closed or unloaded
            self.ending_reason='error'
            self.close_current_and_next()

        # used  for stopping show from other shows  etc.
        elif self.exit_signal is True:
            self.exit_signal=False
            self.stop_timers()
            self.ending_reason='exit'
            self.close_current_and_next()

        # user wants to stop the show 
        elif self.user_stop_signal is True:
            self.user_stop_signal=False
            self.stop_timers()
            self.ending_reason='user-stop'
            self.close_current_and_next()
            
        elif self.medialist.length() == 0:
            self.load_first_track()

        # end of medialist
        elif self.end_medialist_signal is True:
            self.end_medialist_signal=False
            self.end_medialist_warning=False
            # test for ordered since medialist at end gives false positives for shuffle
            
            # repeat so go back to start
            if self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'repeat':
                self.show_next_track()

            # single run so end
            elif self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run':
                self.ending_reason='end-of-medialist'
                self.close_current_and_next()

            else:
                # otherwise show the next track
                self.show_next_track()
        else:
            # otherwise show the next track
            self.show_next_track()

            
    def show_next_track(self):
        self.mon.trace(self,' - SHUFFLE')
        self.previous_player=self.current_player
        self.current_player=self.next_player
        self.next_player=None
        self.mon.trace(self,'AFTER SHUFFLE n-c-p' +  self.mon.pretty_inst(self.next_player) + ' ' + self.mon.pretty_inst(self.current_player) + ' ' + self.mon.pretty_inst(self.previous_player) )
        self.mon.trace(self, 'showing track')
        if self.end_medialist_warning is True:
            self.end_medialist_signal = True
        self.current_player.show(self.track_ready_callback,self.finished_showing,self.closed_after_showing)
        # load the next after a wait to allow animation etc to be timely.
        self.canvas.after(self.load_delay,self.what_to_load_next)


    def finished_showing(self,reason,message):
        # showing has finished with 'pause at end', showing the next track will close it after next has started showing
        self.mon.trace(self,' - pause at end')
        self.mon.log(self,"finished_showing - pause at end of showing with reason: "+reason+ ' and message: '+ message)
    
        if self.current_player.play_state == 'show-failed':
            self.req_next = 'error'
            self.what_next()
        else:
            self.req_next='finished-player'
            self.wait_for_load()


    def closed_after_showing(self,reason,message):
        # showing has finished with closing of player but track instance is alive for hiding the x_content
        self.mon.trace(self,' - closed after showing')
        self.mon.log(self,"closed_after_showing - Closed after showing with reason: "+reason+ ' and message: '+ message)
        if self.current_player.play_state == 'show-failed':
            self.req_next = 'error'
            self.what_next()
        else:
            self.req_next='finished-player'
            self.wait_for_load()        

        
    # pre-load the next track. Runs concurrently to show. Control goes nowhere after completion, success is detected from the states.    
    def what_to_load_next(self):
        self.mon.trace(self,self.pretty_state ())

        # closing down so don't load anything
        if self.ending_reason in ('killed','error'):
            return

        # wanting to exit so don't load just skip to what-next
        if self.terminate_signal is True or self.exit_signal is True or self.req_next=='error':
            self.what_next()

        # has content of list been changed (replaced if it has, used for content of livelist)
        # print 'WHAT to load NEXT'
        self.medialist.create_new_livelist()

        # print result, self.medialist.new_length(),self.medialist.anon_length()
        if self.medialist.livelist_changed() is True:
            # print 'ITS CHANGED'
            self.ending_reason='change-medialist'
            self.close_current_and_next()
        else:
            # get the next track and init player
            self.medialist.next(self.show_params['sequence'])
            Show.delete_admin_message(self)
            if self.medialist.at_end() is True:
                self.end_medialist_warning=True
            # print "!!!!! artshow init next "
            self.next_player=Show.base_init_selected_player(self,self.medialist.selected_track())
            if self.next_player is None:
                self.mon.err(self,"Track Type cannot be played by this show: "+self.medialist.selected_track()['type'])
                self.req_next='error'
                self.what_next()
            else:
                # load the next track while current is showing
                # messageplayer passes the text not a file name
                if self.medialist.selected_track()['type'] == 'message':
                    track_file=self.medialist.selected_track()['text']
                else:
                    track_file=Show.base_complete_path(self,self.medialist.selected_track()['location'])
                # print "!!!!! artshow load next ",track_file
                self.mon.trace(self, track_file)
                self.next_player.load(track_file,
                                      self.loaded_callback,
                                      enable_menu=False)

    def loaded_callback(self,reason,message):
        self.mon.trace(self,' - load complete with reason: ' + reason + '  message: ' + message)  


##    def end_close_previous(self,reason,message):
##        self.mon.log(self,"end_close_previous - Previous closed with reason: "+reason+ ' and message: '+ message)
##        self.mon.trace(self,' - previous closed')
##        self.previous_player=None    # safer to delete the player here rather than in player as play-state is read elsewhere.


    
    def close_current_and_next(self):
        # end of show so close current, next and previous before ending
        if self.current_player is not None and self.current_player.get_play_state() == 'showing':
            self.mon.trace(self,' - closing_current from ' + self.ending_reason)
            self.current_player.close(self.end_close_current)
        if self.next_player is not None:
            if self.next_player.get_play_state() not in ('unloaded','closed','initialised','load-failed'):
                self.mon.trace(self, '- unloading next from ' + self.ending_reason)
                self.next_player.unload()
        self.wait_for_end()


    def end_close_current(self,reason,message):
        self.mon.log(self,"Current track closed with reason: "+ reason + ' and message: '+ message)
        self.mon.trace(self,' - current closed')
        self.current_player=None    # safer to delete the player here rather than in player as play-state is read elsewhere.


        
    # previous=None at this point,just wait for loading and closing to complete then end
    def wait_for_end(self):
        self.mon.trace(self, self.pretty_state())
        ok_to_end=0
        if self.current_player is None or self.current_player.get_play_state() == 'closed':
            self.current_player=None
            ok_to_end+=1
        if self.next_player is None or self.next_player.get_play_state() in ('initialised','unloaded','load-failed'):
            self.next_player=None
            ok_to_end+=1
        if ok_to_end != 2:
            self.canvas.after(50,self.wait_for_end)
        else:
            self.mon.trace(self,' - next and current closed ' + self.ending_reason)

            if self.ending_reason == 'killed':
                self.base_close_previous()

            elif self.ending_reason=='error':
                self.base_close_previous()
                
            elif self.ending_reason == 'exit':
                self.base_close_previous()

            elif self.ending_reason == 'end-trigger':
                self.state='waiting'
                self.wait_for_trigger()

            elif self.ending_reason in ('user-stop','end-of-medialist'):
                self.end('normal',"show quit by user or natural end")                

            elif self.ending_reason == 'change-medialist':
                    self.load_first_track()
            else:
                self.mon.err(self,"Unhandled ending_reason: "+ self.ending_reason)
                self.end('error',"Unhandled ending_reason: "+ self.ending_reason)                

    def track_ready_callback(self,enable_show_background):
        self.mon.trace(self, '')

        # get control bindings for this show
        self.controlsmanager=ControlsManager()
        if self.show_params['disable-controls'] == 'yes':
            self.controls_list=[]
        else:
            reason,message,self.controls_list= self.controlsmanager.get_controls(self.show_params['controls'])
            if reason=='error':
                self.mon.err(self,message)
                self.end('error',"error in controls: " + message)
                return
            # print '\nshow controls',self.show_params['controls']
   
            #merge controls from the track
            controls_text=self.current_player.get_links()
            # print 'current player controls',controls_text
            reason,message,track_controls=self.controlsmanager.parse_controls(controls_text)
            if reason == 'error':
                self.mon.err(self,message + " in track: "+ self.current_player.track_params['track-ref'])
                self.error_signal=True
                self.what_next_after_showing()
            self.controlsmanager.merge_controls(self.controls_list,track_controls)

        # show the show background done for every track but quick operation
        if enable_show_background is True:
            self.base_show_show_background()
        else:
            self.base_withdraw_show_background()
        # !!!!!!!!! withdraw the background from the parent show
        if self.previous_shower != None:
            self.previous_shower.base_withdraw_show_background()
            
        # close the player from the previous track
        if self.previous_player is not None:
            self.mon.trace(self, 'hiding previous: ' + self.mon.pretty_inst(self.previous_player))
            self.previous_player.hide()
            if self.previous_player.get_play_state() == 'showing':
                self.mon.trace(self,'closing previous: ' + self.mon.pretty_inst(self.previous_player))
                self.previous_player.close(self.closed_callback)
            else:
                self.mon.trace(self, 'previous is none')
                self.previous_player=None


    def closed_callback(self,reason,message):
        self.mon.trace(self, reason +' '+ message)
        self.previous_player=None


    def base_close_previous(self):
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": base close previous")
        self.mon.trace(self, '')
        # close the player from the previous track
        if self.previous_player is not  None:
            self.mon.trace(self, 'previous is not None ' + self.mon.pretty_inst(self.previous_player))
            if self.previous_player.get_play_state() == 'showing':
                # showing or frozen
                self.mon.trace(self,'closing previous ' + self.mon.pretty_inst(self.previous_player))
                self.previous_player.close(self._base_close_previous_callback)
            else:
                self.mon.trace(self, 'previous is not showing')
                self.previous_player.hide()
                self.previous_player=None
                self.end(self.ending_reason,'')
        else:
            self.mon.trace(self,'previous is None')
            self.end(self.ending_reason,'')
            
                
    def _base_close_previous_callback(self,status,message):
        self.mon.trace(self,' previous is None  - was ' + self.mon.pretty_inst(self.previous_player))
        self.previous_player.hide()
        self.previous_player=None
        self.end(self.ending_reason,'')


# ***************************
# end of show 
# ***************************

    def end(self,reason,message):
        Show.delete_admin_message(self)
        self.base_withdraw_show_background()
        self.base_delete_show_background()
        self.mon.log(self,"Ending Artshow: "+ self.show_params['show-ref'])
        self.end_callback(self.show_id,reason,message)
        self=None

    
    def stop_timers(self):
        pass
        #if self.duration_timer is not None:
            #self.canvas.after_cancel(self.duration_timer)
            #self.duration_timer=None
        # clear outstanding time of day events for this show
        # self.tod.clear_times_list(id(self))     


# ***************************
# debug 
# ***************************
  
    def pretty_state(self):
        state = '  n-c-p   -  '
        if self.next_player is not None:
            state += self.next_player.get_play_state()
        else:
            state += 'None'
        if self.current_player is not None:
            state += self.current_player.get_play_state()
        else:
            state += 'None'
        if self.previous_player is not None:
            state +=  self.previous_player.get_play_state()
        else:
            state += 'None'
        return state




        
