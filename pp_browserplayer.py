import os
import copy
from pp_uzbldriver import UZBLDriver
from pp_player import Player
from pp_utils import parse_rectangle


class BrowserPlayer(Player):

# ***************************************
# EXTERNAL COMMANDS
# ***************************************

    def __init__(self,
                 show_id,
                 showlist,
                 root,
                 canvas,
                 show_params,
                 track_params ,
                 pp_dir,
                 pp_home,
                 pp_profile,
                 end_callback,
                 command_callback):

        # initialise items common to all players   
        Player.__init__( self,
                         show_id,
                         showlist,
                         root,
                         canvas,
                         show_params,
                         track_params ,
                         pp_dir,
                         pp_home,
                         pp_profile,
                         end_callback,
                         command_callback)

        self.mon.trace(self,'')
        # and initialise things for this player        

    
        # get duration limit (secs ) from profile
        if self.track_params['duration'] != '':
            self.duration= int(self.track_params['duration'])
        else:
            self.duration= int(self.show_params['duration'])
        self.duration_limit=20*self.duration

        # process web window                  
        if self.track_params['web-window'] != '':
            self.web_window= self.track_params['web-window']
        else:
            self.web_window= self.show_params['web-window']

        # create an instance of uzbl driver
        self.bplayer=UZBLDriver(self.canvas)

        # Initialize variables
        self.command_timer=None
        self.tick_timer=None
        self.quit_signal=False     # signal that user has pressed stop
        
        # initialise the play state
        self.play_state='initialised'
        self.show_state=''
        self.load_state=''


    # LOAD - loads the browser and show stuff
    def load(self,track,loaded_callback,enable_menu):  
        # instantiate arguments
        self.track=track
        self.loaded_callback=loaded_callback   # callback when loaded
        self.mon.trace(self,'')

        # do common bits of  load
        Player.pre_load(self)
        
        #parse web window
        reason,message,command,has_window,x1,y1,x2,y2=self.parse_window(self.web_window)
        if reason == 'error':
            self.mon.err(self,'web window error: '+'  ' + message + ' in ' + self.web_window)
            self.play_state='load-failed'
            if self.loaded_callback is not  None:
                self.loaded_callback('error',message)
                return


        # compute web_window size
        if has_window is False:
            self.geometry = ' --geometry=maximized '
        else:
            width=x2-x1
            height=y2-y1
            self.geometry = "--geometry=%dx%d%+d%+d "  % (width,height,x1,y1)
            
        # parse browser commands to self.command_list
        reason,message=self.parse_commands(self.track_params['browser-commands'])
        if reason == 'error':
            self.mon.err(self,message)
            self.play_state='load-failed'
            if self.loaded_callback is not  None:
                self.loaded_callback('error',message)
                return


        # load the plugin, this may modify self.track and enable the plugin drawing to canvas
        if self.track_params['plugin'] != '':
            status,message=self.load_plugin()
            if status == 'error':
                self.mon.err(self,message)
                self.play_state='load-failed'
                if self.loaded_callback is not  None:
                    self.loaded_callback('error',message)
                    return

        # start loading the browser
        self.play_state='loading'
        self.bplayer.play(self.track,self.geometry)
        self.mon.log (self,'Loading browser from show Id: '+ str(self.show_id))

        # load the images and text
        status,message=self.load_x_content(enable_menu)
        if status == 'error':
            self.mon.err(self,message)
            self.play_state='load-failed'
            if self.loaded_callback is not  None:
                self.loaded_callback('error',message)
                return

        # wait for browser to load
        self.start_load_state_machine()


    # UNLOAD - abort a load when browser is loading or loaded
    def unload(self):
        self.mon.trace(self,'')
        self.mon.log(self,">unload received from show Id: "+ str(self.show_id))
        self.start_unload_state_machine()

         
     # SHOW - show a track from its loaded state 
    def show(self,ready_callback,finished_callback,closed_callback):
                         
        # instantiate arguments
        self.ready_callback=ready_callback         # callback when ready to show a web page- 
        self.finished_callback=finished_callback         # callback when finished showing  - not used
        self.closed_callback=closed_callback            # callback when closed

        self.mon.trace(self,'')
        
        # init state and signals  
        self.quit_signal=False

        # do common bits
        Player.pre_show(self)
        
        # start show state machine
        self.start_show_state_machine_show()


    # CLOSE - nothing to do in browserplayer - x content is removed by ready callback and hide browser does not implement pause_at_end
    def close(self,closed_callback):
        self.mon.trace(self,'')
        self.closed_callback=closed_callback
        self.mon.log(self,">close received from show Id: "+ str(self.show_id))
        self.start_show_state_machine_close()


    def input_pressed(self,symbol):
        self.mon.trace(self,symbol)
        # print symbol, symbol[0:5]
        if symbol[0:5]=='uzbl-':
            self.control(symbol[5:])
        elif symbol == 'pause':
            self.pause()
        elif symbol == 'pause-on':
            self.pause_on()
        elif symbol == 'pause-off':
            self.pause_off()
        elif symbol=='stop':
            self.stop()

    # browsers do not do pause
    def pause(self):
        self.mon.log(self,"!<pause rejected")
        return False

    # browsers do not do pause
    def pause_on(self):
        self.mon.log(self,"!<pause on rejected")
        return False

    # browsers do not do pause
    def pause_off(self):
        self.mon.log(self,"!<pauseon rejected")
        return False
        
    # other control when playing, not currently used
    def control(self,chars):
        if self.play_state == 'showing' and chars not in ('exit'):
            self.mon.log(self,"> send control to uzbl:"+ chars)
            self.bplayer.control(chars)
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

 
    def start_load_state_machine(self):
        # initialise all the state machine variables
        self.load_state='starting'
        # and start polling for state changes and count duration
        self.tick_timer=self.canvas.after(50, self.load_state_machine)


    def load_state_machine(self):
        # print self.load_state,self.play_state
        if self.load_state  in ('initialised','loaded','unloaded'):
            self.mon.log(self,"      Load state machine: " + self.load_state)
            return 
                
        elif self.load_state ==  'starting':
            # self.mon.log(self,"      Load state machine: " + self.load_state)
            
            # if uzbl fifo is available can send commands to uzbl but change to wait state to wait for it to appear on screen
            if self.bplayer.start_play_signal is True:
                self.mon.log(self,"            <fifo available signal received from uzbl" + self.bplayer.fifo)
                self.bplayer.start_play_signal=False
                self.load_state='waiting'
                # get rid of status bar
                # self.bplayer.control('set show_status = 0')
                # and get ready to wait for browser to appear
                self.wait_count= 50   # 10 seconds at 200mS steps 
                self.mon.log(self,"      State machine: uzbl process alive")
                
            self.tick_timer=self.canvas.after(200, self.load_state_machine)

        elif self.load_state == 'waiting':
            # self.mon.log(self,"      Load state machine: " + self.load_state)
            if self.wait_count==0:
                self.load_state='loaded'
                self.play_state = 'loaded'
                self.bplayer.control('set show_status = 0')
               
                # and start executing the browser commands
                self.play_commands()
                self.mon.log(self,"      State machine: uzbl loaded")
                if self.loaded_callback is not None:
                    self.loaded_callback('normal','browser loaded')
            else:
                self.wait_count -=1
                self.tick_timer=self.canvas.after(200, self.load_state_machine)


    def start_unload_state_machine(self):
        # print 'browserplayer - starting unload',self.play_state
        if self.play_state in('closed','initialised','unloaded'):
            pass
        else:
            if self.play_state  ==  'loaded':
                pass
                # load already complete
                self.unload_state_machine()
            elif self.play_state == 'loading':
                # wait for load to complete before unloading - must do this because does not respond to exit when loading
                self.tick_timer=self.canvas.after(10,self.start_unload_state_machine)
            else:
                self.mon.err(self,'illegal state in unload method ' + self.play_state)
                self.end('error','illegal state in unload method '  + self.play_state)           


    def unload_state_machine(self):
        # self.mon.log(self,"      Unload state machine: " + self.play_state)
        if self.play_state == 'unloaded':
            return 

        elif self.play_state == 'loaded':
            # service any queued stop signals and test duration count
            self.mon.log(self,"Exit browser")
            self.bplayer.stop()
            self.play_state='unloading'
            self.tick_timer=self.canvas.after(50, self.unload_state_machine)

        elif self.play_state == 'unloading':
            # self.mon.log(self,"      Unload state machine: " + self.load_state)
            # if spawned process has closed can change to closed state
            # self.mon.log (self,"      State machine : is uzbl process running? -  "  + str(self.bplayer.is_running()))
            if self.bplayer.is_running() is False:
                self.mon.log(self,"            <uzbl process is dead")
                # clean up and fifos and sockets left by uzbl
                os.system('rm -f  /tmp/uzbl_*')
                self.play_state = 'unloaded'
            else:
                self.tick_timer=self.canvas.after(50, self.unload_state_machine)
                
                


    def start_show_state_machine_show(self):
        self.play_state='showing'
        self.show_state='showing'
        self.duration_count=self.duration_limit
        self.tick_timer=self.canvas.after(50, self.show_state_machine)


    def start_show_state_machine_close(self):
        self.play_state='showing'
        self.quit_signal=True
        self.duration_limit = 0
        self.tick_timer=self.canvas.after(50, self.show_state_machine)


    def show_state_machine(self):

        if self.play_state == 'closed':
            self.mon.log(self,"      Show state machine: " + self.show_state)
            return 

        elif self.play_state == 'showing':
            self.duration_count -= 1
            # self.mon.log(self,"      Show state machine: " + self.show_state)
            
            # service any queued stop signals and test duration count
            if self.quit_signal is True or (self.duration_limit != 0 and self.duration_count == 0):
                self.mon.log(self,"      Service stop required signal or timeout")
                if self.quit_signal  is True:
                    self.quit_signal=False
                self.bplayer.stop()
                self.play_state = 'closing'
            self.tick_timer=self.canvas.after(50, self.show_state_machine)

        elif self.play_state == 'closing':
            # self.mon.log(self,"      Show state machine: " + self.show_state)
            # if spawned process has closed can change to closed state
            # self.mon.log (self,"      State machine : is uzbl process running? -  "  + str(self.bplayer.is_running()))
            if self.bplayer.is_running() is False:
                self.mon.log(self,"            <uzbl process is dead")
                # clean up and fifos and sockets left by uzbl
                os.system('rm -f  /tmp/uzbl_*')
                self.play_state = 'closed'
                if self.closed_callback is not None:
                    self.closed_callback('normal','browser closed')
            else:
                self.tick_timer=self.canvas.after(50, self.show_state_machine)
                
                


# *******************   
# browser commands
# ***********************

    def parse_commands(self,command_text):
        self.command_list=[]
        lines = command_text.split('\n')
        for line in lines:
            if line.strip() == '':
                continue
            reason,entry=self.parse_command(line)
            if reason != 'normal':
                return 'error',entry
            self.command_list.append(copy.deepcopy(entry))
        # print self.command_list
        return 'normal',''

    def parse_command(self,line):
        fields = line.split()
        if fields[0] == 'uzbl':
            # print fields[0], line[4:]
            return  'normal',[fields[0],line[4:]]
        
        if len(fields) not in (1,2):
            return 'error',"incorrect number of fields in command: " + line
        command=fields[0]
        arg=''
        if command not in ('load','refresh','wait','exit','loop'):
            return 'error','unknown command: '+ command
            
        if command in ('refresh','exit','loop') and len(fields) !=1:
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
            # self.canvas.focus_force()
            # self.root.lower()
            url=self.complete_path(arg)
            self.bplayer.control('uri '+ url)
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

        

# parse the browser window field
    def parse_window(self,line):
        # parses warp _ or xy2 or x+y*w*h
        
        fields = line.split()
        # check there is a command field
        if len(fields) < 1:
            return 'error','no type field in '+ line,'',False,0,0,0,0
            

        #deal with warp which has 1 or 5  arguments
        # check basic syntax
        if  fields[0] <>'warp':
            return 'error','not a valid type:'+ fields[0],'',False,0,0,0,0

        # deal with window coordinatesor not   
        if len(fields) == 1:
            # fullscreen
            has_window=False
            return 'normal','',fields[0],has_window,0,0,0,0
        else:
            print ' '.join(fields[1:])
            status,message,x1,y1,x2,y2 = parse_rectangle(' '.join(fields[1:]))
            if status=='error':
                return 'error',message,'',False,0,0,0,0
            else:
                has_window=True
                return 'normal','',fields[0],has_window,x1,y1,x2,y2                
            #window is specified
            




