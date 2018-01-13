# dec 2015 - !!!!!! bug in pause half corrected 
# feb 2016 fix bug in pause properly

import os
from Tkinter import CENTER,NW
from PIL import Image
from PIL import ImageTk
from pp_utils import StopWatch, parse_rectangle,calculate_text_position
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
        # and initialise things for this player
        # print 'imageplayer init'
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


        # get  image rotation from profile
        if self.track_params['image-rotate'].strip() != '':
            self.image_rotate = int(self.track_params['image-rotate'].strip())
        else:
            self.image_rotate= int(self.show_params['image-rotate'].strip())


        if self.track_params['pause-timeout'] != '':
            pause_timeout_text= self.track_params['pause-timeout']
        else:
            pause_timeout_text= self.show_params['pause-timeout']

        if pause_timeout_text.isdigit():
            self.pause_timeout= int(pause_timeout_text)
        else:
            self.pause_timeout=0



        self.track_image_obj=None
        self.tk_img=None
        self.paused=False
        self.pause_text_obj=None
        self.pause_timer= None

        # initialise the state machine
        self.play_state='initialised'    
            
            
    # LOAD - loads the images and text
    def load(self,track,loaded_callback,enable_menu):  
        # instantiate arguments
        self.track=track
        # print 'imageplayer load',self.track
        self.loaded_callback=loaded_callback   # callback when loaded
        self.mon.trace(self,'')


        Player.pre_load(self)

        # parse the image_window
        status,message,self.command,self.has_coords,self.window_x1,self.window_y1,self.window_x2,self.window_y2,self.image_filter=self.parse_window(self.image_window)
        if status  == 'error':
            self.mon.err(self,'image window error, '+message+ ': '+self.image_window)
            self.play_state='load-failed'
            self.loaded_callback('error','image window error, '+message+ ': '+self.image_window)
            return
 
        # load the plugin, this may modify self.track and enable the plugin drawing to canvas
        if self.track_params['plugin'] != '':
            status,message=self.load_plugin()
            if status == 'error':
                self.mon.err(self,message)
                self.play_state='load-failed'
                self.loaded_callback('error',message)
                return


        # load the images and text
        status,message=Player.load_x_content(self,enable_menu)
        if status == 'error':
            self.mon.err(self,message)
            self.play_state='load-failed'
            self.loaded_callback('error',message)
            return
        else:
            self.play_state='loaded'
            if self.loaded_callback is not None:
                self.loaded_callback('loaded','image track loaded')

            
    # UNLOAD - abort a load when sub-process is loading or loaded
    def unload(self):
        self.mon.trace(self,'')        
        # nothing to do for imageplayer
        self.mon.log(self,">unload received from show Id: "+ str(self.show_id))
        self.play_state='unloaded'
     
            

     # SHOW - show a track from its loaded state 
    def show(self,ready_callback,finished_callback,closed_callback):
                         
        # instantiate arguments
        self.ready_callback=ready_callback         # callback when ready to show an image - 
        self.finished_callback=finished_callback         # callback when finished showing 
        self.closed_callback=closed_callback            # callback when closed - not used by imageplayer

        self.mon.trace(self,'')
        
        # init state and signals  
        self.tick = 100 # tick time for image display (milliseconds)
        self.dwell = 10*self.duration
        self.dwell_counter=0
        self.quit_signal=False
        self.paused=False
        self.pause_text_obj=None

        # do common bits
        Player.pre_show(self)
        
        # start show state machine
        self.start_dwell()


    # CLOSE - nothing to do in imageplayer - x content is removed by ready callback and hide
    def close(self,closed_callback):
        self.mon.trace(self,'')
        self.closed_callback=closed_callback
        self.mon.log(self,">close received from show Id: "+ str(self.show_id))
        if self.tick_timer!= None:
            self.canvas.after_cancel(self.tick_timer)
        self.play_state='closed'
        if self.closed_callback is not None:
            self.closed_callback('normal','imageplayer closed')


    def input_pressed(self,symbol):
        self.mon.trace(self,symbol)
        if symbol  == 'pause':
            self.pause()
        if symbol  == 'pause-on':
            self.pause_on()
        if symbol  == 'pause-off':
            self.pause_off()
        elif symbol == 'stop':
            self.stop()

      
    def pause(self):
        if self.paused is False: 
            self.paused = True
            if self.pause_timeout>0:
                # kick off the pause teimeout timer
                print "!!toggle pause on"
                self.pause_timer=self.canvas.after(self.pause_timeout*1000,self.pause_timeout_callback)
        else:
            self.paused=False
            # cancel the pause timer
            if self.pause_timer != None:
                print "!!toggle pause off"
                self.canvas.after_cancel(self.pause_timer)
                self.pause_timer=None


    def pause_timeout_callback(self):
        print "!!callback pause off"
        self.pause_off()
        self.pause_timer=None

    def pause_on(self):
        self.paused = True
        print "!!pause on"
        self.pause_timer=self.canvas.after(self.pause_timeout*1000,self.pause_timeout_callback)
 

    def pause_off(self):
        self.paused = False
        print "!!pause off"
        # cancel the pause timer
        if self.pause_timer != None:
            self.canvas.after_cancel(self.pause_timer)
            self.pause_timer=None
 

    def stop(self):
        # cancel the pause timer
        if self.pause_timer != None:
            self.canvas.after_cancel(self.pause_timer)
            self.pause_timer=None
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
            if self.finished_callback is not None:
                self.finished_callback('pause_at_end','user quit or duration exceeded')
                # use finish so that the show will call close
        else:
            if self.paused is False:
                self.dwell_counter=self.dwell_counter+1

            # one time flipping of pause text
            pause_text= self.track_params['pause-text']
            if self.paused is True and self.pause_text_obj is None:
                x,y,anchor,justify=calculate_text_position(self.track_params['pause-text-x'],self.track_params['pause-text-y'],
                                             self.show_canvas_x1,self.show_canvas_y1,
                                             self.show_canvas_centre_x,self.show_canvas_centre_y,
                                             self.show_canvas_x2,self.show_canvas_y2,self.track_params['pause-text-justify'])                
                self.pause_text_obj=self.canvas.create_text(x,y, anchor=anchor,justify=justify,
                                                        text=pause_text,
                                                        fill=self.track_params['pause-text-colour'],
                                                        font=self.track_params['pause-text-font'])
                self.canvas.update_idletasks( )
                
            if self.paused is False and self.pause_text_obj is not None:
                self.canvas.delete(self.pause_text_obj)
                self.pause_text_obj=None
                self.canvas.update_idletasks( )

            if self.dwell != 0 and self.dwell_counter == self.dwell:
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
        ppil_image=None  # Keep landscape happy
        
        # get the track to be displayed
        if os.path.exists(self.track) is True:
            try:
                ppil_image=Image.open(self.track)
            except:
                ppil_image=None
                self.tk_img=None
                self.track_image_obj=None
                return 'error','Not a recognised image format '+ self.track                
        else:
            ppil_image=None
            self.tk_img=None
            self.track_image_obj=None
            return 'error','Track file not found '+ self.track

        # display track image
        if ppil_image is not None:
            #rotate the image
            # print self.image_width,self.image_height
            if self.image_rotate!=0:
                ppil_image=ppil_image.rotate(self.image_rotate,expand=True)      
            self.image_width,self.image_height=ppil_image.size
            # print self.image_width,self.image_height

            
            if self.command == 'original':
                # display image at its original size
                if self.has_coords is False:
                    
                    # load and display the unmodified image in centre
                    self.tk_img=ImageTk.PhotoImage(ppil_image)
                    del ppil_image
                    self.track_image_obj = self.canvas.create_image(self.show_canvas_centre_x+self.show_canvas_x1,
                                                                    self.show_canvas_centre_y+self.show_canvas_y1,
                                                                    image=self.tk_img, anchor=CENTER)
                else:
                    # load and display the unmodified image at x1,y1
                    self.tk_img=ImageTk.PhotoImage(ppil_image)
                    del ppil_image
                    self.track_image_obj = self.canvas.create_image(self.window_x1+self.show_canvas_x1,
                                                                    self.window_y1+self.show_canvas_y1,
                                                                    image=self.tk_img, anchor=NW)


            elif self.command in ('fit','shrink'):
                # shrink fit the window or screen preserving aspect
                if self.has_coords is True:
                    window_width=self.window_x2 - self.window_x1
                    window_height=self.window_y2 - self.window_y1
                    window_centre_x=(self.window_x2+self.window_x1)/2
                    window_centre_y= (self.window_y2+self.window_y1)/2
                else:
                    window_width=self.show_canvas_width
                    window_height=self.show_canvas_height
                    window_centre_x=self.show_canvas_centre_x
                    window_centre_y=self.show_canvas_centre_y
                if (self.image_width > window_width or self.image_height > window_height and self.command == 'fit') or (self.command == 'shrink') :
                    # print 'show canvas',self.show_canvas_x1,self.show_canvas_y1,self.show_canvas_x2,self.show_canvas_y2
                    # print 'canvas width/height/centre',self.show_canvas_width,self.show_canvas_height,self.show_canvas_centre_x,self.show_canvas_centre_y
                    # print 'window dimensions/centre',window_width,window_height,window_centre_x,window_centre_y
                    # print
                    # original image is larger or , shrink it to fit the screen preserving aspect
                    # print ppil_image.size
                    ppil_image.thumbnail((int(window_width),int(window_height)),eval(self.image_filter))
                    # print ppil_image.size
                    self.tk_img=ImageTk.PhotoImage(ppil_image)
                    del ppil_image
                    self.track_image_obj = self.canvas.create_image(window_centre_x + self.show_canvas_x1,
                                                                    window_centre_y + self.show_canvas_y1,
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
                    ppil_image=ppil_image.resize((int(increased_width), int(increased_height)),eval(self.image_filter))
                    self.tk_img=ImageTk.PhotoImage(ppil_image)
                    del ppil_image
                    self.track_image_obj = self.canvas.create_image(window_centre_x + self.show_canvas_x1,
                                                                    window_centre_y + self.show_canvas_y1,
                                                                    image=self.tk_img, anchor=CENTER)                                                 

            elif self.command in ('warp'):
                # resize to window or screen without preserving aspect
                if self.has_coords is True:
                    window_width=self.window_x2 - self.window_x1
                    window_height=self.window_y2 - self.window_y1
                    window_centre_x=(self.window_x2+self.window_x1)/2
                    window_centre_y= (self.window_y2+self.window_y1)/2
                else:
                    window_width=self.show_canvas_width
                    window_height=self.show_canvas_height
                    window_centre_x=self.show_canvas_centre_x
                    window_centre_y=self.show_canvas_centre_y

                # print 'window',window_width,window_height,window_centre_x,window_centre_y,self.show_canvas_x1,self.show_canvas_y1,'\n'
                ppil_image=ppil_image.resize((int(window_width), int(window_height)),eval(self.image_filter))
                self.tk_img=ImageTk.PhotoImage(ppil_image)
                del ppil_image
                self.track_image_obj = self.canvas.create_image(window_centre_x+ self.show_canvas_x1,
                                                                window_centre_y+ self.show_canvas_y1,
                                                               image=self.tk_img, anchor=CENTER)
        self.canvas.itemconfig(self.track_image_obj,state='hidden')
        return 'normal','track content loaded';

    def show_track_content(self):
        self.canvas.itemconfig(self.track_image_obj,state='normal')

    def hide_track_content(self):
        if self.pause_text_obj is not None:
            self.canvas.delete(self.pause_text_obj)
            self.pause_text_obj=None
            # self.canvas.update_idletasks( )
        self.canvas.itemconfig(self.track_image_obj,state='hidden')
        self.canvas.delete(self.track_image_obj)
        self.tk_img=None
            
        

    def parse_window(self,line):
        
        fields = line.split()
        # check there is a command field
        if len(fields) < 1:
            return 'error','No command field','',False,0,0,0,0,''

            
        # deal with original whch has 0 or 2 arguments
        image_filter=''
        if fields[0] == 'original':
            if len(fields) not in (1,3):
                return 'error','Original has wrong number of arguments','',False,0,0,0,0,''       
            # deal with window coordinates    
            if len(fields)  ==  3:
                # window is specified
                if not (fields[1].isdigit() and fields[2].isdigit()):
                    return 'error','coordinates are not numbers','',False,0,0,0,0,''
                has_window=True
                return 'normal','',fields[0],has_window,float(fields[1]),float(fields[2]),0,0,image_filter
            else:
                # no window
                has_window=False 
                return 'normal','',fields[0],has_window,0,0,0,0,image_filter



        # deal with remainder which has 1, 2, 5 or  6arguments
        # check basic syntax
        if  fields[0] not in ('shrink','fit','warp'):
            return 'error','illegal command'+fields[0],'',False,0,0,0,0,'' 
        if len(fields) not in (1,2,3,5,6):
            return 'error','wrong number of fields' + str(len(fields)),'',False,0,0,0,0,''
        if len(fields) == 6 and fields[5] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS'):
            return 'error','wrong filter or params'+ fields[5],'',False,0,0,0,0,''
        if len(fields) == 2 and (fields[1] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS') and '*' not in fields[1]):
            return 'error','wrong filter or params'+ fields[1],'',False,0,0,0,0,''
        if len(fields) == 3 and fields[2] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS'):
            return 'error','wrong filter or params'+ fields[2],'',False,0,0,0,0,''


        # deal with no window coordinates and no
        if len(fields) == 1:
            has_window=False           
            return 'normal','',fields[0],has_window,0,0,0,0,'Image.NEAREST'
   
        # deal with window coordinates in +* format with optional filter
        if len(fields) in (2,3) and '*' in fields[1]:
            status,message,x1,y1,x2,y2 = parse_rectangle(fields[1])
            if status=='error':
                return 'error',message,'',False,0,0,0,0,''
            else:
                has_window=True
                if len(fields) == 3:
                    image_filter='Image.'+fields[2]
                else:
                    image_filter='Image.NEAREST'                
                return 'normal','',fields[0],has_window,x1,y1,x2,y2,image_filter
            
        if len(fields) in (5,6):
            # window is specified in x1 y1 x2 y2
            if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                return 'error','coords are not numbers','',False,0,0,0,0,''
            has_window=True
            if len(fields) == 6:
                image_filter='Image.'+fields[5]
            else:
                image_filter='Image.NEAREST'
            return 'normal','',fields[0],has_window,float(fields[1]),float(fields[2]),float(fields[3]),float(fields[4]),image_filter

        else:
            # no window
            has_window=False
            if len(fields) == 2:
                image_filter='Image.'+fields[1]
            else:
                image_filter='Image.NEAREST'
            return 'normal','',fields[0],has_window,0,0,0,0,image_filter

    
