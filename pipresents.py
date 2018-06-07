#! /usr/bin/env python
"""
Pi Presents is a toolkit for construcing and deploying multimedia interactive presentations
on the Raspberry Pi.
It is aimed at primarily at  musems, exhibitions and galleries
but has many other applications including digital signage

Version 1.3 [pipresents-gapless]
Copyright 2012/2013/2014/2015/2016/2017/2018, Ken Thompson
See github for licence conditions
See readme.md and manual.pdf for instructions.
"""

import os
import sys
import signal
from subprocess import call, check_output
import time
import gc
from Tkinter import Tk, Canvas
import tkMessageBox
from time import sleep
# import objgraph


from pp_options import command_options
from pp_showlist import ShowList
from pp_showmanager import ShowManager
from pp_screendriver import ScreenDriver
from pp_timeofday import TimeOfDay
from pp_utils import Monitor
from pp_utils import StopWatch
from pp_animate import Animate
from pp_oscdriver import OSCDriver
from pp_network import Mailer, Network
from pp_iopluginmanager import IOPluginManager
from pp_countermanager import CounterManager

class PiPresents(object):

    def pipresents_version(self):
        vitems=self.pipresents_issue.split('.')
        if len(vitems)==2:
            # cope with 2 digit version numbers before 1.3.2
            return 1000*int(vitems[0])+100*int(vitems[1])
        else:
            return 1000*int(vitems[0])+100*int(vitems[1])+int(vitems[2])


    def __init__(self):
        # gc.set_debug(gc.DEBUG_UNCOLLECTABLE|gc.DEBUG_INSTANCES|gc.DEBUG_OBJECTS|gc.DEBUG_SAVEALL)
        gc.set_debug(gc.DEBUG_UNCOLLECTABLE|gc.DEBUG_SAVEALL)
        self.pipresents_issue="1.3.5"
        self.pipresents_minorissue = '1.3.5c'
        # position and size of window without -f command line option
        self.nonfull_window_width = 0.45 # proportion of width
        self.nonfull_window_height= 0.7 # proportion of height
        self.nonfull_window_x = 0 # position of top left corner
        self.nonfull_window_y=0   # position of top left corner


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
            if self.options['manager']  is False:
                tkMessageBox.showwarning("Pi Presents","Bad Application Directory")
            exit(102)

        
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
                            'PathManager','ControlsManager','ShowManager','PluginManager','IOPluginManager',
                            'MplayerDriver','OMXDriver','UZBLDriver',
                            'TimeOfDay','ScreenDriver','Animate','OSCDriver','CounterManager',
                            'Network','Mailer'
                            ]
        

        # Monitor.classes=['PiPresents','MediaShow','GapShow','Show','VideoPlayer','Player','OMXDriver']
        # Monitor.classes=['OSCDriver']
        
        # get global log level from command line
        Monitor.log_level = int(self.options['debug'])
        Monitor.manager = self.options['manager']
        # print self.options['manager']
        self.mon.newline(3)
        self.mon.sched (self,None, "Pi Presents is starting, Version:"+self.pipresents_minorissue + ' at '+time.strftime("%Y-%m-%d %H:%M.%S"))
        self.mon.log (self, "Pi Presents is starting, Version:"+self.pipresents_minorissue+ ' at '+time.strftime("%Y-%m-%d %H:%M.%S"))
        # self.mon.log (self," OS and separator:" + os.name +'  ' + os.sep)
        self.mon.log(self,"sys.path[0] -  location of code: "+sys.path[0])

        # log versions of Raspbian and omxplayer, and GPU Memory
        with open("/boot/issue.txt") as ifile:
            self.mon.log(self,'\nRaspbian: '+ifile.read())

        self.mon.log(self,'\n'+check_output(["omxplayer", "-v"]))
        self.mon.log(self,'\nGPU Memory: '+check_output(["vcgencmd", "get_mem", "gpu"]))

        if os.geteuid() == 0:
            print 'Do not run Pi Presents with sudo'
            self.mon.log(self,'Do not run Pi Presents with sudo')
            self.mon.finish()
            sys.exit(102)

        
        if "DESKTOP_SESSION" not in os.environ:
            print 'Pi Presents must be run from the Desktop'
            self.mon.log(self,'Pi Presents must be run from the Desktop')
            self.mon.finish()
            sys.exit(102)
        else:
            self.mon.log(self,'Desktop is '+ os.environ['DESKTOP_SESSION'])
        
        # optional other classes used
        self.root=None
        self.ppio=None
        self.tod=None
        self.animate=None
        self.ioplugin_manager=None
        self.oscdriver=None
        self.osc_enabled=False
        self.tod_enabled=False
        self.email_enabled=False
        
        user=os.getenv('USER')

        if user is None:
            tkMessageBox.showwarning("You must be logged in to run Pi Presents")
            exit(102)

        if user !='pi':
            self.mon.warn(self,"You must be logged as pi to use GPIO")

        self.mon.log(self,'User is: '+ user)
        # self.mon.log(self,"os.getenv('HOME') -  user home directory (not used): " + os.getenv('HOME')) # does not work
        # self.mon.log(self,"os.path.expanduser('~') -  user home directory: " + os.path.expanduser('~'))   # does not work



        # check network is available
        self.network_connected=False
        self.network_details=False
        self.interface=''
        self.ip=''
        self.unit=''
        
        # sets self.network_connected and self.network_details
        self.init_network()

        
        # start the mailer and send email when PP starts
        self.email_enabled=False
        if self.network_connected is True:
            self.init_mailer()
            if self.email_enabled is True and self.mailer.email_at_start is True:
                subject= '[Pi Presents] ' + self.unit + ': PP Started on ' + time.strftime("%Y-%m-%d %H:%M")
                message = time.strftime("%Y-%m-%d %H:%M") + '\nUnit: ' + self.unit + '   Profile: '+ self.options['profile']+ '\n ' + self.interface + '\n ' + self.ip 
                self.send_email('start',subject,message) 

         
        # get profile path from -p option
        if self.options['profile'] != '':
            self.pp_profile_path="/pp_profiles/"+self.options['profile']
        else:
            self.mon.err(self,"Profile not specified in command ")
            self.end('error','Profile not specified with the commands -p option')
        
       # get directory containing pp_home from the command,
        if self.options['home']  == "":
            home = os.sep+ 'home' + os.sep + user + os.sep+"pp_home"
        else:
            home = self.options['home'] + os.sep+ "pp_home"         
        self.mon.log(self,"pp_home directory is: " + home)


        # check if pp_home exists.
        # try for 10 seconds to allow usb stick to automount
        found=False
        for i in range (1, 10):
            self.mon.log(self,"Trying pp_home at: " + home +  " (" + str(i)+')')
            if os.path.exists(home):
                found=True
                self.pp_home=home
                break
            time.sleep (1)
        if found is True:
            self.mon.log(self,"Found Requested Home Directory, using pp_home at: " + home)
        else:
            self.mon.err(self,"Failed to find pp_home directory at " + home)
            self.end('error',"Failed to find pp_home directory at " + home)


        # check profile exists
        self.pp_profile=self.pp_home+self.pp_profile_path
        if os.path.exists(self.pp_profile):
            self.mon.sched(self,None,"Running profile: " + self.pp_profile_path)
            self.mon.log(self,"Found Requested profile - pp_profile directory is: " + self.pp_profile)
        else:
            self.mon.err(self,"Failed to find requested profile: "+ self.pp_profile)
            self.end('error',"Failed to find requested profile: "+ self.pp_profile)

        self.mon.start_stats(self.options['profile'])
        
        if self.options['verify'] is True:
            self.mon.err(self,"Validation option not supported - use the editor")
            self.end('error','Validation option not supported - use the editor')

         
        # initialise and read the showlist in the profile
        self.showlist=ShowList()
        self.showlist_file= self.pp_profile+ "/pp_showlist.json"
        if os.path.exists(self.showlist_file):
            self.showlist.open_json(self.showlist_file)
        else:
            self.mon.err(self,"showlist not found at "+self.showlist_file)
            self.end('error',"showlist not found at "+self.showlist_file)

        # check profile and Pi Presents issues are compatible
        if self.showlist.profile_version() != self.pipresents_version():
            self.mon.err(self,"Version of showlist " + self.showlist.profile_version_string + " is not  same as Pi Presents")
            self.end('error',"Version of showlist " + self.showlist.profile_version_string + " is not  same as Pi Presents")


        # get the 'start' show from the showlist
        index = self.showlist.index_of_start_show()
        if index >=0:
            self.showlist.select(index)
            self.starter_show=self.showlist.selected_show()
        else:
            self.mon.err(self,"Show [start] not found in showlist")
            self.end('error',"Show [start] not found in showlist")


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
        self.root.config(bg=self.starter_show['background-colour'])

        self.mon.log(self, 'monitor screen dimensions are ' + str(self.root.winfo_screenwidth()) + ' x ' + str(self.root.winfo_screenheight()) + ' pixels')
        if self.options['screensize'] =='':        
            self.screen_width = self.root.winfo_screenwidth()
            self.screen_height = self.root.winfo_screenheight()
        else:
            reason,message,self.screen_width,self.screen_height=self.parse_screen(self.options['screensize'])
            if reason =='error':
                self.mon.err(self,message)
                self.end('error',message)

        self.mon.log(self, 'forced screen dimensions (--screensize) are ' + str(self.screen_width) + ' x ' + str(self.screen_height) + ' pixels')
       
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
            os.system('unclutter &')
            self.window_x=0
            self.window_y=0  
            self.root.geometry("%dx%d%+d%+d"  % (self.window_width,self.window_height,self.window_x,self.window_y))
            self.root.attributes('-zoomed','1')

        # canvas cover the whole screen whatever the size of the window. 
        self.canvas_height=self.screen_height
        self.canvas_width=self.screen_width
  
        # make sure focus is set.
        self.root.focus_set()

        # define response to main window closing.
        self.root.protocol ("WM_DELETE_WINDOW", self.handle_user_abort)

        # setup a canvas onto which will be drawn the images or text
        self.canvas = Canvas(self.root, bg=self.starter_show['background-colour'])


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
# INITIALISE THE TOUCHSCREEN DRIVER
# ****************************************

        # each driver takes a set of inputs, binds them to symboic names
        # and sets up a callback which returns the symbolic name when an input event occurs

        self.sr=ScreenDriver()
        # read the screen click area config file
        reason,message = self.sr.read(pp_dir,self.pp_home,self.pp_profile)
        if reason == 'error':
            self.end('error','cannot find, or error in screen.cfg')


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
        self.reboot_required=False
        self.terminate_required=False
        self.exitpipresents_required=False

        # initialise the I/O plugins by importing their drivers
        self.ioplugin_manager=IOPluginManager()
        reason,message=self.ioplugin_manager.init(self.pp_dir,self.pp_profile,self.root,self.handle_input_event)
        if reason == 'error':
            # self.mon.err(self,message)
            self.end('error',message)

        
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
        if self.network_connected is True:
            if os.path.exists(self.pp_profile + os.sep + 'pp_io_config'+ os.sep + 'osc.cfg'):
                self.oscdriver=OSCDriver()
                reason,message=self.oscdriver.init(self.pp_profile,
                                                   self.unit,self.interface,self.ip,
                                                   self.handle_command,self.handle_input_event,self.e_osc_handle_animate)
                if reason == 'error':
                    self.mon.err(self,message)
                    self.end('error',message)
                else:
                    self.osc_enabled=True
                    self.root.after(1000,self.oscdriver.start_server())

        
        # initialise ToD scheduler calculating schedule for today
        self.tod=TimeOfDay()
        reason,message,self.tod_enabled = self.tod.init(pp_dir,self.pp_home,self.pp_profile,self.showlist,self.root,self.handle_command)
        if reason == 'error':
            self.mon.err(self,message)
            self.end('error',message)
            
        # warn if the network not available when ToD required
        if self.tod_enabled is True and self.network_connected is False:
            self.mon.warn(self,'Network not connected  so Time of Day scheduler may be using the internal clock')

        # init the counter manager
        self.counter_manager=CounterManager()
        self.counter_manager.init()


        # warn about start shows and scheduler

        if self.starter_show['start-show']=='' and self.tod_enabled is False:
            self.mon.sched(self,None,"No Start Shows in Start Show and no shows scheduled") 
            self.mon.warn(self,"No Start Shows in Start Show and no shows scheduled")

        if self.starter_show['start-show'] !='' and self.tod_enabled is True:
            self.mon.sched(self,None,"Start Shows in Start Show and shows scheduled - conflict?") 
            self.mon.warn(self,"Start Shows in Start Show and shows scheduled - conflict?")

        # run the start shows
        self.run_start_shows()           

        # kick off the time of day scheduler which may run additional shows
        if self.tod_enabled is True:
            self.tod.poll()

        # start the I/O plugins input event generation
        self.ioplugin_manager.start()


        # start Tkinters event loop
        self.root.mainloop( )


    def parse_screen(self,size_text):
        fields=size_text.split('*')
        if len(fields)!=2:
            return 'error','do not understand --screensize comand option',0,0
        elif fields[0].isdigit()  is False or fields[1].isdigit()  is False:
            return 'error','dimensions are not positive integers in --screensize',0,0
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

    def e_osc_handle_animate(self,line):
        #jump  out of server thread
        self.root.after(1, lambda arg=line: self.osc_handle_animate(arg))

    def osc_handle_animate(self,line):
        self.mon.log(self,"animate command received: "+ line)
        #osc sends output events as a string
        reason,message,delay,name,param_type,param_values=self.animate.parse_animate_fields(line)
        if reason == 'error':
            self.mon.err(self,message)
            self.end(reason,message)
        self.handle_output_event(name,param_type,param_values,0)

    # output events are animate commands       
    def handle_output_event(self,symbol,param_type,param_values,req_time):
            reason,message=self.ioplugin_manager.handle_output_event(symbol,param_type,param_values,req_time)
            if reason =='error':
                self.mon.err(self,message)
                self.end(reason,message)



    # all input events call this callback providing a symbolic name.
    # handle events that affect PP overall, otherwise pass to all active shows
    def handle_input_event(self,symbol,source):
        self.mon.log(self,"event received: "+symbol + ' from '+ source)
        if symbol == 'pp-terminate':
            self.handle_user_abort()
            
        elif symbol == 'pp-shutdown':
            self.mon.err(self,'pp-shutdown removed in version 1.3.3a, see Release Notes')
            self.end('error','pp-shutdown removed in version 1.3.3a, see Release Notes')

            
        elif symbol == 'pp-shutdownnow':
            # need root.after to grt out of st thread
            self.root.after(1,self.shutdownnow_pressed)
            return
        
        elif symbol == 'pp-exitpipresents':
            self.exitpipresents_required=True
            if self.show_manager.all_shows_exited() is True:
                # need root.after to grt out of st thread
                self.root.after(1,self.e_all_shows_ended_callback)
                return
            reason,message= self.show_manager.exit_all_shows()
        else:
            # pass the input event to all registered shows
            for show in self.show_manager.shows:
                show_obj=show[ShowManager.SHOW_OBJ]
                if show_obj is not None:
                    show_obj.handle_input_event(symbol)



    # commands are generaed by tracks and shows
    # they can open or close shows, generate input events and do special tasks
    # commands also generate osc outputs to other computers
    # handles one command provided as a line of text
    
    def handle_command(self,command_text,source='',show=''):
        # print 'PIPRESENTS ',command_text,'\n   Source',source,'from',show
        self.mon.log(self,"command received: " + command_text)
        if command_text.strip()=="":
            return

        fields= command_text.split()

        if fields[0] in ('osc','OSC'): 
            if self.osc_enabled is True:
                status,message=self.oscdriver.parse_osc_command(fields[1:])
                if status=='warn':
                    self.mon.warn(self,message)
                if status=='error':
                    self.mon.err(self,message)
                    self.end('error',message)
                return
        

        if fields[0] =='counter':
            status,message=self.counter_manager.parse_counter_command(fields[1:])
            if status=='error':
                self.mon.err(self,message)
                self.end('error',message)
            return

                           
        show_command=fields[0]
        if len(fields)>1:
            show_ref=fields[1]
        else:
            show_ref=''
        if show_command in ('open','close','closeall','openexclusive'):
            self.mon.sched(self, TimeOfDay.now,command_text + ' received from show:'+show)
            if self.shutdown_required is False and self.terminate_required is False:
                reason,message=self.show_manager.control_a_show(show_ref,show_command)
            else:
                return
            
        elif show_command =='monitor':
            self.handle_monitor_command(show_ref)
            return

        elif show_command =='cec':
            self.handle_cec_command(show_ref)
            return
        
        elif show_command == 'event':
            self.handle_input_event(show_ref,'Show Control')
            return
        
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
            self.root.after(1,self.shutdownnow_pressed)
            return

        elif show_command == 'reboot':
            # need root.after to get out of st thread
            self.root.after(1,self.reboot_pressed)
            return
        
        else:
            reason='error'
            message = 'command not recognised: '+ show_command
            
        if reason=='error':
            self.mon.err(self,message)
        return


    def handle_monitor_command(self,command):
        if command == 'on':
            os.system('vcgencmd display_power 1 >/dev/null')
        elif command == 'off':
            os.system('vcgencmd display_power 0 >/dev/null')

    def handle_cec_command(self,command):
        if command == 'on':
            os.system('echo "on 0" | cec-client -s')
        elif command == 'standby':
            os.system('echo "standby 0" | cec-client -s')

        elif command == 'scan':
            os.system('echo scan | cec-client -s -d 1')
                      
    # deal with differnt commands/input events

    def shutdownnow_pressed(self):
        self.shutdown_required=True
        if self.show_manager.all_shows_exited() is True:
           self.all_shows_ended_callback('normal','no shows running')
        else:
            # calls exit method of all shows, results in all_shows_closed_callback
            self.show_manager.exit_all_shows()

    def reboot_pressed(self):
        self.reboot_required=True
        if self.show_manager.all_shows_exited() is True:
           self.all_shows_ended_callback('normal','no shows running')
        else:
            # calls exit method of all shows, results in all_shows_closed_callback
            self.show_manager.exit_all_shows() 


    def handle_sigterm(self,signum):
        self.mon.log(self,'SIGTERM received - '+ str(signum))
        self.terminate()


    def handle_user_abort(self):
        self.mon.log(self,'User abort received')
        self.terminate()

    def terminate(self):
        self.mon.log(self, "terminate received")
        self.terminate_required=True
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

    def e_all_shows_ended_callback(self):
        self.all_shows_ended_callback('normal','no shows running')

    # callback from ShowManager when all shows have ended
    def all_shows_ended_callback(self,reason,message):
        self.canvas.config(bg=self.starter_show['background-colour'])
        if reason in ('killed','error') or self.shutdown_required is True or self.exitpipresents_required is True or self.reboot_required is True:
            self.end(reason,message)

    def end(self,reason,message):
        self.mon.log(self,"Pi Presents ending with reason: " + reason)
        if self.root is not None:
            self.root.destroy()
        self.tidy_up()
        if reason == 'killed':
            if self.email_enabled is True and self.mailer.email_on_terminate is True:
                subject= '[Pi Presents] ' + self.unit + ': PP Exited with reason: Terminated'
                message = time.strftime("%Y-%m-%d %H:%M") + '\n ' + self.unit + '\n ' + self.interface + '\n ' + self.ip 
                self.send_email(reason,subject,message)
            self.mon.sched(self, None,"Pi Presents Terminated, au revoir\n")
            self.mon.log(self, "Pi Presents Terminated, au revoir")
                          
            # close logging files
            self.mon.finish()
            print 'Uncollectable Garbage',gc.collect()
            # objgraph.show_backrefs(objgraph.by_type('Monitor'))
            sys.exit(101)
                          
        elif reason == 'error':
            if self.email_enabled is True and self.mailer.email_on_error is True:
                subject= '[Pi Presents] ' + self.unit + ': PP Exited with reason: Error'
                message_text = 'Error message: '+ message + '\n'+ time.strftime("%Y-%m-%d %H:%M") + '\n ' + self.unit + '\n ' + self.interface + '\n ' + self.ip 
                self.send_email(reason,subject,message_text)   
            self.mon.sched(self,None, "Pi Presents closing because of error, sorry\n")
            self.mon.log(self, "Pi Presents closing because of error, sorry")
                          
            # close logging files 
            self.mon.finish()
            print 'uncollectable garbage',gc.collect()
            sys.exit(102)

        else:           
            self.mon.sched(self,None,"Pi Presents  exiting normally, bye\n")
            self.mon.log(self,"Pi Presents  exiting normally, bye")
            
            # close logging files 
            self.mon.finish()
            if self.reboot_required is True:
                # print 'REBOOT'
                call (['sudo','reboot'])
            if self.shutdown_required is True:
                # print 'SHUTDOWN'
                call (['sudo','shutdown','now','SHUTTING DOWN'])
            print 'uncollectable garbage',gc.collect()
            sys.exit(100)


    # tidy up all the peripheral bits of Pi Presents
    def tidy_up(self):
        self.handle_monitor_command('on')
        self.mon.log(self, "Tidying Up")
        # turn screen blanking back on
        if self.options['noblank'] is True:
            call(["xset","s", "on"])
            call(["xset","s", "+dpms"])
            
        # tidy up animation
        if self.animate is not None:
            self.animate.terminate()

        # tidy up i/o plugins
        if self.ioplugin_manager != None:
            self.ioplugin_manager.terminate()

        if self.osc_enabled is True:
            self.oscdriver.terminate()
            
        # tidy up time of day scheduler
        if self.tod_enabled is True:
            self.tod.terminate()



# *******************************
# Connecting to network and email
# *******************************

    def init_network(self):

        timeout=int(self.options['nonetwork'])
        if timeout== 0:
            self.network_connected=False
            self.unit=''
            self.ip=''
            self.interface=''
            return
        
        self.network=Network()
        self.network_connected=False

        # try to connect to network
        self.mon.log (self, 'Waiting up to '+ str(timeout) + ' seconds for network')
        success=self.network.wait_for_network(timeout)
        if success is False:
            self.mon.warn(self,'Failed to connect to network after ' + str(timeout) + ' seconds')
            # tkMessageBox.showwarning("Pi Presents","Failed to connect to network so using fake-hwclock")
            return

        self.network_connected=True
        self.mon.sched (self, None,'Time after network check is '+ time.strftime("%Y-%m-%d %H:%M.%S"))
        self.mon.log (self, 'Time after network check is '+ time.strftime("%Y-%m-%d %H:%M.%S"))

        # Get web configuration
        self.network_details=False
        network_options_file_path=self.pp_dir+os.sep+'pp_config'+os.sep+'pp_web.cfg'
        if not os.path.exists(network_options_file_path):
            self.mon.warn(self,"pp_web.cfg not found at "+network_options_file_path)
            return
        self.mon.log(self, 'Found pp_web.cfg in ' + network_options_file_path)

        self.network.read_config(network_options_file_path)
        self.unit=self.network.unit

        # get interface and IP details of preferred interface
        self.interface,self.ip = self.network.get_preferred_ip()
        if self.interface == '':
            self.network_connected=False
            return
        self.network_details=True
        self.mon.log (self, 'Network details ' + self.unit + ' ' + self.interface + ' ' +self.ip)


    def init_mailer(self):

        self.email_enabled=False
        email_file_path = self.pp_dir+os.sep+'pp_config'+os.sep+'pp_email.cfg'
        if not os.path.exists(email_file_path):
            self.mon.log(self,'pp_email.cfg not found at ' + email_file_path)
            return
        self.mon.log(self,'Found pp_email.cfg at ' + email_file_path)
        self.mailer=Mailer()
        self.mailer.read_config(email_file_path)
        # all Ok so can enable email if config file allows it.
        if self.mailer.email_allowed is True:
            self.email_enabled=True
            self.mon.log (self,'Email Enabled')


    def try_connect(self):
        tries=1
        while True:
            success, error = self.mailer.connect()
            if success is True:
                return True
            else:
                self.mon.log(self,'Failed to connect to email SMTP server ' + str(tries) +  '\n ' +str(error))
                tries +=1
                if tries >5:
                    self.mon.log(self,'Failed to connect to email SMTP server after ' + str(tries))
                    return False


    def send_email(self,reason,subject,message):
        if self.try_connect() is False:
            return False
        else:
            success,error = self.mailer.send(subject,message)
            if success is False:
                self.mon.log(self, 'Failed to send email: ' + str(error))
                success,error=self.mailer.disconnect()
                if success is False:
                    self.mon.log(self,'Failed disconnect after send:' + str(error))
                return False
            else:
                self.mon.log(self,'Sent email for ' + reason)
                success,error=self.mailer.disconnect()
                if success is False:
                    self.mon.log(self,'Failed disconnect from email server ' + str(error))
                return True
              

         
if __name__ == '__main__':

    # wait for environment variables to stabilize. Required for Jessie autostart
    tries=0
    success=False
    while tries < 40:
        # get directory holding the code
        code_dir=sys.path[0]
        code_path=code_dir+os.sep+'pipresents.py'
        if os.path.exists(code_path):
            success =True
            break
        tries +=1
        sleep (0.5)
        
    if success is False:
        tkMessageBox.showwarning("pipresents.py","Bad application directory: "+ code_dir)
        exit()

    pp = PiPresents()





