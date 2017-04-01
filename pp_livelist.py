import os
import json
import copy
import random
import ConfigParser
import time

from pp_definitions import PPdefinitions
from pp_utils import Monitor

class LiveList(object):


    def __init__(self,sequence):
        self.mon=Monitor()
        self.sequence=sequence
        self._tracks=[]
        self._num_tracks=0
        self.last_num_tracks=-1
        

# ***************************
# Medialist Tracks
# ***************************

# medialist is kept for residual tracks with track references

    def open_list(self,filename,profile_version):
        """
        opens a saved medialist
        medialists are stored as json arrays.
        for liveshow medialist should contain only tracks with a track reference e.g. child track and empty track
        """
        ifile  = open(filename, 'rb')
        mdict = json.load(ifile)
        ifile.close()
        self.medialist_tracks = mdict['tracks']
        if 'issue' in mdict:
            self.medialist_version_string= mdict['issue']
        else:
            self.medialist_version_string="1.0"
            
        if self.medialist_version()==profile_version:
            return True
        else:
            return False

    def medialist_version(self):
        vitems=self.medialist_version_string.split('.')
        if len(vitems)==2:
            # cope with 2 digit version numbers before 1.3.2
            return 1000*int(vitems[0])+100*int(vitems[1])
        else:
            return 1000*int(vitems[0])+100*int(vitems[1])+int(vitems[2])


    # lookup index from track_ref
    def index_of_track(self,wanted_track):
        index = 0
        for track in self.medialist_tracks:
            if track['track-ref']==wanted_track:
                return index
            index +=1
        return -1

    # return dictionary of 
    def track(self,index):
        return self.medialist_tracks[index]
 


# ***************************
# Livelist Tracks
# ***************************

# the methods mirror medialist methods for anonymous tracks

    # pass live_track directories from child
    def live_tracks(self,dir1,dir2):
        self.pp_live_dir1=dir1
        self.pp_live_dir2=dir2

    def length(self):
        return self._num_tracks


##    def display_length(self):
##        self.create_new_livelist()
##        self._tracks=copy.deepcopy(self.new_livelist)
##        self._num_tracks=len(self._tracks)
##        self._selected_track_index=-1
##        return self._num_tracks

    def anon_length(self):
        return self._num_tracks        
    
    def next(self,sequence):
        if sequence=='ordered':
            if self._selected_track_index==self._num_tracks-1:
                self._selected_track_index=0
            else:
                self._selected_track_index +=1
                
            self.select(self._selected_track_index)
            return True
        else:
            cand=random.randint(0,self._num_tracks-1)
            # print '\nnext - initial cand',cand
            if len(self.played_tracks)==self._num_tracks:
                # all played so start again
                # stop same track being played twice
                if self.played_tracks[-1]==cand:
                    cand+=1
                    if cand == self._num_tracks:
                        cand=0
                self.played_tracks=[cand]
                self._selected_track_index = cand
                # print 'all played',self._selected_track_index
                # print self.played_tracks
                self.select(self._selected_track_index)
                return True
            else:
                while True:
                    # print 'trying',cand
                    if cand not in self.played_tracks:
                        self.played_tracks.append(cand)
                        self._selected_track_index = cand
                        # print 'add to played',self._selected_track_index
                        # print self.played_tracks
                        self.select(self._selected_track_index)
                        return True
                    else:
                        cand+=1
                        if cand == self._num_tracks:
                            cand=0
                        # print 'increment candidate to ',cand




    def previous(self,sequence):
        if sequence=='ordered':
            if self._selected_track_index == 0:
                self._selected_track_index=self._num_tracks-1
            else:
                self._selected_track_index -=1
            self.select(self._selected_track_index)
            return True            
        else:
            cand=random.randint(0,self._num_tracks-1)
            # print '\nprevious - initial cand',cand
            if len(self.played_tracks)==self._num_tracks:
                # all played so start again
                # stop same track being played twice
                if self.played_tracks[-1]==cand:
                    cand+=1
                    if cand == self._num_tracks:
                        cand=0
                self.played_tracks=[cand]
                self._selected_track_index = cand
                # print 'all played',self._selected_track_index
                # print self.played_tracks
                self.select(self._selected_track_index)
                return True
            else:
                while True:
                    # print 'trying',cand
                    if cand not in self.played_tracks:
                        self.played_tracks.append(cand)
                        self._selected_track_index = cand
                        # print 'add to played',self._selected_track_index
                        # print self.played_tracks
                        self.select(self._selected_track_index)
                        return True
                    else:
                        cand+=1
                        if cand == self._num_tracks:
                            cand=0
                        # print 'increment candidate to ',cand

        
    def start(self):
        if self._num_tracks==0:
            return False
        else:
            self._selected_track_index=-1
            self.played_tracks=[]
            self.next(self.sequence)
            return True

    def finish(self):
        if self._num_tracks==0:
            return False
        else:
            self._selected_track_index=self._num_tracks-1
            self.played_tracks=[]
            self.next(self.sequence)
            return True

    def at_start(self):
        if self._selected_track_index==0:
            return True
        else:
            return False

    def at_end(self):
        if self._selected_track_index==self._num_tracks-1:
            return True
        else:
            return False

    def select(self,index):
        """does housekeeping necessary when a track is selected"""
        if self._num_tracks>0 and index>=0 and index< self._num_tracks:
            self._selected_track_index=index
            self._selected_track = self._tracks[index]
            return True
        else:
            return False

    def selected_track(self):
        """returns a dictionary containing all fields in the selected track """
        return self._selected_track

  


# ***************************
# Constructing NEW Livelist
# ***************************       

    def livelist_changed(self):
        if  self.new_livelist != self._tracks:
            return True
        else:
            return False

    def new_length(self):
        return len(self.new_livelist)
    
    
    def use_new_livelist(self):
        self.last_num_tracks=self._num_tracks
        # will have only anonymous tracks
        self._tracks=copy.deepcopy(self.new_livelist)
        self._num_tracks=len(self._tracks)
        self._selected_track_index=-1
        return True


    def create_new_livelist(self):
        self.new_livelist=[]
        if os.path.exists(self.pp_live_dir1):
            for track_file in os.listdir(self.pp_live_dir1):
                track_file = self.pp_live_dir1 + os.sep + track_file
                (root_name,leaf)=os.path.split(track_file)
                if leaf[0] == '.':
                    continue
                else:
                    (root_file,ext_file)= os.path.splitext(track_file)
                    if (ext_file.lower() in PPdefinitions.IMAGE_FILES+PPdefinitions.VIDEO_FILES+PPdefinitions.AUDIO_FILES+PPdefinitions.WEB_FILES) or (ext_file.lower()=='.cfg'):
                        self.livelist_add_track(track_file)
                        
        if os.path.exists(self.pp_live_dir2):
            for track_file in os.listdir(self.pp_live_dir2):
                track_file = self.pp_live_dir2 + os.sep + track_file
                (root_name,leaf)=os.path.split(track_file)
                if leaf[0] == '.':
                    continue
                else:
                    (root_file,ext_file)= os.path.splitext(track_file)
                    if (ext_file.lower() in PPdefinitions.IMAGE_FILES+PPdefinitions.VIDEO_FILES+PPdefinitions.AUDIO_FILES+PPdefinitions.WEB_FILES) or (ext_file.lower()=='.cfg'):
                        self.livelist_add_track(track_file)
                        
        self.new_livelist= sorted(self.new_livelist, key= lambda track: os.path.basename(track['location']).lower())
        # self.print_livelist()




    def print_livelist(self):
        print 'LIVELIST'
        for it in self.new_livelist:
            print 'type: ', it['type'], 'loc: ',it['location'],'\nplugin cfg: ', it['plugin']
        print ''


        
    def livelist_add_track(self,afile):
        (root,title)=os.path.split(afile)
        (root_plus,ext)= os.path.splitext(afile)
        if ext.lower() in PPdefinitions.IMAGE_FILES:
            self.livelist_new_track(PPdefinitions.new_tracks['image'],{'title':title,'track-ref':'','location':afile})
        if ext.lower() in PPdefinitions.VIDEO_FILES:
            self.livelist_new_track(PPdefinitions.new_tracks['video'],{'title':title,'track-ref':'','location':afile})
        if ext.lower() in PPdefinitions.AUDIO_FILES:
            self.livelist_new_track(PPdefinitions.new_tracks['audio'],{'title':title,'track-ref':'','location':afile})
        if ext.lower() in PPdefinitions.WEB_FILES:
            self.livelist_new_track(PPdefinitions.new_tracks['web'],{'title':title,'track-ref':'','location':afile})
        if ext.lower()=='.cfg':
            self.livelist_new_plugin(afile,title)
           

    def livelist_new_plugin(self,plugin_cfg,title):
        # read the file which is a plugin cfg file into a dictionary
        self.plugin_config = ConfigParser.ConfigParser()
        self.plugin_config.read(plugin_cfg)
        self.plugin_params =  dict(self.plugin_config.items('plugin'))
        # create a new livelist entry of a type specified in the config file with plugin
        # miss entry if type is not  config file
        if 'type' in self.plugin_params:
            self.livelist_new_track(PPdefinitions.new_tracks[self.plugin_params['type']],{'title':title,'track-ref':'','plugin':plugin_cfg,'location':plugin_cfg})        

        
    def livelist_new_track(self,fields,values):
        new_track=fields
        self.new_livelist.append(copy.deepcopy(new_track))
        last = len(self.new_livelist)-1
        self.new_livelist[last].update(values)        
    



   
   





