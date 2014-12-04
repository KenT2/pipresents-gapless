from Tkinter import NW
from pp_utils import StopWatch
from pp_player import Player

class MessagePlayer(Player):

    """ Displays a message on a canvas for a period of time. Message display can be  interrupted
          Differs from other players in that text is passed as parameter rather than file containing the text

        __init_ just makes sure that all the things the player needs are available
        load and unload loads and unloads the track
        show shows the track,close closes the track after pause at end
        input-pressed receives user input while the track is playing.
    """
 
    def __init__(self,
                 show_id,
                 showlist,
                 root,
                 canvas,
                 show_params,
                 track_params ,
                 pp_dir,
                 pp_home,
                 pp_profile,
                 end_callback):

        # initialise items common to all players   
        Player.__init__( self,
                         show_id,
                         showlist,
                         root,
                         canvas,
                         show_params,
                         track_params ,
                         pp_dir,
                         pp_home,
                         pp_profile,
                         end_callback)                    

        # comment this out to turn the trace off          
        # self.trace=True

        # control debugging log
        self.mon.on()
        
        # stopwatch for timing functions
        StopWatch.global_enable=False
        self.sw=StopWatch()
        self.sw.off()

        if self.trace: print '    Messageplayer/init ',self
        # and initilise things for this player
        
        # get duration from profile
        if self.track_params['duration'] != "":
            self.duration= int(self.track_params['duration'])
        else:
            self.duration= int(self.show_params['duration'])       
        
        # initialise the state machine
        self.play_state='initialised'    
            
            
    # LOAD - loads the images and text
    def load(self,text,loaded_callback,enable_menu):  
        # instantiate arguments
        self.track=text
        self.loaded_callback=loaded_callback   # callback when loaded
        if self.trace: print '    Messageplayer/load ',self

        # load the plugin, this may modify self.ttack and enable the plugin drawign to canvas
        if self.track_params['plugin'] != '':
            status,message=self.load_plugin()
            if status == 'error':
                self.mon.err(self,message)
                self.play_state='load-failed'
                if self.loaded_callback is not  None:
                    self.loaded_callback('error',message)


        # load the images and text including message text
        status,message=self.load_x_content(enable_menu)
        if status == 'error':
            self.mon.err(self,message)
            self.play_state='load-failed'
            if self.loaded_callback is not  None:
                self.loaded_callback('error',message)
        else:
            self.play_state='loaded'
            if self.loaded_callback is not None:
                self.loaded_callback('loaded','image track loaded')

            
    # UNLOAD - abort a load when omplayer is loading or loaded
    def unload(self):
        if self.trace: print '    Messageplayer/unload ',self
        # nothing to do for Messageplayer
        self.mon.log(self,">unload received from show Id: "+ str(self.show_id))
        self.play_state='unloaded'
     
            

     # SHOW - show a track from its loaded state 
    def show(self,ready_callback,finished_callback,closed_callback):
                         
        # instantiate arguments
        self.ready_callback=ready_callback         # callback when ready to show an image - 
        self.finished_callback=finished_callback         # callback when finished showing 
        self.closed_callback=closed_callback            # callback when closed - not used by Messageplayer

        if self.trace: print '    Messageplayer/show ',self
        
        # init state and signals  
        self.tick = 100 # tick time for image display (milliseconds)
        self.dwell = 10*self.duration
        self.dwell_counter=0
        self.quit_signal=False
        self.show_x_content()
        if self.ready_callback is not None:
            self.ready_callback()

        # do common bits
        Player.pre_show(self)
        
        # start show state machine
        self.start_dwell()

    # CLOSE - nothing ot do in messageplayer - x content is removed by ready callback
    def close(self,closed_callback):
        if self.trace: print '    Messageplayer/close ',self
        self.closed_callback=closed_callback
        self.mon.log(self,">close received from show Id: "+ str(self.show_id))
        self.play_state='closed'
        if self.closed_callback is not None:
            self.closed_callback('normal','Messageplayer closed')


    def input_pressed(self,symbol):
        if symbol ==  'stop':
            self.stop()


    def stop(self):
        self.quit_signal=True
        


        
# ******************************************
# Sequencing
# ********************************************

    def start_dwell(self):
        self.play_state='showing'
        self.tick_timer=self.canvas.after(self.tick, self.do_dwell)

        
    def do_dwell(self):
        if self.quit_signal  is   True:
            self.mon.log(self,"quit received")
            if self.finished_callback is not None:
                self.finished_callback('pause_at_end','user quit or duration exceeded')
                # use finish so that the show will call close
        else:
            self.dwell_counter=self.dwell_counter+1

            if self.dwell != 0 and self.dwell_counter ==  self.dwell:
                if self.finished_callback is not None:
                    self.finished_callback('pause_at_end','user quit or duration exceeded')
                    # use finish and pause_at_end so that the show will call close
            else:
                self.tick_timer=self.canvas.after(self.tick, self.do_dwell)

# *****************
# x content
# *****************    

    # called from Player, load_x_content       
    def load_track_content(self):
        # load message text
        if self.track_params['message-x'] != '':
            self.track_obj=self.canvas.create_text(int(self.track_params['message-x']), int(self.track_params['message-y']),
                                                   text=self.track.rstrip('\n'),
                                                   fill=self.track_params['message-colour'],
                                                   font=self.track_params['message-font'],
                                                   justify=self.track_params['message-justify'],
                                                   anchor = NW)
        else:
            self.track_obj=self.canvas.create_text(int(self.canvas['width'])/2, int(self.canvas['height'])/2,
                                                   text=self.track.rstrip('\n'),
                                                   fill=self.track_params['message-colour'],
                                                   font=self.track_params['message-font'],
                                                   justify=self.track_params['message-justify'])     

        return self.track_obj
    

    def hide_track_content(self):
        self.canvas.itemconfig(self.track_obj,state='hidden')
        self.canvas.delete(self.track_obj)

            
 
    
