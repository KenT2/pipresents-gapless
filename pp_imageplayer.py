import os
from Tkinter import CENTER,NW
from PIL import Image
from PIL import ImageTk
from pp_utils import StopWatch
from pp_utils import Monitor
from pp_player import Player

class ImagePlayer(Player):

    """ Displays an image on a canvas for a period of time. Image display can be paused and interrupted
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
                    
        # must be true if player is being used with the test harness
        self.testing=False
        
        self.trace=True
        # self.trace=False
        
        # debugging trace
        self.mon=Monitor()
        self.mon.on()
        
        # stopwatch for timing functions
        StopWatch.global_enable=False
        self.sw=StopWatch()
        self.sw.off()

        
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

        if self.trace: print '    Imageplayer/init ',self
        # and initialise things for this player
        
        # get duration from profile
        if self.track_params['duration'] != '':
            self.duration= int(self.track_params['duration'])
        else:
            self.duration= int(self.show_params['duration'])
            
        # get  image window from profile
        if self.track_params['image-window'].strip() != '':
            self.image_window= self.track_params['image-window'].strip()
        else:
            self.image_window= self.show_params['image-window'].strip()

        # parse the image_window
        status,self.command,self.has_coords,self.image_x1,self.image_y1,self.image_x2,self.image_y2,self.filter=self.parse_window(self.image_window)
        if status  == 'error':
            self.mon.err(self,'image window error: '+self.image_window)
            self.end('error','image window error')
        
        # initialise the state machine
        self.play_state='initialised'    
            
            
    # LOAD - loads the images and text
    def load(self,track,loaded_callback,enable_menu):  
        # instantiate arguments
        self.track=track
        self.loaded_callback=loaded_callback   # callback when loaded
        self.enable_menu=enable_menu
        if self.trace: print '    Imageplayer/load ',self
        
        # load the plugin, this may modify self.track and enable the plugin drawign to canvas
        if self.track_params['plugin'] != '':
            status,message=self.load_plugin()
            if status == 'error':
                self.mon.err(self,message)
                self.end('error',message)
                self=None

        # load the images and text
        status,message=self.load_x_content()
        if status == 'error':
            self.mon.err(self,message)
            self.end('error',message)
            self=None
        else:
            self.play_state='loaded'
            if self.loaded_callback is not None:
                self.loaded_callback('loaded','image track loaded')

            
    # UNLOAD - abort a load when omplayer is loading or loaded
    def unload(self):
        if self.trace: print '    Imageplayer/unload ',self
        # nothing to do for imageplayer
        self.mon.log(self,">unload received from show Id: "+ str(self.show_id))
        self.play_state='unloaded'
     
            

     # SHOW - show a track from its loaded state 
    def show(self,
                ready_callback,
                finished_callback,
                closed_callback,
                enable_menu=False):
                         
        # instantiate arguments
        self.ready_callback=ready_callback         # callback when ready to show an image - 
        self.finished_callback=finished_callback         # callback when finished showing 
        self.closed_callback=closed_callback            # callback when closed - not used by imageplayer
        self.enable_menu = enable_menu
        if self.trace: print '    Imageplayer/show ',self
        
        # init state and signals  
        self.tick = 100 # tick time for image display (milliseconds)
        self.dwell = 10*self.duration
        self.dwell_counter=0
        self.quit_signal=False
        self.paused=False
        self.pause_text=None

        self.show_x_content()
        
        if self.ready_callback is not None:
            self.ready_callback()

        # do common bits
        Player.pre_show(self)
        
        # start show state machine
        self.start_dwell()


    # CLOSE - nothing to do in imageplayer - x content is removed by ready callback and hide
    def close(self,closed_callback):
        if self.trace: print '    Imageplayer/close ',self
        self.closed_callback=closed_callback
        self.mon.log(self,">close received from show Id: "+ str(self.show_id))
        self.play_state='closed'
        if self.closed_callback is not None:
            self.closed_callback('normal','imageplayer closed')


    def input_pressed(self,symbol):
        if self.trace: print '    Imageplayer/input_pressed ',symbol
        if symbol  == 'pause':
            self.pause()
        elif symbol == 'stop':
            self.stop()

      
    def pause(self):
        if not self.paused:
            self.paused = True
        else:
            self.paused=False

    def stop(self):
        self.quit_signal=True
        


        
# ******************************************
# Sequencing
# ********************************************

    def start_dwell(self):
        self.play_state='showing'
        self.tick_timer=self.canvas.after(self.tick, self.do_dwell)

        
    def do_dwell(self):
        if self.quit_signal is  True:
            self.mon.log(self,"quit received")
            self.play_state='pause_at_end'
            if self.finished_callback is not None:
                self.finished_callback('pause_at_end','user quit or duration exceeded')
                # use finish so that the show will call close
        else:
            if self.paused is False:
                self.dwell_counter=self.dwell_counter+1

            # one time flipping of pause text
            if self.paused is True and self.pause_text is None:
                self.pause_text=self.canvas.create_text(100,100, anchor=NW,
                                                      text=self.resource('imageplayer','m01'),
                                                      fill="white",
                                                      font="arial 25 bold")
                self.canvas.update_idletasks( )
                
            if self.paused is False and self.pause_text is not None:
                    self.canvas.delete(self.pause_text)
                    self.pause_text=None
                    self.canvas.update_idletasks( )

            if self.dwell != 0 and self.dwell_counter == self.dwell:
                self.play_state='pause_at_end'
                if self.finished_callback is not None:
                    self.finished_callback('pause_at_end','user quit or duration exceeded')
                    # use finish so that the show will call close
            else:
                self.tick_timer=self.canvas.after(self.tick, self.do_dwell)



# *****************
# x content
# *****************          
                
    # called from Player, load_x_content      
            
    def load_track_content(self):
        self.canvas_centre_x = int(self.canvas['width'])/2
        self.canvas_centre_y = int(self.canvas['height'])/2
        
        # get the track to be displayed
        if os.path.exists(self.track) is True:
            pil_image=Image.open(self.track)
        else:
            pil_image=None
            self.tk_img=None
            self.track_image_obj=None

        # display track image                                    
        if pil_image is not None:
            self.image_width,self.image_height=pil_image.size

            if self.command == 'original':
                # display image at its original size
                if self.has_coords is False:
                    # load and display the unmodified image in centre
                    self.tk_img=ImageTk.PhotoImage(pil_image)
                    del pil_image
                    self.track_image_obj = self.canvas.create_image(self.canvas_centre_x, self.canvas_centre_y,
                                                  image=self.tk_img, anchor=CENTER)
                else:
                    # load and display the unmodified image at x1,y1
                    self.tk_img=ImageTk.PhotoImage(pil_image)
                    self.track_image_obj = self.canvas.create_image(self.image_x1, self.image_y1,
                                                      image=self.tk_img, anchor=NW)


            elif self.command in ('fit','shrink'):
                    # shrink fit the window or screen preserving aspect
                    if self.has_coords is True:
                        window_width=self.image_x2 - self.image_x1
                        window_height=self.image_y2 - self.image_y1
                        window_centre_x=(self.image_x2+self.image_x1)/2
                        window_centre_y= (self.image_y2+self.image_y1)/2
                    else:
                        window_width=int(self.canvas['width'])
                        window_height=int(self.canvas['height'])
                        window_centre_x=self.canvas_centre_x
                        window_centre_y=self.canvas_centre_y
                    
                    if (self.image_width > window_width or self.image_height > window_height and self.command == 'fit') or (self.command == 'shrink') :
                        # original image is larger or , shrink it to fit the screen preserving aspect
                        pil_image.thumbnail((window_width,window_height),eval(self.filter))                 
                        self.tk_img=ImageTk.PhotoImage(pil_image)
                        del pil_image
                        self.track_image_obj = self.canvas.create_image(window_centre_x, window_centre_y,
                                                      image=self.tk_img, anchor=CENTER)
                    else:
                        # fitting and original image is smaller, expand it to fit the screen preserving aspect
                        prop_x = float(window_width) / self.image_width
                        prop_y = float(window_height) / self.image_height
                        if prop_x > prop_y:
                            prop=prop_y
                        else:
                            prop=prop_x
                            
                        increased_width=int(self.image_width * prop)
                        increased_height=int(self.image_height * prop)
                        # print 'result',prop, increased_width,increased_height
                        pil_image=pil_image.resize((increased_width, increased_height),eval(self.filter))
                        self.tk_img=ImageTk.PhotoImage(pil_image)
                        del pil_image
                        self.track_image_obj = self.canvas.create_image(window_centre_x, window_centre_y,
                                                      image=self.tk_img, anchor=CENTER)                                                 

            elif self.command in ('warp'):
                    # resize to window or screen without preserving aspect
                    if self.has_coords is True:
                        window_width=self.image_x2 - self.image_x1
                        window_height=self.image_y2 - self.image_y1
                        window_centre_x=(self.image_x2+self.image_x1)/2
                        window_centre_y= (self.image_y2+self.image_y1)/2
                    else:
                        window_width=int(self.canvas['width'])
                        window_height=int(self.canvas['height'])
                        window_centre_x=self.canvas_centre_x
                        window_centre_y=self.canvas_centre_y
                    
                    pil_image=pil_image.resize((window_width, window_height),eval(self.filter))
                    self.tk_img=ImageTk.PhotoImage(pil_image)
                    del pil_image
                    self.track_image_obj = self.canvas.create_image(window_centre_x, window_centre_y,
                                                  image=self.tk_img, anchor=CENTER)


    def show_track_content(self):
            self.canvas.itemconfig(self.track_image_obj,state='normal')

    def hide_track_content(self):
        self.canvas.itemconfig(self.track_image_obj,state='hidden')
        self.canvas.delete(self.track_image_obj)
        self.tk_img=None
            
        

    def parse_window(self,line):
        
            fields = line.split()
            # check there is a command field
            if len(fields) < 1:
                    return 'error','',False,0,0,0,0,''
                
            # deal with original whch has 0 or 2 arguments
            filter=''
            if fields[0] == 'original':
                if len(fields) not in (1,3):
                        return 'error','',False,0,0,0,0,''       
                # deal with window coordinates    
                if len(fields)  ==  3:
                    # window is specified
                    if not (fields[1].isdigit() and fields[2].isdigit()):
                        return 'error','',False,0,0,0,0,''
                    has_window=True
                    return 'normal',fields[0],has_window,int(fields[1]),int(fields[2]),0,0,filter
                else:
                    # no window
                    has_window=False 
                    return 'normal',fields[0],has_window,0,0,0,0,filter



            # deal with remainder which has 1, 2, 5 or  6arguments
            # check basic syntax
            if  fields[0] not in ('shrink','fit','warp'):
                    return 'error','',False,0,0,0,0,'' 
            if len(fields) not in (1,2,5,6):
                    return 'error','',False,0,0,0,0,''
            if len(fields) == 6 and fields[5] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS'):
                    return 'error','',False,0,0,0,0,''
            if len(fields) == 2 and fields[1] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS'):
                    return 'error','',False,0,0,0,0,''
            
            # deal with window coordinates    
            if len(fields) in (5,6):
                # window is specified
                if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                    return 'error','',False,0,0,0,0,''
                has_window=True
                if len(fields) == 6:
                    filter=fields[5]
                else:
                    filter='Image.NEAREST'
                    return 'normal',fields[0],has_window,int(fields[1]),int(fields[2]),int(fields[3]),int(fields[4]),filter
            else:
                # no window
                has_window=False
                if len(fields) == 2:
                    filter=fields[1]
                else:
                    filter='Image.NEAREST'
                return 'normal',fields[0],has_window,0,0,0,0,filter
                

    
