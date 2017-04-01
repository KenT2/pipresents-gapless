# 1/2/2016 - add write stats

from pp_medialist import MediaList
from pp_show import Show
from pp_controlsmanager import ControlsManager
from pp_screendriver import ScreenDriver

class MenuShow(Show):

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
                          pp_profile,
                          command_callback)
        

        # instatiatate the screen driver - used only to access enable and hide click areas
        self.sr=ScreenDriver()

        self.controlsmanager=ControlsManager()

        # init variables
        self.show_timeout_timer=None
        self.track_timeout_timer=None
        self.next_track_signal=False
        self.next_track=None
        self.menu_index=0
        self.menu_showing=True
        self.req_next=''
        self.last_menu_index=0
        self.return_to_zero=False



    def play(self,end_callback,show_ready_callback,parent_kickback_signal,level,controls_list):
        """ displays the menu 
              end_callback - function to be called when the menu exits
              show_ready_callback - callback when menu is ready to display (not used)
              level is 0 when the show is top level (run from [start] or from show control)
              parent_kickback_signal  - not used other than it being passed to a show
        """
        # need to instantiate the medialist here as not using gapshow
        self.medialist=MediaList('ordered')

        Show.base_play(self,end_callback,show_ready_callback, parent_kickback_signal,level,controls_list)
        
        self.mon.trace(self,self.show_params['show-ref'])

        #parse the show and track timeouts
        reason,message,self.show_timeout=Show.calculate_duration(self,self.show_params['show-timeout'])
        if reason =='error':
            self.mon.err(self,'Show Timeout has bad time: '+self.show_params['show-timeout'])
            self.end('error','show timeout, bad time: ' + self.show_params['show-timeout'])

        reason,message,self.track_timeout=Show.calculate_duration(self,self.show_params['track-timeout'])
        if reason=='error':
            self.mon.err(self,'Track Timeout has bad time: '+self.show_params['track-timeout'])
            self.end('error','track timeout, bad time: ' + self.show_params['track-timeout'])
            
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


    def  handle_input_event(self,symbol):
        Show.base_handle_input_event(self,symbol)


    def handle_input_event_this_show(self,symbol):
        # menushow has only internal operation
        operation=self.base_lookup_control(symbol,self.controls_list)
        self.do_operation(operation)


    def do_operation(self,operation):
        # service the standard inputs for this show

        self.mon.trace(self,operation)
        if operation =='exit':
            self.exit()
            
        elif operation == 'stop':
            self.stop_timers()
            if self.current_player is not None:
                if self.menu_showing is True  and self.level != 0:
                    # if quiescent then set signal to stop the show when track has stopped
                    self.user_stop_signal=True
                self.current_player.input_pressed('stop')
      
        elif operation in ('up','down'):
            # stop show timeout
            if self.show_timeout_timer is not None:
                self.canvas.after_cancel(self.show_timeout_timer)
                # and start it again
                if self.show_timeout != 0:
                    self.show_timeout_timer=self.canvas.after(self.show_timeout*1000,self.show_timeout_stop)
            if operation=='up':
                self.previous()
            else:
                self.next()
                
        elif operation =='play':
            self.next_track_signal=True
            st=self.medialist.select_anon_by_index(self.menu_index)
            self.next_track=self.medialist.selected_track()
            self.current_player.stop()


            # cancel show timeout
            if self.show_timeout_timer is not None:
                self.canvas.after_cancel(self.show_timeout_timer)
                self.show_timeout_timer=None

            # stop current track (the menuplayer) if running or just start the next track
            if self.current_player is not None:
                self.current_player.input_pressed('stop')
            else:
                self.what_next_after_showing()
                
        elif operation  in ('no-command','null'):
            return

        elif operation in ('pause','pause-on','pause-off','mute','unmute','go'):
            if self.current_player is not None:
                self.current_player.input_pressed(operation)
                
        elif operation[0:4]=='omx-' or operation[0:6]=='mplay-'or operation[0:5]=='uzbl-':
            if self.current_player is not None:
                self.current_player.input_pressed(operation)

        
    def next(self):
        # remove highlight
        if self.current_player.__class__.__name__ == 'MenuPlayer':
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
        if self.current_player.__class__.__name__ == 'MenuPlayer':
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
        self.do_operation('stop')

    def do_menu_track(self):
        self.menu_showing=True
        self.mon.trace(self,'')
        # start show timeout alarm if required
        if self.show_timeout != 0:
            self.show_timeout_timer=self.canvas.after(self.show_timeout *1000,self.show_timeout_stop)

        index = self.medialist.index_of_track(self.show_params['menu-track-ref'])
        if index == -1:
                self.mon.err(self,"'menu-track' not in medialist: " + self.show_params['menu-track-ref'])
                self.end('error',"menu-track not in medialist: " + self.show_params['menu-track-ref'])
                return
        
        #make the medialist available to the menuplayer for cursor scrolling
        self.show_params['medialist_obj']=self.medialist
        
        # load the menu track 
        self.start_load_show_loop(self.medialist.track(index))


# *********************
# Playing show or track loop
# *********************

    def start_load_show_loop(self,selected_track):
        # shuffle players
        Show.base_shuffle(self)
        self.mon.trace(self,'')
        self.display_eggtimer()

        # get control bindings for this show
        # needs to be done for each track as track can override the show controls
        if self.show_params['disable-controls'] == 'yes':
            self.controls_list=[]
        else:
            reason,message,self.controls_list= self.controlsmanager.get_controls(self.show_params['controls'])
            if reason=='error':
                self.mon.err(self,message)
                self.end('error',"error in controls: " + message)
                return

        # load the track or show
        Show.base_load_track_or_show(self,selected_track,self.what_next_after_load,self.end_shower,False)

 
  # track has loaded (menu or otherwise) so show it.
    def what_next_after_load(self,status,message):

        if self.current_player.play_state=='load-failed':
            self.req_next='error'
            self.what_next_after_showing()

        else:
            # get the calculated length of the menu for the loaded menu track
            if self.current_player.__class__.__name__ == 'MenuPlayer':
                if self.medialist.anon_length()==0:
                    self.req_next='error'
                    self.what_next_after_showing()
                    return

                #highlight either first or returning entry and select appropiate medialist entry
                if self.return_to_zero is True:
                    # init the index used to hiighlight the selected menu entry by menuplayer
                    self.menu_index=0
                    # print 'initial index',self.menu_index
                else:
                    self.menu_index=self.last_menu_index
                    # print ' return to last ',self.menu_index

                
                self.menu_length=self.current_player.menu_length
                self.current_player.highlight_menu_entry(self.menu_index,True)
            self.mon.trace(self,' - load complete with status: ' + status + '  message: ' + message)


            if self.show_timeout_signal is True or self.terminate_signal  is True or self.exit_signal  is True or self.user_stop_signal  is True:
                self.what_next_after_showing()
            else:
                self.mon.trace(self,'')
                self.current_player.show(self.track_ready_callback,self.finished_showing,self.closed_after_showing)


    def finished_showing(self,reason,message):
        # showing has finished with 'pause at end', showing the next track will close it after next has started showing
        self.mon.trace(self,'')
        self.mon.log(self,"pause at end of showing track with reason: "+reason+ ' and message: '+ message)
        self.sr.hide_click_areas(self.controls_list)
        if self.current_player.play_state == 'show-failed':
            self.req_next = 'error'
        else:
            self.req_next='finished-player'
        self.what_next_after_showing()

    def closed_after_showing(self,reason,message):
        # showing has finished with closing of player but track instance is alive for hiding the x_content
        self.mon.trace(self,'')
        self.mon.log(self,"Closed after showing track with reason: "+reason+ ' and message: '+ message)
        self.sr.hide_click_areas(self.controls_list)
        if self.current_player.play_state == 'show-failed':
            self.req_next = 'error'
        else:
            self.req_next='closed-player'
        self.what_next_after_showing()

    # subshow or child show has ended
    def end_shower(self,show_id,reason,message):
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ': Returned from shower with ' + reason +' ' + message)
        self.sr.hide_click_areas(self.controls_list)        
        self.req_next=reason
        Show.base_end_shower(self)
        self.what_next_after_showing()
 

     # at the end of a track check for terminations else re-display the menu      
    def what_next_after_showing(self):
        self.mon.trace(self,'')
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
            if self.track_timeout != 0:
                self.track_timeout_timer=self.canvas.after(self.track_timeout*1000,self.track_timeout_callback)
            self.last_menu_index=self.menu_index
            Show.write_stats(self,'play',self.show_params,self.next_track)
            self.start_load_show_loop(self.next_track)
            
        else:
            # no stopping the show required so re-display the menu
            self.do_menu_track()


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

        self.sr.enable_click_areas(self.controls_list)
        
        Show.base_track_ready_callback(self,enable_show_background)

    # callback from begining of a subshow, provide previous shower player to called show        
    def subshow_ready_callback(self):
        return Show.base_subshow_ready_callback(self)



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

