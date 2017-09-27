"""
The track file is modified saved and returned to be displayed

"""

import os
from PIL import Image, ImageDraw, ImageFont

class krt_image_text(object):

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
        self.liveshow=liveshow
  
        # if plugin is called in a liveshow then  a track file will not be provided so need to get one from somewhere else or create one
        if self.liveshow==True: 
            self.track_file='/home/pi/pp_home/media/river.jpg'
            self.img = Image.open(self.track_file)
        else:
            # can use the file from track_params, but don't have to
            self.img = Image.open(self.track_file)
            
        # define path of the temporary file to take the output of plugin.
        self.used_file='/tmp/image_time_ny.jpg'

        #create the weather image in used_file
        self.overlay_text()

        #and return the image modified
        return 'normal','',self.used_file
 

    def show(self):
        # nothing to redraw so set redraw time to 0
        return 0

    def redraw(self):
        pass

         
    def hide(self):
        # delete the temporary file
        if self.used_file !='':
            os.remove(self.used_file)

            

    def overlay_text(self):

        usrfont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 30)
        tcolor=(255,0,0)
        
        # use the track file specified in the profile as the base of the weather report
        draw = ImageDraw.Draw(self.img)

        #get text from plugin configuraton file
        text = self.plugin_params['text']
        draw.text((100,150),text,fill=tcolor,font=usrfont)
        del draw
        self.img.save(self.used_file)
        del self.img



