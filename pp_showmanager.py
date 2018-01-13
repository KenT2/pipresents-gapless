import copy
from pp_utils import Monitor, parse_rectangle
from pp_timeofday import TimeOfDay


class ShowManager(object):
    """
    ShowManager manages PiPresents' concurrent shows. It does not manage sub-shows or child-shows but has a bit of common code to initilise them
    concurrent shows are always top level (level 0) shows:
    They can be opened/closed  by the start show(open only) or by 'open/close myshow' in the Show Control field of players, by time of day sceduler or by OSC
    
   Two shows with the same show reference cannot be run concurrently as there is no way to reference an individual instance.
   However a workaround is to make the secong instance a subshow of a mediashow with a different reference.

    """
    
    # Declare class variables
    shows=[]
    canvas=None    #canvas for all shows
    shutdown_required=False
    SHOW_TEMPLATE=['',None]
    SHOW_REF= 0   # show-reference  - name of the show as in editor
    SHOW_OBJ = 1   # the python object
    showlist=[]


    # Initialise class variables, first time through only in pipresents.py

    def init(self,canvas,all_shows_ended_callback,command_callback,showlist):
        ShowManager.all_shows_ended_callback=all_shows_ended_callback
        ShowManager.shows=[]
        ShowManager.shutdown_required=False
        ShowManager.canvas=canvas
        ShowManager.command_callback = command_callback
        ShowManager.showlist = showlist

# **************************************
# functions to manipulate show register
# **************************************

    def register_shows(self):
        for show in ShowManager.showlist.shows():
            if show['show-ref'] != 'start':
                reason,message=self.register_show(show['show-ref'])
                if reason =='error':
                    return reason,message
        return 'normal','shows regiistered'
            

    def register_show(self,ref):
        registered=self.show_registered(ref)
        if registered == -1:
            ShowManager.shows.append(copy.deepcopy(ShowManager.SHOW_TEMPLATE))
            index=len(ShowManager.shows)-1
            ShowManager.shows[index][ShowManager.SHOW_REF]=ref
            ShowManager.shows[index][ShowManager.SHOW_OBJ]=None
            self.mon.trace(self,' - register show: show_ref = ' + ref + ' index = ' + str(index))
            return'normal','show registered'
        else:
            # self.mon.err(self, ' more than one show in showlist with show-ref: ' + ref )
            return 'error', ' more than one show in showlist with show-ref: ' + ref 
        
    # is the show registered?
    # can be used to return the index to the show
    def show_registered(self,show_ref):
        index=0
        for show in ShowManager.shows:
            if show[ShowManager.SHOW_REF] == show_ref:
                return index
            index+=1
        return -1

    # needs calling program to check that the show is not already running
    def set_running(self,index,show_obj):
        ShowManager.shows[index][ShowManager.SHOW_OBJ]=show_obj
        self.mon.trace(self, 'show_ref= ' + ShowManager.shows[index][ShowManager.SHOW_REF] + ' show_id= ' + str(index))


    # is the show running?
    def show_running(self,index):
        if ShowManager.shows[index][ShowManager.SHOW_OBJ] is not None:
            return ShowManager.shows[index][ShowManager.SHOW_OBJ]
        else:
            return None

    def set_exited(self,index):
        ShowManager.shows[index][ShowManager.SHOW_OBJ]=None
        self.mon.trace(self,'show_ref= ' + ShowManager.shows[index][ShowManager.SHOW_REF] + ' show_id= ' + str(index))


    # are all shows exited?
    def all_shows_exited(self):
        all_exited=True
        for show in ShowManager.shows:
            if show[ShowManager.SHOW_OBJ] is not None:
                all_exited=False
        return all_exited


    # fromat for printing
    def pretty_shows(self):
        shows='\n'
        for show in ShowManager.shows:
            shows += show[ShowManager.SHOW_REF] +'\n'
        return shows
            
# *********************************
# show control
# *********************************

    # show manager can be initialised by a player, shower or by pipresents.py
    # if by pipresents.py then show_id=-1
    def __init__(self,show_id,showlist,show_params,root,canvas,pp_dir,pp_profile,pp_home):
        self.show_id=show_id
        self.showlist=showlist
        self.show_params=show_params
        self.root=root
        self.show_canvas=canvas
        self.pp_dir=pp_dir
        self.pp_profile=pp_profile
        self.pp_home=pp_home


        self.mon=Monitor()

    def control_a_show(self,show_ref,show_command):
        if show_command == 'open':
            return self.start_show(show_ref)
        elif show_command  == 'close':
            return self.exit_show(show_ref)
        elif show_command  == 'closeall':
            return self.exit_all_shows()
        elif show_command  == 'openexclusive':
            return self.open_exclusive(show_ref)
        else:
            return 'error','command not recognised '+ show_command

    def open_exclusive(self,show_ref):
        self.exit_all_shows()
        self.exclusive_show=show_ref
        self.wait_for_openexclusive()
        return 'normal','opened exclusive' 


    def wait_for_openexclusive(self):
        if self.all_shows_exited() is False:
            ShowManager.canvas.after(1,self.wait_for_openexclusive)
            return
        self.start_show(self.exclusive_show)
          
            

    def exit_all_shows(self):
        for show in ShowManager.shows:
            self.exit_show(show[ShowManager.SHOW_REF])
        return 'normal','exited all shows'


    # kick off the exit sequence of a show by calling the shows exit method.
    # it will result in all the shows in a stack being closed and end_play_show being called
    def exit_show(self,show_ref):
        index=self.show_registered(show_ref)
        self.mon.log(self,"De-registering show "+ show_ref + ' show index:' + str(index))
        show_obj=self.show_running(index)
        if show_obj is not None:
            self.mon.log(self,"Exiting show "+ show_ref + ' show index:' + str(index))
            show_obj.exit()
        return 'normal','exited a concurrent show'
            

    def start_show(self,show_ref):
        index=self.show_registered(show_ref)
        if index <0:
            return 'error',"Show not found in showlist: "+ show_ref
        show_index = self.showlist.index_of_show(show_ref)
        show=self.showlist.show(show_index)
        reason,message,show_canvas=self.compute_show_canvas(show)
        if reason == 'error':
            return reason,message
        # print 'STARTING TOP LEVEL SHOW',show_canvas
        self.mon.sched(self,TimeOfDay.now,'Starting Show: ' + show_ref  + ' from show: ' + self.show_params['show-ref'])
        self.mon.log(self,'Starting Show: ' + show_ref  + ' from: ' + self.show_params['show-ref'])
        if self.show_running(index):
            self.mon.sched(self,TimeOfDay.now,"show already running so ignoring command: "+show_ref)
            self.mon.warn(self,"show already running so ignoring command: "+show_ref)
            return 'normal','this concurrent show already running'
        show_obj = self.init_show(index,show,show_canvas)
        if show_obj is None:
            return 'error',"unknown show type in start concurrent show - "+ show['type']
        else:
            self.set_running(index,show_obj)
            # params - end_callback, show_ready_callback, parent_kickback_signal, level
            show_obj.play(self._end_play_show,None,False,0,[])
            return 'normal','concurrent show started'

 
    # used by shows to create subshows or child shows
    def init_subshow(self,show_id,show,show_canvas):
        return self.init_show(show_id,show,show_canvas)



    def _end_play_show(self,index,reason,message):
        show_ref_to_exit =ShowManager.shows[index][ShowManager.SHOW_REF]
        show_to_exit =ShowManager.shows[index][ShowManager.SHOW_OBJ]
        self.mon.sched(self,TimeOfDay.now,'Closed show: ' + show_ref_to_exit)
        self.mon.log(self,'Exited from show: ' + show_ref_to_exit + ' ' + str(index) )
        self.mon.log(self,'Exited with Reason = ' + reason)
        self.mon.trace(self,' Show is: ' + show_ref_to_exit + ' show index ' + str(index))
        # closes the video/audio from last track then closes the track
        # print 'show to exit ',show_to_exit, show_to_exit.current_player,show_to_exit.previous_player
        self.set_exited(index)
        if self.all_shows_exited() is True:
            ShowManager.all_shows_ended_callback(reason,message)
        return reason,message


    # common function to initilaise the show by type
    def init_show(self,show_id,selected_show,show_canvas,):
        if selected_show['type'] == "mediashow":
            return MediaShow(show_id,
                             selected_show,
                             self.root,
                             show_canvas,
                             self.showlist,
                             self.pp_dir,
                             self.pp_home,
                             self.pp_profile,
                             ShowManager.command_callback)

        elif selected_show['type'] == "liveshow":    
            return LiveShow(show_id,
                            selected_show,
                            self.root,
                            show_canvas,
                            self.showlist,
                            self.pp_dir,
                            self.pp_home,
                            self.pp_profile,
                            ShowManager.command_callback)


        elif selected_show['type'] == "radiobuttonshow":
            return RadioButtonShow(show_id,
                                   selected_show,
                                   self.root,
                                   show_canvas,
                                   self.showlist,
                                   self.pp_dir,
                                   self.pp_home,
                                   self.pp_profile,
                                   ShowManager.command_callback)

        elif selected_show['type'] == "hyperlinkshow":
            return HyperlinkShow(show_id,
                                 selected_show,
                                 self.root,
                                 show_canvas,
                                 self.showlist,
                                 self.pp_dir,
                                 self.pp_home,
                                 self.pp_profile,
                                 ShowManager.command_callback)
        
        elif selected_show['type'] == "menu":
            return MenuShow(show_id,
                            selected_show,
                            self.root,
                            show_canvas,
                            self.showlist,
                            self.pp_dir,
                            self.pp_home,
                            self.pp_profile,
                            ShowManager.command_callback)
        
        elif selected_show['type'] == "artmediashow":    
            return ArtMediaShow(show_id,
                                selected_show,
                                self.root,
                                show_canvas,
                                self.showlist,
                                self.pp_dir,
                                self.pp_home,
                                self.pp_profile,
                                ShowManager.command_callback)
        
        elif selected_show['type'] == "artliveshow":    
            return ArtLiveShow(show_id,
                               selected_show,
                               self.root,
                               show_canvas,
                               self.showlist,
                               self.pp_dir,
                               self.pp_home,
                               self.pp_profile,
                               ShowManager.command_callback)
        else:
            return None


    def compute_show_canvas(self,show_params):
        canvas={}
        canvas['canvas-obj']= ShowManager.canvas
        status,message,self.show_canvas_x1,self.show_canvas_y1,self.show_canvas_x2,self.show_canvas_y2= self.parse_show_canvas(show_params['show-canvas'])
        if status  == 'error':
            # self.mon.err(self,'show canvas error: ' + message + ' in ' + show_params['show-canvas'])
            return 'error','show canvas error: ' + message + ' in ' + show_params['show-canvas'],canvas
        else:
            self.show_canvas_width = self.show_canvas_x2 - self.show_canvas_x1
            self.show_canvas_height=self.show_canvas_y2 - self.show_canvas_y1
            self.show_canvas_centre_x= self.show_canvas_width/2
            self.show_canvas_centre_y= self.show_canvas_height/2
            canvas['show-canvas-x1'] = self.show_canvas_x1
            canvas['show-canvas-y1'] = self.show_canvas_y1
            canvas['show-canvas-x2'] = self.show_canvas_x2
            canvas['show-canvas-y2'] = self.show_canvas_y2
            canvas['show-canvas-width']  = self.show_canvas_width
            canvas['show-canvas-height'] = self.show_canvas_height
            canvas['show-canvas-centre-x'] = self.show_canvas_centre_x 
            canvas['show-canvas-centre-y'] = self.show_canvas_centre_y
            return 'normal','',canvas



    def parse_show_canvas(self,text):
        fields = text.split()
        # blank so show canvas is the whole screen
        if len(fields) < 1:
            return 'normal','',0,0,int(self.canvas['width']),int(self.canvas['height'])
             
        elif len(fields) in (1,4):
            # window is specified
            status,message,x1,y1,x2,y2=parse_rectangle(text)
            if status=='error':
                return 'error',message,0,0,0,0
            else:
                return 'normal','',x1,y1,x2,y2
        else:
            # error
            return 'error','Wrong number of fields in Show canvas: '+ text,0,0,0,0

from pp_menushow import MenuShow
from pp_liveshow import LiveShow
from pp_mediashow import MediaShow
from pp_hyperlinkshow import HyperlinkShow
from pp_radiobuttonshow import RadioButtonShow
from pp_artliveshow import ArtLiveShow
from pp_artmediashow import ArtMediaShow   



