"""
This example writes to the screen directly using Tkinter.

The local time is read and is written direct to the Tkinter canvas that is used by
Pi Presents to display its output.

"""

import time
from Tkinter import NW

class krt_time(object):

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


    def draw(self):
        #  a. draw objects direct to the screen setting their state to 'hidden' so they are not seen until show is called
        #  b. determines whether drawing to the screen should happen repeatedly in the track by calling the redraw method
        #    =0  do not redraw
        #     >0 redraw at intervals (mS.)
        # returns the above value

        # draw objects direct to the screen setting their state to 'hidden' so they are not seen until show is called
        time_text='My Local Time is: ' + time.asctime()

        plugin_obj1=self.canvas.create_text(100,500,
                                        anchor=NW,
                                      text='two objects created by the plugin',
                                      fill='red',
                                      font='arial 20 bold',
                                     state = 'hidden'
                                )
        self.plugin_objects.append(plugin_obj1)
        
        plugin_obj2=self.canvas.create_text(100,600,
                                        anchor=NW,
                                      text=time_text,
                                      fill='green',
                                      font='arial 20 bold',
                                     state = 'hidden'
                                )
        self.plugin_objects.append(plugin_obj2)
        # return the interval to redraw
        return 500


    def show(self):
        # executed at ready_callback to show the plugin objects
        # show any objects that have been loaded
        for plugin_object in self.plugin_objects:
            self.canvas.itemconfig(plugin_object,state='normal')


    def redraw(self):
        # update the text of the second object with the latest time
        time_text='My Local Time is: ' + time.asctime()
        self.canvas.itemconfig(self.plugin_objects[1],text=time_text)
    

    def hide(self):
        # called at ready_callback to delete the previous track's plugin objects
        # this is done on another instance of the plugin
        for plugin_object in self.plugin_objects:
            self.canvas.itemconfig(plugin_object,state='hidden')
            self.canvas.delete(plugin_object)
        # and delete any PIL image files
        for plugin_image in self.plugin_images:
            plugin_image=None
                      
                       
                               

