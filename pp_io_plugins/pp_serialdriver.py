#usb serial port driver
import copy
import os
import ConfigParser
import serial

class pp_serialdriver(object):

    # control list items
    NAME=0                # symbolic name for input and output
    DIRECTION = 1         # in/out
    MATCH = 2             # for input the character/string to match (no EOL)
    MODE= 3               # for input the match mode any-char,char,any-line,line
    TYPE=4                # for output string or bytes  or blank
    VALUE=5      # for output the vaue to be used if type is not in the animate command
    MESSAGE_TYPE=6
    MESSAGE=7

    TEMPLATE=['','','','','','','','']

# CLASS VARIABLES  (pp_serialdriver.)
    driver_active=False
    title=''          # usd for error reporting and logging
    tick_interval=''     # mS between polls of the serial input

    match_mode=''     # char or line, whether input characters are matched for each character or a complete line
    eol_char=''
    
    port_name=''      # linux port name
    baud_rate=''
    byte_size_text=''
    parity_bit_text=''
    stop_bit_text=''

    inputs={}

    # executed by main program and by each object using the driver
    def __init__(self):
        pass

     # executed once from main program   
    def init(self,filename,filepath,widget,event_callback=None):
        
        # instantiate arguments
        self.widget=widget
        self.filename=filename
        self.filepath=filepath
        self.event_callback=event_callback

        pp_serialdriver.ser=None
        pp_serialdriver.driver_active = False

        # read pp_serialdriver.cfg file.
        reason,message=self._read(self.filename,self.filepath)
        if reason =='error':
            return 'error',message
        if self.config.has_section('DRIVER') is False:
            return 'error','No DRIVER section in '+self.filepath
        
        # all the below are used by another instance of pp_serialdriver so must reference class variables
        # read information from DRIVER section
        pp_serialdriver.title=self.config.get('DRIVER','title')
        pp_serialdriver.tick_interval = self.config.get('DRIVER','tick-interval')
        pp_serialdriver.port_name = self.config.get('DRIVER','port-name')
        pp_serialdriver.baud_rate = self.config.get('DRIVER','baud-rate')
        pp_serialdriver.byte_size_text = self.config.get('DRIVER','byte-size')
        pp_serialdriver.parity_bit_text = self.config.get('DRIVER','parity-bit')
        pp_serialdriver.stop_bit_text = self.config.get('DRIVER','stop-bits')
        pp_serialdriver.eol_char = self.config.get('DRIVER','eol-char')
        # construct the control list from the config file
        pp_serialdriver.in_names=[]
        pp_serialdriver.out_names=[]
        for section in self.config.sections():
            if section == 'DRIVER':
                continue
            if entry[pp_serialdriver.DIRECTION] == 'none':
                continue
            entry=copy.deepcopy(pp_serialdriver.TEMPLATE)
            entry[pp_serialdriver.NAME]=self.config.get(section,'name')
            entry[pp_serialdriver.DIRECTION]=self.config.get(section,'direction')
            
            if entry[pp_serialdriver.DIRECTION] == 'in':
                entry[pp_serialdriver.MODE]=self.config.get(section,'mode')
                if entry[pp_serialdriver.MODE] in ('specific-character','specific-line'):
                    entry[pp_serialdriver.MATCH]=self.config.get(section,'match')
                pp_serialdriver.in_names.append(copy.deepcopy(entry))

                
            elif entry[pp_serialdriver.DIRECTION] == 'out':
                entry[pp_serialdriver.TYPE]=self.config.get(section,'type')
                entry[pp_serialdriver.VALUE]=self.config.get(section,'value')
                if entry[pp_serialdriver.VALUE] != '':
                    entry[pp_serialdriver.MESSAGE_TYPE]=self.config.get(section,'message-type')
                    entry[pp_serialdriver.MESSAGE]=self.config.get(section,'message')                   
                pp_serialdriver.out_names.append(copy.deepcopy(entry))
                
            else:
                return 'error',pp_serialdriver.title + ' direction not in or out or none'
        # print pp_serialdriver.in_names
        # print pp_serialdriver.out_names


        # open the serial port
        pp_serialdriver.ser = serial.Serial(pp_serialdriver.port_name,pp_serialdriver.baud_rate,timeout=0)

        
        # evaluate and set parity
        if pp_serialdriver.parity_bit_text =="odd":
            pp_serialdriver.ser.parity = serial.PARITY_ODD
        elif pp_serialdriver.parity_bit_text == "even":
            pp_serialdriver.ser.parity = serial.PARITY_EVEN
        elif pp_serialdriver.parity_bit_text == "none":
            pp_serialdriver.ser.parity = serial.PARITY_NONE
        else:
            return 'error',pp_serialdriver.title + ' invalid parity ' + pp_serialdriver.parity_bit_text
        
       # evaluate and set stop bit
        if pp_serialdriver.stop_bit_text.isdigit():
            if int(pp_serialdriver.stop_bit_text) == 0:
                pp_serialdriver.ser.stopbits = serial.STOPBITS_NONE
            elif int(pp_serialdriver.stop_bit_text)== 1:
                pp_serialdriver.ser.stopbits = serial.STOPBITS_ONE  
            elif int(pp_serialdriver.stop_bit_text)== 2:
                pp_serialdriver.ser.stopbits = serial.STOPBITS_TWO
            else:
                return 'error',pp_serialdriver.title + ' invalid stop bits ' + pp_serialdriver.stop_bit_text
        else:
            return 'error',pp_serialdriver.title + ' stop bits is not a positive integer ' + pp_serialdriver.stop_bit_text

            
       # evaluate and set byte size
        if pp_serialdriver.byte_size_text.isdigit():
            if int(pp_serialdriver.byte_size_text) == 5:  
                pp_serialdriver.ser.bytesize=serial.FIVEBITS
            elif int(pp_serialdriver.byte_size_text) == 6:
                pp_serialdriver.ser.bytesize=serial.SIXBITS
            elif int(pp_serialdriver.byte_size_text) == 7:
                pp_serialdriver.ser.bytesize=serial.SEVENBITS
            elif int(pp_serialdriver.byte_size_text) == 8:
                pp_serialdriver.ser.bytesize=serial.EIGHTBITS
            else:
                return 'error',pp_serialdriver.title + ' invalid byte size ' + pp_serialdriver.byte_size_text
        else:
            return 'error',pp_serialdriver.title + ' byte size is not a positive integer ' + pp_serialdriver.byte_size_text
        
        # all ok so indicate the driver is active
        pp_serialdriver.driver_active=True

        # init must return two arguments
        return 'normal',pp_serialdriver.title + ' active'



    # start method must be defined. If not using inputs just pass 
    def start(self):
        self.data=''
        pp_serialdriver.inputs['current-character']=''
        pp_serialdriver.inputs['current-line']=''
        pp_serialdriver.inputs['previous-line']=''
        self.tick_timer=self.widget.after(1,self.tick_loop)
        

    def tick_loop(self):
        # generate the events with symbolic names if driver is active
        if pp_serialdriver.driver_active is True and pp_serialdriver.ser.is_open is True:
            chars = pp_serialdriver.ser.read(9999)
            if len(chars)>0:
                for char in chars:
                    # print 'received ', hex(ord(char)),char

                    # if char is eol then match the line and start a new line
                    if ord(char) == int(pp_serialdriver.eol_char,16):
                        # do match of line
                        # print 'match line',pp_serialdriver.inputs['current-line']
                        self.match_line(pp_serialdriver.inputs['current-line'])
                        # shuffle and empty the buffer
                        pp_serialdriver.inputs['previous-line'] = pp_serialdriver.inputs['current-line']
                        pp_serialdriver.inputs['current-line']=''
                        pp_serialdriver.inputs['current-character']=''
                        
                    else:
                        # do match with character entries
                        # print 'match char',char
                        pp_serialdriver.inputs['current-character']=char
                        pp_serialdriver.inputs['current-line']+=char
                        self.match_char(char)                        

            self.tick_timer=self.widget.after(int(pp_serialdriver.tick_interval),self.tick_loop)


    def match_char(self,char):
        for entry in pp_serialdriver.in_names:
            if entry[pp_serialdriver.MODE] == 'any-character':
                # print 'match any character', char, 'current line is ',pp_serialdriver.inputs['current-line']
                if self.event_callback  is not  None:
                        self.event_callback(entry[pp_serialdriver.NAME],pp_serialdriver.title)
            if entry[pp_serialdriver.MODE] == 'specific-character' and char == entry[pp_serialdriver.MATCH]:
                # print 'match specific character', char
                if self.event_callback  is not  None:
                        self.event_callback(entry[pp_serialdriver.NAME],pp_serialdriver.title)

    def match_line(self,line):
        for entry in pp_serialdriver.in_names:
            if entry[pp_serialdriver.MODE] == 'any-line':
                # print 'match any line',line
                if self.event_callback  is not  None:
                        self.event_callback(entry[pp_serialdriver.NAME],pp_serialdriver.title)

            if entry[pp_serialdriver.MODE] == 'specific-line' and line == entry[pp_serialdriver.MATCH]:
                # print 'match specific line', line
                if self.event_callback  is not  None:
                        self.event_callback(entry[pp_serialdriver.NAME],pp_serialdriver.title)


    # allow track plugins (or anyting else) to access analog input values
    def get_input(self,key):
        if key in pp_serialdriver.inputs:
            return True, pp_serialdriver.inputs[key]
        else:
            return False, None


  # called by main program only. Called when PP is closed down               
    def terminate(self):
        if pp_serialdriver.driver_active is True:
            pp_serialdriver.ser.close()
            pp_serialdriver.ser=None
            if self.tick_timer is not None:
                self.widget.after_cancel(self.tick_timer)
            pp_serialdriver.driver_active = False


# ************************************************
# output interface method
# this can be called from many objects so needs to operate on class variables
# ************************************************                            
    # execute an output event

    def handle_output_event(self,name,param_type,param_values,req_time):

        # print 'comand is',name,param_type, param_values[0]

        #match command against all out entries in config data
        self.result=''
        for entry in pp_serialdriver.out_names:
            # does the symbolic name and type match value in the configuration 
            if name == entry[pp_serialdriver.NAME] and param_type == entry[pp_serialdriver.TYPE]:
                status,message=self.dispatch_command(name,param_type,param_values,entry)
                if status == 'error':
                    return status,message
        return 'normal',self.result


    def dispatch_command(self,name,param_type,param_values,entry):
        # print 'dispatch',name,param_type, param_values[0]
        if entry[pp_serialdriver.VALUE] == '':
            # value is blank in config so send message in command with message type from command
            # print 'no value in config send ',entry[pp_serialdriver.MESSAGE_TYPE],param_values[0]
            if param_type == 'bytes':
                status,message=self.send_bytes(param_values[0])
                return status,message
            else:
                status,message=self.send_string(param_values[0])
                return status,message
        else:
            # if value in command matches config value send message in config
            if param_values[0] == entry[pp_serialdriver.VALUE]:
                # print 'value match send message from config ',entry[pp_serialdriver.MESSAGE_TYPE],entry[pp_serialdriver.MESSAGE]
                if entry[pp_serialdriver.MESSAGE_TYPE]=='bytes':
                    status,message=self.send_bytes(entry[pp_serialdriver.MESSAGE])
                    return status,message
                else:
                    status,message=self.send_string(entry[pp_serialdriver.MESSAGE])
                    return status,message
            # print '  ---- no match for ',entry[pp_serialdriver.VALUE]
            return 'normal','no match'

               
    def send_bytes(self,byte_text):
        # convert byte string to a byte array
        fields=byte_text.split(' ')
        bytes=bytearray()
        for field in fields:
            intfield=int(field,base=16)
            if intfield>255:
                return 'error',pp_serialdriver.title + ' illegal code: ' + field
            else:
                bytes.append(intfield)

        
        if pp_serialdriver.ser.is_open is False:        
            return 'error',pp_serialdriver.title + ' serial port not open: ' + name
        bytes_sent = pp_serialdriver.ser.write(bytes)
        self.result += pp_serialdriver.title + ': sent ' + str(bytes_sent) + ' bytes to ' + pp_serialdriver.ser.name

        # print pp_serialdriver.title + ': sent ' + str(bytes_sent) + ' bytes to ' + pp_serialdriver.ser.name
        # print bytes

        return 'normal',pp_serialdriver.title + 'message sent'

    def send_string(self,text):
        # convert string to a byte array
        bytes=bytearray()
        for char in text:
            intfield=ord(char)
            if intfield>255:
                return 'error',pp_serialdriver.title + ' illegal character: ' + char + ' ' + ord(char)
            else:
                bytes.append(intfield)
        
        if pp_serialdriver.ser.is_open is False:        
            return 'error',pp_serialdriver.title + ' serial port not open: ' + name
        bytes_sent = pp_serialdriver.ser.write(bytes)
        self.result += pp_serialdriver.title + ': sent ' + str(bytes_sent) + ' characters to ' + pp_serialdriver.ser.name

        # print pp_serialdriver.title + ': sent ' + str(bytes_sent) + ' characters to ' + pp_serialdriver.ser.name
        # print bytes
        
        return 'normal',pp_serialdriver.title + 'message sent'


    # allow querying of driver state
    def is_active(self):
        return pp_serialdriver.driver_active

# ***********************************
# reading .cfg file
# ************************************

    def _read(self,filename,filepath):
        if os.path.exists(filepath):
            self.config = ConfigParser.ConfigParser()
            self.config.read(filepath)
            return 'normal',filename+' read'
        else:
            return 'error',filename+' not found at: '+filepath

            
