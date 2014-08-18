from pp_gapshow import GapShow
from pp_medialist import MediaList

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

        # control logging
        self.mon.on()
        
        # remove comment to trace this bottom level derived class
        self.trace=True

        # use the appropriate medialist
        self.medialist=MediaList()



        
