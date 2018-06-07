import os
import imp
import ConfigParser
from pp_utils import Monitor

class IOPluginManager(object):

    plugins=[]

    def __init__(self):
        self.mon=Monitor()



    def init(self,pp_dir,pp_profile,widget,callback):
        self.pp_dir=pp_dir
        self.pp_profile=pp_profile
        IOPluginManager.plugins=[]

        if os.path.exists(self.pp_profile+os.sep+'pp_io_config'):
            # read the .cfg files in /pp_io_config in profile registring the I/O plugin
            for cfgfile in os.listdir(self.pp_profile+os.sep+'pp_io_config'):
                if cfgfile in ('screen.cfg','osc.cfg'):
                    continue
                cfgfilepath = self.pp_profile+os.sep+'pp_io_config'+os.sep+cfgfile
                status,message=self.init_config(cfgfile,cfgfilepath,widget,callback)
                if status == 'error':
                    return status,message

        #read .cfg file in /pipresents/pp_io_config if file not present in profile then use this one
        for cfgfile in os.listdir(self.pp_dir+os.sep+'pp_io_config'):
            if cfgfile in ('screen.cfg','osc.cfg'):
                continue
            if not os.path.exists(self.pp_profile+os.sep+'pp_io_config'+os.sep+cfgfile):
                cfgfilepath=self.pp_dir+os.sep+'pp_io_config'+os.sep+cfgfile
                status,message=self.init_config(cfgfile,cfgfilepath,widget,callback)
                if status == 'error':
                    return status,message
                 
        # print IOPluginManager.plugins
        return 'normal','I/O Plugins registered'

    def init_config(self,cfgfile,cfgfilepath,widget,callback):
        # print cfgfile,cfgfilepath
        reason,message,config=self._read(cfgfile,cfgfilepath)
        if reason =='error':
            self.mon.err(self,'Failed to read '+cfgfile + ' ' + message)
            return 'error','Failed to read '+cfgfile + ' ' + message                
        if config.has_section('DRIVER') is False:
            self.mon.err(self,'No DRIVER section in '+cfgfilepath)
            return 'error','No DRIVER section in '+cfgfilepath
        entry = dict()
        #read information from DRIVER section
        entry['title']=config.get('DRIVER','title')
        if config.get('DRIVER','enabled')=='yes':
            driver_name=config.get('DRIVER','module')
            driver_path=self.pp_dir+os.sep+'pp_io_plugins'+os.sep+driver_name+'.py'
            if not os.path.exists(driver_path):
                self.mon.err(self,driver_name + ' Driver not found in ' + driver_path)
                return 'error',driver_name + ' Driver not found in ' + driver_path
            
            instance = self._load_plugin_file(driver_name,self.pp_dir+os.sep+'pp_io_plugins')
            reason,message=instance.init(cfgfile,cfgfilepath,widget,callback)
            if reason=='warn':
                self.mon.warn(self,message)
                return 'error',message
            if reason=='error':
                self.mon.warn(self,message)
                return 'error',message
            entry['instance']=instance
            self.mon.log(self,message)
            IOPluginManager.plugins.append(entry)
        return 'normal','I/O Plugins registered'
    

    def start(self):
        for entry in IOPluginManager.plugins:
            plugin=entry['instance']
            if plugin.is_active() is True:
                plugin.start()
                
        
    def terminate(self):
        for entry in IOPluginManager.plugins:
            plugin=entry['instance']
            if plugin.is_active() is True:
                plugin.terminate()
                self.mon.log(self,'I/O plugin '+entry['title']+ ' terminated')

    def get_input(self,key):
        for entry in IOPluginManager.plugins:
            plugin=entry['instance']
            # print 'trying ',entry['title'],plugin.is_active()
            if plugin.is_active() is True:
                found,value = plugin.get_input(key)
                if found is True:
                    return found,value
        # key not found in any plugin
        return False,None

    def handle_output_event(self,name,param_type,param_values,req_time):
        for entry in IOPluginManager.plugins:
            plugin=entry['instance']
            # print 'trying ',entry['title'],name,param_type,plugin.is_active()
            if plugin.is_active() is True:
                reason,message= plugin.handle_output_event(name,param_type,param_values,req_time)
                if reason == 'error':
                    # self.mon.err(self,message)
                    return 'error',message
                else:
                    self.mon.log(self,message)
        return 'normal','output scan complete'

    def _load_plugin_file(self, name, driver_dir):
        fp, pathname,description = imp.find_module(name,[driver_dir])
        module_id =  imp.load_module(name,fp,pathname,description)
        plugin_class = getattr(module_id,name)
        return plugin_class()

        

    def _read(self,filename,filepath):
        if os.path.exists(filepath):
            config = ConfigParser.ConfigParser()
            config.read(filepath)
            self.mon.log(self,filename+" read from "+ filepath)
            return 'normal',filename+' read',config
        else:
            return 'error',filename+' not found at: '+filepath,None




        
        
    
