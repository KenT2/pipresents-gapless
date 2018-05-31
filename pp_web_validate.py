import os
import json
import ConfigParser
import remi.gui as gui
from remi_plus import AdaptableDialog
from pp_utils import parse_rectangle
"""
1/12/2016 - warn if foreign files in profile rather than abort

"""


class Validator(AdaptableDialog):

    def __init__(self, title):
        self.text=''
        self.errors=0
        self.warnings=0

        super(Validator, self).__init__('Validation Result','',width=600,height=500,confirm_name='Done')
        self.textb = gui.TextInput(width=550,height=400,single_line=False)
        self.append_field(self.textb,'text')


    def confirm_dialog(self):
          self.hide()

    def display(self,priority,text):
        if priority == 'f':   self.errors+=1
        if priority  == 'w':self.warnings +=1       
        if self.display_it is False: return
        if priority == 't':
            self.insert(text+"\n")
        if priority == 'f':
            self.insert("    ** Error:   "+text+"\n\n")
        if priority == 'w':
            self.insert("    ** Warning:   "+text+"\n\n")           

    def insert(self,text):
        self.text +=text
        self.textb.set_value(self.text)

    def stats(self):
        if self.display_it is False: return
        self.insert("\nErrors: "+str(self.errors)+"\nWarnings: "+str(self.warnings)+"\n\n\n")


    def num_errors(self):
        return self.errors


    def validate_profile(self, pp_dir, pp_home, pp_profile,editor_issue,display_it):
        self.display_it=display_it
        # USES
        # self.current_showlist

        # CREATES
        # v_media_lists - file names of all medialists in the profile
        # v_shows
        # v_track_labels - list of track labels in current medialist.
        # v_show_labels - list of show labels in the showlist
        # v_medialist_refs - list of references to medialist files in the showlist

        # open results display
        self.display('t',"\nVALIDATING PROFILE '"+ pp_profile + "'")

        if not  os.path.exists(pp_profile+os.sep+"pp_showlist.json"):
            self.display('f',"pp_showlist.json not in profile")
            self.display('t', "Validation Aborted")
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
            self.display('f',"Profile version "+profile_issue+ " is different to that editor")
            self.display('t', "Validation Aborted")
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
            if not medialist_file.endswith(".json") and medialist_file not in ('readme.txt') and not os.path.isdir(pp_profile+os.sep+medialist_file):
                self.display('w',"Placing a media file in a profile is discouraged: "+ medialist_file + '\n         Place it in a directory')
                
            if medialist_file.endswith(".json") and medialist_file not in  ('pp_showlist.json','schedule.json'):
                self.display('t',"\nChecking medialist '"+medialist_file+"'")
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
                    self.display('f',"Medialist version "+medialist_issue+ " is different to that editor")
                    self.display('t', "Validation Aborted")
                    return False

                # open a medialist and test its tracks
                v_track_labels=[]
                anonymous=0
                for track in tracks:
                    self.display('t',"    Checking track '"+track['title']+"'")
                    
                    # check track-ref
                    if track['track-ref'] == '':
                        anonymous+=1
                    else:
                        if track['track-ref'] in v_track_labels:
                            self.display('f',"'duplicate track reference: "+ track['track-ref'])
                        v_track_labels.append(track['track-ref'])
     
                    # warn if media tracks blank  where optional
                    if track['type'] in ('audio','image','web','video'):
                        if track['location'].strip() == '':
                            self.display('w',"blank location")
                    
                    # check location of relative media tracks where present                   
                    if track['type'] in ('video','audio','image','web'):    
                        track_file=track['location']
                        if track_file.strip() != '' and  track_file[0] == "+":
                            track_file=pp_home+track_file[1:]
                            if not os.path.exists(track_file): self.display('f',"location "+track['location']+ " Media File not Found")
                            
                        if track_file.strip() != '' and  track_file[0] == "@":
                            track_file=pp_profile+track_file[1:]
                            if not os.path.exists(track_file): self.display('f',"location "+track['location']+ " Media File not Found")

                    if track['type'] in ('video','audio','message','image','web','menu'):
                        
                        # check common fields
                        self.check_animate('animate-begin',track['animate-begin'])
                        self.check_animate('animate-end',track['animate-end'])
                        self.check_plugin(track['plugin'],pp_home,pp_profile)
                        self.check_show_control(track['show-control-begin'],v_show_labels)
                        self.check_show_control(track['show-control-end'],v_show_labels)
                        if track['background-image'] != '':
                            track_file=track['background-image']
                            if track_file[0] == "+":
                                track_file=pp_home+track_file[1:]
                                if not os.path.exists(track_file): self.display('f',"background-image "+track['background-image']+ " background image file not found")                                
                            if track_file[0] == "@":
                                track_file=pp_profile+track_file[1:]
                                if not os.path.exists(track_file): self.display('f',"location "+track['location']+ " Background Image not Found")

                        if track['track-text'] != "":
                            if track['track-text-x'] != "" and not track['track-text-x'].isdigit(): self.display('f',"'Track Text x position' is not a positive integer")
                            if track['track-text-y'] != "" and not track['track-text-y'].isdigit(): self.display('f',"'Track Text y Position' is not a positive integer")
                            if track['track-text-justify'] != "" and track['track-text-justify'] not in ('left','right','center'): self.display('f',"'Track Text Justify' has illegal value")

                    if track['type']=='menu':
                        self.check_menu(track)

                    
                    if track['type'] == "image":
                        if track['pause-timeout'] != "" and not track['pause-timeout'].isdigit():
                            self.display('f',"'Pause Timeout' is not blank or a positive integer")
                        else:
                            if track['pause-timeout'] != "" and int(track['pause-timeout']) < 1: self.display('f',"'Pause Timeout' is less than 1")
                        if track['duration'] != "" and not track['duration'].isdigit(): self.display('f',"'Duration' is not blank, 0 or a positive integer")
                        if track['image-rotate'] != "" and not track['image-rotate'].isdigit(): self.display('f',"'Image Rotation' is not blank, 0 or a positive integer")
                        self.check_image_window('track','image-window',track['image-window'])

                    if track['type'] == "video":
                        if track['pause-timeout'] != "" and not track['pause-timeout'].isdigit():
                            self.display('f',"'Pause Timeout' is not blank or a positive integer")
                        else:
                            if track['pause-timeout'] != "" and int(track['pause-timeout']) < 1: self.display('f',"'Pause Timeout' is less than 1")

                        self.check_omx_window('track','omx-window',track['omx-window'])
                        self.check_volume('track','omxplayer-volume',track['omx-volume'])
                            
                    if track['type'] == "audio":
                        if track['pause-timeout'] != "" and not track['pause-timeout'].isdigit():
                            self.display('f',"'Pause Timeout' is not blank or a positive integer")
                        else:
                            if track['pause-timeout'] != "" and int(track['pause-timeout']) < 1: self.display('f',"'Pause Timeout' is less than 1")

                        if track['duration'] != '' and not track['duration'].isdigit(): self.display('f',"'Duration' is not 0 or a positive integer")
                        if track['duration'] == '0' : self.display('w',"'Duration' of an audio track is zero")
                        self.check_volume('track','mplayer-volume',track['mplayer-volume'])
                        
                    if track['type'] == "message":
                        if track['duration'] != '' and not track['duration'].isdigit(): self.display('f',"'Duration' is not 0 or a positive integer")
                        if track['text'] != "":
                            if track['message-x'] != '' and not track['message-x'].isdigit(): self.display('f',"'Message x Position' is not blank, a positive integer")
                            if track['message-y'] != '' and not track['message-y'].isdigit(): self.display('f',"'Message y Position' is not blank, a positive integer")
                            if track['message-colour']=='': self.display('f',"'Message Text Colour' is blank")
                            if track['message-font']=='': self.display('f',"Message Text Font' is blank")                        
                            
                    if track['type'] == 'web':
                        self.check_browser_commands(track['browser-commands'])
                        self.check_web_window('track','web-window',track['web-window'])

                  
                    # CHECK CROSS REF TRACK TO SHOW
                    if track['type'] == 'show':
                        if track['sub-show'] == "":
                            self.display('f',"No 'Sub-show to Run'")
                        else:
                            if track['sub-show'] not in v_show_labels: self.display('f',"Sub-show "+track['sub-show'] + " does not exist")
                            
                # if anonymous == 0 :self.display('w',"zero anonymous tracks in medialist " + file)

                # check for duplicate track-labels
                # !!!!!!!!!!!!!!!!!! add check for all labels


        # SHOWS
        # find start show and test it, test show-refs at the same time
        found=0
        for show in v_shows:
            if show['type'] == 'start':
                self.display('t',"\nChecking show '"+show['title'] + "' first pass")
                found+=1
                if show['show-ref'] !=  'start': self.display('f',"start show has incorrect label")
            else:
                self.display('t',"Checking show '"+show['title'] + "' first pass")
                if show['show-ref'] == '': self.display('f',"Show Reference is blank")
                if ' ' in show['show-ref']: self.display('f',"Spaces not allowed in Show Reference: " + show['show-ref'])
                
        if found == 0:self.display('f',"There is no start show")
        if found > 1:self.display('f',"There is more than 1 start show")    


        # check for duplicate show-labels
        for show_label in v_show_labels:
            found = 0
            for show in v_shows:
                if show['show-ref'] == show_label: found+=1
            if found > 1: self.display('f',show_label + " is defined more than once")
            
        # check other things about all the shows and create a list of medialist file references
        v_medialist_refs=[]
        for show in v_shows:
            if show['type'] == "start":
                self.display('t',"\nChecking show '"+show['title']+ "' second pass" )
                self.check_start_shows(show,v_show_labels)               
            else:
                self.display('t',"Checking show '"+show['title']+ "' second pass" )

                if show['medialist']=='': self.display('f', show['show-ref']+ " show has blank medialist")
                
                if '.json' not in show['medialist']:
                    self.display('f', show['show-ref']+ " show has invalid medialist")
                    self.display('t', "Validation Aborted")
                    return False

                if show['medialist'] not in v_media_lists:
                    self.display('f', "'"+show['medialist']+ "' medialist not found")
                    self.display('t', "Validation Aborted")
                    return False

                if not os.path.exists(pp_profile + os.sep + show['medialist']):
                    self.display('f', "'"+show['medialist']+ "' medialist file does not exist")
                    self.display('t', "Validation Aborted")
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
                    if show['show-text-x'] != "" and not show['show-text-x'].isdigit(): self.display('f',"'Show Text x Position' is not a positive integer")
                    if show['show-text-y'] != "" and not show['show-text-y'].isdigit(): self.display('f',"'Show Text y Position' is not a positive integer")
                    if show['show-text-colour']=='': self.display('f',"'Show Text Colour' is blank")
                    if show['show-text-font']=='': self.display('f',"'Show Text Font' is blank")
                    
                background_image_file=show['background-image']
                if background_image_file.strip() != '' and  background_image_file[0] == "+":
                    track_file=pp_home+background_image_file[1:]
                    if not os.path.exists(track_file): self.display('f',"Background Image "+show['background-image']+ " background image file not found")
                if background_image_file.strip() != '' and  background_image_file[0] == "@":
                    track_file=pp_profile+background_image_file[1:]
                    if not os.path.exists(track_file): self.display('f',"Background Image "+show['background-image']+ " background image file not found")


                #track defaults

                if show['track-text-x'] != ''and not show['track-text-x'].isdigit(): self.display('f',"'Track Text x Position' is not a positive integer")
                if show['track-text-y'] != ''and not show['track-text-y'].isdigit(): self.display('f',"'Track Text y Position' is not a positive integer")
                if show['track-text-colour']=='': self.display('f',"'Track Text Colour' is blank")
                if show['track-text-font']=='': self.display('f',"'Track Text Font' is blank")
                if show['track-text-justify'] not in ('left','right','center'): self.display('f',"'Track Text Justify' has illegal value")
                
                
                if not show['duration'].isdigit(): self.display('f',"'Duration' is not 0 or a positive integer")
                if show['pause-timeout'] != "" and not show['pause-timeout'].isdigit():
                    self.display('f',"'Pause Timeout' is not blank or a positive integer")
                else:
                    if show['pause-timeout'] != "" and int(show['pause-timeout']) < 1: self.display('f',"'Pause Timeout' is less than 1")

                if not show['image-rotate'].isdigit(): self.display('f',"'Image Rotation' is not 0 or a positive integer")
                self.check_volume('show','Video Player Volume',show['omx-volume'])
                self.check_volume('show','Audio Volume',show['mplayer-volume'])
                self.check_omx_window('show','Video Window',show['omx-window'])
                self.check_image_window('show','Image Window',show['image-window'])

                #eggtimer
                if show['eggtimer-text'] != "":
                    if show['eggtimer-colour']=='': self.display('f',"'Eggtimer Colour' is blank")
                    if show['eggtimer-font']=='': self.display('f',"'Eggtimer Font' is blank")                
                    if not show['eggtimer-x']!='' and not show['eggtimer-x'].isdigit(): self.display('f',"'Eggtimer x Position' is not a positive integer")
                    if not show['eggtimer-y']!='' and not show['eggtimer-y'].isdigit(): self.display('f',"'Eggtimer y Position' is not a positive integer")

 
                # Validate simple fields of each show type
                if show['type'] in ("mediashow",'liveshow'):
                    if show['child-track-ref'] != '':
                        if show['child-track-ref'] not in v_track_labels:
                            self.display('f',"'Child Track ' " + show['child-track-ref'] + ' is not in medialist' )             
                        if not show['hint-x']!='' and not show['hint-y'].isdigit(): self.display('f',"'Hint y Position' is not a positive integer")
                        if not show['hint-x']!='' and not show['hint-x'].isdigit(): self.display('f',"'Hint x Position' is not a positive integer")
                        if show['hint-colour']=='': self.display('f',"'Hint Colour' is blank")
                        if show['hint-font']=='': self.display('f',"'Hint Font' is blank")

                        
                    self.check_hh_mm_ss('Show Timeout',show['show-timeout'])
                    
                    self.check_hh_mm_ss('Repeat Interval',show['interval'])
                    
                    if not show['track-count-limit'].isdigit(): self.display('f',"'Track Count Limit' is not 0 or a positive integer")

                    if show['trigger-start-type']in('input','input-persist'):
                        self.check_triggers('Start Trigger Parameters',show['trigger-start-param'])

                    if show['trigger-next-type'] == 'input':
                        self.check_triggers('Next Trigger Parameters',show['trigger-next-param'])

                    if show['trigger-end-type'] == 'input':
                        self.check_triggers('End Trigger Parameters',show['trigger-end-param']) 
                        
                    self.check_web_window('show','web-window',show['web-window'])
                    
                    self.check_controls('controls',show['controls'])

                    #notices
                    if show['trigger-wait-text'] != "" or show['empty-text'] != "":
                        if show['admin-colour']=='': self.display('f',"' Notice Text Colour' is blank")
                        if show['admin-font']=='': self.display('f',"'Notice Text Font' is blank")                
                        if not show['admin-x']!='' and not show['admin-x'].isdigit(): self.display('f',"'Notice Text x Position' is not a positive integer")
                        if not show['admin-y']!='' and not show['admin-y'].isdigit(): self.display('f',"'Notice Text y Position' is not a positive integer")


                if show['type'] in ("artmediashow",'artliveshow'):
                    
                    #notices
                    if show['empty-text'] != "":
                        if show['admin-colour']=='': self.display('f',"' Notice Text Colour' is blank")
                        if show['admin-font']=='': self.display('f',"'Notice Text Font' is blank")                
                        if not show['admin-x']!='' and not show['admin-x'].isdigit(): self.display('f',"'Notice Text x Position' is not a positive integer")
                        if not show['admin-y']!='' and not show['admin-y'].isdigit(): self.display('f',"'Notice Text y Position' is not a positive integer")

                    self.check_controls('controls',show['controls'])
                    
                            
                if show['type'] == "menu":
                    self.check_hh_mm_ss('Show Timeout',show['show-timeout'])                 
                    self.check_hh_mm_ss('Track Timeout',show['track-timeout'])

                    if show['menu-track-ref']=='':
                        self.display('f',"'menu track ' is blank")
                    else:
                        if show['menu-track-ref'] not in v_track_labels:
                            self.display('f',"'menu track ' is not in medialist: " + show['menu-track-ref'])     
                    self.check_web_window('show','web-window',show['web-window'])
                    self.check_controls('controls',show['controls'])

  
                if show['type'] == 'hyperlinkshow':
                    if show['first-track-ref']=='':
                        self.display('f',"'First Track ' is blank")
                    else:
                        if show['first-track-ref'] not in v_track_labels:
                            self.display('f',"'First track ' is not in medialist: " + show['first-track-ref'])
                            
                    if show['home-track-ref']=='':
                        self.display('f',"'Home Track ' is blank")
                    else:
                        if show['home-track-ref'] not in v_track_labels:
                            self.display('f',"'Home track ' is not in medialist: " + show['home-track-ref'])

                    if show['timeout-track-ref']=='':
                        self.display('w',"'Timeout Track ' is blank")
                    else:
                        if show['timeout-track-ref'] not in v_track_labels:
                            self.display('f',"'timeout track ' is not in medialist: " + show['timeout-track-ref'])            
                    self.check_hyperlinks('links',show['links'],v_track_labels)
                    self.check_hh_mm_ss('Show Timeout',show['show-timeout'])                 
                    self.check_hh_mm_ss('Track Timeout',show['track-timeout'])
                    self.check_web_window('show','web-window',show['web-window'])

                if show['type'] == 'radiobuttonshow':
                    if show['first-track-ref']=='':
                        self.display('f',"'Home Track ' is blank")
                    else:
                        if show['first-track-ref'] not in v_track_labels:
                            self.display('f',"'first track ' is not in medialist: " + show['first-track-ref'])
                        
                    self.check_radiobutton_links('links',show['links'],v_track_labels)
                    self.check_hh_mm_ss('Show Timeout',show['show-timeout'])                 
                    self.check_hh_mm_ss('Track Timeout',show['track-timeout'])
                    self.check_web_window('show','web-window',show['web-window'])

        self.display('t', "\nValidation Complete")
        self.stats()
        if self.num_errors() == 0:
            return True
        else:
            return False

    def check_hh_mm_ss(self,name,item):          
        fields=item.split(':')
        if len(fields) == 0:
            return
        if len(fields)>3:
            self.display('f','Too many fields in '+ name + ': '  + item)
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
            self.display('f','Fields of  '+ name + ' are not positive integers: ' + item)
            return        
        if int(minutes)>59 or int(seconds)>59:
            if len(fields)<>1:
                self.display('f','Fields of  '+ name + ' are out of range: ' + item)
            else:
                self.display('w','Seconds or Minutes is greater then 59 in '+ name + ': ' + item)          
            return    
 
    def check_start_shows(self,show,v_show_labels):
        text=show['start-show']
        show_count=0
        fields = text.split()
        for field in fields:
            show_count+=1
            if field not in v_show_labels:
                self.display('f',"start show has undefined Start Show: "+ field)
        if show_count == 0:
            self.display('w',"start show has zero Start Shows")


# ***********************************
# triggers
# ************************************ 

    def check_triggers(self,field,line):
        words=line.split()
        if len(words)!=1: self.display('f','Wrong number of fields in: ' + field + ", " + line)

# ***********************************
# volume
# ************************************ 

    def check_volume(self,track_type,field,line):
        if track_type == 'show' and line.strip() == '':
            self.display('f','Wrong number of fields: ' + field + ", " + line)
            return
        if track_type == 'track' and line.strip() == '':
            return
        if line[0] not in ('0','-'):
            self.display('f','Invalid value: ' + field + ", " + line)
            return
        if line[0] ==  '0':
            if not line.isdigit():
                self.display('f','Invalid value: ' + field + ", " + line)
                return
            if int(line) != 0:
                self.display('f','out of range -60 > 0: ' + field + ", " + line)
                return
            return
            
        elif line[0] == '-':
            if not line[1:].isdigit():
                self.display('f','Invalid value: ' + field + ", " + line)
                return
            if int(line)<-60 or int(line)>0:
                self.display('f','out of range -60 > 0: ' + field + ", " + line)
                return
            return
        
        else:
            self.display('f','help, do not understaand!: ' + field + ", " + line)
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
        if len(items) == 0: self.display('w','No time values when using time of day trigger: ')
        for item in items:
            self.check_times_item(item)

    def check_times_item(self,item):
        if item[0] == '+':
            if not item.lstrip('+').isdigit():
                self.display('f','Value of relative time is not positive integer: ' + item)
                return
        else:
            # hh:mm;ss
            fields=item.split(':')
            if len(fields) == 0:
                return
            if len(fields) == 1:
                self.display('f','Too few fields in time: ' + item)
                return
            if len(fields)>3:
                self.display('f','Too many fields in time: ' + item)
                return
            if len(fields) != 3:
                seconds='0'
            else:
                seconds=fields[2]
            if not fields[0].isdigit() or not  fields[1].isdigit() or  not seconds.isdigit():
                self.display('f','Fields of time are not positive integers: ' + item)
                return        
            if int(fields[0])>23 or int(fields[1])>59 or int(seconds)>59:
                self.display('f','Fields of time are out of range: ' + item)
                return
             
    def check_duration(self,field,line):          
        fields=line.split(':')
        if len(fields) == 0:
            self.display('f','End Trigger, ' + field +' Field is empty: ' + line)
            return
        if len(fields)>3:
            self.display('f','End Trigger, ' + field + ' More then 3 fields: ' + line)
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
            self.display('f','End Trigger, ' + field + ' Fields are not positive integers: ' + line)
            return
        
        if int(hours)>23 or int(minutes)>59 or int(secs)>59:
            self.display('f','End Trigger, ' + field + ' Fields are out of range: ' + line)
            return

# *******************   
# Check menu
# ***********************               
# window
# consistencty of modes
        
    def check_menu(self,track):

        if not track['menu-rows'].isdigit(): self.display('f'," Menu Rows is not 0 or a positive integer")
        if not track['menu-columns'].isdigit(): self.display('f'," Menu Columns is not 0 or a positive integer")     
        if not track['menu-icon-width'].isdigit(): self.display('f'," Icon Width is not 0 or a positive integer") 
        if not track['menu-icon-height'].isdigit(): self.display('f'," Icon Height is not 0 or a positive integer")
        if not track['menu-horizontal-padding'].isdigit(): self.display('f'," Horizontal Padding is not 0 or a positive integer")
        if not track['menu-vertical-padding'].isdigit(): self.display('f'," Vertical padding is not 0 or a positive integer") 
        if not track['menu-text-width'].isdigit(): self.display('f'," Text Width is not 0 or a positive integer") 
        if not track['menu-text-height'].isdigit(): self.display('f'," Text Height is not 0 or a positive integer")
        if not track['menu-horizontal-separation'].isdigit(): self.display('f'," Horizontal Separation is not 0 or a positive integer") 
        if not track['menu-vertical-separation'].isdigit(): self.display('f'," Vertical Separation is not 0 or a positive integer")
        if not track['menu-strip-padding'].isdigit(): self.display('f'," Stipple padding is not 0 or a positive integer")    

        if not track['hint-x']!='' and not track['hint-x'].isdigit(): self.display('f',"'Hint x Position' is not a positive integer")
        if not track['hint-y']!='' and not track['hint-y'].isdigit(): self.display('f',"'Hint y Position' is not a positive integer")

        if track['track-text-x'] != "" and not track['track-text-x'].isdigit(): self.display('f'," Menu Text x Position is not a positive integer") 
        if track['track-text-y'] != "" and not track['track-text-y'].isdigit(): self.display('f'," Menu Text y Position is not a positive integer")

        if track['menu-icon-mode'] == 'none' and track['menu-text-mode'] == 'none':
            self.display('f'," Icon and Text are both None") 

        if track['menu-icon-mode'] == 'none' and track['menu-text-mode'] == 'overlay':
            self.display('f'," cannot overlay none icon") 
            
        self.check_menu_window(track['menu-window'])

    def check_menu_window(self,line):
        if line  == '':
            self.display('f'," menu Window: may not be blank")
            return
        
        if line != '':
            fields = line.split()
            if len(fields) not in  (1, 2,4):
                self.display('f'," menu Window: wrong number of fields") 
                return
            if len(fields) == 1:
                if fields[0] != 'fullscreen':
                    self.display('f'," menu Window: single argument must be fullscreen")
                    return
            if len(fields) == 2:                    
                if not (fields[0].isdigit() and fields[1].isdigit()):
                    self.display('f'," menu Window: coordinates must be positive integers")
                    return
                    
            if len(fields) == 4:                    
                if not(fields[0].isdigit() and fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit()):
                    self.display('f'," menu Window: coordinates must be positive integers")
                    return




             
             
# *******************   
# Check plugin
# ***********************             
             
    def check_plugin(self,plugin_cfg,pp_home,pp_profile):
        if plugin_cfg.strip() != '' and  plugin_cfg[0] == "+":
            plugin_cfg=pp_home+plugin_cfg[1:]
            if not os.path.exists(plugin_cfg):
                self.display('f','plugin configuration file not found: '+ plugin_cfg)
        if plugin_cfg.strip() != '' and  plugin_cfg[0] == "@":
            plugin_cfg=pp_profile+plugin_cfg[1:]
            if not os.path.exists(plugin_cfg):
                self.display('f','plugin configuration file not found: '+ plugin_cfg)

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
            self.display('f','incorrect number of fields in browser command: '+ line)
            return
            
        command = fields[0]
        if command not in ('load','refresh','wait','exit','loop'):
            self.display('f','unknown command in browser commands: '+ line)
            return
           
        if command in ('refresh','exit','loop') and len(fields) != 1:
            self.display('f','incorrect number of fields for '+ command + 'in: '+ line)
            return
            
        if command == 'load':
            if len(fields) != 2:
                self.display('f','incorrect number of fields for '+ command + 'in: '+ line)
                return

        if command == 'wait':
            if len(fields) != 2:
                self.display('f','incorrect number of fields for '+ command + 'in: '+ line)
                return          
            arg = fields[1]
            if not arg.isdigit():
                self.display('f','Argument for Wait is not 0 or positive number in: '+ line)
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
            self.display('f',"incorrect number of fields in Control: " + line)
            return
        operation=fields[1]
        if operation in ('up','down','play','stop','exit','pause','no-command','null','pause-on','pause-off','mute','unmute','go') or operation[0:6] == 'mplay-' or operation[0:4] == 'omx-' or operation[0:5] == 'uzbl-':
            return
        else:
            self.display('f',"unknown Command in Control: " + line)


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
            self.display('f',"Incorrect number of fields in Control: " + line)
            return
        symbol=fields[0]
        operation=fields[1]
        if operation in ('home','null','stop','exit','repeat','pause','no-command','pause-on','pause-off','mute','unmute','go') or operation[0:6] == 'mplay-' or operation[0:4] == 'omx-' or operation[0:5] == 'uzbl-':
            return

        elif operation in ('call','goto','jump'):
            if len(fields)!=3:
                self.display('f','Incorrect number of fields in Control: ' + line)
                return
            else:
                operand=fields[2]
                if operand not in v_track_labels:
                    self.display('f',operand + " Command argument is not in medialist: " + line)
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
                        self.display('f',operand + " Command argument is not in medialist: " + line)
                        return
        else:
            self.display('f',"unknown Command in Control: " + line)


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
            self.display('f',"Incorrect number of fields in Control: " + line)
            return
        symbol=fields[0]
        operation=fields[1]
        if operation in ('return','stop','exit','pause','no-command','pause-on','pause-off','mute','unmute','go') or operation[0:6] == 'mplay-' or operation[0:4] == 'omx-' or operation[0:5] == 'uzbl-':
            return
        
        elif operation == 'play':
            if len(fields)!=3:
                self.display('f','Incorrect number of fields in Control: ' + line)
                return
            else:
                operand=fields[2]
                if operand not in v_track_labels:
                    self.display('f',operand + " Command argument is not in medialist: " + line)
                    return
        else:
            self.display('f',"unknown Command in Control: " + line)




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
        elif fields[0]=='counter':
            self.check_counters(line,fields[1:])
            return
        # OSC command
        elif fields[0] in ('osc','OSC'):
            if len(fields)<3:
                self.display('f','Show control - Too few fields in OSC command: ' + line)
                return
            else:
                dest=fields[1]
                self.check_osc(line,dest,fields[2:],v_show_labels)
            return

        if fields[0] not in ('exitpipresents','shutdownnow','reboot','open','openexclusive','close','closeall','monitor','event'):
                self.display('f','Show control - Unknown command in: ' + line)
                return
            
        if len(fields)==1:
            if fields[0] not in ('exitpipresents','shutdownnow','reboot','closeall'):
                self.display('f','Show control - Incorrect number of fields in: ' + line)
                return
            
        if len(fields) == 2:
            if fields[0] not in ('open','close','monitor','cec','event','openexclusive'):
                self.display('f','Show Control - Incorrect number of fields: ' + line)
            else:
                if fields[0] =='monitor' and fields[1] not in ('on','off'):
                    self.display('f',"Show Control - monitor parameter not on or off: "+ line)
                    return

                if fields[0] =='cec' and fields[1] not in ('on','standby','scan'):
                    self.display('f',"Show Control - monitor parameter not on standby or scan: "+ line)
                    return

                if fields[0] in ('open','close','openexclusive') and fields[1] not in v_show_labels:
                    self.display('f',"Show Control - cannot find Show Reference: "+ line)
                    return



    def check_osc(self,line,dest,fields,v_show_labels):
        if fields[0] not in ('exitpipresents','shutdownnow','reboot','open','close','openexclusive','closeall','monitor','event','send','server-info','loopback','animate'):
                self.display('f','Show control - Unknown command in: ' + line)
                return
            
        if len(fields)==1:
            if fields[0] not in ('exitpipresents','shutdownnow','reboot','closeall','server-info','loopback'):
                self.display('f','Show control, OSC - Incorrect number of fields in: ' + line)
                return
            
        if len(fields) == 2:
            if fields[0] not in ('open','close','openexclusive','monitor','event','send'):
                self.display('f','Show Control, OSC - Incorrect number of fields: ' + line)
            else:
                if fields[0] =='monitor' and fields[1] not in ('on','off'):
                    self.display('f',"Show Control, OSC - monitor parameter not on or off: "+ line)
                    return


 

    def check_counters(self,line,fields):
        if len(fields) < 2:
            self.display('f','Show Control too few fields in counter command - ' + ' ' +line)
            return          
        name=fields[0]
        command=fields[1]
        
        if command =='set':
            if len(fields) < 3:
                self.display('f','Show Control too few fields in counter command - ' +line)
                return          

            value=fields[2]
            if not value.isdigit():
                self.display('f','Show Control: value of counter is not a positive integer - ' +line)
                return

        elif command in ('inc','dec'):
            if len(fields) < 3:
                self.display('f','Show Control too few fields in counter command - '  +line)
                return          

            value=fields[2]
            if not value.isdigit():
                self.display('f','Show Control: value of counter is not a positive integer - ' +line)
                return      
        
        elif command =='delete':
            return

        else:
            self.display('f','Show Control: illegal counter comand - ' +line)
            return      

        return

                 
            
# ***********************************
# checking animation
# ************************************ 

    def check_animate_fields(self,field,line):
        fields= line.split()
        if len(fields) == 0: return

        if len(fields)<3:
            self.display('f','Too few fields in: ' + field + ", " + line)
            return

        delay_text=fields[0]
        if  not delay_text.isdigit(): self.display('f','Delay is not 0 or a positive integer in:' + field + ", " + line)

        name = fields[1]
        # name not checked - done at runtime

        out_type = fields[2]

        if out_type in ('state',):
            if len(fields) != 4:
                   self.display('f','wrong number of fields for State: ' + field + ", " + line)
            else:                   
                to_state_text=fields[3]
                if (to_state_text not in ('on','off')): self.display('f','Unknown parameter value in: ' + field + ", " + line)
        else:
            self.display('w','Unknown parameter type in: ' + field + ", " + line + ' This could be due to use of a new I/O plugin')

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
            self.display('t', "gpio.cfg not found in pp_home")
            tryfile=pp_dir+os.sep+'pp_resources'+os.sep+"gpio.cfg"
            if os.path.exists(tryfile):
                filename=tryfile
            else:
                self.display('w', "gpio.cfg not found in pipresents/pp_resources - GPIO checking turned off")
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
            self.display('f','Show must specify Web Window: ' + line)
            return
            
        if len(fields) == 0:
            return        

        #deal with warp which has 1 or 5  arguments
        # check basic syntax
        if  fields[0] !='warp':
            self.display('f','Web Window, Illegal command: ' + line)


        # deal with window coordinates or not   
        if len(fields) == 1:
            # fullscreen so line is just warp - ok
            return
        else:
            status,message,x1,y1,x2,y2 = parse_rectangle(' '.join(fields[1:]))
            if status=='error':
                self.display('f','Web Window: '+ message)
                return


                
# *************************************
# SHOW CANVAS
# ************************************              
                           
    def check_show_canvas(self,track_type,name,line):
        fields=line.split()
        if len(fields)== 0:
            return

        if len(fields) in (1,4):
            # window is specified
            status,message,x1,y1,x2,y2=parse_rectangle(line)
            if status=='error':
                self.display('f','Show Canvas: '+message)
                return
            else:
                return
        else:
            self.display('f','Wrong number of fields in Show canvas: '+ line)



# *************************************
# IMAGE WINDOW
# ************************************

    def check_image_window(self,track_type,field,line):
    
        fields = line.split()
        
        if track_type == 'show' and len(fields) == 0:
            self.display('f','Show must specify Image Window: ' + field + ", " + line)
            return
            
        if len(fields) == 0:
            return

        
        # deal with original whch has 0 or 2 arguments
        image_filter=''
        if fields[0] == 'original':
            if len(fields) not in (1,3):
                self.display('f','Image Window, Original has wrong number of arguments')
                return
            
            # deal with window coordinates    
            if len(fields)  ==  3:
                # window is specified
                if not (fields[1].isdigit() and fields[2].isdigit()):
                    self.display('f','Image Window, coordinates are not numbers')
            return

        # deal with remainder which has 1, 2, 5 or  6arguments
        # check basic syntax
        if  fields[0] not in ('shrink','fit','warp'):
            self.display('f','Image Window, illegal command: '+fields[0])
        if len(fields) not in (1,2,3,5,6):
            self.display('f','wrong number of fields in: '+ line)
            return
        if len(fields) == 6 and fields[5] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS'):
            self.display('f','wrong filter: '+ fields[5]+ ' in '+ line)
            return
        if len(fields) == 2 and (fields[1] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS') and '*' not in fields[1]):
            self.display('f','wrong filter: '+ fields[1]+ ' in '+ line)
            return
        if len(fields) == 3 and fields[2] not in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS'):
            self.display('f','wrong filter: '+ fields[2]+ ' in '+ line)
            return


        # deal with no window coordinates and no filter
        if len(fields) == 1:         
            return
   
        # deal with window coordinates in +* format with optional filter
        if len(fields) in (2,3) and '*' in fields[1]:
            status,message,x1,y1,x2,y2 = parse_rectangle(fields[1])
            if status=='error':
                self.display('f','Image Window, '+message)
                return
            
        if len(fields) in (5,6):
            # window is specified in x1 y1 x2 y2
            if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                self.display('f','coords are not numbers')
                return

                     
# *************************************
# VIDEO WINDOW
# ************************************
                    
    def check_omx_window(self,track_type,field,line):

        fields = line.split()
        if track_type == 'show' and len(fields) == 0:
            self.display('f','show must have video window: ' + field + ", " + line)
            return
            
        if len(fields) == 0:
            return

        # deal with original which has 1
        if fields[0] == 'original':
            if len(fields)  !=  1:
                self.display('f','Video Window, wrong number of fields for original in: '+line)  
                return
        else:
            # deal with warp which has 1 or 5  arguments
            # check basic syntax
            if  fields[0]  != 'warp':
                self.display('f','Video Window, '+fields[0] + 'is not a valid type in : '+ line)
            else:
            
                if len(fields) not in (1,2,5):
                    self.display('f','Video Window, wrong number of coordinates for warp in: '+ line)
                    return
                                 
                # deal with window coordinates    
                if len(fields) == 1:
                    return 
                else:
                    # window is specified
                    status,message,x1,y1,x2,y2=parse_rectangle(' '.join(fields[1:]))
                    if status == 'error':                                   
                        self.display('f','Video Window, '+message)




