from pp_medialist import MediaList
from pp_show import Show
from pp_pathmanager import PathManager
from pp_screendriver import ScreenDriver

class RadioButtonShow(Show):
    """
        starts at 'first-track' which can be any type of track or a show
        The show has links of the form 'symbolic-name play track-ref'
        An event with the symbolic-name will play the referenced track,
        at the end of that track control will return to first-track
        links in the tracks are ignored. Links are inherited from the show.
        timeout returns to first-track

        interface:
        * __init__ - initlialises the show
         * play - selects the first track to play (first-track) 
         * input_pressed,  - receives user events passes them to a Shower/Player if a track is playing,
                otherwise actions them depending on the symbolic name supplied
        *exit  - exits the show from another show, time of day scheduler or external
        * terminate  - aborts the show, used whan clsing or after errors
        * track_ready_callback - called by the next track to be played to remove the previous track from display
        * subshow_ready_callback - called by the subshow to get the last track of the parent show
        * subshow_ended_callback - called at the start of a parent show to get the last track of the subshow
        
    """
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

        # create an instance of PathManager -  only used to parse the links.
        self.path = PathManager()

        self.allowed_links=('play','pause','exit','return')
        # init variables
        self.track_timeout_timer=None
        self.show_timeout_timer=None
        self.next_track_signal=False
        self.current_track_ref=''
        self.req_next=''


    def play(self,end_callback,show_ready_callback,direction_command,level,controls_list):
        """ starts the hyperlink show at start-track 
              end_callback - function to be called when the show exits
              show_ready_callback - callback to get the previous track
              level is 0 when the show is top level (run from [start] or from show control)
              direction_command  - not used other than it being passed to a show
        """
        # need to instantiate the medialist here as in gapshow done in derived class
        self.medialist=MediaList('ordered')
        
        Show.base_play(self,end_callback,show_ready_callback, direction_command,level,controls_list)
        
        self.mon.trace(self,self.show_params['show-ref'])
        
        # read the show links. Track links will NOT be added by ready_callback
        links_text=self.show_params['links']
        reason,message,self.links=self.path.parse_links(links_text,self.allowed_links)
        if reason == 'error':
            self.mon.err(self,message + " in show")
            self.end('error',message)
      
        # get the previous player and show from calling show
        # Show.base_get_previous_player_from_parent(self)
        
        # and delete eggtimer
        if self.previous_shower is not  None:
            self.previous_shower.delete_eggtimer()
            
        self.do_first_track()

# ********************************
# Respond to external events
# ********************************

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


   # respond to inputs
    def input_pressed(self,symbol,edge,source):
        Show.base_input_pressed(self,symbol,edge,source)


    def input_pressed_this_show(self,symbol,edge,source):
        # for radiobuttonshow the symbolic names are links to play tracks, also a limited number of in-track operations
        # find the first entry in links that matches the symbol and execute its operation
        # print 'radiobuttonshow ',symbol
        found,link_op,link_arg=self.path.find_link(symbol,self.links)                    
        if link_op == 'play':
            self.do_play(link_arg,edge,source)
            
        elif link_op == 'exit':
            #exit the show
            self.exit()

        elif link_op== 'return':
            # return to the first track
            if self.current_track_ref != self.first_track_ref:
                self.do_play(self.first_track_ref,edge,source)

        # in-track operations
        elif link_op =='pause':
            if self.current_player is not  None:
                self.current_player.input_pressed(link_op)
                
        elif link_op[0:4] == 'omx-' or link_op[0:6] == 'mplay-'or link_op[0:5] == 'uzbl-':
            if self.current_player is not None:
                self.current_player.input_pressed(link_op)
                
        else:
            self.mon.err(self,"unknown link command: "+ link_op)
            self.end('error',"unknown link command")




# *********************
# INTERNAL FUNCTIONS
# ********************

# *********************
# Show Sequencer
# *********************

    def track_timeout_callback(self):
        self.do_play(self.first_track_ref,'front','timeout')


    def do_play(self,track_ref,edge,source):
        if track_ref != self.current_track_ref:
            # cancel the show timeout when playing another track
            if self.show_timeout_timer is not None:
                self.canvas.after_cancel(self.show_timeout_timer)
                self.show_timeout_timer=None
            self.next_track_signal=True
            self.next_track_op='play'
            self.next_track_arg=track_ref
            if self.shower is not None:
                self.shower.input_pressed('stop',edge,source)
            elif self.current_player is not None:
                self.current_player.input_pressed('stop')
            else:
                self.what_next_after_showing()



    def do_first_track(self):
        # get first-track from profile
        self.first_track_ref=self.show_params['first-track-ref']

        # find the track-ref in the medialisst
        index = self.medialist.index_of_track(self.first_track_ref)
        if index >=0:
            # don't use select the track as not using selected_track in radiobuttonshow
            self.current_track_ref=self.first_track_ref
            # start the show timer when displaying the first track
            if self.show_timeout_timer is not None:
                self.canvas.after_cancel(self.show_timeout_timer)
                self.show_timeout_timer=None
            if int(self.show_params['show-timeout']) != 0:
                self.show_timeout_timer=self.canvas.after(int(self.show_params['show-timeout'])*1000 ,self.show_timeout_stop)

            # and load it
            self.start_load_show_loop(self.medialist.track(index))
        else:
            self.mon.err(self,"first-track not found in medialist: "+ self.show_params['first-track-ref'])
            self.end('error',"first track not found in medialist")


# *********************
# Playing show or track
# *********************

    def start_load_show_loop(self,selected_track):
        # shuffle players
        Show.base_shuffle(self)

        self.mon.trace(self,'')
        
        self.display_eggtimer(Show.base_resource(self,'radiobuttonshow','m01'))

        if self.track_timeout_timer is not None:
            self.canvas.after_cancel(self.track_timeout_timer)
            self.track_timeout_timer=None

        # start timeout for the track if required           
        if self.current_track_ref != self.first_track_ref and int(self.show_params['track-timeout']) != 0:
            self.track_timeout_timer=self.canvas.after(int(self.show_params['track-timeout'])*1000,self.track_timeout_callback)
            
        # load the track or show
        # params - track,, track loaded callback, end eshoer callback,enable_menu
        Show.base_load_track_or_show(self,selected_track,self.what_next_after_load,self.end_shower,False)


   # track has loaded so show it.
    def what_next_after_load(self,status,message):
        self.mon.trace(self, 'load complete with status: ' + status + '  message: ' +message)
        if self.current_player.play_state == 'load-failed':
            self.req_next='error'
            self.what_next_after_showing()
        else:
            if self.show_timeout_signal is True  or self.terminate_signal is True or self.exit_signal is True or self.user_stop_signal is True:
                self.what_next_after_showing()
            else:
                self.mon.trace(self, '- showing track')
                self.current_player.show(self.track_ready_callback,self.finished_showing,self.closed_after_showing)


    

    def finished_showing(self,reason,message):
        # showing has finished with 'pause at end', showing the next track will close it after next has started showing
        self.mon.trace(self,' - pause at end')
        self.mon.log(self,"pause at end of showing track with reason: "+reason+ ' and message: '+ message)
        self.sr.hide_click_areas(self.links)
        if self.current_player.play_state == 'show-failed':
            self.req_next = 'error'
        else:
            self.req_next='finished-player'
        self.what_next_after_showing()

    def closed_after_showing(self,reason,message):
        # showing has finished with closing of player but track instance is alive for hiding the x_content
        self.mon.trace(self, '- closed after showing')
        self.mon.log(self,"Closed after showing track with reason: "+reason+ ' and message: '+ message)
        self.sr.hide_click_areas(self.links)
        if self.current_player.play_state == 'show-failed':
            self.req_next = 'error'
        else:
            self.req_next='closed-player'
        self.what_next_after_showing()


    # subshow or child show has ended
    def end_shower(self,show_id,reason,message):
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ': Returned from shower with ' + reason +' ' + message)
        self.sr.hide_click_areas(self.links)
        self.req_next=reason
        Show.base_end_shower(self)
        self.what_next_after_showing()

           

    def what_next_after_showing(self):
        self.mon.trace(self, '')

        # need to terminate
        if self.terminate_signal is True:
            self.terminate_signal=False
            # what to do when closed or unloaded
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
            # what to do when closed or unloaded
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

        # user has selected another track
        elif self.next_track_signal is True:
            self.next_track_signal=False
            self.current_track_ref=self.next_track_arg                         
            index = self.medialist.index_of_track(self.current_track_ref)
            if index >=0:
                # don't use select the track as not using selected_track in radiobuttonshow
                # and load it
                self.start_load_show_loop(self.medialist.track(index))
            else:
                self.mon.err(self,"next track not found in medialist: "+ self.current_track_ref)
                self.end('error',"next track not found in medialist")
                    
        else:
            # track ends naturally or is quit so go back to first track
            self.do_first_track()


# *********************
# Interface with other shows/players to reduce black gaps
# *********************

    # called just before a track is shown to remove the  previous track from the screen
    # and if necessary close it
    def track_ready_callback(self,enable_show_background):
        self.delete_eggtimer()
        # enable the click-area that are in the list of links
        self.sr.enable_click_areas(self.links)
        Show.base_track_ready_callback(self,enable_show_background)

    # callback from begining of a subshow, provide previous shower player to called show        
    def subshow_ready_callback(self):
        return Show.base_subshow_ready_callback(self)


    
# *********************
# End the show
# *********************
    def end(self,reason,message):
        self.stop_timers()
        Show.base_end(self,reason,message)


    def stop_timers(self):
        if self.show_timeout_timer is not None:
            self.canvas.after_cancel(self.show_timeout_timer)
            self.show_timeout_timer=None   
        if self.track_timeout_timer is not None:
            self.canvas.after_cancel(self.track_timeout_timer)
            self.track_timeout_timer=None  
           




