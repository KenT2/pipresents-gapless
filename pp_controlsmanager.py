import os
import ConfigParser
import copy
from pp_utils import Monitor

class ControlsManager(object):
    config=None
    global_controls=[]


    def __init__(self):
        self.mon=Monitor()

    def get_controls(self,controls_text):
        # print 'controls text: ',controls_text
        controls_list=[]
        reason,message,show_controls=self.parse_controls(controls_text)
        # print 'show controls:',show_controls
        if reason=='error':
            return reason,message,[]
        else:
            for control in show_controls:
                controls_list.append([control[0],control[1]])
            return 'normal','controls read',controls_list

    def merge_controls(self,current_controls,track_controls):
        for track_control in track_controls:
            for control in current_controls:
                if track_control[0] ==  control[0]:
                    # link exists so overwrite
                    control[1]=track_control[1]
                    break
            else:
                # new link so append it
                current_controls.append([track_control[0],track_control[1]])
        # print "\n merging"
        # print current_controls


                                            
    #  parse controls from controls field in a show
    def parse_controls(self,controls_text):
        controls=[]
        lines = controls_text.split('\n')
        num_lines=0
        for line in lines:
            if line.strip() == '':
                continue
            num_lines+=1
            error_text,control=self.parse_control(line.strip())
            if error_text != '':
                return 'error',error_text,controls
            controls.append(copy.deepcopy(control))
        return 'normal','',controls

    def parse_control(self,line):
        fields = line.split()
        if len(fields) != 2:
            return "incorrect number of fields in control "+line,['','']
        symbol=fields[0]
        operation=fields[1]
        if operation  in ('stop','play','up','down','pause','exit','null','no-command','pause-on','pause-off','mute','unmute','go') or operation[0:4] == 'omx-' or operation[0:6] == 'mplay-'or operation[0:5] == 'uzbl-':
            return '',[symbol,operation]
        else:
            return "controls, unknown operation in\n "+ line,['','']

        

