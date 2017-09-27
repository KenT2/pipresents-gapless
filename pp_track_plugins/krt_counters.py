"""
This example writes values of counters to the screen directly using Tkinter.

The counters are written direct to the Tkinter canvas that is used by
Pi Presents to display its output.

There is also an example of how to send debugging text to the terminal window.

"""
# ------ load the counter manager module
from pp_countermanager import CounterManager

import time
from Tkinter import NW

class krt_counters(object):

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

        # ------ Make an instance of CounterManager
        self.cm=CounterManager()


    def load(self,track_file,liveshow,track_type):
        # Called in advance, while the previous track is being shown (frozen) as track loading can take a while.
        # Use load to modify the track file or track file name that is about to be loaded
        # must return the track file whether modified, replaced  or unaltered
        # return 'normal' if no error encountered, otherwise return 'error'
        return 'normal','',track_file



        #  called before show_control_begin so can be used to draw anything but counters.

        # in load() draw objects direct to the canvas setting their state to 'hidden' so they are not seen until show is called  

    def show(self):

        #  Draw objects direct to the screen setting their state
        #  to 'normal' so they are dislayed
        #
        #  Determine whether drawing to the screen should happen repeatedly
        #  in the track by calling the redraw method
        #   = 0  do not redraw
        #   > 0 redraw at intervals (mS.)
        #  return the above value

        # ------ get the value of counter 'fred' using get_counter() function
        # ------ status is 'error' if counter does not exist, value_text contains an error message
        status,value=self.cm.get_counter('fred')
        
        my_text= 'Value of fred using get_counter '+ value
        plugin_obj1=self.canvas.create_text(100,200,
                                        anchor=NW,
                                      text=my_text,
                                      fill='red',
                                      font='arial 20 bold',
                                     state = 'normal'
                                )
        self.plugin_objects.append(plugin_obj1)
        

        my_text= 'All counter value from str_counters\n'+ self.cm.str_counters()        

        plugin_obj2=self.canvas.create_text(100,300,
                                        anchor=NW,
                                      text=my_text,
                                      fill='green',
                                      font='arial 20 bold',
                                     state = 'normal'
                                )
        self.plugin_objects.append(plugin_obj2)


        my_text= 'print_counters is used \nto print the value of all counters \nto the terminal window'     

        plugin_obj3=self.canvas.create_text(100,420,
                                        anchor=NW,
                                      text=my_text,
                                      fill='yellow',
                                      font='arial 20 bold',
                                     state = 'normal'
                                )
        self.plugin_objects.append(plugin_obj3)

        self.cm.print_counters()
        

        # return the interval to redraw, zero if redraw is not required.
        return 0

    def redraw(self):
        pass
    

    def hide(self):
        # called to delete the previous track's plugin objects
        for plugin_object in self.plugin_objects:
            self.canvas.itemconfig(plugin_object,state='hidden')
            self.canvas.delete(plugin_object)
        # and delete any PIL image files
        for plugin_image in self.plugin_images:
            plugin_image=None

                      
                       
                               

