#! /usr/bin/env python

"""
12/6/2016 - wait for environment variable to stabilise. Required for Jessie autostart
12/6/2106 - report startup failures via tk instead of printing
1/10/2016 - send output to named channel to work with debug_autostart.sh
2/11/2016 - remove sudo
2/11/2016 - browser update interval now 0.2 seconds
14/11/2016 - automatically find the ip address of the Pi
14/11/2016 - send an email with IP address of the Pi
20/11/2016 - sorted profiles display
20/11/2016 - Add livetracks, logs, and email options
1/12/2016 - corrected bug where options coild be partially changed it cancel hit after an error
10/12/2016 - fix email on abort bug after upload
"""

import remi.gui as gui
from remi import start, App
from remi_plus import OKDialog, OKCancelDialog

import time
import subprocess
import sys, os, shutil
import ConfigParser
import zipfile
from threading import Timer
from time import sleep

from pp_network import Mailer, Network



class PPManager(App):

    def __init__(self, *args):
        super(PPManager, self).__init__(*args)


    def main(self):
        # get directory holding the code
        self.manager_dir=sys.path[0]
            
        if not os.path.exists(self.manager_dir + os.sep + 'pp_manager.py'):
            print >> sys.stderr, 'Pi Presents Manager - Bad Application Directory'
            exit()

        # object if there is no options file
        self.options_file_path=self.manager_dir+os.sep+'pp_config'+os.sep+'pp_web.cfg'
        if not os.path.exists(self.options_file_path):
            print >> sys.stderr, 'Pi Presents Manager - Cannot find web options file'
            exit()

        # read the options
        self.options_config=self.read_options(self.options_file_path)
        self.get_options(self.options_config)

        # get interface and IP
        network=Network()
        self.interface, self.ip = network.get_ip()
        print self.interface, self.ip

        # create a mailer instance and read mail options
        self.email_options_file_path=self.manager_dir+os.sep+'pp_config'+os.sep+'pp_email.cfg'
        if not os.path.exists(self.email_options_file_path):
            print >> sys.stderr, 'Pi Presents Manager - Cannot find email options file'
            exit()
        self.mailer=Mailer()
        self.mailer.read_config(self.email_options_file_path)
        print >> sys.stderr,'read email options'

        #create upload directory if necessary
        self.upload_dir_path=self.pp_home_dir+os.sep+'pp_temp'
        if not os.path.exists(self.upload_dir_path):
            os.makedirs(self.upload_dir_path)

        self.pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'+self.pp_profiles_offset
        if not os.path.exists(self.pp_profiles_dir):
            print >> sys.stderr, 'Profiles directory does not exist: ' + self.pp_profiles_dir
            exit()

        print >> sys.stderr, 'Web server started by pp_manager'

        #init variables
        self.profile_objects=[]
        self.current_profile=''

        # Initialise an instance of the Pi Presents and Web Editor driver classes
        self.pp=PiPresents()
        self.ed = WebEditor()
        self.ed.init(self.manager_dir)


        mww=550
        # root and frames
        root = gui.VBox(width=mww,height=600) #10
        top_frame=gui.VBox(width=mww,height=40) #1
        middle_frame=gui.VBox(width=mww,height=500) #5
        button_frame=gui.HBox(width=250,height=40) #10

        # menu
        menu = gui.Menu(width=mww-20, height=30)

        miw=70
        # media menu
        media_menu = gui.MenuItem('Media',width=miw, height=30)        
        media_import_menu = gui.MenuItem('Import',width=miw, height=30)
        media_upload_menu = gui.MenuItem('Upload',width=miw, height=30)
        media_manage_menu = gui.MenuItem('Manage',width=miw, height=30)
        media_manage_menu.set_on_click_listener(self, 'on_media_manage_clicked')
        media_import_menu.set_on_click_listener(self, 'on_media_import_clicked')
        media_upload_menu.set_on_click_listener(self, 'on_media_upload_clicked')

        # livetracks menu
        livetracks_menu = gui.MenuItem('Live Tracks',width=miw, height=30)        
        livetracks_import_menu = gui.MenuItem('Import',width=miw, height=30)
        livetracks_upload_menu = gui.MenuItem('Upload',width=miw, height=30)
        livetracks_import_menu.set_on_click_listener(self, 'on_livetracks_import_clicked')
        livetracks_upload_menu.set_on_click_listener(self, 'on_livetracks_upload_clicked')
        livetracks_manage_menu = gui.MenuItem('Manage',width=miw, height=30)
        livetracks_manage_menu.set_on_click_listener(self, 'on_livetracks_manage_clicked')
 
  
        #profile menu
        profile_menu = gui.MenuItem( 'Profile',width=miw, height=30)        
        profile_import_menu = gui.MenuItem('Import',width=miw, height=30)
        profile_import_menu.set_on_click_listener(self, 'on_profile_import_clicked')
        profile_upload_menu = gui.MenuItem('Upload',width=miw, height=30)
        profile_upload_menu.set_on_click_listener(self, 'on_profile_upload_clicked')
        profile_download_menu = gui.MenuItem('Download',width=miw, height=30)
        profile_download_menu.set_on_click_listener(self, 'on_profile_download_clicked')

        #logs menu
        logs_menu = gui.MenuItem( 'Logs',width=miw, height=30)  
        log_download_menu = gui.MenuItem('Download Log',width=miw + 80, height=30)
        log_download_menu.set_on_click_listener(self, 'on_log_download_clicked')
        stats_download_menu = gui.MenuItem('Download Stats',width=miw + 80, height=30)
        stats_download_menu.set_on_click_listener(self, 'on_stats_download_clicked')
        
        # editor menu
        editor_menu=gui.MenuItem('Editor',width=miw,height=30)
        editor_run_menu=gui.MenuItem('Run',width=miw,height=30)
        editor_run_menu.set_on_click_listener(self,'on_editor_run_menu_clicked')
        editor_exit_menu=gui.MenuItem('Exit',width=miw,height=30)
        editor_exit_menu.set_on_click_listener(self,'on_editor_exit_menu_clicked')  


        #options menu
        options_menu=gui.MenuItem('Options',width=miw,height=30)
        options_manager_menu=gui.MenuItem('Manager',width=miw,height=30)
        options_manager_menu.set_on_click_listener(self,'on_options_manager_menu_clicked')
        options_autostart_menu=gui.MenuItem('Autostart',width=miw,height=30)
        options_autostart_menu.set_on_click_listener(self,'on_options_autostart_menu_clicked')        
        options_email_menu=gui.MenuItem('Email',width=miw,height=30)
        options_email_menu.set_on_click_listener(self,'on_options_email_menu_clicked')

        # Pi menu
        pi_menu=gui.MenuItem('Pi',width=miw,height=30)
        pi_reboot_menu=gui.MenuItem('Reboot',width=miw,height=30)
        pi_reboot_menu.set_on_click_listener(self,'pi_reboot_menu_clicked')

        
        # list of profiles
        self.profile_list = gui.ListView(width=250, height=300)
        self.profile_list.set_on_selection_listener(self,'on_profile_selected')

         
        #status and buttons

        self.profile_name = gui.Label('Selected Profile: ',width=400, height=20)
        
        self.pp_state_display = gui.Label('',width=400, height=20)
        
        self.run_pp = gui.Button('Run',width=80, height=30)
        self.run_pp.set_on_click_listener(self, 'on_run_button_pressed')
        
        self.exit_pp = gui.Button('Exit',width=80, height=30)
        self.exit_pp.set_on_click_listener(self, 'on_exit_button_pressed')

        self.refresh = gui.Button('Refresh List',width=120, height=30)
        self.refresh.set_on_click_listener(self, 'on_refresh_profiles_pressed')
        
        self.status = gui.Label('Manager for Pi Presents Started',width=400, height=30)

        # Build the layout

        # buttons
        button_frame.append(self.run_pp)
        button_frame.append(self.exit_pp)
        button_frame.append(self.refresh)
        
        # middle frame
        middle_frame.append(self.pp_state_display)
        middle_frame.append(button_frame)
        middle_frame.append(self.profile_list)
        middle_frame.append(self.profile_name)
        middle_frame.append(self.status)

        # menus
        profile_menu.append(profile_import_menu)
        profile_menu.append(profile_upload_menu)
        profile_menu.append(profile_download_menu)
        
        media_menu.append(media_import_menu)
        media_menu.append(media_upload_menu)
        media_menu.append(media_manage_menu)

        livetracks_menu.append(livetracks_import_menu)
        livetracks_menu.append(livetracks_upload_menu)
        livetracks_menu.append(livetracks_manage_menu)

        logs_menu.append(log_download_menu)        
        logs_menu.append(stats_download_menu)
        
        editor_menu.append(editor_run_menu)
        editor_menu.append(editor_exit_menu)
        
        options_menu.append(options_manager_menu)
        options_menu.append(options_autostart_menu)
        options_menu.append(options_email_menu)

        pi_menu.append(pi_reboot_menu)

        menu.append(profile_menu)
        menu.append(media_menu)
        menu.append(livetracks_menu)
        menu.append(logs_menu)
        menu.append(editor_menu)
        menu.append(options_menu)
        menu.append(pi_menu)
        
        top_frame.append(menu)
        
        root.append(top_frame)
        root.append(middle_frame)
        

        # display the initial list of profiles
        self.display_profiles()

        # kick of regular display of Pi Presents running state
        self.display_state()

        # returning the root widget
        return root


    # Display Status

    def update_status(self,text):
        self.status.set_text(text)


    # ******************
    # Pi Reboot
    # ******************

    def pi_reboot_menu_clicked(self):
        subprocess.call (['sudo','reboot'])


        
    # ******************
    # MANAGER OPTIONS
    # ******************


    def read_options(self,options_file):
        """reads options from options file """
        config=ConfigParser.ConfigParser()
        config.read(options_file)
        return config
    

    def get_options(self,config):

        self.pp_profiles_offset =config.get('manager-editable','profiles_offset',0)
        self.media_offset =config.get('manager-editable','media_offset',0)
        self.livetracks_offset =config.get('manager-editable','livetracks_offset',0)
        self.options = config.get('manager-editable','options',0)

        self.pp_home_dir =config.get('manager','home',0)
        self.top_dir = config.get('manager','import_top',0)
        self.unit=config.get('network','unit')

        self.autostart_path=config.get('manager-editable','autostart_path')
        self.autostart_options = config.get('manager-editable','autostart_options',0)

        self.pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'+self.pp_profiles_offset
        self.media_dir=self.pp_home_dir+self.media_offset
        self.livetracks_dir=self.pp_home_dir+self.livetracks_offset

        self.editor_port= config.get('editor','port')
        # self.print_paths()


    def print_paths(self):
        print 'home',self.pp_home_dir
        print 'profiles',self.pp_profiles_offset, self.pp_profiles_dir
        print 'media', self.media_offset, self.media_dir
        print 'livetracks', self.livetracks_offset, self.livetracks_dir
        print 'top',self.top_dir



    def save_options(self,config,options_file):
        """ save the output of the options edit dialog to file"""
        
        config.set('manager-editable','media_offset',self.media_offset)
        config.set('manager-editable','livetracks_offset',self.livetracks_offset)
        config.set('manager-editable','profiles_offset',self.pp_profiles_offset)
        config.set('manager-editable','options',self.options)

        config.set('manager-editable','autostart_path',self.autostart_path)        
        config.set('manager-editable','autostart_options',self.autostart_options)
        
        with open(options_file, 'wb') as config_file:
            config.write(config_file)
    

    def on_options_autostart_menu_clicked(self):
        self.options_autostart_dialog=gui.GenericDialog(width=450,height=300,title='Autostart Options',
                                            message='Edit then click OK or Cancel',autohide_ok=False)
             


        self.autostart_path_field= gui.TextInput(width=250, height=30)
        self.autostart_path_field.set_text(self.autostart_path)
        self.autostart_path_field.set_on_enter_listener(self,'dummy_enter')
        self.options_autostart_dialog.add_field_with_label('autostart_path_field','Autostart Profile Path',self.autostart_path_field)

         
        self.autostart_options_field= gui.TextInput(width=250, height=30)
        self.autostart_options_field.set_text(self.autostart_options)
        self.autostart_options_field.set_on_enter_listener(self,'dummy_enter')
        self.options_autostart_dialog.add_field_with_label('autostart_options_field','Autostart Options',self.autostart_options_field)

        self.autostart_error=gui.Label('',width=440,height=30)
        self.options_autostart_dialog.add_field('autostart_error',self.autostart_error)

        self.options_autostart_dialog.set_on_confirm_dialog_listener(self,'on_options_autostart_dialog_confirm')
        self.options_autostart_dialog.set_on_cancel_dialog_listener(self,'on_options_autostart_dialog_cancel')
        self.options_autostart_dialog.show(self)


    def on_options_manager_menu_clicked(self):
        self.options_manager_dialog=gui.GenericDialog(width=450,height=300,title='Manager Options',
                                                      message='Edit then click OK or Cancel',autohide_ok=False)

        self.media_field= gui.TextInput(width=250, height=30)
        self.media_field.set_text(self.media_offset)
        self.media_field.set_on_enter_listener(self,'dummy_enter')
        self.options_manager_dialog.add_field_with_label('media_field','Media Offset',self.media_field)

        self.livetracks_field= gui.TextInput(width=250, height=30)
        self.livetracks_field.set_text(self.livetracks_offset)
        self.livetracks_field.set_on_enter_listener(self,'dummy_enter')
        self.options_manager_dialog.add_field_with_label('livetracks_field','Live Tracks Offset',self.livetracks_field)

        
        self.profiles_field= gui.TextInput(width=250, height=30)
        self.profiles_field.set_text(self.pp_profiles_offset)
        self.profiles_field.set_on_enter_listener(self,'dummy_enter')
        self.options_manager_dialog.add_field_with_label('profiles_field','Profiles Offset',self.profiles_field)
        
        self.options_field= gui.TextInput(width=250, height=30)
        self.options_field.set_on_enter_listener(self,'dummy_enter')
        self.options_field.set_text(self.options)
        self.options_manager_dialog.add_field_with_label('options_field','Pi Presents Options',self.options_field)

        self.options_error=gui.Label('',width=440,height=30)
        self.options_manager_dialog.add_field('options_error',self.options_error)
        
        self.options_manager_dialog.set_on_confirm_dialog_listener(self,'on_options_manager_dialog_confirm')
        self.options_manager_dialog.set_on_cancel_dialog_listener(self,'on_options_manager_dialog_cancel')
        self.options_manager_dialog.show(self)


    def dummy_enter(self,fred):
        # fudge to stop enter key making the text disapppear in single line text input
        pass


    def on_options_autostart_dialog_confirm(self):
        result=self.options_autostart_dialog.get_field('autostart_path_field').get_value()            
        autostart_profile_path=self.pp_home_dir+os.sep+'pp_profiles'+os.sep+result
        if not os.path.exists(autostart_profile_path):
            self.autostart_error.set_text('Profile does not exist: ' + autostart_profile_path)
            return
        else:
            self.autostart_path=result

        self.autostart_options=self.options_autostart_dialog.get_field('autostart_options_field').get_value() 

        self.save_options(self.options_config,self.options_file_path)
        self.options_autostart_dialog.hide()
        

    def on_options_autostart_dialog_cancel(self):
        self.get_options(self.options_config)
        

    def on_options_manager_dialog_confirm(self):
        media_offset=self.options_manager_dialog.get_field('media_field').get_value()
        media_dir=self.pp_home_dir+media_offset
        if not os.path.exists(media_dir):
            self.options_error.set_text('Media Directory does not exist: ' + media_dir)
            return
        else:
            self.media_offset=media_offset

        livetracks_offset=self.options_manager_dialog.get_field('livetracks_field').get_value()
        livetracks_dir=self.pp_home_dir+livetracks_offset
        if not os.path.exists(livetracks_dir):
            self.options_error.set_text('Live Tracks Directory does not exist: ' + livetracks_dir)
            return
        else:
            self.livetracks_offset=livetracks_offset
        
        result=self.options_manager_dialog.get_field('profiles_field').get_value()
        pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'+result
        if not os.path.exists(pp_profiles_dir):
            self.options_error.set_text('Profiles Offset does not exist: ' + pp_profiles_dir)
            return
        else:
            self.pp_profiles_offset = result

        self.options=self.options_manager_dialog.get_field('options_field').get_value() 

        self.save_options(self.options_config,self.options_file_path)

        self.options_manager_dialog.hide()
        
        # and display the new list of profiles
        self.get_options(self.options_config)
        self.display_profiles()
        
    def on_options_manager_dialog_cancel(self):
        self.get_options(self.options_config)
        

    # ******************
    # EMAIL OPTIONS
    # ******************

    def on_options_email_menu_clicked(self):
        self.options_email_dialog=gui.GenericDialog(width=450,height=700,title='Email Options',
                                                      message='Edit then click OK or Cancel',autohide_ok=False)

        self.email_allowed_field= gui.TextInput(width=200, height=30)
        self.email_allowed_field.set_text(self.mailer.config.get('email-editable','email_allowed'))
        self.email_allowed_field.set_on_enter_listener(self,'dummy_enter')
        self.options_email_dialog.add_field_with_label('email_allowed_field','Allow Email',self.email_allowed_field)

        self.email_to_field= gui.TextInput(width=200, height=90)
        self.email_to_field.set_text(self.mailer.config.get('email-editable','to'))
        # self.email_to_field.set_on_enter_listener(self,'dummy_enter')
        self.options_email_dialog.add_field_with_label('email_to_field','To',self.email_to_field)

        self.email_with_ip_field= gui.TextInput(width=200, height=30)
        self.email_with_ip_field.set_text(self.mailer.config.get('email-editable','email_with_ip'))
        self.email_with_ip_field.set_on_enter_listener(self,'dummy_enter')
        self.options_email_dialog.add_field_with_label('email_with_ip_field','Email with IP',self.email_with_ip_field)

        self.email_at_start_field= gui.TextInput(width=200, height=30)
        self.email_at_start_field.set_text(self.mailer.config.get('email-editable','email_at_start'))
        self.email_at_start_field.set_on_enter_listener(self,'dummy_enter')
        self.options_email_dialog.add_field_with_label('email_at_start_field','Email at Start',self.email_at_start_field)

        self.email_on_error_field= gui.TextInput(width=200, height=30)
        self.email_on_error_field.set_text(self.mailer.config.get('email-editable','email_on_error'))
        self.email_on_error_field.set_on_enter_listener(self,'dummy_enter')
        self.options_email_dialog.add_field_with_label('email_on_error_field','Email on Error',self.email_on_error_field)
  
        self.email_on_terminate_field= gui.TextInput(width=200, height=30)
        self.email_on_terminate_field.set_text(self.mailer.config.get('email-editable','email_on_terminate'))
        self.email_on_terminate_field.set_on_enter_listener(self,'dummy_enter')
        self.options_email_dialog.add_field_with_label('email_on_terminate_field','Email on Terminate',self.email_on_terminate_field)

        self.log_on_error_field= gui.TextInput(width=200, height=30)
        self.log_on_error_field.set_text(self.mailer.config.get('email-editable','log_on_error'))
        self.log_on_error_field.set_on_enter_listener(self,'dummy_enter')
        self.options_email_dialog.add_field_with_label('log_on_error_field','Log on Error',self.log_on_error_field)
  
 
        
        self.options_error=gui.Label('',width=440,height=30)
        self.options_email_dialog.add_field('options_error',self.options_error)
        
        self.options_email_dialog.set_on_confirm_dialog_listener(self,'on_options_email_dialog_confirm')
        self.options_email_dialog.set_on_cancel_dialog_listener(self,'on_options_email_dialog_cancel')
        self.options_email_dialog.show(self)

    def on_options_email_dialog_confirm(self):

        email_allowed=self.options_email_dialog.get_field('email_allowed_field').get_value()
        if email_allowed not in ('yes','no'):   
            self.options_error.set_text('ERROR: Allow Email must be Yes or No')
            return

        email_to=self.options_email_dialog.get_field('email_to_field').get_value()

        email_with_ip=self.options_email_dialog.get_field('email_with_ip_field').get_value()
        if email_with_ip not in ('yes','no'):   
            self.options_error.set_text('ERROR: Email with IP must be Yes or No')
            return

        email_at_start=self.options_email_dialog.get_field('email_at_start_field').get_value()
        if email_at_start not in ('yes','no'):   
            self.options_error.set_text('ERROR: Email at Start must be Yes or No')
            return

        email_on_error=self.options_email_dialog.get_field('email_on_error_field').get_value()
        if email_on_error not in ('yes','no'):   
            self.options_error.set_text('ERROR: Email on Error must be Yes or No')
            return

        email_on_terminate=self.options_email_dialog.get_field('email_on_terminate_field').get_value()
        if email_on_terminate not in ('yes','no'):   
            self.options_error.set_text('ERROR: Email on Abort must be Yes or No')
            return

        log_on_error=self.options_email_dialog.get_field('log_on_error_field').get_value()
        if log_on_error not in ('yes','no'):   
            self.options_error.set_text('ERROR: Log on Error must be Yes or No')
            return

        # all correct so save
        self.mailer.email_allowed = True if email_allowed == 'yes' else False
        self.mailer.is_to=email_to
        self.mailer.email_with_ip = True if email_with_ip == 'yes' else False
        self.mailer.email_at_start = True if email_at_start == 'yes' else False
        self.mailer.email_on_error = True if email_on_error == 'yes' else False
        self.mailer.email_on_terminate = True if email_on_terminate == 'yes' else False
        self.mailer.log_on_error = True if log_on_error == 'yes' else False
        self.mailer.save_config(self.email_options_file_path)
            
        self.mailer.read_config(self.email_options_file_path)
        self.options_email_dialog.hide()
        

    def on_options_email_dialog_cancel(self):
        # use the previous saved options
        self.mailer.read_config(self.email_options_file_path)
        self.options_email_dialog.hide()        

    # ******************
    #MEDIA
    # ******************
    
     # import 
    def on_media_import_clicked(self):
        if not os.path.exists(self.top_dir):
            self.update_status('ERROR: Cannot find import directory')
            return              
        fileselectionDialog = gui.FileSelectionDialog('Import Media', 'Select files to import',True, self.top_dir)
        fileselectionDialog.set_on_confirm_value_listener(self, 'on_media_import_dialog_confirm')
        fileselectionDialog.set_on_cancel_dialog_listener(self, 'on_media_import_dialog_cancel')
        fileselectionDialog.show(self)

    def on_media_import_dialog_cancel(self):
        self.update_status('Media import cancelled: ')

    def on_media_import_dialog_confirm(self, filelist):
        if len(filelist)==0:
            self.update_status('FAILED: Import Media')
            OKDialog('Import Media','Error: No file selected').show(self)
            return    
        self.import_list=filelist
        import_from1=filelist[0]
        self.import_to=self.media_dir
        if not import_from1.startswith(self.top_dir):
            self.update_status('FAILED: Import Media')
            OKDialog('Import Media','Error: Access to source prohibited: ' + import_from1).show(self)
            return
        if not os.path.exists(self.import_to):
            self.update_status('FAILED: Import Media')
            OKDialog('Import Media',' Error: Media directory does not exist: ' + self.import_to).show(self)
            return

        # print self.import_list, self.import_to
        OKCancelDialog('Import Media','Files will be ovewritten even if newer',self.import_media_confirm).show(self)


    def import_media_confirm(self,result):
        if result:
            for item in self.import_list:
                if os.path.isdir(item):
                    self.update_status('FAILED: Import Media')
                    OKDialog('Import Media',' Error: Cannot import a directory').show(self)
                else:
                    shutil.copy2(item, self.import_to)
            self.update_status('Media import sucessful: ')
        else:
            self.update_status('Media import cancelled: ')


    #upload


    def on_media_upload_clicked(self):
        self.media_upload_dialog=gui.GenericDialog(width=500,height=200,title='<b>Upload Media</b>',
                                                   message='Select Media to Upload',autohide_ok=False)
        self.media_upload_button=gui.FileUploader(self.media_dir+'/',width=250,height=30,multiple_selection_allowed=True)
        self.media_upload_button.set_on_success_listener(self,'on_media_upload_success')
        self.media_upload_button.set_on_failed_listener(self,'on_media_upload_failed')
        self.media_upload_status=gui.Label('', width=450, height=30)
        self.media_upload_dialog.add_field('1',self.media_upload_button)
        self.media_upload_dialog.add_field('2',self.media_upload_status)
        self.media_upload_dialog.set_on_confirm_dialog_listener(self,'on_media_upload_dialog_confirm')
 
        self.media_upload_dialog.show(self)
      
    def on_media_upload_success(self,filelist):
        self.media_upload_status.set_text('File upload successful')

    def on_media_upload_failed(self,result):
        self.media_upload_status.set_text('ERROR: File upload failed')

    def on_media_upload_dialog_confirm(self):
        self.media_upload_dialog.hide()

    #manage

    def on_media_manage_clicked(self):
        media_items = os.listdir(self.media_dir) 
        if len(media_items) ==0:
            self.update_status('FAILED: Media folder empty')
            return
        self.manage_media_dialog=FileManager("Manage Media",self.media_dir,self.finished_manage_media)
        self.manage_media_dialog.show(self)

    def finished_manage_media(self):
        pass



    # *********************
    # LIVE TRACKS
    # *********************


     # import 
    def on_livetracks_import_clicked(self):
        if not os.path.exists(self.top_dir):
            self.update_status('ERROR: Cannot find import directory')
            return              
        fileselectionDialog = gui.FileSelectionDialog('Import Live Tracks', 'Select files to import',True, self.top_dir)
        fileselectionDialog.set_on_confirm_value_listener(self, 'on_livetracks_import_dialog_confirm')
        fileselectionDialog.set_on_cancel_dialog_listener(self, 'on_livetracks_import_dialog_cancel')
        fileselectionDialog.show(self)

    def on_livetracks_import_dialog_cancel(self):
        self.update_status('Live Tracks import cancelled: ')

    def on_livetracks_import_dialog_confirm(self, filelist):
        if len(filelist)==0:
            self.update_status('FAILED: Import Live Tracks')
            OKDialog('Import Live Tracks','Error: No file selected').show(self)
            return    
        self.import_list=filelist
        import_from1=filelist[0]
        self.import_to=self.livetracks_dir
        if not import_from1.startswith(self.top_dir):
            self.update_status('FAILED: Import Live Tracks')
            OKDialog('Import Live Tracks','Error: Access to source prohibited: ' + import_from1).show(self)
            return
        if not os.path.exists(self.import_to):
            self.update_status('FAILED: Import Live Tracks')
            OKDialog('Import Live Tracks',' Error: Live Tracks directory does not exist: ' + self.import_to).show(self)
            return

        # print self.import_list, self.import_to
        OKCancelDialog('Import livetracks','Files will be ovewritten even if newer',self.import_livetracks_confirm).show(self)


    def import_livetracks_confirm(self,result):
        if result:
            for item in self.import_list:
                if os.path.isdir(item):
                    self.update_status('FAILED: Import Live Tracks')
                    OKDialog('Import Live Tracks',' Error: Cannot import a directory').show(self)
                else:
                    shutil.copy2(item, self.import_to)
            self.update_status('Live Tracks import sucessful: ')
        else:
            self.update_status('Live Tracks import cancelled: ')


    #upload

    def on_livetracks_upload_clicked(self):
        self.livetracks_upload_dialog=gui.GenericDialog(width=500,height=200,title='<b>Upload Live Tracks</b>',
                                                   message='Select Live Tracks to Upload',autohide_ok=False)
        self.livetracks_upload_button=gui.FileUploader(self.livetracks_dir+'/',width=250,height=30,multiple_selection_allowed=True)
        self.livetracks_upload_button.set_on_success_listener(self,'on_livetracks_upload_success')
        self.livetracks_upload_button.set_on_failed_listener(self,'on_livetracks_upload_failed')
        self.livetracks_upload_status=gui.Label('', width=450, height=30)
        self.livetracks_upload_dialog.add_field('1',self.livetracks_upload_button)
        self.livetracks_upload_dialog.add_field('2',self.livetracks_upload_status)
        self.livetracks_upload_dialog.set_on_confirm_dialog_listener(self,'on_livetracks_upload_dialog_confirm')
 
        self.livetracks_upload_dialog.show(self)
      
    def on_livetracks_upload_success(self,filelist):
        self.livetracks_upload_status.set_text('File upload successful')

    def on_livetracks_upload_failed(self,result):
        self.livetracks_upload_status.set_text('ERROR: File upload failed')

    def on_livetracks_upload_dialog_confirm(self):
        self.livetracks_upload_dialog.hide()

    #manage

    def on_livetracks_manage_clicked(self):
        media_items = os.listdir(self.livetracks_dir) 
        if len(media_items) ==0:
            self.update_status('FAILED: Live Tracks folder empty')
            return
        self.manage_livetracks_dialog=FileManager("Manage Live Tracks",self.livetracks_dir,self.finished_manage_livetracks)
        self.manage_livetracks_dialog.show(self)

    def finished_manage_livetracks(self):
        pass


    # ******************        
    #PROFILES
    # ******************

    # import
    def on_profile_import_clicked(self):
        fileselectionDialog = gui.FileSelectionDialog('Import Profile', 'Select a Profile to import',False,self.top_dir)
        fileselectionDialog.set_on_confirm_value_listener(self, 'on_profile_import_dialog_confirm')
        fileselectionDialog.set_on_cancel_dialog_listener(self, 'on_profile_import_dialog_cancel')
        fileselectionDialog.show(self)

    def on_profile_import_dialog_cancel(self):
        self.update_status('Profile import cancelled: ')

    def on_profile_import_dialog_confirm(self, filelist):
        if len(filelist)==0:
            self.update_status('FAILED: import Profile')
            OKDialog('Import Profile','Error: No profile selected').show(self)
            return    
        self.import_from=filelist[0]
        self.from_basename=os.path.basename(self.import_from)
        self.import_to=self.pp_profiles_dir+os.sep+self.from_basename
        # print self.import_from, self.import_to, self.top_dir
        if not self.import_from.startswith(self.top_dir):
            self.update_status('FAILED: Import Profile')
            OKDialog('Import Profile','Error: Access to source prohibited: ' + self.import_from).show(self)
            return
        if not os.path.isdir(self.import_from):
            self.update_status('FAILED: import Profile')
            OKDialog('Import Profile','Error: Source is not a directory: ' + self.import_from).show(self)
            return
        if not os.path.exists(self.import_from + os.sep + 'pp_showlist.json'):
            self.update_status('FAILED: Import Profile')
            OKDialog('Import Profile','Error: Source is not a profile: ' + self.import_from).show(self)            
            return
        if os.path.exists(self.import_to):
            OKCancelDialog('Import Profile','Profile already exists, overwrite?',self.import_profile_confirm).show(self)

        else:
            self.import_profile_confirm(True)


    def import_profile_confirm(self,result):            
        if result:
            if os.path.exists(self.import_to):
                shutil.rmtree(self.import_to)
            # print self.import_from,self.import_to
            shutil.copytree(self.import_from, self.import_to)
            self.profile_count=self.display_profiles()

            self.update_status('Profile import successful ')
        else:
            self.update_status('Profile import cancelled ')


    # download
    def on_profile_download_clicked(self):
        if self.current_profile != '':
            dest=self.upload_dir_path+os.sep+self.current_profile_name
            base=self.pp_home_dir+os.sep+'pp_profiles'+self.current_profile
            shutil.make_archive(dest,'zip',base)
            self.profile_download_dialog=gui.GenericDialog(width=500,height=200,title='<b>Download Profile</b>',
                                                           message='',autohide_ok=False)
            self.profile_download_button = gui.FileDownloader('Click Link to Download', dest+'.zip', width=200, height=30)
            self.profile_download_status=gui.Label('', width=450, height=30)
            self.profile_download_dialog.add_field('1',self.profile_download_button)
            self.profile_download_dialog.add_field('2',self.profile_download_status)
            self.profile_download_dialog.show(self)
            self.profile_download_dialog.set_on_confirm_dialog_listener(self,'on_profile_download_dialog_confirm')
        else:
            OKDialog('Download Profile', 'Error: No profile selected').show(self)


# NO WAY TO DELETE THE ZIP


    def on_profile_download_dialog_confirm(self):
        self.profile_download_dialog.hide()      


    # upload
    def on_profile_upload_clicked(self):
        self.profile_upload_dialog=gui.GenericDialog(width=500,height=200,title='<b>Upload Profile</b>',
                                                     message='Select Profile to Upload',autohide_ok=False)
        self.profile_upload_button=gui.FileUploader(self.upload_dir_path+os.sep,width=250,height=30,multiple_selection_allowed=False)
        self.profile_upload_button.set_on_success_listener(self,'on_profile_upload_success')
        self.profile_upload_button.set_on_failed_listener(self,'on_profile_upload_failed')
        self.profile_upload_status=gui.Label('', width=450, height=30)
        self.profile_upload_dialog.add_field('1',self.profile_upload_button)
        self.profile_upload_dialog.add_field('2',self.profile_upload_status)
        self.profile_upload_dialog.show(self)
        self.profile_upload_dialog.set_on_confirm_dialog_listener(self,'on_profile_upload_dialog_confirm')


    def on_profile_upload_dialog_confirm(self):
        self.profile_upload_dialog.hide()      


    def on_profile_upload_success(self,filename):
        #filename is leafname of uploaded file
        # uploaded zip file goes into as specified in the widget constructor
        self.profile_upload_filename=filename    # xxxx.zip
        self.profile_upload_directory='/'+self.profile_upload_filename.split('.')[0]  # /xxxx
        source_file_path =self.upload_dir_path+os.sep+self.profile_upload_filename   
        # unzip it into  a directory in pp_temp with the uploaded filename
        if not zipfile.is_zipfile(source_file_path):
            self.profile_upload_status.set_text('ERROR: Uploaded file is not a Zip archive')
            os.remove(source_file_path)
            return
        zzip=zipfile.ZipFile(source_file_path)
        zzip.extractall(self.upload_dir_path)
        os.remove(source_file_path)
        
        # check temp directory is a profile
        if not os.path.exists(self.upload_dir_path+self.profile_upload_directory+os.sep+'pp_showlist.json'):
            self.profile_upload_status.set_text('ERROR: Uploaded Zip is not a profile')
            shutil.rmtree(self.upload_dir_path+self.profile_upload_directory)
        else:
            # warn if profile already exists
            if os.path.exists(self.pp_profiles_dir+self.profile_upload_directory):
                OKCancelDialog('Profile Upload','Profile already exists, overwrite?',self.on_profile_replace_ok).show(self)
            else:
                self.on_profile_replace_ok(True)


    def on_profile_replace_ok(self,result=False):            
        if result:
            if os.path.exists(self.pp_profiles_dir+self.profile_upload_directory):
                shutil.rmtree(self.pp_profiles_dir+self.profile_upload_directory)
            shutil.move(self.upload_dir_path+self.profile_upload_directory, self.pp_profiles_dir)
            self.profile_count=self.display_profiles()
            self.profile_upload_status.set_text('Profile upload successful: '+self.profile_upload_filename)
        else:
            self.profile_upload_status.set_text('Profile upload cancelled')
            shutil.rmtree(self.upload_dir_path+self.profile_upload_directory)

    def on_profile_upload_failed(self,filename):
        self.profile_upload_status.set_text(' Upload of Zip File Failed: ' + filename )
        self.profile_upload_filename=filename    # xxxx.zip
        source_file_path =self.upload_dir_path+os.sep+self.profile_upload_filename   
        if os.path.exists(source_file_path):
            os.remove(source_file_path)           



    # ******************
    # PROFILES LIST
    # ******************

    def on_refresh_profiles_pressed(self):
        self.display_profiles()

    
    def display_profiles(self):
        self.profile_list.empty()
        us_items = os.listdir(self.pp_profiles_dir)
        items=sorted(us_items)
        i=0
        for item in items:
            obj= gui.ListItem(item,width=300, height=20)
            self.profile_objects.append(obj)
            self.profile_list.append(obj,key=i)
            i+=1
        return


    def on_profile_selected(self,key):
        self.current_profile_name=self.profile_list.children[key].get_text()
        self.current_profile=self.pp_profiles_offset + os.sep + self.current_profile_name
        self.profile_name.set_text('Selected Profile:   '+self.pp_profiles_offset+os.sep+self.current_profile_name)



    # ******************
    # LOGS
    # ******************

    def on_log_download_clicked(self):
        self.on_logs_download_clicked('pp_log.txt','Log')
        
    def on_stats_download_clicked(self):
        self.on_logs_download_clicked('pp_stats.txt','Statistics')
        
    # download
    def on_logs_download_clicked(self,log_file,name):
        self.logs_dir=self.manager_dir+os.sep+'pp_logs'
        self.logs_download_dialog=gui.GenericDialog(width=500,height=200,title='<b>Download ' + name+ '</b>',
                                                       message='',autohide_ok=False)
        self.logs_download_button = gui.FileDownloader('Click Link to Download',self.logs_dir+os.sep+log_file, width=200, height=30)
        self.logs_download_status=gui.Label('', width=450, height=30)
        self.logs_download_dialog.add_field('1',self.logs_download_button)
        self.logs_download_dialog.add_field('2',self.logs_download_status)
        self.logs_download_dialog.show(self)
        self.logs_download_dialog.set_on_confirm_dialog_listener(self,'on_logs_download_dialog_confirm')


    def on_logs_download_dialog_confirm(self):
        self.logs_download_dialog.hide()      




    # ******************
    # RUNNING Pi Presents
    # ******************

    def display_state(self):
        if os.name== 'nt':
            self.pp_state_display.set_text('Server on Windows')   
        else:
            my_state=self.pp.am_i_running()
            # Poll state of Pi Presents
            pid,user,profile=self.pp.is_pp_running()
            if pid!=-1:
                self.pp_state_display.set_text('<b>'+self.unit +  ':</b>   RUNNING   '+ profile)   
            else:
                self.pp_state_display.set_text('<b>' +self.unit + ':</b>   STOPPED   (' + self.pp.lookup_state(my_state)+')')
        Timer(0.5,self.display_state).start()  
            


    def on_run_button_pressed(self):
        if os.name== 'nt':
            self.update_status('FAILED, Server on Windows')
            return
        if self.current_profile != '':
            command = self.manager_dir+'/pipresents.py'
            success=self.pp.run_pp(command,self.current_profile,self.options)
            if success is True:
                self.update_status('Pi Presents Started')
            else:
                self.update_status('FAILED, Pi Presents Not Started')
                OKDialog('Run Pi Presents','Error: Pi Presents already Running').show(self)
        else:
            OKDialog('Run Pi Presents','Error: No profile selected').show(self)
            self.update_status('FAILED, No profile selected')


    def on_exit_button_pressed(self):
        if os.name== 'nt':
            self.update_status('FAILED, Server on Windows')
            return
        success=self.pp.exit_pp()
        if success is True:
            self.update_status('Pi Presents Exited')
        else:
            self.update_status('FAILED, Pi Presents Not Exited')
            OKDialog('Exit Pi Presents','Pi Presents Not Running').show(self)


    # ******************
    # RUNNING Editor
    # ******************

    def ed_display_state(self):
        if os.name== 'nt':
            self.ed_state_display.set_text('Server on Windows')   
        else:
            my_state=self.ed.am_i_running()
            # Poll state of Editor
            pid,user=self.pp.is_ed_running()
            if pid!=-1:
                self.ed_state_display.set_text('<b>'+self.unit +  ':</b>   RUNNING  Web Editor as '+user)   
            else:
                self.ed_state_display.set_text('<b>' +self.unit + ':</b>   STOPPED   (' + self.ed.lookup_state(my_state)+')')
        Timer(0.5,self.ed_display_state).start()  
            


    def on_editor_run_menu_clicked(self):
        if os.name== 'nt':
            self.update_status('FAILED, Server on Windows')
            return
        command = self.manager_dir+'/pp_web_editor.py'
        self.ed_options=''
        # run editor if it is not already running
        self.ed.run_ed(command,self.ed_options)
        # and show a dialog to open a browser tab
        self.update_status('Editor Running')
        OKDialog('Open Editor Page',' <br><a href="http://'+self.ip+':'+self.editor_port +'"target="_blank">Click to Open Editor Page</a> ').show(self)


    def on_editor_exit_menu_clicked(self):
        if os.name== 'nt':
            self.update_status('FAILED, Server on Windows')
            return
        success=self.ed.exit_ed()
        if success is True:
            self.update_status('Editor Stopped')
        else:
            OKDialog('Exit Editor','Error: Editor Not Running').show(self)


# ******************
# File Manager
# ******************

class RenameDialog(gui.GenericDialog):
    def __init__(self, title,file_dir,filename):
        self.filename=filename
        self.file_dir=file_dir
        self.width=400
        self.height=400
        super(RenameDialog, self).__init__('<b>'+title+'</b>','',width=self.width,height=self.height,autohide_ok=False)
        self.root=gui.VBox(width=self.width-50, height=self.height-100)
        self.add_field('root',self.root)

        self.name_field=gui.TextInput(single_line=True,width=self.width-100,height=20)
        self.name_field.set_value(self.filename)
        self.set_on_confirm_dialog_listener(self,'on_rename_dialog_confirm')
        self.show(self)
        return None

    def rename_dialog_confirm(self):
        new_name=self.name_field.get_value()
        files_in_dir = os.listdir(self.file_dir)
        if new_name in files_in_dir:
            print 'exists'
        else:
            print 'absent'

        
class FileManager(gui.GenericDialog):
    
    def __init__(self, title, media_dir, callback):

        self.title=title
        self.media_dir=media_dir
        self.callback=callback
        self.root_width= 400
        self.root_height=450

        super(FileManager, self).__init__('<b>'+title+'</b>','',width=self.root_width,height=self.root_height,autohide_ok=False,display_cancel=False)

        media_items = os.listdir(self.media_dir)
        
        if len(media_items) !=0:
            
            self.root=gui.VBox(width=self.root_width-50, height=self.root_height-100)
            self.add_field('root',self.root)
            
            self.media_list = gui.ListView(width=300, height=300)
            self.media_list.set_on_selection_listener(self,'on_media_selected')
            self.root.append(self.media_list,key='media-list')

            self.media_name=gui.Label('Selected File: ',width=300, height=20)
            self.root.append(self.media_name,key='media-name')
            
            self.buttons_frame= gui.HBox(width=300, height=40)
            self.root.append(self.buttons_frame,key='buttons-frame')
            
            self.delete_media = gui.Button('Delete',width=80, height=30)
            self.delete_media.set_on_click_listener(self, 'on_delete_media_button_pressed')
            self.buttons_frame.append(self.delete_media,key='delete-media')
            
            # self.rename_media = gui.Button('Rename',width=80, height=30)
            # self.rename_media.set_on_click_listener(self, 'on_rename_media_button_pressed')
            # self.buttons_frame.append(self.rename_media,key='rename-media')

            self.set_on_confirm_dialog_listener(self,'on_media_manage_dialog_confirm')
            
            self.display_media()
            return None
        else:
            return None
        

    def on_refresh_media_pressed(self):
        self.display_media()

    
    def display_media(self):
        self.media_list.empty()
        items=sorted(os.listdir(self.media_dir))
        i=0
        for item in items:
            obj= gui.ListItem(item,width=300, height=20)
            # self.media_objects.append(obj)
            self.media_list.append(obj,key=i)
            i+=1
        return


    def on_media_selected(self,key):
        self.current_media_name=self.media_list.children[key].get_text()
        self.media_name.set_text('Selected File:   '+ self.current_media_name)


    def on_media_manage_dialog_confirm(self):
        self.hide()
        self.callback()

    def on_delete_media_button_pressed(self):
        # print self.media_dir+os.sep+self.current_media_name
        os.remove(self.media_dir+os.sep+self.current_media_name)
        self.display_media()

    def on_rename_media_button_pressed(self):
        self.rename_item_dialog=RenameDialog("Rename File",self.current_media_name,self.media_dir)
        self.rename_item_dialog.show(self)


# ******************
# Editor Driver
# ******************
      
class WebEditor(object):
    my_ed=None
    manager_dir=None

    # run when every instance is started
    def __init__(self):
        pass

    # run once when Manager is started
    def init(self,manager_dir):
        WebEditor.my_ed=None
        WebEditor.manager_dir=manager_dir
        pass

    def run_ed(self,command,options):
        WebEditor.my_ed=None
        pid,user=self.is_ed_running()
        # print pid,user,running_profile
        if pid ==-1:
            options_list= options.split(' ')
            command = ['python',command]
            if options_list[0] != '':
                command = command + options_list
            # print 'COMMAND',command
            WebEditor.my_ed=subprocess.Popen(command)
            return True
        else:
            return False

    def am_i_running(self):
        # -1 don't know as not started by manager
        # 0 running under manager
        # >0 stopped Web Editor that was run under the manager return code
        # return code 
        if WebEditor.my_ed !=None:
            ret_code=WebEditor.my_ed.poll()
            if ret_code==None:
                return 0
            else:
                return ret_code
        else:
            return -1

    def lookup_state(self,code):
        if code==-1: return ''
        elif code==0: return 'running'
        elif code==100: return 'normal exit'
        elif code==101: return 'Aborted'
        elif code==102: return 'Error Detected'
        else: return 'Unknown Code'


    def exit_ed(self):
        pid,user=self.is_ed_running()
        command = WebEditor.manager_dir+"/exit_ed.sh"
        if pid !=-1:
            subprocess.call([command,"exit"])
            self.my_ed=None
            return True
        else:
            return False

 
    def is_ed_running(self):
        p = subprocess.Popen(['ps', '-A', '-o', 'pid,user,cmd'], stdout=subprocess.PIPE)
        out, err = p.communicate()
        for line in out.splitlines():
            if '/pipresents/pp_web_editor.py' in line:
                # print 'LINE',line
                split=line.split()
                pid=int(split[0])
                user=split[1]
                # print 'PID/USER/PROFILE',pid, user
                return pid,user
        # print 'NOT RUNNING'
        return -1,''




# ******************
# Pi Presents Driver
# ******************
      
class PiPresents(object):
    my_pp=None
    manager_dir=None

    # run when every instance is started
    def __init__(self):
        pass

    # run once when Manager is started
    def init(self,manager_dir):
        PiPresents.my_pp=None
        PiPresents.manager_dir=manager_dir
        pass

    def run_pp(self,command,current_profile,options):
        PiPresents.my_pp=None
        pid,user,running_profile=self.is_pp_running()
        # print pid,user,running_profile
        if pid ==-1:
            options_list= options.split(' ')
            command = ['python',command,'-p',current_profile,'--manager']
            if options_list[0] != '':
                command = command + options_list
            # print 'COMMAND',command
            PiPresents.my_pp=subprocess.Popen(command)
            return True
        else:
            return False

    def am_i_running(self):
        # -1 don't know as not started by manager
        # 0 running under manager
        # >0 stopped PP that was run under the manager return code
        # return code 
        if PiPresents.my_pp !=None:
            ret_code=PiPresents.my_pp.poll()
            if ret_code==None:
                return 0
            else:
                return ret_code
        else:
            return -1

    def lookup_state(self,code):
        if code==-1: return ''
        elif code==0: return 'running'
        elif code==100: return 'normal exit'
        elif code==101: return 'Aborted'
        elif code==102: return 'Error Detected'
        else: return 'Unknown Code'


    def exit_pp(self):
        pid,user,running_profile=self.is_pp_running()
        command = PiPresents.manager_dir+"/exit_pp.sh"
        if pid !=-1:
            subprocess.call([command,"exit"])
            self.my_pp=None
            return True
        else:
            return False

 
    def is_pp_running(self):
        p = subprocess.Popen(['ps', '-A', '-o', 'pid,user,cmd'], stdout=subprocess.PIPE)
        out, err = p.communicate()
        for line in out.splitlines():
            if '/pipresents/pipresents.py' in line:
                # print 'LINE',line
                split=line.split()
                pid=int(split[0])
                user=split[1]
                p_index=split.index('-p')
                profile=split[p_index+1]
                # print 'PID/USER/PROFILE',pid, user, profile
                return pid,user,profile
        # print 'NOT RUNNING'
        return -1,'',''


    # ******************
    # Autostart Pi Presents
    # ******************

class Autostart(object):

    def autostart(self):
        # get directory holding the code
        self.manager_dir=sys.path[0]
            
        if not os.path.exists(self.manager_dir + os.sep + 'pp_manager.py'):
            print >> sys.stderr, 'Pi Presents Manager - Bad Application Directory'
            exit()

        self.options_file_path=self.manager_dir+os.sep+'pp_config'+os.sep+'pp_web.cfg'
        if not os.path.exists(self.options_file_path):
            print >> sys.stderr, 'Pi Presents Manager - web options file not found'
            exit()

        # read the options
        config=self.autostart_read_options(self.options_file_path)
        self.autostart_get_options(config)

        # and construct the paths
        self.pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'
        
        #start the Pi Presents Driver
        pp_auto=PiPresents()
        # and initialise its class variables
        pp_auto.init(self.manager_dir)


        if self.autostart_path != '' and os.name !='nt':
            autostart_profile_path= self.pp_home_dir+os.sep+'pp_profiles'+os.sep+self.autostart_path
            if not os.path.exists(autostart_profile_path):
                print >> sys.stderr, 'Autostart - Profile does not exist: ' + autostart_profile_path
            else:
                command =self.manager_dir+'/pipresents.py'
                success=pp_auto.run_pp(command,self.autostart_path,self.autostart_options)
                if success is True:
                    print >> sys.stderr, 'Pi Presents AUTO Started profile ',autostart_profile_path
                    return self.autostart_path
                else:
                    print >> sys.stderr, 'FAILED, Pi Presents AUTO Not Started'
                    return ''
        else:
            return ''

        


    def autostart_read_options(self,options_file):
        """reads options from options file """
        config=ConfigParser.ConfigParser()
        config.read(options_file)
        return config
    

    def autostart_get_options(self,config):
        self.autostart_path=config.get('manager-editable','autostart_path')
        self.autostart_options = config.get('manager-editable','autostart_options',0)
        self.pp_home_dir =config.get('manager','home',0)
        
        # self.print_paths()




# ***************************************
# MAIN
# ***************************************

if __name__  ==  "__main__":


    def try_connect(mailer):
        tries=1
        while True:
            success, error = mailer.connect()
            if success is True:
                return True
            else:
                print >> sys.stderr,'Failed to connect to email SMTP server ' + str(tries) +  '\n ' +str(error)
                tries +=1
                if tries >5:
                    print >> sys.stderr,'Failed to connect to email SMTP server after ' + str(tries)
                    return False

    def send_email(mailer,reason,subject,message):
        if try_connect(mailer) is False:
            return False
        else:
            success,error = mailer.send(subject,message)
            if success is False:
                print >> sys.stderr, 'Failed to send email: ' + str(error)
                success,error=mailer.disconnect()
                if success is False:
                    print >> sys.stderr,'Failed disconnect after send:' + str(error)
                return False
            else:
                print >> sys.stderr,'Sent email for ' + reason
                success,error=mailer.disconnect()
                if success is False:
                    print >> sys.stderr,'Failed disconnect ' + str(error)
                return True


    print >> sys.stderr, '\n *** Pi Presents Manager Started ***'

    # wait for environment ariables to stabilize. Required for Jessie autostart
    tries=0
    success=False
    while tries < 40:
        # get directory holding the code
        manager_dir=sys.path[0]
        manager_path=manager_dir+os.sep+'pp_manager.py'
        if os.path.exists(manager_path):
            success =True
            break
        tries +=1
        sleep (0.5)
        
    if success is False:
        print >> sys.stderr, "Manager: Bad application directory: " + manager_dir
        # tkMessageBox.showwarning("pp_manager.py","Bad application directory: "+ manager_dir)
        exit()

    print >> sys.stderr, 'Manager: Found pp_manager.py in ', manager_dir


    # Autostart Pi Presents if necessary
    auto=Autostart()
    auto_profile=auto.autostart()

    # wait for network to be available
    network=Network()
    print >> sys.stderr, 'Manager: Waiting for Network'
    network_connected=network.wait_for_network(10)
    if network_connected is False:
        print >> sys.stderr, 'Manager: Failed to connect to network after 10 seconds'
        # tkMessageBox.showwarning("Pi Presents Manager","Failed to connect to network after 10 seconds")       
        # exit()   

    # Read network config  -  pp_web.cfg
    manager_options_file_path=manager_dir+os.sep+'pp_config'+os.sep+'pp_web.cfg'
    if not os.path.exists(manager_options_file_path):
        print >> sys.stderr,'Manager: pp_web.cfg not found at ' + manager_options_file_path
        # tkMessageBox.showwarning("Pi Presents Manager",'pp_web.cfg not found at ' + manager_options_file_path)
        exit()
    network.read_config(manager_options_file_path)
    print >> sys.stderr, 'Manager: Found pp_web.cfg in ', manager_options_file_path


    # get interface and IP details of preferred interface
    if network_connected is True:
        interface,ip = network.get_preferred_ip()
        print >> sys.stderr, 'Manager: Network details ' + network.unit + ' ' + interface + ' ' + ip
        network.set_ip(interface,ip)


        # start the mailer
        email_file_path = manager_dir+os.sep+'pp_config'+os.sep+'pp_email.cfg'
        if not os.path.exists(email_file_path):
            print >> sys.stderr,'Manager: pp_email.cfg not found at ' + email_file_path
            # tkMessageBox.showwarning("Pi Presents Manager",'pp_email.cfg not found at ' + email_file_path)
            exit()
        print >> sys.stderr,'Manager: Found pp_email.cfg at ' + email_file_path
        
        mailer=Mailer()
        email_enabled=False
        mailer.read_config(email_file_path)    
        # all Ok so can enable email if config file allows it.
        if mailer.email_allowed is True:
            email_enabled=True
            print >> sys.stderr,'Manager: Email Enabled'
        
        # send an email with IP address of the server.
        if email_enabled is True and mailer.email_with_ip is True:
            subject= '[Pi Presents] ' + network.unit + ' Manager started: ' + ip + ':' + str(network.manager_port)

            message_text = time.strftime("%Y-%m-%d %H:%M") + ' \n ' + network.unit + '\n ' + interface + '\n'
            message_text +=' Manager: http://' + ip + ':' + str(network.manager_port) + '\n'
            message_text +=' Editor: http://' + ip + ':' + str(network.editor_port) + '\n'
            if auto_profile != '':
                message_text = message_text + 'Autostarting profile: '+ auto_profile
            # print >> sys.stderr,subject,message_text
            send_email(mailer,'IP Address',subject,message_text)
    else:
        ip='127.0.0.1'
        interface = 'local'


    # setting up remi debug level 
    #   2=all debug messages   1=error messages   0=no messages
    import remi.server
    remi.server.DEBUG_MODE = 0

    # start the web server to serve the Pi Presents Manager App
    start(PPManager,address=ip, port=network.manager_port,username=network.manager_username,password=network.manager_password,
          multiple_instance=False,enable_file_cache=True,
          update_interval=0.2, start_browser=False)





