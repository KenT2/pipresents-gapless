import os
import time
#from datetime import *
from Tkinter import *
import Tkinter
import Image, ImageChops, ImageDraw, ImageFont, ImageFilter
import tkFont
import pp_paths

STATE_NONE   = 0
STATE_LOADED = 1
STATE_DRAWN  = 2
STATE_ACTIVE = 3

class Plugin:
    # support for PP 1.2

    def __init__(self,root,canvas,plugin_params,track_params,show_params,pp_dir,pp_home,pp_profile):
        self.plugin = awk_ticker(root,canvas,plugin_params,track_params,show_params,pp_dir,pp_home,pp_profile)

    def do_plugin(self,track_file):
        error, msg, track_file = self.plugin.load(track_file, '', '')
        self.plugin.show()
        return error, msg, track_file

    def stop_plugin(self):
        self.plugin.stop_plugin()

class awk_ticker(object):

    def __init__(self,root,canvas,plugin_params,track_params,show_params,pp_dir,pp_home,pp_profile):
        # called by PiPresents when starting the first show
        self.state         = STATE_NONE
        self.root          = root
        self.canvas        = canvas
        self.screenwidth   = None
        self.plugin_params = plugin_params
        self.track_params  = track_params
        self.show_params   = show_params
        self.pp_dir        = pp_dir
        self.pp_home       = pp_home
        self.pp_profile    = pp_profile

        self.timer=None
        self.flashed = False
        
        # read params into variables
        self.get_or_default('clear_before_repeat', True)
        self.get_or_default('anim_time',   30)
        self.get_or_default('anim_dx',     5)
        self.get_or_default('font_family', 'Arial')
        self.get_or_default('font_size',   50)
        self.get_or_default('font_weight', 'normal')
        self.get_or_default('fgcolor',     '#FFF')
        self.get_or_default('bgcolor',     '#000')
        self.get_or_default('bgtop',       0)
        self.get_or_default('bgheight',    90)
        self.get_or_default('text_y',      0)
        self.get_or_default('text_x',      100)
        self.get_or_default('text_file',   '')

        # keep track of the Tkinter objects we create
        self.tk_objects=[]
    
        self.font = tkFont.Font(family=self.font_family, size=self.font_size, weight=self.font_weight)
        self.lines = []
        self.formatted = []
        self.widths = []
        self.totallength = 0
        self.text_file = self.plugin_params['text_file']

    def create_object(self, type, *args, **kwargs):
        # for canvas objects
        # draw them hidden and keep a list of them
        #if type == 'font':
        #    tkobj = tkFont.Font(state='hidden', args, kwargs)
        if type == 'line':
            tkobj = self.canvas.create_line(args, kwargs) #, state='hidden')
        elif type == 'text':
            tkobj = self.canvas.create_text(args, kwargs) #, state = 'hidden')
        self.tk_objects.append(tkobj)
        return tkobj

    def destroy_objects(self):
        self.canvas.delete('awk-ticker')
        del self.tk_objects[:]

    # Creates an attribute having the same name as the setting
    # If the setting is found, it is casted to match the type of the default value.
    def get_or_default(self, setting, default):
        value = default
        try:
            if setting in self.plugin_params and not self.plugin_params[setting] == '':
                s = self.plugin_params[setting]
                if isinstance(default, bool):
                    value = s.lower() in ['1', 'yes', 'true']
                else:
                    value = type(default)(s)
        except:
            #print "Exception on setting: " + setting
            pass
        setattr(self, setting, value)
        return value
        
    def read_text_file(self):
        fname = pp_paths.get_file(self.text_file)
        if fname is None:
          print "could not find " + self.text_file
        else:
          with open(fname) as f:
              self.lines = f.readlines()
        # fallback to date/time if the file is empty
        if len(self.lines) == 0:
            self.lines.append("{date} at {time}")
    
    def measure_lines(self):
        self.totallength = 0
        for line in self.lines:
            text = self.format_text(line)
            self.formatted.append(text)
            width = self.font.measure(text)
            self.widths.append(width)
            self.totallength += width + self.text_x

    def format_text(self, text):
        #text = text.replace("{time}", time.strftime('%I:%M:%S'))
        text = text.replace("{time}", time.strftime('%I:%M'))
        text = text.replace("{date}", time.strftime('%a %b %d'))
        return text
 
    def load(self, track_file, liveshow, track_type):
        # Called while previous track is being shown
        self.read_text_file()
        self.measure_lines()
        self.state = STATE_LOADED
        return 'normal', '', track_file
    
    def show(self):
        if self.state < STATE_DRAWN:
            self.draw()
        # executed at ready_callback to show the plugin objects
        # show any objects that have been loaded
        self.draw()
        for plugin_object in self.tk_objects:
            self.canvas.itemconfig(plugin_object,state='normal')

    def draw(self):
        if self.state < STATE_LOADED:
            self.load('', '', '')
        if len(self.lines) == 0:
            return
        # draw objects to the screen (hidden state, until show() is called)
        if not self.canvas is None and self.screenwidth is None:
        #kick off the function to ticker drawing
            self.screenwidth = self.canvas.winfo_screenwidth()
        self.xtick = self.screenwidth
        self.timer = self.canvas.after(self.anim_time, self.draw_tick)
            self.state = STATE_DRAWN
            #self.init_timer.cancel()
            
        # return the interval for redraw (0 = none)
        return 0
        
    def redraw(self):
        if self.state < STATE_DRAWN:
            self.draw()
        self.draw_tick

    def draw_tick(self):
        if self.state < STATE_DRAWN:
            self.draw()
        self.destroy_objects()
        # draw tape background
        top = self.bgtop + (self.bgheight / 2)
        self.create_object('line', 0, top, self.screenwidth, top,
            width=self.bgheight, fill=self.bgcolor, tag=('awk-ticker','pp-content'))
        self.draw_texts()
        self.xtick = self.xtick - self.anim_dx
        # reset such there is a smooth wrap-around from the last text to the first
        if self.xtick + self.totallength <= 0:
            if self.clear_before_repeat:
                self.xtick = self.screenwidth
            else:
                self.xtick += self.totallength
        self.timer=self.canvas.after(self.anim_time, self.draw_tick)

    def draw_texts(self):
        i = 0
        x = self.xtick
        # fill up available space on the bar. 
        # start over at the first text if there is still room after printing everything.
        while self.lines:
            for text in self.lines:
                text = self.format_text(self.lines[i])
                if text != self.lines[i] and text != self.formatted[i]:
                    if text != self.formatted[i]:
                        diff = self.font.measure(self.formatted[i]) - self.font.measure(text)
                    else:
                        diff = self.font.measure(self.lines[i]) - self.font.measure(text)
                    self.widths[i] -= diff
                    self.totallength -= diff
                    self.formatted[i] = text
                self.create_object('text', x, self.bgtop + self.text_y, text=text, 
                    font=self.font, fill=self.fgcolor, 
                    anchor='nw', tag=('awk-ticker','pp-content'))
                x += self.widths[i] + self.text_x
                i += 1
                if i >= len(self.widths): 
                    if self.clear_before_repeat:
                        return
                    i = 0
                if x >= self.screenwidth: 
                    return

    def hide(self):
        # called at ready_callback to delete the previous track's plugin objects
        # this is done on another instance of the plugin
        for tk_object in self.tk_objects:
            self.canvas.itemconfig(tk_object,state='hidden')
            #self.canvas.delete(plugin_object)

    def stop_plugin(self):
        # gets called by Pi Presents at the end of the presentation
        #stop the timer
        if self.timer<>None:
            self.canvas.after_cancel(self.timer)
        pass
