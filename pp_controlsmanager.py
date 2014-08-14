import os
import ConfigParser
import copy
from pp_utils import Monitor

class ControlsManager(object):
    config=None
    global_controls=[]


    def __init__(self):
        self.mon=Monitor()
        self.mon.on()
                
    # read controls.cfg, done once in Pi Presents
    def read(self,pp_dir,pp_home,pp_profile):
        if ControlsManager.config is None:
            # try inside profile
            tryfile=pp_profile+os.sep+"controls.cfg"
            # self.mon.log(self,"Trying controls.cfg in profile at: "+ tryfile)
            if os.path.exists(tryfile):
                filename=tryfile
            else:
                # try inside pp_home
                # self.mon.log(self,"controls.cfg not found at "+ tryfile+ " trying pp_home")
                tryfile=pp_home+os.sep+"controls.cfg"
                if os.path.exists(tryfile):
                    filename=tryfile
                else:
                    # try inside pipresents
                    # self.mon.log(self,"controls.cfg not found at "+ tryfile + " trying inside pipresents")
                    tryfile=pp_dir+os.sep+'pp_home'+os.sep+"controls.cfg"
                    if os.path.exists(tryfile):
                        filename=tryfile
                    else:
                        self.mon.log(self,"controls.cfg not found at "+ tryfile)
                        self.mon.err(self,"controls.cfg not found")
                        return False   
            ControlsManager.config = ConfigParser.ConfigParser()
            ControlsManager.config.read(filename)
            self.mon.log(self,"controls.cfg read from "+ filename)
            return True


    def parse_defaults(self):
        if ControlsManager.config.has_section('controls'):
            ControlsManager.global_controls=ControlsManager.config.items('controls')
            # print 'global controls ',ControlsManager.global_controls
            return True
        else:
            return False


    # get the default controls for the show that has been read in by read from controls.cfg
    def default_controls(self):
        control_defs=ControlsManager.global_controls
        controls_list=[]
        for control_def in control_defs:
            op=control_def[1]
            default_name=control_def[0]
            controls_list.append([default_name,op])
        return controls_list


    # Merge in controls from a show.
     
    # the set of default controls for all shows can be overridden in a top level show
    # by the controls defined in the show
    # if show has an operation other than 'null' change the symbolic name to that inthe show
    # if the show has a null operation change the operation of the attached symbolic name to null
    
                                            
    def merge_show_controls(self,controls_list,show_text):
        # print 'show text: ',show_text
        reason,message,show_controls=self.parse_controls(show_text)
        # print 'show controls:',show_controls

        # overwrite the default symbolic_name if re-defined in the show
        for show_control in show_controls:
            show_name=show_control[0]
            show_operation=show_control[1]
            # find the operation in the controls list and change its name
            # print 'op to change name of: ',show_operation
            # print 'change to ',show_name
            for control in controls_list:              
                if control[1] == show_operation:
                    control[0]=show_name       
        # print 'after rename ',controls_list

        # add additional operations if defined in the show
        for show_control in show_controls:
            show_name=show_control[0]
            show_operation=show_control[1]
            # is operation in the controls list
            # print 'op to add: ',show_operation
            # print 'name to add ',show_name
            found=False
            for control in controls_list:              
                if control[1] == show_operation:
                    found=True
                    
            # if the operation has not been found and it is omx- or mplay- then add it.
            if found is False and (show_operation[0:4] == 'omx-' or show_operation[0:6] == 'mplay-'):
               #  print 'appending ', show_name,show_operation
                controls_list.append([show_name,show_operation])
                

        
        # step through controls list dealing with null
        new_controls=[]
        # find the name in controls list and delete it?
        for control in controls_list:
            name=control[0]
            operation = control [1]
            found=False
            for show_control in show_controls:
                show_name=show_control[0]
                show_operation=show_control[1]
                if show_name == name and show_operation == 'null':
                    found=True
                    break
            if found is False:
                new_controls.append(control)
                #  print 'preserved ',control
            
        # print 'merged controls',new_controls
        return new_controls              


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
            return "incorrect number of fields in control",['','']
        symbol=fields[0]
        operation=fields[1]
        if operation  in ('stop','play','up','down','pause','null') or operation[0:4] == 'omx-' or operation[0:6] == 'mplay-':
            return '',[symbol,operation]
        else:
            return "unknown operation",['','']

        

