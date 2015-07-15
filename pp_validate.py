import os
import json
import ConfigParser
from Tkinter import Toplevel, Scrollbar,Text
from Tkinter import VERTICAL,RIGHT,LEFT,BOTH,Y,NORMAL,END,DISABLED

class Validator(object):

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
                      
        if profile_issue != editor_issue:
            self.result.display('f',"Profile version "+profile_issue+ " is different to that editor")
            self.result.display('t', "Validation Aborted")
            return False                                            
        
        # read the gpio config
        # gpio_cfg_ok=read_gpio_cfg(pp_dir,pp_home,pp_profile)
            
            
        # MAKE LIST OF SHOW LABELS
        v_show_labels=[]
        for show in v_shows:
            if show['type'] != 'start': v_show_labels.append(show['show-ref'])

        # CHECK ALL MEDIALISTS AND THEIR TRACKS
        v_media_lists = []
        for medialist_file in os.listdir(pp_profile):
            if not medialist_file.endswith(".json") and medialist_file not in ('pp_io_config','readme.txt'):
                self.result.display('f',"Invalid medialist in profile: "+ medialist_file)
                self.result.display('t', "Validation Aborted")
                return False
                
            if medialist_file.endswith(".json") and medialist_file not in  ('pp_showlist.json','schedule.json'):
                self.result.display('t',"\nChecking medialist '"+medialist_file+"'")
                v_media_lists.append(medialist_file)

                # open a medialist and test its tracks
                ifile  = open(pp_profile + os.sep + medialist_file, 'rb')
                sdict= json.load(ifile)
                ifile.close()                          
                tracks = sdict['tracks']
                if 'issue' in sdict:
                    medialist_issue= sdict['issue']
                else:
                    medialist_issue="1.0"
                      
                # check issue of medialist      
                if medialist_issue  !=  editor_issue:
                    self.result.display('f',"Medialist version "+medialist_issue+ " is different to that editor")
                    self.result.display('t', "Validation Aborted")
                    return False

                # open a medialist and test its tracks
                v_track_labels=[]
                anonymous=0
                for track in tracks:
                    self.result.display('t',"    Checking track '"+track['title']+"'")
                    
                    # check track-ref
                    if track['track-ref'] == '':
                        anonymous+=1
                    else:
                        if track['track-ref'] in v_track_labels:
                            self.result.display('f',"'duplicate track reference: "+ track['track-ref'])
                        v_track_labels.append(track['track-ref'])
     
                    # warn if media tracks blank  where optional
                    if track['type'] in ('audio','image','web','video'):
                        if track['location'].strip() == '':
                            self.result.display('w',"blank location")
                    
                    # check location of absolute and relative media tracks where present                   
                    if track['type'] in ('video','audio','image','web'):    
                        track_file=track['location']
                        if track_file.strip() != '':
                            if track_file[0] == "+":
                                track_file=pp_home+track_file[1:]
                            if not os.path.exists(track_file): self.result.display('f',"location "+track['location']+ " Media File not Found")

                    if track['type'] in ('video','audio','message','image','web','menu'):
                        
                        # check common fields
                        self.check_animate('animate-begin',track['animate-begin'])
                        self.check_animate('animate-end',track['animate-end'])
                        self.check_plugin(track['plugin'],pp_home)
                        self.check_show_control(track['show-control-begin'],v_show_labels)
                        self.check_show_control(track['show-control-end'],v_show_labels)
                        if track['background-image'] != '':
                            track_file=track['background-image']
                            if track_file[0] == "+":
                                track_file=pp_home+track_file[1:]
                            if not os.path.exists(track_file): self.result.display('f',"background-image "+track['background-image']+ " background image file not found")                                
                        if track['track-text'] != "":
                            if not track['track-text-x'].isdigit(): self.result.display('f',"'Track Text x position' is not 0 or a positive integer")
                            if not track['track-text-y'].isdigit(): self.result.display('f',"'Track Text y Position' is not 0 or a positive integer")
                            if track['track-text-colour']=='': self.result.display('f',"'Track Text Colour' is blank")
                            if track['track-text-font']=='': self.result.display('f',"'Track Text Font' is blank")                        


                    if track['type']=='menu':
                        self.check_menu(track)

                    
                    if track['type'] == "image":
                        if track['duration'] != "" and not track['duration'].isdigit(): self.result.display('f',"'Duration' is not blank, 0 or a positive integer")
                        if track['image-rotate'] != "" and not track['image-rotate'].isdigit(): self.result.display('f',"'Image Rotation' is not blank, 0 or a positive integer")
                        self.check_image_window('track','image-window',track['image-window'])

                    if track['type'] == "video":
                        self.check_omx_window('track','omx-window',track['omx-window'])
                        self.check_volume('track','omxplayer-volume',track['omx-volume'])
                            
                    if track['type'] == "audio":
                        if track['duration'] != '' and not track['duration'].isdigit(): self.result.display('f',"'Duration' is not 0 or a positive integer")
                        if track['duration'] == '0' : self.result.display('w',"'Duration' of an audio track is zero")
                        self.check_volume('track','mplayer-volume',track['mplayer-volume'])
                        
                    if track['type'] == "message":
                        if track['duration'] != '' and not track['duration'].isdigit(): self.result.display('f',"'Duration' is not 0 or a positive integer")
                        if track['text'] != "":
                            if track['message-x'] != '' and not track['message-x'].isdigit(): self.result.display('f',"'Message x Position' is not blank, 0 or a positive integer")
                            if track['message-y'] != '' and not track['message-y'].isdigit(): self.result.display('f',"'Message y Position' is not blank, 0 or a positive integer")
                            if track['message-colour']=='': self.result.display('f',"'Message Text Colour' is blank")
                            if track['message-font']=='': self.result.display('f',"Message Text Font' is blank")                        
                            
                    if track['type'] == 'web':
                        self.check_browser_commands(track['browser-commands'])
                        self.check_web_window('track','web-window',track['web-window'])

                  
                    # CHECK CROSS REF TRACK TO SHOW
                    if track['type'] == 'show':
                        if track['sub-show'] == "":
                            self.result.display('f',"No 'Sub-show to Run'")
                        else:
                            if track['sub-show'] not in v_show_labels: self.result.display('f',"Sub-show "+track['sub-show'] + " does not exist")
                            
                # if anonymous == 0 :self.result.display('w',"zero anonymous tracks in medialist " + file)

                # check for duplicate track-labels
                # !!!!!!!!!!!!!!!!!! add check for all labels


        # SHOWS
        # find start show and test it, test show-refs at the same time
        found=0
        for show in v_shows:
            if show['type'] == 'start':
                self.result.display('t',"\nChecking show '"+show['title'] + "' first pass")
                found+=1
                if show['show-ref'] !=  'start': self.result.display('f',"start show has incorrect label")
            else:
                self.result.display('t',"Checking show '"+show['title'] + "' first pass")
                if show['show-ref'] == '': self.result.display('f',"Show Reference is blank")
                if ' ' in show['show-ref']: self.result.display('f',"Spaces not allowed in Show Reference: " + show['show-ref'])
                
        if found == 0:self.result.display('f',"There is no start show")
        if found > 1:self.result.display('f',"There is more than 1 start show")    


        # check for duplicate show-labels
        for show_label in v_show_labels:
            found = 0
            for show in v_shows:
                if show['show-ref'] == show_label: found+=1
            if found > 1: self.result.display('f',show_label + " is defined more than once")
            
        # check other things about all the shows and create a list of medialist file references
        v_medialist_refs=[]
        for show in v_shows:
            if show['type'] == "start":
                self.result.display('t',"\nChecking show '"+show['title']+ "' second pass" )
                self.check_start_shows(show,v_show_labels)               
            else:
                self.result.display('t',"Checking show '"+show['title']+ "' second pass" )

                if show['medialist']=='': self.result.display('f', show['show-ref']+ " show has blank medialist")
                
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
                
                
                # open medialist and produce a dictionary of its contents for use later
                ifile  = open(pp_profile + os.sep + show['medialist'], 'rb')
                tracks = json.load(ifile)['tracks']
                ifile.close()
                
                # make a list of the track labels
                v_track_labels=[]
                for track in tracks:
                    if track['track-ref'] !='':
                        v_track_labels.append(track['track-ref'])
                
                
                # check common fields in the show
                #show
                self.check_show_canvas('show','Show Canvas',show['show-canvas'])
                
                #show background and text
                if show['show-text'] != "":
                    if not show['show-text-x'].isdigit(): self.result.display('f',"'Show Text x Position' is not 0 or a positive integer")
                    if not show['show-text-y'].isdigit(): self.result.display('f',"'Show Text y Position' is not 0 or a positive integer")
                    if show['show-text-colour']=='': self.result.display('f',"'Show Text Colour' is blank")
                    if show['show-text-font']=='': self.result.display('f',"'Show Text Font' is blank")
                background_image_file=show['background-image']
                if background_image_file.strip() != '' and  background_image_file[0] == "+":
                    track_file=pp_home+background_image_file[1:]
                    if not os.path.exists(track_file): self.result.display('f',"Background Image "+show['background-image']+ " background image file not found")

                #track defaults
                if not show['duration'].isdigit(): self.result.display('f',"'Duration' is not 0 or a positive integer")
                if not show['image-rotate'].isdigit(): self.result.display('f',"'Image Rotation' is not 0 or a positive integer")
                self.check_volume('show','Video Player Volume',show['omx-volume'])
                self.check_volume('show','Audio Volume',show['mplayer-volume'])
                self.check_omx_window('show','Video Window',show['omx-window'])
                self.check_image_window('show','Image Window',show['image-window'])

                #eggtimer
                if show['eggtimer-text'] != "":
                    if show['eggtimer-colour']=='': self.result.display('f',"'Eggtimer Colour' is blank")
                    if show['eggtimer-font']=='': self.result.display('f',"'Eggtimer Font' is blank")                
                    if not show['eggtimer-x'].isdigit(): self.result.display('f',"'Eggtimer x Position' is not 0 or a positive integer")
                    if not show['eggtimer-y'].isdigit(): self.result.display('f',"'Eggtimer y Position' is not 0 or a positive integer")

 
                # Validate simple fields of each show type
                if show['type'] in ("mediashow",'liveshow'):
                    if show['child-track-ref'] != '':
                        if show['child-track-ref'] not in v_track_labels:
                            self.result.display('f',"'Child Track ' " + show['child-track-ref'] + ' is not in medialist' )             
                        if not show['hint-y'].isdigit(): self.result.display('f',"'Hint y Position' is not 0 or a positive integer")
                        if not show['hint-x'].isdigit(): self.result.display('f',"'Hint x Position' is not 0 or a positive integer")
                        if show['hint-colour']=='': self.result.display('f',"'Hint Colour' is blank")
                        if show['hint-font']=='': self.result.display('f',"'Hint Font' is blank")

                        
                    self.check_hh_mm_ss('Show Timeout',show['show-timeout'])
                    
                    self.check_hh_mm_ss('Repeat Interval',show['interval'])
                    
                    if not show['track-count-limit'].isdigit(): self.result.display('f',"'Track Count Limit' is not 0 or a positive integer")

                    if show['trigger-start-type']in('input','input-persist'):
                        self.check_triggers('Trigger for Start',show['trigger-start-param'])

                    if show['trigger-next-type'] == 'input':
                        self.check_triggers('Trigger for Next',show['trigger-next-param'])

                    if show['trigger-end-type'] == 'input':
                        self.check_triggers('Trigger for End',show['trigger-end-param']) 
                        
                    self.check_web_window('show','web-window',show['web-window'])
                    
                    self.check_controls('controls',show['controls'])

                    #notices
                    if show['trigger-wait-text'] != "" or show['empty-text'] != "":
                        if show['admin-colour']=='': self.result.display('f',"' Notice Text Colour' is blank")
                        if show['admin-font']=='': self.result.display('f',"'Notice Text Font' is blank")                
                        if not show['admin-x'].isdigit(): self.result.display('f',"'Notice Text x Position' is not 0 or a positive integer")
                        if not show['admin-y'].isdigit(): self.result.display('f',"'Notice Text y Position' is not 0 or a positive integer")


                if show['type'] in ("artmediashow",'artliveshow'):
                    
                    #notices
                    if show['empty-text'] != "":
                        if show['admin-colour']=='': self.result.display('f',"' Notice Text Colour' is blank")
                        if show['admin-font']=='': self.result.display('f',"'Notice Text Font' is blank")                
                        if not show['admin-x'].isdigit(): self.result.display('f',"'Notice Text x Position' is not 0 or a positive integer")
                        if not show['admin-y'].isdigit(): self.result.display('f',"'Notice Text y Position' is not 0 or a positive integer")

                    self.check_controls('controls',show['controls'])
                    
                            
                if show['type'] == "menu":
                    self.check_hh_mm_ss('Show Timeout',show['show-timeout'])                 
                    self.check_hh_mm_ss('Track Timeout',show['track-timeout'])
                    
                    if show['menu-track-ref'] not in v_track_labels:
                        self.result.display('f',"'menu track ' is not in medialist: " + show['menu-track-ref'])     
                    self.check_web_window('show','web-window',show['web-window'])
                    self.check_controls('controls',show['controls'])

  
                if show['type'] == 'hyperlinkshow':
                    if show['first-track-ref'] not in v_track_labels:
                        self.result.display('f',"'first track ' is not in medialist: " + show['first-track-ref'])             
                    if show['home-track-ref'] not in v_track_labels:
                        self.result.display('f',"'home track ' is not in medialist: " + show['home-track-ref'])              
                    if show['timeout-track-ref'] not in v_track_labels:
                        self.result.display('f',"'timeout track ' is not in medialist: " + show['timeout-track-ref'])            
                    self.check_hyperlinks('links',show['links'],v_track_labels)
                    self.check_hh_mm_ss('Show Timeout',show['show-timeout'])                 
                    self.check_hh_mm_ss('Track Timeout',show['track-timeout'])
                    self.check_web_window('show','web-window',show['web-window'])

                if show['type'] == 'radiobuttonshow':
                    if show['first-track-ref'] not in v_track_labels:
                        self.result.display('f',"'first track ' is not in medialist: " + show['first-track-ref'])
                        
                    self.check_radiobutton_links('links',show['links'],v_track_labels)
                    self.check_hh_mm_ss('Show Timeout',show['show-timeout'])                 
                    self.check_hh_mm_ss('Track Timeout',show['track-timeout'])
                    self.check_web_window('show','web-window',show['web-window'])

        self.result.display('t', "\nValidation Complete")
        self.result.stats()
        if self.result.num_errors() == 0:
            return True
        else:
            return False

    def check_hh_mm_ss(self,name,item):          
        fields=item.split(':')
        if len(fields) == 0:
            return
        if len(fields)>3:
            self.result.display('f','Too many fields in '+ name + ': '  + item)
            return
        if len(fields) == 1:
            seconds=fields[0]
            minutes='0'
            hours='0'
        if len(fields) == 2:
            seconds=fields[1]
            minutes=fields[0]
            hours='0'
        if len(fields) == 3:
            seconds=fields[2]
            minutes=fields[1]
            hours=fields[0]
        if not seconds.isdigit() or not  minutes.isdigit() or  not hours.isdigit():
            self.result.display('f','Fields of  '+ name + ' are not positive integers: ' + item)
            return        
        if int(minutes)>59 or int(seconds)>59:
            if len(fields)<>1:
                self.result.display('f','Fields of  '+ name + ' are out of range: ' + item)
            else:
                self.result.display('w','Seconds or Minutes is greater then 59 in '+ name + ': ' + item)          
            return    
 
    def check_start_shows(self,show,v_show_labels):
        text=show['start-show']
        show_count=0
        fields = text.split()
        for field in fields:
            show_count+=1
            if field not in v_show_labels:
                self.result.display('f',"start show has undefined Start Show: "+ field)
        if show_count == 0:
            self.result.display('w',"start show has zero Start Shows")


# ***********************************
# triggers
# ************************************ 

    def check_triggers(self,field,line):
        words=line.split()
        if len(words)!=1: self.result.display('f','Wrong number of fields in: ' + field + ", " + line)

# ***********************************
# volume
# ************************************ 

    def check_volume(self,track_type,field,line):
        if track_type == 'show' and line.strip() == '':
            self.result.display('f','Wrong number of fields: ' + field + ", " + line)
            return
        if track_type == 'track' and line.strip() == '':
            return
        if line[0] not in ('0','-'):
            self.result.display('f','Invalid value: ' + field + ", " + line)
            return
        if line[0] ==  '0':
            if not line.isdigit():
                self.result.display('f','Invalid value: ' + field + ", " + line)
                return
            if int(line) != 0:
                self.result.display('f','out of range -60 > 0: ' + field + ", " + line)
                return
            return
            
        elif line[0] == '-':
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
            self.check_times_line(line)
            
    def check_times_line(self,line):
        items = line.split()
        if len(items) == 0: self.result.display('w','No time values when using time of day trigger: ')
        for item in items:
            self.check_times_item(item)

    def check_times_item(self,item):
        if item[0] == '+':
            if not item.lstrip('+').isdigit():
                self.result.display('f','Value of relative time is not positive integer: ' + item)
                return
        else:
            # hh:mm;ss
            fields=item.split(':')
            if len(fields) == 0:
                return
            if len(fields) == 1:
                self.result.display('f','Too few fields in time: ' + item)
                return
            if len(fields)>3:
                self.result.display('f','Too many fields in time: ' + item)
                return
            if len(fields) != 3:
                seconds='0'
            else:
                seconds=fields[2]
            if not fields[0].isdigit() or not  fields[1].isdigit() or  not seconds.isdigit():
                self.result.display('f','Fields of time are not positive integers: ' + item)
                return        
            if int(fields[0])>23 or int(fields[1])>59 or int(seconds)>59:
                self.result.display('f','Fields of time are out of range: ' + item)
                return
             
    def check_duration(self,field,line):          
        fields=line.split(':')
        if len(fields) == 0:
            self.result.display('f','End Trigger, ' + field +' Field is empty: ' + line)
            return
        if len(fields)>3:
            self.result.display('f','End Trigger, ' + field + ' More then 3 fields: ' + line)
            return
        if len(fields) == 1:
            secs=fields[0]
            minutes='0'
            hours='0'
        if len(fields) == 2:
            secs=fields[1]
            minutes=fields[0]
            hours='0'
        if len(fields) == 3:
            secs=fields[2]
            minutes=fields[1]
            hours=fields[0]
        if not hours.isdigit() or not  minutes.isdigit() or  not secs.isdigit():
            self.result.display('f','End Trigger, ' + field + ' Fields are not positive integers: ' + line)
            return
        
        if int(hours)>23 or int(minutes)>59 or int(secs)>59:
            self.result.display('f','End Trigger, ' + field + ' Fields are out of range: ' + line)
            return

# *******************   
# Check menu
# ***********************               
# window
# consistencty of modes
        
    def check_menu(self,track):

        if not track['menu-rows'].isdigit(): self.result.display('f'," Menu Rows is not 0 or a positive integer")
        if not track['menu-columns'].isdigit(): self.result.display('f'," Menu Columns is not 0 or a positive integer")     
        if not track['menu-icon-width'].isdigit(): self.result.display('f'," Icon Width is not 0 or a positive integer") 
        if not track['menu-icon-height'].isdigit(): self.result.display('f'," Icon Height is not 0 or a positive integer")
        if not track['menu-horizontal-padding'].isdigit(): self.result.display('f'," Horizontal Padding is not 0 or a positive integer")
        if not track['menu-vertical-padding'].isdigit(): self.result.display('f'," Vertical padding is not 0 or a positive integer") 
        if not track['menu-text-width'].isdigit(): self.result.display('f'," Text Width is not 0 or a positive integer") 
        if not track['menu-text-height'].isdigit(): self.result.display('f'," Text Height is not 0 or a positive integer")
        if not track['menu-horizontal-separation'].isdigit(): self.result.display('f'," Horizontal Separation is not 0 or a positive integer") 
        if not track['menu-vertical-separation'].isdigit(): self.result.display('f'," Vertical Separation is not 0 or a positive integer")
        if not track['menu-strip-padding'].isdigit(): self.result.display('f'," Stipple padding is not 0 or a positive integer")    

        if not track['hint-x'].isdigit(): self.result.display('f',"'Hint x Position' is not 0 or a positive integer")
        if not track['hint-y'].isdigit(): self.result.display('f',"'Hint y Position' is not 0 or a positive integer")

        if not track['track-text-x'].isdigit(): self.result.display('f'," Menu Text x Position is not 0 or a positive integer") 
        if not track['track-text-y'].isdigit(): self.result.display('f'," Menu Text y Position is not 0 or a positive integer")

        if track['menu-icon-mode'] == 'none' and track['menu-text-mode'] == 'none':
            self.result.display('f'," Icon and Text are both None") 

        if track['menu-icon-mode'] == 'none' and track['menu-text-mode'] == 'overlay':
            self.result.display('f'," cannot overlay none icon") 
            
        self.check_menu_window(track['menu-window'])

    def check_menu_window(self,line):
        if line  == '':
            self.result.display('f'," menu Window: may not be blank")
            return
        
        if line != '':
            fields = line.split()
            if len(fields) not in  (1, 2,4):
                self.result.display('f'," menu Window: wrong number of fields") 
                return
            if len(fields) == 1:
                if fields[0] != 'fullscreen':
                    self.result.display('f'," menu Window: single argument must be fullscreen")
                    return
            if len(fields) == 2:                    
                if not (fields[0].isdigit() and fields[1].isdigit()):
                    self.result.display('f'," menu Window: coordinates must be positive integers")
                    return
                    
            if len(fields) == 4:                    
                if not(fields[0].isdigit() and fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit()):
                    self.result.display('f'," menu Window: coordinates must be positive integers")
                    return




             
             
# *******************   
# Check plugin
# ***********************             
             
    def check_plugin(self,plugin_cfg,pp_home):
        if plugin_cfg.strip() != '' and  plugin_cfg[0] == "+":
            plugin_cfg=pp_home+plugin_cfg[1:]
            if not os.path.exists(plugin_cfg):
                self.result.display('f','plugin configuration file not found: '+ plugin_cfg)


# *******************   
# Check browser commands
# ***********************             
             
    def check_browser_commands(self,command_text):
        lines = command_text.split('\n')
        for line in lines:
            if line.strip() == "":
                continue
            self.check_browser_command(line)


    def check_browser_command(self,line):
        fields = line.split()
        if fields[0] == 'uzbl':
            return
        
        if len(fields) not in (1,2):
            self.result.display('f','incorrect number of fields in browser command: '+ line)
            return
            
        command = fields[0]
        if command not in ('load','refresh','wait','exit','loop'):
            self.result.display('f','unknown command in browser commands: '+ line)
            return
           
        if command in ('refresh','exit','loop') and len(fields) != 1:
            self.result.display('f','incorrect number of fields for '+ command + 'in: '+ line)
            return
            
        if command == 'load':
            if len(fields) != 2:
                self.result.display('f','incorrect number of fields for '+ command + 'in: '+ line)
                return

        if command == 'wait':
            if len(fields) != 2:
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
            if line.strip() == "":
                continue
            self.check_control(line)


    def check_control(self,line):
        fields = line.split()
        if len(fields) != 2 :
            self.result.display('f',"incorrect number of fields in Control: " + line)
            return
        operation=fields[1]
        if operation in ('up','down','play','stop','exit','pause','no-command','null') or operation[0:6] == 'mplay-' or operation[0:4] == 'omx-' or operation[0:5] == 'uzbl-':
            return
        else:
            self.result.display('f',"unknown Command in Control: " + line)


# *******************   
# Check hyperlinkshow links
# ***********************

    def check_hyperlinks(self,name,links_text,v_track_labels):
        lines = links_text.split('\n')
        for line in lines:
            if line.strip() == "":
                continue
            self.check_hyperlink(line,v_track_labels)


    def check_hyperlink(self,line,v_track_labels):
        fields = line.split()
        if len(fields) not in (2,3):
            self.result.display('f',"Incorrect number of fields in Control: " + line)
            return
        symbol=fields[0]
        operation=fields[1]
        if operation in ('home','null','stop','exit','repeat','pause','no-command') or operation[0:6] == 'mplay-' or operation[0:4] == 'omx-' or operation[0:5] == 'uzbl-':
            return

        elif operation in ('call','goto','jump'):
            if len(fields)!=3:
                self.result.display('f','Incorrect number of fields in Control: ' + line)
                return
            else:
                operand=fields[2]
                if operand not in v_track_labels:
                    self.result.display('f',operand + " Command argument is not in medialist: " + line)
                    return

        elif operation == 'return':
            if len(fields)==2:
                return
            else:
                operand=fields[2]
                if operand.isdigit() is True:
                    return
                else:
                    if operand not in v_track_labels:
                        self.result.display('f',operand + " Command argument is not in medialist: " + line)
                        return
        else:
            self.result.display('f',"unknown Command in Control: " + line)


# *******************   
# Check radiobuttonshow  links
# ***********************

    def check_radiobutton_links(self,name,links_text,v_track_labels):
        lines = links_text.split('\n')
        for line in lines:
            if line.strip() == "":
                continue
            self.check_radiobutton_link(line,v_track_labels)

    def check_radiobutton_link(self,line,v_track_labels):
        fields = line.split()
        if len(fields) not in (2,3):
            self.result.display('f',"Incorrect number of fields in Control: " + line)
            return
        symbol=fields[0]
        operation=fields[1]
        if operation in ('return','stop','exit','pause','no-command') or operation[0:6] == 'mplay-' or operation[0:4] == 'omx-' or operation[0:5] == 'uzbl-':
            return
        
        elif operation == 'play':
            if len(fields)!=3:
                self.result.display('f','Incorrect number of fields in Control: ' + line)
                return
            else:
                operand=fields[2]
                if operand not in v_track_labels:
                    self.result.display('f',operand + " Command argument is not in medialist: " + line)
                    return
        else:
            self.result.display('f',"unknown Command in Control: " + line)




# ***********************************
# checking show controls
# ************************************ 

    def check_show_control(self,text,v_show_labels):
        lines = text.split("\n")
        for line in lines:
            self.check_show_control_fields(line,v_show_labels)

    def check_show_control_fields(self,line,v_show_labels):
        fields = line.split()
        if len(fields) == 0:
            return
        # OSC command
        elif len(fields)>0 and fields[0][0] =='/':
                return
        elif len(fields)==1:
            if fields[0] not in ('exitpipresents','shutdownnow'):
                self.result.display('f','Show control - Unknown command in: ' + line)
                return
        elif len(fields) == 2:
            if fields[0] not in ('open','close'):
                self.result.display('f','Show Control - Unknown command in: ' + line)
            if fields[1] not in v_show_labels:
                self.result.display('f',"Show Control - cannot find Show Reference: "+ line)
                return
        else:
            self.result.display('f','Show Control - Incorrect number of fields in: ' + line)
            return
                 
            
# ***********************************
# checking animation
# ************************************ 

    def check_animate_fields(self,field,line):
        fields= line.split()
        if len(fields) == 0: return
            
        if len(fields)>4: self.result.display('f','Too many fields in: ' + field + ", " + line)

        if len(fields)<4:
            self.result.display('f','Too few fields in: ' + field + ", " + line)
            return

        delay_text=fields[0]
        if  not delay_text.isdigit(): self.result.display('f','Delay is not 0 or a positive integer in:' + field + ", " + line)

        name = fields[1]
        # name not checked - done at runtime

        out_type = fields[2]
        if out_type != 'state': self.result.display('f','Unknownl type in: ' + field + ", " + line)
        
        to_state_text=fields[3]
        if not (to_state_text  in ('on','off')): self.result.display('f','Unknown parameter in: ' + field + ", " + line)
        
        return
    

    
    def check_animate(self,field,text):
        lines = text.split("\n")
        for line in lines:
            self.check_animate_fields(field,line)


# *************************************
# GPIO CONFIG - NOT USED
# ************************************
             
    def read_gpio_cfg(self,pp_dir,pp_home):
        tryfile=pp_home+os.sep+"gpio.cfg"
        if os.path.exists(tryfile):
            filename=tryfile
        else:
            self.result.display('t', "gpio.cfg not found in pp_home")
            tryfile=pp_dir+os.sep+'pp_resources'+os.sep+"gpio.cfg"
            if os.path.exists(tryfile):
                filename=tryfile
            else:
                self.result.display('w', "gpio.cfg not found in pipresents/pp_resources - GPIO checking turned off")
                return False
        self.config = ConfigParser.ConfigParser()
        self.config.read(filename)
        return True

        
    def get(self,section,item):
        if self.config.has_option(section,item) is False:
            return False
        else:
            return self.config.get(section,item)



# *************************************
# WEB WINDOW
# ************************************           
                 
    def check_web_window(self,track_type,field,line):

        # check warp _ or xy2
        fields = line.split()
        
        if track_type == 'show' and len(fields) == 0:
            self.result.display('f','Show must specify Web Window: ' + field + ", " + line)
            return
            
        if len(fields) == 0:
            return        

        # deal with warp which has 1 or 5  arguments
        if  fields[0]  != 'warp':
            self.result.display('f','Illegal command: ' + field + ", " + line)
        if len(fields) not in (1,5):
            self.result.display('f','Wrong number of fields for warp: ' + field + ", " + line)
            return

        # deal with window coordinates    
        if len(fields) == 5:
            # window is specified
            if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                self.result.display('f','coordinate is not a positive integer ' + field + ", " + line)
                return

                
# *************************************
# SHOW CANVAS
# ************************************              
                           
    def check_show_canvas(self,track_type,name,line):
        fields=line.split()
        if len(fields)== 0:
            return
        if len(fields) !=4:
            self.result.display('f','wrong number of fields for ' + name + ", " + line)
            return
        else:
            # show canvas is specified
            if not (fields[0].isdigit() and fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit()):
                self.result.display('f','coordinate is not a positive integer ' + name + ", " + line)
                return
       

    

# *************************************
# IMAGE WINDOW
# ************************************

    def check_image_window(self,track_type,field,line):
    
        fields = line.split()
        
        if track_type == 'show' and len(fields) == 0:
            self.result.display('f','Show must specify Image Window: ' + field + ", " + line)
            return
            
        if len(fields) == 0:
            return

        # deal with original whch has 0 or 2 arguments
        if fields[0] == 'original':
            if len(fields) not in (1,3):
                self.result.display('f','Wrong number of fields for original: ' + field + ", " + line)
                return      
            # deal with window coordinates    
            if len(fields) == 3:
                # window is specified
                if not (fields[1].isdigit() and fields[2].isdigit()):
                    self.result.display('f','coordinate is not a positive integer ' + field + ", " + line)
                    return
                return
            else:
                return

        # deal with remainder which has 1, 2, 5 or  6arguments
        # check basic syntax
        if  fields[0] not in ('shrink','fit','warp'):
            self.result.display('f','Illegal command: ' + field + ", " + line)
            return
        if len(fields) not in (1,2,5,6):
            self.result.display('f','Wrong number of fields: ' + field + ", " + line)
            return
        if len(fields) == 6 and fields[5] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS'):
            self.result.display('f','Illegal Filter: ' + field + ", " + line)
            return
        if len(fields) == 2 and fields[1] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS'):
            self.result.display('f','Illegal Filter: ' + field + ", " + line)
        
        # deal with window coordinates    
        if len(fields) in (5,6):
            # window is specified
            if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                self.result.display('f','coordinate is not a positive integer ' + field + ", " + line)
                return

            





                     
# *************************************
# VIDEO WINDOW
# ************************************
                    
    def check_omx_window(self,track_type,field,line):

        fields = line.split()
        if track_type == 'show' and len(fields) == 0:
            self.result.display('f','show must have video window: ' + field + ", " + line)
            return
            
        if len(fields) == 0:
            return
            
        # deal with original which has 1
        if fields[0] == 'original':
            if len(fields)  !=  1:
                self.result.display('f','Wrong number of fields for original: ' + field + ", " + line)
                return 
            return


        # deal with warp which has 1 or 5  arguments
        # check basic syntax
        if  fields[0]  != 'warp':
            self.result.display('f','Illegal command: ' + field + ", " + line)
            return
        if len(fields) not in (1,5):
            self.result.display('f','Wrong number of fields for warp: ' + field + ", " + line)

        # deal with window coordinates    
        if len(fields) == 5:
            # window is specified
            if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                self.result.display('f','coordinate is not a positive integer ' + field + ", " + line)
                return

    def get_results(self):
        return self.result.errors, self.result.warnings



# *************************************
# RESULT WINDOW CLASS
# ************************************


class ResultWindow(object):

    def __init__(self, parent, title,display_it):
        self.display_it=display_it
        self.errors=0
        self.warnings=0
        if self.display_it is False: return
        top = Toplevel()
        top.title(title)
        scrollbar = Scrollbar(top, orient=VERTICAL)
        self.textb = Text(top,width=80,height=40, wrap='word', font="arial 11",padx=5,yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.textb.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.textb.pack(side=LEFT, fill=BOTH, expand=1)
        self.textb.config(state=NORMAL)
        self.textb.delete(1.0, END)
        self.textb.config(state=DISABLED)
        top.bind("<Escape>", self.escape_keypressed)
        self.top = top

    def escape_keypressed(self, event=None):
        self.top.destroy()

    def display(self,priority,text):
        if priority == 'f':   self.errors+=1
        if priority  == 'w':self.warnings +=1       
        if self.display_it is False: return
        self.textb.config(state=NORMAL)
        if priority == 't':
            self.textb.insert(END, text+"\n")
        if priority == 'f':
            self.textb.insert(END, "    ** Error:   "+text+"\n\n")
        if priority == 'w':
            self.textb.insert(END, "    ** Warning:   "+text+"\n\n")           
        self.textb.config(state=DISABLED)

    def stats(self):
        if self.display_it is False: return
        self.textb.config(state=NORMAL)
        # show the summary at the top so user doesn't have to scroll all the way down to see
        # whether there were errors
        self.textb.insert(1.0, "\nErrors: "+str(self.errors)+"\nWarnings: "+str(self.warnings)+"\n\n\n")
        self.textb.config(state=DISABLED)

    def num_errors(self):
        return self.errors
