# 1/2/2016 add write_stats
# 4/11/2016 write stats for each track (commented out)

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
        self.error_signal=False
        self.show_timeout_signal=False
        
        self.req_next='nil'
        self.state='closed'

        self.count=0
        self.interval=0
        self.duration=0
        self.controls_list=[]
        self.enable_hint= True
        self.escapetrack_required=False
        

    def play(self,end_callback,show_ready_callback, parent_kickback_signal,level,controls_list):
        self.mon.newline(3)
        self.mon.trace(self, self.show_params['show-ref'])
             
        Show.base_play(self,end_callback,show_ready_callback,parent_kickback_signal, level,controls_list)

        # unpack show parameters

        reason,message,self.show_timeout = Show.calculate_duration(self,self.show_params['show-timeout'])
        if reason=='error':
            self.mon.err(self,'ShowTimeout has bad time: '+self.show_params['show-timeout'])
            self.end('error','ShowTimeout has bad time: '+self.show_params['show-timeout'])
            
        self.track_count_limit = int(self.show_params['track-count-limit'])
            
        reason,message,self.interval = Show.calculate_duration (self, self.show_params['interval'])
        if reason=='error':
            self.mon.err(self,'Interval has bad time: '+self.show_params['interval'])
            self.end('error','Interval has bad time: '+self.show_params['interval'])

        if self.medialist.anon_length()==0 and self.show_params['type'] not in ('liveshow','artliveshow'):
            self.mon.err(self,'No anonymous tracks in medialist ')
            self.end('error','No anonymous tracks in medialist ')
               

        # delete eggtimer started by the parent
        if self.previous_shower is not None:
            self.previous_shower.delete_eggtimer()
            
        self.start_show()


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
    def handle_input_event(self,symbol):
        Show.base_handle_input_event(self,symbol)

    def handle_input_event_this_show(self,symbol):
        #  check symbol against mediashow triggers
        if self.state == 'waiting' and self.show_params['trigger-start-type'] in ('input','input-persist') and symbol  ==  self.show_params['trigger-start-param']:
            self.mon.stats(self.show_params['type'],self.show_params['show-ref'],self.show_params['title'],'start trigger',
                            '','','')
            Show.delete_admin_message(self)
            self.start_list()
            
        elif self.state == 'playing' and self.show_params['trigger-end-type'] == 'input' and symbol == self.show_params['trigger-end-param']:
            self.end_trigger_signal=True
            if self.shower is not None:
                self.shower.do_operation('stop')
            elif self.current_player is not None:
                self.current_player.input_pressed('stop')
                
        elif self.state == 'playing' and self.show_params['trigger-next-type'] == 'input' and symbol == self.show_params['trigger-next-param']:
            self.mon.stats(self.show_params['type'],self.show_params['show-ref'],self.show_params['title'],'next trigger',
                            '','','')
            self.next()
        else:
            # event is not a trigger so must be internal operation
            operation=self.base_lookup_control(symbol,self.controls_list)
            if operation != '':
                self.do_operation(operation)


    # overrides base
    # service the standard operations for this show
    def do_operation(self,operation):
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
            # print '\nUP'
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
                    self.mon.stats(self.show_params['type'],self.show_params['show-ref'],self.show_params['title'],'start trigger',
                            '','','')
                    Show.delete_admin_message(self)
                    self.start_list()

        elif operation in ('pause','pause-on','pause-off','mute','unmute','go'):
            if self.current_player is not None:
                self.current_player.input_pressed(operation)

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
            self.shower.do_operation('stop')
        else:
            if self.current_player is not None:
                self.current_player.input_pressed('stop')


    def previous(self):
        self.previous_track_signal=True
        if self.shower is not None:
            self.shower.do_operation('stop')
        else:
            if self.current_player is not None:
                self.current_player.input_pressed('stop')


# ***************************
# Show sequencing
# ***************************

    def start_show(self):
        # initial direction from parent show
        
        self.kickback_for_next_track=self.parent_kickback_signal
        # print '\n\ninital KICKBACK from parent', self.kickback_for_next_track
   
        # start duration timer
        if self.show_timeout  != 0:
            # print 'set alarm ', self.show_timeout
            self.duration_timer = self.canvas.after(self.show_timeout*1000,self.show_timeout_stop)

        self.first_list=True

        # and start the first list of the show
        self.wait_for_trigger()

    
    def wait_for_trigger(self):
        
        # wait for trigger sets the state to waiting so that trigger events can do a start_list.
        self.state='waiting'

        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Waiting for trigger: "+ self.show_params['trigger-start-type'])

  
        if self.show_params['trigger-start-type'] == "input":
            
            #close the previous track to display admin message
            Show.base_shuffle(self)
            Show.base_track_ready_callback(self,False)
            Show.display_admin_message(self,self.show_params['trigger-wait-text'])

        elif self.show_params['trigger-start-type'] == "input-persist":
            if self.first_list ==True:
                #first time through track list so play the track without waiting to get to end.
                self.start_list()
            else:
                #wait for trigger while displaying previous track
                pass

        elif self.show_params['trigger-start-type'] == "start":
            # don't close the previous track to give seamless repeat of the show
            self.start_list()
            
        else:
            self.mon.err(self,"Unknown trigger: "+ self.show_params['trigger-start-type'])
            self.end('error',"Unknown trigger: "+ self.show_params['trigger-start-type'])


    # timer for repeat=interval
    def end_interval_timer(self):
        self.interval_timer_signal=True
        # print 'INTERVAL TIMER ended'
        if self.shower is not None:
            self.shower.do_operation('stop')
        elif self.current_player is not None:
            self.current_player.input_pressed('stop')       

    #  show timeout happened
    def show_timeout_stop(self):
        self.stop_timers()
        Show.base_show_timeout_stop(self)
        

    def start_list(self):
        # starts the list or any repeat having waited for trigger first.
        self.state='playing'

        # initialise track counter for the list
        self.track_count=0
       
        # start interval timer
        self.interval_timer_signal = False
        if self.interval != 0:
            self.interval_timer=self.canvas.after(self.interval*1000,self.end_interval_timer)

        # print '\nSTART LIST', self.first_list
        if  self.first_list is True:
            # first list so go to what next
            self.what_next_after_showing()
        else:
            #get first or last track depending on direction
            if self.kickback_for_next_track is True:
                self.medialist.finish()
            else:
                self.medialist.start()
            self.start_load_show_loop(self.medialist.selected_track())



# ***************************
# Track load/show loop
# ***************************  

    # track playing loop starts here
    def start_load_show_loop(self,selected_track):

        # uncomment the next line to write stats for every track
        # Show.write_stats(self,'play a track',self.show_params,selected_track)
        
        # shuffle players
        Show.base_shuffle(self)
        
        self.delete_eggtimer()

        # is child track required
        if self.show_params['child-track-ref'] != '':
            self.enable_child=True
        else:
            self.enable_child=False

    

        # load the track or show
        # params - track,enable_menu
        enable=self.enable_child & self.enable_hint
        Show.base_load_track_or_show(self,selected_track,self.what_next_after_load,self.end_shower,enable)
        

    # track has loaded so show it.
    def what_next_after_load(self,status,message):
        self.mon.log(self,'Show Id ' + str(self.show_id)+' load complete with status: ' + status +'  message: ' +message)
        if self.current_player.play_state == 'load-failed':
            self.error_signal=True
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
            self.error_signal=True
        else:
            self.req_next='finished-player'
        # showing has finished with 'pause at end', showing the next track will close it after next has started showing
        self.mon.trace(self, ' - pause at end ')
        self.mon.log(self,"pause at end of showing track with reason: "+reason+ ' and message: '+ message)
        self.what_next_after_showing()


    def closed_after_showing(self,reason,message):
        self.sr.hide_click_areas(self.controls_list)
        if self.current_player.play_state == 'show-failed':
            self.error_signal=True
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
        state += '\n* error signal ' + str(self.error_signal)
        state += '\n* req_next used to indicate subshow reports an error ' + self.req_next
        state += '\n* exit signal ' +  str(self.exit_signal)
        state += '\n* show timeout  signal ' + str(self.show_timeout_signal)
        state += '\n* user stop  signal ' + str(self.user_stop_signal)
        state += '\n* previous track  signal ' + str(self.previous_track_signal)
        state += '\n* next track  signal ' + str(self.next_track_signal)
        state += '\n* kickback from subshow ' + str(self.subshow_kickback_signal)
        return state +'\n'
        

    def what_next_after_showing(self):
        # print 'WHAT NEXT'
        self.mon.trace(self,self.pretty_what_next_after_showing_state())
                        
        self.track_count+=1
        # set false when child rack is to be played
        self.enable_hint=True

        # first of all deal with conditions that do not require the next track to be shown
        # some of the conditions can happen at any time, others only when a track is closed or at pause_at_end

        # need to terminate
        if self.terminate_signal is True:
            self.terminate_signal=False
            self.stop_timers()
            # set what to do after closed or unloaded
            self.ending_reason='killed'
            Show.base_close_or_unload(self)

        elif self.error_signal== True or self.req_next=='error':
            self.error_signal=False
            self.req_next=''
            self.stop_timers()
            # set what to do after closed or unloaded
            self.ending_reason='error'
            Show.base_close_or_unload(self)

        # used for exiting show from other shows, time of day, external etc.
        elif self.exit_signal is True:
            self.exit_signal=False
            self.stop_timers()
            self.ending_reason='exit'
            Show.base_close_or_unload(self)

        #  show timeout
        elif self.show_timeout_signal is True:
            self.show_timeout_signal=False
            self.stop_timers()
            self.ending_reason='user-stop'
            Show.base_close_or_unload(self)

        # user wants to stop the show
        elif self.user_stop_signal is True:
            self.user_stop_signal=False
            # print 'user stop'
            self.stop_timers()
            self.ending_reason='user-stop'
            Show.base_close_or_unload(self)


       # interval > 0. If last track has finished we are waiting for interval timer before ending the list
       # note: if medialist finishes after interval is up then this route is used to start trigger. 
        elif self.waiting_for_interval is True:
            # interval_timer_signal set by alarm clock started in start_list
            if self.interval_timer_signal is True:
                self.interval_timer_signal=False
                self.waiting_for_interval=False
                # print 'RECEIVED INTERVAL TIMER SIGNAL'
                if self.show_params['repeat']=='repeat':
                    self.wait_for_trigger()
                else:
                    self.stop_timers()
                    self.ending_reason='user-stop'
                    Show.base_close_or_unload(self)
            else:
                self.poll_for_interval_timer=self.canvas.after(1000,self.what_next_after_showing)

        else:
            self.medialist.create_new_livelist()
            escapetrack_required=self.escapetrack_required
            self.escapetrack_required=False
            # print escapetrack_required,self.medialist.new_length()
            if escapetrack_required is True and self.medialist.new_length() == 0:
                # print 'use escape track'
                index = self.medialist.index_of_track(self.show_params['escape-track-ref'])
                self.mon.log(self,'Starting Escape Track: '+ self.show_params['escape-track-ref'])
                if index >=0:
                    # don't use select the track as need to preserve mediashow sequence for returning from esacpe track
                    escape_track=self.medialist.track(index)
                    Show.write_stats(self,'play escape track',self.show_params,escape_track)
                    self.display_eggtimer()
                    # use new empty livelist so if changed works OK when return from empty track
                    self.medialist.use_new_livelist()
                    self.start_load_show_loop(escape_track)
                else:
                    self.mon.err(self,"Escape Track empty")
                    self.end('error',"Escape Track empty")

            # print 'FOR IF CHANGED',self.first_list,self.medialist.length(),self.medialist.new_length(),self.medialist.livelist_changed()
            elif self.first_list is True or self.medialist.livelist_changed() is True or (self.medialist.length() == 0 and self.medialist.new_length() == 0):                            

                if self.first_list is False:
                    # do show control
                    if self.medialist.length() == 0 and self.medialist.new_length() != 0:
                            # print 'show control empty to not empty'
                            # do show control when goes from not empty to empty only
                            self.show_control(self.show_params['show-control-not-empty'])
                            
                    elif self.medialist.length() != 0 and self.medialist.new_length() == 0:
                            # print 'show control not empty to empty'
                            # do show control when goes from empty to not empty only
                            self.show_control(self.show_params['show-control-empty'])  

                self.first_list=False
                
                if self.medialist.new_length()==0 and self.show_params['repeat']=='repeat':
                    # start empty track/show
                    index = self.medialist.index_of_track(self.show_params['empty-track-ref'])
                    self.mon.log(self,'Starting Empty Track: '+ self.show_params['empty-track-ref'])
                    if index >=0:
                        # don't use select the track as need to preserve mediashow sequence for returning from empty track/show
                        empty_track=self.medialist.track(index)
                        # print 'play empty track', empty_track['title'],empty_track['type']
                        Show.write_stats(self,'play empty track',self.show_params,empty_track)
                        if empty_track['type'] =='show':
                            self.escapetrack_required=True
                        
                        self.display_eggtimer()
                        # use new empty livelist so if changed works OK when return from empty track
                        self.medialist.use_new_livelist()
                        self.start_load_show_loop(empty_track)
                    else:
                        self.mon.err(self,"List Empty Track not specified")
                        self.end('error',"List Empty Track not specified")
  

                elif self.medialist.new_length()==0 and self.show_params['repeat']=='single-run':
                    if self.level != 0:
                        self.kickback_for_next_track=False
                        self.subshow_kickback_signal=False
                        self.end('normal',"End of single run - Return from Sub Show")
                    else:
                        # end of single run and at top - exit the show
                        self.stop_timers()
                        self.ending_reason='user-stop'
                        Show.base_close_or_unload(self)

                else:
                    #changed but new is not zero
                    self.medialist.use_new_livelist()
                    # print 'livelist changed and not empty'
                    self.start_list()               


            # otherwise consider operation that might show the next track          
            else:
                # print 'ELSE',self.medialist.at_end()
                # report error if medilaist is empty (liveshow will not get this far
                if self.medialist.length()==0:
                    self.mon.err(self,"Medialist empty")
                    self.end('error',"Medialist empty")
                    
                # setup default direction for next track as normally goes forward unless kicked back
                self.kickback_for_next_track=False
                # print 'init direction to False at begin of what_next_after showing', self.kickback_for_next_track
                # end trigger from input, or track count
                if self.end_trigger_signal is True or (self.track_count_limit >0  and self.track_count == self.track_count_limit):
                    self.end_trigger_signal=False
                    # repeat so test start trigger
                    if self.show_params['repeat'] == 'repeat':
                        self.stop_timers()
                        # print 'END TRIGGER restart'
                        self.wait_for_trigger()
                    else:
                        # single run so exit show
                        if self.level != 0:
                            self.kickback_for_next_track=False
                            self.subshow_kickback_signal=False
                            # print 'single run exit subshow'
                            self.end('normal',"End of single run - Return from Sub Show")
                        else:
                            # end of single run and at top - exit the show
                            self.stop_timers()
                            # print 'ENDING'
                            self.ending_reason='user-stop'
                            Show.base_close_or_unload(self)                   

                # user wants to play child
                elif self.play_child_signal is True:
                    self.play_child_signal=False
                    index = self.medialist.index_of_track(self.child_track_ref)
                    if index >=0:
                        # don't use select the track as need to preserve mediashow sequence for returning from child
                        child_track=self.medialist.track(index)
                        Show.write_stats(self,'play child',self.show_params,child_track)
                        self.display_eggtimer()
                        self.enable_hint=False
                        self.start_load_show_loop(child_track)
                    else:
                        self.mon.err(self,"Child not found in medialist: "+ self.child_track_ref)
                        self.ending_reason='error'
                        Show.base_close_or_unload(self)



                # skip to next track on user input or after subshow
                elif self.next_track_signal is True:
                    # print 'skip forward test' ,self.subshow_kickback_signal
                    if self.next_track_signal is True or self.subshow_kickback_signal is False:
                        self.next_track_signal=False
                        self.kickback_for_next_track=False
                        if self.medialist.at_end() is True:
                            # medialist_at_end can give false positive for shuffle
                            if  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'repeat':
                                self.wait_for_trigger()
                            elif  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run':
                                if self.level != 0:
                                    self.kickback_for_next_track=False
                                    self.subshow_kickback_signal=False
                                    # print 'end subshow skip forward test, self. direction is ' ,self.kickback_for_next_track
                                    self.end('normal',"Return from Sub Show")
                                else:
                                    # end of single run and at top - exit the show
                                    self.stop_timers()
                                    self.ending_reason='user-stop'
                                    Show.base_close_or_unload(self)
                            else:
                                # shuffling  - just do next track
                                self.kickback_for_next_track=False
                                self.medialist.next(self.show_params['sequence'])
                                self.start_load_show_loop(self.medialist.selected_track())      
                        else:
                            # not at end just do next track
                            self.medialist.next(self.show_params['sequence'])
                            self.start_load_show_loop(self.medialist.selected_track())


                # skip to previous track on user input or after subshow
                elif self.previous_track_signal is True or self.subshow_kickback_signal is True:
                    # print 'skip backward test, subshow kickback is' ,self.subshow_kickback_signal
                    self.subshow_kickback_signal=False
                    self.previous_track_signal=False
                    self.kickback_for_next_track=True
                    # medialist_at_start can give false positive for shuffle
                    if self.medialist.at_start() is True:
                        # print 'AT START'
                        if  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'repeat':
                            self.kickback_for_next_track=True
                            self.wait_for_trigger()
                        elif  self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'single-run':
                            if self.level != 0:
                                self.kickback_for_next_track=True
                                self.subshow_kickback_signal=True
                                # print 'end subshow skip forward test, self. direction is ' ,self.kickback_for_next_track
                                self.end('normal',"Return from Sub Show")
                            else:
                                # end of single run and at top - exit the show
                                self.stop_timers()
                                self.ending_reason='user-stop'
                                Show.base_close_or_unload(self)
                        else:
                            # shuffling  - just do previous track
                            self.kickback_for_next_track=True
                            self.medialist.previous(self.show_params['sequence'])
                            self.start_load_show_loop(self.medialist.selected_track())               
                    else:
                        # not at end just do next track
                        self.medialist.previous(self.show_params['sequence'])              
                        self.start_load_show_loop(self.medialist.selected_track())


                    

                # AT END OF MEDIALIST
                elif self.medialist.at_end() is True:
                    # print 'MEDIALIST AT END'

                    # interval>0 and list finished so wait for the interval timer
                    if self.show_params['sequence'] == "ordered"  and self.interval > 0 and self.interval_timer_signal==False:
                        self.waiting_for_interval=True
                        # print 'WAITING FOR INTERVAL'
                        Show.base_shuffle(self)
                        Show.base_track_ready_callback(self,False)
                        self.poll_for_interval_timer=self.canvas.after(200,self.what_next_after_showing) 

                    # interval=0   
                    #elif self.show_params['sequence'] == "ordered" and self.show_params['repeat'] == 'repeat' and self.show_params['trigger-end-type']== 'interval' and int(self.show_params['trigger-end-param']) == 0:
                        #self.medialist.next(self.show_params['sequence'])
                        # self.start_load_show_loop(self.medialist.selected_track())

                    # shuffling so there is no end condition, get out of end test
                    elif self.show_params['sequence'] == "shuffle":
                        self.medialist.next(self.show_params['sequence'])
                        self.start_load_show_loop(self.medialist.selected_track())
                        
                    # nothing special to do at end of list, just repeat or exit
                    elif self.show_params['sequence'] == "ordered":
                        if self.show_params['repeat'] == 'repeat':
                            # print 'repeating at end of list'
                            self.wait_for_trigger()
                        else:
                            # single run
                            # if not at top return to parent
                            if self.level !=0:
                                self.end('normal',"End of Single Run")
                            else:
                                # at top so close the show
                                # print 'closing show'
                                self.stop_timers()
                                self.ending_reason='user-stop'
                                Show.base_close_or_unload(self)
                            
                    else:
                        self.mon.err(self,"Unhandled playing event at end of list: "+self.show_params['sequence'] +' with ' + self.show_params['repeat']+" of "+ self.show_params['trigger-end-param'])
                        self.end('error',"Unhandled playing event at end of list: "+self.show_params['sequence'] +' with ' + self.show_params['repeat']+" of "+ self.show_params['trigger-end-param'])
                    
                elif self.medialist.at_end() is False:
                    # nothing special just do the next track
                    # print 'nothing special'
                    self.medialist.next(self.show_params['sequence'])
                    self.start_load_show_loop(self.medialist.selected_track())
                          
                else:
                    # unhandled state
                    self.mon.err(self,"Unhandled playing event: "+self.show_params['sequence'] +' with ' + self.show_params['repeat']+" of "+ self.show_params['trigger-end-param'])
                    self.end('error',"Unhandled playing event: "+self.show_params['sequence'] +' with ' + self.show_params['repeat']+" of "+ self.show_params['trigger-end-param'])

   
   
# *********************
# Interface with other shows/players to reduce black gaps
# *********************

    # called just before a track is shown to remove the  previous track from the screen
    # and if necessary close it
    def track_ready_callback(self,enable_show_background):
        self.delete_eggtimer()

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

            # print 'controls',reason,self.show_params['controls'],self.controls_list
            #merge controls from the track
            controls_text=self.current_player.get_links()
            reason,message,track_controls=self.controlsmanager.parse_controls(controls_text)
            if reason == 'error':
                self.mon.err(self,message + " in track: "+ self.current_player.track_params['track-ref'])
                self.error_signal=True
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





