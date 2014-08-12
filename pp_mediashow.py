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

        # init the common bits
        GapShow.__init__(self,
                         show_id,
                         show_params,
                         root,
                         canvas,
                         showlist,
                         pp_dir,
                         pp_home,
                         pp_profile)

        # use the appropriate medialist
        self.medialist=MediaList()
        
        self.trace=True
        # self.trace=False


        
