from pp_utils import enum

# must be a string that can be cast to float
__version__ = "1.3"


PPObjTypes = enum('PROFILE', 'SHOW', 'LIST', 'TRACK', 'FIELD')
PROFILE  = PPObjTypes.PROFILE
SHOW     = PPObjTypes.SHOW
LIST     = PPObjTypes.LIST
TRACK    = PPObjTypes.TRACK
FIELD    = PPObjTypes.FIELD

ValidationSeverity = enum('NONE', 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'OK')
CRITICAL = ValidationSeverity.CRITICAL
ERROR    = ValidationSeverity.ERROR
WARNING  = ValidationSeverity.WARNING
INFO     = ValidationSeverity.INFO


class PPdefinitions(object):

    IMAGE_FILES=('Image files', '.gif','.jpg','.jpeg','.bmp','.png','.tif')
    VIDEO_FILES= ('Video Files','.asf','.avi','.mpg','.mp4','.mpeg','.m2v','.m1v','.vob','.divx','.xvid','.mov','.m4v','.m2p','.mkv','.m2ts','.ts','.mts','.wmv','.webm')
    AUDIO_FILES=('Audio files','.mp3','.wav','.ogg','.ogm','.wma','.asf','.mp2')
    WEB_FILES=('Web files','.htm','.html')

    # order of fields for editor display and which tab they are in.
    show_types = {

        'artliveshow':[
            'tab-show','sep',  
                'type','title','show-ref', 'medialist','live-tracks-dir1','live-tracks-dir2','sequence','repeat','show-canvas',
            'tab-eggtimer','sep',  
                'eggtimer-text','eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-notices','sep',              
                'empty-text','admin-x','admin-y','admin-font','admin-colour',
            'tab-show-text','sep',
                'background-image','background-colour','show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                 'duration','image-window','image-rotate','transition','sep',
                'audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','sep',
                'omx-audio','omx-volume','omx-window','freeze-at-end','omx-other-options',
            'tab-controls','sep',  
                'disable-controls','controls'
            ],

        'artmediashow':[
            'tab-show','sep',  
                'type','title','show-ref', 'medialist','sequence','repeat','show-canvas',
            'tab-eggtimer','sep',  
                'eggtimer-text','eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-notices','sep',              
                'empty-text','admin-x','admin-y','admin-font','admin-colour',
            'tab-show-text','sep',
                'background-image','background-colour','show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                'duration','image-window','image-rotate','transition','sep',
                'audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','sep',
                'omx-audio','omx-volume','omx-window','freeze-at-end','omx-other-options',
            'tab-controls','sep',  
                'disable-controls','controls'
            ],
    
        'mediashow':[
            'tab-show','sep',  
                'type','title','show-ref', 'medialist','show-timeout','sep',
            'trigger-start-type','trigger-start-param','trigger-next-type','trigger-next-param','sequence','track-count-limit','repeat','interval','trigger-end-type','trigger-end-param',
            'sep','show-canvas',
            'tab-child','sep',  
                'child-track-ref', 'hint-text', 'hint-x','hint-y','hint-font','hint-colour',
            'tab-eggtimer','sep',  
                'eggtimer-text','eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-notices','sep',              
            'trigger-wait-text','empty-text','admin-x','admin-y','admin-font','admin-colour',
            'tab-show-text','sep',
                'background-image','background-colour','show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',
                'duration','image-window','image-rotate','transition','sep',
                'audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','sep',
                'omx-audio','omx-volume','omx-window','freeze-at-end','omx-other-options','sep',
                'web-window',
            'tab-controls','sep',  
                'disable-controls', 'controls'
            ],
                 
        'menu':[
            'tab-show','sep',
                'type','title','show-ref','medialist','show-timeout','track-timeout','menu-track-ref','show-canvas',
            'tab-eggtimer','sep',  
                'eggtimer-text','eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-show-text','sep',  
                'background-image','background-colour','show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',
                'duration','image-window','image-rotate','transition','sep',
                'audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','sep',
                'omx-audio','omx-volume','omx-window','freeze-at-end','omx-other-options','sep',
                'web-window',
            'tab-controls','sep',  
                'disable-controls','controls'
            ],
        
        'liveshow':[
            'tab-show','sep',  
                'type','title','show-ref', 'medialist','live-tracks-dir1','live-tracks-dir2','show-timeout','sep',
            'trigger-start-type','trigger-start-param','trigger-next-type','trigger-next-param','sequence','track-count-limit','repeat','interval','trigger-end-type','trigger-end-param',
            'sep','show-canvas',
            'tab-child','sep',  
                'child-track-ref', 'hint-text', 'hint-x','hint-y','hint-font','hint-colour',
            'tab-eggtimer','sep',  
                'eggtimer-text','eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-notices','sep',              
                'trigger-wait-text','empty-text','admin-x','admin-y','admin-font','admin-colour',
            'tab-show-text','sep',
                'background-image','background-colour','show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',
                'duration','image-window','image-rotate','transition','sep',
                'audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','sep',
                'omx-audio','omx-volume','omx-window','freeze-at-end','omx-other-options','sep',
                'web-window',
            'tab-controls','sep',  
                'disable-controls','controls'
            ],
                   
        'hyperlinkshow':[
            'tab-show','sep',  
                'type','title','show-ref','medialist','first-track-ref','home-track-ref','show-timeout','track-timeout','timeout-track-ref','show-canvas', 'debug-path',         
            'tab-eggtimer','sep',  
                'eggtimer-text','eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-show-text','sep',
                'background-image','background-colour','show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep', 
                'duration','image-window','image-rotate','transition','sep',
                'audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','sep',
                'omx-audio','omx-volume','omx-window','freeze-at-end','omx-other-options','sep',
                'web-window',
            'tab-links','sep',
                'disable-controls','links'
            ],

        'radiobuttonshow':[
            'tab-show','sep',  
                'type','title','show-ref','medialist','first-track-ref','show-timeout','track-timeout','show-canvas',
            'tab-eggtimer','sep',  
                'eggtimer-text','eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-show-text','sep',
                'background-image','background-colour','show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                'duration','image-window','image-rotate','transition','sep',
                'audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','sep',
                'omx-audio','omx-volume','omx-window','freeze-at-end','omx-other-options','sep',
                'web-window',
            'tab-links','sep',
                'disable-controls','links'
            ],

        'start':[
            'tab-show','sep',  
                'type','title','show-ref','start-show', 'plugin'
        ]
    }


    # field details for creating new shows and for update of profile    
    new_shows={
        'artliveshow':{
                'title': 'New ArtLiveshow','show-ref':'','show-canvas':'',  'type': 'artliveshow', 'disable-controls':'no','sequence': 'ordered','repeat':'repeat','medialist': '',
                'show-text':'','show-text-font':'{Liberation Sans} 20 bold','show-text-colour':'white','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                'eggtimer-text':'Loading....', 'eggtimer-x':'100','eggtimer-y':'100','eggtimer-font':'{Liberation Sans} 10 bold','eggtimer-colour':'white',
                'empty-text':'Nothing to show','admin-font':'{Liberation Sans} 10 bold','admin-colour':'white','admin-x':'100','admin-y':'200',
                'transition': 'cut', 'duration': '5','image-window':'original','image-rotate':'0','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                'omx-audio': 'hdmi','omx-volume':'0','omx-window':'warp 300 300 655 500','omx-other-options': '','freeze-at-end':'yes',
                'live-tracks-dir1':'','live-tracks-dir2':'',
                'controls':'pp-down down\npp-stop stop\npp-pause pause\n'},

        'artmediashow':{
                'title': 'New ArtMediashow','show-ref':'','show-canvas':'',  'type': 'artmediashow', 'disable-controls':'no','sequence': 'ordered','repeat':'repeat','medialist': '',
                'show-text':'','show-text-font':'{Liberation Sans} 20 bold','show-text-colour':'white','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                'eggtimer-text':'Loading....','eggtimer-x':'100','eggtimer-y':'100','eggtimer-font':'{Liberation Sans} 10 bold','eggtimer-colour':'white',
                'empty-text':'Nothing to show','admin-font':'{Liberation Sans} 10 bold','admin-colour':'white','admin-x':'100','admin-y':'200',
                'transition': 'cut', 'duration': '5','image-window':'original','image-rotate':'0','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                'omx-audio': 'hdmi','omx-volume':'0','omx-window':'warp 300 300 655 500','omx-other-options': '','freeze-at-end':'yes',
                'controls':'pp-down down\npp-stop stop\npp-pause pause\n'},

       'hyperlinkshow':{
                'type':'hyperlinkshow','title':'New Hyperlink Show','show-ref':'', 'show-canvas':'', 'medialist':'','debug-path':'no',
                'links':'','first-track-ref':'','home-track-ref':'','timeout-track-ref':'','disable-controls':'no','show-timeout': '0','track-timeout': '0',
                'show-text':'','show-text-font':'{Liberation Sans} 20 bold','show-text-colour':'white','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                'eggtimer-text':'Loading....','eggtimer-x':'100','eggtimer-y':'100','eggtimer-font':'{Liberation Sans} 10 bold','eggtimer-colour':'white',
                'transition': 'cut', 'duration': '0','image-window':'original','image-rotate':'0',
                'audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                'omx-audio': 'hdmi','omx-volume':'0','omx-window':'warp 300 300 655 500','omx-other-options': '','web-window':'warp 300 300 700 700','freeze-at-end':'yes'
                },

       'radiobuttonshow':{
                'type':'radiobuttonshow','title':'New Radio Button Show','show-ref':'', 'show-canvas':'', 'medialist':'',
                'links':'','first-track-ref':'','disable-controls':'no','show-timeout': '0','track-timeout': '0',
                'show-text':'','show-text-font':'{Liberation Sans} 20 bold','show-text-colour':'white','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                'eggtimer-text':'Loading....','eggtimer-x':'100','eggtimer-y':'100','eggtimer-font':'{Liberation Sans} 10 bold','eggtimer-colour':'white',
                'transition': 'cut', 'duration': '0','image-window':'original','image-rotate':'0',
                'audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                'omx-audio': 'hdmi','omx-volume':'0','omx-window':'warp 300 300 655 500','omx-other-options': '','web-window':'warp 300 300 700 700','freeze-at-end':'yes'
                },

        'mediashow':{
                'title': 'New Mediashow','show-ref':'', 'show-canvas':'', 'type': 'mediashow','medialist': '','show-timeout': '0','interval':'0','track-count-limit':'0',
                'disable-controls':'no','trigger-start-type': 'start','trigger-start-param':'','trigger-next-type': 'continue','trigger-next-param':'','sequence': 'ordered','repeat': 'repeat','trigger-end-type':'none', 'trigger-end-param':'',
                'child-track-ref': '', 'hint-text': '', 'hint-x':'200','hint-y': '750','hint-font': '{Liberation Sans} 30 bold','hint-colour': 'white',
                'eggtimer-text':'Loading....','eggtimer-x':'100','eggtimer-y':'100','eggtimer-font':'{Liberation Sans} 10 bold','eggtimer-colour':'white',
                'trigger-wait-text':'Waiting for Trigger....','empty-text':'Nothing to show','admin-font':'{Liberation Sans} 10 bold','admin-colour':'white','admin-x':'100','admin-y':'200',
                'show-text':'','show-text-font':'{Liberation Sans} 20 bold','show-text-colour':'white','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                'transition': 'cut', 'duration': '5','image-window':'original','image-rotate':'0','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'','web-window':'warp 300 300 700 700',
                'omx-audio': 'hdmi','omx-volume':'0','omx-window':'warp 300 300 655 500','omx-other-options': '','freeze-at-end':'yes',
                'controls':'pp-down down\npp-up up\npp-play play\npp-stop stop\npp-pause pause\n'},
                             
        'liveshow':{
                'title': 'New Liveshow','show-ref':'','show-canvas':'', 'type': 'liveshow','show-timeout': '0','interval':'0','track-count-limit':'0',
                'disable-controls':'no','trigger-start-type':'start','trigger-start-param':'','trigger-next-type': 'continue','trigger-next-param':'','sequence': 'ordered','repeat': 'repeat','trigger-end-type':            'none', 'trigger-end-param':'','medialist': '',
                'child-track-ref': '', 'hint-text': '','hint-x':'200', 'hint-y': '750','hint-font': '{Liberation Sans} 30 bold','hint-colour': 'white',
                'trigger-wait-text':'Waiting for Trigger....','empty-text':'Nothing to show','admin-font':'{Liberation Sans} 10 bold','admin-colour':'white','admin-x':'100','admin-y':'200',
                'show-text':'','show-text-font':'{Liberation Sans} 20 bold','show-text-colour':'white','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                'eggtimer-text':'Loading....','eggtimer-x':'100','eggtimer-y':'100','eggtimer-font':'{Liberation Sans} 10 bold','eggtimer-colour':'white',
                'transition': 'cut', 'duration': '5','image-window':'original','image-rotate':'0','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                'omx-audio': 'hdmi','omx-volume':'0','omx-window':'warp 300 300 655 500','omx-other-options': '','web-window':'warp 300 300 700 700','freeze-at-end':'yes',
                'live-tracks-dir1':'','live-tracks-dir2':'',
                'controls':'pp-down down\npp-up up\npp-play play\npp-stop stop\npp-pause pause\n'},

        'menu':{
                'show-ref': '', 'title': 'New Menu','type': 'menu','medialist': '','show-canvas':'',
                'show-timeout': '0','track-timeout':'0','menu-track-ref':'menu-track',
                'eggtimer-text':'Loading....','eggtimer-x':'100','eggtimer-y':'100','eggtimer-font':'{Liberation Sans} 10 bold','eggtimer-colour':'white',                       
                'show-text':'','show-text-font':'{Liberation Sans} 20 bold','show-text-colour':'white','show-text-x':'100','show-text-y':'50','background-image':'','background-colour':'',
                'transition': 'cut',  'duration': '5','image-window':'original','image-rotate':'0','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0', 'mplayer-other-options':'',
                'omx-audio': 'hdmi','omx-volume':'0','omx-window':'warp 300 300 655 500','omx-other-options': '','web-window':'warp 300 300 700 700','freeze-at-end':'yes',
                'disable-controls':'no','controls':'pp-down down\npp-up up\npp-play play\npp-stop stop\npp-pause pause\n'},    
    
        'start':{'title': 'Start','show-ref':'start', 'type': 'start','start-show':'', 'plugin':''}
    }
    
    values_yes_no           = ['yes', 'no']
    values_mplayer_audio    = ['hdmi', 'local']
    values_omxplayer_audio  = ['hdmi', 'local', 'both']
    values_speaker_channels = ['left', 'right', 'stereo']
    values_transition       = ['cut', ]
    values_repeat           = ['repeat', 'single-run']
    values_sequence         = ['ordered', 'shuffle']
    values_trigger_start    = ['start', 'input', 'input-persist']
    values_trigger_end      = ['none', 'input', 'duration']
    values_trigger_next     = ['continue', 'input']
    values_volume_range     = [-60, 0]

    # VALIDATION RULES
    # Rule names correspond to function names in the validator module.
    # The rule value is converted as follows:
    #    - It is prepended with 'rule_'
    #    - Dashes are converted to underscores.
    #    - The first argument is always the value to test
    #    - An args argument may be added if a rule includes an args element.
    # For example, a rule value of 'is-in-list' is converted and called as:
    #    'validator.rule_is_one_of(value, args)'
    # Rule functions return a RuleResult with:
    #     blank = True if the value is blank (passed = None)
    #     passed = False if the value fails to meet the criteria of the rule.
    #     passed = True  if the value passes validation

    show_field_rules = {
        # rulesets           # list of ruleset(string) or list of ruleset(dict: keys='rule','args')
        # same as spec---    list of rules the value must pass--------
        'audio-speaker'    : [{'rule': 'is-in-list', 'args': values_speaker_channels}, ],
        'background-color' : ['is-color'],
        'background-image' : ['is-image-file', 'file-exists'],
        'child-track-ref'  : [{'rule':'is-in-list', 'args': 'track-labels'}],
        'controls'         : ['is-control-script'],
        'track-count-limit': ['is-zero-or-positive-integer'],

        'debug-path'       : ['is-yes-no'],
        'disable-controls' : ['is-yes-no'],
        'duration'         : ['is-zero-or-positive-integer'],  # seconds
        'first-track-ref'  : [{'rule': 'is-in-list', 'args': 'track-labels'}],
        'has-background'   : ['is-yes-no'],
        'home-track-ref'   : [{'rule': 'is-in-list', 'args': 'track-labels'}],
        'image-rotate'     : ['is-zero-or-positive-integer'],
        'image-window'     : ['is-image-window', 'is-not-blank'],
        'interval'         : ['is-hh-mm-ss-or-seconds'],
        'links'            : [{'rule': 'is-script', 'args': 'track-labels', 'field-arg': 'type'}],
        'live-tracks-dir1' : ['dir-exists'],
        'live-tracks-dir2' : ['dir-exists'],
        'medialist'        : ['is-medialist-file'],
        'menu-track-ref'   : [{'rule': 'is-in-list', 'args': 'track-labels'}],
        'mplayer-audio'    : [{'rule': 'is-in-list',   'args': values_mplayer_audio}],
        #'mplayer-other-options': [''],
        'mplayer-volume'   : [{'rule': 'is-in-range', 'args': values_volume_range}],
        'omx-audio'        : [{'rule': 'is-in-list',   'args': values_omxplayer_audio}],
        #'omx-other-options': [ '' ],  # validating the command line options for omx would be cumbersome
        'omx-volume'       : [{'rule': 'is-in-range', 'args': values_volume_range}],
        'omx-window'       : ['is-video-window', 'is-not-blank'],
        'freeze-at-end'    : ['is-yes-no'],

        'plugin'           : ['file-exists'],
        'repeat'           : [{'rule': 'is-in-list', 'args': values_repeat}],
        'sequence'         : [{'rule': 'is-in-list', 'args': values_sequence}],
        'show-canvas'      : ['is-rectangle' ],
        'show-ref'         : [{'rule': 'is-showref', 'field-arg': 'type'}],
        'start-show'       : [{'rule': 'is-startshow', 'args': 'show-labels'}], # is-not-blank is checked separately
        'show-timeout'     : ['is-hh-mm-ss-or-seconds'],
        'timeout-track-ref': [{'rule': 'is-in-list', 'args': 'track-labels'}],
        #'title'            : [ '' ],  # no validation... can be anything, even blank
        'track-timeout'    : ['is-hh-mm-ss-or-seconds'],
        'transition'       : [{'rule': 'is-in-list', 'args': values_transition}],
        'trigger-start-type' : [{'rule': 'is-in-list', 'args': values_trigger_start}],
        'trigger-end-type'   : [{'rule': 'is-in-list', 'args': values_trigger_end}],
        'trigger-next-type'  : [{'rule': 'is-in-list', 'args': values_trigger_next}],
        'trigger-start-param': [{'rule': 'is-trigger-param', 'field-arg': 'trigger-start-type'}],
        'trigger-end-param'  : [{'rule': 'is-trigger-param', 'field-arg': 'trigger-end-type'}],
        'trigger-next-param' : [{'rule': 'is-trigger-param', 'field-arg': 'trigger-next-type'}],
        'type'               : ['is-show-type'],
        'web-window'         : ['is-web-window', 'is-not-blank'],

        # Text items

            'eggtimer-text'    : [{'required-fields' : ['eggtimer-colour', 'eggtimer-font', 'eggtimer-x', 'eggtimer-y']}, ],
            'eggtimer-color'   : [{'rule': 'is-color',   'dependents': 'eggtimer-text', 'severity': WARNING}, ],
            'eggtimer-font'    : [{'rule': 'is-font',    'dependents': 'eggtimer-text', 'severity': WARNING}, ],
            'eggtimer-x'       : [{'rule': 'is-integer', 'dependents': 'eggtimer-text'}, ],
            'eggtimer-y'       : [{'rule': 'is-integer', 'dependents': 'eggtimer-text'}, ],

            'hint-text'        : [{'required-fields' : ['hint-colour', 'hint-font', 'hint-x', 'hint-y']}, ],
            'hint-color'       : [{'rule': 'is-color',   'dependents': 'hint-text', 'severity': WARNING}, ],
            'hint-font'        : [{'rule': 'is-font',    'dependents': 'hint-text', 'severity': WARNING}, ],
            'hint-x'           : [{'rule': 'is-integer', 'dependents': 'hint-text'}, ],
            'hint-y'           : [{'rule': 'is-integer', 'dependents': 'hint-text'}, ],

            'show-text'        : [{'required-fields' : ['show-text-colour', 'show-text-font', 'show-text-x', 'show-text-y']}],
            'show-text-color'  : [{'rule': 'is-color',   'dependents': 'show-text', 'severity': WARNING}, ],
            'show-text-font'   : [{'rule': 'is-font',    'dependents': 'show-text', 'severity': WARNING}, ],
            'show-text-x'      : [{'rule': 'is-integer', 'dependents': 'show-text'}, ],
            'show-text-y'      : [{'rule': 'is-integer', 'dependents': 'show-text'}, ],

            'text'             : [{'required-fields' : ['message-colour', 'message-font'], }],
            'message-font'     : [{'rule': 'is-font',    'dependents': 'text'}, 'is-not-blank'],  # this is the only field with must = yes... why?
            'message-color'    : [{'rule': 'is-color',   'dependents': 'text', 'severity': WARNING}, ],

            'empty-text'       : [{'required-fields': ['admin-colour', 'admin-font', 'admin-x', 'admin-y']}, ],
            'trigger-wait-text': [{'required-fields': ['admin-colour', 'admin-font', 'admin-x', 'admin-y']}, ],
            'admin-color'      : [{'rule': 'is-color',   'dependents': ['trigger-wait-text', 'empty-text'], 'severity': WARNING}, ],
            'admin-font'       : [{'rule': 'is-font',    'dependents': ['trigger-wait-text', 'empty-text'], 'severity': WARNING}, ],
            'admin-x'          : [{'rule': 'is-integer', 'dependents': ['trigger-wait-text', 'empty-text']}, ],
            'admin-y'          : [{'rule': 'is-integer', 'dependents': ['trigger-wait-text', 'empty-text']}, ],
    }

    show_field_specs={
        'sep'               :{'shape':'sep'},
        'admin-font'        :{'shape':'font',   'text':'Notice Text Font','must':'no','read-only':'no'},
        'admin-colour'      :{'shape':'colour', 'text':'Notice Text Colour','must':'no','read-only':'no'},
        'admin-x'           :{'shape':'entry',  'text':'Notice Text x Position','must':'no','read-only':'no'},
        'admin-y'           :{'shape':'entry',  'text':'Notice Text y Position','must':'no','read-only':'no'},
        'audio-speaker'     :{'shape':'option-menu','text':'Audio Speaker','must':'no','read-only':'no',
                              'values':values_speaker_channels},

        'background-colour' :{'shape':'colour', 'text':'Background Colour','must':'no','read-only':'no'},
        'background-image'  :{'shape':'browse', 'text':'Background Image','must':'no','read-only':'no'},
        'child-track-ref'   :{'shape':'entry',  'text':'Child Track','must':'no','read-only':'no'},
        'controls'          :{'shape':'text',   'text':'Controls','must':'no','read-only':'no'},
        'track-count-limit' :{'shape':'entry',  'text':'Track Count Limit','must':'no','read-only':'no'},

        'debug-path'        :{'shape':'option-menu', 'text':'Print Path Debug ','must':'no','read-only':'no','values':values_yes_no},
        'disable-controls'  :{'shape':'option-menu', 'text':'Disable Controls ','must':'no','read-only':'no','values':values_yes_no},
        'duration'          :{'shape':'entry',  'text':'Duration (secs)','must':'no','read-only':'no'},
        'eggtimer-text'     :{'shape':'text',   'text':'Egg Timer Text','must':'no','read-only':'no'},
        'eggtimer-x'        :{'shape':'entry',  'text':'Egg Timer x Position','must':'no','read-only':'no'},
        'eggtimer-y'        :{'shape':'entry',  'text':'Egg Timer y Position','must':'no','read-only':'no'},
        'eggtimer-font'     :{'shape':'font',   'text':'Egg Timer Font','must':'no','read-only':'no'},
        'eggtimer-colour'   :{'shape':'colour', 'text':'Egg Timer Colour','must':'no','read-only':'no'},
        'empty-text'        :{'shape':'text',   'text':'Live Tracks Empty Text','must':'no','read-only':'no'},

        'first-track-ref'   :{'shape':'entry',  'text':'First Track','must':'no','read-only':'no'},
        'has-background'    :{'shape':'option-menu','text':'Has Background Image','must':'no','read-only':'no','values':values_yes_no},
        'home-track-ref'    :{'shape':'entry',  'text':'Home Track','must':'no','read-only':'no'},
        'hint-text'         :{'shape':'text',   'text':'Hint Text','must':'no','read-only':'no'},
        'hint-x'            :{'shape':'entry',  'text':'Hint Text x Position','must':'no','read-only':'no'},
        'hint-y'            :{'shape':'entry',  'text':'Hint Text y Position','must':'no','read-only':'no'},
        'hint-font'         :{'shape':'font',   'text':'Hint Font','must':'no','read-only':'no'},
        'hint-colour'       :{'shape':'colour', 'text':'Hint Colour','must':'no','read-only':'no'},
        'image-rotate'      :{'shape':'entry',  'text':'Image Rotation','must':'no','read-only':'no'},
        'image-window'      :{'shape':'entry',  'text':'Image Window','must':'no','read-only':'no'},
        'interval'          :{'shape':'entry',  'text':'Repeat Interval','must':'no','read-only':'no'},
        'links'             :{'shape':'text',   'text':'Controls','must':'no','read-only':'no'},
        'live-tracks-dir1'  :{'shape':'entry',  'text':'Live Tracks Directory 1','must':'no','read-only':'no'},
        'live-tracks-dir2'  :{'shape':'entry',  'text':'Live Tracks Directory 2 ','must':'no','read-only':'no'},
        'medialist'         :{'shape':'entry',  'text':'Medialist','must':'no','read-only':'no'},
        'menu-track-ref'    :{'shape':'entry',  'text':'Menu Track','must':'no','read-only':'no'},
        'message-font'      :{'shape':'font',   'text':'Text Font','must':'yes','read-only':'no'},
        'message-colour'    :{'shape':'colour', 'text':'Text Colour','must':'yes','read-only':'no'},
        'mplayer-audio'     :{'shape':'option-menu','text':'Audio Player Audio','must':'no','read-only':'no',
                              'values':values_mplayer_audio},
        'mplayer-other-options':{'shape':'entry','text':'Audio Player Options','must':'no','read-only':'no'},
        'mplayer-volume'    :{'shape':'entry',  'text':'Audio Volume','must':'no','read-only':'no'},
        'omx-audio'         :{'shape':'option-menu','text':'Video Player Audio','must':'no','read-only':'no',
                              'values':values_omxplayer_audio},
        'omx-other-options' :{'shape':'entry',  'text':'Video Player Options','must':'no','read-only':'no'},
        'omx-volume'        :{'shape':'entry',  'text':'Video Player Volume','must':'no','read-only':'no'},
        'omx-window'        :{'shape':'entry',  'text':'Video Window','must':'no','read-only':'no'},
        'freeze-at-end'     :{'shape':'option-menu','text':'Freeze at End','must':'no','read-only':'no',
                              'values':values_yes_no},

        'plugin'            :{'shape':'browse', 'text':'Plugin Config File','must':'no','read-only':'no'},
        'repeat'            :{'shape':'option-menu','text':'Repeat/Single','must':'no','read-only':'no',
                              'values':values_repeat},
        'sequence'          :{'shape':'option-menu','text':'Sequence','must':'no','read-only':'no',
                              'values':values_sequence},
        'show-canvas'       :{'shape':'entry',  'text':'Show Canvas','must':'no','read-only':'no'},                    
        'show-ref'          :{'shape':'entry',  'text':'Show Reference','must':'no','read-only':'no'},
        'show-text'         :{'shape':'text',   'text':'Show Text','must':'no','read-only':'no'},
        'show-text-font'    :{'shape':'font',   'text':'Show Text Font','must':'no','read-only':'no'},
        'show-text-colour'  :{'shape':'colour', 'text':'Show Text Colour','must':'no','read-only':'no'},
        'show-text-x'       :{'shape':'entry',  'text':'Show Text x Position','must':'no','read-only':'no'},
        'show-text-y'       :{'shape':'entry',  'text':'Show Text y Position','must':'no','read-only':'no'},
        'start-show'        :{'shape':'entry',  'text':'Start Shows','must':'no','read-only':'no'},
        'tab-animation'     :{'shape':'tab',    'name':'animation','text':'Animation'},
        'tab-child'         :{'shape':'tab',    'name':'child','text':'Child Track'},
        'tab-controls'      :{'shape':'tab',    'name':'controls','text':'Controls'},
        'tab-eggtimer'      :{'shape':'tab',    'name':'eggtimer','text':'Egg Timer'},
        'tab-links'         :{'shape':'tab',    'name':'links','text':'Controls'},
        'tab-notices'       :{'shape':'tab',    'name':'notices','text':'Notices'},
        'tab-show'          :{'shape':'tab',    'name':'show','text':'Show'},
        'tab-show-text'     :{'shape':'tab',    'name':'show-text','text':'Show Background and Text'},
        'tab-menu-text'     :{'shape':'tab',    'name':'menu-text','text':'Menu Text'},
        'tab-track'         :{'shape':'tab',    'name':'track','text':'Track'},
        'tab-tracks'        :{'shape':'tab',    'name':'tracks','text':'Track Defaults'},
        'text'              :{'shape':'text',   'text':'Message Text','must':'no','read-only':'no'},
        'show-timeout'      :{'shape':'entry',  'text':'Show Timeout','must':'no','read-only':'no'},
        'timeout-track-ref' :{'shape':'entry',  'text':'Timeout Track','must':'no','read-only':'no'},
        'title'             :{'shape':'entry',  'text':'Title','must':'no','read-only':'no'},
        'track-timeout'     :{'shape':'entry',  'text':'Track Timeout (secs)','must':'no','read-only':'no'},
        'transition'        :{'shape':'option-menu','text':'Transition','must':'no','read-only':'no',
                              'values':values_transition},
        'trigger-start-type':{'shape':'option-menu','text':'Trigger for Start','must':'no','read-only':'no',
                              'values':values_trigger_start},
        'trigger-end-type'  :{'shape':'option-menu','text':'Trigger for End','must':'no','read-only':'no','values':values_trigger_end},
        'trigger-next-type' :{'shape':'option-menu','text':'Trigger for next','must':'no','read-only':'no','values':values_trigger_next},
        'trigger-next-param':{'shape':'entry',  'text':'Next Trigger Parameters','must':'no','read-only':'no'},
        'trigger-start-param':{'shape':'entry', 'text':'Start Trigger Parameters','must':'no','read-only':'no'},
        'trigger-end-param' :{'shape':'entry',  'text':'End Trigger Parameters','must':'no','read-only':'no'},
        'trigger-wait-text' :{'shape':'text',   'text':'Trigger Wait Text','must':'no','read-only':'no'},
        'type'              :{'shape':'entry',  'text':'Type','must':'no','read-only':'yes'},
        'web-window'        :{'shape':'entry',  'text':'Web Window','must':'no','read-only':'no'},
        }

    track_types={
        'video':[
            'tab-track','sep',  
                    'type','title','track-ref','location','thumbnail','freeze-at-end','omx-audio','omx-volume','omx-window','omx-other-options',
                    'background-colour','background-image','display-show-background','plugin','seamless-loop',
            'tab-track-text','sep',
                'track-text','track-text-font','track-text-colour','track-text-x','track-text-y','display-show-text',
            'tab-links','sep',
                'links',
            'tab-show-control','sep',
                'show-control-begin','show-control-end',
            'tab-animate','sep',
                'animate-begin','animate-clear','animate-end'
            ],
                
        'message':[
            'tab-track','sep',  
                'type','title','track-ref','text','thumbnail','duration','message-font','message-colour','message-justify','message-x','message-y',
            'background-colour','background-image','display-show-background','plugin',
            'tab-track-text','sep',
                'track-text','track-text-font','track-text-colour','track-text-x','track-text-y','display-show-text',
            'tab-links','sep',
                'links',
            'tab-show-control','sep',
                'show-control-begin','show-control-end',
            'tab-animate','sep',
                'animate-begin','animate-clear','animate-end'
            ],
        
                
        'show':[
            'tab-track','sep',  
                'type','title','track-ref','sub-show','thumbnail'
            ],
        
                 
        'image':[
            'tab-track','sep',  
                'type','title','track-ref','location','thumbnail','duration','transition','image-window','image-rotate','background-colour','background-image','display-show-background','plugin',
            'tab-track-text','sep',
                'track-text','track-text-font','track-text-colour','track-text-x','track-text-y','display-show-text','pause-text','pause-text-font','pause-text-colour','pause-text-x','pause-text-y',
            'tab-links','sep',
                'links',
            'tab-show-control','sep',
                'show-control-begin','show-control-end',
            'tab-animate','sep',
                'animate-begin','animate-clear','animate-end'
            ],


        'menu':[
            'tab-track','sep',
                'type','title','track-ref','background-colour','background-image','entry-font','entry-colour', 'entry-select-colour','display-show-background','plugin',
            'tab-menu-geometry','sep',
                'menu-window','menu-direction','menu-rows','menu-columns','menu-icon-mode','menu-text-mode','menu-bullet','menu-icon-width','menu-icon-height',
                'menu-horizontal-padding','menu-vertical-padding','menu-text-width','menu-text-height','menu-horizontal-separation','menu-vertical-separation',
            'menu-strip','menu-strip-padding','menu-guidelines',
            'tab-track-text','sep',
                   'hint-text', 'hint-x', 'hint-y', 'hint-font', 'hint-colour','sep', 'track-text', 'track-text-font', 'track-text-colour','track-text-x', 'track-text-y', 'display-show-text',
            'tab-links','sep',  
               'links',
            'tab-show-control','sep',
                 'show-control-begin','show-control-end',
            'tab-animate','sep',
                 'animate-begin','animate-clear','animate-end'
            ],
               
        'audio':[
            'tab-track','sep',  
                'type','title','track-ref','location','thumbnail','duration','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options',
                       'background-colour','background-image','display-show-background','plugin',
            'tab-track-text','sep',
                 'track-text','track-text-font','track-text-colour','track-text-x','track-text-y','display-show-text',
            'tab-links','sep',
                 'links',
            'tab-show-control','sep',
                 'show-control-begin','show-control-end',
            'tab-animate','sep',
                 'animate-begin','animate-clear','animate-end'
                 ],

         'web':[
            'tab-track','sep',  
                'type','title','track-ref','location','thumbnail','duration','web-window',
                       'background-colour','background-image','display-show-background','plugin',
            'tab-track-text','sep',
                 'track-text','track-text-font','track-text-colour','track-text-x','track-text-y','display-show-text',
            'tab-browser-commands','sep',
                 'browser-commands',
            'tab-links','sep',
                 'links',
            'tab-show-control','sep',
                 'show-control-begin','show-control-end',
            'tab-animate','sep',
                 'animate-begin','animate-clear','animate-end'
                 ]

                         }                   

    new_tracks={
        'video':{'title':'New Video','track-ref':'','type':'video','location':'','thumbnail':'','freeze-at-end':'yes','seamless-loop':'no',
                 'omx-audio':'','omx-volume':'','omx-window':'','omx-other-options': '','background-colour':'','background-image':'','display-show-background':'yes','display-show-text':'yes',
                 'track-text':'','track-text-font':'{Liberation Sans} 20 bold',
                 'track-text-colour':'white','track-text-x':'0','track-text-y':'40','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':'','plugin':''},
               
        'message':{'title':'New Message','track-ref':'','type':'message','text':'','thumbnail':'','duration':'','message-font':'{Liberation Sans} 30 bold','message-colour':'white','message-justify':'left','message-x':'','message-y':'',
                   'track-text':'','track-text-font':'{Liberation Sans} 20 bold','track-text-colour':'white','track-text-x':'0','track-text-y':'40',
                   'background-colour':'','background-image':'','display-show-background':'yes','display-show-text':'yes','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':'','plugin':''},
        
        'show':{'title':'New Show','track-ref':'','type':'show','sub-show':'','thumbnail':''},   
        
        'image':{'title':'New Image','track-ref':'','type':'image','location':'','thumbnail':'','duration':'','transition':'','image-window':'','image-rotate':'',
                 'pause-text':'Paused......','pause-text-font':'{Liberation Sans} 20 bold','pause-text-colour':'white','pause-text-x':'10','pause-text-y':'40',
                 'background-colour':'','background-image':'','display-show-background':'yes','display-show-text':'yes','track-text':'','track-text-font':'{Liberation Sans} 20 bold',
                 'track-text-colour':'white','track-text-x':'0','track-text-y':'40','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':'','plugin':''},
               
        'audio':{'title':'New Audio','track-ref':'','type':'audio','location':'', 'thumbnail':'','duration':'','audio-speaker':'','mplayer-audio':'','mplayer-volume':'','display-show-text':'yes',
                 'mplayer-other-options':'',
                 'background-colour':'','background-image':'','display-show-background':'yes',
                 'track-text':'','track-text-font':'{Liberation Sans} 20 bold','track-text-colour':'white','track-text-x':'0','track-text-y':'40','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':'','plugin':''},

        'web':{'title':'New Web','track-ref':'','type':'web','location':'', 'thumbnail':'','duration':'','web-window':'','display-show-text':'yes',
               'background-colour':'','background-image':'','display-show-background':'yes',
               'track-text':'','track-text-font':'{Liberation Sans} 20 bold','track-text-colour':'white','track-text-x':'0','track-text-y':'40','links':'',
               'show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':'','browser-commands':'','plugin':''},

        'menu':{'type':'menu','title':'Menu Track','track-ref':'menu-track','background-colour':'','background-image':'','display-show-background':'yes','plugin':'',
                'entry-font': '{Liberation Sans} 30 bold','entry-colour': 'white', 'entry-select-colour': 'red',
                'menu-window':'300 250','menu-direction':'vertical','menu-rows':'10','menu-columns':'1','menu-icon-mode':'bullet','menu-text-mode':'right',
                'menu-bullet':'/home/pi/pipresents/pp_resources/bullet.png',
                'menu-icon-width':'80','menu-icon-height':'80',
                'menu-horizontal-padding':'10','menu-vertical-padding':'10','menu-text-width':'800','menu-text-height':'50',
                'menu-horizontal-separation':'20','menu-vertical-separation':'20','menu-strip':'no','menu-strip-padding':'5','menu-guidelines':'never',
                'hint-text': 'Up, down to Select, Return to Play', 'hint-x':'200','hint-y': '980', 'hint-font': '{Liberation Sans} 30 bold', 'hint-colour': 'white',
                'display-show-text':'yes','track-text': '', 'track-text-x':'200','track-text-y': '20', 'track-text-font': '{Liberation Sans} 30 bold', 'track-text-colour': 'white',
                'show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':'',
                'links':'pp-down down\npp-up up\npp-play play\npp-stop stop\n'}
    }




    track_field_rules = {
        'animate-begin'    : ['is-animation-script'],
        'animate-end'      : ['is-animation-script'],
        'animate-clear'    : ['is-yes-no'],
        'audio-speaker'    : [{'rule': 'is-in-list', 'args': values_speaker_channels}, ],
        'background-color' : ['is-color'],
        'background-image' : ['is-image-file', 'file-exists'],
        'browser-commands' : ['is-browser-script'],
        'display-show-background': ['is-yes-no'],
        'display-show-text'      : ['is-yes-no'],
        'duration'         : ['is-zero-or-positive-integer'],
        'entry-font'       : [{'rule': 'is-font',  'severity': WARNING}, ],
        'entry-color'      : [{'rule': 'is-color', 'severity': WARNING}, ],
        'entry-select-color' : ['is-color'],
        'image-rotate'     : ['is-zero-or-positive-integer'],  # does this really need to be an integer? maybe negative allowed?
        'image-window'     : ['is-image-window', 'is-not-blank'],
        'location'         : [{'rule': 'is-location', 'field-arg': 'type'}],   # file or URL
        'links'            : [{'rule': 'is-script', 'args': 'track-labels', 'field-arg': 'type'}],  # hyperlink or radiobutton?

        'mplayer-audio'    : [{'rule': 'is-in-list', 'args': values_mplayer_audio}],
        #'mplayer-other-options': [''],
        'mplayer-volume'   : [{'rule': 'is-in-range', 'args': values_volume_range}],
        'omx-audio'        : [{'rule': 'is-in-list', 'args': values_omxplayer_audio}],
        #'omx-other-options': [ '' ],  # validating the command line options for omx would be cumbersome
        'omx-volume'       : [{'rule': 'is-in-range', 'args': values_volume_range}],
        'omx-window'       : ['is-video-window', 'is-not-blank'],

        'freeze-at-end'    : ['is-yes-no'],

        'plugin'           : ['file-exists'],
        'seamless-loop'    : ['is-yes-no'],
        'show-ref'          : [{'rule': 'is-in-list', 'args': 'show-labels'}],
        'show-control-begin': [{'rule': 'is-showcontrol-script', 'args': 'show-labels'}],
        'show-control-end'  : [{'rule': 'is-showcontrol-script', 'args': 'show-labels'}],
        'sub-show'          : [{'rule': 'is-in-list', 'args': 'show-labels'}],
        'thumbnail'        : ['is-image-file'],
        #'title'           : [''],  # no validation, could be blank or could be anything
        'track-ref'        : [{'rule': 'is-in-list', 'args': 'track-labels'}],

        'transition'       : [{'rule': 'is-in-list', 'args': values_transition}],
        'type'             : ['is-track-type'],
        'web-window'       : ['is-web-window', 'is-not-blank'],

        # menu items
            'menu-window'      : ['is-menu-window'],
            'menu-icon-mode'   : [{'rule': 'is-icon-mode', 'field-arg': 'menu-text-mode'}],
            'menu-text-mode'   : [{'rule': 'is-text-mode', 'field-arg': 'menu-icon-mode'}],
            'menu-rows'        : ['is-zero-or-positive-integer'],
            'menu-columns'     : ['is-zero-or-positive-integer'],
            'menu-icon-width'  : ['is-zero-or-positive-integer'],
            'menu-icon-height' : ['is-zero-or-positive-integer'],
            'menu-horizontal-padding'   : ['is-zero-or-positive-integer'],
            'menu-vertical-padding'     : ['is-zero-or-positive-integer'],
            'menu-text-width'           : ['is-zero-or-positive-integer'],
            'menu-text-height'          : ['is-zero-or-positive-integer'],
            'menu-horizontal-separation': ['is-zero-or-positive-integer'],
            'menu-vertical-separation'  : ['is-zero-or-positive-integer'],
            'menu-strip-padding'        : ['is-zero-or-positive-integer'],

        # Text items    

            'hint-text'        : [{'required-fields' : ['hint-colour', 'hint-font', 'hint-x', 'hint-y']}, ],
            'hint-color'       : [{'rule': 'is-color',   'dependents': 'hint-text', 'severity': WARNING}, ],
            'hint-font'        : [{'rule': 'is-font',    'dependents': 'hint-text', 'severity': WARNING}, ],
            'hint-x'           : [{'rule': 'is-integer', 'dependents': 'hint-text'}, ],
            'hint-y'           : [{'rule': 'is-integer', 'dependents': 'hint-text'}, ],

            'text'             : [{'required-fields' : ['message-colour', 'message-font'], }],
            'message-font'     : [{'rule': 'is-font',    'dependents': 'text', 'severity': WARNING}, ],
            'message-color'    : [{'rule': 'is-color',   'dependents': 'text', 'severity': WARNING}, ],
            'message-justify'  : [{'rule': 'is-text-justify', 'dependents': 'text'}],

            'pause-text'       : [{'required-fields' : ['pause-text-colour', 'pause-text-font', 'pause-text-x', 'pause-text-y']}, ],
            'pause-text-color' : [{'rule': 'is-color',   'dependents': 'pause-text', 'severity': WARNING}, ],
            'pause-text-font'  : [{'rule': 'is-font',    'dependents': 'pause-text', 'severity': WARNING}, ],
            'pause-text-x'     : [{'rule': 'is-integer', 'dependents': 'pause-text'}, ],
            'pause-text-y'     : [{'rule': 'is-integer', 'dependents': 'pause-text'}, ],

            'track-text'       : [{'required-fields' : ['track-text-colour', 'track-text-font', 'track-text-x', 'track-text-y']}, ],
            'track-text-color' : [{'rule': 'is-color',   'dependents': 'track-text', 'severity': WARNING}, ],
            'track-text-font'  : [{'rule': 'is-font',    'dependents': 'track-text', 'severity': WARNING}, ],
            'track-text-x'     : [{'rule': 'is-integer', 'dependents': 'track-text'}, ],
            'track-text-y'     : [{'rule': 'is-integer', 'dependents': 'track-text'}, ],
    }
    
    track_field_specs={'sep':{'shape':'sep'},
                            'animate-begin':{'shape':'text','text':'Animation at Beginning','must':'no','read-only':'no'},
                            'animate-end':{'shape':'text','text':'Animation at End','must':'no','read-only':'no'},
                            'animate-clear':{'shape':'option-menu','text':'Clear Animation','must':'no','read-only':'no',
                                      'values':['yes','no']},
                            'audio-speaker':{'shape':'option-menu','text':'Audio Speaker','must':'no','read-only':'no',
                                       'values':['left','right','stereo','']},
                            'background-image':{'shape':'browse','text':'Background Image','must':'no','read-only':'no'},
                            'background-colour':{'shape':'colour','text':'Background Colour','must':'no','read-only':'no'},
                            'browser-commands':{'shape':'text','text':'Browser Commands','must':'no','read-only':'no'},
                            'display-show-background':{'shape':'option-menu','text':'Display Show Background Image','must':'no','read-only':'no',
                                       'values':['yes','no','']},
                            'display-show-text':{'shape':'option-menu','text':'Display Show Text','must':'no','read-only':'no',
                                       'values':['yes','no','']},
                            'duration':{'shape':'entry','text':'Duration (secs)','must':'no','read-only':'no'},
                       
                    'entry-font':{'shape':'font','text':'Entry Font','must':'no','read-only':'no'},
                    'entry-colour':{'shape':'colour','text':'Entry Colour','must':'no','read-only':'no'},
                    'entry-select-colour':{'shape':'colour','text':'Selected Entry Colour','must':'no','read-only':'no'},

                    'hint-text':{'shape':'text','text':'Hint Text','must':'no','read-only':'no'},
                    'hint-x':{'shape':'entry','text':'Hint Text x Position','must':'no','read-only':'no'},

                    'hint-y':{'shape':'entry','text':'Hint Text y Position','must':'no','read-only':'no'},
                    'hint-font':{'shape':'font','text':'Hint Font','must':'no','read-only':'no'},
                    'hint-colour':{'shape':'colour','text':'Hint Colour','must':'no','read-only':'no'},
                    'image-rotate':{'shape':'entry','text':'Image Rotation','must':'no','read-only':'no'},
                       
                            'image-window':{'shape':'entry','text':'Image Window','must':'no','read-only':'no'},
                            'location':{'shape':'browse','text':'Location','must':'no','read-only':'no'},
                            'links':{'shape':'text','text':'Controls','must':'no','read-only':'no'},
                    'menu-background-colour':{'shape':'colour','text':'Menu Background Colour','must':'no','read-only':'no'},
                    'menu-background-image':{'shape':'browse','text':'Menu Background Image','must':'no','read-only':'no'},


                    'menu-window':{'shape':'entry','text':'Menu Window','must':'no','read-only':'no'},
                    'menu-direction':{'shape':'option-menu','text':'Direction','must':'no','read-only':'no',
                                       'values':['horizontal','vertical']},
                    'menu-rows':{'shape':'entry','text':'Rows','must':'no','read-only':'no'},
                    'menu-columns':{'shape':'entry','text':'Columns','must':'no','read-only':'no'},
                    'menu-icon-mode':{'shape':'option-menu','text':'Icon Mode','must':'no','read-only':'no',
                                       'values':['none','thumbnail','bullet']},
                    'menu-text-mode':{'shape':'option-menu','text':'Text Mode','must':'no','read-only':'no',
                                       'values':['none','overlay','right','below']},
                    'menu-strip':{'shape':'option-menu','text':'Stipple Background','must':'no','read-only':'no',
                                       'values':['no','yes']},
                    'menu-strip-padding':{'shape':'entry','text':'Stipple Background Padding','must':'no','read-only':'no'},

                    'menu-guidelines':{'shape':'option-menu','text':'Guidelines','must':'no','read-only':'no',
                                       'values':['never','auto','always']},
                    'menu-bullet':{'shape':'browse','text':'Bullet','must':'no','read-only':'no'},
                    'menu-icon-width':{'shape':'entry','text':'Icon Width','must':'no','read-only':'no'},
                    'menu-icon-height':{'shape':'entry','text':'Icon Height','must':'no','read-only':'no'},
                    'menu-horizontal-padding':{'shape':'entry','text':'Horizontal Padding','must':'no','read-only':'no'},
                    'menu-vertical-padding':{'shape':'entry','text':'Vertical Padding','must':'no','read-only':'no'},
                    'menu-horizontal-separation':{'shape':'entry','text':'Horizontal Separation','must':'no','read-only':'no'},
                    'menu-vertical-separation':{'shape':'entry','text':'Vertical Separation','must':'no','read-only':'no'},
                    'menu-text-width':{'shape':'entry','text':'Text Width','must':'no','read-only':'no'},
                    'menu-text-height':{'shape':'entry','text':'Text Height','must':'no','read-only':'no'},
                    

                            'message-font':{'shape':'font','text':'Text Font','must':'no','read-only':'no'},
                            'message-colour':{'shape':'colour','text':'Text Colour','must':'no','read-only':'no'},
                            'message-justify':{'shape':'option-menu','text':'Justification','must':'no','read-only':'no',
                                       'values':['left','center','right']},
                            'message-x':{'shape':'entry','text':'Message x Position','must':'no','read-only':'no'},
                            'message-y':{'shape':'entry','text':'Message y Position','must':'no','read-only':'no'},
                            'mplayer-audio':{'shape':'option-menu','text':'Audio Player Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local','']},
                            'mplayer-other-options':{'shape':'entry','text':'Audio Player Options','must':'no','read-only':'no'},
                            'mplayer-volume':{'shape':'entry','text':'Audio Player Volume','must':'no','read-only':'no'},
                            'omx-audio':{'shape':'option-menu','text':'Video Player Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local','both','']},
                            'omx-other-options':{'shape':'entry','text':'Video Player Options','must':'no','read-only':'no'},
                            'omx-volume':{'shape':'entry','text':'Video Player Volume','must':'no','read-only':'no'},
                            'omx-window':{'shape':'entry','text':'Video Window','must':'no','read-only':'no'},
                            'pause-text':{'shape':'text','text':'Pause Text','must':'no','read-only':'no'},
                       
                            'pause-text-font':{'shape':'font','text':'Pause Text Font','must':'no','read-only':'no'},
                            'pause-text-colour':{'shape':'colour','text':'Pause Text Colour','must':'no','read-only':'no'},
                            'pause-text-x':{'shape':'entry','text':'Pause Text x Position','must':'no','read-only':'no'},
                            'pause-text-y':{'shape':'entry','text':'Pause Text y Position','must':'no','read-only':'no'},

                            'plugin':{'shape':'browse','text':'Plugin Config File','must':'no','read-only':'no'},
                              'freeze-at-end':{'shape':'option-menu','text':'Freeze at End','must':'no','read-only':'no',
                                       'values':['yes','no']},
                            'seamless-loop':{'shape':'option-menu','text':'Seamless Loop','must':'no','read-only':'no',
                                       'values':['yes','no']},
                            'show-ref':{'shape':'entry','text':'Show Reference','must':'no','read-only':'no'},
                            'show-control-begin':{'shape':'text','text':'Show Control at Beginning','must':'no','read-only':'no'},
                            'show-control-end':{'shape':'text','text':'Show Control at End','must':'no','read-only':'no'},
                            'sub-show':{'shape':'option-menu','text':'Show to Run','must':'no','read-only':'no'},

                            'tab-animate':{'shape':'tab','name':'animate','text':'Animation'},
                            'tab-browser-commands':{'shape':'tab','name':'browser-commands','text':'Browser Commands'},
                        'tab-menu-geometry':{'shape':'tab','name':'menu-geometry','text':'Geometry'},
                            'tab-show-control':{'shape':'tab','name':'show-control','text':'Show Control'},
                            'tab-links':{'shape':'tab','name':'links','text':'Controls'},
                            'tab-track-text':{'shape':'tab','name':'track-text','text':'Text'},
                            'tab-track':{'shape':'tab','name':'track','text':'Track'},
                            'text':{'shape':'text','text':'Message Text','must':'no','read-only':'no'},
                            'thumbnail':{'shape':'browse','text':'Thumbnail','must':'no','read-only':'no'},
                            'title':{'shape':'entry','text':'Title','must':'no','read-only':'no'},
                            'track-ref':{'shape':'entry','text':'Track Reference','must':'no','read-only':'no'},
                            'track-text':{'shape':'text','text':'Track Text','must':'no','read-only':'no'},
                            'track-text-font':{'shape':'font','text':'Track Text Font','must':'no','read-only':'no'},
                            'track-text-colour':{'shape':'colour','text':'Track Text Colour','must':'no','read-only':'no'},
                            'track-text-x':{'shape':'entry','text':'Track Text x Position','must':'no','read-only':'no'},
                            'track-text-y':{'shape':'entry','text':'Track Text y Position','must':'no','read-only':'no'},
                            'transition':{'shape':'option-menu','text':'Transition','must':'no','read-only':'no','values':['cut','']},
                            'type':{'shape':'entry','text':'Type','must':'no','read-only':'yes'},
                            'web-window':{'shape':'entry','text':'Web Window','must':'no','read-only':'no'},
                          }
        
