class PPdefinitions(object):

    IMAGE_FILES=('Image files', '.gif','.jpg','.jpeg','.bmp','.png','.tif')
    VIDEO_FILES=('Video files','.mp4','.mkv','.avi','.mp2','.wmv','.m4v')
    AUDIO_FILES=('Audio files','.mp3','.wav','.ogg')
    WEB_FILES=('Web files','.htm','.html')


    # order of fields for editor display
    show_types={

        'artliveshow':[
            'tab-show','sep',  
                'type','title','show-ref', 'medialist','live-tracks-dir1','live-tracks-dir2','trigger-start-type','trigger-start-param','trigger-end-type','trigger-end-param','show-canvas',
            'tab-show-text','sep',
                   'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                'background-image','background-colour','transition', 'duration','image-window','audio-speaker','mplayer-audio',
                'mplayer-volume','mplayer-other-options','omx-audio','omx-volume','omx-window','omx-other-options','pause-at-end',
            'tab-controls','sep',  
                'disable-controls','controls'
            ],

        'artmediashow':[
            'tab-show','sep',  
                'type','title','show-ref', 'medialist','trigger-start-type','trigger-start-param','trigger-end-type','trigger-end-param','show-canvas',
            'tab-show-text','sep',
                   'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                'background-image','background-colour','transition', 'duration','image-window','audio-speaker','mplayer-audio',
                'mplayer-volume','mplayer-other-options','omx-audio','omx-volume','omx-window','omx-other-options','pause-at-end',
            'tab-controls','sep',  
                'disable-controls','controls'
            ],
    
        'mediashow':[
            'tab-show','sep',  
                     'type','title','show-ref', 'medialist','trigger-start-type','trigger-start-param','progress','trigger-next-type','trigger-next-param','sequence','repeat','repeat-interval','trigger-end-type','trigger-end-param','show-canvas',
            'tab-child','sep',  
                'has-child', 'hint-text', 'hint-x','hint-y','hint-font','hint-colour',
            'tab-eggtimer','sep',  
                 'eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-show-text','sep',
                   'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                    'background-image','background-colour','transition', 'duration','image-window','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options',
                    'omx-audio','omx-volume','omx-window','omx-other-options','web-window','pause-at-end',
            'tab-controls','sep',  
                    'disable-controls', 'controls'
            ],
                 
        'menu':[
            'tab-show','sep',  
                'type','title','show-ref','medialist','show-timeout','track-timeout','menu-background-colour','menu-background-image','entry-font','entry-colour', 'entry-select-colour','show-canvas',
            'tab-menu-geometry','sep',
                'menu-window','menu-direction','menu-rows','menu-columns','menu-icon-mode','menu-text-mode','menu-bullet','menu-icon-width','menu-icon-height',
                'menu-horizontal-padding','menu-vertical-padding','menu-text-width','menu-text-height','menu-horizontal-separation','menu-vertical-separation',
            'menu-strip','menu-strip-padding','menu-guidelines',
            'tab-menu-text','sep',
                   'hint-text', 'hint-x', 'hint-y', 'hint-font', 'hint-colour','sep', 'menu-text', 'menu-text-x', 'menu-text-y', 'menu-text-font', 'menu-text-colour',
            'tab-eggtimer','sep',  
                 'eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-show-text','sep',  
                    'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                    'background-image','background-colour','transition','duration','image-window','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options',
            'omx-audio','omx-volume','omx-window','omx-other-options','web-window','pause-at-end',
            'tab-controls','sep',  
               'disable-controls','controls'
            ],

        
        'liveshow':[
            'tab-show','sep',  
                'type','title','show-ref', 'medialist','live-tracks-dir1','live-tracks-dir2','trigger-start-type','trigger-start-param','progress','trigger-next-type','trigger-next-param','sequence','repeat','repeat-interval','trigger-end-type','trigger-end-param','show-canvas',
            'tab-child','sep',  
                    'has-child', 'hint-text', 'hint-x','hint-y','hint-font','hint-colour',
            'tab-eggtimer','sep',  
                 'eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-show-text','sep',
                   'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                'background-image','background-colour','transition', 'duration','image-window','audio-speaker','mplayer-audio',
                'mplayer-volume','mplayer-other-options','omx-audio','omx-volume','omx-window','omx-other-options','web-window','pause-at-end',
            'tab-controls','sep',  
                'disable-controls','controls'
            ],
        
                   
        'hyperlinkshow':[
            'tab-show','sep',  
                'type','title','show-ref','medialist','first-track-ref','home-track-ref','show-timeout','track-timeout','timeout-track-ref','show-canvas',          
            'tab-show-text','sep',
                'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-eggtimer','sep',  
                 'eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-tracks','sep', 
                'background-image','background-colour','transition', 'duration','image-window','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options',
            'omx-audio','omx-volume','omx-window','omx-other-options','web-window','pause-at-end',
            'tab-links','sep',
                'links',
            'tab-controls','sep',  
                'disable-controls','controls'
            ],
        

        'radiobuttonshow':[
            'tab-show','sep',  
                'type','title','show-ref','medialist','first-track-ref','show-timeout','track-timeout','show-canvas',
            'tab-show-text','sep',
                    'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-eggtimer','sep',  
                 'eggtimer-x','eggtimer-y','eggtimer-font','eggtimer-colour',
            'tab-tracks','sep',  
                'background-image','background-colour','transition', 'duration','image-window','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options',
            'omx-audio','omx-volume','omx-window','omx-other-options','web-window','pause-at-end',
            'tab-links','sep',
                'links',
            'tab-controls','sep',  
                'disable-controls','controls'
                    ],
              
                'start':[
                    'tab-show','sep',  
                        'type','title','show-ref','start-show'
                    ]
             }


    # field details for creating new shows and for update of profile    
    new_shows={

                'artliveshow':{'title': 'New ArtLiveshow','show-ref':'','show-canvas':'',  'type': 'artliveshow', 'disable-controls':'no','trigger-start-type': 'start','trigger-start-param':'','trigger-end-type':'none', 'trigger-end-param':'','medialist': '',
                        'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                         'transition': 'cut', 'duration': '5','image-window':'original','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                            'omx-audio': 'hdmi','omx-volume':'0','omx-window':'original','omx-other-options': '','pause-at-end':'yes',
                            'controls':'','live-tracks-dir1':'','live-tracks-dir2':''},

                'artmediashow':{'title': 'New ArtMediashow','show-ref':'','show-canvas':'',  'type': 'artmediashow', 'disable-controls':'no','trigger-start-type':'start','trigger-start-param':'','trigger-end-type':'none', 'trigger-end-param':'','medialist': '',
                        'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                         'transition': 'cut', 'duration': '5','image-window':'original','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                            'omx-audio': 'hdmi','omx-volume':'0','omx-window':'original','omx-other-options': '','pause-at-end':'yes',
                            'controls':''},

               'hyperlinkshow':{ 'type':'hyperlinkshow','title':'New Hyperlink Show','show-ref':'', 'show-canvas':'', 'medialist':'',
                    'links':'','first-track-ref':'','home-track-ref':'','timeout-track-ref':'','disable-controls':'no','show-timeout': '60','track-timeout': '0',
                             'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                             'eggtimer-x':'','eggtimer-y':'','eggtimer-font':'','eggtimer-colour':'',
                            'transition': 'cut', 'duration': '0','image-window':'original',
                             'audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                                 'omx-audio': 'hdmi','omx-volume':'0','omx-window':'original','omx-other-options': '','web-window':'warp','pause-at-end':'yes',
                            'controls':''},

    
               'radiobuttonshow':{ 'type':'radiobuttonshow','title':'New Radio Button Show','show-ref':'', 'show-canvas':'', 'medialist':'',
                    'links':'','first-track-ref':'','disable-controls':'no','show-timeout': '60','track-timeout': '0',
                             'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                             'eggtimer-x':'','eggtimer-y':'','eggtimer-font':'','eggtimer-colour':'',
                            'transition': 'cut', 'duration': '0','image-window':'original',
                             'audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                                   'omx-audio': 'hdmi','omx-volume':'0','omx-window':'original','omx-other-options': '','web-window':'warp','pause-at-end':'yes',
                                   'controls':''},
    
                'mediashow':{'title': 'New Mediashow','show-ref':'', 'show-canvas':'', 'type': 'mediashow','medialist': '',
                          'disable-controls':'no','trigger-start-type': 'start','trigger-start-param':'','progress': 'auto','trigger-next-type': 'continue','trigger-next-param':'','sequence': 'ordered','repeat': 'interval','repeat-interval': '10','trigger-end-type':'none', 'trigger-end-param':'',
                            'has-child': 'no', 'hint-text': '', 'hint-x':'200','hint-y': '980','hint-font': 'Helvetica 30 bold','hint-colour': 'white',
                             'eggtimer-x':'','eggtimer-y':'','eggtimer-font':'','eggtimer-colour':'',
                            'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                            'transition': 'cut', 'duration': '5','image-window':'original','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'','web-window':'warp',
                             'omx-audio': 'hdmi','omx-volume':'0','omx-window':'original','omx-other-options': '','pause-at-end':'yes',
                             'controls':''},
                                     
                'liveshow':{'title': 'New Liveshow','show-ref':'','show-canvas':'',  'type': 'liveshow', 'disable-controls':'no','trigger-start-type': 'start','trigger-start-param':'','progress': 'auto','trigger-next-type': 'continue','trigger-next-param':'','sequence': 'ordered','repeat': 'interval','repeat-interval': '10','trigger-end-type':'none', 'trigger-end-param':'','medialist': '',
                        'has-child': 'no', 'hint-text': '','hint-x':'200', 'hint-y': '980','hint-font': 'Helvetica 30 bold','hint-colour': 'white',
                        'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                        'eggtimer-x':'','eggtimer-y':'','eggtimer-font':'','eggtimer-colour':'',
                         'transition': 'cut', 'duration': '5','image-window':'original','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                            'omx-audio': 'hdmi','omx-volume':'0','omx-window':'original','omx-other-options': '','web-window':'warp','pause-at-end':'yes',
                            'controls':'','live-tracks-dir1':'','live-tracks-dir2':''},
            
                'menu':{'show-ref': '','show-canvas':'', 'title': 'New Menu','type': 'menu','medialist': '',
                        'disable-controls':'no','show-timeout': '0','track-timeout':'0','menu-background-colour':'black','menu-background-image':'',
                        'entry-font': 'Helvetica 30 bold','entry-colour': 'white', 'entry-select-colour': 'red',
                        'hint-text': 'Up, down to Select, Return to Play', 'hint-x':'200','hint-y': '980', 'hint-font': 'Helvetica 30 bold', 'hint-colour': 'white',
                         'menu-text': '', 'menu-text-x':'','menu-text-y': '', 'menu-text-font': '', 'menu-text-colour': '',                       
                         'menu-window':'300 250','menu-direction':'vertical','menu-rows':'10','menu-columns':'1','menu-icon-mode':'bullet','menu-text-mode':'right',
                        'menu-bullet':'/home/pi/pipresents/pp_home/pp_resources/bullet_square_grey.png',
                        'menu-icon-width':'80','menu-icon-height':'80',
                        'menu-horizontal-padding':'10','menu-vertical-padding':'10','menu-text-width':'800','menu-text-height':'50',
                        'menu-horizontal-separation':'20','menu-vertical-separation':'20','menu-strip':'no','menu-strip-padding':'5','menu-guidelines':'never',
                         'eggtimer-x':'','eggtimer-y':'','eggtimer-font':'','eggtimer-colour':'',                       
                        'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                'transition': 'cut',  'duration': '5','image-window':'original','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0', 'mplayer-other-options':'',
                        'omx-audio': 'hdmi','omx-volume':'0','omx-window':'original','omx-other-options': '','web-window':'warp','pause-at-end':'yes',
                        'controls':''},
            
                'start':{'title': 'Start','show-ref':'start', 'type': 'start','start-show':''}  
            }
    
    show_field_specs={
                    'sep':{'shape':'sep'},
                    'audio-speaker':{'param':'audio-speaker','shape':'option-menu','text':'Audio Speaker','must':'no','read-only':'no',
                             'values':['left','right','stereo']},
                    'background-colour':{'param':'background-colour','shape':'colour','text':'Background Colour','must':'no','read-only':'no'},
                    'background-image':{'param':'background-image','shape':'browse','text':'Background Image','must':'no','read-only':'no'},
                    'controls':{'param':'controls','shape':'text','text':'Controls','must':'no','read-only':'no'},
                    'disable-controls':{'param':'disable-controls','shape':'option-menu','text':'Disable Controls ','must':'no','read-only':'no','values':['yes','no']},
                    'duration':{'param':'duration','shape':'entry','text':'Duration (secs)','must':'no','read-only':'no'},
                    'eggtimer-x':{'param':'eggtimer-x','shape':'entry','text':'Egg Timer x Position','must':'no','read-only':'no'},

                    'eggtimer-y':{'param':'eggtimer-y','shape':'entry','text':'Egg Timer y Position','must':'no','read-only':'no'},
                    'eggtimer-font':{'param':'eggtimer-font','shape':'font','text':'Egg Timer Font','must':'no','read-only':'no'},
                    'eggtimer-colour':{'param':'eggtimer-colour','shape':'colour','text':'Egg Timer Colour','must':'no','read-only':'no'},
  
                    'entry-font':{'param':'entry-font','shape':'font','text':'Entry Font','must':'no','read-only':'no'},
                    'entry-colour':{'param':'entry-colour','shape':'colour','text':'Entry Colour','must':'no','read-only':'no'},
                    'entry-select-colour':{'param':'entry-select-colour','shape':'colour','text':'Selected Entry Colour','must':'no','read-only':'no'},
                    'timeout-track-ref':{'param':'timeout-track-ref','shape':'entry','text':'Timeout Track','must':'no','read-only':'no'},
                    'first-track-ref':{'param':'first-track-ref','shape':'entry','text':'First Track','must':'no','read-only':'no'},
                    'has-child':{'param':'has-child','shape':'option-menu','text':'Has Child','must':'no','read-only':'no',
                                        'values':['yes','no']},
                    'has-background':{'param':'has-background','shape':'option-menu','text':'Has Background Image','must':'no','read-only':'no','values':['yes','no']},
                    'hint-text':{'param':'hint-text','shape':'text','text':'Hint Text','must':'no','read-only':'no'},
                    'hint-x':{'param':'hint-x','shape':'entry','text':'Hint Text x Position','must':'no','read-only':'no'},

                    'hint-y':{'param':'hint-y','shape':'entry','text':'Hint Text y Position','must':'no','read-only':'no'},
                    'hint-font':{'param':'hint-font','shape':'font','text':'Hint Font','must':'no','read-only':'no'},
                    'hint-colour':{'param':'hint-colour','shape':'colour','text':'Hint Colour','must':'no','read-only':'no'},
                    'home-track-ref':{'param':'home-track-ref','shape':'entry','text':'Home Track','must':'no','read-only':'no'},
                    'image-window':{'param':'image-window','shape':'entry','text':'Image Window','must':'no','read-only':'no'},
                    'links':{'param':'links','shape':'text','text':'Links','must':'no','read-only':'no'},
                    'live-tracks-dir1':{'param':'live-tracks-dir1','shape':'entry','text':'Live Tracks Directory 1 (not used)','must':'no','read-only':'no'},
                    'live-tracks-dir2':{'param':'live-tracks-dir2','shape':'entry','text':'Live Tracks Directory 2 (not used)','must':'no','read-only':'no'},
                    'medialist':{'param':'medialist','shape':'entry','text':'Medialist','must':'no','read-only':'no'},
                    'message-font':{'param':'message-font','shape':'font','text':'Text Font','must':'yes','read-only':'no'},
                    'menu-background-colour':{'param':'menu-background-colour','shape':'colour','text':'Menu Background Colour','must':'no','read-only':'no'},
                    'menu-background-image':{'param':'menu-background-image','shape':'browse','text':'Menu Background Image','must':'no','read-only':'no'},
                    'menu-text':{'param':'menu-text','shape':'text','text':'Menu Text','must':'no','read-only':'no'},
                    'menu-text-font':{'param':'menu-text-font','shape':'font','text':'Menu Text Font','must':'no','read-only':'no'},
                    'menu-text-colour':{'param':'menu-text-colour','shape':'colour','text':'Menu Text Colour','must':'no','read-only':'no'},
                    'menu-text-x':{'param':'menu-text-x','shape':'entry','text':'Menu Text x Position','must':'no','read-only':'no'},
                    'menu-text-y':{'param':'menu-text-y','shape':'entry','text':'Menu Text y Position','must':'no','read-only':'no'},


                    'menu-window':{'param':'menu-window','shape':'entry','text':'Menu Window','must':'no','read-only':'no'},
                    'menu-direction':{'param':'menu-direction','shape':'option-menu','text':'Direction','must':'no','read-only':'no',
                                       'values':['horizontal','vertical']},
                    'menu-rows':{'param':'menu-rows','shape':'entry','text':'Rows','must':'no','read-only':'no'},
                    'menu-columns':{'param':'menu-columns','shape':'entry','text':'Columns','must':'no','read-only':'no'},
                    'menu-icon-mode':{'param':'menu-icon-mode','shape':'option-menu','text':'Icon Mode','must':'no','read-only':'no',
                                       'values':['none','thumbnail','bullet']},
                    'menu-text-mode':{'param':'menu-text-mode','shape':'option-menu','text':'Text Mode','must':'no','read-only':'no',
                                       'values':['none','overlay','right','below']},
                    'menu-strip':{'param':'menu-strip','shape':'option-menu','text':'Stipple Background','must':'no','read-only':'no',
                                       'values':['no','yes']},
                    'menu-strip-padding':{'param':'menu-strip-padding','shape':'entry','text':'Stipple Background Padding','must':'no','read-only':'no'},

                    'menu-guidelines':{'param':'menu-guidelines','shape':'option-menu','text':'Guidelines','must':'no','read-only':'no',
                                       'values':['never','auto','always']},
                    'menu-bullet':{'param':'menu-bullet','shape':'browse','text':'Bullet','must':'no','read-only':'no'},
                    'menu-icon-width':{'param':'menu-icon-width','shape':'entry','text':'Icon Width','must':'no','read-only':'no'},
                    'menu-icon-height':{'param':'menu-icon-height','shape':'entry','text':'Icon Height','must':'no','read-only':'no'},
                    'menu-horizontal-padding':{'param':'menu-horizontal-padding','shape':'entry','text':'Horizontal Padding','must':'no','read-only':'no'},
                    'menu-vertical-padding':{'param':'menu-vertical-padding','shape':'entry','text':'Vertical Padding','must':'no','read-only':'no'},
                    'menu-horizontal-separation':{'param':'menu-horizontal-separation','shape':'entry','text':'Horizontal Separation','must':'no','read-only':'no'},
                    'menu-vertical-separation':{'param':'menu-vertical-separation','shape':'entry','text':'Vertical Separation','must':'no','read-only':'no'},
                    'menu-text-width':{'param':'menu-text-width','shape':'entry','text':'Text Width','must':'no','read-only':'no'},
                    'menu-text-height':{'param':'menu-text-height','shape':'entry','text':'Text Height','must':'no','read-only':'no'},
                    
                    'message-colour':{'param':'message-colour','shape':'colour','text':'Text Colour','must':'yes','read-only':'no'},
                    'mplayer-audio':{'param':'mplayer-audio','shape':'option-menu','text':'Audio Player Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local']},
                    'mplayer-other-options':{'param':'mplayer-other-options','shape':'entry','text':'Audio Player Options','must':'no','read-only':'no'},
                    'mplayer-volume':{'param':'mplayer-volume','shape':'entry','text':'Audio Volume','must':'no','read-only':'no'},
                    'omx-audio':{'param':'omx-audio','shape':'option-menu','text':'Video Player Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local']},
                    'omx-other-options':{'param':'omx-other-options','shape':'entry','text':'Video Player Options','must':'no','read-only':'no'},
                    'omx-volume':{'param':'omx-volume','shape':'entry','text':'Video Player Volume','must':'no','read-only':'no'},
                    'omx-window':{'param':'omx-window','shape':'entry','text':'Video Window','must':'no','read-only':'no'},
                    'pause-at-end':{'param':'pause-at-end','shape':'option-menu','text':'Pause at End','must':'no','read-only':'no',
                                       'values':['yes','no']},

                    'progress':{'param':'progress','shape':'option-menu','text':'Progress','must':'no','read-only':'no',
                                        'values':['auto','manual']},
                    'repeat':{'param':'repeat','shape':'option-menu','text':'Repeat','must':'no','read-only':'no',
                                        'values':['oneshot','interval','single-run']},
                    'repeat-interval':{'param':'repeat-interval','shape':'entry','text':'Repeat Interval (secs.)','must':'no','read-only':'no'},
                    'sequence':{'param':'sequence','shape':'option-menu','text':'Sequence','must':'no','read-only':'no',
                                        'values':['ordered','shuffle']},
                    'show-canvas':{'param':'show-canvas','shape':'entry','text':'Show Canvas (not used)','must':'no','read-only':'no'},                    
                    'show-ref':{'param':'show-ref','shape':'entry','text':'Show Reference','must':'no','read-only':'no'},
                    'show-text':{'param':'show-text','shape':'text','text':'Show Text','must':'no','read-only':'no'},
                    'show-text-font':{'param':'show-text-font','shape':'font','text':'Show Text Font','must':'no','read-only':'no'},
                    'show-text-colour':{'param':'show-text-colour','shape':'colour','text':'Show Text Colour','must':'no','read-only':'no'},
                    'show-text-x':{'param':'show-text-x','shape':'entry','text':'Show Text x Position','must':'no','read-only':'no'},
                    'show-text-y':{'param':'show-text-y','shape':'entry','text':'Show Text y Position','must':'no','read-only':'no'},
                    'start-show':{'param':'start-show','shape':'entry','text':'Start Shows','must':'no','read-only':'no'},
                    'tab-animation':{'shape':'tab','name':'animation','text':'Animation'},
                    'tab-child':{'shape':'tab','name':'child','text':'Child Show'},
                    'tab-controls':{'shape':'tab','name':'controls','text':'Controls'},
                    'tab-eggtimer':{'shape':'tab','name':'eggtimer','text':'Egg Timer'},
                    'tab-links':{'shape':'tab','name':'links','text':'Links'},
                    'tab-menu-geometry':{'shape':'tab','name':'menu-geometry','text':'Geometry'},
                    'tab-show':{'shape':'tab','name':'show','text':'Show'},
                    'tab-show-text':{'shape':'tab','name':'show-text','text':'Show Text'},
                    'tab-menu-text':{'shape':'tab','name':'menu-text','text':'Menu Text'},
                    'tab-track':{'shape':'tab','name':'track','text':'Track'},
                    'tab-tracks':{'shape':'tab','name':'tracks','text':'Track Defaults'},
                    'text':{'param':'text','shape':'text','text':'Message Text','must':'no','read-only':'no'},
                    'show-timeout':{'param':'show-timeout','shape':'entry','text':'Show Timeout (secs)','must':'no','read-only':'no'},
                    'title':{'param':'title','shape':'entry','text':'Title','must':'no','read-only':'no'},
                    'track-timeout':{'param':'track-timeout','shape':'entry','text':'Track Timeout (secs)','must':'no','read-only':'no'},
                    'transition':{'param':'transition','shape':'option-menu','text':'Transition','must':'no','read-only':'no',
                                 'values':['cut',]},
                    'trigger-start-type':{'param':'trigger-start-type','shape':'option-menu','text':'Trigger for Start','must':'no','read-only':'no',
                                 'values':['start','input','input-quiet','time','time-quiet']},
                    'trigger-end-type':{'param':'trigger-end-type','shape':'option-menu','text':'Trigger for End','must':'no','read-only':'no','values':['none','time','duration']},
                    'trigger-next-type':{'param':'trigger-next','shape':'option-menu','text':'Trigger for next','must':'no','read-only':'no','values':['continue','input']},
                    'trigger-next-param':{'param':'trigger-next-param','shape':'entry','text':'Next Trigger Parameters','must':'no','read-only':'no'},
                    'trigger-start-param':{'param':'trigger-start-param','shape':'entry','text':'Start Trigger Parameters','must':'no','read-only':'no'},
                    'trigger-end-param':{'param':'trigger-end-param','shape':'entry','text':'End Trigger Parameters','must':'no','read-only':'no'},
                    'type':{'param':'type','shape':'entry','text':'Type','must':'no','read-only':'yes'},
                    'web-window':{'param':'web-window','shape':'entry','text':'Browser Window','must':'no','read-only':'no'},
                          }

    track_types={
        'video':[
            'tab-track','sep',  
                    'type','title','track-ref','location','thumbnail','duration','pause-at-end','omx-audio','omx-volume','omx-window','omx-other-options',
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
                'type','title','track-ref','location','thumbnail','duration','transition','image-window','background-colour','background-image','display-show-background','plugin',
            'tab-track-text','sep',
                'track-text','track-text-font','track-text-colour','track-text-x','track-text-y','display-show-text',
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
                       'clear-screen','background-colour','background-image','display-show-background','plugin',
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
                 ],

 
        'menu-background':[
            'tab-track','sep',  
                'type','title','track-ref','location'
            ]
                         }                   

    new_tracks={
        
                'video':{'title':'New Video','track-ref':'','type':'video','location':'','thumbnail':'','duration':'0','pause-at-end':'yes','seamless-loop':'no','omx-audio':'','omx-volume':'','omx-window':'','omx-other-options': '','background-colour':'','background-image':'','display-show-background':'yes','display-show-text':'yes','track-text':'','track-text-font':'',
                       'track-text-colour':'','track-text-x':'0','track-text-y':'0','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':'','plugin':''},
                       
                'message':{'title':'New Message','track-ref':'','type':'message','text':'','thumbnail':'','duration':'','message-font':'Helvetica 30 bold','message-colour':'white','message-justify':'left','message-x':'','message-y':'',
                           'track-text':'','track-text-font':'','track-text-colour':'','track-text-x':'0','track-text-y':'0',
                           'background-colour':'','background-image':'','display-show-background':'yes','display-show-text':'no','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':'','plugin':''},
                
                'show':{'title':'New Show','track-ref':'','type':'show','sub-show':'','thumbnail':''},   
                
                'image':{'title':'New Image','track-ref':'','type':'image','location':'','thumbnail':'','duration':'','transition':'','image-window':'','background-colour':'','background-image':'','display-show-background':'yes','display-show-text':'yes','track-text':'','track-text-font':'',
                       'track-text-colour':'','track-text-x':'0','track-text-y':'0','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':'','plugin':''},
                       
                'audio':{'title':'New Audio','track-ref':'','type':'audio','location':'', 'thumbnail':'','duration':'','audio-speaker':'','mplayer-audio':'','mplayer-volume':'','display-show-text':'yes',
                          'mplayer-other-options':'','clear-screen':'no','background-colour':'','background-image':'','display-show-background':'yes','track-text':'','track-text-font':'','track-text-colour':'','track-text-x':'0','track-text-y':'0','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':'','plugin':''},

                'web':{'title':'New Web','track-ref':'','type':'web','location':'', 'thumbnail':'','duration':'','web-window':'','display-show-text':'yes',
                          'background-colour':'','background-image':'','display-show-background':'yes','track-text':'','track-text-font':'','track-text-colour':'','track-text-x':'0','track-text-y':'0','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':'','browser-commands':'','plugin':''},

                          
                'menu-background':{'title':'New Menu Background','track-ref':'pp-menu-background','type':'menu-background','location':''},
                
                'child-show': {'title':'New Child Show','track-ref':'pp-child-show','type':'show','sub-show':'','thumbnail':''}
                         }


    
    track_field_specs={'sep':{'shape':'sep'},
                            'animate-begin':{'param':'animate-begin','shape':'text','text':'Animation at Beginning','must':'no','read-only':'no'},
                            'animate-end':{'param':'animate-end','shape':'text','text':'Animation at End','must':'no','read-only':'no'},
                            'animate-clear':{'param':'animate-clear','shape':'option-menu','text':'Clear Animation','must':'no','read-only':'no',
                                      'values':['yes','no']},
                            'audio-speaker':{'param':'audio-speaker','shape':'option-menu','text':'Audio Speaker','must':'no','read-only':'no',
                                       'values':['left','right','stereo','']},
                            'background-image':{'param':'background-image','shape':'browse','text':'Background Image','must':'no','read-only':'no'},
                            'background-colour':{'param':'background-colour','shape':'colour','text':'Background Colour','must':'no','read-only':'no'},
                            'browser-commands':{'param':'browser-commands','shape':'text','text':'Browser Commands','must':'no','read-only':'no'},
                            'clear-screen':{'param':'clear-screen','shape':'option-menu','text':'Clear Screen','must':'no','read-only':'no',
                                       'values':['yes','no']},
                            'display-show-background':{'param':'display-show-background','shape':'option-menu','text':'Display Show Background Image','must':'no','read-only':'no',
                                       'values':['yes','no','']},
                            'display-show-text':{'param':'display-show-text','shape':'option-menu','text':'Display Show Text','must':'no','read-only':'no',
                                       'values':['yes','no','']},
                            'duration':{'param':'duration','shape':'entry','text':'Duration (secs)','must':'no','read-only':'no'},
                            'image-window':{'param':'image-window','shape':'entry','text':'Image Window','must':'no','read-only':'no'},
                            'location':{'param':'location','shape':'browse','text':'Location','must':'no','read-only':'no'},
                            'links':{'param':'links','shape':'text','text':'Links','must':'no','read-only':'no'},
                            'message-font':{'param':'message-font','shape':'font','text':'Text Font','must':'no','read-only':'no'},
                            'message-colour':{'param':'message-colour','shape':'colour','text':'Text Colour','must':'no','read-only':'no'},
                            'message-justify':{'param':'message-justify','shape':'option-menu','text':'Justification','must':'no','read-only':'no',
                                       'values':['left','center','right']},
                            'message-x':{'param':'message-x','shape':'entry','text':'Message x Position','must':'no','read-only':'no'},
                            'message-y':{'param':'message-y','shape':'entry','text':'Message y Position','must':'no','read-only':'no'},
                            'mplayer-audio':{'param':'mplayer-audio','shape':'option-menu','text':'Audio Player Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local','']},
                            'mplayer-other-options':{'param':'mplayer-other-options','shape':'entry','text':'Audio Player Options','must':'no','read-only':'no'},
                            'mplayer-volume':{'param':'mplayer-volume','shape':'entry','text':'Audio Player Volume','must':'no','read-only':'no'},
                            'omx-audio':{'param':'omx-audio','shape':'option-menu','text':'Video Player Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local','']},
                            'omx-other-options':{'param':'omx-other-options','shape':'entry','text':'Video Player Options','must':'no','read-only':'no'},
                            'omx-volume':{'param':'omx-volume','shape':'entry','text':'Video Player Volume','must':'no','read-only':'no'},
                            'omx-window':{'param':'omx-window','shape':'entry','text':'Video Window','must':'no','read-only':'no'},
                            'plugin':{'param':'plugin','shape':'browse','text':'Plugin Config File','must':'no','read-only':'no'},
                              'pause-at-end':{'param':'pause-at-end','shape':'option-menu','text':'Pause at End','must':'no','read-only':'no',
                                       'values':['yes','no']},
                            'seamless-loop':{'param':'seamless-loop','shape':'option-menu','text':'Seamless Loop','must':'no','read-only':'no',
                                       'values':['yes','no']},
                            'show-ref':{'param':'show-ref','shape':'entry','text':'Show Reference','must':'no','read-only':'no'},
                            'show-control-begin':{'param':'show-control-begin','shape':'text','text':'Show Control at Beginning','must':'no','read-only':'no'},
                            'show-control-end':{'param':'show-control-end','shape':'text','text':'Show Control at End','must':'no','read-only':'no'},
                            'sub-show':{'param':'sub-show','shape':'option-menu','text':'Show to Run','must':'no','read-only':'no'},

                            'tab-animate':{'shape':'tab','name':'animate','text':'Animation'},
                            'tab-browser-commands':{'shape':'tab','name':'browser-commands','text':'Browser Commands'},
                            'tab-show-control':{'shape':'tab','name':'show-control','text':'Show Control'},
                            'tab-links':{'shape':'tab','name':'links','text':'Links'},
                            'tab-track-text':{'shape':'tab','name':'track-text','text':'Text'},
                            'tab-track':{'shape':'tab','name':'track','text':'Track'},
                            'text':{'param':'text','shape':'text','text':'Message Text','must':'no','read-only':'no'},
                            'thumbnail':{'param':'thumbnail','shape':'browse','text':'Thumbnail','must':'no','read-only':'no'},
                            'title':{'param':'title','shape':'entry','text':'Title','must':'no','read-only':'no'},
                            'track-ref':{'param':'track-ref','shape':'entry','text':'Track Reference','must':'no','read-only':'no'},
                            'track-text':{'param':'track-text','shape':'text','text':'Track Text','must':'no','read-only':'no'},
                            'track-text-font':{'param':'track-text-font','shape':'font','text':'Track Text Font','must':'no','read-only':'no'},
                            'track-text-colour':{'param':'track-text-colour','shape':'colour','text':'Track Text Colour','must':'no','read-only':'no'},
                            'track-text-x':{'param':'track-text-x','shape':'entry','text':'Track Text x Position','must':'no','read-only':'no'},
                            'track-text-y':{'param':'track-text-y','shape':'entry','text':'Track Text y Position','must':'no','read-only':'no'},
                            'transition':{'param':'transition','shape':'option-menu','text':'Transition','must':'no','read-only':'no','values':['cut','']},
                            'type':{'param':'type','shape':'entry','text':'Type','must':'no','read-only':'yes'},
                            'web-window':{'param':'web-window','shape':'entry','text':'Browser Window','must':'no','read-only':'no'},
                          }
        
