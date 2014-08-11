from Tkinter import *
import Tkinter as tk
import tkFileDialog
import tkMessageBox
import tkSimpleDialog
import tkFont
import os
import json


class Validator:

    def validate_profile(self, root, pp_dir, pp_home, pp_profile,editor_issue,display):

        # USES
        # self.current_showlist

        # CREATES
        # v_media_lists - file names of all medialists in the profile
        # v_shows
        # v_track_labels - list of track labels in current medialist.
        # v_show_labels - list of show labels in the showlist
        # v_medialist_refs - list of references to medialist files in the showlist

            # open results display
            self.result=ResultWindow(root,"Validate "+pp_profile,display)
            self.result.display('t',"\nVALIDATING PROFILE '"+ pp_profile + "'")

            if not  os.path.exists(pp_profile+os.sep+"pp_showlist.json"):
                self.result.display('f',"pp_showlist.json not in profile")
                self.result.display('t', "Validation Aborted")
                return False                   
            ifile  = open(pp_profile+os.sep+"pp_showlist.json", 'rb')
            sdict= json.load(ifile)
            ifile.close()
            v_shows=sdict['shows']
            if 'issue' in sdict:
                profile_issue= sdict['issue']
            else:
                profile_issue="1.0"
                          
            if profile_issue <> editor_issue:
                self.result.display('f',"Profile version "+profile_issue+ " is different to that editor")
                self.result.display('t', "Validation Aborted")
                return False                                            
            
            # read the gpio config
            # gpio_cfg_ok=read_gpio_cfg(pp_dir,pp_home,pp_profile)
                
                
            # MAKE LIST OF SHOW LABELS
            v_show_labels=[]
            for show in v_shows:
                if show['type']<>'start': v_show_labels.append(show['show-ref'])

            # CHECK ALL MEDIALISTS AND THEIR TRACKS
            v_media_lists = []
            for file in os.listdir(pp_profile):
                if not file.endswith(".json") and file not in ('gpio.cfg','controls.cfg','screen.cfg','keys.cfg','resources.cfg'):
                    self.result.display('f',"Invalid medialist in profile: "+ file)
                    self.result.display('t', "Validation Aborted")
                    return False
                    
                if file.endswith(".json") and file<>'pp_showlist.json':
                    self.result.display('t',"\nChecking medialist '"+file+"'")
                    v_media_lists.append(file)

                    #open a medialist and test its tracks
                    ifile  = open(pp_profile + os.sep + file, 'rb')
                    sdict= json.load(ifile)
                    ifile.close()                          
                    tracks = sdict['tracks']
                    if 'issue' in sdict:
                        medialist_issue= sdict['issue']
                    else:
                        medialist_issue="1.0"
                          
                    # check issue of medialist      
                    if medialist_issue <> editor_issue:
                        self.result.display('f',"Medialist version "+medialist_issue+ " is different to that editor")
                        self.result.display('t', "Validation Aborted")
                        return False

                    #open a medialist and test its tracks
                    v_track_labels=[]
                    anonymous=0
                    for track in tracks:
                        self.result.display('t',"    Checking track '"+track['title']+"'")
                        
                        # check track-ref
                        if track['track-ref']=='':
                            anonymous+=1
                        else:
                            v_track_labels.append(track['track-ref'])
                            if track['track-ref']=='pp-child-show' and track['type']<>'show': self.result.display('f',"pp-child-show track is not a show")
                            if track['track-ref']=='pp-menu-background' and track['type']<>'menu-background': self.result.display('f',"pp-menu-background track is not a 'menu-background'")
                        
                        # check media tracks not blank where mandatory
                        if track['type'] in ('menu-background'):
                            if track['location'].strip()=='':
                                self.result.display('f',"blank location")

                        # warn if media tracks blank  where optional
                        if track['type'] in ('audio','image','web','video'):
                            if track['location'].strip()=='':
                                self.result.display('w',"blank location")
                        
                        # check location of relative media tracks where present                   
                        if track['type'] in ('video','audio','image','menu-background','web'):    
                            track_file=track['location']
                            if track_file.strip()<>'' and  track_file[0]=="+":
                                    track_file=pp_home+track_file[1:]
                                    if not os.path.exists(track_file): self.result.display('f',"location "+track['location']+ " media file not found")

                        if track['type'] in ('video','audio','message','image','web'):
                            # check common fields
                            self.check_animate('animate-begin',track['animate-begin'])
                            self.check_animate('animate-end',track['animate-end'])
                            self.check_plugin(track['plugin'],pp_home)
                            self.check_show_control(track['show-control-begin'],v_show_labels)
                            self.check_show_control(track['show-control-end'],v_show_labels)
                            if track['background-image']<>'':
                                track_file=track['background-image']
                                if track_file[0]=="+":
                                    track_file=pp_home+track_file[1:]
                                    if not os.path.exists(track_file): self.result.display('f',"background-image "+track['background-image']+ " background image file not found")                                

                            
                        # Check simple fields                        
                        if track['type']=="image":
                            if track['duration']<>"" and not track['duration'].isdigit(): self.result.display('f',"'duration' is not blank, 0 or a positive integer")
                            if track['track-text']<>"":
                                if not track['track-text-x'].isdigit(): self.result.display('f',"'track-text-x' is not 0 or a positive integer")
                                if not track['track-text-y'].isdigit(): self.result.display('f',"'track-text-y' is not 0 or a positive integer")
                            self.check_image_window('track','image-window',track['image-window'])


                        if track['type']=="video":
                            if track['track-text']<>"":
                                if not track['track-text-x'].isdigit(): self.result.display('f',"'track-text-x' is not 0 or a positive integer")
                                if not track['track-text-y'].isdigit(): self.result.display('f',"'track-text-y' is not 0 or a positive integer")
                            self.check_omx_window('track','omx-window',track['omx-window'])
                            self.check_volume('track','omxplayer-volume',track['omx-volume'])
                                
                        if track['type'] == "audio":
                            if track['duration']<>'' and not track['duration'].isdigit(): self.result.display('f',"'duration' is not 0 or a positive integer")
                            if track['duration']=='0' : self.result.display('w',"'Duration' of an audio track is zero")
                            if track['track-text']<>"":
                                if not track['track-text-x'].isdigit(): self.result.display('f',"'track-text-x' is not 0 or a positive integer")
                                if not track['track-text-y'].isdigit(): self.result.display('f',"'track-text-y' is not 0 or a positive integer")
                                self.check_volume('track','mplayer-volume',track['mplayer-volume'])
                            
                        if track['type']=="message":
                            if track['duration']<>'' and not track['duration'].isdigit(): self.result.display('f',"'duration' is not 0 or a positive integer")
                            if track['text']<>"":
                                if track['message-x']<>'' and not track['message-x'].isdigit(): self.result.display('f',"'message-x' is not blank, 0 or a positive integer")
                                if track['message-y']<>'' and not track['message-y'].isdigit(): self.result.display('f',"'message-y' is not blank, 0 or a positive integer")
                                
                        if track['type']=='web':
                            self.check_browser_commands(track['browser-commands'])
                            self.check_web_window('track','web-window',show['web-window'])
  
                      
                        # CHECK CROSS REF TRACK TO SHOW
                        if track['type'] == 'show':
                                if track['sub-show']=="":
                                    self.result.display('f',"No 'Show to Run'")
                                else:
                                    if track['sub-show'] not in v_show_labels: self.result.display('f',"show "+track['sub-show'] + " does not exist")
                                
                    # if anonymous == 0 :self.result.display('w',"zero anonymous tracks in medialist " + file)

                    # check for duplicate track-labels
                    # !!!!!!!!!!!!!!!!!! add check for all labels
                    if v_track_labels.count('pp-menu-background') >1: self.result.display('f', "more than one pp-menu-background")
                    if v_track_labels.count('pp-child-show') >1: self.result.display('f', "more than one pp-child-show")

            # SHOWS
            # find start show and test it, test show-refs at the same time
            found=0
            for show in v_shows:
                if show['type']=='start':
                    self.result.display('t',"\nChecking show '"+show['title'] + "' first pass")
                    found+=1
                    if show['show-ref']<> 'start': self.result.display('f',"start show has incorrect label")
                else:
                    self.result.display('t',"Checking show '"+show['title'] + "' first pass")
                    if show['show-ref']=='': self.result.display('f',"show-ref is blank")
                    if ' ' in show['show-ref']: self.result.display('f',"Spaces not allowed in show-ref " + show['show-ref'])
                    
            if found == 0:self.result.display('f',"There is no start show")
            if found > 1:self.result.display('f',"There is more than 1 start show")    


            # check for duplicate show-labels
            for show_label in v_show_labels:
                found = 0
                for show in v_shows:
                    if show['show-ref']==show_label: found+=1
                if found > 1: self.result.display('f',show_label + " is defined more than once")
                
            # check other things about all the shows and create a list of medialist file references
            v_medialist_refs=[]
            for show in v_shows:
                if show['type']=="start":
                    self.result.display('t',"\nChecking show '"+show['title']+ "' second pass" )
                    self.check_start_shows(show,v_show_labels)               
                else:
                    self.result.display('t',"Checking show '"+show['title']+ "' second pass" )
                    
                    if '.json' not in show['medialist']:
                        self.result.display('f', show['show-ref']+ " show has invalid medialist")
                        self.result.display('t', "Validation Aborted")
                        return False

                    if show['medialist'] not in v_media_lists:
                        self.result.display('f', "'"+show['medialist']+ "' medialist not found")
                        self.result.display('t', "Validation Aborted")
                        return False

                    if not os.path.exists(pp_profile + os.sep + show['medialist']):
                        self.result.display('f', "'"+show['medialist']+ "' medialist file does not exist")
                        self.result.display('t', "Validation Aborted")
                        return False
                        
                    v_medialist_refs.append(show['medialist'])
                    
                    # check common fields    
                    if show['show-text']<>"":
                            if not show['show-text-x'].isdigit(): self.result.display('f',"'show-text-x' is not 0 or a positive integer")
                            if not show['show-text-y'].isdigit(): self.result.display('f',"'show-text-y' is not 0 or a positive integer")
                    if not show['duration'].isdigit(): self.result.display('f',"'duration' is not 0 or a positive integer")
                    background_image_file=show['background-image']
                    if background_image_file.strip()<>'' and  background_image_file[0]=="+":
                            track_file=pp_home+background_image_file[1:]
                            if not os.path.exists(track_file): self.result.display('f',"location "+show['background-image']+ " background image file not found")
                    self.check_volume('show','omx-volume',show['omx-volume'])
                    self.check_volume('show','mplayer-volume',show['mplayer-volume'])
                    self.check_omx_window('show','omx-window',show['omx-window'])
                    self.check_image_window('show','image-window',show['image-window'])
                    self.check_web_window('show','web-window',show['web-window'])
                    self.check_controls('controls',show['controls'])


                    # Validate simple fields of show
                    if show['type']=="mediashow":
                            if show['has-child']=='yes':
                                if not show['hint-y'].isdigit(): self.result.display('f',"'hint-y' is not 0 or a positive integer")
                            if show['repeat']=='interval' and not show['repeat-interval'].isdigit(): self.result.display('f',"'repeat-interval' is not 0 or a positive integer")
                            if show['trigger']in('input','input-quiet'):
                                self.check_triggers('trigger',show['trigger-input'])
                            elif show['trigger']in('time','time-quiet'):
                                self.check_times(show['trigger-input'])
                            if show['trigger-next']=='input':
                                self.check_triggers('trigger-next',show['next-input'])
                            if show['trigger-end']=='time':
                                self.check_times(show['trigger-end-time'])
                            if show['trigger-end']=='duration':
                                self.check_end_duration(show['trigger-end-time'])

                                
                    if show['type']=="menu":
                            if not show['timeout'].isdigit(): self.result.display('f',"'timeout' is not 0 or a positive integer")
                            if not show['hint-x'].isdigit(): self.result.display('f',"'hint-x' is not 0 or a positive integer")
                            if not show['hint-y'].isdigit(): self.result.display('f',"'hint-y' is not 0 or a positive integer")


                    if show['type']=="liveshow":
                            if show['has-child']=='yes':
                                if not show['hint-y'].isdigit(): self.result.display('f',"'hint-y' is not 0 or a positive integer")
                            if show['trigger-start']in ('time','time-quiet'):
                                self.check_times(show['trigger-start-time'])
                            if show['trigger-end']=='time':
                                self.check_times(show['trigger-end-time'])
                            if show['trigger-end']=='duration':
                                self.check_end_duration(show['trigger-end-time'])


                    if show['type']=='hyperlinkshow':
                            # validate first, home, timeout track???????
                            self.check_links('links',show['links'])
                            if not show['timeout'].isdigit(): self.result.display('f',"'timeout' is not 0 or a positive integer")

                    if show['type']=='radiobuttonshow':
                            # validate first track??????????
                            self.check_button_links('links',show['links'])
                            if not show['timeout'].isdigit(): self.result.display('f',"'timeout' is not 0 or a positive integer")


        
               # CHECK CROSS REF SHOW TO TRACK
                    ifile  = open(pp_profile + os.sep + show['medialist'], 'rb')
                    tracks = json.load(ifile)['tracks']
                    ifile.close()
                    
                     # make a list of the track labels
                    v_track_labels=[]
                    for track in tracks:
                        if track['track-ref'] in ('pp-menu-background','pp-child-show'):
                            v_track_labels.append(track['track-ref'])
                            
                    if show['type']in('mediashow','liveshow') and show['has-child']=='yes':
                        if 'pp-child-show' not in v_track_labels: self.result.display('f'," pp-child-show track missing in medialist "+show['medialist'])
                    if show['type']=='menu' and show['has-background']=='yes':
                         if 'pp-menu-background' not in v_track_labels: self.result.display('f', " pp-menu-background track missing in medialist "+show['medialist'])

            self.result.display('t', "\nValidation Complete")
            self.result.stats()
            if self.result.num_errors() == 0:
                return True
            else:
                return False
 
 
    def check_start_shows(self,show,v_show_labels):
        text=show['start-show']
        show_count=0
        fields = text.split()
        for field in fields:
                show_count+=1
                if field not in v_show_labels:
                    self.result.display('f',"start show has undefined start-show: "+ field)
        if show_count==0:
            self.result.display('f',"start show has zero start-shows")


# ***********************************
# triggers
# ************************************ 

    def check_triggers(self,field,line):
        words=line.split()
        if len(words)!=1: self.result.display('f','Wrong number of fields in: ' + field + ", " + line)

# ***********************************
# volume
# ************************************ 

    def check_volume(self,type,field,line):
        if type=='show' and line.strip()=='':
                self.result.display('f','Wrong number of fields: ' + field + ", " + line)
                return
        if type=='track' and line.strip()=='':
            return
        if line[0] not in ('0','-'):
            self.result.display('f','Invalid value: ' + field + ", " + line)
            return
        if line[0]== '0':
            if not line.isdigit():
                self.result.display('f','Invalid value: ' + field + ", " + line)
                return
            if int(line)<>0:
                self.result.display('f','out of range -60 > 0: ' + field + ", " + line)
                return
            return
            
        elif line[0]=='-':
            if not line[1:].isdigit():
                self.result.display('f','Invalid value: ' + field + ", " + line)
                return
            if int(line)<-60 or int(line)>0:
                self.result.display('f','out of range -60 > 0: ' + field + ", " + line)
                return
            return
        
        else:
                self.result.display('f','help, do not understaand!: ' + field + ", " + line)
                return        
        
            

# ***********************************
# time of day inputs
# ************************************ 

    def check_times(self,text):
        lines = text.split("\n")
        for line in lines:
            error_text=self.check_times_line(line)
            
    def check_times_line(self,line):
        items = line.split()
        if len(items)==0: self.result.display('w','No time values when using time of day trigger: ')
        for item in items:
            self.check_times_item(item)

    def check_times_item(self,item):
        if item[0]=='+':
            if not item.lstrip('+').isdigit():
                self.result.display('f','Value of relative time is not positive integer: ' + item)
                return
        else:
            #hh:mm;ss
            fields=item.split(':')
            if len(fields)==0:
                return
            if len(fields)==1:
                 self.result.display('f','Too few fields in time: ' + item)
                 return
            if len(fields)>3:
                 self.result.display('f','Too many fields in time: ' + item)
                 return
            if len(fields)<>3:
                seconds='0'
            else:
                seconds=fields[2]
            if not fields[0].isdigit() or not  fields[1].isdigit() or  not seconds.isdigit():
                self.result.display('f','Fields of time are not positive integers: ' + item)
                return        
            if int(fields[0])>23 or int(fields[1])>59 or int(seconds)>59:
             self.result.display('f','Fields of time are out of range: ' + item)
             return
             
    def check_end_duration(self,line):          
        fields=line.split(':')
        if len(fields)==0:
            self.result.display('f','End Trigger, Duration: Field is empty: ' + line)
            return
        if len(fields)>3:
            self.result.display('f','End Trigger, Duration: More then 3 fields: ' + line)
            return
        if len(fields)==1:
            secs=fields[0]
            minutes='0'
            hours='0'
        if len(fields)==2:
            secs=fields[1]
            minutes=fields[0]
            hours='0'
        if len(fields)==3:
            secs=fields[2]
            minutes=fields[1]
            hours=fields[0]
        if not hours.isdigit() or not  minutes.isdigit() or  not secs.isdigit():
            self.result.display('f','End Trigger, Duration: Fields are not positive integers: ' + line)
            return
        
        if int(hours)>23 or int(minutes)>59 or int(secs)>59:
             self.result.display('f','End Trigger, Duration: Fields are out of range: ' + line)
             return

# *******************   
# Check menu
# ***********************               
# window
# consistencty of modes
        
    def check_menu(self,show):

        if not show['menu-rows'].isdigit(): self.result.display('f'," Menu Rows is not 0 or a positive integer")
        if not show['menu-columns'].isdigit(): self.result.display('f'," Menu Columns is not 0 or a positive integer")     
        if not show['menu-icon-width'].isdigit(): self.result.display('f'," Icon Width is not 0 or a positive integer") 
        if not show['menu-icon-height'].isdigit(): self.result.display('f'," Icon Height is not 0 or a positive integer")
        if not show['menu-horizontal-padding'].isdigit(): self.result.display('f'," Horizontal Padding is not 0 or a positive integer")
        if not show['menu-vertical-padding'].isdigit(): self.result.display('f'," Vertical padding is not 0 or a positive integer") 
        if not show['menu-text-width'].isdigit(): self.result.display('f'," Text Width is not 0 or a positive integer") 
        if not show['menu-text-height'].isdigit(): self.result.display('f'," Text Height is not 0 or a positive integer")
        if not show['menu-horizontal-separation'].isdigit(): self.result.display('f'," Horizontal Separation is not 0 or a positive integer") 
        if not show['menu-vertical-separation'].isdigit(): self.result.display('f'," Vertical Separation is not 0 or a positive integer")
        if not show['menu-strip-padding'].isdigit(): self.result.display('f'," Stipple padding is not 0 or a positive integer")    

        if not show['menu-text-x'].isdigit(): self.result.display('f'," Menu Text x is not 0 or a positive integer") 
        if not show['menu-text-y'].isdigit(): self.result.display('f'," Menu Text y is not 0 or a positive integer")

        if self.show['menu-icon-mode']=='none' and self.show['menu-text-mode']=='none':
            self.result.display('f'," Icon and Text are both None") 

        if self.show['menu-icon-mode']=='none' and self.show['menu-text-mode']=='overlay':
            self.result.display('f'," cannot overlay none icon") 
            
        self.check_menu_window(show['menu-window'])

    def check_menu_window(self,line):
        if line =='':
            self.result.display('f'," menu Window: may noot be blank")
            return
        
        if line<>'':
            fields = line.split()
            if len(fields) not in  (1, 2,4):
                self.result.display('f'," menu Window: wrong number of fields") 
                return
            if len(fields)==1:
                if fields[0]<>'fullscreen':
                    self.result.display('f'," menu Window: single argumetn must be fullscreen")
                    return
            if len(fields)==2:                    
                if not (fields[0].isdigit() and fields[1].isdigit()):
                    self.result.display('f'," menu Window: coordinates must be positive integers")
                    return
                    
            if len(fields)==4:                    
                if not(fields[0].isdigit() and fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit()):
                    self.result.display('f'," menu Window: coordinates must be positive integers")
                    return




             
             
# *******************   
# Check plugin
# ***********************             
             
    def check_plugin(self,plugin_cfg,pp_home):
        if plugin_cfg.strip()<>'' and  plugin_cfg[0]=="+":
            plugin_cfg=pp_home+plugin_cfg[1:]
            if not os.path.exists(plugin_cfg):
                self.result.display('f','plugin configuration file not found: '+ plugin_cfg)


# *******************   
# Check browser commands
# ***********************             
             
    def check_browser_commands(self,command_text):
        lines = command_text.split('\n')
        for line in lines:
            if line.strip()=="":
                continue
            self.check_browser_command(line)


    def check_browser_command(self,line):
        fields = line.split()
        if fields[0]=='uzbl':
            return
        
        if len(fields) not in (1,2):
            self.result.display('f','incorrect number of fields in browser command: '+ line)
            return
            
        command = fields[0]
        if command not in ('load','refresh','wait','exit','loop'):
            self.result.display('f','unknown command in browser commands: '+ line)
            return
           
        if command in ('refresh','exit','loop') and len(fields)<>1:
            self.result.display('f','incorrect number of fields for '+ command + 'in: '+ line)
            return
            
        if command == 'load':
            if len(fields)<>2:
                self.result.display('f','incorrect number of fields for '+ command + 'in: '+ line)
                return

        if command == 'wait':
            if len(fields)<>2:
                self.result.display('f','incorrect number of fields for '+ command + 'in: '+ line)
                return          
            arg = fields[1]
            if not arg.isdigit():
                self.result.display('f','Argument for Wait is not 0 or positive number in: '+ line)
                return
      
             
# *******************   
# Check controls
# *******************

    def check_controls(self,name,controls_text):
        lines = controls_text.split('\n')
        for line in lines:
            if line.strip()=="":
                continue
            error_text=self.check_control(line)


    def check_control(self,line):
            fields = line.split()
            if len(fields)<>2 :
                self.result.display('f',"incorrect number of fields in Control: " + line)
                return


# *******************   
# Check links
# ***********************

    def check_links(self,name,links_text):
        lines = links_text.split('\n')
        for line in lines:
            if line.strip()=="":
                continue
            error_text=self.check_link(line)


    def check_link(self,line):
            fields = line.split()
            if len(fields)<2 or len(fields)>3:
                self.result.display('f',"incorrect number of fields in link: " + line)
                return
            symbol=fields[0]
            operation=fields[1]
            if operation not in ('return','home','call','null','exit','goto','jump'):
                self.result.display('f',"unknown command in link: " + line)

# *******************   
# Check button links
# ***********************

    def check_button_links(self,name,links_text):
        lines = links_text.split('\n')
        for line in lines:
            if line.strip()=="":
                continue
            error_text=self.check_button_link(line)


    def check_button_link(self,line):
            fields = line.split()
            if len(fields)<>3:
                self.result.display('f',"incorrect number of fields in link: " + line)
                return
            operation=fields[1]
            if operation not in ('play'):
                self.result.display('f',"unknown command in link: " + line)


# ***********************************
# checking show controls
# ************************************ 

    def check_show_control(self,text,v_show_labels):
        lines = text.split("\n")
        for line in lines:
            error_text=self.check_show_control_fields(line,v_show_labels)

    def check_show_control_fields(self,line,v_show_labels):
        fields = line.split()
        if len(fields)==0: return

        if len(fields)<>2:
            self.result.display('f','Show Control - Incorrect number of fields in: ' + line)
            return
        
        if fields[1] not in ('start','stop','exit','shutdownnow'):
            self.result.display('f','Incorrect command in: ' + line)
            return

        if fields[1] in ( 'start','stop') and fields[0] not in v_show_labels:
            self.result.display('f',"Show Control - cannot find show reference: "+ fields[0])
            return
            
# ***********************************
# checking animation
# ************************************ 

    def check_animate_fields(self,field,line):
        fields= line.split()
        if len(fields)==0: return
            
        if len(fields)>3: self.result.display('f','Too many fields in: ' + field + ", " + line)

        if len(fields)<2:
            self.result.display('f','Too few fields in: ' + field + ", " + line)
            return
        
        name = fields[0]
        # name not checked - done at runtime
        
        to_state_text=fields[1]
        if not (to_state_text  in ('on','off')): self.result.display('f','Illegal to-state in: ' + field + ", " + line)
        
        if len(fields)==2:
            delay_text='0'
        else:
            delay_text=fields[2]
        
        if  not delay_text.isdigit(): self.result.display('f','Delay is not 0 or a positive integer in:' + field + ", " + line)

        return
    

    
    def check_animate(self,field,text):
        lines = text.split("\n")
        for line in lines:
            error_text=self.check_animate_fields(field,line)

             
    def read_gpio_cfg(self,pp_dir,pp_home):
        tryfile=self.pp_home+os.sep+"gpio.cfg"
        if os.path.exists(tryfile):
             filename=tryfile
        else:
            self.result.display('t', "gpio.cfg not found in pp_home")
            tryfile=self.pp_dir+os.sep+'pp_home'+os.sep+"gpio.cfg"
            if os.path.exists(tryfile):
                filename=tryfile
            else:
                self.result.display('w', "gpio.cfg not found in pipresents/pp_home - GPIO checking turned off")
                return False
        self.config = ConfigParser.ConfigParser()
        self.config.read(filename)
        return True

        
    def get(self,section,item):
        if self.config.has_option(section,item)==False:
            return False
        else:
            return self.config.get(section,item)

            
            
            
    def check_web_window(self,type,field,line):

        # check warp _ or xy2
        fields = line.split()
        
        if type=='show' and len(fields)==0:
            self.result.display('f','Show must have web window: ' + field + ", " + line)
            return
            
        if len(fields) == 0:
            return        

        #deal with warp which has 1 or 5  arguments
        if  fields[0] <>'warp':
            self.result.display('f','Illegal command: ' + field + ", " + line)
        if len(fields) not in (1,5):
            self.result.display('f','Wrong number of fields for warp: ' + field + ", " + line)
            return

        # deal with window coordinates    
        if len(fields) == 5:
            #window is specified
            if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                self.result.display('f','coordinate is not a positive integer ' + field + ", " + line)
                return



    

# *************************************
# IMAGE WINDOW
# ************************************

    def check_image_window(self,type,field,line):
    
        fields = line.split()
        
        if type=='show' and len(fields)==0:
            self.result.display('f','Show must have image window: ' + field + ", " + line)
            return
            
        if len(fields) == 0:
            return

        # deal with original whch has 0 or 2 arguments
        filter=''
        if fields[0]=='original':
            if len(fields) not in (1,3):
                self.result.display('f','Wrong number of fields for original: ' + field + ", " + line)
                return      
            # deal with window coordinates    
            if len(fields) == 3:
                #window is specified
                if not (fields[1].isdigit() and fields[2].isdigit()):
                    self.result.display('f','coordinate is not a positive integer ' + field + ", " + line)
                    return
                return
            else:
                return

        #deal with remainder which has 1, 2, 5 or  6arguments
        # check basic syntax
        if  fields[0] not in ('shrink','fit','warp'):
            self.result.display('f','Illegal command: ' + field + ", " + line)
            return
        if len(fields) not in (1,2,5,6):
            self.result.display('f','Wrong number of fields: ' + field + ", " + line)
            return
        if len(fields)==6 and fields[5] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS'):
            self.result.display('f','Illegal Filter: ' + field + ", " + line)
            return
        if len(fields)==2 and fields[1] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS'):
            self.result.display('f','Illegal Filter: ' + field + ", " + line)
        
        # deal with window coordinates    
        if len(fields) in (5,6):
            #window is specified
            if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                self.result.display('f','coordinate is not a positive integer ' + field + ", " + line)
                return

            





                     
# *************************************
# OMX WINDOW
# ************************************
                    
    def check_omx_window(self,type,field,line):

        fields = line.split()
        if type=='show' and len(fields)==0:
            self.result.display('f','show must have video window: ' + field + ", " + line)
            return
            
        if len(fields) == 0:
            return
            
        # deal with original which has 1
        if fields[0]=='original':
            if len(fields) <> 1:
                self.result.display('f','Wrong number of fields for original: ' + field + ", " + line)
                return 
            return


        #deal with warp which has 1 or 5  arguments
        # check basic syntax
        if  fields[0] <>'warp':
            self.result.display('f','Illegal command: ' + field + ", " + line)
            return
        if len(fields) not in (1,5):
            self.result.display('f','Wrong number of fields for warp: ' + field + ", " + line)

        # deal with window coordinates    
        if len(fields) == 5:
            #window is specified
            if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                self.result.display('f','coordinate is not a positive integer ' + field + ", " + line)
                return




# *************************************
# RESULT WINDOW CLASS
# ************************************


class ResultWindow:

    def __init__(self, parent, title,display_it):
        self.display_it=display_it
        self.errors=0
        self.warnings=0
        if self.display_it == False: return
        top = tk.Toplevel()
        top.title(title)
        scrollbar = Scrollbar(top, orient=tk.VERTICAL)
        self.textb = Text(top,width=80,height=40, wrap='word', font="arial 11",padx=5,yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.textb.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.textb.pack(side=LEFT, fill=BOTH, expand=1)
        self.textb.config(state=NORMAL)
        self.textb.delete(1.0, END)
        self.textb.config(state=DISABLED)


    def display(self,priority,text):
        if priority=='f':   self.errors+=1
        if priority =='w':self.warnings +=1       
        if self.display_it==False: return
        self.textb.config(state=NORMAL)
        if priority=='t':
             self.textb.insert(END, text+"\n")
        if priority=='f':
            self.textb.insert(END, "    ** Error:   "+text+"\n\n")
        if priority=='w':
            self.textb.insert(END, "    ** Warning:   "+text+"\n\n")           
        self.textb.config(state=DISABLED)

    def stats(self):
        if self.display_it==False: return
        self.textb.config(state=NORMAL)
        self.textb.insert(END, "\nErrors: "+str(self.errors)+"\nWarnings: "+str(self.warnings)+"\n\n\n")
        self.textb.config(state=DISABLED)

    def num_errors(self):
        return self.errors
