
"""
added source name to loopback and info request


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
from pp_timeofday import TimeOfDay

import threading
import ConfigParser
import OSC_plus as OSC
import socket

class myOSCServer(OSC.OSCServer):
    allow_reuse_address=True
    print_tracebacks = True
                 
class OSCDriver(object):

    # executed by main program
    def  init(self,pp_profile,manager_unit,preferred_interface,my_ip,show_command_callback,input_event_callback,animate_callback):

        self.pp_profile=pp_profile
        self.show_command_callback=show_command_callback
        self.input_event_callback=input_event_callback
        self.animate_callback=animate_callback

        self.mon=Monitor()
        config_file=self.pp_profile + os.sep +'pp_io_config'+os.sep+ 'osc.cfg'
        if not os.path.exists(config_file):
            self.mon.err(self, 'OSC Configuration file not found: '+config_file)
            return'error','OSC Configuration file nof found: '+config_file
        
        self.mon.log(self, 'OSC Configuration file found at: '+config_file)        
        self.osc_config=OSCConfig()
        
        # reads config data 
        if self.osc_config.read(config_file) ==False:
            return 'error','failed to read osc.cfg'

        # unpack config data and initialise

        if self.osc_config.this_unit_name =='':
            return 'error','OSC Config -  This Unit has no name'
        if len(self.osc_config.this_unit_name.split())>1:
            return 'error','OSC config - This Unit Name not a single word: '+self.osc_config.this_unit_name
        self.this_unit_name=self.osc_config.this_unit_name
               
                 
        if self.osc_config.this_unit_ip=='':
            self.this_unit_ip=my_ip
        else:
            self.this_unit_ip=self.osc_config.this_unit_ip

        if self.osc_config.slave_enabled == 'yes':
            if not self.osc_config.listen_port.isdigit():
                return 'error','OSC Config - Listen port is not a positve number: '+ self.osc_config.listen_port
            self.listen_port= self.osc_config.listen_port

        if self.osc_config.master_enabled == 'yes':
            if not self.osc_config.reply_listen_port.isdigit():
                return 'error','OSC Config - Reply Listen port is not a positve number: '+ self.osc_config.reply_listen_port
            self.reply_listen_port= self.osc_config.reply_listen_port

            # prepare the list of slaves
            status,message=self.parse_slaves()
            if status=='error':
                return status,message
             

        self.prefix='/pipresents'
        self.this_unit='/' + self.this_unit_name
        
        self.input_server=None
        self.input_reply_client=None
        self.input_st=None
        
        self.output_client=None
        self.output_reply_server=None
        self.output_reply_st=None


        if self.osc_config.slave_enabled == 'yes' and self.osc_config.master_enabled == 'yes' and self.listen_port == self.reply_listen_port:
            # The two listen ports are the same so use one server for input and output

            #start the client that sends commands to the slaves
            self.output_client=OSC.OSCClient()
            self.mon.log(self, 'sending commands to slaves and replies to master on: '+self.reply_listen_port)

            #start the input+output reply server
            self.mon.log(self, 'listen to commands and replies from slave units using: ' + self.this_unit_ip+':'+self.reply_listen_port)
            self.output_reply_server=myOSCServer((self.this_unit_ip,int(self.reply_listen_port)),self.output_client)
            self.add_default_handler(self.output_reply_server)
            self.add_input_handlers(self.output_reply_server)
            self.add_output_reply_handlers(self.output_reply_server)

            self.input_server=self.output_reply_server
            
        else:

            if self.osc_config.slave_enabled == 'yes':
                # we want this to be a slave to something else

                # start the client that sends replies to controlling unit
                self.input_reply_client=OSC.OSCClient()
                
                #start the input server
                self.mon.log(self, 'listening to commands on: ' + self.this_unit_ip+':'+self.listen_port)
                self.input_server=myOSCServer((self.this_unit_ip,int(self.listen_port)),self.input_reply_client)
                self.add_default_handler(self.input_server)
                self.add_input_handlers(self.input_server)
                print self.pretty_list(self.input_server.getOSCAddressSpace(),'\n')
                
            if self.osc_config.master_enabled =='yes':
                #we want to control other units
               
                #start the client that sends commands to the slaves
                self.output_client=OSC.OSCClient()
                self.mon.log(self, 'sending commands to slaves on port: '+self.reply_listen_port)

                #start the output reply server
                self.mon.log(self, 'listen to replies from slave units using: ' + self.this_unit_ip+':'+self.reply_listen_port)
                self.output_reply_server=myOSCServer((self.this_unit_ip,int(self.reply_listen_port)),self.output_client)
                self.add_default_handler(self.output_reply_server)
                self.add_output_reply_handlers(self.output_reply_server)
        
        return 'normal','osc.cfg read'


    def terminate(self):
        if self.input_server != None:
            self.input_server.close()
        if self.output_reply_server != None:
            self.output_reply_server.close()
        self.mon.log(self, 'Waiting for Server threads to finish')
        if self.input_st != None:
            self.input_st.join() ##!!!
        if self.output_reply_st != None:
            self.output_reply_st.join() ##!!!
        self.mon.log(self,'server threads closed')
        if self.input_reply_client !=None:
            self.input_reply_client.close()
        if self.output_client !=None:
            self.output_client.close()


    def start_server(self):
        # Start input Server
        self.mon.log(self,'Starting input OSCServer')
        if self.input_server != None:
            self.input_st = threading.Thread( target = self.input_server.serve_forever )
            self.input_st.start()

        # Start output_reply server
        self.mon.log(self,'Starting output reply OSCServer')
        if self.output_reply_server != None:
            self.output_reply_st = threading.Thread( target = self.output_reply_server.serve_forever )
            self.output_reply_st.start()

    def parse_slaves(self):
        name_list=self.osc_config.slave_units_name.split()
        ip_list=self.osc_config.slave_units_ip.split()
        if len(name_list)==0:
            return 'error','OSC Config - List of slaves name is empty'
        if len(name_list) != len(ip_list):
            return 'error','OSC Config - Lengths of list of slaves name and slaves IP is different'       
        self.slave_name_list=[]
        self.slave_ip_list=[]
        for i, name in enumerate(name_list):
            self.slave_name_list.append(name)
            self.slave_ip_list.append(ip_list[i])
        return 'normal','slaves parsed'


    def parse_osc_command(self,fields):
    # send message to slave unit - INTERFACE WITH pipresents
        if len(fields) <2:
               return 'error','too few fields in OSC command '+' '.join(fields)
        to_unit_name=fields[0]
        show_command=fields[1]
        # print 'FIELDS ',fields
        
        # send an arbitary osc message            
        if show_command == 'send':
            if len(fields)>2:
                osc_address= fields[2]
                arg_list=[]
                if len(fields)>3:
                    arg_list=fields[3:]
            else:
                return 'error','OSC - wrong nmber of fields in '+ ' '.join(fields)

        elif show_command in ('open','close','openexclusive'):
            if len(fields)==3:
                osc_address=self.prefix+'/'+ to_unit_name + '/core/'+ show_command
                arg_list= [fields[2]]
            else:
                return 'error','OSC - wrong number of fields in '+ ' '.join(fields)
                
        elif show_command =='monitor':
            if fields[2] in ('on','off'):
                osc_address=self.prefix+'/'+ to_unit_name + '/core/'+ show_command
                arg_list=[fields[2]]
            else:
                self.mon.err(self,'OSC - illegal state in '+ show_command + ' '+fields[2])
        
        elif show_command =='event':                
            if len(fields)==3:
                osc_address=self.prefix+'/'+ to_unit_name + '/core/'+ show_command
                arg_list= [fields[2]]


        elif show_command == 'animate':                
            if len(fields)>2:
                osc_address=self.prefix+'/'+ to_unit_name + '/core/'+ show_command
                arg_list= fields[2:]
            else:
                return 'error','OSC - wrong nmber of fields in '+ ' '.join(fields)
            
        elif show_command in ('closeall','exitpipresents','shutdownnow','reboot'):
            if len(fields)==2:
                osc_address=self.prefix+'/'+ to_unit_name + '/core/'+ show_command
                arg_list= []
            else:
                return 'error','OSC - wrong nmber of fields in '+ ' '.join(fields)

        elif show_command in ('loopback','server-info'):
            if len(fields)==2:
                osc_address=self.prefix+'/'+ to_unit_name + '/system/'+ show_command
                arg_list= []
            else:
                return 'error','OSC - wrong nmber of fields in '+ ' '.join(fields)
            
        else:
            return 'error','OSC - unkown command in '+ ' '.join(fields)

        
        ip=self.find_ip(to_unit_name,self.slave_name_list,self.slave_ip_list)
        if ip=='':
            return 'warn','OSC Unit Name not in the list of slaves: '+ to_unit_name
        self.sendto(ip,osc_address,arg_list)
        return 'normal','osc command sent'


    def find_ip(self,name,name_list,ip_list):
        i=0
        for j in name_list:
            if j == name:
                break
            i=i+1
            
        if i==len(name_list):
            return ''
        else:
            return ip_list[i]
                    

    def sendto(self,ip,osc_address,arg_list):
        # print ip,osc_address,arg_list
        if self.output_client is None:
            self.mon.warn(self,'Master not enabled, ignoring OSC command')
            return
        msg = OSC.OSCMessage()
        # print address
        msg.setAddress(osc_address)
        for arg in arg_list:
            # print arg
            msg.append(arg)
            
        try:
            self.output_client.sendto(msg,(ip,int(self.reply_listen_port)))
            self.mon.log(self,'Sent OSC command: '+osc_address+' '+' '.join(arg_list) + ' to '+ ip +':'+self.reply_listen_port)
        except Exception as e:
            self.mon.warn(self,'error in client when sending OSC command: '+ str(e))


# **************************************
# Handlers for fallback
# **************************************

    def add_default_handler(self,server):
        server.addMsgHandler('default', self.no_match_handler)

    def no_match_handler(self,addr, tags, stuff, source):
        text= "No handler for message from %s" % OSC.getUrlStr(source)+'\n'
        text+= "     %s" % addr+ self.pretty_list(stuff,'')
        self.mon.warn(self,text)
        return None

# **************************************
# Handlers for Slave (input)
# **************************************    

    def add_input_handlers(self,server):
        server.addMsgHandler(self.prefix + self.this_unit+"/system/server-info", self.server_info_handler)
        server.addMsgHandler(self.prefix + self.this_unit+"/system/loopback", self.loopback_handler)
        server.addMsgHandler(self.prefix+ self.this_unit+'/core/open', self.open_show_handler)
        server.addMsgHandler(self.prefix+ self.this_unit+'/core/close', self.close_show_handler)
        server.addMsgHandler(self.prefix+ self.this_unit+'/core/openexclusive', self.openexclusive_handler)
        server.addMsgHandler(self.prefix+ self.this_unit+'/core/closeall', self.closeall_handler)
        server.addMsgHandler(self.prefix+ self.this_unit+'/core/exitpipresents', self.exitpipresents_handler)
        server.addMsgHandler(self.prefix+ self.this_unit+'/core/shutdownnow', self.shutdownnow_handler)
        server.addMsgHandler(self.prefix+ self.this_unit+'/core/reboot', self.reboot_handler)
        server.addMsgHandler(self.prefix+ self.this_unit+'/core/event', self.input_event_handler)
        server.addMsgHandler(self.prefix+ self.this_unit+'/core/animate', self.animate_handler)
        server.addMsgHandler(self.prefix+ self.this_unit+'/core/monitor', self.monitor_handler)


    # reply to master unit with name of this unit and commands
    def server_info_handler(self,addr, tags, stuff, source):

        msg = OSC.OSCMessage(self.prefix+'/system/server-info-reply')
        msg.append(self.this_unit_name)
        msg.append(self.input_server.getOSCAddressSpace())
        self.mon.log(self,'Sent Server Info reply to %s:' % OSC.getUrlStr(source))
        return msg


    # reply to master unit with a loopback message
    def loopback_handler(self,addr, tags, stuff, source):
        msg = OSC.OSCMessage(self.prefix+'/system/loopback-reply')
        self.mon.log(self,'Sent loopback reply to %s:' % OSC.getUrlStr(source))
        return msg


 
    def open_show_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('open ',args,1)

    def openexclusive_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('openexclusive ',args,1)
        
    def close_show_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('close ', args,1)

    def closeall_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('closeall',args,0)

    def monitor_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('monitor ', args,1)

    def exitpipresents_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('exitpipresents',args,0)

    def reboot_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('reboot',args,0)

    def shutdownnow_handler(self,address, tags, args, source):
        self.prepare_show_command_callback('shutdownnow',args,0)

    def prepare_show_command_callback(self,command,args,limit):
        if len(args) == limit:
            if limit !=0:
                self.mon.sched(self,TimeOfDay.now,'Received from OSC: '+ command + ' ' +args[0])
                self.show_command_callback(command+args[0])
            else:
                self.mon.sched(self,TimeOfDay.now,'Received from OSC: '+ command)
                self.show_command_callback(command)                
        else:
            self.mon.warn(self,'OSC show command does not have '+limit +' argument - ignoring')  

    def input_event_handler(self,address, tags, args, source):
        if len(args) == 1:
            self.input_event_callback(args[0],'OSC')
        else:
            self.mon.warn(self,'OSC input event does not have 1 argument - ignoring')    


    def animate_handler(self,address, tags, args, source):
        if len(args) !=0:
            # delay symbol,param_type,param_values,req_time as a string
            text='0 '
            for arg in args:
                text= text+ arg + ' '
            text = text + '0'
            print text
            self.animate_callback(text)
        else:
            self.mon.warn(self,'OSC output event has no arguments - ignoring')      

# **************************************
# Handlers for Master- replies from slaves (output)
# **************************************

    # reply handlers do not have the destinatuion unit in the address as they are always sent to the originator
    def add_output_reply_handlers(self,server):
        server.addMsgHandler(self.prefix+"/system/server-info-reply", self.server_info_reply_handler)
        server.addMsgHandler(self.prefix+"/system/loopback-reply", self.loopback_reply_handler)
        
        
    # print result of info request from slave unit
    def server_info_reply_handler(self,addr, tags, stuff, source):
        self.mon.log(self,'server info reply from slave '+OSC.getUrlStr(source)+ self.pretty_list(stuff,'\n'))
        print 'Received reply to Server-Info command from slave: ',OSC.getUrlStr(source), self.pretty_list(stuff,'\n')
        return None

    #print result of info request from slave unit
    def loopback_reply_handler(self,addr, tags, stuff, source):
        self.mon.log(self,'server info reply from slave '+OSC.getUrlStr(source)+ self.pretty_list(stuff,'\n'))
        print 'Received reply to Loopback command from slave: ' + OSC.getUrlStr(source)+ ' '+ self.pretty_list(stuff,'\n')
        return None


    def pretty_list(self,fields, separator):
        text=' '
        for field in fields:
            text += str(field) + separator
        return text+'\n'



if __name__ == '__main__':

    def pretty_list(fields):
        text=' '
        for field in fields:
            text += str(field) + ' '
        return text

    def show_command_callback(text):
        pass
        print 'show control command: '+text

    def input_event_callback(text):
        pass
        print 'input event: '+ text
        
    def output_event_callback(args):
        pass
        print 'animate: ' + pretty_list(args)


    od = OSCDriver('/home/pi/pipresents',show_command_callback,input_event_callback,output_event_callback)
