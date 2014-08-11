import os
from pp_gapshow import GapShow
from pp_livelist import LiveList
from pp_utils import Monitor
from pp_options import command_options

class LiveShow(GapShow):

    def __init__(self,
                             show_id,
                            show_params,
                             root,
                            canvas,
                            showlist,
                             pp_dir,
                            pp_home,
                            pp_profile):

        self.mon=Monitor()
        self.mon.on()
        self.trace=True
        self.trace=False


        
        #instantiate arguments
        self.show_id=show_id
        self.show_params =show_params
        self.showlist=showlist
        self.root=root
        self.canvas=canvas
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile


        self.options=command_options()
               
        self.pp_live_dir1 = self.pp_home + os.sep + 'pp_live_tracks'
        if not os.path.exists(self.pp_live_dir1):
            os.mkdir(self.pp_live_dir1)

        self.pp_live_dir2=''   
        if self.options['liveshow'] <>"":
            self.pp_live_dir2 = self.options['liveshow']
            if not os.path.exists(self.pp_live_dir2):
                self.mon.err(self,"live tracks directory not found " + self.pp_live_dir2)
                self.end('error',"live tracks directory not found")


        # use the appropriate medialist
        self.medialist=LiveList()

        #and pass directories to livelist
        self.medialist.live_tracks(self.pp_live_dir1,self.pp_live_dir2)
        
        # init the common bits
        GapShow.__init__(self)
