"""
ACKNOWLEDGEMENTS 
-----------------------------------
The idea for plugins came from 2-sidedtoast on the Raspberry Pi forum
His original module at code.google.com/p/python-weather-images/ used a program separate from
Pi Presents and initiated by Cron to write the image to the liveshow directory.

I have integrated his idea into Pi Presents such that you can call a plugin from imageplayer, videoplayer, audioplayer, messageplayer  and browserplayer.
Plugins work for all types of show but Liveshows and Artliveshows need special treatment.

API
----
All track plugins must be present in /pipresents/pp_track_plugins. Plugins are organised as Python Classes.
The class name must be identical to the name of the file that contains it (without .py)
The plugin to be used by a track is specified in the xxxxx.cfg file. The path of the plugin file is in the Plugin Config File parameter of a track.

Each instance of a Player creates an instance of a Plugin which calls __init__  The plugin class must have the methods
  __init__, load, show, redraw, and hide.

__init__(....)

  __init__ creates an instance of the plugin class and allows the context to be passed to the plugin.
  Most of the arguments are unlikely to be used. You can initialise your own state variables in __init__.
-----------------
Arguments of __init__ :
    root -
    the top level window - not of great use to a track plugin.
    
    canvas -
    the Tkinter canvas on which all displayed output of the Player is written. A plugin could write to the canvas directly and return the provided file path (see krt_time.py)
    
    plugin_params -
    dictionary of the parameters defined in the plugin configuration file that called this plugin
    e.g. plugin_params['line2'] will return 'text added from cfg file' for this example.
    
    show_params -
    dictionary of show parameters, definitions in /pipresents/pp_definitions.py.
    
    track_params -
    dictionary of track parameters, definitions in /pipresents/pp_definitions.py
    
    pp_dir -
    path of pipresents directory
    
    pp_home -
    path of data home directory
    
    pp_profile -
    path of profile directory


load
------
  Code that determines or modifies the track file to be played must be in the method load 

        load(self,track_file,liveshow,type).

  load is executed when a track is loaded, which may be some time before it is shown.
  The main purpose of the method is to modify a, or provide an alternative, track file.
  
  load has the following arguments:

    a. liveshow

    False if the plugin is called from any othr type of show. These shows have medilaist and track_file and type are provided by the track entry in the medialist and 
    
    True if the plugin has been called from a liveshow or artliveshow. If called from a liveshow the track_file parameter contains rubbish
    and the type paramter is obtained from the .cfg file that specified the plugin. This is because the plugin is
    the track, not associated with another type of track. If liveshow is True the load method must return the track file (see below)

    b. type
    The type of track, this determines the player that will play the track. Currently audio, video, image, web, message
    

    c. track_file

    If the plugin is called from within a liveshow or artliveshow then this will be rubbish

    If the plugin is called from any other type of show then:
    
    For type='message' - the argument contains the message text that would be  displayed.

    For all other players - The full path of the file specified in the Location field of the profile entry for this track. For audio this may be blank.

    Note: The track file/message eventually used will be that whose path is returned by the plugin.

 load returns a tuple: status,message, filepath

    1. status -
    'normal','error'.  Return 'normal' if OK. 'error' is for fatal errors and will cause Pi Presents to exit after displaying the message.
    The plugin should deal nicely with non-fatal errors, like temporary loss of the internet connection, and return status='normal'
    
    2. message -
    an error message for status='error'
    
    3. filepath -
    Full path of the track file to  be used by the player or the message text. Blank if no file is to be played, where this is allowed by the player (audio only at present.
    The type of file specified should be compatible with the underlying player (omxplayer etc.)
    So if you wantjust |Tkinter drawing use an audio track

show(self)
-----------

    show() allows user code to  draw on the screen (canvas) while the track is showing. Drawing is by use of Tkinter canvas objects.

    The objects are drawn after other elements of the track are displayed so appear on top. They are displayed immeadiately so their state should be set to normal.

    The method must return redraw interval  which is the time in milliseconds after which the redraw method is repetively called.
    If redraw is not to be called then redraw interval should be 0

    for more detail see krt_time.py


redraw(self)
---------------
   redraw allows Tkinter canvas objects created in draw to be updated.
   
 hide(self)
 -------------
    The plugin code must  have the method  hide(self)
    It is executed at the end of a track when the display of the track ends.
    The method must hide then delete any Tkinter canvas objects created by the plugin
    It should also be used to delete any temporary files.
    Note: This method is executed after the show method for the next track. This should not matter as each track has its own instance of a plugin.


EXAMPLE
-------------
An example follows. It demonstrates the principles and is very long as it addresses all show and track type combinations.
Usually a plugin will be written for a single track type. krt_time.py and krt_image_text.py are shorter examples demonstrating file modification  and drawing .
"""

import os
import time
from Tkinter import NW
from PIL import Image, ImageDraw, ImageFont

# the class must have the same name as the file without .py
class pp_example_plugin(object):

    # it must have an __init__ with these arguments
    def __init__(self,root,canvas,plugin_params,track_params,show_params,pp_dir,pp_home,pp_profile):
        self.root=root      # Tkinter root
        self.canvas=canvas    # the canvas onto which Tkinter objects are written. Beware the canvas origin is the top left corner of the show canvas but is not clipped by the bottom right corner
        self.plugin_params=plugin_params   # as provided in plginxxx.cfg
        self.track_params=track_params  # track parameters (not for liveshows)
        self.show_params=show_params # show paramters
        self.pp_dir=pp_dir   # path to pi presents code directory
        self.pp_home=pp_home    # path to pi presents home 
        self.pp_profile=pp_profile  #path to current profile

        ##    print pp_dir
        ##    print pp_home
        ##    print pp_profile
        ##    print show_params['show-ref']
        ##    print track_params['type']




    def load(self,track_file,liveshow,track_type):

        self.liveshow=liveshow
        self.track_type=track_type
        # print 'track file' ,track_file
        # print 'liveshow',self.liveshow
        # print 'track type',self.track_type

        #initialise instance variables
        # make it an instance variable as it will be used in another method of the instance
        self.modified_file=''

        # was the player called from a liveshow?
        # if plugin is called in a liveshow then a track file will not be provided so get one from somewhere
        if self.liveshow==True:
            # liveshows have a limited number of track types image, video, audio. Plugins can add message to liveshows
            if self.track_type=='image':
                self.modified_file= self.pp_home + os.sep + 'media' + os.sep + 'space.jpg'
                # check it exists and return a fatal error if not.
                if not os.path.exists(self.modified_file):
                    return 'error','file not found by plugin: ' + self.plugin_params['plugin']+ ' ' +self.modified_file,''
                
            elif self.track_type=='video':
                self.modified_file=self.pp_home + os.sep + 'media' + os.sep + 'xthresh.mp4'
                # check it exists and return a fatal error if not.
                if not os.path.exists(self.modified_file):
                    return 'error','file not found by plugin: ' + self.plugin_params['plugin']+ ' ' + self.modified_file,''

            elif self.track_type=='audio':
                self.modified_file=self.pp_home + os.sep + 'media' + os.sep + '01.mp3'
                # for audio self.modified_file = '' is permissible
                # check it exists and return a fatal error if not.
                if not os.path.exists(self.modified_file):
                    return 'error','file not found by plugin: ' + self.plugin_params['plugin']+ ' ' +self.modified_file,''

            elif self.track_type=='message':
                self.modified_file='message text generated by plugin'
                
            else:
                return 'error',self.plugin_params['type']+ ' not a file type for a liveshow: ' + self.plugin_params['plugin'],''

        else:
            # liveshow is false so modify the provided track or provide an alternative track file
            if self.track_type=='image':
                self.modified_file='/tmp/krt_file.jpg'
                img = Image.open(track_file)
                # modify the image by adding some text using PIL
                usrfont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 30)
                tcolor=(0,0,0)
                draw = ImageDraw.Draw(img)
                text1 = 'This text added by the plugin. The first line taken from the plugin code'
                # get second line from the plugin parameters
                text2 = self.plugin_params['line2']
                draw.text((100,150),text1,fill=tcolor,font=usrfont)
                draw.text((100,200),text2,fill=tcolor,font=usrfont)
                # delete the temporary structure to ensure no memory leak
                del draw
                img.save(self.modified_file)
                # delete the temporary structure to ensure no memory leak
                del img

            elif self.track_type=='message':
                # change the provided text
                self.modified_file='the message text has been modified by the plugin'

            elif self.track_type=='video':
                # just pass it through because I do not know how to modifiy a video file!
                self.modified_file=track_file

            elif self.track_type=='audio':
                # audio allows blank tracks so lets play nothing
                self.modified_file=''

            elif self.track_type=='web':
                # let's try a different url
                self.modified_file='http://www.facebook.com'
                
            else:
                return 'error','not a file type for non-liveshow: ' + self.plugin_params['plugin'],''

        #  print 'modified track file is',self.modified_file
        # and return the file you want displayed
        return 'normal','',self.modified_file



    def show(self):

        # make a text string and write it to the Tkinter canvas.
        time_text='My Local Time is: ' + time.asctime()

        # assign the object to an instance variable so we can modify and hide it later
        self.plugin_object = self.canvas.create_text(100,100,
                                      anchor=NW,
                                      text=time_text,
                                      fill='white',
                                      font='arial 20 bold',
                                        state='normal'
                                )
        # and redraw after 500mS.
        return 500
        

    def redraw(self):
        # update the text object with the latest time
        time_text='My Local Time is: ' + time.asctime()
        self.canvas.itemconfig(self.plugin_object,text=time_text)


    def hide(self):
        # called at the end of the track
        # hide and delete the Tkinter canvas objects
        self.canvas.itemconfig(self.plugin_object,state='hidden')
        self.canvas.delete(self.plugin_object)
        
        # delete the file created when modifying the image as it is no longer of use.
        if self.track_type=='image' and self.liveshow==False:
            os.remove(self.modified_file)
        
