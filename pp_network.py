import subprocess
import smtplib
from email.mime.text import MIMEText
import ConfigParser
import time
from time import sleep
from pp_utils import Monitor

class Mailer(object):

    config=None

    def __init__(self):
        self.mon=Monitor()

    """ email is enabled if email.cfg exists"""        
    def read_config(self,options_file=None):
        if options_file != None:
            Mailer.options_file=options_file
            Mailer.config=ConfigParser.ConfigParser()
        self.config=Mailer.config
        self.config.read(Mailer.options_file)
        self.server=self.config.get('email','server',0)
        self.port=self.config.get('email','port',0)
        self.username=self.config.get('email','username',0)
        self.password=self.config.get('email','password',0)
        self.email_to=self.config.get('email-editable','to',0)
        self.is_to_list= self.email_to.splitlines()
        self.is_to = ', '.join(self.is_to_list)

        email_allowed=self.config.get('email-editable','email_allowed',0)
        if email_allowed == 'yes':
            self.email_allowed = True
        else:
            self.email_allowed = False

        email_with_ip=self.config.get('email-editable','email_with_ip',0)            
        if email_with_ip == 'yes':
            self.email_with_ip = True
        else:
            self.email_with_ip=False
            
            
        email_on_error=self.config.get('email-editable','email_on_error',0)
        if email_on_error == 'yes':
            self.email_on_error = True
        else:
            self.email_on_error=False
            
        email_on_terminate=self.config.get('email-editable','email_on_terminate',0)
        if email_on_terminate == 'yes':
            self.email_on_terminate = True
        else:
            self.email_on_terminate=False
            
        email_at_start=self.config.get('email-editable','email_at_start',0)
        if email_at_start == 'yes':
            self.email_at_start = True
        else:
            self.email_at_start=False
            
        attach_log=self.config.get('email-editable','log_on_error',0)
        if attach_log == 'yes':
            self.log_on_error = True
        else:
            self.log_on_error=False


    def save_config(self):
        self.config.set('email-editable','email_allowed','yes' if self.email_allowed is True else'no')
        self.config.set('email-editable','to',self.email_to)
        self.config.set('email-editable','email_with_ip','yes' if self.email_with_ip is True else'no')
        self.config.set('email-editable','email_at_start','yes'if self.email_at_start is True else 'no')
        self.config.set('email-editable','email_on_error','yes' if self.email_on_error is True else 'no')
        self.config.set('email-editable','email_on_terminate','yes' if self.email_on_terminate is True else 'no')
        self.config.set('email-editable','log_on_error','yes' if self.log_on_error is True else 'no')
        with open(Mailer.options_file, 'wb') as config_file:
            self.config.write(config_file)
            

    def connect(self):
        tries = 0
        while True:
            try:
                self.smtpserver = smtplib.SMTP(self.server, self.port, timeout=1)
                break
            except Exception as e:
                tries = tries + 1
                if (tries > 5):
                    return False, e
                time.sleep(1)
        return True, ''
        

    def send(self,subject,message):

        #say hello
        try:
            self.smtpserver.ehlo()
        except Exception as ex:
            return False,'First ehlo ' + str(ex)
        try:
            self.smtpserver.starttls()
        except Exception as ex:
            return False,'Start TLS '  + str(ex)
        
        try:   
            self.smtpserver.ehlo()
        except Exception as ex:
            return False,'Second ehlo ' + str(ex)        

        #login
        try:
            self.smtpserver.login(self.username, self.password)
        except Exception as ex:
            return False,'Login ' + str(ex)         

        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = self.is_to

        
        try:
            self.smtpserver.sendmail(self.username, self.is_to_list, msg.as_string())
        except Exception as ex:
            return False,'sendmail ' + str(ex)
        return True,''

    def disconnect(self):
        try:
            self.smtpserver.quit()
        except Exception as ex:
            return False,str(ex)
        return True,''        
            


class Network(object):

    ip=''
    interface=''

    def __init__(self):
        self.mon=Monitor()
        self.force_ip=''

    def get_ip(self):
        return Network.interface, Network.ip
    

    def set_ip(self, interface,ip):
        Network.interface = interface
        Network.ip = ip

        
    def read_config(self,options_file_path):
        
        config=ConfigParser.ConfigParser()
        config.read(options_file_path)
        self.preferred_interface=config.get('network','preferred_interface',0)
        self.unit=config.get('network','unit',0)
        self.force_ip=config.get('network','force_ip',0)
        self.manager_port=int(config.get('manager','port',0))
        self.manager_username=config.get('manager','username',0)
        self.manager_password=config.get('manager','password',0)
        self.editor_username=config.get('editor','username',0)
        self.editor_password=config.get('editor','password',0)
        self.editor_port=int(config.get('editor','port',0))        

    def wait_for_network(self,tries):       
        i=0
        while True:
            if self.is_connected() is True:
                return True
            else:        
                i+=1
                self.mon.log(self, 'Trying to connect to network ' + str(i))
                if i>tries:
                    return False
                sleep(1)

    def is_connected(self):
        interfaces,ips = self.get_ips()
        if interfaces == 0:
            return False
        else:
            return True
        
    def get_ips(self):
        arg='ip route list'
        p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
        data = p.communicate()

        # Split data [0] obtained from stdout into lines
        # print ' data is',data[0]
        ip_lines = data[0].splitlines()
        if len(ip_lines) == 0:
            # print 'not connected'
            return 0, []

        interfaces=0
        result=[]
        for line in ip_lines:
            fields= line.split()

            if fields[0] != 'default' and 'src' in fields:
                interface= fields[fields.index('dev')+1]
                ip = fields[fields.index('src')+1]
                interfaces +=1
                result=result + [[interface,ip]]
        return interfaces, result

    def get_preferred_ip(self):
        # returned ip_type
        # none available - return ''
        # 1 available - return it
        # 2 or more available - return one that matches or if none match first found
        if self.force_ip.strip() != '':
            return self.preferred_interface,self.force_ip   
        number, interfaces=self.get_ips()
        # print interfaces,ips
        if number == 0:
            return '',''
        elif number == 1:
            #if one interface return only
            i_type = interfaces[0][0]
            ip = interfaces[0][1]
            return i_type,ip
        else:
            i_type=''
            for interface in interfaces:
                if interface[0] == self.preferred_interface:
                    i_type=interface[0]
                    ip=interface[1]
                    return i_type,ip 
            # nothing matches preferred so use first one

            i_type=interfaces[0][0]
            ip=interfaces[0][1]  
            return i_type,ip         


if __name__ == "__main__":

    network=Network()

    i=0
    while True:
        if network.is_connected() is True:
            break
        else:        
            i+=1
            if i>20:
                print 'failed to connect after 20 seconds'
                exit()
            sleep(1)

    print 'network available'

    preferred_interface=''   
    i_type,ip=network.get_preferred_ip()
    print i_type,ip

    mailer=Mailer()

    mailer.read_config('/home/pi/pipresents/pp_config/pp_email.cfg')
    success=mailer.connect()
    print 'Connected '+ str(success)

    mailer.send(
                'test','hello')

    mailer.disconnect()
                
    

