"""
This example writes to the screen directly using Tkinter.

The local time is read and is written direct to the Tkinter canvas that is used by
Pi Presents to display its output.

"""

import time
from Tkinter import NW
import urllib2,re


class krt_time(object):

    def __init__(self,root,canvas,plugin_params,track_params,show_params,pp_dir,pp_home,pp_profile):
        self.root=root
        self.canvas=canvas
        self.plugin_params=plugin_params
        self.track_params=track_params
        self.show_params=show_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile


    def load(self,track_file,liveshow,track_type):
        self.track_file=track_file
        # dummy just return whatever was supplied and kick off drawing
        return 'normal','',self.track_file,5000

    def show(self):
        pass


    def draw(self):
        
        time_text='My Local Time is: ' + time.asctime()

        # pp-plugin-content tag ensures that Pi Presents deletes the text at the end of the track
        # it must be inclued
        self.canvas.create_text(100,500,
                                        anchor=NW,
                                      text=time_text,
                                      fill='white',
                                      font='arial 20 bold',
                                        tag=('pp-plugin-content'),
                                state='normal'
                                )
         
    def hide(self):
        # called at the end of the track, nothing to do
        pass



