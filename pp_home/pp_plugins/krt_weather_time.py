"""
The track file is modified saved and returned to be displayed

In addition the local time is read and is written direct to the Tkinter canvas that is used by
Pi Presents to display its output.

"""

import os
import time
from Tkinter import *
import Tkinter
import urllib,urllib2,re
from PIL import Image, ImageDraw, ImageFont

class krt_weather_time:

    def __init__(self,root,canvas,plugin_params,track_params,show_params,pp_dir,pp_home,pp_profile):
        self.root=root
        self.canvas=canvas
        self.plugin_params=plugin_params
        self.track_params=track_params
        self.show_params=show_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        self.used_file=''



    def load(self,track_file,liveshow,track_type):

        self.track_file=track_file
        self.liveshow=liveshow

        ##    print self.track_file
        ##    print self.liveshow
        
        # if plugin is called in a liveshow then  a track file will not be provided so need to get one from somewhere else or create one
        if self.liveshow==True: 
            self.track_file='/home/pi/pp_home/media/river.jpg'
            self.img = Image.open(self.track_file)
        else:
            # can use the file from track_params, but don't have to
            self.img = Image.open(self.track_file)
            

        # define path of the temporary file to take the output of plugin.
        self.used_file='/tmp/weather_time_ny.jpg'


        #create the weather image in used_file
        self.load_weather()


        #and return the image modified with draw_weather, kicking off drawing to the canvas
        return 'normal','',self.used_file,5000

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
        # called at the end of the track
        # delete the temporary file
        if self.used_file<>'':
            os.remove(self.used_file)

            

    def load_weather(self):

        usrfont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 30)
        tcolor=(0,0,0)
        
        # use the track file specified in the profile as the base of the weather report
        draw = ImageDraw.Draw(self.img)

        #use the zip code specified in the plugin configuraton file
        url='http://www.weather.com/weather/today/'+self.plugin_params['zip']
        
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
        try:
            response = urllib2.urlopen(req,timeout=5)
         
        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                text =  'The server could not fulfill the request. ' + str(e.code)
                draw.text((100,150),text,fill=tcolor,font=usrfont)
                self.img.save(self.used_file)
                
            elif hasattr(e, 'reason'):
                text =  'We failed to reach a server. ' + str(e.reason)
                draw.text((100,150),text,fill=tcolor,font=usrfont)
                self.img.save(self.used_file)
        else:
            # everything is fine
            link=response.read()
            response.close

            match2 = re.compile('<span itemprop="feels-like-temperature-fahrenheit">(.+?)</span>').findall(link)
            match3 = re.compile('<div class="wx-wind-label">(.+?)</div>').findall(link)
            match4 = re.compile('<div class="wx-phrase ">(.+?)</div>').findall(link)

            text2 = self.plugin_params['place']+", Current Temperature = " + match2[0]
            text3 = match4[0] + " with winds " + match3[0]
            draw.text((100,150),text2,fill=tcolor,font=usrfont)
            draw.text((100,200),text3,fill=tcolor,font=usrfont)

            del draw
            self.img.save(self.used_file)
            del self.img



