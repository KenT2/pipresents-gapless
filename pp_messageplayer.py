from Tkinter import NW,N,W,CENTER,LEFT,RIGHT
from pp_utils import StopWatch,calculate_text_position
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
                 end_callback,
                 command_callback):

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
                         end_callback,
                         command_callback)                    

        # stopwatch for timing functions
        StopWatch.global_enable=False
        self.sw=StopWatch()
        self.sw.off()

        self.mon.trace(self,'')
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
        self.mon.trace(self,'')

        # do common bits of  load
        Player.pre_load(self)   

        # load the plugin, this may modify self.ttack and enable the plugin drawign to canvas
        if self.track_params['plugin'] != '':
            status,message=self.load_plugin()
            if status == 'error':
                self.mon.err(self,message)
                self.play_state='load-failed'
                if self.loaded_callback is not  None:
                    self.loaded_callback('error',message)
                    return


        # load the images and text including message text
        status,message=self.load_x_content(enable_menu)
        if status == 'error':
            self.mon.err(self,message)
            self.play_state='load-failed'
            if self.loaded_callback is not  None:
                self.loaded_callback('error',message)
                return
        else:
            self.play_state='loaded'
            if self.loaded_callback is not None:
                self.loaded_callback('loaded','message track loaded')

            
    # UNLOAD - abort a load when omplayer is loading or loaded
    def unload(self):
        self.mon.trace(self,'')
        # nothing to do for Messageplayer
        self.mon.log(self,">unload received from show Id: "+ str(self.show_id))
        self.play_state='unloaded'
     
            

     # SHOW - show a track from its loaded state 
    def show(self,ready_callback,finished_callback,closed_callback):
                         
        # instantiate arguments
        self.ready_callback=ready_callback         # callback when ready to show an image - 
        self.finished_callback=finished_callback         # callback when finished showing 
        self.closed_callback=closed_callback            # callback when closed - not used by Messageplayer

        self.mon.trace(self,'')
        # init state and signals  
        self.tick = 100 # tick time for image display (milliseconds)
        self.dwell = 10*self.duration
        self.dwell_counter=0
        self.quit_signal=False

        # do common bits
        Player.pre_show(self)
        
        # start show state machine
        self.start_dwell()

    # CLOSE - nothing to do in messageplayer - x content is removed by ready callback
    def close(self,closed_callback):
        self.mon.trace(self,'')
        self.closed_callback=closed_callback
        self.mon.log(self,">close received from show Id: "+ str(self.show_id))
        if self.tick_timer!= None:
            self.canvas.after_cancel(self.tick_timer)
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
        # print 'show canvas',self.show_canvas_x1,self.show_canvas_y1,self.show_canvas_x2,self.show_canvas_y2
        #  print 'canvas width/height/centre',self.show_canvas_width,self.show_canvas_height,self.show_canvas_centre_x,self.show_canvas_centre_y
        #  print
    
        x,y,anchor,justify=calculate_text_position(self.track_params['message-x'],self.track_params['message-y'],
                                     self.show_canvas_x1,self.show_canvas_y1,
                                     self.show_canvas_centre_x,self.show_canvas_centre_y,
                                     self.show_canvas_x2,self.show_canvas_y2,self.track_params['message-justify'])
        

        self.track_obj=self.canvas.create_text(x,y,
                                               text=self.track.rstrip('\n'),
                                               fill=self.track_params['message-colour'],
                                               font=self.track_params['message-font'],
                                               justify=justify,
                                               anchor = anchor)
            
        self.canvas.itemconfig(self.track_obj,state='hidden')
        return 'normal','message loaded'
    

    def show_track_content(self):
        self.canvas.itemconfig(self.track_obj,state='normal')

    def hide_track_content(self):
        self.canvas.itemconfig(self.track_obj,state='hidden')
        self.canvas.delete(self.track_obj)

            
 
    
