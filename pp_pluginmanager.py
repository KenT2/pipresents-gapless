import os
import imp
import ConfigParser
from pp_utils import Monitor

class PluginManager(object):

    def __init__(self,show_id,root,canvas,show_params,track_params,pp_dir,pp_home,pp_profile):
        """
                show_id - show instance that player is run from (for monitoring only)
                canvas - the canvas onto which the image is to be drawn
                show_params -  dictionary of show parameters
                track_params - disctionary of track paramters
                pp_home - data home directory
                pp_dir - path of pipresents directory
                pp_profile - profile name
        """

        self.mon=Monitor()
        self.mon.off()

        self.show_id=show_id
        self.root=root
        self.canvas=canvas
        self.show_params=show_params
        self.track_params=track_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        self.plugin_timer=None
        self.plugin=None
        self.plugin_draw_time=0

 
    # called by players to load a plugin during load
    # load_plugin is expected to modify track file and kick off drawing to the canvas
    def load_plugin(self,track_file,plugin_cfg):

        # checks existence of and reads the plugin config file
        plugin_cfg_file= self.complete_path(plugin_cfg)
        if not os.path.exists(plugin_cfg_file):
            return 'error','plugin configuration file not found '+ plugin_cfg_file,''
        print plugin_cfg_file
        self.plugin_params=self.read(plugin_cfg_file)
        print self.plugin_params
        # checks the plugin exists
        plugin_dir = self.pp_dir+os.sep+'pp_home'+os.sep+'pp_plugins'
        plugin_file = plugin_dir+os.sep+self.plugin_params['plugin']+'.py'

        if not os.path.exists(plugin_file):
            return 'error','plugin file not found '+ plugin_file,''

        # import and run the plugin
        name = self.plugin_params['plugin']
        self.load_plugin_file(name, plugin_dir)
        if self.show_params['type'] in ('artliveshow','liveshow'):
            liveshow= True
            if 'type' in self.plugin_params:
                track_type=self.plugin_params['type']
            else:
                return 'error','track type not found in '+ plugin_file,''
        else:
            liveshow=False
            track_type=self.track_params['type']

        error,message,used_track,self.plugin_draw_time=self.plugin.load(track_file,liveshow,track_type)
        # self.canvas.itemconfig('pp-plugin-content',state='hidden')
        if error  !=  'normal':
            return error,message,''
        else:
            return 'normal','',used_track
        

    # called by players show method to start the plugin's display.
    def show_plugin(self):
        # do anything in the plugins show method
        if self.plugin is not None:
            self.plugin.show()
        # delete any old drawn content
        self.canvas.delete('pp-plugin-content')
        if self.plugin is not None and self.plugin_draw_time>=0:
            self.plugin.draw()
            self.canvas.itemconfig('pp-plugin-content',state='normal')
            self.canvas.update_idletasks()
            # and repeat if time>0
            if self.plugin_draw_time>0:
                self.plugin_timer=self.canvas.after(self.plugin_draw_time,self._repeat_plugin)

    def _repeat_plugin(self):
        self.canvas.delete('pp-plugin-content')
        self.plugin.draw()
        self.canvas.itemconfig('pp-plugin-content',state='normal')
        self.canvas.update_idletasks()
        self.plugin_timer=self.canvas.after(self.plugin_draw_time,self._repeat_plugin)


    # called by players at the end of a track
    def stop_plugin(self):
        # stop the timer as the stop_plugin may have been called while it is running
        if self.plugin_timer is not None:
            self.canvas.after_cancel(self.plugin_timer)
        if self.plugin is not None:
            self.canvas.itemconfig('pp-plugin-content',state='hidden')
            self.canvas.delete('pp-plugin-content')
            self.canvas.update_idletasks()
            # and call the plugin's hide method to allow tidy up.
            self.plugin.hide()



# **************************************
# plugin utilities
# **********************************

    def load_plugin_file(self, name, plugin_dir):
        fp, pathname,description = imp.find_module(name,[plugin_dir])
        module_id =  imp.load_module(name,fp,pathname,description)
        plugin_class=getattr(module_id,name)
        self.plugin=plugin_class(self.root,self.canvas,
                                 self.plugin_params,self.track_params,self.show_params,
                                 self.pp_dir,self.pp_home,self.pp_profile)



# ***********************************
# plugin configuration file
# ***********************************

    def read(self,plugin_cfg_file):
        self.plugin_config = ConfigParser.ConfigParser()
        self.plugin_config.read(plugin_cfg_file)
        return dict(self.plugin_config.items('plugin'))
        

# ***********************************
# utilities
# ***********************************

    def complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file[0] == "+":
            track_file=self.pp_home+track_file[1:]
        return track_file     
