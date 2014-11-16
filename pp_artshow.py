import os
from pp_show import Show

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


        # Init variables for this show
        self.end_medialist_signal=False
        self.end_medialist_warning=False
        self.next_track_signal=False
        self.state='closed'


    def play(self,end_callback,show_ready_callback, direction_command,level,controls_list):
        if self.trace: print '\n\nARTSHOW/play ',self.show_params['show-ref']
        Show.base_play(self,end_callback,show_ready_callback,direction_command, level,controls_list)

        # get the previous shower and player from calling show
        Show.base_get_previous_player_from_parent(self)

        # and delete eggtimer started by the parent
        if self.previous_shower is not None:
            self.previous_shower.delete_eggtimer()

        self.wait_for_trigger()   

   

# ********************************
# Respond to external events
# ********************************

    def managed_stop(self):
        # set signal to stop the show when all  sub-shows and players have ended
        self.stop_command_signal=True
        # then stop track.
        if self.current_player is not None:
            self.current_player.input_pressed('stop')
        else:
            self.end('normal','stopped by ShowManager')

                
    # kill or error
    def terminate(self,reason):
        self.terminate_signal=True
        if self.current_player is not None:
            self.current_player.terminate(reason)
        else:
            self.end(reason,' terminated with no shower or player to terminate')

 
   # respond to key presses.
    def input_pressed(self,symbol,edge,source):
        self.mon.log(self, self.show_params['show-ref']+ ' '+ str(self.show_id)+": received input: " + symbol)
        Show.base_input_pressed(self,symbol,edge,source)


    def do_trigger_or_link(self,symbol,edge,source):
        pass

    # service the standard operations for this show
    def do_operation(self,operation,edge,source):
        if self.trace: print 'artshow/input_pressed ',operation
        # service the standard inputs for this show
        if operation == 'stop':
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

        elif operation  ==  'pause':
            # pass down if show or track running.
            if self.current_player is not None:
                self.current_player.input_pressed('pause')

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
        if self.trace: print 'artshow/load_first_track'
        if self.medialist.start() is False:
            # list is empty - display a message for 10 secs and then retry
            Show.display_admin_message(self,self.canvas,None,Show.base_resource(self,'mediashow','m11'),10,self.what_next)
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
            
        # has content of list been changed (replaced if it has, used for content of livelist)
        elif self.medialist.replace_if_changed() is True:
            self.ending_reason='change-medialist'
            self.close_current_and_next()

        elif self.medialist.length() == 0:
            self.load_first_track()

        # end of medialist
        elif self.end_medialist_signal is True:
            print '!!!!!!! END MEDIALIST', self.show_params['repeat']
            self.end_medialist_signal=False
            self.end_medialist_warning=False
            # test for oredered since medialist at end gives false positives for shuffle
            
            # repeat so go back to start
            if self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'repeat':
                # self.state='waiting'
                self.wait_for_trigger()

            # single run and at top so repeat
            elif self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run' and self.level == 0:
                self.start_trigger()
                # self.ending_reason='end-trigger'
                # self.close_current_and_next()

            # single run and not at top so end
            elif self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run' and self.level != 0:
                self.ending_reason='end-of-medialist'
                self.close_current_and_next()

            else:
                # otherwise show the next track
                print 'show next track after end'
                self.show_next_track()
        else:
            # otherwise show the next track
            print '!!!!!!!!!! show next track'
            self.show_next_track()

            
    def show_next_track(self):
        if self.trace: print 'artshow/show_next_track - SHUFFLLE'
        self.previous_player=self.current_player
        self.current_player=self.next_player
        self.next_player=None
        if self.trace: print 'AFTER SHUFFLE n-c-p', self.next_player,self.current_player,self.previous_player
        if self.trace: print 'artshow/show_next_track - showing track'
        if self.end_medialist_warning is True:
            self.end_medialist_signal = True
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
        if self.previous_player is not None and self.previous_player.get_play_state() == 'showing':
            # close the previous player
            if self.trace: print 'artshow/close_and_load -  closing previous '
            self.previous_player.close(self.end_close_previous)
            
        # get the next track and init player
        self.medialist.next(self.show_params['sequence'])
        if self.medialist.at_end() is True:
            self.end_medialist_warning=True
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
        if self.current_player is not None and self.current_player.get_play_state() == 'showing':
            if self.trace: print 'artshow/what_next - closing_current from ',self.ending_reason 
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
                    
            elif self.ending_reason in ('stop-command','user-stop','end-of-medialist'):
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
            if self.previous_player.get_play_state() == 'showing':
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
        pass
        #if self.duration_timer is not None:
            #self.canvas.after_cancel(self.duration_timer)
            #self.duration_timer=None
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




        
