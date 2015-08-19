import os
import json
import ConfigParser
import re
import PIL.Image
import urlparse
from Tkinter import Toplevel
from Tkinter import VERTICAL,RIGHT,LEFT,BOTH,Y,NORMAL,END,DISABLED
from ttkStatusBar import StatusBar
import ttk
import tkFont
from tkconversions import *
import pp_paths
from pp_utils import enum
import pp_definitions
from pp_definitions import PPdefinitions, PROFILE, SHOW, LIST, TRACK, FIELD
from pp_definitions import ValidationSeverity, CRITICAL, ERROR, WARNING, INFO

# shorter ways to call these

SAME = ''  # for setting a current item without changing other current items

ValidationRuleTypes = enum('INVALID_VALUE', 'MISSING_FILE')


class RuleResult(object):
    true = None
    blank = None

    def __init__(self, passed=None, message=None, blank=None, severity=None):
        self.passed   = passed
        self.message  = message
        self.blank    = blank  # hmm, not to be confused with RuleResult.blank
        self.severity = severity
        if RuleResult.__dict__.get('true') == None:
            setattr(RuleResult, 'true', '')     # prevent recursion
            setattr(RuleResult, 'blank', '')
            RuleResult.true = RuleResult(True)  # set the actual item
            RuleResult.blank = RuleResult(True, blank=True)


class ValidationResult(object):

    def __init__(self, validator, objtype, severity, msg, **kwargs):
        dummy = RuleResult(True).passed  # force instantiation of RuleResult.true by creating an instance

        self.objtype   = objtype                     # PROFILE, SHOW, LIST, TRACK
        self.severity  = severity                    # CRITICAL, ERROR, WARNING, (INFO?), (OK?)
        self.message   = msg
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
        if self.track: self.trackref = Validator.get_trackref(self.track)

        if self.objtype == PROFILE:
            pass
        if self.objtype == TRACK:
            self.id = ".{0}.{1}.{2}".format(self.showref, self.listref, self.trackref)
        elif self.objtype == LIST:
            self.id = ".{0}.{1}".format(self.showref, self.listref)
        elif self.show:
            self.id = ".{0}".format(self.showref)
        #else:
        #    print "Something wrong... show:{0}, list:{1}, track{2}" \
        #        .format(self.showref, self.listref, self.trackref)
        #print "id: " + self.id

    def __cmp__(self, other):
        if self.severity  == other.severity: return 0
        if self.severity  == NONE: return -1
        if other.severity == NONE: return  1
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

    # Static methods

    @staticmethod
    def get_showref(show):
        if show:
            return show['show-ref']
        else:
            return ''

    @staticmethod
    def get_trackref(track):
        trackref = track['track-ref']
        if not trackref: trackref = track['title']
        if not trackref: trackref = track['location']
        return trackref

    @staticmethod
    def get_track_title(track):
        title = track['title']
        if not title: title = track['track-ref']
        if not title: title = track['location']
        return title

    def __init__(self):
        dummy = RuleResult(True).passed  # force instantiation of RuleResult.true by creating an instance
        self.pp_home = pp_paths.pp_home
        self.pp_profile = pp_paths.pp_profile_dir

        self.scope = None
        self.result = None          # indicates whether the validator has been initialized
        self.results = []           # list of ValidationResult, povides referenceable results
        self.v_medialist_refs = []  # list of medialist file references (used for ?)
        self.v_show_labels = []     # (same order as in editor) used for checking uniqueness
        self.v_start_shows = []     # used for checking number of start shows
        self.anonymous = 0          # provides a pseudo-trackref for tracks that don't have one

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
        showlist = json.load(ifile)
        ifile.close()
        self.v_shows = showlist['shows']
        #if not self.check_profile_compatibility(showlist):
        #    return False

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

    def validate_show(self, objtype, show):
        self.scope = SHOW
        if self.result is None:
            raise ValueException("The validator needs to be initialized before calling this method.")
        self.check_show(show)

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
            list = json.load(ifile)
            tracks = list['tracks']
            ifile.close()

            # make a list of the track labels
            v_track_labels=[]
            for track in tracks:
                self.set_current(list=list, track=track)
                self.result.add_track(show['show-ref'], show['medialist'], track)
                if track['track-ref'] !='':
                    v_track_labels.append(track['track-ref'])
                       
        # check each field for the show, as defined by the show field specs
        specs = PPdefinitions.show_field_specs
        scheme = PPdefinitions.show_field_rules
        for field in show: #PPdefinitions.show_types[show['type']]:
            self.set_current(show=show, track=None)
            #try:
            self.process_ruleset(SHOW, show, field)
            #except Exception as e:
            #    print "An exception occurred on {0} {1}, field {2}: {3}".format('show', show['show-ref'], field, e)

        return True

    def check_medialist(self, medialist_file):
        # we don't do anything with these (yet)
        if medialist_file in ('pp_io_config.json'):
            return
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
            myversion = pp_definitions.__version__
            if medialist_issue  !=  myversion:
                return self.add_critical(LIST, "Medialist version {0} does not match this editor (version {1})" \
                    .format(medialist_issue, myversion), abort=False)

            # open a medialist and test its tracks
            self.v_track_labels=[]
            self.anonymous=0
            for track in tracks:
                self.check_track(track, self.anonymous)

    def check_track(self, track, anonymous):
        self.set_current(track=track, checking=TRACK)
        showref = self.get_showref(self.current_show)
        listref = self.current_list
        self.result.add_track(showref, listref, track)
        if track['track-ref'] == '':
            self.anonymous+=1        
        trackref = self.get_trackref(track)
        tracktitle = self.get_track_title(track)

        # check each field for the track, as defined by the field specs
        for field in track:
            #try:
                self.process_ruleset(TRACK, track, field)
            #except Exception as e:
            #    print "An exception occurred on {0} {1}, field {2}: {3}".format('track', self.get_trackref(track), field, e)
        return True

    def get_results(self):
        return self.result.criticals, self.result.errors, self.result.warnings

# ValidationResult handling methods: do the actual adding to both the result list and the result text

    def add_result(self, objtype, severity, msg, **kwargs):
        if severity == CRITICAL: return self.add_critical(objtype, msg, **kwargs)
        if severity == ERROR   : return self.add_error   (objtype, msg, **kwargs)
        if severity == WARNING : return self.add_warning (objtype, msg, **kwargs)
        #if severity == INFO    : return self.add_info    (objtype, msg, **kwargs)

    def add_critical(self, objtype, msg, **kwargs):
        abort = kwargs.pop('abort', True)
        result = ValidationResult(self, objtype, CRITICAL, msg, **kwargs)
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
        result = ValidationResult(self, objtype, ERROR, msg, **kwargs)
        self.results.append(result)
        if msg == '': raise ValueError("The error message was empty.")
        self.result.display('f', msg)
        self.result.add_result(result)

    def add_warning(self, objtype, msg, **kwargs):
        # possible kwargs: show, medialist, track, text
        result = ValidationResult(self, objtype, WARNING, msg, **kwargs)
        self.results.append(result)
        if msg == '': raise ValueError("The warning message was empty.")
        self.result.display('w', msg)
        self.result.add_result(result)

# 'check' methods: add ValidationResults as needed

    def check_file_exists(self, objtype, severity, path, format='', **kwargs):
        arg = kwargs.pop('arg', 'path')
        if not format: format = "File not found: '{" + arg + "}'"
        return self.check_path_exists(objtype, severity, path, format, **kwargs)

    def check_dir_exists(self, objtype, severity, path, format='', **kwargs):
        arg = kwargs.pop('arg', 'path')
        if not format: format = "Directory not found: '{" + arg + "}'"
        return self.check_path_exists(objtype, severity, path, format, **kwargs)

    def check_path_exists(self, objtype, severity, path, format='', **kwargs):
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

    def check_profile_compatibility(self, showlist):
        myversion = pp_definitions.__version__
        if 'issue' in showlist:
            profile_issue = showlist['issue']
        else:
            profile_issue ="1.0"
        if profile_issue == myversion:
            return True
        matches = 0
        extra = 0
        missing = 0
        for show in showlist['shows']:
            self.set_current(show, checking=SHOW)
            schema = PPdefinitions.new_shows
            if show['type'] in PPdefinitions.new_shows:
                schema = PPdefinitions.new_shows[show['type']]
                for field in schema:
                    if field in show:
                        matches += 1
                    else:
                        self.add_critical(SHOW, "Schema is missing field '{0}'.".format(field))
                for field in show:
                    if field not in schema:
                        extra += 1
                        self.add_error(SHOW, "Schema has extra field '{0}'.".format(field))
        if missing > 0:
            self.add_critical(PROFILE, "Profile version {0} is not compatible with this version of PiPresents ({1})" 
                .format(profile_issue, myversion), abort=True)
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
        text = show['start-show']
        show_count = 0
        fields = text.split()
        for field in fields:
            show_count += 1
            if field not in labels:
                self.add_error(SHOW, "The start show calls '{0}', which was not found in the show labels.".format(field))
                passed = False
        if show_count == 0:
            self.add_warning(SHOW, "The start show doesn't call any shows.")
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
        # Retaining the current show, list, and track allow ValidationResults to remember
        # the hierarchicalitem they apply to.
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

# Rule processing and helpers

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
        if self.is_blank(value):
            if spec['must'] != 'no':
                self.add_error(objtype, "A value is required for {0}".format(field), **kwargs)
                return RuleResult.true
            if is_dependency:
                if not self.is_blank(obj[dependent_field]):
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
                severity = ERROR
                if isinstance(rulespec, str):
                    rule = rulespec
                elif isinstance(rulespec, dict):
                    if 'rule'            in rulespec: rule = rulespec['rule']
                    if 'args'            in rulespec: args = rulespec['args']
                    if 'required-fields' in rulespec: reqs = rulespec['required-fields']
                    if 'depends-on'      in rulespec: deps = rulespec['depends-on']
                    if 'field-arg'       in rulespec: farg = rulespec['field-arg']
                    if 'severity'        in rulespec: severity = rulespec['severity']
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
                try:
                    rule_func = getattr(self, rule_name)
                except:
                    rule_func = None
                #print "Checking: {0}({1})".format(rule_name, value)
                if field == 'start-show':
                    print "Checking '{0}': '{1}' with rule {2}".format(field, obj[field], self.current_show)
                if rule_func is None or not hasattr(rule_func, '__call__'):
                    msg = "The processor function for rule '{0}', field '{1}' is not present.".format(rule, field)
                    self.add_critical(objtype, msg)
                    return RuleResult(False, msg, severity=CRITICAL)

                try:
                    if args and farg:
                        rule_result = rule_func(value, args, obj[farg])
                    elif args:
                        rule_result = rule_func(value, args)
                    elif farg:
                        rule_result = rule_func(value, obj[farg])
                    else:
                        rule_result = rule_func(value)
                except Exception as e:
                    msg = "Failed to check validation for '{0}' ({1}): {2}".format(field, rule_func, e)
                    return RuleResult(False, msg, severity=CRITICAL)

                if not isinstance(rule_result, RuleResult):
                    msg = "The processor function '{0}' returned an invalid result.".format(rule_name)
                    self.add_critical(objtype, msg)
                    return RuleResult(False, msg, severity=CRITICAL)

                if is_dependency and rule_result.blank is True:
                    # the rule validated, but it's blank and it's required for a dependent rule
                    msg = "{0} is blank, but is required for {1}".format(field, dependent_field)
                    rule_result.passed = False

                if rule_result.passed is False:
                    rule_result.severity = severity
                    if rule_result.message:
                        # the rule method doesn't know the field name, so we add it here
                        msg = "{0}: {1}".format(spec['text'], rule_result.message)
                        self.add_result(SHOW, severity, msg)
                    else:
                        msg = "{0}: {1} is an invalid value".format(spec['text'], value)
                        self.add_result(SHOW, severity, msg)
                        #self.add_error(SHOW, msg)
                elif rule_result.passed is True:
                    if reqs and rule_result.blank is not True:
                        for req in reqs:
                            #print "Checking dependencies for rule (2) ", field
                            self.process_ruleset(objtype, obj, req, dependent_field=field)
        if rule_result is not None and rule_result.passed is False:
            print "[{0}] {1}: {2}".format(severity, field, rule_result.message)
            pass
        return rule_result

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

    def is_blank(self, value):
        # rules should validate if the value is blank, except for the rule that requires a non-blank value.
        # If an item is required to be non-blank, it should include the is-not-blank rule 
        # (which would fail for blank values) in addition to any other rule(s) needed to 
        # validate non-blank values (which would pass for blank values)
        return value is None or value == ''

    def is_integer(self, value):
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

# Rules: return a RuleResult object

    def rule_is_not_blank(self, value):
        if not self.is_blank(value):
            return RuleResult.true
        return RuleResult(False, "Cannot be blank.")

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

    def rule_is_location(self, value, track_type):
        if self.is_blank(value): return RuleResult.blank
        if track_type == 'web':
            return self.rule_is_web_location(value)
        result = self.rule_file_exists(value)
        #if result.passed is False:
        #    print "Home: ", pp_paths.pp_home
        return result

    def rule_is_web_location(self, value):
        if self.is_blank(value): return RuleResult.blank
        # a valid url is almost anything
        return RuleResult.true
        # you could try the following, but the example shows that use web addresses
        # ('pipresents.wordpress.com') fail this validation.
        #loc = os.path.basename(track['location'])
        #url = urlparse.urlparse(value)
        #if url.scheme != '' and url.netloc != '':
        #    return RuleResult.true
        #return RuleResult(False, "'{0}' does not appear to be a valid web location. scheme: {1}, loc: {2}.".
        #    format(value, url.scheme, url.netloc))

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

    def rule_is_in_list(self, value, values):
        # ?  if self.is_blank(value): return RuleResult.blank
        if value in values:
            return RuleResult.true
        return RuleResult(False, "'{0}' is not one of the available choices.".format(value))

    def rule_is_all_in_list(self, value, values):
        # check if all values in the value are in the list
        missing = []
        for val in value:
            if val not in values:
                missing.append(val)
        count = len(missing)
        if count > 0:
            if count == 1:
                msg = "{0} is not in the list.".format(missing[0])
            elif count <= 3:
                msg = "{0} are not in the list.".format(missing)
            else:
                msg = "{0} items are not in the list.".format(count)
            result = RuleResult(False, msg)
            result.arg = missing
            return result
        return RuleResult.true

    def rule_is_startshow(self, value, show_labels):
        if self.is_blank(value): return RuleResult(False, "The start show does not call any shows.", severity=WARNING)
        shows = value.split()
        missing = []
        for show in shows:
            if show not in show_labels:
                missing.append(val)
        count = len(missing)
        if count > 0:
            if count == 1:
                msg = "{0} is not in the show list.".format(missing[0])
            elif count <= 3:
                msg = "{0} are not in the show list.".format(missing)
            else:
                msg = "{0} items are not in the show list.".format(count)
            result = RuleResult(False, msg)
            result.arg = missing
            return result
        return RuleResult.true

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
        tx = int(tx)
        ty = int(ty)
        bx = int(bx)
        by = int(by)
        if not tx < bx:
            return RuleResult(False, "The left x coordinate ({0}) needs to be a lower value than the right x coordinate ({1}."
                .format(tx, bx))
        if not ty < by:
            return RuleResult(False, "The top y coordinate ({0}) needs to be a lower value than the bottom y coordinate ({1})."
                .format(ty, by))
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

    def rule_is_hh_mm_ss_or_seconds(self, value):
        result = self.rule_is_zero_or_positive_integer(value)
        if result.passed is True or result.blank is True:
            return result
        return self.rule_is_hh_mm_ss(value)

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
            file = pp_paths.get_file(value)
            if file is None:
                return RuleResult(False, "'{0}' does not exist.".format(value))
            img = PIL.Image.open(file)
            return RuleResult.true
        except Exception as ex:
            return RuleResult(False, "The image file check failed for '{0}': {1}".format(value, ex))
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
            family = re.sub(r"\{(.*)\}.*", r"\1", family)  # using the font picker adds the brackets
            family = re.sub(r"\s\d+\s.*", "", family)      # brackets are not required
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
                        if style not in ("bold", "normal", "italic", "roman", "underline", "overstrike"):
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

    def rule_is_script(self, value, labels=None, scripttype=None):
        # labels is first to meet calling order in process_rule()
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
            elif scripttype in ('video', 'message', 'show', 'image', 'audio', 'web', 'menu'):
                # this is a track... we don't have a good way of knowing what type of show it is
                # (hyperlink or radiobutton) so we'll use the generic processor function
                line_result = rule_is_link_command(line, labels, line_num)
            else:
                return RuleResult(False, "Unknown sript type '{0}'.".format(scripttype), severity=CRITICAL)
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
        return self.rule_is_script(value, None, 'animation')

    def rule_is_browser_script(self, value):
        return self.rule_is_script(value, None, 'browser')

    def rule_is_control_script(self, value):
        return self.rule_is_script(value, None, 'control')

    def rule_is_radiobutton_script(self, value, track_labels):
        return self.rule_is_script(value, track_labels, 'radiobutton')

    def rule_is_hyperlink_script(self, value, track_labels):
        return self.rule_is_script(value, track_labels, 'hyperlink')

    def rule_is_showcontrol_script(self, value, show_labels):
        return self.rule_is_script(value, show_labels, 'showcontrol')

    def rule_is_trigger_script(self, value):
        return self.rule_is_script(value, None, 'trigger')

    def rule_is_animation_command(self, value, line_num=None):
        if value.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = value.split()
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
        if value.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = value.split()
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
            if not self.is_zero_or_positive_integer(fields[1]):
                return RuleResult(False, "'{0}' needs to be zero or a positive integer{1}.".format(fields[1], line_str))
        return RuleResult.true

    def rule_is_control_command(self, value, line_num=None):
        if value.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = value.split()
        if len(fields) != 2:
            return RuleResult(False, "A control command needs the command and a parameter{1}".format(line_num))
        # command = fields[0]
        op = fields[1]
        if (op in ('up', 'down', 'play', 'stop', 'exit', 'pause', 'no-command', 'null') or
                op.startswith('mplay-') or op.startswith('omx-') or op.startswith('uzbl-')):
            return RuleResult.true
        return RuleResult(False, "'{0} is not a recognized command{1}.".format(op, line_str))

    def rule_is_radiobutton_command(self, value, track_labels, line_num=None):
        if value.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = value.split()
        if len(fields) not in (2, 3):
            return RuleResult(False, "The command needs one or two parameters{0}.".format(line_str))
        # symbol = fields[0]
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

    def rule_is_link_command(self, value, track_labels, line_num=None):
        # a generic rule that checks both radiobutton and hyperlink commands
        if value.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = value.split()
        if len(fields) not in (2, 3):
            return RuleResult(False, "The command needs one or two parameters{0}.".format(line_str))
        # symbol = fields[0]
        op = fields[1]
        trackref = None
        if len(fields) == 3: trackref = fields[2]
        # check radiobutton commands
        if (op in ('return') or                                 # radiobutton-only commands
            op in ('home', 'null', 'repeat') or                 # hyperlink-only commands
            op in ('stop', 'exit', 'pause', 'no-command') or    # common to both
                op.startswith('mplay-') or op.startswith('omx-') or op.startswith('uzbl-')):
            return RuleResult.true
        # 'play' is a radiobutton command, the others are hyperlink commands
        elif op == 'play' or op in ('call', 'goto', 'jump'):
            if len(fields) != 3:
                return RuleResult(False, "'play' needs to know the track label{0}.".format(line_str))
            if trackref not in track_labels:
                return RuleResult(False, "'{0}' was not found in the medialist{1}.".format(trackref, line_str))
            return RuleResult.true
        # 'return' is a hyperlink command
        elif op in ('return', ):
            if trackref is None:
                return RuleResult.true
            if trackref not in track_labels:
                return RuleResult(False, "'{0}' was not found in the medialist{1}.".format(trackref, line_str))
        else:
            return RuleResult(False, "'{0}' is not a recognized command{1}.".format(op, line_str))
        return RuleResult.true

    def rule_is_hyperlink_command(self, value, track_labels, line_num=None):
        if value.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = value.split()
        if len(fields) not in (2, 3):
            return RuleResult(False, "The command needs one or two parameters{0}.".format(line_str))
        # symbol = fields[0]
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
        # value is the line
        if value.strip() == '': return RuleResult.blank
        if line_num is None:
            line_str = ""
        else:
            line_str = " (line {0})".format(line_num)
        fields = value.split()
        command = fields[0]
        showref = None
        if len(fields) >= 2: showref = fields[1]
        if command.startswith('/'):  # osc command... followed by any number of params?
            return RuleResult.true
        elif len(fields) == 1 and command not in ('exitpipresents', 'shutdownnow'):
            return RuleResult(False, "'{0}' is not a recognized command or is missing parameters{1}.".format(command, line_str))
        elif len(fields) == 2:
            if command not in ('open', 'close'):
                return RuleResult(False, "'{0}' is not a recognized command or has incorrect parameters{1}.".format(command, line_str))
            if showref not in show_labels:
                return RuleResult(False, "'{0}' was not found in the show list{1}.".format(showref, line_str))
        return RuleResult.true

    def rule_is_trigger_param(self, value, triggertype):
        # For mediashow and liveshow
        # Possible trigger types
        # start trigger:  start,    input, input-persist
        #   end trigger:  none,     input, duration
        #  next trigger:  continue, input
        if self.is_blank(): return RuleResult.blank
        fields = value.split()
        if len(fields) != 1:
            return RuleResult(False, "The trigger parameter can be one word, a number, or hh:mm:ss, mm:ss, or ss.")
        return RuleResult.true

    def rule_is_schema_valid(self, this, that):
        # checks the fields in the first level of the schema
        # counts fields that match, are extraneous, or are missing
        matches = {}
        extra   = {}
        missing = {}
        for field in this:
            if field in that:
                match.append(field)
            else:
                missing.append(field)
        for field in that:
            if field not in this:
                extra.append(field)
        if len(extra) > 0 or len(missing) > 0:
            msg = "{0} fields matched, {1} missing, {2} extraneous".format(
                len(matches), len(missing), len(extra))
            result = RuleResult(False, msg)
            result.matches = matches
            result.extra   = extra
            result.missing = missing
            return result
        else:
            result.matches = matches
            result.extra   = extra
            result.missing = missing
            return RuleResults(True)

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
# RESULT WINDOW CLASS
# ************************************

class ResultWindow(object):

    def __init__(self, title, display_it=False):
        self.title = title
        self.display_it = display_it
        self.criticals = 0
        self.errors    = 0
        self.warnings  = 0
        if self.display_it:
            self.show_window()

    def show_window(self):
        top = Toplevel()
        top.title(self.title)

        notebook = ttk.Notebook(top)
        tree_tab = ttkFrame(notebook)
        text_tab = ttkFrame(notebook)
        notebook.add(tree_tab, text="Tree")
        notebook.add(text_tab, text="Text")
        notebook.pack(side=TOP, fill=BOTH, expand=True, anchor=S)

        tree = ttkTreeview(tree_tab) #, columns=('Message'))
        #tree.column('#0', width=0, stretch=False)
        #tree.column('Message',  width=50)
        #tree.heading('Message', text='Message')
        tree.tag_configure('critical', foreground='white', background='red')
        tree.tag_configure('error',    foreground='red')
        tree.tag_configure('warning',  foreground='dark orange')
        tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.tree = tree

        #scrollbar = Scrollbar(text_tab, orient=VERTICAL)
        #self.textb = Text(text_tab,width=80,height=40, wrap='word', font="arial 11",padx=5,yscrollcommand=scrollbar.set)
        #scrollbar.config(command=self.textb.yview)
        #scrollbar.pack(side=RIGHT, fill=Y)
        self.textb = ttkScrolledText(text_tab, wrap='word')
        self.textb.pack(side=LEFT, fill=BOTH, expand=1)
        self.textb.config(state=NORMAL)
        self.textb.delete(1.0, END)
        self.textb.config(state=DISABLED)

        # define status bar
        self.status = StatusBar(top)
        self.status.set("")
        self.status.pack(side=BOTTOM, fill=X, expand=False, anchor=S)

        top.bind("<Escape>", self.escape_keypressed)
        notebook.enable_traversal()  # keybinding for tab switching
        self.top = top

    def add_profile(self, title):
        if not self.display_it: return
        text = 'PROFILE: ' + title
        id   = '.'
        if self.tree.exists(id): return
        self.tree.insert(END, text, iid=id, tags=('profile',))

    def add_show(self, show):
        if not self.display_it: return
        if not show:
            show = '..'
        if isinstance(show, basestring):
            if show == '.':   # profile item, don't do anything
                return
            if show == '..':  # orphaned items
                text = '(orphaned medialists or other lists)'
                id = ".."
                if self.tree.exists(id): 
                    return
                # insert below profile
                self.tree.insert(1, text, iid=id, tags=('show',))
        else:
            showref = show['show-ref']
            text = 'SHOW: ' + show['title']
            id   = ".{0}".format(showref)
            if self.tree.exists(id): 
                return
            self.tree.insert(END, text, iid=id, tags=('show',))

    def add_list(self, showref, list):
        if not self.display_it: return
        if not showref: 
            self.add_show(None)
            parent = ".."
        elif showref == ".":
            parent = "."
        elif showref == "..":
            self.add_show("..")
            parent = ".."
        else:
            parent = ".{0}".format(showref)
        id     = ".{0}.{1}".format(showref, list)
        text   = 'LIST: ' + list
        if self.tree.exists(id): return
        self.tree.insert(END, text, iid=id, tags=('list',), parent=parent)

    def add_track(self, showref, listref, track):
        if not self.display_it: return
        trackref = Validator.get_trackref(track)
        text   = 'TRACK: ' + Validator.get_track_title(track)
        parent = ".{0}.{1}".format(showref, listref)
        id     = ".{0}.{1}.{2}".format(showref, listref, trackref)
        if self.tree.exists(id): return
        self.tree.insert(END, text, iid=id, tags=('track',), parent=parent)

    def get_parentid(self, result):
        if result.is_profile(): return '.'
        if result.is_show()   : return "."+result.showref
        if result.is_list()   : return ".{0}.{1}".format(result.showref, result.listref)
        if result.is_track()  : return ".{0}.{1}.{2}".format(result.showref, result.listref, result.trackref)

    def add_result(self, result):
        if not self.display_it: return
        # add result item
        sev = ValidationSeverity.names[result.severity]
        msg = "{0}: {1}".format(sev, result.message)
        parentid = self.get_parentid(result)
        # insert before the list item, if there is one
        children = self.tree.get_children(parentid)
        index = -1
        for childid in children:
            child = self.tree.item(childid, option='text')
            if 'LIST' in child:
                index = children.index(childid)
        if index == -1:
            index = END
        iid = self.tree.insert(index, msg, parent=parentid, open=True,
            tags=(sev.lower(),)
            #values=()
            )
        # bubble up the error tag to all parents and open them
        tree = self.tree
        while parentid != '':
            if result.severity == CRITICAL:
                tree.add_tag(parentid, 'critical')
                tree.remove_tag(parentid, 'error')
            elif result.severity == ERROR:
                if not tree.has_tag(parentid, 'critical'):
                    tree.add_tag   (parentid, 'error')
                    tree.remove_tag(parentid, 'warning')
            elif result.severity == WARNING:
                if not (tree.has_tag(parentid, 'critical') or tree.has_tag(parentid, 'error')):
                    tree.add_tag (parentid, 'warning')
            tree.remove_tag(parentid, 'info')
            tree.item(parentid, open=True)
            parentid = self.tree.parent(parentid)

    def escape_keypressed(self, event=None):
        self.top.destroy()

    def display(self,priority,text):
        if priority == 'c': self.criticals += 1
        if priority == 'f': self.errors    += 1
        if priority == 'w': self.warnings  += 1       
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
        msg = "Criticals: {0}\nErrors: {0}\nWarnings: {1}".format(self.criticals, self.errors, self.warnings)
        self.textb.config(state=NORMAL)
        self.textb.insert(1.0, msg + "\n\n")  # at beginning
        self.textb.insert(END, "\n\n" + msg)  # at end
        self.textb.config(state=DISABLED)

        # update status bar
        if self.criticals == 1: critical_text = "1 critical"
        else:                   critical_text = "{0} criticals".format(self.criticals)
        if self.errors == 1: error_text = "1 error"
        else:                error_text = "{0} errors".format(self.errors)
        if self.warnings == 1: warn_text = "1 warning"
        else:                  warn_text = "{0} warnings".format(self.warnings)
        self.status.set_info("{0}, {1}, {2}.", critical_text, error_text, warn_text)

    def num_errors(self):
        return self.criticals + self.errors
