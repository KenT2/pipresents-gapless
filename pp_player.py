import os
from Tkinter import NW
from PIL import Image
from PIL import ImageTk

from pp_pluginmanager import PluginManager
from pp_animate import Animate
from pp_utils import Monitor,calculate_text_position

class Player(object):

    # common bits of __init__(...)
    def __init__(self,
                 show_id,
                 showlist,
                 root,
                 canvas,
                 show_params,
                 track_params,
                 pp_dir,
                 pp_home,
                 pp_profile,
                 end_callback,
                 command_callback):

        # create debugging log object
        self.mon=Monitor()

        self.mon.trace(self,'')

        # instantiate arguments
        self.show_id=show_id
        self.showlist=showlist
        self.root=root
        self.canvas=canvas['canvas-obj']
        self.show_canvas_x1 = canvas['show-canvas-x1']
        self.show_canvas_y1 = canvas['show-canvas-y1']
        self.show_canvas_x2 = canvas['show-canvas-x2']
        self.show_canvas_y2 = canvas['show-canvas-y2']
        self.show_canvas_width = canvas['show-canvas-width']
        self.show_canvas_height= canvas['show-canvas-height']
        self.show_canvas_centre_x= canvas['show-canvas-centre-x']
        self.show_canvas_centre_y= canvas['show-canvas-centre-y']
        self.show_params=show_params
        self.track_params=track_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile
        self.end_callback=end_callback
        self.command_callback=command_callback
                
        # get background image from profile.
        self.background_file=''
        if self.track_params['background-image'] != '':
            self.background_file= self.track_params['background-image']

            
        # get background colour from profile.
        if self.track_params['background-colour'] != '':
            self.background_colour= self.track_params['background-colour']
        else:
            self.background_colour= self.show_params['background-colour']
        
        # get animation instructions from profile
        self.animate_begin_text=self.track_params['animate-begin']
        self.animate_end_text=self.track_params['animate-end']

        # create an  instance of showmanager so we can control concurrent shows
        # self.show_manager=ShowManager(self.show_id,self.showlist,self.show_params,self.root,self.canvas,self.pp_dir,self.pp_profile,self.pp_home)

        # open the plugin Manager
        self.pim=PluginManager(self.show_id,self.root,self.canvas,self.show_params,self.track_params,self.pp_dir,self.pp_home,self.pp_profile) 

        # create an instance of Animate so we can send animation commands
        self.animate = Animate()

        # initialise state and signals
        self.background_obj=None
        self.show_text_obj=None
        self.track_text_obj=None
        self.hint_obj=None
        self.background=None
        self.freeze_at_end_required='no' # overriden by videoplayer
        self.tick_timer=None
        self.terminate_signal=False
        self.play_state=''



    def pre_load(self):

        pass

              
    # common bits of show(....) 
    def pre_show(self):
        self.mon.trace(self,'')

        # show_x_content moved to just before ready_callback to improve flicker.
        self.show_x_content()
  
        #ready callback hides and closes players from previous track, also displays show background
        if self.ready_callback is not None:
            self.ready_callback(self.enable_show_background)


        # Control other shows and do counters and osc at beginning
        self.show_control(self.track_params['show-control-begin'])

        # and show whatever the plugin has created
        self.show_plugin()
        
        # create animation events
        reason,message=self.animate.animate(self.animate_begin_text,id(self))
        if reason  ==  'error':
            self.mon.err(self,message)
            self.play_state='show-failed'
            if self.finished_callback is not None:
                self.finished_callback('error',message)
        else:
            # return to start playing the track.
            self.mon.log(self,">show track received from show Id: "+ str(self.show_id))
            return


    # to keep landscape happy
    def ready_callback(self,enable_show_background):
        self.mon.fatal(self,'ready callback not overridden')
        self.end('error','ready callback not overridden')

    def finished_callback(self,reason,message):
        self.mon.fatal(self,'finished callback not overridden')
        self.end('error','finished callback not overridden')

    def closed_callback(self,reason,message):
        self.mon.fatal(self,'closed callback not overridden')
        self.end('error','closed callback not overridden')


# Control shows so pass the show control commands back to PiPresents via the command callback
    def show_control(self,show_control_text): 
        lines = show_control_text.split('\n')
        for line in lines:
            if line.strip() == "":
                continue
            # print 'show control command: ',line
            self.command_callback(line, source='track',show=self.show_params['show-ref'])



# *****************
# hide content and end animation, show control etc.
# called by ready calback and end
# *****************

    def hide(self):
        self.mon.trace(self,'')
        # abort the timer
        if self.tick_timer is not None:
            self.canvas.after_cancel(self.tick_timer)
            self.tick_timer=None
        
        self.hide_x_content()
        
        # stop the plugin
        self.hide_plugin()

        # Control concurrent shows at end
        self.show_control(self.track_params['show-control-end'])
        
        # clear events list for this track
        if self.track_params['animate-clear'] == 'yes':
            self.animate.clear_events_list(id(self))
                
        # create animation events for ending
        # !!!!! TEMPORARY FIX
        reason,message=self.animate.animate(self.animate_end_text,id(self))
        if reason == 'error':
            self.mon.err(self,message)
            # self.play_state='show-failed'
            # if self.finished_callback is not None:
                # self.finished_callback('error',message)
        else:
            return


    def terminate(self):
        self.mon.trace(self,'')
        self.terminate_signal=True
        if self.play_state == 'showing':
            # call the derived class's stop method
            self.stop()
        else:
            self.end('killed','terminate with no track or show open')

    # must be overriden by derived class
    def stop(self):
        self.mon.fatal(self,'stop not overidden by derived class')
        self.play_state='show-failed'
        if self.finished_callback is not None:
            self.finished_callback('error','stop not overidden by derived class')


    def get_play_state(self):
        return self.play_state
  
# *****************
# ending the player
# *****************

    def end(self,reason,message):
        self.mon.trace(self,'')
        # stop the plugin

        if self.terminate_signal is True:
            reason='killed'
            self.terminate_signal=False
            self.hide()

        self.end_callback(reason,message)
        self=None


# *****************
# displaying common things
# *****************

    def load_plugin(self):
        # called in load before load_x_content modify the track here
        if self.track_params['plugin'] != '':
            reason,message,self.track = self.pim.load_plugin(self.track,self.track_params['plugin'])
            return reason,message
        
    def show_plugin(self):
        # called at show time, write to the track here if you need it after show_control_begin (counters)
        if self.track_params['plugin'] != '':
            self.pim.show_plugin()

    def hide_plugin(self):
        # called at the end of the track
        if self.track_params['plugin'] != '':
            self.pim.stop_plugin()

    def load_x_content(self,enable_menu):
        self.mon.trace(self,'')
        self.background_obj=None
        self.background=None
        self.track_text_obj=None
        self.show_text_obj=None
        self.hint_obj=None
        self.track_obj=None

        
        # background image
        if self.background_file != '':
            background_img_file = self.complete_path(self.background_file)
            if not os.path.exists(background_img_file):
                return 'error',"Track background file not found "+ background_img_file
            else:
                try:
                    pil_background_img=Image.open(background_img_file)
                except:
                    pil_background_img=None
                    self.background=None
                    self.background_obj=None
                    return 'error','Track background, not a recognised image format '+ background_img_file                
                # print 'pil_background_img ',pil_background_img
                image_width,image_height=pil_background_img.size
                window_width=self.show_canvas_width
                window_height=self.show_canvas_height
                if image_width != window_width or image_height != window_height:
                    pil_background_img=pil_background_img.resize((window_width, window_height))
                self.background = ImageTk.PhotoImage(pil_background_img)
                del pil_background_img
                self.background_obj = self.canvas.create_image(self.show_canvas_x1,
                                                               self.show_canvas_y1,
                                                               image=self.background,
                                                               anchor=NW)
                # print '\nloaded background_obj: ',self.background_obj


        # load the track content.  Dummy function below is overridden in players          
        status,message=self.load_track_content()
        if status == 'error':
            return 'error',message
                          
        # load show text if enabled
        if self.show_params['show-text'] !=  '' and self.track_params['display-show-text'] == 'yes':

            x,y,anchor,justify=calculate_text_position(self.show_params['show-text-x'],self.show_params['show-text-y'],
                                     self.show_canvas_x1,self.show_canvas_y1,
                                     self.show_canvas_centre_x,self.show_canvas_centre_y,
                                     self.show_canvas_x2,self.show_canvas_y2,self.show_params['show-text-justify'])
 
            self.show_text_obj=self.canvas.create_text(x,y,
                                                       anchor=anchor,
                                                       justify=justify,
                                                       text=self.show_params['show-text'],
                                                       fill=self.show_params['show-text-colour'],
                                                       font=self.show_params['show-text-font'])


        # load track text if enabled

        if self.track_params['track-text-x'] =='':
            track_text_x= self.show_params['track-text-x']
        else:
            track_text_x= self.track_params['track-text-x']


        if self.track_params['track-text-y'] =='':
            track_text_y= self.show_params['track-text-y']
        else:
            track_text_y= self.track_params['track-text-y']

        if self.track_params['track-text-justify'] =='':
            track_text_justify= self.show_params['track-text-justify']
        else:
            track_text_justify= self.track_params['track-text-justify']

        if self.track_params['track-text-font'] =='':
            track_text_font= self.show_params['track-text-font']
        else:
            track_text_font= self.track_params['track-text-font']
            

        if self.track_params['track-text-colour'] =='':
            track_text_colour= self.show_params['track-text-colour']
        else:
            track_text_colour= self.track_params['track-text-colour']
            
            
        if self.track_params['track-text'] !=  '':

            x,y,anchor,justify=calculate_text_position(track_text_x,track_text_y,
                                     self.show_canvas_x1,self.show_canvas_y1,
                                     self.show_canvas_centre_x,self.show_canvas_centre_y,
                                     self.show_canvas_x2,self.show_canvas_y2,track_text_justify)
 
            
            self.track_text_obj=self.canvas.create_text(x,y,
                                                        anchor=anchor,
                                                        justify=justify,
                                                        text=self.track_params['track-text'],
                                                        fill=track_text_colour,
                                                        font=track_text_font)

        # load instructions if enabled
        if enable_menu is  True:

            x,y,anchor,justify=calculate_text_position(self.show_params['hint-x'],self.show_params['hint-y'],
                                     self.show_canvas_x1,self.show_canvas_y1,
                                     self.show_canvas_centre_x,self.show_canvas_centre_y,
                                     self.show_canvas_x2,self.show_canvas_y2,self.show_params['hint-justify'])
 

            self.hint_obj=self.canvas.create_text(x,y,
                                                  justify=justify,
                                                  text=self.show_params['hint-text'],
                                                  fill=self.show_params['hint-colour'],
                                                  font=self.show_params['hint-font'],
                                                  anchor=anchor)

        self.display_show_canvas_rectangle()

        self.canvas.tag_raise('pp-click-area')
        self.canvas.itemconfig(self.background_obj,state='hidden')
        self.canvas.itemconfig(self.show_text_obj,state='hidden')
        self.canvas.itemconfig(self.track_text_obj,state='hidden')
        self.canvas.itemconfig(self.hint_obj,state='hidden')
        self.canvas.update_idletasks( )
        return 'normal','x-content loaded'


    # display the rectangle that is the show canvas
    def display_show_canvas_rectangle(self):
        # coords=[self.show_canvas_x1,self.show_canvas_y1,self.show_canvas_x2-1,self.show_canvas_y2-1]
        # self.canvas.create_rectangle(coords,
        #            outline='yellow',
        #          fill='')
        pass


    # dummy functions to manipulate the track content, overidden in some players,
    # message text in messageplayer
    # image in imageplayer
    # menu stuff in menuplayer
        
    def load_track_content(self):
        return 'normal','player has no track content to load'

    def show_track_content(self):
        pass

    def hide_track_content(self):
        pass

    def show_x_content(self):
        self.mon.trace(self,'')
        # background colour
        if  self.background_colour != '':
            self.canvas.config(bg=self.background_colour)
        # print 'showing background_obj: ', self.background_obj
        # reveal background image and text
        self.canvas.itemconfig(self.background_obj,state='normal')
        self.show_track_content()

        self.canvas.itemconfig(self.show_text_obj,state='normal')
        self.canvas.itemconfig(self.track_text_obj,state='normal')
        self.canvas.itemconfig(self.hint_obj,state='normal')
        # self.canvas.update_idletasks( )

        # decide whether the show background should be enabled.
        # print 'DISPLAY SHOW BG',self.track_params['display-show-background'],self.background_obj
        if self.background_obj is None and self.track_params['display-show-background']=='yes':
            self.enable_show_background=True
        else:
            self.enable_show_background=False
        # print 'ENABLE SB',self.enable_show_background


    def hide_x_content(self):
        self.mon.trace(self,'')
        self.hide_track_content()
        self.canvas.itemconfig(self.background_obj,state='hidden')
        self.canvas.itemconfig(self.show_text_obj,state='hidden')
        self.canvas.itemconfig(self.track_text_obj,state='hidden')
        self.canvas.itemconfig(self.hint_obj,state='hidden')
        # self.canvas.update_idletasks( )
        
        self.canvas.delete(self.background_obj)
        self.canvas.delete(self.show_text_obj)
        self.canvas.delete(self.track_text_obj)
        self.canvas.delete(self.hint_obj)
        self.background=None
        # self.canvas.update_idletasks( )


# ****************
# utilities
# *****************

    def get_links(self):
        return self.track_params['links']

    # produce an absolute path from the relative one in track paramters
    def complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file[0] == "+":
            track_file=self.pp_home+track_file[1:]
        elif track_file[0] == "@":
            track_file=self.pp_profile+track_file[1:]
        return track_file
        
    # get a text string from resources.cfg
    def resource(self,section,item):
        value=self.rr.get(section,item)
        return value # False if not found


