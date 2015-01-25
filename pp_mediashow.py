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
                 pp_profile,
                 command_callback):


        # init the common bits
        GapShow.__init__(self,
                         show_id,
                         show_params,
                         root,
                         canvas,
                         showlist,
                         pp_dir,
                         pp_home,
                         pp_profile,
                         command_callback)


    def play(self,end_callback,show_ready_callback, direction_command,level,controls_list):

        # use the appropriate medialist
        self.medialist=MediaList(self.show_params['sequence'])
        
        GapShow.play(self,end_callback,show_ready_callback, direction_command,level,controls_list)

        




        
