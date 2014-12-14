import copy
from pp_medialist import MediaList
from pp_show import Show

class MenuShow(Show):

    def __init__(self,
                 show_id,
                 show_params,
                 root,
                 canvas,
                 showlist,
                 pp_dir,
                 pp_home,
                 pp_profile):
        
        """
            show_id - index of the top level show caling this (for debug only)
            show_params - dictionary section for the menu
            canvas - the canvas that the menu is to be written on
            showlist  - the showlist
            pp_dir - Pi Presents directory
            pp_home - Pi presents data_home directory
            pp_profile - Pi presents profile directory
        """

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
        

        # remove comment to turn the trace on          
        # self.trace=True

        # control debugging log
        self.mon.on()

        # init variables
        self.show_timeout_timer=None
        self.track_timeout_timer=None
        self.next_track_signal=False
        self.next_track=None
        self.menu_index=0
        self.menu_showing=True
        self.req_next=''



    def play(self,end_callback,show_ready_callback,direction_command,level,controls_list):
        """ displays the menu 
              end_callback - function to be called when the menu exits
              show_ready_callback - callback when menu is ready to display (not used)
              level is 0 when the show is top level (run from [start] or from show control)
              direction_command  - not used other than it being passed to a show
        """
        # need to instantiate the medialist here as in gapshow done in derived class
        self.medialist=MediaList('ordered')

        Show.base_play(self,end_callback,show_ready_callback, direction_command,level,controls_list)
        if self.trace: print 'MENUSHOW/play ', self.show_params['show-ref']

        # condition the show timeout
        self.show_timeout_value=int(self.show_params['show-timeout'])*1000                               

        # get the previous player and show from calling show
        Show.base_get_previous_player_from_parent(self)
        
        # and delete eggtimer
        if self.previous_shower is not None:
            self.previous_shower.delete_eggtimer()

        # and display the menu 
        self.do_menu_track()


# ********************
# respond to inputs.
# ********************

    # exit received from another concurrent show
    def exit(self):
        self.stop_timers()
        Show.base_exit(self)

    #  show timeout happened
    def show_timeout_stop(self):
        self.stop_timers()
        Show.base_show_timeout_stop(self)

    # terminate Pi Presents
    def terminate(self):
        self.stop_timers()
        Show.base_terminate(self)            


    def input_pressed(self,symbol,edge,source):
        Show.base_input_pressed(self,symbol,edge,source)


    def input_pressed_this_show(self,symbol,edge,source):
        # menushow has only internal operation
        operation=self.base_lookup_control(symbol,self.controls_list)
        self.do_operation(operation,edge,source)


    def do_operation(self,operation,edge,source):
        # service the standard inputs for this show
        if self.trace: print 'menushow/input_pressed ',operation
        if operation=='stop':
            self.stop_timers()
            if self.current_player is not None:
                if self.menu_showing is True and self.level != 0:
                    # if quiescent then set signal to stop the show when track has stopped
                    self.user_stop_signal=True
                self.current_player.input_pressed('stop')
      
        elif operation in ('up','down'):
            # stop show timeout
            if self.show_timeout_timer is not None:
                self.canvas.after_cancel(self.show_timeout_timer)
                # and start it again
                if self.show_timeout_value != 0:
                    self.show_timeout_timer=self.canvas.after(self.show_timeout_value,self.show_timeout_stop)
            if operation=='up':
                self.previous()
            else:
                self.next()
                
        elif operation =='play':
            self.next_track_signal=True
            self.next_track=self.medialist.selected_track()

            # cancel show timeout
            if self.show_timeout_timer is not None:
                self.canvas.after_cancel(self.show_timeout_timer)
                self.show_timeout_timer=None

            # stop current track (the menuplayer) if running or just start the next track
            if self.current_player is not None:
                self.current_player.input_pressed('stop')
            else:
                self.what_next_after_showing()


        elif operation == 'pause':
            if self.current_player is not None:
                self.current_player.input_pressed(operation)
                
        elif operation[0:4]=='omx-' or operation[0:6]=='mplay-'or operation[0:5]=='uzbl-':
            if self.current_player is not None:
                self.current_player.input_pressed(operation)

        
    def next(self):
        # remove highlight
        self.current_player.highlight_menu_entry(self.menu_index,False)
        self.medialist.next('ordered')
        if self.menu_index==self.menu_length-1:
            self.menu_index=0
        else:
            self.menu_index+=1
        # and highlight the new entry
        self.current_player.highlight_menu_entry(self.menu_index,True)     


    def previous(self):
        # remove highlight
        self.current_player.highlight_menu_entry(self.menu_index,False)
        if self.menu_index==0:
            self.menu_index=self.menu_length-1
        else:
            self.menu_index-=1
        self.medialist.previous('ordered')
        # and highlight the new entry
        self.current_player.highlight_menu_entry(self.menu_index,True)
        

# *********************
# Sequencing
# *********************

    def track_timeout_callback(self):
        self.do_operation('stop','none','timeout')

    def do_menu_track(self):
        self.showing_menu=True
        if self.trace: print 'menushow/do_menu_track'

        # start show timeout alarm if required
        if int(self.show_params['show-timeout']) != 0:
            self.show_timeout_timer=self.canvas.after(self.show_timeout_value,self.show_timeout_stop)

        # init the index used to hiighlight the selected menu entry by menuplayer
        self.menu_index=0

        # create track paramters from show parameters and doctor as necessary
        self.menu_track_params=copy.deepcopy(self.show_params)
        self.menu_track_params['location']=''
        self.menu_track_params['track-text']=''
        self.menu_track_params['animate-begin']=''
        self.menu_track_params['animate-end']=''
        self.menu_track_params['animate-clear']='no'
        self.menu_track_params['show-control-begin']=''
        self.menu_track_params['show-control-end']=''
        self.menu_track_params['plugin']=''
        self.menu_track_params['display-show-background']='no'
        self.menu_track_params['background-colour']=self.show_params['menu-background-colour']
        self.menu_track_params['background-image']=self.show_params['menu-background-image']
        self.menu_track_params['medialist_obj']=self.medialist
        
        # load the menu track by using the show parameters as track parameters Yields type=menu
        self.start_load_show_loop(self.menu_track_params)



# *********************
# Playing show or track loop
# *********************

    def start_load_show_loop(self,selected_track):
        # shuffle players
        Show.base_shuffle(self)

        if self.trace: print 'menushow/start_load_show_loop'
        self.display_eggtimer(Show.base_resource(self,'menushow','m01'))
            
        # load the track or show
        Show.base_load_track_or_show(self,selected_track,self.what_next_after_load,self.end_shower,False)

 
  # track has loaded (menu or otherwise) so show it.
    def what_next_after_load(self,status,message):
        # get the calculated length of the menu for the loaded menu track
        if self.current_player.__class__.__name__ == 'MenuPlayer':
            self.medialist.start()
            self.menu_index=0
            self.menu_length=self.current_player.menu_length
            self.current_player.highlight_menu_entry(self.menu_index,True)
            
        if self.trace: print 'menushow/what_next_after_load - load complete with status: ',status,'  message: ',message
        if self.current_player.play_state=='load-failed':
            self.req_next='error'
            self.what_next_after_showing()

        else:
            if self.show_timeout_signal is True or self.terminate_signal  is True or self.exit_signal  is True or self.user_stop_signal  is True:
                self.what_next_after_showing()
            else:
                if self.trace: print 'menushow/what_next_after_load- showing track'
                self.current_player.show(self.track_ready_callback,self.finished_showing,self.closed_after_showing)


    def finished_showing(self,reason,message):
        # showing has finished with 'pause at end', showing the next track will close it after next has started showing
        if self.trace: print 'menushow/finished_showing - pause at end'
        self.mon.log(self,"pause at end of showing track with reason: "+reason+ ' and message: '+ message)
        if self.current_player.play_state == 'show-failed':
            self.req_next = 'error'
        else:
            self.req_next='finished-player'
        self.what_next_after_showing()

    def closed_after_showing(self,reason,message):
        # showing has finished with closing of player but track instance is alive for hiding the x_content
        if self.trace: print 'menushow/closed_after_showing - closed after showing'
        self.mon.log(self,"Closed after showing track with reason: "+reason+ ' and message: '+ message)
        if self.current_player.play_state == 'show-failed':
            self.req_next = 'error'
        else:
            self.req_next='closed-player'
        self.what_next_after_showing()

    # subshow or child show has ended
    def end_shower(self,show_id,reason,message):
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ': Returned from shower with ' + reason +' ' + message)
        self.req_next=reason
        Show.base_end_shower(self)
        self.what_next_after_showing()
 

     # at the end of a track check for terminations else re-display the menu      
    def what_next_after_showing(self):
        if self.trace: print 'menushow/what_next_after_showing '
        print self.user_stop_signal, self.current_player,self.previous_player
        # cancel track timeout timer
        if self.track_timeout_timer is not None:
            self.canvas.after_cancel(self.track_timeout_timer)
            self.track_timeout_timer=None
            
        # need to terminate?
        if self.terminate_signal is True:
            self.terminate_signal=False
            # set what to do when closed or unloaded
            self.ending_reason='killed'
            Show.base_close_or_unload(self)

        elif self.req_next== 'error':
            self.req_next=''
            # set what to do after closed or unloaded
            self.ending_reason='error'
            Show.base_close_or_unload(self)

        # show timeout
        elif self.show_timeout_signal is True:
            self.show_timeout_signal=False
            # set what to do when closed or unloaded
            self.ending_reason='show-timeout'
            Show.base_close_or_unload(self)

        # used by exit for stopping show from other shows. 
        elif self.exit_signal is True:
            self.exit_signal=False
            self.ending_reason='exit'
            Show.base_close_or_unload(self)

        # user wants to stop
        elif self.user_stop_signal is True:
            self.user_stop_signal=False
            self.ending_reason='user-stop'
            Show.base_close_or_unload(self)

        elif self.next_track_signal is True:
            self.next_track_signal=False
            self.menu_showing=False
            # start timeout for the track if required           
            if int(self.show_params['track-timeout']) != 0:
                self.track_timeout_timer=self.canvas.after(int(self.show_params['track-timeout'])*1000,self.track_timeout_callback)
            self.start_load_show_loop(self.next_track)
            
        else:
            # no stopping the show required so re-display the menu
            self.do_menu_track()


# *********************
# Interface with other shows/players to reduce black gaps
# *********************

    # called just before a track is shown to remove the  previous track from the screen
    # and if necessary close it
    def track_ready_callback(self):
        self.delete_eggtimer()
        Show.base_track_ready_callback(self)

    # callback from begining of a subshow, provide previous shower player to called show        
    def subshow_ready_callback(self):
        return Show.base_subshow_ready_callback(self)

    # called by end_shower of a parent show  to get the last track of the subshow
    def subshow_ended_callback(self):
        return Show.base_subshow_ended_callback(self)



# *********************
# Ending the show
# *********************

    def end(self,reason,message):
        self.stop_timers()
        Show.base_end(self,reason,message)


    def stop_timers(self):
        if self.track_timeout_timer is not None:
            self.canvas.after_cancel(self.track_timeout_timer)
            self.track_timeout_timer=None
        if self.show_timeout_timer is not None:
            self.canvas.after_cancel(self.show_timeout_timer)
            self.show_timeout_timer=None    

