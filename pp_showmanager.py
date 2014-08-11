import os
import sys
import copy
from pp_utils import Monitor


class ShowManager:
    
# ShowManager manages PiPresents' concurrent shows. It does not manage sub-shows or child-shows.
# concurrent shows are always top level (level 0 shows:
# They can be started by the start show or by 'myshow start' in the Show Control field of players
# They can be stopped either by 'myshow stop' in the Show Control field in players

# a show with the same reference should not be run twice as there is no way to reference an individual instance when stopping
# ??? this could be changed as there is single-run to stop them, the stop command could stop all instances.

# Declare class variables
    shows=[]
    shutdown_required=False
    SHOW_TEMPLATE=['',None]
    SHOW_REF= 0   # show-reference  - name of the show as in editor
    SHOW_OBJ = 1   # the python object


# Initialise, first time through only in pipresents.py

    def init(self,all_shows_ended_callback):
        ShowManager.all_shows_ended_callback=all_shows_ended_callback
        ShowManager.shows=[]
        ShowManager.shutdown_required=False

# **************************************
# functions to manipulate show register
# **************************************

#adds a new concurrent show to the register if not already there, returns an index for use by start and stop

    def register_show(self,ref):
        registered=self.show_registered(ref)
        if registered==-1:
            ShowManager.shows.append(copy.deepcopy(ShowManager.SHOW_TEMPLATE))
            index=len(ShowManager.shows)-1
            ShowManager.shows[index][ShowManager.SHOW_REF]=ref
            ShowManager.shows[index][ShowManager.SHOW_OBJ]=None
            if self.trace: print 'showmanager/register_show  new show: show_ref=',ref,' show_id=',index
            return index
        else:
            if self.trace: print 'showmanager/register_show show exists: show_ref=',ref,' show_id=',registered
            return registered
        
# is the show registered?
# can be used to return the index to the show
    def show_registered(self,show_ref):
        index=0
        for show in ShowManager.shows:
            if show[ShowManager.SHOW_REF]==show_ref:
                return index
            index+=1
        return -1

# needs calling program to check that the show is not already running
    def set_running(self,index,show_obj):
        ShowManager.shows[index][ShowManager.SHOW_OBJ]=show_obj
        if self.trace: print 'showmanager/set_running: show_ref=',ShowManager.shows[index][ShowManager.SHOW_REF],' show_id=',index
        if self.trace: print 'concurrent shows:', ShowManager.shows

# is the show running?
    def show_running(self,index):
        if ShowManager.shows[index][ShowManager.SHOW_OBJ]<>None:
                return ShowManager.shows[index][ShowManager.SHOW_OBJ]
        else:
            return None

    def set_stopped(self,index):
        ShowManager.shows[index][ShowManager.SHOW_OBJ]=None
        if self.trace: print 'showmanager/set_stopped: show_ref=',ShowManager.shows[index][ShowManager.SHOW_REF],' show_id=',index
        if self.trace: print 'concurrent shows:', ShowManager.shows


# are all shows stopped?
    def all_shows_stopped(self):
        all_stopped=True
        for show in ShowManager.shows:
            if show[ShowManager.SHOW_OBJ]<>None:
                all_stopped=False
        return all_stopped


# *********************************
# show control
# *********************************

    #show manager can be initialised by a player, shower or by pipresents.py
    # if by pipresents.py then show_id=-1
    def __init__(self,show_id,showlist,show_params,root,canvas,pp_dir,pp_profile,pp_home):
        self.show_id=show_id
        self.showlist=showlist
        self.show_params=show_params
        self.root=root
        self.canvas=canvas
        self.pp_dir=pp_dir
        self.pp_profile=pp_profile
        self.pp_home=pp_home


        self.mon=Monitor()
        self.mon.on()

        self.trace=True
        self.trace=False

# control initial shows from PiPresents so command is always start

    def start_initial_shows(self,start_shows_text):
        show_refs= start_shows_text.split()
        fields=['','']
        for show_ref in show_refs:
            fields[0]=show_ref
            fields[1]='start'
            reason,message=self.control_a_show(fields)
            if reason<>'normal':
                return reason,message
        #no shows started
        return 'normal',''
            

# Control shows from Players so need to handle start and stop commands
    def show_control(self,show_control_text): 
        lines = show_control_text.split('\n')
        for line in lines:
            if line.strip()=="":
                continue
            fields= line.split()
            #control a show and return its ending reason
            # print 'show control fields: ',fields
            reason,message=self.control_a_show(fields)
            if reason<>'normal':
                return reason,message
        #all commands done OK
        return 'normal',''


    def control_a_show(self,fields):
            show_ref=fields[0]
            show_command=fields[1]
            if show_command=='start':
                return self.start_show(show_ref)
            elif show_command =='stop':
                return self.stop_show(show_ref)
            elif show_command=='exit':
                return self.stop_all_shows()
            elif show_command=='shutdownnow':
                ShowManager.shutdown_required=True
                return self.stop_all_shows()
            else:
                return 'error','command not recognised '+ show_command

    def stop_show(self,show_ref):
        index=self.show_registered(show_ref)
        self.mon.log(self,"Stopping show "+ show_ref + ' show index:' + str(index))
        show_obj=self.show_running(index)
        if show_obj<>None:
            show_obj.managed_stop()
        return 'normal','stopped a concurrent show'
            

    def stop_all_shows(self):
        for show in ShowManager.shows:
            self.stop_show(show[ShowManager.SHOW_REF])
        return 'normal','stopped all shows'


    def start_show(self,show_ref):
            show_index = self.showlist.index_of_show(show_ref)
            if show_index <0:
                return 'error',"Show not found in showlist: "+ show_ref
            
            show=self.showlist.show(show_index)
            index=self.register_show(show_ref)
            self.mon.log(self,'Starting Show from: ' + self.show_params['show-ref']+ ' '+ str(self.show_id)+" show_ref:"+ show_ref + ' show_id' + str(index) )
            if self.show_running(index):
                self.mon.log(self,"show already running "+show_ref)
                return 'normal','this concurrent show already running'
            
            if show['type']=="mediashow":
                show_obj = MediaShow(index,
                                                                 show,
                                                                 self.root,
                                                                self.canvas,
                                                                self.showlist,
                                                                 self.pp_dir,
                                                                self.pp_home,
                                                                self.pp_profile)
                self.set_running(index,show_obj)
                # params - end_callback, show_ready_callback, direction_command, level
                show_obj.play(self._end_play_show,None,'nil',0)
                return 'normal','concurrent show started'

            if show['type']=="radiobuttonshow":
                show_obj = RadioButtonShow(index,show,
                                                               self.root,
                                                                self.canvas,
                                                                self.showlist,
                                                               self.pp_dir,
                                                                self.pp_home,
                                                                self.pp_profile)
                self.set_running(index,show_obj)
                show_obj.play(self._end_play_show,None,'nil',0)
                return 'normal','concurrent show started'
 
            if show['type']=="hyperlinkshow":
                show_obj = HyperlinkShow(index,show,
                                                                 self.root,
                                                                self.canvas,
                                                                self.showlist,
                                                                 self.pp_dir,
                                                                self.pp_home,
                                                                self.pp_profile)
                self.set_running(index,show_obj)
                show_obj.play(self._end_play_show,None,'nil',0)
                return 'normal','concurrent show started'
            
            elif show['type']=="menu":
                show_obj = MenuShow(index,show,
                                                        self.root,
                                                        self.canvas,
                                                        self.showlist,
                                                        self.pp_dir,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.set_running(index,show_obj)
                show_obj.play(self._end_play_show,None,'nil',0)
                return 'normal','concurrent show started'

            elif show['type']=="liveshow":
                show_obj= LiveShow(index,show,
                                                        self.root,
                                                        self.canvas,
                                                        self.showlist,
                                                       self.pp_dir,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.set_running(index,show_obj)
                show_obj.play(self._end_play_show,None,'nil',0)
                return 'normal','concurrent show started'

            elif show['type']=="artliveshow":
                show_obj= ArtLiveShow(index,show,
                                                        self.root,
                                                        self.canvas,
                                                        self.showlist,
                                                       self.pp_dir,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.set_running(index,show_obj)
                show_obj.play(self._end_play_show,None,'nil',0)
                return 'normal','concurrent show started'

            elif show['type']=="artmediashow":
                show_obj= ArtMediaShow(index,show,
                                                        self.root,
                                                        self.canvas,
                                                        self.showlist,
                                                       self.pp_dir,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.set_running(index,show_obj)
                show_obj.play(self._end_play_show,None,'nil',0)
                return 'normal','concurrent show started'
            else:
                return 'error',"unknown show type in start concurrent show - "+ show['type']


    def _end_play_show(self,index,reason,message):
        self.mon.log(self,'Closing Show from: ' + self.show_params['show-ref']+ ' '+ str(self.show_id)+" show_ref:" + ShowManager.shows[index][ShowManager.SHOW_REF] + ' show_id:' + str(index) )
        self.mon.log(self,'      Reason and message: ' + reason+ message)
        if self.trace: print 'showmanager/_end_play_show Show is: ',ShowManager.shows[index][ShowManager.SHOW_REF] , ' show index ', index
        self.set_stopped(index)
        if self.all_shows_stopped()==True:
            ShowManager.all_shows_ended_callback('normal','All shows ended',ShowManager.shutdown_required)
        return reason,message



    # used by shows to create subshows or child shows
    def init_selected_show(self,selected_show):
        if selected_show['type']=="mediashow":    
            return MediaShow(self.show_id,
                                                            selected_show,                                      
                                                           self.root,
                                                            self.canvas,
                                                            self.showlist,
                                                           self.pp_dir,
                                                            self.pp_home,
                                                            self.pp_profile)

        elif selected_show['type']=="liveshow":    
           return LiveShow(self.show_id,
                                                            selected_show,
                                                            self.root,
                                                            self.canvas,
                                                            self.showlist,
                                                            self.pp_dir,
                                                            self.pp_home,
                                                            self.pp_profile)


        elif selected_show['type']=="radiobuttonshow":
            return RadioButtonShow(self.show_id,
                                                    selected_show,
                                                     self.root,
                                                    self.canvas,
                                                    self.showlist,
                                                    self.pp_dir,
                                                    self.pp_home,
                                                    self.pp_profile)

        elif selected_show['type']=="hyperlinkshow":
            return HyperlinkShow(self.show_id,
                                                    selected_show,
                                                   self.root,
                                                    self.canvas,
                                                    self.showlist,
                                                   self.pp_dir,
                                                    self.pp_home,
                                                    self.pp_profile)
        
        elif selected_show['type']=="menu":
            return MenuShow(self.show_id,
                                                    selected_show,
                                                    self.root,
                                                    self.canvas,
                                                    self.showlist,
                                                      self.pp_dir,
                                                    self.pp_home,
                                                    self.pp_profile)
        
        elif selected_show['type']=="artmediashow":    
            return ArtMediaShow(self.show_id,
                                                            selected_show,                                      
                                                           self.root,
                                                            self.canvas,
                                                            self.showlist,
                                                           self.pp_dir,
                                                            self.pp_home,
                                                            self.pp_profile)
        
        elif selected_show['type']=="artliveshow":    
            return ArtLiveShow(self.show_id,
                                                            selected_show,                                      
                                                           self.root,
                                                            self.canvas,
                                                            self.showlist,
                                                           self.pp_dir,
                                                            self.pp_home,
                                                            self.pp_profile)
        else:
            return None


from pp_menushow import MenuShow
from pp_liveshow import LiveShow
from pp_mediashow import MediaShow
from pp_hyperlinkshow import HyperlinkShow
from pp_radiobuttonshow import RadioButtonShow
from pp_artliveshow import ArtLiveShow
from pp_artmediashow import ArtMediaShow   



