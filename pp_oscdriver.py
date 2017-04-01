
"""
30/12/2016 - fixed missing self.mon.err(

Heavily modified from the examples here, with thanks:
receiving OSC with pyOSC
https://trac.v2.nl/wiki/pyOSC
example by www.ixi-audio.net based on pyOSC documentation
this is a very basic example, for detailed info on pyOSC functionality check the OSC.py file 
or run pydoc pyOSC.py. you can also get the docs by opening a python shell and doing
>>> import OSC
>>> help(OSC)
"""
import os
from pp_utils import Monitor
from pp_oscconfig import OSCConfig
import threading
import ConfigParser

import OSC
class myOSCServer(OSC.OSCServer):
    allow_reuse_address=True
    print_tracebacks = True
                 
class OSCDriver(object):

    # executed by main program
    def  init(self,pp_profile,show_command_callback,input_event_callback,output_event_callback):

        self.pp_profile=pp_profile
        self.show_command_callback=show_command_callback
        self.input_event_callback=input_event_callback
        self.output_event_callback=output_event_callback

        self.mon=Monitor()
        config_file=self.pp_profile + os.sep +'pp_io_config'+os.sep+ 'osc.cfg'
        if not os.path.exists(config_file):
            self.mon.err(self, 'OSC Configuration file not found: '+config_file)
            return'error','OSC Configuration file nof found: '+config_file
        
        self.mon.log(self, 'OSC Configuration file found at: '+config_file)        
        self.options=OSCConfig()
        # only reads the  data for required unit_type 
        if self.options.read(config_file) ==False:
            return 'error','failed to read osc.cfg'

        self.prefix='/pipresents'
        self.this_unit='/' + self.options.this_unit_name
        self.this_unit_type = self.options.this_unit_type

        self.reply_client=None
        self.command_client=None
        self.client=None
        self.server=None

        if self.this_unit_type not in ('master','slave','master+slave'):
            return 'error','OSC config, this unit type not known: '+self.this_unit_type

        if self.this_unit_type in('slave','master+slave'):
            #start the client that sends replies to controlling unit
            self.reply_client=OSC.OSCClient()
            self.mon.log(self, 'sending replies to controller at: '+self.options.controlled_by_ip+':'+self.options.controlled_by_port)
            self.reply_client.connect((self.options.controlled_by_ip,int(self.options.controlled_by_port)))
            self.mon.log(self,'sending repiles to: '+ str(self.reply_client))
            self.client=self.reply_client
            
        if self.this_unit_type in ('master','master+slave'):
            #start the client that sends commands to the controlled unit
            self.command_client=OSC.OSCClient()
            self.command_client.connect((self.options.controlled_unit_1_ip,int(self.options.controlled_unit_1_port)))
            self.mon.log(self, 'sending commands to controled unit at: '+self.options.controlled_unit_1_ip+':'+self.options.controlled_unit_1_port)
            self.mon.log(self,'sending commands to: '+str(self.command_client))
            self.client=self.command_client

        #start the listener's server
        self.mon.log(self, 'listen to commands from controlled by unit and replies from controlled units on: ' + self.options.this_unit_ip+':'+self.options.this_unit_port)
        self.server=myOSCServer((self.options.this_unit_ip,int(self.options.this_unit_port)),self.client)
        # return_port=int(self.options.controlled_by_port)
        self.mon.log(self,'listening on: '+str(self.server))
        self.add_initial_handlers()
        return 'normal','osc.cfg read'

    def terminate(self):
        if self.server != None:
            self.server.close()
        self.mon.log(self, 'Waiting for Server-thread to finish')
        if self.st != None:
            self.st.join() ##!!!
        self.mon.log(self,'server thread closed')
        self.client.close()



    def start_server(self):
        # Start OSCServer
        self.mon.log(self,'Starting OSCServer')
        self.st = threading.Thread( target = self.server.serve_forever )
        self.st.start()


    def add_initial_handlers(self):
        self.server.addMsgHandler('default', self.no_match_handler)        
        self.server.addMsgHandler(self.prefix+self.this_unit+"/system/server-info", self.server_info_handler)
        self.server.addMsgHandler(self.prefix+self.this_unit+"/system/loopback", self.loopback_handler)
        self.server.addMsgHandler(self.prefix+ self.this_unit+'/core/open', self.open_show_handler)
        self.server.addMsgHandler(self.prefix+ self.this_unit+'/core/close', self.close_show_handler)
        self.server.addMsgHandler(self.prefix+ self.this_unit+'/core/exitpipresents', self.exitpipresents_handler)
        self.server.addMsgHandler(self.prefix+ self.this_unit+'/core/shutdownnow', self.shutdownnow_handler)
        self.server.addMsgHandler(self.prefix+ self.this_unit+'/core/event', self.input_event_handler)
        self.server.addMsgHandler(self.prefix+ self.this_unit+'/core/output', self.output_event_handler)


    def no_match_handler(self,addr, tags, stuff, source):
        self.mon.warn(self,"no match for osc msg with addr : %s" % addr)
        return None


    def server_info_handler(self,addr, tags, stuff, source):
        msg = OSC.OSCMessage(self.prefix+'/'+self.options.controlled_by_name+'/system/server-info-reply')
        msg.append('Unit: '+ self.options.this_unit_name)
        return msg


    def loopback_handler(self,addr, tags, stuff, source):
         # send a reply to the client.
        msg = OSC.OSCMessage(self.prefix+'/'+self.options.controlled_by_name+'/system/loopback-reply')
        return msg

    
    def open_show_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('open ',args,1)
        
    def close_show_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('close ', args,1)

    def exitpipresents_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('exitpipresents',args,0)

    def shutdownnow_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('shutdownnow',args,0)

    def prepare_show_command_callback(self,command,args,limit):
        if len(args) == limit:
            if limit !=0:
                self.mon.sched(self,'Received from OSC: '+ command + ' ' +args[0])
                self.show_command_callback(command+args[0])
            else:
                self.mon.sched(self,'Received from OSC: '+ command)
                self.show_command_callback(command)                
        else:
            self.mon.warn(self,'OSC show command does not have '+limit +' argument - ignoring')  

    def input_event_handler(self,address, tags, args, source):
        if len(args) == 1:
            self.input_event_callback(args[0],'OSC')
        else:
            self.mon.warn(self,'OSC input event does not have 1 argument - ignoring')    


    def output_event_handler(self,address, tags, args, source):
        if len(args) !=0:
            # delay symbol,param_type,param_values,req_time as a string
            text='0 '
            for arg in args:
                text= text+ arg + ' '
            text = text + '0'
            self.output_event_callback(text)
        else:
            self.mon.warn(self,'OSC output event has no arguments - ignoring')      


    #send messages to controlled units
    # parses the message string into fields and sends - NO error checking
    def send_command(self,text):
        self.mon.log(self,'send OSC Command: ' + text )
        if self.this_unit_type not in ('master','remote','master+slave'):
            self.mon.warn(self,'Unit is not an OSC Master, ignoring command')
            return
        fields=text.split()
        address = fields[0]
        # print 'ADDRESS'+address
        address_fields=address[1:].split('/')
        if address_fields[0] != 'pipresents':
            self.mon.warn(self,'prefix is not pipresents: '+address_fields[0])
        if address_fields[1] != self.options.controlled_unit_1_name:
             self.mon.warn(self,'not sending OSC to the controlled unit: ' +self.options.controlled_unit_1_name + ' is '+ address_fields[1])
        arg_list=fields[1:]
        self.send(address,arg_list)


    def send(self,address,arg_list):
        # print self.command_client
        msg = OSC.OSCMessage()
        # print address
        msg.setAddress(address)
        for arg in arg_list:
            # print arg
            msg.append(arg)
        self.command_client.send(msg)    




class Options(object):

    def __init__(self,app_dir):
        self.options_file = app_dir+os.sep+'pp_osc.cfg'
    
    
    def read(self):
        if os.path.exists(self.options_file):
            config=ConfigParser.ConfigParser()
            config.read(self.options_file)
            
            # this unit
            self.this_unit_type = config.get('this-unit','type',0)
            self.this_unit_name = config.get('this-unit','name',0)
            self.this_unit_ip=config.get('this-unit','ip',0)
            self.this_unit_port =  config.get('this-unit','port',0)  #listen on this port for messages and for replies from controlled units
            #used to send replies to the controlled unit
            self.controlled_by_ip =  config.get('this-unit','controlled-by-ip',0)
            self.controlled_by_port= config.get('this-unit','controlled-by-port',0)
            self.controlled_by_name=config.get('this-unit','controlled-by-name',0)
            controlled_units=config.get('this-unit','controlled-units',0)
            # controller1
            self.controlled_unit_1_ip = config.get('controlled-unit-1','controlled-unit-ip',0)
            self.controlled_unit_1_port = config.get('controlled-unit-1','controlled-unit-port',0)
            self.controlled_unit_1_name = config.get('controlled-unit-1','controlled-unit-name',0)
            return True
        else:
            return False
        



if __name__ == '__main__':

    def pretty_list(fields):
        text=' '
        for field in fields:
            text += str(field) + ' '
        return text

    def show_command_callback(text):
        pass
        # print 'show control command: '+text

    def input_event_callback(text):
        pass
        # print 'input event: '+ text
        
    def output_event_callback(args):
        pass
        # print 'animate: ' + pretty_list(args)


    od = OSCDriver('/home/pi/pipresents',show_command_callback,input_event_callback,output_event_callback)
