import os
from Tkinter import CENTER, NW
from PIL import Image
from PIL import ImageTk

from pp_showmanager import ShowManager
from pp_pluginmanager import PluginManager
from pp_gpio import PPIO
from pp_resourcereader import ResourceReader
from pp_utils import Monitor

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
                 end_callback):

        # init trace to off, derived classes can turn it on
        self.trace=False

        # create debugging log object
        self.mon=Monitor()

        # must be true if player is being used with the test harness
        # it removes all the subsiduary functions such as animation
        self.testing=False
        
        if self.trace: print '    Player/init ',self
        # instantiate arguments
        self.show_id=show_id
        self.showlist=showlist
        self.root=root
        self.canvas = canvas
        self.show_params=show_params
        self.track_params=track_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile
        self.end_callback=end_callback
        
        # open resources
        self.rr=ResourceReader()
                        
        # get background image from profile.
        self.background_file=''
        if self.track_params['background-image'] != '':
            self.background_file= self.track_params['background-image']
        else:
            if self.track_params['display-show-background'] == 'yes':
                self.background_file= self.show_params['background-image']
            
        # get background colour from profile.
        if self.track_params['background-colour'] != '':
            self.background_colour= self.track_params['background-colour']
        else:
            self.background_colour= self.show_params['background-colour']
        
        # get animation instructions from profile
        self.animate_begin_text=self.track_params['animate-begin']
        self.animate_end_text=self.track_params['animate-end']


        if not self.testing:
            # create an  instance of showmanager so we can control concurrent shows
            self.show_manager=ShowManager(self.show_id,self.showlist,self.show_params,self.root,self.canvas,self.pp_dir,self.pp_profile,self.pp_home)

        if not self.testing:
            # open the plugin Manager
            self.pim=PluginManager(self.show_id,self.root,self.canvas,self.show_params,self.track_params,self.pp_dir,self.pp_home,self.pp_profile) 

        if not self.testing:
            # create an instance of PPIO so we can create gpio events
            self.ppio = PPIO()

        # initialise state and signals
        self.pause_at_end_required='no' # overriden by videoplayer
        self.tick_timer=None
        self.terminate_signal=False
        self.previous_player=None
        self.play_state=''

              
    # common bits of show(....) 
    def pre_show(self):
        if self.trace: print '    Player/pre-show ',self
        # show_x_content moved to just before ready_callback to improve flicker.

        # but pim needs to be done here as it uses the pp-plugin-content tag which needs to be created later
        self.pim.show_plugin()
        # Control other shows at beginning
        if not self.testing:
            reason,message=self.show_manager.show_control(self.track_params['show-control-begin'])
        else:
            reason='normal'
        if reason in ('error','killed'):
            self.end(reason,message)
            self=None
        else:      

            # create animation events
            if not self.testing:
                reason,message=self.ppio.animate(self.animate_begin_text,id(self))
            else:
                reason='normal'
            if reason  ==  'error':
                self.mon.err(self,message)
                self.end(reason,message)
                self=None
            else:
                # return to start playing the track.
                self.mon.log(self,">show track received from show Id: "+ str(self.show_id))
                return

# *****************
# hide content and end animationtion, end show etc.
# called by ready calback and end
# *****************

    def hide(self):
        if self.trace: print '    Player/hide ',self

        # abort the timer
        if self.tick_timer is not None:
            self.canvas.after_cancel(self.tick_timer)
            self.tick_timer=None
        
        self.hide_x_content()
        
        # stop the plugin
        if not self.testing:
            if self.track_params['plugin'] != '':
                self.pim.stop_plugin()

        # Control concurrent shows at end
        if not self.testing:
            reason,message=self.show_manager.show_control(self.track_params['show-control-end'])
        else:
            reason='normal'
        if reason  == 'error':
            self.mon.err(self,message)
            self.end_callback(reason,message)
            self=None
        else:
            
           # clear events list for this track
            if  not self.testing:
                if self.track_params['animate-clear'] == 'yes':
                    self.ppio.clear_events_list(id(self))
                    
            # create animation events for ending
            if  not self.testing:
                reason,message=self.ppio.animate(self.animate_end_text,id(self))
            else:
                reason='normal'
                
            if reason == 'error':
                self.mon.err(self,message)
                self.end_callback(reason,message)
                self=None
            else:
                return



    def terminate(self,reason):
        if self.trace:  print '    Player/terminate ',self
        self.terminate_signal=True
        if self.play_state in ('showing','pause_at_end'):
            # call the derived class's stop method
            self.stop()


    def get_play_state(self):
        return self.play_state
  
# *****************
# ending the player
# *****************

    def end(self,reason,message):
        if self.trace: print '    Player/end ',self
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
        # load the plugin if required
        if self.track_params['plugin'] != '':
            reason,message,self.track = self.pim.load_plugin(self.track,self.track_params['plugin'],)
            return reason,message

    def load_x_content(self,enable_menu):
        if self.trace: print '    Player/load_x_content ',self
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
                self.mon.err(self,"Trackbackground file not found: "+ background_img_file)
                self.end('error',"Track background file not found")
            else:
                pil_background_img=Image.open(background_img_file)
                # print 'pil_background_img ',pil_background_img
                self.background = ImageTk.PhotoImage(pil_background_img)
                del pil_background_img
                # print 'self.background ',self.background
                self.background_obj = self.canvas.create_image(int(self.canvas['width'])/2,
                                                               int(self.canvas['height'])/2,
                                                               image=self.background,
                                                               anchor=CENTER)
                # print '\nloaded background_obj: ',self.background_obj


            

        # load the track content.  Dummy function below is overridden in players          
        self.load_track_content()
                          
        # load show text if enabled
        if self.show_params['show-text'] !=  '' and self.track_params['display-show-text'] == 'yes':
            self.show_text_obj=self.canvas.create_text(int(self.show_params['show-text-x']),
                                                       int(self.show_params['show-text-y']),
                                                       anchor=NW,
                                                       text=self.show_params['show-text'],
                                                       fill=self.show_params['show-text-colour'],
                                                       font=self.show_params['show-text-font'])


        # load track text if enabled
        if self.track_params['track-text'] !=  '':
            self.track_text_obj=self.canvas.create_text(int(self.track_params['track-text-x']),
                                                        int(self.track_params['track-text-y']),
                                                        anchor=NW,
                                                        text=self.track_params['track-text'],
                                                        fill=self.track_params['track-text-colour'],
                                                        font=self.track_params['track-text-font'])

        # load instructions if enabled
        if enable_menu is  True:
            self.hint_obj=self.canvas.create_text(int(self.show_params['hint-x']),
                                                  int(self.show_params['hint-y']),
                                                  text=self.show_params['hint-text'],
                                                  fill=self.show_params['hint-colour'],
                                                  font=self.show_params['hint-font'],
                                                  anchor=NW)

        self.canvas.tag_raise('pp-click-area')
        self.canvas.itemconfig(self.background_obj,state='hidden')
        self.canvas.itemconfig(self.show_text_obj,state='hidden')
        self.canvas.itemconfig(self.track_text_obj,state='hidden')
        self.canvas.itemconfig(self.hint_obj,state='hidden')
        self.canvas.update_idletasks( )
        return 'normal',''


    # dummy functions to manipulate the track content, overidden in some players,
    # message text in messageplayer
    # image in imageplayer
    # menu stuff in menuplayer
        
    def load_track_content(self):
        pass

    def show_track_content(self):
        pass

    def hide_track_content(self):
        pass

    def show_x_content(self):
        if self.trace: print '    Player/show_x_content ',self
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
        self.canvas.update_idletasks( )       


    def hide_x_content(self):
        if self.trace: print '    Player/hide_x_content ',self
        self.hide_track_content()
        # print 'hide background obj', self.background_obj
        self.canvas.itemconfig(self.background_obj,state='hidden')
        self.canvas.itemconfig(self.show_text_obj,state='hidden')
        self.canvas.itemconfig(self.track_text_obj,state='hidden')
        self.canvas.itemconfig(self.hint_obj,state='hidden')
        self.canvas.update_idletasks( )
        
        self.canvas.delete(self.background_obj)
        self.canvas.delete(self.show_text_obj)
        self.canvas.delete(self.track_text_obj)
        self.canvas.delete(self.hint_obj)
        self.background=None
        self.canvas.update_idletasks( )


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
        self.mon.log(self,"Background image is "+ track_file)
        return track_file
        
    # get a text string from resources.cfg
    def resource(self,section,item):
        value=self.rr.get(section,item)
        if value is False:
            self.mon.err(self, "resource: "+section +': '+ item + " not found" )
            self.end('error','resource not found')
        else:
            return value

