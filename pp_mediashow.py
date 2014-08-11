from pp_gapshow import GapShow
from pp_medialist import MediaList
from pp_utils import Monitor

class MediaShow(GapShow):

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
        #self.trace=False

        
        #instantiate arguments
        self.show_id=show_id
        self.show_params =show_params
        self.showlist=showlist
        self.root=root
        self.canvas=canvas
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        # use the appropriate medialist
        self.medialist=MediaList()

        # init the common bits
        GapShow.__init__(self)




        
