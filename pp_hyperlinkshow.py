from pp_medialist import MediaList
from pp_pathmanager import PathManager
from pp_screendriver import ScreenDriver
from pp_show import Show


class HyperlinkShow(Show):
    """
        Aimed at touchscreens but can be used for any purpose where the user is required to follow hyperlinks between tracks
        Profiles for media tracks (message, image, video, audio ) specify links to other tracks
        In a link a symbolic name of an input is associated with a track-reference
        The show begins at a special track specified in the profiile called the First Track and moves to other tracks
         - when a link is executed by a input event with a specified symbolic name
        -  at the natural end of the track using the special pp-onend symbolic name
        If using the 'call' link command PP keeps a record of the tracks it has visited so the 'return' command can go back.
        Executes timeout-track if no user input is received (includes pp-onend but not repeat)

        There is a another special track with Home Track. The home command returns here and the 'return n' command will not go back past here.
        This was designed to allow the timeout to go back to First Track which would advertise the show.
        Once the user had been enticed and clicked a link to move to Home pressing home or return would not return him to First Track

        You can make the Home Track and the First Track the same track if you want.
        You may want a track, if it is a video or audio track, to repeat. You can use repeat for this and it will not cancel the timeout.
        
        Image and message tracks can have a zero duration so they never end naturally so repeat is not required.

        links are of the form:
           symbolic-name command [track-ref]
        
        link commands:
          call <track-ref> play track-ref and add it to the path
          return - return 1 back up the path removing the track from the path, stops at home-track.
          return n - return n tracks back up the path removing the track from the path, stops at home-track.
          return <track-ref> return to <track-ref> removing tracks from the path
          home  - return to home-track removing tracks from the path
          jump <track-ref-> - play track-ref forgetting the path back to home-track
          goto <track-ref> - play track-ref, forget the path
          repeat - repeat the track
          exit - end the hyperlink show
          null - inhibits the link defined in the show with the same symbolic name.

          reserved symbolic names
          pp-onend command  - pseudo symbolic name for end of a track

    interface:
        * __init__ - initlialises the show
         * play - selects the first track to play (first-track) 
         * input_pressed,  - receives user events passes them to a Shower/Player if a track is playing,
                otherwise actions them depending on the symbolic name supplied
        * managed_stop  - stops the show from another show
        * terminate  - aborts the show, used whan clsing or after errors
        * track_ready_callback - called by the next track to be played to remove the previous track from display
        * subshow_ready_callback - called by the subshow to get the last track of the parent show
        * subshow_ended_callback - called at the start of a parent show to get the last track of the subshow
        
    """

# *********************
# external interface
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

        # create a path stack
        self.path = PathManager()

        # instatiatate the screen driver - used only to access enable and hide click areas
        self.sr=ScreenDriver()
        
        # init variables
        self.track_timeout_timer=None
        self.show_timeout_timer=None
        self.next_track_signal=False
        self.next_track_ref=''
        self.current_track_ref=''
        self.current_track_type=''


    def play(self,end_callback,show_ready_callback,direction_command,level):
        """ starts the hyperlink show at start-track 
              end_callback - function to be called when the show exits
              show_ready_callback - callback to get previous show and track
              level is 0 when the show is top level (run from [start] or from show control)
              direction_command is not used oassed to subshow
        """
        # need to instantiate the medialist here as in gapshow done in derived class
        self.medialist=MediaList()        

        Show.base_play(self,end_callback,show_ready_callback, direction_command,level)
        
        if self.trace: print '\n\nHYPERLINKSHOW/play ',self.show_params['show-ref']
        
 
        # read show destinations
        self.first_track_ref=self.show_params['first-track-ref']
        self.home_track_ref=self.show_params['home-track-ref']
        self.timeout_track_ref=self.show_params['timeout-track-ref']

  
        # get the previous player from calling show
        Show.base_get_previous_player_from_parent(self)
        # and delete eggtimer
        if self.previous_shower is not None:
            self.previous_shower.delete_eggtimer()
        
        self.do_first_track()

        
# stop received from another concurrent show via ShowManager

    def managed_stop(self):
        self.stop_timers()
        Show.base_managed_stop(self)

    #  show timeout happened
    def show_timeout_stop(self):
        self.stop_timers()
        Show.base_show_timeout_stop(self)                
  
       
    # kill or error
    def terminate(self,reason):
        self.stop_timers()
        Show.base_terminate(self,reason)

          

   # respond to inputs
    def input_pressed(self,symbol,edge,source):

        self.mon.log(self,"received symbol: " + symbol)
        
        # does the symbol match a link, if so execute it
        if self.try_link(symbol,edge,source) is True:
            return
        
        # controls are disabled so ignore anything else
        if self.show_params['disable-controls'] == 'yes':
            return

        # does it match a control       
        # if at top convert symbolic name to operation otherwise lower down we have received an operatio    
        # look through list of controls to find match
        if self.level == 0:
            operation=Show.base_lookup_control(self,symbol,self.controls_list)
        else:
            operation=symbol
        # print 'operation',operation 
        if operation != '':
            self.do_operation(operation,edge,source)



    def do_operation(self,operation,edge,source):
        if self.shower is not None:
            # if next lower show is running pass down to stop the show and lower level
            self.shower.input_pressed(operation,edge,source) 
        else:        
            # control this show and its tracks
            # ?????? should stop from first track get out of the show
            if self.trace: print 'hyperlinkshow/input_pressed ',operation
            if operation == 'stop':
                self.stop_timers()
                if self.current_player is not  None:
                    if self.current_track_ref == self.first_track_ref and self.level != 0:
                        self.user_stop_signal=True
                    self.current_player.input_pressed('stop')

            elif operation == 'pause':
                if self.current_player != None:
                    self.current_player.input_pressed(operation)

            elif operation[0:4] == 'omx-' or operation[0:6] == 'mplay-'or operation[0:5] == 'uzbl-':
                if self.current_player is not None:
                    self.current_player.input_pressed(operation)

   
    def try_link(self,symbol,edge,source):
        # find the first entry in links that matches the symbol and execute its operation
        print 'hyperlinkshow ',symbol
        found,link_op,link_arg=self.path.find_link(symbol,self.links)
        if found is True:
            #cancel the show timeout when playing another track
            if self.show_timeout_timer != None:
                self.canvas.after_cancel(self.show_timeout_timer)
                self.show_timeout_timer=None
            print 'match',link_op
            if link_op == 'home':
                self.do_home(edge,source)
            elif link_op  == 'return':
                self.do_return(link_arg,edge,source)
            elif link_op  == 'call':
                self.do_call(link_arg,edge,source)
            elif link_op  == 'goto':
                self.do_goto(link_arg,edge,source)
            elif link_op  == 'jump':
                self.do_jump(link_arg,edge,source)
            elif link_op  ==  'repeat':
                self.do_repeat(edge,source)
            elif link_op == 'exit':
                self.end('normal','executed exit command')
        return found





# *********************
# INTERNAL FUNCTIONS
# ********************

# *********************
# Show Sequencer
# *********************


    def track_timeout_callback(self):
        if self.trace: print '\nhyperlinkshow/Timeout Event - goto',self.timeout_track_ref
        self.do_goto(self.timeout_track_ref,'front','timeout')


    def do_call(self,track_ref,edge,source):
        if track_ref != self.current_track_ref:
            self.mon.log(self, 'call: '+track_ref)
            self.next_track_signal=True
            self.next_track_op='call'
            self.next_track_arg=track_ref
            if self.shower != None:
                self.shower.input_pressed('stop',edge,source)
            elif self.current_player != None:
                self.current_player.input_pressed('stop')
            else:
                self.what_next_after_showing()


    def do_goto(self,to,edge,source):
        self.mon.log(self,'goto: '+to)
        self.next_track_signal=True
        self.next_track_op='goto'
        self.next_track_arg=to
        if self.shower != None:
            self.shower.input_pressed('stop',edge,source)
        elif self.current_player != None:
            print 'current stopped',self.current_player
            self.current_player.input_pressed('stop')
        else:
            self.what_next_after_showing()

    def do_jump(self,to,edge,source):
        self.mon.log(self,'jump to: '+to)
        self.next_track_signal=True
        self.next_track_op='jump'
        self.next_track_arg=to
        if self.shower != None:
            self.shower.input_pressed('stop',edge,source)
        elif self.current_player != None:
            self.current_player.input_pressed('stop')
        else:
            self.what_next_after_showing()

    def do_repeat(self,edge,source):
        self.mon.log(self,'repeat: ')
        self.next_track_signal=True
        self.next_track_op='repeat'
        if self.shower != None:
            self.shower.input_pressed('stop',edge,source)
        elif self.current_player != None:
            self.current_player.input_pressed('stop')
        else:
            self.what_next_after_showing()
                
    def do_return(self,to,edge,source):
        self.next_track_signal=True
        if to.isdigit() or to == '':
            self.mon.log(self,'hyperlink command - return by: '+to)
            self.next_track_op='return-by'
            if to  ==  '':
                self.next_track_arg='1'
            else:    
                self.next_track_arg=to
        else:
            self.mon.log(self,'hyperlink command - return to: '+to)
            self.next_track_op='return-to'
            self.next_track_arg=to        
        if self.shower != None:
            self.shower.input_pressed('stop',edge,source)
        elif self.current_player != None:
            self.current_player.input_pressed('stop')
        else:
            self.what_next_after_showing()
        
    def do_home(self,edge,source):
        self.mon.log(self,'hyperlink command - home')
        self.next_track_signal=True
        self.next_track_op='home'
        if self.shower != None:
            self.shower.input_pressed('stop',edge,source)
        elif self.current_player != None:
            self.current_player.input_pressed('stop')
        else:
            self.what_next_after_showing()


    def do_first_track(self):
        index = self.medialist.index_of_track(self.first_track_ref)
        if index >=0:
            self.continue_timeout=False
            # don't use select the track as not using selected_track in hyperlinkshow            
            first_track=self.medialist.track(index)
            self.current_track_ref=first_track['track-ref']
            self.path.append(first_track['track-ref'])
            if self.trace:
                print '\nFirst Track',first_track['track-ref']
                self.path.print_path()
            self.start_load_show_loop(first_track)
        else:
            self.mon.err(self,"first-track not found in medialist: "+ self.show_params['first-track-ref'])
            self.end('error',"first track not found in medialist")


    def start_load_show_loop(self,selected_track):
        # shuffle players
        Show.base_shuffle(self)

        if self.trace: print 'hyperlinkshow/start_load_show_loop'
                                      
        self.display_eggtimer(Show.base_resource(self,'hyperlinkshow','m01'))


        # start the show timer when displaying the first track
        if self.current_track_ref == self.first_track_ref:
            if self.show_timeout_timer != None:
                self.canvas.after_cancel(self.show_timeout_timer)
                self.show_timeout_timer=None
            if int(self.show_params['show-timeout']) != 0:
                self.show_timeout_timer=self.canvas.after(int(self.show_params['show-timeout'])*1000 ,self.show_timeout_stop)

        
       # start timeout for the track if required   ???? differnet to radiobuttonshow
        if self.continue_timeout is False:
            if self.track_timeout_timer != None:
                self.canvas.after_cancel(self.track_timeout_timer)
                self.track_timeout_timer=None
            if self.current_track_ref != self.first_track_ref and int(self.show_params['track-timeout']) != 0:
                self.track_timeout_timer=self.canvas.after(int(self.show_params['track-timeout'])*1000,self.track_timeout_callback)


        # read the show links. Track links will be added by track_ready_callback
        # needs to be done in loop as each track adds different links o the show links
        links_text=self.show_params['links']
        reason,message,self.links=self.path.parse_links(links_text)
        if reason == 'error':
            self.mon.err(self,message + " in show")
            self.end('error',message)

        # load the track or show
        # params - track,, track loaded callback, end eshoer callback,enable_menu
        Show.base_load_track_or_show(self,selected_track,self.what_next_after_load,self.end_shower,False)


   # track has loaded so show it.
    def what_next_after_load(self,status,message):
        if self.trace: print 'hyperlinkshow/what_next_after_load - load complete with status: ',status,'  message: ',message
        if self.current_player.play_state == 'load_failed':
            self.mon.err(self,'load failed')
            self.terminate_signal=True
            self.what_next_after_showing()
        else:
            if self.show_timeout_signal is True  or self.terminate_signal is True or self.stop_command_signal is True or self.user_stop_signal is True:
                self.what_next_after_showing()
            else:
                if self.trace: print 'show/what_next_after_load- showing track'
                self.current_player.show(self.track_ready_callback,self.finished_showing,self.closed_after_showing)


    def finished_showing(self,reason,message):
        # showing has finished with 'pause at end'. Player is paused and track instance is alive for hiding the x_content
        # this will happen in track_ready_callback of next track or in end?????
        if self.trace: print 'hyperlinkshow/finished_showing - pause at end'
        self.mon.log(self,"pause at end of showing track with reason: "+reason+ ' and message: '+ message)
        self.sr.hide_click_areas(self.canvas)
        self.what_next_after_showing()


    def closed_after_showing(self,reason,message):
        # showing has finished with closing of player. Track instance is alive for hiding the x_content
        # this will happen in track_ready_callback of next track or in end?????
        if self.trace: print 'hyperlinkshow/closed_after_showing - closed after showing'
        self.mon.log(self,"Closed after showing track with reason: "+reason+ ' and message: '+ message)
        self.sr.hide_click_areas(self.canvas)
        self.what_next_after_showing()


    # subshow or child show has ended
    def end_shower(self,show_id,reason,message):
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ': Returned from shower with ' + reason +' ' + message)                                     
        self.sr.hide_click_areas(self.canvas)
        Show.base_end_shower(self)
        self.what_next_after_showing()


        
    
    def what_next_after_showing(self):
        if self.trace: print 'hyperlinkshow/what_next_after_showing '

        # need to terminate
        if self.terminate_signal is True:
            self.terminate_signal=False
            # what to do when closed or unloaded
            self.ending_reason='terminate'
            Show.base_close_or_unload(self)

        # show timeout
        elif self.show_timeout_signal is True:
            self.show_timeout_signal=False
            # what to do when closed or unloaded
            self.ending_reason='show-timeout'
            Show.base_close_or_unload(self)
            
        # used by managed_stop for stopping show from other shows. 
        elif self.stop_command_signal is True:
            self.stop_command_signal=False
            self.ending_reason='stop-command'
            Show.base_close_or_unload(self)

        # user wants to stop
        elif self.user_stop_signal is True:
            self.user_stop_signal=False
            self.ending_reason='user-stop'
            Show.base_close_or_unload(self)

        # user has selected another track
        elif self.next_track_signal is True:
            print self.next_track_signal,self.next_track_op
            self.next_track_signal=False
            self.continue_timeout=False

            # home
            if self.next_track_op in ('home'):
                # back to 1 before home
                back_ref=self.path.back_to(self.home_track_ref)
                if back_ref == '':
                    self.mon.err(self,"home - home track not in path: "+self.home_track_ref)
                    self.end('error',"home - home track not in path")
                # play home
                self.next_track_ref=self.home_track_ref
                self.path.append(self.next_track_ref)
                if self.trace:
                    print '\nExecuted Home'
                    self.path.print_path()

            # return-by
            elif self.next_track_op in ('return-by'):
                if self.current_track_ref != self.home_track_ref:
                    # back n stopping at home
                    # back one more and return it
                    back_ref=self.path.back_by(self.home_track_ref,self.next_track_arg)
                    # use returned track
                    self.next_track_ref=back_ref
                    self.path.append(self.next_track_ref)
                    if self.trace:
                        print '\nExecuted Return',self.next_track_arg
                        self.path.print_path()

            # repeat is return by 1
            elif self.next_track_op in ('repeat'):
                    # print 'current', self.current_track_ref
                    # print 'home', self.home_track_ref
               # if self.current_track_ref != self.home_track_ref:
                    self.path.pop_for_sibling()
                    self.next_track_ref=self.current_track_ref
                    self.path.append(self.current_track_ref)
                    self.continue_timeout=True
                    if self.trace:
                        print '\nExecuted Repeat'
                        self.path.print_path()

            # return-to
            elif self.next_track_op in ('return-to'):
                # back to one before return-to track
                back_ref=self.path.back_to(self.next_track_arg)
                if back_ref == '':
                    self.mon.err(self,"return-to - track not in path: "+self.next_track_arg)
                    self.end('error',"return-to - track not in path")
                # and append the return to track
                self.next_track_ref=self.next_track_arg
                self.path.append(self.next_track_ref)
                if self.trace:
                    print '\nExecuted Return',self.next_track_arg
                    self.path.print_path()
                
            # call
            elif self.next_track_op in ('call'):
                # append the required track
                self.path.append(self.next_track_arg)
                self.next_track_ref=self.next_track_arg
                if self.trace:
                    print '\nExecuted Call',self.next_track_arg
                    self.path.print_path()

            # goto
            elif self.next_track_op in ('goto'):
                self.path.empty()
                # add the goto track
                self.next_track_ref=self.next_track_arg
                self.path.append(self.next_track_arg)
                if self.trace:
                    print '\nExecuted Goto',self.next_track_arg
                    self.path.print_path()

            # jump
            elif self.next_track_op in ('jump'):
                # back to home and remove it
                back_ref=self.path.back_to(self.home_track_ref)
                if back_ref == '':
                    self.mon.err(self,"jump - home track not in path: "+self.home_track_ref)
                    self.end('error',"jump - track not in path")
                # add back the home track without playing it
                self.path.append(self.home_track_ref)
                # append the jumped to track
                self.next_track_ref=self.next_track_arg
                self.path.append(self.next_track_ref)
                if self.trace:
                    print '\nExecuted Jump',self.next_track_arg
                    self.path.print_path()

            else:
                self.mon.err(self,"unaddressed what next: "+ self.next_track_op+ ' '+self.next_track_arg)
                self.end('error',"unaddressed what next")
            
            self.current_track_ref=self.next_track_ref                    
            index = self.medialist.index_of_track(self.next_track_ref)
            if index >=0:
                # don't use select the track as not using selected_track in hyperlinkshow
                self.start_load_show_loop(self.medialist.track(index))

            else:
                self.mon.err(self,"next-track not found in medialist: "+ self.next_track_ref)
                self.end('error',"next track not found in medialist")
                
        else:
            # track ends naturally so look to see if there is a pp-onend link
            found,self.next_track_op,self.next_track_arg=self.path.find_link('pp-onend',self.links)
            if found is True:
                self.next_track_signal=True
                self.what_next_after_showing()



    def track_ready_callback(self):
        # called from a Player when ready to play, merge the links from the track with those from the show
        # and then enable the click areas
        self.delete_eggtimer()                         
        links_text=self.current_player.get_links()
        reason,message,track_links=self.path.parse_links(links_text)
        if reason == 'error':
            self.mon.err(self,message + " in page")
            self.end('error',message)
        self.path.merge_links(self.links,track_links)
        
        # enable the click-area that are in the list of links
        self.sr.enable_click_areas(self.links,self.canvas)
        
        Show.base_track_ready_callback(self)





    # callback from begining of a subshow, provide previous shower and player to called show        
    def subshow_ready_callback(self):
        # in a show can only use 'show' links to define click areas
        self.sr.enable_click_areas(self.links,self.canvas)
        return Show.base_subshow_ready_callback(self)              
    
    # called by end_shower of a parent show  to get the last track of the subshow
    def subshow_ended_callback(self):
        return Show.base_subshow_ended_callback(self)




# *********************
# End the show
# *********************
    # finish the player for killing, error or normally
    # this may be called directly sub/child shows or players are not running
    # if they might be running then need to call terminate.

    def end(self,reason,message):
        self.mon.log(self,"Ending hyperlinkshow: "+ self.show_params['show-ref'])
        self.stop_timers()
        Show.base_end(self,reason,message)


    def stop_timers(self):
        pass
