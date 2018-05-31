import time
import copy
import os
import ConfigParser
import ctypes
import pynfc.src.nfc as nfc


class pp_pn532driver(object):

    # CLASS VARIABLES  (pp_pn532driver.)
    driver_active=False
    title=''
    tag_codes=[] #dynamic list constructed from .cfg file and other dynamic variables


    # configuration from PN532.cfg
    TAG_CODE=0
    DIRECTION = 1 # IN/OUT/NONE (OUT is not used)
    REMOVED_NAME=2             # symbolic name for removed callback
    DETECTED_NAME=3      # symbolic name of detected callback
  
    TEMPLATE = ['',       # tag code
                '',              # direction
                '',''      #symbolic names
                        ]

    # executed by main program and by each object using the driver
    def __init__(self):
        pass



    # executed once from main program   
    def init(self,filename,filepath,widget,button_callback=None):
        self.widget=widget
        self.button_callback=button_callback
        self.filename=filename
        self.filepath=filepath

        # read .cfg file.
        reason,message=self._read(self.filename,self.filepath)
        if reason =='error':
            return 'error',message
        if self.config.has_section('DRIVER') is False:
            return 'error','no DRIVER section in '+ self.filename           

        #read information from DRIVER section
        pp_pn532driver.title=self.config.get('DRIVER','title')
        self.threshold=int(self.config.get('DRIVER','threshold'))
        tagcode_text=self.config.get('DRIVER','tag-codes')
        pp_pn532driver.TAGCODELIST = tagcode_text.split(',')
        
        # construct the tag_code control list from the configuration
        for index, tag_code_def in enumerate(pp_pn532driver.TAGCODELIST):
            if self.config.has_section(tag_code_def) is False:
                return 'error',"no tag code definition for "+ tag_code_def         
            else:
                entry=copy.deepcopy(pp_pn532driver.TEMPLATE)
                entry[pp_pn532driver.TAG_CODE]=tag_code_def
                if self.config.get(tag_code_def,'direction') == 'none':
                    # disabled tag
                    entry[pp_pn532driver.DIRECTION]='none'
                else:
                    entry[pp_pn532driver.DIRECTION]=self.config.get(tag_code_def,'direction')
                    if entry[pp_pn532driver.DIRECTION] == 'in':
                        # input ony
                        entry[pp_pn532driver.DETECTED_NAME]=self.config.get(tag_code_def,'detected-name')
                        entry[pp_pn532driver.REMOVED_NAME]=self.config.get(tag_code_def,'removed-name')
 
            # add entry to working list of tag_codes  (list of lists [0] of sublist is key code)      
            pp_pn532driver.tag_codes.append(copy.deepcopy(entry))

        # print pp_pn532driver.tag_codes

        #Start the PN532 tag reader

        self.__context = None
        self.__device = None

        mods = [(nfc.NMT_ISO14443A, nfc.NBR_106)]
        self.__modulations = (nfc.nfc_modulation * len(mods))()
        for i in range(len(mods)):
            self.__modulations[i].nmt = mods[i][0]
            self.__modulations[i].nbr = mods[i][1]
        self.__context = ctypes.pointer(nfc.nfc_context())
        nfc.nfc_init(ctypes.byref(self.__context))

        conn_strings = (nfc.nfc_connstring * 10)()
        devices_found = nfc.nfc_list_devices(self.__context, conn_strings, 10)
        if devices_found < 1:
            return 'error',pp_pn532driver.title + 'PN532 tag reader not found'
        else:
            self.__device = nfc.nfc_open(self.__context, conn_strings[0])
            try:
                _ = nfc.nfc_initiator_init(self.__device)
            except IOError, e:
                return 'error',pp_pn532driver.title + 'Exception initiating tag reader' + str(e)
            
        # init timer
        self.button_tick_timer=None

        pp_pn532driver.driver_active=True
        return 'normal',pp_pn532driver.title + ' active'            
            

    def start(self):
        self.count=1
        self.last_tag_code = ''
        self.debounced_tag_code=''    # empty string is no tag
        self.last_debounced_tag_code=''    # empty string is no tag
        self.last_event_entry=None
        # self.start_time=time.time()
        # print 'start poll'
        self.button_tick_timer=self.widget.after(0,self.poll)


    def poll(self):
        """One iteration of a loop that polls for tags"""
        # print 'poll',"%.2f" % (time.time()-self.start_time)
        status,message,tag_code=self.read_tag()
        # print 'tag read',"%.2f" % (time.time()-self.start_time)
        # get event table entry corresonding to tag code
        if tag_code != '':
            event_entry=self.find_event_entry(tag_code)
            if event_entry is None or event_entry[pp_pn532driver.DIRECTION] != 'in':
                # print 'not found',tag_code
                self.button_tick_timer=self.widget.after(5,self.poll)
                return
        else:
            event_entry=None
        

        # do threshold
        # print self.count,self.threshold,tag_code
        if tag_code == self.last_tag_code:
            self.count+=1
            if self.count > self.threshold:
                self.count=self.threshold
        else:
            self.count=1
        self.last_tag_code = tag_code
        if self.count == self.threshold:
            self.debounced_tag_code = tag_code

        # print 'code: ',self.debounced_tag_code
            
        # generate events on change of tag code
        if self.debounced_tag_code != self.last_debounced_tag_code:
            if self.last_debounced_tag_code !='':
                #remove tag event
                self.button_callback(self.last_event_entry[pp_pn532driver.REMOVED_NAME],pp_pn532driver.title)
            if self.debounced_tag_code != '':
                # detect tag event
                self.button_callback(event_entry[pp_pn532driver.DETECTED_NAME],pp_pn532driver.title)
            self.last_debounced_tag_code = self.debounced_tag_code
            self.last_event_entry=event_entry 
        self.button_tick_timer=self.widget.after(5,self.poll)
        



    def read_tag(self):
        nt = nfc.nfc_target()
        res = nfc.nfc_initiator_poll_target(self.__device, self.__modulations, len(self.__modulations),
                                            1, 1,ctypes.byref(nt)) 
        # print "RES", res
        if res < 0:
            # print 'card absent'
            return 'normal','',''
        elif res >= 1:
            uid_length=nt.nti.nai.szUidLen
            # print 'length ',uid_length
            uid = "".join([chr(nt.nti.nai.abtUid[i]) for i in range(uid_length)])
            uid_hex=uid.encode("hex")
            # print uid_hex
            return 'normal','',uid_hex
        else:
            print 'tag reader error: reader returns zero result'
            return 'error','reader returns zero result',''

    def find_event_entry(self,tag_code):
        for entry in pp_pn532driver.tag_codes:
            if entry[pp_pn532driver.TAG_CODE]==tag_code:
                # print entry
                return entry
        return None
    

    # no inputs to get from this driver
    def get_input(self,channel):
            return False, None

    def is_active(self):
        return pp_pn532driver.driver_active

    def terminate(self):
        if pp_pn532driver.driver_active is True:
            if self.button_tick_timer is not None:
                self.widget.after_cancel(self.button_tick_timer)
                
            nfc.nfc_exit(self.__context)
            nfc.nfc_close(self.__device)
            
            pp_pn532driver.driver_active=False


# ***********************************
# output events
# ************************************

    # execute an output event
    def handle_output_event(self,name,param_type,param_values,req_time):
        return 'normal',pp_pn532driver.title + ' does not accept outputs'
        
    def reset_outputs(self):
        return


# ***********************************
# reading .cfg file
# ************************************

    def _read(self,filename,filepath):
        # try inside profile
        if os.path.exists(filepath):
            self.config = ConfigParser.ConfigParser()
            self.config.read(filepath)
            return 'normal',filename+' read'
        else:
            return 'error',filename + ' not found at: '+filepath


# ***********************************
# Test harness
# ************************************


if __name__ == '__main__':
    from Tkinter import *

    def button_callback(symbol,source):
        print 'callback',symbol,source
        if symbol=='pp-stop':
            pn.terminate()
            exit()


    root = Tk()

    w = Label(root, text="pp_pn532driver.py test harness")
    w.pack()

    pn=pp_pn532driver()
    reason,message=pn.init('pn532.cfg','/home/pi/pipresents/pp_resources/pp_templates/pn532.cfg',root,button_callback)
    print reason,message
    pn.start()
    root.mainloop()

    




