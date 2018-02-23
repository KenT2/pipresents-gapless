"""
This example writes values of the automation HAT analog input 1 to the screen directly using Tkinter.

The values are written direct to the Tkinter canvas that is used by
Pi Presents to display its output.

There is also an example of how to send debugging text to the terminal window.

"""
# ------ load the i2c driver class from the I/O plugin module
from pp_iopluginmanager import IOPluginManager
from pp_i2cdriver import pp_i2cdriver

import time
from Tkinter import NW

class krt_i2cinputs(object):

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

        # ------ Make an instance of i2cdriver
        self.pm=IOPluginManager()
        self.i2c=pp_i2cdriver()


    def load(self,track_file,liveshow,track_type):
        #  called before show_control_begin so can be used to draw anything but counters.
        
        # in load() draw objects direct to the canvas setting their state to 'hidden' so they are not seen until show is called  
        # Called in advance, while the previous track is being shown (frozen) as track loading can take a while.
        # Use load to modify the track file or track file name that is about to be loaded
        # must return the track file whether modified, replaced  or unaltered
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

        found,value=self.pm.get_input('analog1-volts')
        if found is True:
            value = str(round(value,3))
        else:
            value = 'Not available'

        my_text= 'Voltage on Analog Input 1 \n read every 100mS       '+ value
        plugin_obj1=self.canvas.create_text(100,200,
                                        anchor=NW,
                                      text=my_text,
                                      fill='white',
                                      font='arial 20 bold',
                                     state = 'normal'
                                )
        self.plugin_objects.append(plugin_obj1)
        

        my_text= 'print_inputs is used \n to print the value of all analog inputs \n to the terminal window \n at the beginning of the track'     

        plugin_obj3=self.canvas.create_text(100,420,
                                        anchor=NW,
                                      text=my_text,
                                      fill='yellow',
                                      font='arial 20 bold',
                                     state = 'normal'
                                )
        self.plugin_objects.append(plugin_obj3)

        # print the analog values to the terminal window
        # need to access the plugin directly, noot via pluginmanager
        self.i2c.print_inputs()
        

        # return the interval to redraw, zero if redraw is not required.
        return 100


    def redraw(self):

        found,value=self.pm.get_input('analog1-volts')
        if found is True:
            value = str(round(value,3))
        else:
            value = 'Not available'
        my_text= 'Voltage on Analog Input 1 \n read every 100mS       '+ value
        self.canvas.itemconfig(self.plugin_objects[0],text=my_text)
    

    def hide(self):
        # called to delete the previous track's plugin objects
        for plugin_object in self.plugin_objects:
            self.canvas.itemconfig(plugin_object,state='hidden')
            self.canvas.delete(plugin_object)
        # and delete any PIL image files
        for plugin_image in self.plugin_images:
            plugin_image=None

                      
                       
                               

