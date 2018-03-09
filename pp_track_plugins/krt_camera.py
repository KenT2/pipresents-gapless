"""
This example does a camera preview and, when the Down is pressed cappture the image to a file
and writes to the screen directly using Tkinter.

The local time is read and is written direct to the Tkinter canvas that is used by
Pi Presents to display its output.

"""
from picamera import PiCamera
import time
from Tkinter import NW

class krt_camera(object):

    def __init__(self,root,canvas,plugin_params,track_params,show_params,pp_dir,pp_home,pp_profile):
        # called when a player is executed for a track
        self.root=root
        self.canvas=canvas
        self.plugin_params=plugin_params
        self.track_params=track_params
        self.show_params=show_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        # plugin must keep track of the Tkinter objects it creates.
        self.plugin_objects=[]
        # plugin must keep track of the PIL image files it creates
        self.plugin_images=[]


    def load(self,track_file,liveshow,track_type):
        # Called in advance, while the previous track is being shown.
        # called after all other track objects are loaded so these objects appear on top
        # Can do three things:
        # a. modify the track file or track file name that is about to be  loaded
        #   must return the track file whether modified, replaced  or unaltered
        # return 'normal' if no error encountered, otherwise return 'error'
        return 'normal','',track_file



    def show(self):
        #  Draw objects direct to the screen setting their state
        #  to 'normal' so they are dislayed
        #
        #  Determine whether drawing to the screen should happen repeatedly
        #  in the track by calling the redraw method
        #   = 0  do not redraw
        #   > 0 redraw at intervals (mS.)
        #  return the above value

        time_text='My Local Time is: ' + time.asctime()

        plugin_obj1=self.canvas.create_text(100,500,
                                        anchor=NW,
                                      text='Press Down Cursor to take Photo',
                                      fill='red',
                                      font='arial 20 bold',
                                     state = 'normal'
                                )
        self.plugin_objects.append(plugin_obj1)

        plugin_obj3=self.canvas.create_text(250,250,
                                        anchor=NW,
                                      text='Camera Warming Up',
                                      fill='red',
                                      font='arial 20 bold',
                                     state = 'normal'
                                )
        self.plugin_objects.append(plugin_obj3)
        
        plugin_obj2=self.canvas.create_text(100,600,
                                        anchor=NW,
                                      text=time_text,
                                      fill='green',
                                      font='arial 20 bold',
                                     state = 'normal'
                                )
        self.plugin_objects.append(plugin_obj2)

        # inittialise the camera and allow time for it to warm up
        # looks like 500mS is adequate so set count to 0
        self.warm_up_count=0
        self.preview_started=False
        self.cam = PiCamera()        
        # return the interval to redraw
        return 500


    def redraw(self):
        # update the text of the second object with the latest time
        time_text= time.asctime()
        self.canvas.itemconfig(self.plugin_objects[2],text=time_text)

        while self.warm_up_count >0 or self.preview_started is True:
            self.warm_up_count -=1
            return
        x0 = int(self.plugin_params['x0'])
        y0 = int(self.plugin_params['y0'])
        width = int(self.plugin_params['width'])
        height = int(self.plugin_params['height'])
        self.cam.start_preview(fullscreen=False, window = (x0, y0, width, height))
        self.preview_started=True
        
    

    def hide(self):
        # capture the image to the profile media file
        self.cam.stop_preview()
        self.cam.capture(self.pp_profile+'/media/myphoto.jpg')
        self.cam.close()
        
        # called at ready_callback to delete the previous track's plugin objects
        # this is done on another instance of the plugin
        for plugin_object in self.plugin_objects:
            self.canvas.itemconfig(plugin_object,state='hidden')
            self.canvas.delete(plugin_object)
            
        # and delete any PIL image files
        for plugin_image in self.plugin_images:
            plugin_image=None
                      
                       
                               

