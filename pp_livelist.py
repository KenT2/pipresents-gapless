import os
import json
import copy
import random
import ConfigParser

from pp_definitions import PPdefinitions
from pp_utils import Monitor

class LiveList(object):

    def __init__(self,sequence):
        self.mon=Monitor()
        self.sequence=sequence

    # pass live_track direcotries from child
    def live_tracks(self,dir1,dir2):
        self.pp_live_dir1=dir1
        self.pp_live_dir2=dir2

    def open_list(self,filename,showlist_issue):
        """
        opens a saved medialist
        medialists are stored as json arrays.
        In medialists for liveshows igore any anymous tracks so length=0
        """
        ifile  = open(filename, 'rb')
        mdict = json.load(ifile)
        ifile.close()
        self._tracks = mdict['tracks']
        if 'issue' in mdict:
            self.issue= mdict['issue']
        else:
            self.issue="1.0"
        if self.issue==showlist_issue:
            self._num_tracks=0
            self._selected_track_index=-1
            return True
        else:
            return False


# ***************************
# UsingLivelist
# ***************************   

    def length(self):
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
            self._selected_track_index=random.randint(0,self._num_tracks-1)
            # print self._selected_track_index
            self.select(self._selected_track_index)
            return True
            

    def start(self):
        self.new_livelist_create()
        self._tracks = copy.deepcopy(self.new_livelist)
        self._num_tracks=len(self._tracks)
        if self._num_tracks==0:
            return False
        else:
            self._selected_track_index=-1
            self.next(self.sequence)
            return True

    def finish(self):
        self.new_livelist_create()
        self._tracks = copy.deepcopy(self.new_livelist)
        self._num_tracks=len(self._tracks)
        if self._num_tracks==0:
            return False
        else:
            self._selected_track_indexindex=self._num_tracks-1
            self.select(index)
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

    # lookup index from show_ref, return -1 because liveshow does not have child tracks.
    def index_of_track(self,show_ref):
        return -1
   
    def replace_if_changed(self):
        self.new_livelist_create()
        if  self.new_livelist != self._tracks:
            self._tracks=copy.deepcopy(self.new_livelist)
            self._num_tracks=len(self._tracks)
            self._selected_track_index=-1
            return True
        else:
            return False

# ***************************
# Constructing NEW Livelist
# ***************************       

    def new_livelist_create(self):
        self.new_livelist=[]
        if os.path.exists(self.pp_live_dir1):
            for track_file in os.listdir(self.pp_live_dir1):
                track_file = self.pp_live_dir1 + os.sep + track_file
                (root_file,ext_file)= os.path.splitext(track_file)
                if (ext_file.lower() in PPdefinitions.IMAGE_FILES+PPdefinitions.VIDEO_FILES+PPdefinitions.AUDIO_FILES) or (ext_file.lower()=='.cfg'):
                    self.livelist_add_track(track_file)
                    
        if os.path.exists(self.pp_live_dir2):
            for track_file in os.listdir(self.pp_live_dir2):
                track_file = self.pp_live_dir2 + os.sep + track_file
                (root_file,ext_file)= os.path.splitext(track_file)
                if (ext_file.lower() in PPdefinitions.IMAGE_FILES+PPdefinitions.VIDEO_FILES+PPdefinitions.AUDIO_FILES) or (ext_file.lower()=='.cfg'):
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
    



   
   





