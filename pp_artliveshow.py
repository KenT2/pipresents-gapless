import os
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
                 pp_profile):

        # init the common bits
        ArtShow.__init__(self,
                         show_id,
                         show_params,
                         root,
                         canvas,
                         showlist,
                         pp_dir,
                         pp_home,
                         pp_profile)

        # control the debugging log
        self.mon.on()

        # uncomment to turn trace on 
        self.trace=True

        # delay in mS before next track is loaded after showing a track.
        # can be reduced if animation is not required
        self.load_delay = 2000

        # get the live tracks directories
        self.options=command_options()
               
        self.pp_live_dir1 = self.pp_home + os.sep + 'pp_live_tracks'
        if not os.path.exists(self.pp_live_dir1):
            os.mkdir(self.pp_live_dir1)

        self.pp_live_dir2=''   
        if self.options['liveshow']  != '':
            self.pp_live_dir2 = self.options['liveshow']
            if not os.path.exists(self.pp_live_dir2):
                self.mon.err(self,"live tracks directory not found " + self.pp_live_dir2)
                self.end('error',"live tracks directory not found")
       
        # use the appropriate medialist
        self.medialist=LiveList(show_params['sequence'])

        # and pass directories to Livelist
        self.medialist.live_tracks(self.pp_live_dir1,self.pp_live_dir2)


