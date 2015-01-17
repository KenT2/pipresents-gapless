from pp_artshow import ArtShow
from pp_medialist import MediaList

class ArtMediaShow(ArtShow):

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


        # delay in mS before next track is loaded after showing a track.
        # can be reduced if animation is not required
        self.load_delay = 2000
        
        # use the appropriate medialist
        self.medialist=MediaList(show_params['sequence'])
        


        
