import configparser
import os
import subprocess

class AudioManager(object):

    config=None
    profile_names=('hdmi','local')
    sink_map={}
    audio_sys= ''
    
        
    #called for every class that uses it.
    def __init__(self):
        return
    
    #called once at start
    def init(self,pp_dir):
        AudioManager.sink_map={}
        status,message=self.read_config(pp_dir)
        if status=='error':
            return status,message
            
        status,message,val=self.read_audio_sys()
        if status=='error':
            return status,message
        AudioManager.audio_sys=val
        #print AudioManager.audio_sys
        
        if AudioManager.audio_sys == 'pulse':
            status,message=self.read_sinks()
            if status=='error':
                return status,message
        #print self.get_sink('hdmi')
        return 'normal','audio.cfg read'


    def get_audio_sys(self):
        #print 'config',AudioManager.audio_sys
        return AudioManager.audio_sys


    def get_sink(self,name):
        if name =='':
            return 'normal','',''  
        if name in AudioManager.sink_map:
            return 'normal','',AudioManager.sink_map[name]
        else:
            return 'error',name+'not in audio.cfg',''
            
    def sink_connected(self,sink):
        if sink=='':
            return True
        #command=['pacmd','list-sinks']
        command=['pactl','list','short','sinks']
        l_reply_utf=subprocess.check_output(command)
        #print l_reply_utf
        if sink in l_reply_utf:
            return True
        else:
            return False
       



# ****************************
# configuration
# ****************************
    def read_audio_sys(self):
        if not self.section_in_config('system'):
            return 'error','no system section in audio.cfg',''
        if not self.item_in_config('system','audio-system'):
            return 'error','no audio-system in audio.cfg',''
        val=self.get_item_in_config('system','audio-system').lower()
        if val not in ('pulse','alsa','cset'):
            return 'error','unknown audio-system in audio.cfg - '+ val,''
        return 'normal','',val
                 
    def read_sinks(self):
        if not self.section_in_config('pulse'):
            return 'error','no pulse section in audio.cfg'
        for name in AudioManager.profile_names:
            if not self.item_in_config('pulse',name):
                return 'error','audio device name not in audio.cfg - '+name
            val=self.get_item_in_config('pulse',name)
            AudioManager.sink_map[name]=val
        #print AudioManager.sink_map
        return 'normal',''


    # read pp_audio.cfg    
    def read_config(self,pp_dir):
        filename=pp_dir+os.sep+'pp_config'+os.sep+'pp_audio.cfg'
        if os.path.exists(filename):
            AudioManager.config = configparser.ConfigParser(inline_comment_prefixes = (';',))
            AudioManager.config.read(filename)
            return 'normal','pp_audio.cfg read OK'
        else:
            return 'error',"Failed to find audio.cfg at "+ filename

        
    def section_in_config(self,section):
        return AudioManager.config.has_section(section)
        
    def get_item_in_config(self,section,item):
        return AudioManager.config.get(section,item)

    def item_in_config(self,section,item):
        return AudioManager.config.has_option(section,item)


          
class PiPresents(object):
    def init(self):
        self.am=AudioManager()
        status,message=self.am.init('/home/pi/pipresents')
        #print (status,message)
        #print (self.am.sink_connected('alsa_output.platform-bcm2835_audio.digital-stereo'))

    def info(self):
        audio_sys=self.am.get_audio_sys()
        print ('\nAudio System:  '+audio_sys)
        if audio_sys=='pulse':
            print ('\nDevices:')
            print ('%-10s%-5s%-50s ' % ('Name','Connected','     Sink Name'))
            for name in AudioManager.profile_names:
                sink= self.am.get_sink(name)[2]
                if sink=='':
                    sink='sink not defined, default device will be used '
                    connected = '     '
                else:
                    conn= self.am.sink_connected(sink)
                    if conn:
                        connected='yes'
                    else:
                        connected ='No'
                print ('%-10s%-6s%-50s ' % (name,connected,sink))

if __name__ == '__main__':
    pp=PiPresents()
    pp.init()
    pp.info()

