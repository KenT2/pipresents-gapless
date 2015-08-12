import os
import json
import ConfigParser
import re
#import Image
import PIL.Image
from PIL import ImageDraw, ImageFont, ImageMode, ImageTk # color names
from Tkinter import Tk, Toplevel, Scrollbar,Text
from Tkinter import VERTICAL,RIGHT,LEFT,BOTH,Y,NORMAL,END,DISABLED
import ttk
import tkFont
from tkconversions import *
import pp_paths
from pp_utils import enum

from pp_definitions import PPdefinitions, PROFILE, SHOW, LIST, TRACK, FIELD

ValidationSeverity = enum('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'OK')
# shorter ways to call these
CRITICAL = ValidationSeverity.CRITICAL
ERROR    = ValidationSeverity.ERROR
WARNING  = ValidationSeverity.WARNING
INFO     = ValidationSeverity.INFO

SAME = ''  # for setting a current item without changing other current items

ValidationRuleTypes = enum('INVALID_VALUE', 'MISSING_FILE')

def get_showref(show):
    if show:
        return show['show-ref']
    else:
        return ''
def get_trackref(track):
    trackref = track['track-ref']
    if not trackref: trackref = track['title']
    if not trackref: trackref = track['locatoin']
    return trackref
def get_track_title(track):
    title = track['title']
    if not title: title = track['track-ref']
    if not title: title = track['location']
    return title

class RuleResult(object):
    true = None
    blank = None

    def __init__(self, passed=None, message=None, blank=None):
        self.passed  = passed
        self.message = message
        self.blank   = blank  # hmm, not to be confused with RuleResult.blank
        if RuleResult.__dict__.get('true') == None:
            setattr(RuleResult, 'true', '')     # prevent recursion
            setattr(RuleResult, 'blank', '')
            RuleResult.true = RuleResult(True)  # set the actual item
            RuleResult.blank = RuleResult(True, blank=True)

dummy = RuleResult(True).passed # force instantiation of RuleResult.true by creating an instance

class ValidationResult(object):

    def __init__(self, validator, objtype, severity, **kwargs):
        self.objtype   = objtype                     # PROFILE, SHOW, LIST, TRACK
    	self.severity  = severity                    # CRITICAL, ERROR, WARNING, (INFO?), (OK?)
        self.text      = kwargs.pop('text', '')      # title for collapsible items, message for errors, etc.
        self.show      = validator.current_show
        self.list      = validator.current_list
        self.track     = validator.current_track

        # references
        self.showref  = ''
        self.listref  = ''
        self.trackref = ''
        if self.show:  self.showref  = self.show['show-ref']
        if self.list:  self.listref  = self.list
        if self.track: self.trackref = get_trackref(self.track)

        if self.objtype == PROFILE:
            pass
        if self.objtype == TRACK:
            self.id = ".{0}.{1}.{2}".format(self.showref, self.listref, self.trackref)
        elif self.objtype == LIST:
            self.id = ".{0}.{1}".format(self.showref, self.listref)
        elif self.show:
            self.id = ".{0}".format(self.showref)
        else:
            print "Something wrong... show:{0}, list:{1}, track{2}" \
                .format(self.showref, self.listref, self.trackref)
        #print "id: " + self.id

    def __cmp__(self, other):
        if self.severity  == other.severity: return 0
        if self.severity  == INFO: return -1
        if other.severity == INFO: return  1
        if self.severity  == WARNING: return -1
        if other.severity == WARNING: return  1
        if self.severity  == ERROR: return -1
        if other.severity == ERROR: return  1
        if self.severity  == CRITICAL: return -1
        return 1

    def is_profile(self):
        return self.objtype == PROFILE
    def is_show(self):
        return self.objtype == SHOW
    def is_list(self):
        return self.objtype == LIST
    def is_track(self):
        return self.objtype == TRACK


class Validator(object):

    def __init__(self, editor_issue=None):
        self.pp_home = pp_paths.pp_home
        self.pp_profile = pp_paths.pp_profile_dir
        self.editor_issue = editor_issue

        self.scope = None
        self.result = None          # indicates whether the validator has been initialized
        self.results = []           # list of ValidationResult, povides referenceable results
        self.v_medialist_refs = []  # list of medialist file references (used for ?)
        self.v_show_labels = []     # (same order as in editor) used for checking uniqueness
        self.v_start_shows = []     # used for checking number of start shows

    def initialize(self, scope, title="", display=False):

        # CREATES
        # v_media_lists    - file names of all medialists in the profile
        # v_shows
        # v_track_labels   - list of track labels in current medialist.
        # v_show_labels    - list of show labels in the showlist
        # v_medialist_refs - list of references to medialist files in the showlist

        # initialize results display
        self.result = ResultWindow(title, display)
        self.scope = scope

        # always need to these sanity checks
        self.set_current(None, None, None, checking=PROFILE)
        self.result.add_profile(self.pp_profile)

        if not self.check_file_exists(PROFILE, CRITICAL, [self.pp_profile, "pp_showlist.json"], 
            "pp_showlist not in profile", abort=True):
            return False
        ifile = open(self.pp_profile+os.sep+"pp_showlist.json", 'rb')
        sdict = json.load(ifile)
        ifile.close()
        self.v_shows = sdict['shows']
        if 'issue' in sdict:
            profile_issue = sdict['issue']
        else:
            profile_issue ="1.0"
        if not self.check_profile_compatible_with_editor(profile_issue, self.editor_issue):
            print "not compatible"
            return False

        # read the gpio config
        # gpio_cfg_ok=read_gpio_cfg(pp_dir,pp_home,pp_profile)

        # create lists for checks
        for show in self.v_shows:
            self.result.add_show(show)  # add shows here so medialists can be added
            if show['type'] == 'start': 
                self.v_start_shows.append(show)
            else:
                self.v_show_labels.append(show['show-ref'])
                self.v_medialist_refs.append(show['medialist'])
        return True

    def validate_profile(self, display=False):
        if not self.initialize(PROFILE, "Validate "+self.pp_profile, display):
            return False

        # CHECK ALL MEDIALISTS AND THEIR TRACKS
        self.v_media_lists = []
        files = os.listdir(self.pp_profile)
        if files: files.sort()
        for medialist_file in files:
            self.check_medialist(medialist_file)

        # SHOWS
        # now we can check the shows
        for show in self.v_shows:
            # critical errors on a show only abort checking for that show
            #print "Checking show: ", show['show-ref'], ', ', show['title']
            self.check_show(show)

        # PROFILE
        self.set_current(None, None, None, msg="\nChecking for start show")
        self.check_start_show_is_required(len(self.v_start_shows))

        # ALL DONE
        self.result.display('t', "\nValidation Complete")
        self.result.stats()
        if self.result.num_errors() == 0:
            return True
        else:
            return False

    def validate_widget(self, objtype, obj, field):
        self.scope = FIELD
        if self.result is None:
            raise ValueException("The validator needs to be initialized before calling this method.")
        # 'field' is the name of the field in the specs and the rules.
        result = self.process_ruleset(objtype, obj, field)
        return result

    def check_show(self, show):
        self.result.add_show(show)
        self.set_current(show, None, None, checking=SHOW)
        #print "Checking show: ", show['show-ref'], "------------------------------"
        if show['type'] == "start":
            self.check_one_start_show(len(self.v_start_shows))
            self.check_valid_show_label(show)
            self.check_start_show_calls_valid_show(show, self.v_show_labels)
        else:
            self.check_unique_show_label(show, self.v_show_labels)

            # abort if we can't check the medialist/tracks
            if not self.check_show_has_valid_medialist(show):
                return False

            # open medialist and produce a dictionary of its contents for use later
            ifile  = open(self.pp_profile + os.sep + show['medialist'], 'rb')
            tracks = json.load(ifile)['tracks']
            ifile.close()

            # make a list of the track labels
            v_track_labels=[]
            for track in tracks:
                self.result.add_track(show['show-ref'], show['medialist'], track)
                if track['track-ref'] !='':
                    v_track_labels.append(track['track-ref'])
                #self.check_track_options(show['show-ref'], show['medialist'], track)
                       
            # check each field for the show, as defined by the show field specs
            specs = PPdefinitions.show_field_specs
            scheme = PPdefinitions.show_field_rules
            for field in show: #PPdefinitions.show_types[show['type']]:
                #try:
                    self.process_ruleset(SHOW, show, field)
                #except Exception as e:
                #    print "An exception occurred on {0} {1}, field {2}: {3}".format('show', show['show-ref'], field, e)

        return True

    def ensure_ruleset_is_list(self, ruleset):
        # transform string and dist objects to list
        if isinstance(ruleset, dict):
            ruleset = [ruleset, ]
        elif isinstance(ruleset, str):
            ruleset = [ruleset, ]
        elif isinstance(ruleset, list):
            pass
        else:
            raise TypeError("Ruleset is unexpected type: {0}".format(ruleset.__class__.__name__))
        return ruleset

    def ensure_fields_is_list(self, fields):
        if isinstance(fields, str):
            fields = [fields, ]
        elif isinstance(fields, list):
            pass
        else:
            raise TypeError("Ruleset is unexpected type: {0}".format(fields.__class__.__name__))
        return fields

    def process_ruleset(self, objtype, obj, field, dependent_field=None):
        is_dependency = dependent_field is not None
        if objtype == SHOW:
            specs = PPdefinitions.show_field_specs
            scheme = PPdefinitions.show_field_rules
        elif objtype == TRACK:
            specs = PPdefinitions.track_field_specs
            scheme = PPdefinitions.track_field_rules
        else:
            # medialist is not an item that gets edited
            raise StandardError("This type of object cannot be validated.")
        spec = specs[field]
        value = obj[field]

        # check if blank and whether a value is required
        if value is None or value == '':
            if spec['must'] != 'no':
                self.add_value_required_error(objtype, spec['text'])
            if is_dependency:
                # it may be better for the rule for the field to determine whether the value is blank
                msg = "{0} is blank, but is required for {1}".format(field, dependent_field)
                self.add_error(objtype, msg)
            return RuleResult.true

        rule_field = field.replace('colour', 'color')  # 'color' is the standard python spelling
        if rule_field not in scheme:
            #print "Scheme does not have a rule for ", rule_field
            return RuleResult.true

        rulesets = scheme[rule_field]
        for ruleset in rulesets:
            ruleset = self.ensure_ruleset_is_list(ruleset)

            for rulespec in ruleset:
                rule = None
                args = None
                reqs = None
                deps = None
                farg = None
                if isinstance(rulespec, str):
                    rule = rulespec
                elif isinstance(rulespec, dict):
                    if 'rule'            in rulespec: rule = rulespec['rule']
                    if 'args'            in rulespec: args = rulespec['args']
                    if 'required-fields' in rulespec: reqs = rulespec['required-fields']
                    if 'depends-on'      in rulespec: deps = rulespec['depends-on']
                    if 'field-arg'       in rulespec: farg = rulespec['field-arg']
                else:
                    print "Rule: ", rule, " (", rule.__class__.__name__, ")"
                if args == 'show-labels':
                    args = self.v_show_labels
                elif args == 'track-labels':
                    args = self.v_track_labels

                # skip the rule if it depends on a different field (checking is done by the other field)
                if deps is not None:
                    #deps = self.ensure_fields_is_list(deps)
                    if not is_dependency:
                        # if we're validating a widget, we should call the ruleset for the other rules?
                        # if we're validating a show or presentation, we should skip the dependent rule
                        if self.scope == PROFILE:
                            #print "Skipping dependent rule: ", field
                            return RuleResult.true
                        deps = self.ensure_fields_is_list(deps)
                        for dep in deps:
                            #print "Processing dependent rule: ", dep
                            result = self.process_ruleset(objtype, obj, dep)
                            if result.passed is False:
                                return result
                            if result.blank is True:
                                return RuleResult.blank

                if rule is None:
                    reqs = self.ensure_fields_is_list(reqs)
                    if reqs:
                        for req in reqs:
                            #print "Checking dependencies for rule (1) ", field
                            result = self.process_ruleset(objtype, obj, req, dependent_field=field)
                            return result
                    else: return RuleResult.true

                rule_name = 'rule_' + rule.replace('-', "_")
                rule_func = getattr(self, rule_name)
                #print "Checking: {0}({1})".format(rule_name, value)
                if args and farg:
                    rule_result = rule_func(value, args, obj[farg])
                elif args:
                    rule_result = rule_func(value, args)
                elif farg:
                    rule_result = rule_func(value, obj[farg])
                else:
                    rule_result = rule_func(value)

                if is_dependency and rule_result.blank is True:
                    # the rule validated, but it's blank and it's required for a dependent rule
                    msg = "{0} is blank, but is required for {1}".format()
                    rule_result.passed = False

                if rule_result.passed is False:
                    if rule_result.message:
                        # the rule method doesn't know the field name, so we add it here
                        msg = "{0}: {1}".format(spec['text'], rule_result.message)
                        self.add_error(SHOW, msg)
                    else:
                        msg = "{0}: {1} is an invalid value".format(spec['text'], value)
                        self.add_error(SHOW, msg)
                    #self.add_invalid_value_result(SHOW, severity, spec['text'], value)
                elif rule_result.passed is True:
                    if reqs and rule_result.blank is not True:
                        for req in reqs:
                            print "Checking dependencies for rule (2) ", field
                            self.process_ruleset(objtype, obj, req, dependent_field=field)
        if rule_result is not None and rule_result.passed is False:
            print field, ": ", rule_result.message
        return rule_result

    def dummy(self):
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
            return True

    def check_medialist(self, medialist_file):
        # find the associated show
        show = None
        for eshow in self.v_shows:
            if 'medialist' in eshow:
                if eshow['medialist'] == medialist_file:
                    show = eshow
                    break
        showref = ""
        if show: showref=show['show-ref']
        if medialist_file == 'pp_showlist.json':
            self.result.add_list('.', medialist_file) # make child item of profile
        else:
            self.result.add_list(showref, medialist_file)
        self.set_current(show, medialist_file, None)

        if not medialist_file.endswith(".json") and medialist_file not in ('pp_io_config','readme.txt'):
            return self.add_critical(LIST, "Invalid medialist in profile: {0}".format(medialist_file), abort=False)
            
        if medialist_file.endswith(".json") and medialist_file not in  ('pp_showlist.json','schedule.json'):
            self.set_current(show, medialist_file, None, checking=LIST)
            self.v_media_lists.append(medialist_file)

            # open a medialist and test its tracks
            ifile = open(self.pp_profile + os.sep + medialist_file, 'rb')
            sdict = json.load(ifile)
            ifile.close()                          
            tracks = sdict['tracks']
            if 'issue' in sdict:
                medialist_issue= sdict['issue']
            else:
                medialist_issue="1.0"
                  
            # check issue of medialist
            if medialist_issue  !=  self.editor_issue:
                return self.add_critical(LIST, "Medialist version {0} does not match this editor (version {1})" \
                    .format(medialist_issue, editor_issue), abort=False)

            # open a medialist and test its tracks
            self.v_track_labels=[]
            anonymous=0
            for track in tracks:
                self.check_track(track, anonymous)


    def check_track(self, track, anonymous):
        self.set_current(track=track, checking=TRACK)
        showref = get_showref(self.current_show)
        listref = self.current_list
        self.result.add_track(showref, listref, track)
        trackref = get_trackref(track)
        tracktitle = get_track_title(track)

        # check each field for the track, as defined by the field specs
        for field in track:
            try:
                self.process_ruleset(TRACK, track, field)
            except Exception as e:
                print "An exception occurred on {0} {1}, field {2}: {3}".format('track', get_trackref(track), field, e)
        return True

    def dummy_track(self):
        # check track-ref
        if track['track-ref'] == '':
            anonymous+=1
        else:
            if track['track-ref'] in self.v_track_labels:
                self.result.display('f',"'duplicate track reference: "+ track['track-ref'])
            self.v_track_labels.append(track['track-ref'])

        # warn if media tracks blank where optional
        if track['type'] in ('audio','image','web','video'):
            if track['location'].strip() == '':
                self.result.display('w',"blank location")
        
        # check location of absolute and relative media tracks where present                   
        if track['type'] in ('video','audio','image','web'):    
            track_file=track['location']
            if track_file.strip() != '':
                if track_file[0] == "+":
                    track_file=pp_home+track_file[1:]
                self.check_file_exists(TRACK, ERROR, track_file)

        if track['type'] in ('video','audio','message','image','web','menu'):
            
            # check common fields
            self.check_animate('animate-begin',track['animate-begin'])
            self.check_animate('animate-end',track['animate-end'])
            self.check_plugin(track['plugin'],self.pp_home)
            self.check_show_control(track['show-control-begin'],self.v_show_labels)
            self.check_show_control(track['show-control-end'],self.v_show_labels)
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
                if track['sub-show'] not in self.v_show_labels: self.result.display('f',"Sub-show "+track['sub-show'] + " does not exist")
                
    # if anonymous == 0 :self.result.display('w',"zero anonymous tracks in medialist " + file)

    # check for duplicate track-labels
    # !!!!!!!!!!!!!!!!!! add check for all labels


    def add_result(self, objtype, severity, msg, **kwargs):
        if severity == CRITICAL: return self.add_critical(objtype, msg, **kwargs)
        if severity == ERROR   : return self.add_error   (objtype, msg, **kwargs)
        if severity == WARNING : return self.add_warning (objtype, msg, **kwargs)

    def add_critical(self, objtype, msg, **kwargs):
        abort = kwargs.pop('abort', True)
        result = ValidationResult(self, objtype, CRITICAL, text=msg, **kwargs)
        self.results.append(result)
        if msg == '': raise ValueError("The error message was empty.")
        self.result.display('c', msg)
        if abort:
            self.result.display('t', "\nValidation Aborted")
            self.result.stats()
        self.result.add_result(result)
        return abort

    def add_error(self, objtype, msg, **kwargs):
        # possible kwargs: show, medialist, track, text
        result = ValidationResult(self, objtype, ERROR, text=msg, **kwargs)
        self.results.append(result)
        if msg == '': raise ValueError("The error message was empty.")
        self.result.display('f', msg)
        self.result.add_result(result)

    def add_warning(self, objtype, msg, **kwargs):
        # possible kwargs: show, medialist, track, text
        result = ValidationResult(self, objtype, ERROR, text=msg, **kwargs)
        self.results.append(result)
        if msg == '': raise ValueError("The warning message was empty.")
        self.result.display('f', msg)
        self.result.add_result(result)

    def check_file_exists(self, objtype, severity, path, format='', **kwargs):
        arg = kwargs.pop('arg', 'path')
        if not format: format = "File not found: '{" + arg + "}'"
        return self.check_path_exists(objtype, severity, path, format, **kwargs)

    def check_dir_exists(self, objtype, severity, path, format='', **kwargs):
        arg = kwargs.pop('arg', 'path')
        if not format: format = "Directory not found: '{" + arg + "}'"
        return self.check_path_exists(objtype, severity, path, format, **kwargs)

    def check_path_exists(self, objtype, severity, path, format='', **kwargs):
        if isinstance(path, basestring): path = path.strip()
        else                           : path = os.path.join(*[x.strip() for x in path])
        success = os.path.exists(path)
        if not success:
            arg = kwargs.pop('arg', 'path')
            if not format: 
                format = "Path not found: '{" + arg + "}'"
            format = format.replace("{filename}", "{basename}").replace("{0}", "{path}")
            #print "format '{0}', path='{1}'".format(format, path)
            message = format.format(
                path=path, 
                abspath=os.path.abspath(path), relpath=os.path.relpath(path),
                dirname=os.path.dirname(path), basename=os.path.basename(path))
            self.add_result(objtype, severity, message, **kwargs)
        return success

    def path_exists(self, path):
        # Arguments
        # path     :  Can be a string or a list to join with os.path.join()
        # format   :  Formatter string on which to apply format().
        # arg      :  If 'format' is not supplied, 'arg' can be used to select
        #             the named path argument that gets used in the default format.
        #
        # Named Arguments in the formatter
        # The following named arguments can be used in the formatter : 
        #    {path}                : path as provided
        #    {filename}            : alias for basename
        #    {abspath}, {relpath}  : as in os.path.xxxxx
        #    {dirname}, {basename} : as in os.path.xxxxx
        #
        if isinstance(path, basestring): path = path.strip()
        else                           : path = os.path.join(*[x.strip() for x in path])
        return os.path.exists(path)

    def check_profile_compatible_with_editor(self, profile_issue, editor_issue):
        if editor_issue == None:
            return True
        if profile_issue != editor_issue:
            self.add_critical(PROFILE, "Profile version {0} does not match this editor (version {1})" 
                .format(profile_issue, editor_issue), abort=True)
            return False
        return True

    def check_valid_show_label(self, show):
        result = self.rule_is_showref(show['show-ref'], show['type'])
        if result.passed is False:
            self.add_error(SHOW, result.message)
        return result.passed

    def check_unique_show_label(self, show, labels):
        showref = show['show-ref']
        if labels.count(showref) > 1:
            self.add_error(SHOW, "Show labels must be unique. '{0}' is not unique.".format(showref))
            return False
        return True

    def check_start_show_calls_valid_show(self, show, labels):
        passed = True
        text=show['start-show']
        show_count=0
        fields = text.split()
        for field in fields:
            show_count+=1
            if field not in labels:
                self.add_error(SHOW, "Start show calls label '{0}', which was not found".format(field))
                passed = False
        if show_count == 0:
            self.add_error(SHOW, "Start show needs to call a show".format(field))
            passed = False
        return passed

    def check_one_start_show(self, count):
        if count > 1 : self.add_error(SHOW, "Only one start show is allowed")
        return count > 1

    def check_start_show_is_required(self, count):
        if count != 1: self.add_error(SHOW, "A start show is required")
        return count == 1

    def check_show_has_valid_medialist(self, show):
        passed = True
        list = show['medialist']
        if list == '':
            self.add_error(SHOW, "Medialist cannot be blank")
            passed = False
        if '.json' not in list:
            self.add_error(SHOW, "Medialist '{0}' needs to be a .json file".format(list))
            passed = False
        if list not in self.v_media_lists:
            self.add_error(SHOW, "Medialist '{0}' was not found.".format(list))
            passed = False
        exists = self.check_file_exists(SHOW, CRITICAL, [self.pp_profile, list], 
            format="Medialist file '{0}' does not exist", abort=False)
        return (passed and exists)

# ValidationResult helpers

    def set_current(self, show=SAME, list=SAME, track=SAME, msg='', **kwargs):
        # set show, list or track to empty string to ignore them, which is useful
        # for updating only one of the parameters.
        # Setting to None will update the parameter.
        if show  != SAME: self.current_show = show
        if list  != SAME: self.current_list = list
        if track != SAME: self.current_track = track
        if not msg:
            checking = kwargs.pop('checking', '')
            if checking == PROFILE: msg = "\nVALIDATING PROFILE '{0}'".format(self.pp_profile)
            if checking == SHOW   : msg = "\nChecking show '{0}'".format(show['title'])
            if checking == LIST   : msg = "\nChecking medialist '{0}'".format(list)
            if checking == TRACK  : msg = "    Checking track '{0}'".format(track['title'])
        if msg: 
            append_msg = kwargs.pop('append_msg', '')
            self.result.display('t', msg + append_msg)

    def add_invalid_value_result(self, objtype, severity, value, **kwargs):
        self.add_result(objtype, severity, "Invalid value for {0}: '{1}".format(field, value), **kwargs)

    def add_invalid_value_error(self, objtype, field, value, **kwargs):
        self.add_error(objtype, self.get_invalid_value_message(field, value), **kwargs)

    def get_invalid_value_message(self, field, value):
        return "Invalid value for {0}: '{1}'".format(field, value)

    def add_value_required_error(self, objtype, field, **kwargs):
        self.add_error(objtype, "A value is required for {0}".format(field), **kwargs)

    def is_blank(self, value):
        # rules should validate if the value is blank, except for the rule that requires a non-blank value.
        # If an item is required to be non-blank, it should include the is-not-blank rule 
        # (which would fail for blank values) in addition to any other rule(s) needed to 
        # validate non-blank values (which would pass for blank values)
        return value is None or value == ''

    def rule_is_filetype(self, value, extension_spec):
        # extension spec: first element describes the type, e.g. 'Image Files'
        # elements after that describe the extensions
        if self.is_blank(value): return RuleResult.blank
        ftype = extension_spec.pop(0).lower()
        ext = os.path.splitext(value)
        if ext in extensions:
            return RuleResult.true
        return RuleResult(False, "'{0}' is not the correct extension for {1}".format(ext, ftype))

    def rule_dir_exists(self, value):
        if self.is_blank(value): return RuleResult.blank
        if pp_paths.get_dir(value) is None:
            return RuleResult(False, "'{0}' does not exist.")

    def rule_file_exists(self, value):
        if self.is_blank(value): return RuleResult.blank
        if pp_paths.get_file(value) is None:
            return RuleResult(False, "'{0}' does not exist.".format(value))
        return RuleResult.true

    def rule_is_location(self, value):
        if self.is_blank(value): return RuleResult.true
        if value.startswith("http://"):
            # assume URL is good ... ?
            return RuleResult.true
        return self.rule_file_exists(value)

    def is_int(self, value):
        try:
            value = long(value)
            if isinstance(value, long):
                return True
        except:
            pass
        return False

    def is_zero_or_positive_integer(self, value):
        return self.is_integer(value) and long(value) >= 0

    def is_zero_or_positive_number(self, value):
        return self.is_number(value) and long(value) >= 0

    def is_x_y(self, value):
        if isinstance(value, basestring):
            fields = value.split()
        else:
            fields = list(value)
        x = fields[0]
        y = fields[1]
        return self.is_integer(x) and self.is_integer(y)

    def rule_is_not_blank(self, value):
        if not self.is_blank(value):
            return RuleResult.true
        return RuleResult(False, "Cannot be blank.")

    def rule_is_boolish(self, value):
        if isinstance(value, basestring):
            if value == "": return RuleResult.blank
            value = value.lower()
            if value in ("yes",  "no"   ): return RuleResult.true
            if value in ("true", "false"): return RuleResult.true
            if value in ("0",    "1"    ): return RuleResult.true
        if isinstance(value, (int,long)):
            if value in (0, 1): return RuleResult.true
        return RuleResult(False, "'{0}' needs to evaluate to true/false, yes/no, etc.")

    def rule_is_yes_no(self, value):
        if isinstance(value, basestring):
            value = value.lower()
            if value in ("yes", "no"): return RuleResult.true
        return RuleResult(False, "'{0}' needs to be 'yes' or 'no'.")

    def rule_is_integer(self, value):
        try:
            if isinstance(value, basestring):
                if value == "": return RuleResult.blank
                value = long(value)
                #print "is_integer: ", value
            if isinstance(value, (int, long)):
                return RuleResult.true
        except:
            pass
        return RuleResult(False, "'{0}' needs to be an integer.".format(value))

    def rule_is_zero_or_positive_integer(self, value):
        try:
            if isinstance(value, basestring):
                if value == "": return RuleResult.blank
                value = long(value)
            if isinstance(value, (int, long)) and value >= 0:
                return RuleResult.true
        except:
            pass
        return RuleResult(False, "'{0}' needs to be zero or a positive integer.".format(value))

    def rule_is_x_y(self, value):
        if not self.is_x_y(value):
            return RuleResult(False, "x and y coordinates need to be integers.")
        return RuleResult.true

    def rule_is_rectangle(self, value):
        if isinstance(value, basestring):
            fields = value.split()
        else:
            fields = list(value)
        tx = fields[0]
        ty = fields[1]
        bx = fields[2]
        by = fields[3]
        if not self.is_integer(tx) or not self.is_integer(ty) \
        or not self.is_integer(bx) or not self.is_integer(by):
            return RuleResult(False, "The top-left and bottom-right coordinates need to be integers.")
        if not tx < bx:
            return RuleResult(False, "The left x coordinate needs to be a lower value than the right x coordinate.")
        if not ty < by:
            return RuleResult(False, "The top y coordinate needs to be a lower value than the bottom y coordinate.")
        return RuleResult.true

    def rule_is_in_range(self, value, range):
        if self.is_blank(value): return RuleResult.blank
        try:
            val = long(value)
            if val >= range[0] and val <= range[1]:
                return RuleResult.true
        except:
            pass
        return RuleResult(False, "'{0}' is not in range ({1} to {2})".format(value, range[0], range[1]))

    def rule_is_hh_mm_ss(self, value):
        value = value.lower().strip()
        fields = value.split(":")
        if len(fields) == 1:
            secs = fields[0]
            result = self.rule_is_zero_or_positive_integer(secs)
            if not result.passed is True:
                return result # RuleResult(False, "Valid formats are hh:mm:ss, mm:ss or ss.")
            if int(secs) > 59:
                return RuleResult(False, "For times longer than 59 seconds, use hh:mm:ss or mm:ss.")
            return RuleResult.true
        if self.is_blank(value): return RuleResult.blank
        pattern = r"""^                 # Start of string
                    (?:                 # Try to match...
                     (?:                #  Try to match...
                      ([01]?\d|2[0-3]): #   HH:
                     )?                 #  (optionally).
                     ([0-5]?\d):        #  MM: (required)
                    )?                  # (entire group optional, so either HH:MM:, MM: or nothing)
                    ([0-5]?\d)          # SS (required)
                    $                   # End of string
                    """
        result = self.rule_is_regex_match(value, pattern)
        if result.passed is False: 
            result.message = "'{0}' is not a valid time. Valid formats are hh:mm:ss, mm:ss or ss.".format(value)
        return result

    def rule_is_regex_match(self, value, regex):
        if self.is_blank(value): return RuleResult.blank
        if re.match(regex, value) is None:
            return RuleResult(False, "The value did not pass validation.")
        else: return RuleResult.true

    def rule_is_medialist_file(self, value):
        if self.is_blank(value):
            return RuleResult(False, "Medialist cannot be blank.")
        if '.json' not in value:
            return RuleResult(False, "Medialist '{0}' needs to be a .json file.".format(value))
        if os.path.exists(os.path.join(self.pp_profile, value)) is None:
            #return RuleResult(False, "'{0}' does not exist.")
            return RuleResult(False, "Medialist file '{0}' was not found.".format(value))
        return RuleResult.true

    def rule_is_image_file(self, value):
        if self.is_blank(value): return RuleResult.blank
        try:
            img = Image.open(value)
            return RuleResult.true
        except Exception as ex:
            print "is_image_file: " + str(ex)
        return RuleResult(False, "'{0}' is not a valid image file.".format(value))

    def rule_is_color(self, value):
        val = value.lower().strip()
        if self.is_blank(val): return RuleResult.blank
        # try drawing something with the color to see if it works
        ex = None
        try:
            root = None
            w = Canvas(root, width=0, height=0)
            w.create_line(0,0, 0,0, fill=value)
            #img = PIL.Image.new("RGB", (0,0))
            #draw = ImageDraw.Draw(img)
            #draw.point((0,0), fill=value)
            return RuleResult.true
        except Exception as ex:
            pass
        return RuleResult(False, "'{0}' is not a valid color. Use a color name or a hex format like '#rrggbb' (with '#').".format(value))

    def rule_is_font(self, value):
        if self.is_blank(value): return RuleResult.blank
        ex = None
        try:
            family = value
            family = re.sub(r"\{(.*)\}.*", r"\1", family) # using the font picker adds the brackets
            family = re.sub(r"\s\d+\s.*", "", family)     # brackets are not required
            if family in tkFont.families():
                size = re.sub(r".*\s([\d]+).*", r"\1", value)
                size = int(size)
                # we have the size, now what? 
                # font can be negative to specify pixel units
                # non-zero? integer? absolute max?
                style = value.lower()
                style = re.sub(r".*\d+\s([a-z\s])", r"\1", style)
                if style != value:  # match found
                    styles = style.split(' ')
                    for style in styles:
                        if not styles in ("bold", "normal", "italic", "roman", "underline", "overstrike"):
                            return RuleResult(False, "'{0}'' is not a valid font style.".format(style))
                return RuleResult.true
            else:
                return RuleResult(False, "'{0}' was not found in the system's font list.".format(family))
            #root = None
            #w = Canvas(root, width=0, height=0)
            #w.create_text(0,0, text="dummy", font="blah")
        except Exception as ex:
            print "is_font Exception: " + str(ex)
            pass
        return RuleResult(False, "'{0} (family={1})' is not a valid font ({2}).".format(value, family, ex))

    def rule_is_text_justify(self, value):
        if self.is_blank(value): return RuleResult.blank
        if value not in ('center', 'left', 'right'):
            return RuleResult(False, "'{0}' needs to be 'left', 'center', or 'right'.")
        return RuleResult.true

    def rule_is_image_window(self, value):
        if self.is_blank(value): return RuleResult.blank
        fields = value.lower().split()
        if fields[0] not in ('original', 'fit', 'shrink', 'warp'):
            return RuleResult(False, "'{0}' needs to be 'original', 'fit', 'shrink', or 'warp'.".format(fields[0]))
        if fields[0] == 'original' and not len(fields) in (1,3):
            return RuleResult(False, "'original' takes 0 parameters (centered) or 2 coordinates (top left).")
        if fields[0] == 'original' and len(fields) == 3:
            if not self.is_integer(fields[1]) \
            or not self.is_integer(fields[2]):
                return RuleResult(False, "x and y coordinates need to be integers.")
        if fields[0] in ('fit', 'shrink', 'warp'):
            if len(fields) not in (1,2,5,6):
                return RuleResult(False, "'{0}' takes 0 (centered), 4 (top-left, bottom-right), or 5 (with filter) parameters.".format(fields[0]))
            if len(fields) in (5,6):
                result = self.rule_is_rectangle([fields[1], fields[2], fields[3], fields[4]])
                if not result.passed:
                    return result
            if len(fields) in (2,6):
                if fields[len(fields)-1] not in ('nearest', 'bilinear', 'bicubic', 'antialias'):
                    return RuleResult(False, "The filter needs to be 'nearest', 'bilinear', 'bicubic', or 'antialias'.")
        return RuleResult.true

    def rule_is_video_window(self, value):
        if self.is_blank(value): return RuleResult.blank
        fields = value.lower().split()
        if fields[0] not in ('original', 'warp'):
            return RuleResult(False, "'{0}' needs to be 'original' or 'warp'.".format(fields[0]))
        if fields[0] == 'original' and not len(fields) == 1:
            return RuleResult(False, "'original' does not take any parameters.")
        if fields[0] == 'warp':
            if len(fields) not in (1,5):
                return RuleResult(False, "'warp' takes 0 (fit screen) or 4 parameters (top-left and bottom-right).")
            if len(fields) == 5:
                result = self.rule_is_rectangle([fields[1], fields[2], fields[3], fields[4]])
                if not result.passed:
                    return result
        return RuleResult.true

    def rule_is_web_window(self, value):
        if self.is_blank(value): return RuleResult.blank
        fields = value.lower().split()
        if fields[0] not in ('warp', ):
            return RuleResult(False, "'{0}' needs to be 'warp'.".format(fields[0]))
        if len(fields) not in (1,5):
            return RuleResult(False, "'warp' takes 0 (size to screen) or 4 parameters (rectangle).")
        if len(fields) == 5:
            result = self.rule_is_rectangle([fields[1], fields[2], fields[3], fields[4]])
            if not result.passed:
                return result
        return RuleResult.true

    def rule_is_menu_window(self, value):
        if self.is_blank(value): return RuleResult.blank
        fields = value.lower().split()
        if len(fields) not in (1, 2, 4):
            return RuleResult(False, "The menu window needs to be 'fullscreen' or 1 or 2 pairs of space-separated coordinates.")
        if len(fields) == 1:
            if fields[0] != 'fullscreen':
                return RuleResult(False, "The menu window needs to be 'fullscreen' or 1 or 2 pairs of space-separated coordinates.")
        elif len(fields) == 2:
            if not self.is_x_y(value):
                return RuleResult(False, "The x y coordinates need to be integers.")
        else:  # len(fields) == 4
            return self.rule_is_rectangle(value)
        return RuleResult.true

    def rule_is_icon_mode(self, icon_mode, text_mode):
        icon_mode = icon_mode.lower()
        text_mode = text_mode.lower()
        if icon_mode == 'none' and text_mode == 'none':
            return RuleResult(False, "icon mode and text mode cannot both be 'none'.")
        if icon_mode == 'none' and text_mode == 'overlay':
            return RuleResult(False, "icon mode cannot be 'none' with 'overlay' text mode.")
        return RuleResult.true

    def rule_is_text_mode(self, text_mode, icon_mode):
        return self.rule_is_icon_mode(icon_mode, text_mode)

    def rule_is_showref(self, value, showtype):
        if self.is_blank(value):
            return RuleResult(False, "The show label cannot be blank.")
        if ' ' in value:
            return RuleResult(False, "The show label cannot contain spaces.")
        if showtype == 'start' and value != 'start':
            return RuleResult(False, "The label for the start show must be 'start'.")
        return RuleResult.true
    
    def rule_is_show_type(self, value):
        if value in list(PPdefinitions.show_types.keys()):
            return RuleResult.true
        return RuleResult(False, "'{0}' is not a valid show type.".format(value))

    def rule_is_track_type(self, value):
        if value in list(PPdefinitions.track_types.keys()):
            return RuleResult.true
        return RuleResult(False, "'{0}' is not a valid track type.".format(value))

    def rule_is_script(self, value, scripttype, labels=None):
        # Handles overall processing for multi-line scripts of the following types:
        #   control                    ... no labels
        #   animation, browser,        ... no labels
        #   hyperlink, radiobutton     ... track labels
        #   showcontrol                ... show labels
        if self.is_blank(value.strip()): return RuleResult.blank
        lines = value.split('\n')
        result = RuleResult()
        for line in lines:
            if len(lines) > 1:
                line_num = lines.index(line) + 1
            else:
                line_num = None  # don't print line numbers in messages
            if scripttype.startswith('animation'):
                line_result = self.rule_is_animation_command(line, line_num)
            elif scripttype.startswith('browser'):
                line_result = self.rule_is_browser_command(line, line_num)
            elif scripttype.startswith('control'):
                line_result = self.rule_is_control_command(line, line_num)
            elif scripttype.startswith('hyperlink'):
                line_result = self.rule_is_hyperlink_command(line, labels, line_num)
            elif scripttype.startswith('radiobutton'):
                line_result = self.rule_is_radiobutton_command(line, labels, line_num)
            elif scripttype.startswith('show'):  # showcontrol
                line_result = self.rule_is_showcontrol_command(line, labels, line_num)
            # Append any messages and make the result False if any line fails
            if line_result.message is not None:
                if result.message is None:
                    result.message = line_result.message
                else:
                    result.message += "\n" + line_result.message
            if line_result.passed is False:
                result.passed = False
        return result

    def rule_is_animation_script(self, value):
        return rule_is_script(value, 'animation', None)

    def rule_is_browser_script(self, value):
        return rule_is_script(value, 'browser', None)

    def rule_is_control_script(self, value):
        return rule_is_script(value, 'control', None)

    def rule_is_radiobutton_script(self, value, track_labels):
        return rule_is_script(value, 'radiobutton', track_labels, None)

    def rule_is_hyperlink_script(self, value, track_labels):
        return rule_is_script(value, 'hyoerlink', track_labels)

    def rule_is_showcontrol_script(self, value, show_labels):
        return rule_is_script(value, 'showcontrol', show_labels)

    def rule_is_animation_command(self, value, line_num=None):
        if line.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = line.split()
        if len(fields) != 4: 
            return RuleResult(False, "An animation command needs 4 parameters{0}.".format(line_num))
        delay = fields[0]
        # name  = fields[1] # checked at runtime
        out_type = fields[2]
        to_state = fields[3]
        if not self.rule_is_zero_or_positive_integer(delay):
            return RuleResult(False, "'{0}' needs to be zero or positive{1}.".format(delay, line_str))
        if out_type != 'state':
            return RuleResult(False, "'{0}' needs to be 'state'{1}.".format(out_type, line_str))
        if to_state not in ('on', 'off'):
            return RuleResult(False, "'{0}' needs to be 'on' or 'off'{1}.".format(to_state, line_str))
        return RuleResult.true

    def rule_is_browser_command(self, value, line_num=None):
        if line.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = line.split()
        command = fields[0]
        if len(fields) not in (1, 2):
            return RuleResult(False, "Browser commands have one parameter or none{0}.".format(line_str))
        if command == 'uzbl':  # may have zero or one param
            return RuleResult.true
        if command not in ('load', 'refresh', 'wait', 'exit', 'loop'):
            return RuleResult(False, "'{0}' is not a recognized browser command{1}.".format(command, line_str))
        if command == 'load' and len(fields) != 2:
            return RuleResult(False, "'load' needs a parameter for what to load{0}.".format(command, line_str))
        if command == 'wait':
            if len(fields) != 2:
                return RuleResult(False, "'{0}' needs a parameter{1}.".format(command, line_str))
            if self.is_zero_or_positive_integer(fields[1]):
                return RuleResult(False, "'{0}' needs to be zero or a positive integer{1}.".format(fields[1], line_str))
        return RuleResult.true

    def rule_is_control_command(self, value, line_num=None):
        if line.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = line.split()
        if len(fields) != 2:
            return RuleResult(False, "A control command needs the command and a parameter{1}".format(line_num))
        command = fields[0]
        op = fields[1]
        if (op in ('up', 'down', 'play', 'stop', 'exit', 'pause', 'no-command', 'null') or
            op.starts('mplay-') or op.startswith('omx-') or op.startswith('uzbl-')):
            return RuleResult.true
        return RuleResult(False, "'{0} is not a recognized command{1}.".format(op, line_str))

    def rule_is_radiobutton_command(self, value, track_labels, line_num=None):
        if line.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = line.split()
        if len(fields) not in (2, 3):
            return RuleResult(False, "The command needs one or two parameters{0}.".format(line_str))
        symbol = fields[0]
        op = fields[1]
        trackref = None
        if len(fields) == 3: trackref = fields[2]
        if (op in ('return', 'stop', 'exit', 'pause', 'no-command') or
            op.startswith('mplay-') or op.startswith('omx-') or op.startswith('uzbl-')):
            return RuleResult.true
        elif op == 'play':
            if len(fields) != 3:
                return RuleResult(False, "'play' needs to know the track label{0}.".format(line_str))
            if trackref not in track_labels:
                return RuleResult(False, "'{0}' was not found in the medialist{1}.".format(trackref, line_str))
            return RuleResult.true
        else:
            return RuleResult(False, "'{0}' is not a recognized command{1}.".format(op, line_str))
        return RuleResult.true

    def rule_is_hyperlink_command(self, value, track_labels, line_num=None):
        if line.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = line.split()
        if len(fields) not in (2, 3):
            return RuleResult(False, "The command needs one or two parameters{0}.".format(line_str))
        symbol = fields[0]
        op = fields[1]
        trackref = None
        if len(fields) == 3: trackref = fields[2]
        if (op in ('home', 'null', 'stop', 'exit', 'repeat', 'pause', 'no-command') or
            op.startswith('mplay-') or op.startswith('omx-') or op.startswith('uzbl-')):
                return RuleResult.true
        if op in ('call', 'goto', 'jump'):
            if trackref is None:
                return RuleResult(False, "'{0}' needs to know the track label{1}.".format(op, line_str))
            if trackref not in track_labels:
                return RuleResult(False, "'{0}' was not found in the medialist{1}.".format(trackref, line_str))
            return RuleResult.true
        elif op in ('return', ):
            if trackref is None:
                return RuleResult.true
            if trackref not in track_labels:
                return RuleResult(False, "'{0}' was not found in the medialist{1}.".format(trackref, line_str))
        else:
            return RuleResult(False, "'{0}' is not a recognized command{1}.".format(op, line_str))
        return RuleResult.true

    def rule_is_showcontrol_command(self, value, show_labels, line_num):
        if line.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = line.split()
        command = fields[0]
        showref = None
        if len(fields) >= 2: showref = fields[1]
        if command.startswith('/'):  # osc command... followed by any number of params?
            return RuleResult.true
        elif len(fields) == 1 and command not in ('exitpipresents', 'shutdownnow'):
            return RuleResult(False, "'{0}' is not a recognized command or is missing paramters{1}.".format(command, line_str))
        elif len(fields == 2):
            if command not in ('open', 'close'):
                return RuleResult(False, "'{0}' is not a recognized command or has incorrect paramters{1}.".format(command, line_str))
            if showref not in show_labels:
                return RuleResult(False, "'{0}' was not found in the show list{1}.".format(showref, line_str))
        return RuleResult.true

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
# options
# ************************************

    def rule_is_in_list(self, value, values):
        #?  if self.is_blank(value): return RuleResult.true
        #if spec['shape'] != 'option-menu' or \
        #    not 'values' in spec or \
        #    value in spec['values']:
        #        return RuleResult.true
        #self.add_invalid_value_error(objtype, spec['text'], value)
        if value in values:
            return RuleResult.true
        return RuleResult(False, "'{0}' is not one of the available choices.".format(value))

    def rule_is_one_of_spec_options(self, objtype, value, spec):
        # convenience method that isn't really a rule
        if self.is_blank(value): return
        if spec['shape'] != 'option-menu' or \
            not 'values' in spec or \
            value in spec['values']:
                return True
        self.add_invalid_value_error(objtype, spec['text'], value)

    def check_show_options(self, show):
        for field in PPdefinitions.show_types[show['type']]:
            spec = PPdefinitions.show_field_specs[field]
            if spec['shape'] != 'option-menu':
               continue
            if not 'values' in spec:
                continue
            self.rule_is_one_of_spec_options(SHOW, value=show[field], spec=spec)


    def check_track_options(self, show, list, track):
        for field in PPdefinitions.track_types[track['type']]:
            spec = PPdefinitions.track_field_specs[field]
            if spec['shape'] != 'option-menu':
                continue
            if not 'values' in spec:
                continue
            self.rule_is_one_of_spec_options(TRACK, value=track[field], spec=spec)

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

    def __init__(self, title, display_it=False):
        self.title = title
        self.display_it=display_it
        self.errors=0
        self.warnings=0
        if self.display_it:
            self.show_window()

    def show_window(self):
        top = Toplevel()
        top.title(self.title)

        notebook = ttk.Notebook(top)
        grid_tab = ttkFrame(notebook)
        text_tab = ttkFrame(notebook)
        notebook.add(grid_tab, text="Grid")
        notebook.add(text_tab, text="Text")
        notebook.pack(side=LEFT, fill=BOTH, expand=True)

        grid = ttkListbox(grid_tab) #, columns=('Message'))
        #grid.column('#0', width=0, stretch=False)
        #grid.column('Message',  width=50)
        #grid.heading('Message', text='Message')
        grid.tag_configure('critical', foreground='white', background='red')
        grid.tag_configure('error',    foreground='red')
        grid.pack(side=LEFT, fill=BOTH, expand=True)
        self.grid = grid

        scrollbar = Scrollbar(text_tab, orient=VERTICAL)
        self.textb = Text(text_tab,width=80,height=40, wrap='word', font="arial 11",padx=5,yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.textb.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.textb.pack(side=LEFT, fill=BOTH, expand=1)
        self.textb.config(state=NORMAL)
        self.textb.delete(1.0, END)
        self.textb.config(state=DISABLED)

        top.bind("<Escape>", self.escape_keypressed)
        self.top = top
        top.update()

    def add_profile(self, title):
        if not self.display_it: return
        text = 'PROFILE: ' + title
        id   = '.'
        if self.grid.exists(id): return
        self.grid.insert(END, text, iid=id, tags=('profile',))

    def add_show(self, show):
        if not self.display_it: return
        if not show:
            show = '..'
        if isinstance(show, basestring):
            if show == '.':   # profile item, don't do anything
                return
            if show == '..':  # orphaned items
                text = '(orphaned medialists)'
                id = ".."
                if self.grid.exists(id): 
                    return
                # insert below profile
                self.grid.insert(1, text, iid=id, tags=('show',))
        else:
            showref = show['show-ref']
            text = 'SHOW: ' + show['title']
            id   = ".{0}".format(showref)
            if self.grid.exists(id): 
                return
            self.grid.insert(END, text, iid=id, tags=('show',))

    def add_list(self, showref, list):
        if not self.display_it: return
        if not showref: 
            self.add_show(None);
            parent = ".."
        elif showref == ".":
            parent = "."
        elif showref == "..":
            self.add_show("..");
            parent = ".."
        else:
            parent = ".{0}".format(showref)
        id     = ".{0}.{1}".format(showref, list)
        text   = 'LIST: ' + list
        if self.grid.exists(id): return
        self.grid.insert(END, text, iid=id, tags=('list',), parent=parent)

    def add_track(self, showref, listref, track):
        if not self.display_it: return
        trackref = get_trackref(track)
        text   = 'TRACK: ' + get_track_title(track)
        parent = ".{0}.{1}".format(showref, listref)
        id     = ".{0}.{1}.{2}".format(showref, listref, trackref)
        if self.grid.exists(id): return
        self.grid.insert(END, text, iid=id, tags=('track',), parent=parent)

    def get_parentid(self, result):
        if result.is_profile(): return '.'
        if result.is_show()   : return "."+result.showref
        if result.is_list()   : return ".{0}.{1}".format(result.showref, result.listref)
        if result.is_track()  : return ".{0}.{1}.{2}".format(result.showref, result.listref, result.trackref)

    def add_result(self, result):
        if not self.display_it: return
        # add result item
        sev = ValidationSeverity.names[result.severity]
        msg = "{0}: {1}".format(sev, result.text)
        parentid = self.get_parentid(result)
        # insert before the list item, if there is one
        children = self.grid.get_children(parentid)
        index = -1
        for childid in children:
            child = self.grid.item(childid, option='text')
            if 'LIST' in child:
                index = children.index(childid)
        if index == -1:
            index = END
        iid = self.grid.insert(index, msg, parent=parentid, open=True,
            tags=(sev.lower(),)
            #values=()
            )
        # bubble up the error tag to all parents and open them
        grid = self.grid
        while parentid != '':
            if result.severity == CRITICAL:
                grid.add_tag(parentid, 'critical')
                grid.remove_tag(parentid, 'error')
            elif result.severity == ERROR:
                if not grid.has_tag(parentid, 'critical'):
                    grid.add_tag   (parentid, 'error')
                    grid.remove_tag(parentid, 'warning')
            elif result.severity == WARNING:
                if not (grid.has_tag(parentid, 'critical') or grid.has_tag(parentid, 'error')):
                    grid.add_tag (parentid, 'warning')
            grid.remove_tag(parentid, 'info')
            grid.item(parentid, open=True)
            parentid = self.grid.parent(parentid)

    def escape_keypressed(self, event=None):
        self.top.destroy()

    def display(self,priority,text):
        if priority == 'c': self.errors += 1
        if priority == 'f': self.errors += 1
        if priority == 'w': self.warnings += 1       
        if self.display_it is False: return
        self.textb.config(state=NORMAL)
        if priority == 't': 
            self.textb.insert(END, text+"\n")  # informational
        if priority == 'c':
            self.textb.insert(END, "    ** Critical: "+text+"\n")
        if priority == 'f':
            self.textb.insert(END, "    ** Error:    "+text+"\n")
        if priority == 'w':
            self.textb.insert(END, "    ** Warning:  "+text+"\n")           
        self.textb.config(state=DISABLED)

    def stats(self):
        if self.display_it is False: return
        self.textb.config(state=NORMAL)
        # show the summary at the top so user doesn't have to scroll all the way down to see
        # whether there were errors
        self.textb.insert(1.0, "\nErrors: "+str(self.errors)+"\nWarnings: "+str(self.warnings)+"\n\n")
        self.textb.config(state=DISABLED)

    def num_errors(self):
        return self.errors
