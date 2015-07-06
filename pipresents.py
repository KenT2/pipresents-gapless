#! /usr/bin/env python

"""
Pi Presents is a toolkit for construcing and deploying multimedia interactive presentations
on the Raspberry Pi.
It is aimed at primarily at  musems, exhibitions and galleries
but has many other applications including digital signage

Version 1.3 [pipresents-gapless]
Copyright 2012/2013/2014, Ken Thompson
See github for licence conditions
See manual.pdf for instructions.
"""
import os
import sys
import signal
from subprocess import call
import time
from subprocess import Popen, PIPE


from pp_options import command_options
from pp_showlist import ShowList
from pp_validate import Validator
from pp_showmanager import ShowManager
from pp_screendriver import ScreenDriver
from pp_timeofday import TimeOfDay
from pp_kbddriver import KbdDriver
from pp_utils import Monitor
from pp_utils import StopWatch
from pp_animate import Animate
from pp_gpiodriver import GPIODriver
from pp_oscdriver import OSCDriver


class PiPresents(object):

    def __init__(self):
        gc.set_debug(gc.DEBUG_UNCOLLECTABLE|gc.DEBUG_INSTANCES|gc.DEBUG_OBJECTS|gc.DEBUG_SAVEALL)
        self.pipresents_issue="1.3"
        self.pipresents_minorissue = '1.3.1d'
        # position and size of window without -f command line option
        self.nonfull_window_width = 0.45 # proportion of width
        self.nonfull_window_height= 0.7 # proportion of height
        self.nonfull_window_x = 0 # position of top left corner
        self.nonfull_window_y=0   # position of top left corner
        self.pp_background='black'

        StopWatch.global_enable=False

        # set up the handler for SIGTERM
        signal.signal(signal.SIGTERM,self.handle_sigterm)
        

# ****************************************
# Initialisation
# ***************************************
        # get command line options
        self.options=command_options()

        # get Pi Presents code directory
        pp_dir=sys.path[0]
        self.pp_dir=pp_dir
        
        if not os.path.exists(pp_dir+"/pipresents.py"):
            tkMessageBox.showwarning("Pi Presents","Bad Application Directory")
            exit()

        
        # Initialise logging and tracing
        Monitor.log_path=pp_dir
        self.mon=Monitor()
        # Init in PiPresents only
        self.mon.init()

        # uncomment to enable control of logging from within a class
        # Monitor.enable_in_code = True # enables control of log level in the code for a class  - self.mon.set_log_level()
        
        # make a shorter list to log/trace only some classes without using enable_in_code.
        Monitor.classes  = ['PiPresents',
                            
                            'HyperlinkShow','RadioButtonShow','ArtLiveShow','ArtMediaShow','MediaShow','LiveShow','MenuShow',
                            'GapShow','Show','ArtShow',
                            'AudioPlayer','BrowserPlayer','ImagePlayer','MenuPlayer','MessagePlayer','VideoPlayer','Player',
                            'MediaList','LiveList','ShowList',
                            'PathManager','ControlsManager','ShowManager','PluginManager',
                            'MplayerDriver','OMXDriver','UZBLDriver',
                            'KbdDriver','GPIODriver','TimeOfDay','ScreenDriver','Animate','OSCDriver'
                            ]

        # Monitor.classes=['PiPresents','ArtMediaShow','VideoPlayer','OMXDriver']
        
        # get global log level from command line
        Monitor.log_level = int(self.options['debug'])
        
        self.mon.newline(3)    
        self.mon.log (self, "Pi Presents is starting, Version:"+self.pipresents_minorissue)
        # self.mon.log (self," OS and separator:" + os.name +'  ' + os.sep)
        self.mon.log(self,"sys.path[0] -  location of code: "+sys.path[0])
        if os.geteuid() !=0:
            user=os.getenv('USER')
        else:
            user = os.getenv('SUDO_USER')
        self.mon.log(self,'User is: '+ user)
        # self.mon.log(self,"os.getenv('HOME') -  user home directory (not used): " + os.getenv('HOME')) # does not work
        # self.mon.log(self,"os.path.expanduser('~') -  user home directory: " + os.path.expanduser('~'))   # does not work

        # optional other classes used
        self.root=None
        self.ppio=None
        self.tod=None
        self.animate=None
        self.gpiodriver=None
        self.oscdriver=None
        self.osc_enabled=False
        self.gpio_enabled=False
        self.tod_enabled=False
         
        # get profile path from -p option
        if self.options['profile'] != '':
            self.pp_profile_path="/pp_profiles/"+self.options['profile']
        else:
            self.pp_profile_path = "/pp_profiles/pp_profile"
        
       # get directory containing pp_home from the command,
        # if no home dir is given, default to /home/pi/pp_home
        # if a home dir is given, try:
        #   a) the given home dir
        #   b) a 'pp_home' dir within the given home dir (original PP operation)
        if self.options['home']  == "":
            home    = ""
            home_pp = os.path.expanduser('~')+ os.sep+"pp_home"
        else:
            home    = self.options['home']
            home_pp = self.options['home'] + os.sep + "pp_home"
        self.mon.log(self,"PP home directory is: " + home + "[" + os.sep + "pp_home]")

        # check if pp_home exists.
        # try for 10 seconds to allow usb stick to automount
        # fall back to pipresents/pp_home
        self.pp_home=pp_dir+"/pp_home"
        found=False
        for i in range (1, 10):
            if os.path.exists(home_pp):
                found=True
                self.pp_home=home_pp
                break
            if os.path.exists(home):
                if os.path.exists(home + os.sep + "pp_profiles"):
                  found=True
                  self.pp_home=home
                  break
                self.mon.log(self,"Found the home directory, but no subdirectory pp_home or pp_pprofiles at: {0}".format(home, i))
                break  # if we found the parent dir, the media is mounted... retries are not going to fix a missing sub dir
            self.mon.log(self,"Did not find PP home with {0}pp_home at: {1} ({2} of 10)".format(os.sep, home_pp, i))
            self.mon.log(self,"Did not find PP home with {0}pp_profiles at: {1} ({2} of 10)".format(os.sep, home, i))
            time.sleep (1)
        if found==True:
            self.mon.log(self,"Found requested home directory, using: " + self.pp_home)
        else:
            self.mon.err(self,"Failed to find pp_home directory at " + home)
            self.end('error','Failed to find pp_home')


        # check profile exists
        self.pp_profile=self.pp_home+self.pp_profile_path
        if os.path.exists(self.pp_profile):
            self.mon.log(self,"Found Requested profile - pp_profile directory is: " + self.pp_profile)
        else:
            self.mon.err(self,"Failed to find requested profile: "+ self.pp_profile)
            self.end('error','Failed to find profile')
        
        if self.options['verify'] is True:
            val =Validator()
            if  val.validate_profile(None,pp_dir,self.pp_home,self.pp_profile,self.pipresents_issue,False) is  False:
                self.mon.err(self,"Validation Failed")
                self.end('error','Validation Failed')

         
        # initialise and read the showlist in the profile
        self.showlist=ShowList()
        self.showlist_file= self.pp_profile+ "/pp_showlist.json"
        if os.path.exists(self.showlist_file):
            self.showlist.open_json(self.showlist_file)
        else:
            self.mon.err(self,"showlist not found at "+self.showlist_file)
            self.end('error','showlist not found')

        # check profile and Pi Presents issues are compatible
        if float(self.showlist.sissue()) != float(self.pipresents_issue):
            self.mon.err(self,"Version of profile " + self.showlist.sissue() + " is not  same as Pi Presents, must exit")
            self.end('error','wrong version of profile')


        # get the 'start' show from the showlist
        index = self.showlist.index_of_show('start')
        if index >=0:
            self.showlist.select(index)
            self.starter_show=self.showlist.selected_show()
        else:
            self.mon.err(self,"Show [start] not found in showlist")
            self.end('error','start show not found')

        if self.starter_show['start-show']=='':
             self.mon.warn(self,"No Start Shows in Start Show")       

# ********************
# SET UP THE GUI
# ********************
        # turn off the screenblanking and saver
        if self.options['noblank'] is True:
            call(["xset","s", "off"])
            call(["xset","s", "-dpms"])

        self.root=Tk()   
       
        self.title='Pi Presents - '+ self.pp_profile
        self.icon_text= 'Pi Presents'
        self.root.title(self.title)
        self.root.iconname(self.icon_text)
        self.root.config(bg=self.pp_background)

        self.mon.log(self, 'native screen dimensions are ' + str(self.root.winfo_screenwidth()) + ' x ' + str(self.root.winfo_screenheight()) + ' pixcels')
        if self.options['screensize'] =='':        
            self.screen_width = self.root.winfo_screenwidth()
            self.screen_height = self.root.winfo_screenheight()
        else:
            reason,message,self.screen_width,self.screen_height=self.parse_screen(self.options['screensize'])
            if reason =='error':
                self.mon.err(self,message)
                self.end('error',message)

        self.mon.log(self, 'commanded screen dimensions are ' + str(self.screen_width) + ' x ' + str(self.screen_height) + ' pixcels')
       
        # set window dimensions and decorations
        if self.options['fullscreen'] is False:
            self.window_width=int(self.root.winfo_screenwidth()*self.nonfull_window_width)
            self.window_height=int(self.root.winfo_screenheight()*self.nonfull_window_height)
            self.window_x=self.nonfull_window_x
            self.window_y=self.nonfull_window_y
            self.root.geometry("%dx%d%+d%+d" % (self.window_width,self.window_height,self.window_x,self.window_y))
        else:
            self.window_width=self.screen_width
            self.window_height=self.screen_height
            self.root.attributes('-fullscreen', True)
            #os.system('unclutter &')
            Popen(['unclutter'], stdout=PIPE, stderr=PIPE) # suppress 'someone created subwindow'
            self.window_x=0
            self.window_y=0  
            self.root.geometry("%dx%d%+d%+d"  % (self.window_width,self.window_height,self.window_x,self.window_y))
            self.root.attributes('-zoomed','1')

        # canvs cover the whole screen whatever the size of the window. 
        self.canvas_height=self.screen_height
        self.canvas_width=self.screen_width
  
        # make sure focus is set.
        self.root.focus_set()

        # define response to main window closing.
        self.root.protocol ("WM_DELETE_WINDOW", self.handle_user_abort)

        # setup a canvas onto which will be drawn the images or text
        self.canvas = Canvas(self.root, bg=self.pp_background)


        if self.options['fullscreen'] is True:
            self.canvas.config(height=self.canvas_height,
                               width=self.canvas_width,
                               highlightthickness=0)
        else:
            self.canvas.config(height=self.canvas_height,
                    width=self.canvas_width,
                        highlightthickness=1,
                               highlightcolor='yellow')
            
        self.canvas.place(x=0,y=0)
        # self.canvas.config(bg='black')
        self.canvas.focus_set()


                
# ****************************************
# INITIALISE THE INPUT DRIVERS
# ****************************************

        # each driver takes a set of inputs, binds them to symboic names
        # and sets up a callback which returns the symbolic name when an input event occurs/

        # use keyboard driver to bind keys to symbolic names and to set up callback
        kbd=KbdDriver()
        if kbd.read(pp_dir,self.pp_home,self.pp_profile) is False:
            self.end('error','cannot find or error in keys.cfg')
        kbd.bind_keys(self.root,self.handle_input_event)

        self.sr=ScreenDriver()
        # read the screen click area config file
        reason,message = self.sr.read(pp_dir,self.pp_home,self.pp_profile)
        if reason == 'error':
            self.end('error','cannot find screen.cfg')


        # create click areas on the canvas, must be polygon as outline rectangles are not filled as far as find_closest goes
        # click areas are made on the Pi Presents canvas not the show canvases.
        reason,message = self.sr.make_click_areas(self.canvas,self.handle_input_event)
        if reason == 'error':
            self.mon.err(self,message)
            self.end('error',message)


# ****************************************
# INITIALISE THE APPLICATION AND START
# ****************************************
        self.shutdown_required=False
        self.exitpipresents_required=False
        
        # kick off GPIO if enabled by command line option
        self.gpio_enabled=False
        if os.path.exists(self.pp_profile + os.sep + 'pp_io_config'+os.sep+ 'gpio.cfg'):
            # initialise the GPIO
            self.gpiodriver=GPIODriver()
            reason,message=self.gpiodriver.init(pp_dir,self.pp_home,self.pp_profile,self.canvas,50,self.handle_input_event)
            if reason == 'error':
                self.end('error',message)
            else:
                self.gpio_enabled=True
                # and start polling gpio
                self.gpiodriver.poll()
            
        # kick off animation sequencer
        self.animate = Animate()
        self.animate.init(pp_dir,self.pp_home,self.pp_profile,self.canvas,200,self.handle_output_event)
        self.animate.poll()

        #create a showmanager ready for time of day scheduler and osc server
        show_id=-1
        self.show_manager=ShowManager(show_id,self.showlist,self.starter_show,self.root,self.canvas,self.pp_dir,self.pp_profile,self.pp_home)
        # first time through set callback to terminate Pi Presents if all shows have ended.
        self.show_manager.init(self.canvas,self.all_shows_ended_callback,self.handle_command,self.showlist)
        # Register all the shows in the showlist
        reason,message=self.show_manager.register_shows()
        if reason == 'error':
            self.mon.err(self,message)
            self.end('error',message)

        # Init OSCDriver, read config and start OSC server
        self.osc_enabled=False
        if os.path.exists(self.pp_profile + os.sep + 'pp_io_config'+ os.sep + 'osc.cfg'):
            self.oscdriver=OSCDriver()
            reason,message=self.oscdriver.init(self.pp_profile,self.handle_command,self.handle_input_event,self.e_osc_handle_output_event)
            if reason == 'error':
                self.end('error',message)
            else:
                self.osc_enabled=True
                self.root.after(1000,self.oscdriver.start_server())

        # and run the start shows
        self.run_start_shows()

       # set up the time of day scheduler including catchup         
        self.tod_enabled=False
        if os.path.exists(self.pp_profile + os.sep + 'schedule.json'):
            # kick off the time of day scheduler which may run additional shows
            self.tod=TimeOfDay()
            self.tod.init(pp_dir,self.pp_home,self.pp_profile,self.root,self.handle_command)
            self.tod_enabled = True


        # then start the time of day scheduler
        if self.tod_enabled is True:
            self.tod.poll()

        # start Tkinters event loop
        self.root.mainloop( )


    def parse_screen(self,size_text):
        fields=size_text.split('*')
        if len(fields)!=2:
            return 'error','do not understand --fullscreen comand option',0,0
        elif fields[0].isdigit()  is False or fields[1].isdigit()  is False:
            return 'error','dimensions are not positive integers in ---fullscreen',0,0
        else:
            return 'normal','',int(fields[0]),int(fields[1])
        

# *********************
#  RUN START SHOWS
# ********************   
    def run_start_shows(self):
        self.mon.trace(self,'run start shows')
        # parse the start shows field and start the initial shows       
        show_refs=self.starter_show['start-show'].split()
        for show_ref in show_refs:
            reason,message=self.show_manager.control_a_show(show_ref,'open')
            if reason == 'error':
                self.mon.err(self,message)
                


# *********************
# User inputs
# ********************
    # handles one command provided as a line of text
    def handle_command(self,command_text):
        self.mon.log(self,"command received: " + command_text)
        if command_text.strip()=="":
            return

        if command_text[0]=='/': 
            if self.osc_enabled is True:
                self.oscdriver.send_command(command_text)
            return
        
        fields= command_text.split()
        show_command=fields[0]
        if len(fields)>1:
            show_ref=fields[1]
        else:
            show_ref=''
            
        if show_command in ('open','close'):
            reason,message=self.show_manager.control_a_show(show_ref,show_command)
            
        elif show_command == 'exitpipresents':
            self.exitpipresents_required=True
            if self.show_manager.all_shows_exited() is True:
                # need root.after to get out of st thread
                self.root.after(1,self.e_all_shows_ended_callback)
                return
            else:
                reason,message= self.show_manager.exit_all_shows()

        elif show_command == 'shutdownnow':
            # need root.after to get out of st thread
            self.root.after(1,self.e_shutdown_pressed)
            return
        else:
            reason='error'
            message = 'command not recognised: '+ show_command
            
        if reason=='error':
            self.mon.err(self,message)
        return

    def e_all_shows_ended_callback(self):
            self.all_shows_ended_callback('normal','no shows running')

    def e_shutdown_pressed(self):
            self.shutdown_pressed('now')


    def e_osc_handle_output_event(self,line):
        #jump  out of server thread
        self.root.after(1, lambda arg=line: self.osc_handle_output_event(arg))

    def  osc_handle_output_event(self,line):
        self.mon.log(self,"output event received: "+ line)
        #osc sends output events as a string
        reason,message,delay,name,param_type,param_values=self.animate.parse_animate_fields(line)
        if reason == 'error':
            self.mon.err(self,message)
            self.end(reason,message)
        self.handle_output_event(name,param_type,param_values,0)

               
    def handle_output_event(self,symbol,param_type,param_values,req_time):
        if self.gpio_enabled is True:
            reason,message=self.gpiodriver.handle_output_event(symbol,param_type,param_values,req_time)
            if reason =='error':
                self.mon.err(self,message)
                self.end(reason,message)
        else:
            self.mon.warn(self,'GPIO not enabled')


    # all input events call this callback with a symbolic name.
    # handle events that affect PP overall, otherwise pass to all active shows
    def handle_input_event(self,symbol,source):
        self.mon.log(self,"event received: "+symbol + ' from '+ source)
        if symbol == 'pp-terminate':
            self.handle_user_abort()
            
        elif symbol == 'pp-shutdown':
            self.shutdown_pressed('delay')
            
        elif symbol == 'pp-shutdownnow':
            # need root.after to grt out of st thread
            self.root.after(1,self.e_shutdown_pressed)
            return
        
        elif symbol == 'pp-exitpipresents':
            self.exitpipresents_required=True
            if self.show_manager.all_shows_exited() is True:
                # need root.after to grt out of st thread
                self.root.after(1,self.e_all_shows_ended_callback)
                return
            reason,message= self.show_manager.exit_all_shows()
        else:
            # events for shows affect the show and could cause it to exit.
            for show in self.show_manager.shows:
                show_obj=show[ShowManager.SHOW_OBJ]
                if show_obj is not None:
                    show_obj.handle_input_event(symbol)



    def shutdown_pressed(self, when):
        if when == 'delay':
            self.root.after(5000,self.on_shutdown_delay)
        else:
            self.shutdown_required=True
            if self.show_manager.all_shows_exited() is True:
               self.all_shows_ended_callback('normal','no shows running')
            else:
                # calls exit method of all shows, results in all_shows_closed_callback
                self.show_manager.exit_all_shows()           


    def on_shutdown_delay(self):
        # 5 second delay is up, if shutdown button still pressed then shutdown
        if self.gpiodriver.shutdown_pressed() is True:
            self.shutdown_required=True
            if self.show_manager.all_shows_exited() is True:
               self.all_shows_ended_callback('normal','no shows running')
            else:
                # calls exit method of all shows, results in all_shows_closed_callback
                self.show_manager.exit_all_shows()


    def handle_sigterm(self,signum,frame):
        self.mon.log(self,'SIGTERM received - '+ str(signum))
        self.terminate()


    def handle_user_abort(self):
        self.mon.log(self,'User abort received')
        self.terminate()

    def terminate(self):
        self.mon.log(self, "terminate received")
        needs_termination=False
        for show in self.show_manager.shows:
            # print  show[ShowManager.SHOW_OBJ], show[ShowManager.SHOW_REF]
            if show[ShowManager.SHOW_OBJ] is not None:
                needs_termination=True
                self.mon.log(self,"Sent terminate to show "+ show[ShowManager.SHOW_REF])
                # call shows terminate method
                # eventually the show will exit and after all shows have exited all_shows_callback will be executed.
                show[ShowManager.SHOW_OBJ].terminate()
        if needs_termination is False:
            self.end('killed','killed - no termination of shows required')


# ******************************
# Ending Pi Presents after all the showers and players are closed
# **************************

    # callback from ShowManager when all shows have ended
    def all_shows_ended_callback(self,reason,message):
        self.canvas.config(bg=self.pp_background)
        if reason in ('killed','error') or self.shutdown_required is True or self.exitpipresents_required is True:
            self.end(reason,message)

    def end(self,reason,message):
        self.mon.log(self,"Pi Presents ending with reason: " + reason)
        if self.root is not None:
            self.root.destroy()
        self.tidy_up()
        # gc.collect()
        # print gc.garbage
        if reason == 'killed':
            self.mon.log(self, "Pi Presents Aborted, au revoir")
            # close logging files 
            self.mon.finish()
            sys.exit()     
        elif reason == 'error':
            self.mon.log(self, "Pi Presents closing because of error, sorry")
            # close logging files 
            self.mon.finish()
            sys.exit()            
        else:
            self.mon.log(self,"Pi Presents  exiting normally, bye")
            # close logging files 
            self.mon.finish()
            if self.shutdown_required is True:
                # print 'SHUTDOWN'
                call(['sudo', 'shutdown', '-h', '-t 5','now'])
                sys.exit()
            else:
                sys.exit()


    
    # tidy up all the peripheral bits of Pi Presents
    def tidy_up(self):
        self.mon.log(self, "Tidying Up")
        # turn screen blanking back on
        if self.options['noblank'] is True:
            call(["xset","s", "on"])
            call(["xset","s", "+dpms"])
            
        # tidy up animation and gpio
        if self.animate is not None:
            self.animate.terminate()
            
        if self.gpio_enabled==True:
            self.gpiodriver.terminate()

        if self.osc_enabled is True:
            self.oscdriver.terminate()
            
        # tidy up time of day scheduler
        if self.tod_enabled is True:
            self.tod.terminate()

         
if __name__ == '__main__':
    pp = PiPresents()





