#2/1/2016 add write_stats  function

import os
from Tkinter import NW
from PIL import Image
from PIL import ImageTk

from pp_showmanager import ShowManager
from pp_timeofday import TimeOfDay
from pp_imageplayer import ImagePlayer
from pp_videoplayer import VideoPlayer
from pp_audioplayer import AudioPlayer
from pp_browserplayer import BrowserPlayer
from pp_messageplayer import MessagePlayer
from pp_menuplayer import MenuPlayer
from pp_utils import Monitor,calculate_text_position

class Show(object):


    # ******************************
    # init a show
    # ******************************

    def base__init__(self,
                     show_id,
                     show_params,
                     root,
                     canvas,
                     showlist,
                     pp_dir,
                     pp_home,
                     pp_profile,
                     command_callback):

        # instantiate arguments
        self.show_id=show_id
        self.show_params=show_params
        self.root=root
        self.show_canvas=canvas
        self.canvas=canvas['canvas-obj']
        self.show_canvas_x1 = canvas['show-canvas-x1']
        self.show_canvas_y1 = canvas['show-canvas-y1']
        self.show_canvas_x2 = canvas['show-canvas-x2']
        self.show_canvas_y2 = canvas['show-canvas-y2']
        self.show_canvas_width = canvas['show-canvas-width']
        self.show_canvas_height= canvas['show-canvas-height']
        self.show_canvas_centre_x= canvas['show-canvas-centre-x']
        self.show_canvas_centre_y= canvas['show-canvas-centre-y']
        self.showlist=showlist
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile
        self.command_callback=command_callback

        # init things that will then be reinitialised by derived classes
        self.medialist=None

        # set up logging
        self.leak=False
        self.mon=Monitor()
        self.mon.set_log_level(16)


        # create and instance of TimeOfDay scheduler so we can add events
        self.tod=TimeOfDay()
        
        # create an  instance of showmanager so we can init child/subshows
        self.show_manager=ShowManager(self.show_id,self.showlist,self.show_params,self.root,self.show_canvas,self.pp_dir,self.pp_profile,self.pp_home)


        # init variables
        self.current_player=None
        self.previous_player=None
        self.shower=None
        self.previous_shower=None
        self.user_stop_signal= False
        self.exit_signal=False
        self.terminate_signal=False
        self.show_timeout_signal=False
        self.egg_timer=None
        self.admin_message=None
        self.ending_reason=''
        self.background_obj=None
        self.background_file=''
        self.level=0
        self.subshow_kickback_signal=False
        self.kickback_for_next_track=False
        
        # get background image from profile.
        # print 'background', self.show_params['background-image']
        if self.show_params['background-image'] != '':
            self.background_file= self.show_params['background-image']

    def base_play(self,end_callback,show_ready_callback, parent_kickback_signal,level,controls_list):

        """ starts the common parts of the show
              end_callback - function to be called when the show exits- callback gets last player of subshow
              show_ready_callback - callback at start to get previous_player
              top is True when the show is top level (run from [start] or by show command from another show)
              direction_command - 'forward' or 'backward' direction to play a subshow
        """
        # instantiate the arguments
        if self.leak is True:
            print 'play show - ',self.show_params['title']
        self.end_callback=end_callback
        self.show_ready_callback=show_ready_callback
        self.parent_kickback_signal=parent_kickback_signal
        self.level=level
        # not needed as controls list is not passed down to subshows.
        # self.controls_list=controls_list
        self.mon.trace(self,self.show_params['show-ref'] + ' at level ' + str(self.level))
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Starting show")
        # check  data files are available.
        if self.show_params['medialist'] == '':
            self.mon.err(self,"Blank Medialist in: "+ self.show_params['title'])
            self.end('error',"Blank Medialist in: "+ self.show_params['title'])
        self.medialst_file = self.pp_profile + "/" + self.show_params['medialist']
        if not os.path.exists(self.medialst_file):
            self.mon.err(self,"Medialist file not found: "+ self.medialst_file)
            self.end('error',"Medialist file not found: "+ self.medialst_file)

        # read the medialist for the show
        if self.medialist.open_list(self.medialst_file,self.showlist.profile_version()) is False:
            self.mon.err(self,"Version of medialist different to Pi Presents")
            self.end('error',"Version of medialist different to Pi Presents")
        if self.leak is True:
            print 'IN ',self.show_params['title']
        if self.show_ready_callback is not None:
            # get the previous player from calling show its stored in current because its going to be shuffled before use
            
            self.previous_shower, self.current_player=self.show_ready_callback()
            if self.leak is True:
                print 'from show_ready_callback, previous shower,current player',self.previous_shower.show_params['title'],self.current_player.track_params['title']
            self.mon.trace(self,' - previous shower and player is ' + self.mon.pretty_inst(self.previous_shower)+ ' ' + self.mon.pretty_inst(self.current_player))


        # Control other shows at beginning
        self.show_control(self.show_params['show-control-begin'])

        #load the show background
        reason,message=Show.base_load_show_background(self)
        if reason=='error':
            self.mon.err(self,message)
            self.end('error',message)

    # dummy, must be overidden by derived class
    def subshow_ready_callback(self):
        self.mon.err(self,"subshow_ready_callback not overidden")
        # set what to do when closed or unloaded
        self.ending_reason='killed'
        Show.base_close_or_unload(self)


    def base_subshow_ready_callback(self):
        # callback from begining of a subshow, provide previous player to called show
        # used by show_ready_callback of called show
        # in the case of a menushow last track is always the menu
        if self.leak is True:
            print 'subshow ready callback returns',self.show_params['title'],self.previous_player.track_params['title']
        self.mon.trace(self,' -  sends ' + self.mon.pretty_inst(self.previous_player))
        return self,self.previous_player


    def base_shuffle(self):
        if self.leak is True:
            if self.current_player != None:
                print 'shuffle current player, previous is',self.current_player.track_params['title']
            else:   
                print 'shuffle None player'
        self.previous_player=self.current_player
        self.current_player = None
        if self.leak is True:
            print 'current_player is None'
        self.mon.trace(self,' - LOOP STARTS WITH current is: ' + self.mon.pretty_inst(self.current_player))
        self.mon.trace(self,'       -  previous is: ' + self.mon.pretty_inst(self.previous_player))



    def base_load_track_or_show(self,selected_track,loaded_callback,end_shower_callback,enable_menu):
        track_type=selected_track['type']
        if track_type == "show":
            # get the show from the showlist
            index = self.showlist.index_of_show(selected_track['sub-show'])
            if index <0:
                self.mon.err(self,"Show not found in showlist: "+ selected_track['sub-show'])
                self.end('error','show not in showlist: '+ selected_track['sub-show'])
            else:
                self.showlist.select(index)
                selected_show=self.showlist.selected_show()
                if self.leak is True:
                    print 'IN ',self.show_params['title']
                self.shower=self.show_manager.init_subshow(self.show_id,selected_show,self.show_canvas)
                if self.leak is True:
                    print '\ninit new subshow',self.shower.show_params['show-ref']
                self.mon.trace(self,' - show is: ' + self.mon.pretty_inst(self.shower) + ' ' + selected_show['show-ref'])
                if self.shower is None:
                    self.mon.err(self,"Unknown Show Type: "+ selected_show['type'])
                    self.terminate_signal=True
                    self.what_next_after_showing()
                else:
                    # empty controls list as not used, pleases landscape
                    # print 'send direction to subshow from show',self.kickback_for_next_track
                    # Show.base_withdraw_show_background(self)
                    self.shower.play(end_shower_callback,self.subshow_ready_callback,self.kickback_for_next_track,self.level+1,[])
        else:
            # dispatch track by type
            self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Track type is: "+ track_type)
            self.current_player=self.base_init_selected_player(selected_track)
            if self.leak is True:
                print '\ninit current player ',self.current_player.track_params['title']
            #menu has no track file
            if selected_track['type']=='menu':
                track_file=''
                
            # messageplayer passes the text not a file name
            elif selected_track['type'] == 'message':
                track_file=selected_track['text']
            else:
                track_file=self.base_complete_path(selected_track['location'])
                
            self.mon.trace(self,' - track is: ' + track_file)
            self.mon.trace(self,' - current_player is: '+ self.mon.pretty_inst(self.current_player))
            self.current_player.load(track_file,
                                     loaded_callback,
                                     enable_menu=enable_menu)

    # DUMMY, must be overidden by derived class
    def what_next_after_showing(self):
        self.mon.err(self,"what_next_after showing not overidden")
        # set what to do when closed or unloaded
        self.ending_reason='killed'
        Show.base_close_or_unload(self)


    def base_init_selected_player(self,selected_track):
        # dispatch track by type
        track_type=selected_track['type']
        self.mon.log(self,"Track type is: "+ track_type)
                                      
        if track_type == "image":
            return ImagePlayer(self.show_id,self.showlist,self.root,self.show_canvas,
                               self.show_params,selected_track,self.pp_dir,self.pp_home,
                               self.pp_profile,self.end,self.command_callback)
    
        elif track_type == "video":
            return VideoPlayer(self.show_id,self.showlist,self.root,self.show_canvas,
                               self.show_params,selected_track,self.pp_dir,self.pp_home,
                               self.pp_profile,self.end,self.command_callback)

        elif track_type == "audio":
            return AudioPlayer(self.show_id,self.showlist,self.root,self.show_canvas,
                               self.show_params,selected_track,self.pp_dir,self.pp_home,
                               self.pp_profile,self.end,self.command_callback)

        elif track_type == "web" and self.show_params['type'] not in ('artmediashow','artliveshow'):
            return BrowserPlayer(self.show_id,self.showlist,self.root,self.show_canvas,
                                 self.show_params,selected_track,self.pp_dir,self.pp_home,
                                 self.pp_profile,self.end,self.command_callback)
  
        elif track_type == "message":
            return MessagePlayer(self.show_id,self.showlist,self.root,self.show_canvas,
                                 self.show_params,selected_track,self.pp_dir,self.pp_home,
                                 self.pp_profile,self.end,self.command_callback)

        elif track_type == "menu":
            return MenuPlayer(self.show_id,self.showlist,self.root,self.show_canvas,
                              self.show_params,selected_track,self.pp_dir,self.pp_home,
                              self.pp_profile,self.end,self.command_callback)
                                   
        else:
            return None


    # DUMMY, must be overidden by derived class
    def track_ready_callback(self,track_background):
        self.mon.err(self,"track_ready_callback not overidden")
        # set what to do when closed or unloaded
        self.ending_reason='killed'
        Show.base_close_or_unload(self)


    # called just before a track is shown to remove the  previous track from the screen
    # and if necessary close it        
    def base_track_ready_callback(self,enable_show_background):
        self.mon.trace(self,'')
        if self.leak is True:
            print 'IN ',self.show_params['title']
        # show the show background done for every track but quick operation
        if enable_show_background is True:
            self.base_show_show_background()
        else:
            self.base_withdraw_show_background()
        # !!!!!!!!! withdraw the background from the parent show
        if self.previous_shower != None:
            self.previous_shower.base_withdraw_show_background()
        # close the player from the previous track
        if self.previous_player is not  None:
            self.mon.trace(self,' - hiding previous: ' + self.mon.pretty_inst(self.previous_player))
            self.previous_player.hide()
            # print 'Not None  - previous state is',self.previous_player.get_play_state()
            if self.previous_player.get_play_state() == 'showing':
                # print 'showing so closing previous'
                # showing or frozen
                self.mon.trace(self,' - closing previous: ' + self.mon.pretty_inst(self.previous_player))
                self.previous_player.close(self._base_closed_callback_previous)
            else:
                self.mon.trace(self,' - previous is none\n')
                if self.leak is True:
                    print 'previous player = None - ', self.previous_player.track_params['title']
                self.previous_player=None
        self.canvas.update_idletasks( )


    def _base_closed_callback_previous(self,status,message):
        if self.leak is True:
            print 'IN ',self.show_params['title']
        self.mon.trace(self,' -  previous is None  - was: ' + self.mon.pretty_inst(self.previous_player))
        if self.leak is True:
            print 'previous player = None - base_closed_callback_previous', self.previous_player.track_params['title']
        self.previous_player=None
        if self.previous_shower!=None:
            if self.leak is True:
                print 'previous shower = None - base_closed_callback_previous', self.previous_shower.show_params['title']
            self.previous_shower=None
        if self.shower != None:
            if self.leak is True:
                print 'shower = None',self.shower.show_params['title']
            self.shower=None

    # used by end_shower to get the last track of the subshow
    def base_end_shower(self):
        self.mon.trace(self,' -  returned back to level: ' +str(self.level))
        # get the previous subshow and last track it played
        self.previous_shower,self.current_player=self.shower.base_subshow_ended_callback()
        if self.leak is True:
            print 'IN ',self.show_params['title']
            print 'got from self.shower.base_subshow_ended_callback',self.previous_shower.show_params['title'],
            if self.current_player !=None:
                print self.current_player.track_params['title']
            else:
                print ' None'
        if self.previous_shower!= None:
            self.subshow_kickback_signal=self.shower.subshow_kickback_signal
            # print 'get subshow kickback from subshow',self.subshow_kickback_signal
            self.previous_shower.base_withdraw_show_background()
            self.base_show_show_background()
        self.mon.trace(self,'- get previous_player from subshow: ' + self.mon.pretty_inst(self.current_player))
        if self.shower != None:
            if self.leak is True:
                print 'shower = None',self.shower.show_params['title']
            self.shower=None


    # close or unload the current player when ending the show
    def base_close_or_unload(self):
        if self.leak is True:
            print 'IN ',self.show_params['title']
        self.mon.trace(self,self.mon.pretty_inst(self.current_player))
        # need to test for None because player may be made None by subshow lower down the stack for terminate
        if self.current_player is not None:
            self.mon.trace(self,self.current_player.get_play_state())
            if self.current_player.get_play_state() in ('loaded','showing','show-failed'):
                if self.current_player.get_play_state() == 'loaded':
                    self.mon.trace(self,' - unloading current from: '+self.ending_reason)
                    self.current_player.unload()
                else:
                    self.mon.trace(self,' - closing current from: '  + self.ending_reason)
                    self.current_player.close(None)
            self._wait_for_end()
        else:
            # current_player is None because closed further down show stack
            self.mon.trace(self,' - show ended with current_player=None because: ' + self.ending_reason)

            # if exiting pipresents then need to close previous show else get memory leak
            # if not exiting pipresents the keep previous so it can be closed when showing the next track
            # print 'CURRENT PLAYER IS NONE' ,self.ending_reason
            if self.ending_reason == 'killed':
                self.base_close_previous()

            elif self.ending_reason == 'error':
                self.base_close_previous()

            elif self.ending_reason == 'exit':
                self.end('normal',"show quit by exit command")

            elif self.ending_reason == 'user-stop':
                self.end('normal',"show quit by stop operation")
                 
            else:
                self.mon.fatal(self,"Unhandled ending_reason: " + self.ending_reason)
                self.end('error',"Unhandled ending_reason: " + self.ending_reason)          


    def _base_closed_callback_current(self,status,message):
        self.mon.trace(self,' current is None  - was: ' + self.mon.pretty_inst(self.current_player))


    # wait for unloading or closing to complete then end
    def _wait_for_end(self):
        if self.leak is True:
            print 'IN ',self.show_params['title']
        self.mon.trace(self, self.mon.pretty_inst(self.current_player))
        if self.current_player is not None:
            self.mon.trace(self,' - play state is ' +self.current_player.get_play_state())
            if self.current_player.play_state not in ('unloaded','closed','load-failed'):  ####
                self.canvas.after(50,self._wait_for_end)
            else:
                self.mon.trace(self,' - current closed '+ self.mon.pretty_inst(self.current_player) + ' ' + self.ending_reason)

                 #why is some of thsi different to close and unload????????????? perhaps because current_player isn't none, just closed
                if self.ending_reason == 'killed':
                    self.current_player.hide()
                    self.current_player=None
                    self.base_close_previous()

                elif self.ending_reason == 'error':
                    self.current_player.hide()
                    self.current_player=None
                    self.base_close_previous()

                elif self.ending_reason == 'exit':
                    self.current_player.hide()
                    self.current_player=None
                    self.base_close_previous()

                elif self.ending_reason == 'change-medialist':
                    self.current_player.hide()
                    self.current_player=None
                    # self.base_close_previous()
                    # go to start of list via wait for trigger.
                    self.wait_for_trigger()
                    
                elif self.ending_reason == 'show-timeout':
                    self.current_player.hide()
                    self.current_player=None
                    self.end('normal',"show timeout")
                    
                elif self.ending_reason == 'user-stop':
                    if self.level !=0:
                        self.end('normal',"show quit by stop operation")
                    else:
                        self.current_player.hide()
                        if self.leak is True:
                            print 'current player == none wait for end',self.current_player.track_params['title']
                        self.current_player=None
                        self.base_close_previous()
                        
                    
                else:
                    self.mon.fatal(self,"Unhandled ending_reason: " + self.ending_reason)
                    self.end('error',"Unhandled ending_reason: "+ self.ending_reason)
        else:
            self.mon.trace(self,' - current is None ' +  self.mon.pretty_inst(self.current_player) + ' ' + self.ending_reason)


# ***************************
# end of show 
# ***************************

    # dummy, normally overidden by derived class
    def end(self,reason,message):
        self.mon.err(self,"end not overidden")
        self.base_end('error',message)

    def base_end(self,reason,message):
        self.base_withdraw_show_background()
        self.base_delete_show_background()

        # Control concurrent shows at end
        self.show_control(self.show_params['show-control-end'])
        
        self.mon.trace(self,' at level ' + str(self.level) + '\n - Current is ' + self.mon.pretty_inst(self.current_player) + '\n - Previous is ' + self.mon.pretty_inst(self.previous_player) + '\n with reason' + reason + '\n\n')
        self.mon.log(self,self.show_params['show-ref']+ ' Show Id: '+ str(self.show_id)+ ": Ending Show")
        self.end_callback(self.show_id,reason,message)
        self=None


    def base_subshow_ended_callback(self):
        # called by end_shower of a parent show  to get the last track of the subshow and the subshow
        self.mon.trace(self,' -  returns ' + self.mon.pretty_inst(self.current_player))
        if self.leak is True:
            print 'IN ',self.show_params['title']
            print 'subshow ended callback returns self show,current player',self.show_params['title'],
        if self.current_player!= None:
            if self.leak is True:
                print self.current_player.track_params['title']
            cp=self.current_player
            if self.leak is True:
                print 'current player = None',self.current_player.track_params['title']
            self.current_player=None
        else:
            cp=None
            if self.leak is True:
                print 'None'
        return self,cp
##        print 'subshow ended callback returns self show,current player',self.show_params['title'],
##        if self.current_player!=None:print self.current_player.track_params['title']
##        return self,self.current_player
# ********************************
# Respond to external events
# ********************************


    def base_close_previous(self):
        self.mon.trace(self,'')
        # close the player from the previous track
        if self.previous_player is not  None:
            self.mon.trace(self,' - previous not None ' + self.mon.pretty_inst(self.previous_player))
            if self.previous_player.get_play_state() == 'showing':
                # showing or frozen
                self.mon.trace(self,' - closing previous ' + self.mon.pretty_inst(self.previous_player))
                self.previous_player.close(self._base_close_previous_callback)
            else:
                self.mon.trace(self,'previous is not showing')
                self.previous_player.hide()
                if self.leak is True:
                    print 'previous player = None - ', self.previous_player.track_params['title']
                self.previous_player=None
                self.end(self.ending_reason,'')
        else:
            self.mon.trace(self,' - previous is None')
            self.end(self.ending_reason,'')
            
                

    def _base_close_previous_callback(self,status,message):
        self.mon.trace(self, ' -  previous is None  - was ' + self.mon.pretty_inst(self.previous_player))
        self.previous_player.hide()
        if self.leak is True:
            print 'previous player = None - ', self.previous_player.track_params['title']
        self.previous_player=None
        self.end(self.ending_reason,'')


    # exit received from external source
    def base_exit(self):
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Exit received")
        self.mon.trace(self,'')
        # set signal to exit the show when all  sub-shows and players have ended
        self.exit_signal=True
        # then stop subshow or tracks.
        if self.shower is not None:
            self.shower.exit()
        elif self.current_player is not None:
            self.current_player.input_pressed('stop')
        else:
            self.end('normal','exit by ShowManager')

    # show timeout callback received
    def base_show_timeout_stop(self):
        self.mon.trace(self,'')
        # set signal to exit the show when all  sub-shows and players have ended
        self.show_timeout_signal=True
        # then stop and shows or tracks.
        if self.shower is not None:
            self.shower.show_timeout_stop()
        elif self.current_player is not None:
            self.current_player.input_pressed('stop')
        else:
            self.end('normal','stopped by Show Timeout')


    # dummy, normally overidden by derived class
    def terminate(self):
        self.mon.err(self,"terminate not overidden")
        self.base_end('error',"terminate not overidden")

    # terminate Pi Presents
    def base_terminate(self):
        if self.leak is True:
            print '\nterminate received by ',self.show_params['title']
            if self.shower!= None:
                print self.shower.show_params['title']
            else:
                print 'self.shower is none'
            if self.current_player!= None:
                print self.current_player.track_params['title']
            else:
                print 'self.current player is none'        

        self.mon.trace(self,'')
        # set signal to stop the show when all  sub-shows and players have ended
        self.terminate_signal=True
        if self.shower is not None:
            self.shower.terminate()
        elif self.current_player is not None:
            self.ending_reason='killed'
            Show.base_close_or_unload(self)
        else:
            self.end('killed',' terminated with no shower or player to terminate')


  # respond to input events
    def base_handle_input_event(self,symbol):
        self.mon.log(self, self.show_params['show-ref']+ ' Show Id: '+ str(self.show_id)+": received input event: " + symbol)

        if self.shower is not None:
            self.shower.handle_input_event(symbol)
        else:
            self.handle_input_event_this_show(symbol)

    #dummy must be overridden in derived class
    def handle_input_event_this_show(self,symbol):
        self.mon.err(self,"input_pressed_this_show not overidden")
        self.ending_reason='killed'
        Show.base_close_or_unload(self)
            
    def base_load_show_background(self):
        # load show background image
        if self.background_file != '':
            background_img_file = self.base_complete_path(self.background_file)
            if not os.path.exists(background_img_file):
                return 'error',"Show background file not found "+ background_img_file
            else:
                try:
                    pil_background_img=Image.open(background_img_file)
                except:
                    pil_background_img=None
                    self.background=None
                    self.background_obj=None
                    return 'error','Show background file, not a recognised image format '+ background_img_file  
                # print 'pil_background_img ',pil_background_img
                image_width,image_height=pil_background_img.size
                window_width=self.show_canvas_width
                window_height=self.show_canvas_height
                if image_width != window_width or image_height != window_height:
                    pil_background_img=pil_background_img.resize((window_width, window_height))
                self.background = ImageTk.PhotoImage(pil_background_img)
                del pil_background_img
                # print 'self.background ',self.background
                self.background_obj = self.canvas.create_image(self.show_canvas_x1,
                                                               self.show_canvas_y1,
                                                               image=self.background,
                                                               anchor=NW)
                self.canvas.itemconfig(self.background_obj,state='hidden')
                self.canvas.update_idletasks( )
                # print '\nloaded background_obj: ',self.background_obj
                return 'normal','show background loaded'
        else:
            return 'normal','no backgound to load'
              
    def base_show_show_background(self):
        if self.background_obj is not None:
            # print 'show show background'
            self.canvas.itemconfig(self.background_obj,state='normal')
            # self.canvas.update_idletasks( )    

    def base_withdraw_show_background(self):
        self.mon.trace(self,'')
        if self.background_obj is not None:
            # print 'withdraw background obj', self.background_obj
            self.canvas.itemconfig(self.background_obj,state='hidden')
            # self.canvas.update_idletasks( )


    def base_delete_show_background(self):
        if self.background_obj is not None:
            # print 'delete background obj'
            self.canvas.delete(self.background_obj)
            self.background=None
            # self.canvas.update_idletasks( )


# ******************************
# write statiscics
# *********************************
    def write_stats(self,command,show_params,next_track):
            # action, this ref, this name, type, ref, name, location
            if next_track['type']=='show':
                # get the show from the showlist
                index = self.showlist.index_of_show(next_track['sub-show'])
                if index <0:
                    self.mon.err(self,"Show not found in showlist: "+ next_track['sub-show'])
                    self.end('error','show not in showlist: '+ next_track['sub-show'])
                else:
                    target=self.showlist.show(index)
                    ref=target['show-ref']
                    title=target['title']
                    track_type=target['type']
            else:
                # its a track
                ref= next_track['track-ref']
                title=next_track['title']
                track_type=next_track['type']
            if next_track['type'] in ('show','message'):
                loc = ''
            else:
                loc = next_track['location']                 
            self.mon.stats(show_params['type'],show_params['show-ref'],show_params['title'],command,
                            track_type,ref,title,loc)
            


 # Control shows so pass the show control commands back to PiPresents via the command callback
    def show_control(self,show_control_text):
        lines = show_control_text.split('\n')
        for line in lines:
            if line.strip() != "":
                # print 'show control command: ',line
                self.show_control_command(line)

    def show_control_command(self,line):
        fields= line.split()
        show_command=fields[0]
        if len(fields)>1:
            show_ref=fields[1]
        else:
            show_ref=''
        self.command_callback(line,source='show',show=self.show_params['show-ref'])


# ******************************
# lookup controls 
# *********************************
    def base_lookup_control(self,symbol,controls_list):
        for control in controls_list:
            if symbol == control[0]:
                return control[1]
        # not found so must be a trigger
        return ''

# ******************************
# Eggtimer
# *********************************
        
    def display_eggtimer(self):
        text=self.show_params['eggtimer-text']
        if text != '':

            x,y,anchor,justify=calculate_text_position(self.show_params['eggtimer-x'],self.show_params['eggtimer-y'],
                                     self.show_canvas_x1,self.show_canvas_y1,
                                     self.show_canvas_centre_x,self.show_canvas_centre_y,
                                     self.show_canvas_x2,self.show_canvas_y2,self.show_params['eggtimer-justify'])
            
            self.egg_timer=self.canvas.create_text(x,y,
                                                   text= text,
                                                   justify=justify,
                                                   fill=self.show_params['eggtimer-colour'],
                                                   font=self.show_params['eggtimer-font'],
                                                   anchor=anchor)
            
            self.canvas.update_idletasks( )


    def delete_eggtimer(self):
        if self.egg_timer is not None:
            self.canvas.delete(self.egg_timer)
            self.egg_timer=None
            self.canvas.update_idletasks( )



# ******************************
# Display Admin Messages
# *********************************

    def display_admin_message(self,text):

        x,y,anchor,justify=calculate_text_position(self.show_params['admin-x'],self.show_params['admin-y'],
                                     self.show_canvas_x1,self.show_canvas_y1,
                                     self.show_canvas_centre_x,self.show_canvas_centre_y,
                                     self.show_canvas_x2,self.show_canvas_y2,self.show_params['admin-justify'])

        self.admin_message=self.canvas.create_text(x,y,
                                                   justify=justify,
                                                   text= text,
                                                   fill=self.show_params['admin-colour'],
                                                   font=self.show_params['admin-font'],
                                                   anchor=anchor)
            
        self.canvas.update_idletasks( )


    def delete_admin_message(self):
        if self.admin_message is not None:
            self.canvas.delete(self.admin_message)
            self.canvas.update_idletasks( )


# ******************************
# utilities
# ******************************        

    def base_complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file != '' and track_file[0]=="+":
            track_file=self.pp_home+track_file[1:]
        elif track_file != '' and track_file[0] == "@":
            track_file=self.pp_profile+track_file[1:]
        self.mon.log(self,"Track to load is: "+ track_file)
        return track_file     
  

    def calculate_duration(self,line):
        fields=line.split(':')
        if len(fields)==1:
            secs=fields[0]
            minutes='0'
            hours='0'
        if len(fields)==2:
            secs=fields[1]
            minutes=fields[0]
            hours='0'
        if len(fields)==3:
            secs=fields[2]
            minutes=fields[1]
            hours=fields[0]
        if not secs.isdigit() or not minutes.isdigit() or not hours.isdigit():
            return 'error','bad time: '+ line,0
        else:
            return 'normal','',3600*long(hours)+60*long(minutes)+long(secs)



