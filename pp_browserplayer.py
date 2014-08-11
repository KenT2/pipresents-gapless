import os
import time
import copy

from Tkinter import *
import Tkinter as tk
import PIL.Image
import PIL.ImageTk
import PIL.ImageEnhance

from pp_uzbldriver import uzblDriver
from pp_pluginmanager import PluginManager
from pp_showmanager import ShowManager
from pp_gpio import PPIO
from pp_utils import Monitor

class BrowserPlayer:


    #state constants
    _CLOSED = "player_closed"    #probably will not exist
    _STARTING = "player_starting"  #uzbl beinf loaded and fifo created
    _WAITING = "wait for timeout" # waiting for browser to appear on the screen
    _PLAYING = "player_playing"  #track is playing to the screen
    _ENDING = "player_ending"  #track is in the process of ending due to quit or duration exceeded




# ***************************************
# EXTERNAL COMMANDS
# ***************************************

    def __init__(self,
                        show_id,
                         root,
                        canvas,
                        show_params,
                        track_params,
                     pp_dir,
                        pp_home,
                        pp_profile):

        self.mon=Monitor()
        self.mon.on()

        
        #instantiate arguments
        self.show_id=show_id
        self.root=root,
        self.canvas = canvas
        self.show_params=show_params  
        self.track_params=track_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        # get duration limit (secs ) from profile
        if self.track_params['duration']<>"":
            self.duration= int(self.track_params['duration'])
        else:
            self.duration= int(self.show_params['duration'])
        self.duration_limit=20*self.duration


        # get background image from profile.
        self.background_file=''
        if self.track_params['background-image']<>"":
            self.background_file= self.track_params['background-image']
        else:
            if self.track_params['display-show-background']=='yes':
                self.background_file= self.show_params['background-image']
            
        # get background colour from profile.
        if self.track_params['background-colour']<>"":
            self.background_colour= self.track_params['background-colour']
        else:
            self.background_colour= self.show_params['background-colour']

        #get animation instructions from profile
        self.animate_begin_text=self.track_params['animate-begin']
        self.animate_end_text=self.track_params['animate-end']

        # open the plugin Manager
        self.pim=PluginManager(self.show_id,self.root,self.canvas,self.show_params,self.track_params,self.pp_dir,self.pp_home,self.pp_profile) 

        #create an instance of PPIO so we can create gpio events
        self.ppio = PPIO()

        # could put instance generation in play, not sure which is better.
        self.bplayer=uzblDriver(self.canvas)
        self.command_timer=None
        self.tick_timer=None
        self.init_play_state_machine()



    def play(self, track,
                     showlist,
                     end_callback,
                     ready_callback,
                     enable_menu=False):

        #instantiate arguments
        self.track=track
        self.showlist=showlist
        self.end_callback=end_callback         # callback when finished
        self.ready_callback=ready_callback   #callback when ready to play
        self.enable_menu=enable_menu

        # callback to the calling object to e.g remove egg timer.
        if self.ready_callback<>None:
            self.ready_callback()

        # create an  instance of showmanager so we can control concurrent shows
        self.show_manager=ShowManager(self.show_id,self.showlist,self.show_params,self.root,self.canvas,self.pp_dir,self.pp_profile,self.pp_home)

        #web window                  
        if self.track_params['web-window']<>'':
            self.web_window= self.track_params['web-window']
        else:
            self.web_window= self.show_params['web-window']

        reason,message,command,has_window,x1,y1,x2,y2=self.parse_window(self.web_window)
        if reason =='error':
            self.mon.err(self,'web window error: '+'  ' + message + ' in ' + self.web_window)
            self.end_callback(reason,message)
            self=None
        else:
            #deal with web_window
            if has_window==False:
                self.geometry = ' --geometry=maximized '
            else:
                width=x2-x1
                height=y2-y1
                self.geometry = "--geometry=%dx%d%+d%+d "  % (width,height,x1,y1)

            # get browser commands
            reason,message=self.parse_commands(self.track_params['browser-commands'])
            if reason != 'normal':
                self.mon.err(self,message)
                self.end_callback(reason,message)
                self=None
            else:
            
                # Control other shows at beginning
                reason,message=self.show_manager.show_control(self.track_params['show-control-begin'])
                if reason == 'error':
                    self.mon.err(self,message)
                    self.end_callback(reason,message)
                    self=None
                else:
                    #display content
                    reason,message=self.display_content()
                    if reason == 'error':
                        self.mon.err(self,message)
                        self.end_callback(reason,message)
                        self=None
                    else:
                        # create animation events
                        reason,message=self.ppio.animate(self.animate_begin_text,id(self))
                        if reason=='error':
                            self.mon.err(self,message)
                            self.end_callback(reason,message)
                            self=None
                        else:     
                            # start playing the track.
                            self.start_play_state_machine()

    def terminate(self,reason):
        """
        terminate the  player in special circumstances
        normal user termination if by key_pressed 'stop'
        reason will be killed or error
        """
        # circumvents state machine to terminate lower level and then itself.
        if self.bplayer<>None:
            self.mon.log(self,"sent terminate to uzbldriver")
            self.bplayer.terminate(reason)
            self.end('killed',' end without waiting for uzbl to finish') # end without waiting
        else:
            self.mon.log(self,"terminate, uzbldriver not running")
            self.end('killed','terminate, uzbldriver not running')

    def get_links(self):
        return self.track_params['links']

    def input_pressed(self,symbol):
        # print symbol, symbol[0:5]
        if symbol[0:5]=='uzbl-':
            self.control(symbol[5:])
            
        elif symbol == 'pause':
            self.pause()

        elif symbol=='stop':
            self.stop()


        
# ***************************************
# INTERNAL FUNCTIONS
# ***************************************

    #browser do not do pause
    def pause(self):
        self.mon.log(self,"!<pause rejected")
        return False
        
    # other control when playing, not currently used
    def control(self,char):
        if self.play_state==BrowserPlayer._PLAYING and char not in ('exit'):
            self.mon.log(self,"> send control to uzbl:"+ char)
            self.bplayer.control(char)
            return True
        else:
            self.mon.log(self,"!<control rejected")
            return False

    # respond to normal stop
    def stop(self):
        # send signal to stop the track to the state machine
        self.mon.log(self,">stop received")
        self.quit_signal=True

         
      
# ***************************************
#  sequencing
# ***************************************

    """self. play_state controls the playing sequence, it has the following values.
         I am not entirely sure the starting and ending states are required.
         - _closed - the mplayer process is not running, mplayer process can be initiated
         - _starting - mplayer process is running but is not yet able to receive controls
         - _playing - playing a track, controls can be sent
         - _ending - mplayer is doing its termination, controls cannot be sent
    """

    def init_play_state_machine(self):
        self.quit_signal=False
        self.play_state=BrowserPlayer._CLOSED
 
    def start_play_state_machine(self):
        #initialise all the state machine variables
        self.duration_count = 0
        self.quit_signal=False     # signal that user has pressed stop

        #play the track
        self.bplayer.play(self.track,self.geometry)
        self.mon.log (self,'Playing track from show Id: '+ str(self.show_id))
        self.play_state=BrowserPlayer._STARTING
        
        # and start polling for state changes and count duration
        self.tick_timer=self.canvas.after(50, self.play_state_machine)


    def play_state_machine(self):

        if self.play_state == BrowserPlayer._CLOSED:
            self.mon.log(self,"      State machine: " + self.play_state)
            return 
                
        elif self.play_state == BrowserPlayer._STARTING:
            # self.mon.log(self,"      State machine: " + self.play_state)
            
            # if uzbl fifo is available can send comands to uzbl but change to wait state to wait for it to appear on screen
            if self.bplayer.start_play_signal==True:
                self.mon.log(self,"            <fifo available signal received from uzbl")
                self.bplayer.start_play_signal=False
                self.play_state=BrowserPlayer._WAITING
                # get rid of status bar
                self.bplayer.control('set show_status = 0')
                # and get ready to wait for browser to appear
                self.wait_count= 50   # 10 seconds at 200mS steps 
                self.mon.log(self,"      State machine: uzbl process alive")
                
            self.tick_timer=self.canvas.after(200, self.play_state_machine)


        elif self.play_state == BrowserPlayer._WAITING:
            if self.wait_count==0:
                # set state to playing
                self.play_state = BrowserPlayer._PLAYING
                # and start executing the browser commands
                self.play_commands()
                self.mon.log(self,"      State machine: uzbl_playing started")
                
            self.wait_count -=1
            self.tick_timer=self.canvas.after(200, self.play_state_machine)

        elif self.play_state == BrowserPlayer._PLAYING:
            self.duration_count+=1
            # self.mon.log(self,"      State machine: " + self.play_state)
            
            # service any queued stop signals and test duration count
            if self.quit_signal==True or (self.duration_limit>0 and self.duration_count>self.duration_limit):
                self.mon.log(self,"      Service stop required signal or timeout")
                # self.quit_signal=False
                self.stop_bplayer()
                self.play_state = BrowserPlayer._ENDING

            # uzbl reports it is terminating so change to ending state
            if self.bplayer.end_play_signal:                    
                self.mon.log(self,"            <end play signal received")
                self.play_state = BrowserPlayer._ENDING
            self.tick_timer=self.canvas.after(50, self.play_state_machine)

        elif self.play_state == BrowserPlayer._ENDING:
            # self.mon.log(self,"      State machine: " + self.play_state)
            # if spawned process has closed can change to closed state
            # self.mon.log (self,"      State machine : is luakit process running? -  "  + str(self.bplayer.is_running()))
            if self.bplayer.is_running() ==False:
                self.mon.log(self,"            <uzbl process is dead")
                if self.quit_signal==True:
                    self.quit_signal=False
                self.play_state = BrowserPlayer._CLOSED
                self.end('normal','quit required or timeout')
            else:
                self.tick_timer=self.canvas.after(50, self.play_state_machine)
                


    def stop_bplayer(self):
        # send signal to stop the track to the state machine
        self.mon.log(self,"         >send stop to uzbl driver")
        if self.play_state==BrowserPlayer._PLAYING:
            self.bplayer.stop()
            return True
        else:
            self.mon.log(self,"!<stop rejected")
            return False

# *****************
# ending the player
# *****************

    def end(self,reason,message):
            # stop the plugin
            if self.pim<>None:
                self.pim.stop_plugin()

            # abort the timers
            if self.tick_timer<>None:
                self.canvas.after_cancel(self.tick_timer)
                self.tick_timer=None
            if self.command_timer<>None:
                self.canvas.after_cancel(self.command_timer)
                self.tick_timer=None
            # clean up and fifos and sockets left by uzbl
            os.system('rm -f  /tmp/uzbl_*')
            if reason in ('error','killed'):
                self.end_callback(reason,message)
                self=None

            else:
                # normal end so do show control and animation

                # Control concurrent shows at end
                reason,message=self.show_manager.show_control(self.track_params['show-control-end'])
                if reason =='error':
                    self.mon.err(self,message)
                    self.end_callback(reason,message)
                    self=None
                else:
                   # clear events list for this track
                    if self.track_params['animate-clear']=='yes':
                        self.ppio.clear_events_list(id(self))
                    
                    # create animation events for ending
                    reason,message=self.ppio.animate(self.animate_end_text,id(self))
                    if reason=='error':
                        self.mon.err(self,message)
                        self.end_callback(reason,message)
                        self=None
                    else:
                        self.end_callback('normal',"track has terminated or quit")
                        self=None



# *****************
# displaying things
# *****************
            
    def display_content(self):
       

        self.canvas.delete('pp-content')


        #background colour
        if  self.background_colour<>'':
            self.canvas.config(bg=self.background_colour)
            
        if self.background_file<>'':
            self.background_img_file = self.complete_path(self.background_file)
            if not os.path.exists(self.background_img_file):
                self.mon.err(self,"Audio background file not found: "+ self.background_img_file)
                self.end('error',"Audio background file not found")
            else:
                pil_background_img=PIL.Image.open(self.background_img_file)
                self.background = PIL.ImageTk.PhotoImage(pil_background_img)
                self.drawn = self.canvas.create_image(int(self.canvas['width'])/2,
                                              int(self.canvas['height'])/2,
                                              image=self.background,
                                              anchor=CENTER,
                                                tag='pp-content')

        # execute the plugin if required
        if self.track_params['plugin']<>'':

            reason,message,self.track = self.pim.do_plugin(self.track,self.track_params['plugin'],)
            if reason <> 'normal':
                return reason,message

                
        # display hint text if enabled
       
        if self.enable_menu== True:
            self.canvas.create_text(int(self.show_params['hint-x']),
                                                    int(self.show_params['hint-y']),
                                                  text=self.show_params['hint-text'],
                                                  fill=self.show_params['hint-colour'],
                                                font=self.show_params['hint-font'],
                                                    anchor=NW,
                                                tag='pp-content')

            
        # display show text if enabled
        if self.show_params['show-text']<> ''and self.track_params['display-show-text']=='yes':
            self.canvas.create_text(int(self.show_params['show-text-x']),int(self.show_params['show-text-y']),
                                                    anchor=NW,
                                                  text=self.show_params['show-text'],
                                                  fill=self.show_params['show-text-colour'],
                                                  font=self.show_params['show-text-font'],
                                                tag='pp-content')
            
        # display track text if enabled
        if self.track_params['track-text']<> '':
            self.canvas.create_text(int(self.track_params['track-text-x']),int(self.track_params['track-text-y']),
                                                    anchor=NW,
                                                  text=self.track_params['track-text'],
                                                  fill=self.track_params['track-text-colour'],
                                                  font=self.track_params['track-text-font'],
                                                tag='pp-content')

        self.mon.log(self,"Displayed background and text ")

        self.canvas.tag_raise('pp-click-area')
        
        self.canvas.update_idletasks( )

        return 'normal',''


     
# *******************   
# browser commands
# ***********************

    def parse_commands(self,command_text):
        self.command_list=[]
        lines = command_text.split('\n')
        for line in lines:
            if line.strip()=="":
                continue
            reason,entry=self.parse_command(line)
            if reason != 'normal':
                return 'error',entry
            self.command_list.append(copy.deepcopy(entry))
        # print self.command_list
        return 'normal',''

    def parse_command(self,line):
        fields = line.split()
        if fields[0]=='uzbl':
            # print fields[0], line[4:]
            return  'normal',[fields[0],line[4:]]
        
        if len(fields) not in (1,2):
            return 'error',"incorrect number of fields in command: " + line
        command=fields[0]
        arg=''
        if command not in ('load','refresh','wait','exit','loop'):
            return 'error','unknown command: '+ command
            
        if command in ('refresh','exit','loop') and len(fields)<>1:
            return 'error','incorrect number of fields for '+ command + 'in: ' + line
            
        if command == 'load':
            if len(fields)<>2:
                return 'error','incorrect number of fields for '+ command + 'in: ' + line
            else:
                arg = fields[1]


        if command == 'wait':
            if len(fields)<>2:
                return 'error','incorrect number of fields for '+ command + 'in: ' + line
            else:
                arg = fields[1]
                if not arg.isdigit():return 'error','Argument for Wait is not 0 or positive number in: ' + line

        return 'normal',[command,arg]


        
    def play_commands(self):
        if len(self.command_list)==0:
            return
        self.loop=0
        self.command_index=0
        self.canvas.after(100,self.execute_command)

        
    def execute_command(self):
        entry=self.command_list[self.command_index]
        command=entry[0]
        arg=entry[1]
        if self.command_index==len(self.command_list)-1:
            self.command_index=self.loop
        else:
            self.command_index+=1
            
        # execute command
        if command == 'load':
            #self.canvas.focus_force()
            #self.root.lower()
            file=self.complete_path(arg)
            self.bplayer.control('uri '+ file)
            self.command_timer=self.canvas.after(10,self.execute_command)
        elif command == 'refresh':
            self.bplayer.control('reload_ign_cache')
            self.command_timer=self.canvas.after(10,self.execute_command)
        elif command == 'wait':
            self.command_timer=self.canvas.after(1000*int(arg),self.execute_command)        
        elif  command=='exit':
            self.quit_signal=True
        elif command=='loop':
            self.loop=self.command_index
            self.command_timer=self.canvas.after(10,self.execute_command)
        elif command=='uzbl':
            self.bplayer.control(arg)
            self.command_timer=self.canvas.after(10,self.execute_command)

        
        
        
# *****************
# utilities
# *****************

    def complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file[0]=="+":
                track_file=self.pp_home+track_file[1:]
        self.mon.log(self,"Background image is "+ track_file)
        return track_file     
            





    def parse_window(self,line):
            # parses warp _ or xy2
            
            fields = line.split()
            # check there is a command field
            if len(fields) < 1:
                    return 'error','no type field','',False,0,0,0,0
                

            #deal with warp which has 1 or 5  arguments
            # check basic syntax
            if  fields[0] <>'warp':
                    return 'error','not a valid type','',False,0,0,0,0
            if len(fields) not in (1,5):
                    return 'error','wrong number of coordinates for warp','',False,0,0,0,0

            # deal with window coordinates    
            if len(fields) == 5:
                #window is specified
                if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                    return 'error','coordinates are not positive integers','',False,0,0,0,0
                has_window=True
                return 'normal','',fields[0],has_window,int(fields[1]),int(fields[2]),int(fields[3]),int(fields[4])
            else:
                # fullscreen
                has_window=False
                return 'normal','',fields[0],has_window,0,0,0,0


