import os
import time
from pp_artshow import ArtShow
from pp_livelist import LiveList
from pp_options import command_options

class ArtLiveShow(ArtShow):

    def __init__(self,
                 show_id,
                 show_params,
                 root,
                 canvas,
                 showlist,
                 pp_dir,
                 pp_home,
                 pp_profile,
                 command_callback):

        # init the common bits
        ArtShow.__init__(self,
                         show_id,
                         show_params,
                         root,
                         canvas,
                         showlist,
                         pp_dir,
                         pp_home,
                         pp_profile,
                         command_callback)

        # get the live tracks directories
        self.options=command_options()

    def play(self,end_callback,show_ready_callback, direction_command,level,controls_list):

        self.end_callback=end_callback

        # get the livetracks directories
        if self.show_params['live-tracks-dir1'] != '':
            self.pp_live_dir1= self.show_params['live-tracks-dir1']
        else:
            self.pp_live_dir1 = self.pp_home + os.sep + 'pp_live_tracks'
            if not os.path.exists(self.pp_live_dir1):
                os.mkdir(self.pp_live_dir1)
                
        # wait for usb stick to be mounted  when testing existence
        found=False
        for i in range (1, 10):
            self.mon.log(self,"Trying live tracks directory 1 at: " + self.pp_live_dir1)
            if os.path.exists(self.pp_live_dir1):
                found=True
                break
            time.sleep (1)
        if found is True:
            self.mon.log(self,"Found Requested live tracks Directory 1,  at: " + self.pp_live_dir1)
        else:
            self.mon.err(self,"Failed to find live tracks Directory 1"+ self.pp_live_dir1)
            self.end('error','Failed to find live tracks dir 1'+ self.pp_live_dir1)


        if self.show_params['live-tracks-dir2'] != '':
            self.pp_live_dir2= self.show_params['live-tracks-dir2']
        else:
            self.pp_live_dir2=''   
            if self.options['liveshow'] != '':
                self.pp_live_dir2 = self.options['liveshow']

        # wait for usb stick to be mounted  when testing existence                
        if self.pp_live_dir2 !='':
            found=False
            for i in range (1, 10):
                self.mon.log(self,"Trying live tracks directory 2 at: " + self.pp_live_dir2)
                if os.path.exists(self.pp_live_dir2):
                    found=True
                    break
                time.sleep (1)
            if found is True:
                self.mon.log(self,"Found Requested live tracks Directory 2,  at: " + self.pp_live_dir2)
            else:
                self.mon.err(self,"Failed to find live tracks Directory 2"+ self.pp_live_dir2)
                self.end('error','Failed to find live tracks dir 2'+ self.pp_live_dir2)
            

        # use the appropriate medialist
        self.medialist=LiveList(self.show_params['sequence'])

        # and pass directories to Livelist
        self.medialist.live_tracks(self.pp_live_dir1,self.pp_live_dir2)

        ArtShow.play(self,end_callback,show_ready_callback, direction_command,level,controls_list)
