import os
import copy
import json
import string
from pp_utils import Monitor


class ShowList(object):
    """
    manages a list of show and the show selected from the showlist
    """

    def __init__(self):
        self.mon=Monitor()
        self.clear()

    def clear(self):
        self._shows = []  #MediaList, stored as a list of dicts
        self._num_shows=0
        self._selected_show_index=-1 # index of currently selected show

    def deselect_all(self):
        self._selected_show_index=-1 # index of currently selected show
        
    def print_list(self):
        print self._shows

    def length(self):
        return self._num_shows
        
    def at_end(self):
        if self._selected_show_index==self._num_shows-1:
            return True
        else:
            return False
            
    def at_start(self):
        if self._selected_show_index==0:
            return True
        else:
            return False

    def show_is_selected(self):
        if self._selected_show_index>=0:
            return True
        else:
            return False
        
    def selected_show_index(self):
        return self._selected_show_index
        
    def shows(self):
        return self._shows
        
    def show(self,index):
        return self._shows[index]
    
    def selected_show(self):
        """returns a dictionary containing all fields in the selected show """
        return self._selected_show

    def append(self, show_dict):
        """appends a show dictionary to the end of the showlist store"""
        self._shows.append(copy.deepcopy(show_dict))
        self._num_shows+=1

    def copy(self,show_dict,new_name):
        show_to_copy=copy.deepcopy(show_dict)
        show_to_copy['show-ref']=new_name
        show_to_copy['title']=new_name
        return show_to_copy

    

    def remove(self,index):
        self._shows.pop(index)
        self._num_shows-=1
        # deselect any show, saves worrying about whether index needs changing
        self._selected_show_index=-1

    def replace(self,index,replacement):
        self._shows[index]= replacement
            
    def first(self):
        self.select(0)

    def next(self):
        if self.length()>0:
            if self._selected_show_index== self.length()-1:
                index=0
            else:
                index= self._selected_show_index+1
            self.select(index)

    def previous(self):
        if self.length()>0:
            if self._selected_show_index == 0:
                index=self.length()-1
            else:
                index= self._selected_show_index-1
            self.select(index)

    def index_of_start_show(self):
        index = 0
        for show in self._shows:
            if show['type'] == 'start':
                return index
            index +=1
        return -1        
    
    def index_of_show(self,wanted_show):
        index = 0
        for show in self._shows:
            if show['type']!='start' and show['show-ref'] == wanted_show:
                return index
            index +=1
        return -1

    def select(self, index):
        """
        user clicks on a show in the Shows list so try and select it.
        """
        # needs forgiving int for possible tkinter upgrade
        self._selected_show_index=index
        self._selected_show=self._shows[index]

        
    def open_json(self,filename):
        """
        opens a saved showlistlist
        showlists are stored in files as json arrays within a object 'shows'.
        shows are stored internally as a list of dictionaries in self._shows
        """
        if filename != '' and os.path.exists(filename):
            ifile  = open(filename, 'rb')
            sdict= json.load(ifile)
            ifile.close()
            self._rawshows=sdict['shows']
            self._shows= sorted(self._rawshows, key=lambda k: k['show-ref'])
            if 'issue' in sdict:
                self.profile_version_string= sdict['issue']
            else:
                self.profile_version_string="1.0"
            self._num_shows=len(self._shows)
            self._selected_show_index=-1
            return True
        else:
            return False


    def profile_version(self):
        vitems=self.profile_version_string.split('.')
        if len(vitems)==2:
            # cope with 2 digit version numbers before 1.3.2
            return 1000*int(vitems[0])+100*int(vitems[1])
        else:
            return 1000*int(vitems[0])+100*int(vitems[1])+int(vitems[2])
        
            
    def save_list(self,filename):
        """ save a showlist """
        if filename=="":
            return False
        if os.name=='nt':
            filename = string.replace(filename,'/','\\')
        else:
            filename = string.replace(filename,'\\','/')
        dic={'issue':self.profile_version_string,'shows':self._shows}
        ofile  = open(filename, "wb")
        json.dump(dic,ofile,sort_keys=True,indent=1)
        ofile.close()
        return
            
