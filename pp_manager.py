#! /usr/bin/env python

import remi.gui as gui
from remi import start, App
from remi_plus import OKDialog, OKCancelDialog, AdaptableDialog, append_with_label,FileSelectionDialog

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
    
    def read_options(self,options_file_path):
        self.options=Options()
        self.options.read_options(options_file_path)
        
        self.pp_home_dir=self.options.pp_home_dir

        self.pp_profiles_offset=self.options.pp_profiles_offset
        self.pp_profiles_dir=self.options.pp_profiles_dir
        self.top_dir=self.options.top_dir
        self.media_dir=self.options.media_dir
        self.media_offset=self.options.media_offset
        self.livetracks_dir=self.options.livetracks_dir
        self.livetracks_offset=self.options.livetracks_offset
        self.pp_options=self.options.pp_options
        self.unit=self.options.unit
        self.editor_port=self.options.editor_port


    def main(self):

        #create upload and download directories if necessary
        self.upload_dir='/tmp/pipresents/upload'
        self.download_dir='/tmp/pipresents/download'

        
        # get directory holding the code
        self.manager_dir=sys.path[0]
            
        if not os.path.exists(self.manager_dir + os.sep + 'pp_manager.py'):
            print >> sys.stderr, 'Manager: Bad Application Directory'
            exit()

        # object if there is no options file
        self.options_file_path=self.manager_dir+os.sep+'pp_config'+os.sep+'pp_web.cfg'
        if not os.path.exists(self.options_file_path):
            print >> sys.stderr, 'Manager: Cannot find web options file'
            exit()

        # read the options
        self.read_options(self.options_file_path)

        # get interface and IP
        network=Network()
        self.interface, self.ip = network.get_ip()
        print 'Manager: Network Details '+ self.interface, self.ip

        # create a mailer instance and read mail options
        self.email_options_file_path=self.manager_dir+os.sep+'pp_config'+os.sep+'pp_email.cfg'
        if not os.path.exists(self.email_options_file_path):
            print >> sys.stderr, 'Manager: Cannot find email options file'
            exit()
        self.mailer=Mailer()
        self.mailer.read_config(self.email_options_file_path)
        print >> sys.stderr,'Manager: read email options from '+self.email_options_file_path

        if not os.path.exists(self.pp_profiles_dir):
            print >> sys.stderr, 'Manager: Profiles directory does not exist: ' + self.pp_profiles_dir
            exit()

        print >> sys.stderr, 'Manager: Web server started by pp_manager'

        #init variables
        self.profile_objects=[]
        self.current_profile=''

        # Initialise an instance of the Pi Presents and Web Editor driver classes
        self.pp=PiPresents()
        self.ed = WebEditor()
        self.ed.init(self.manager_dir)


        mww=550
        # root and frames

        root = gui.VBox(width=mww, margin='0px auto') #the margin 0px auto centers the main container
        root.style['display'] = 'block'
        root.style['overflow'] = 'hidden'
        # root = gui.VBox(width=mww,height=600) #10
        top_frame=gui.VBox(width=mww,height=40) #1
        middle_frame=gui.VBox(width=mww,height=500) #5
        # middle_frame.style['background-color'] = 'LightGray'
        button_frame=gui.HBox(width=280,height=30) #10

        menubar=gui.MenuBar(width='100%', height='30px')


        # menu
        # menu = gui.Menu(width=mww-20, height=30)
        menu=gui.Menu(width='100%', height='30px')

        miw=70
        # media menu
        media_menu = gui.MenuItem('Media',width=miw, height=30)        
        media_import_menu = gui.MenuItem('Import',width=miw, height=30)
        media_upload_menu = gui.MenuItem('Upload',width=miw, height=30)
        media_manage_menu = gui.MenuItem('Manage',width=miw, height=30)
        media_manage_menu.set_on_click_listener(self.on_media_manage_clicked)
        media_import_menu.set_on_click_listener(self.on_media_import_clicked)
        media_upload_menu.set_on_click_listener(self.on_media_upload_clicked)

        # livetracks menu
        livetracks_menu = gui.MenuItem('Live Tracks',width=miw, height=30)        
        livetracks_import_menu = gui.MenuItem('Import',width=miw, height=30)
        livetracks_upload_menu = gui.MenuItem('Upload',width=miw, height=30)
        livetracks_import_menu.set_on_click_listener(self.on_livetracks_import_clicked)
        livetracks_upload_menu.set_on_click_listener(self.on_livetracks_upload_clicked)
        livetracks_manage_menu = gui.MenuItem('Manage',width=miw, height=30)
        livetracks_manage_menu.set_on_click_listener(self.on_livetracks_manage_clicked)
 
  
        #profile menu
        profile_menu = gui.MenuItem( 'Profile',width=miw, height=30)        
        profile_import_menu = gui.MenuItem('Import',width=miw, height=30)
        profile_import_menu.set_on_click_listener(self.on_profile_import_clicked)
        profile_upload_menu = gui.MenuItem('Upload',width=miw, height=30)
        profile_upload_menu.set_on_click_listener(self.on_profile_upload_clicked)
        profile_download_menu = gui.MenuItem('Download',width=miw, height=30)
        profile_download_menu.set_on_click_listener(self.on_profile_download_clicked)
        profile_manage_menu = gui.MenuItem('Manage',width=miw, height=30)
        profile_manage_menu.set_on_click_listener(self.on_profiles_manage_clicked)

        #logs menu
        logs_menu = gui.MenuItem( 'Logs',width=miw, height=30)  
        log_download_menu = gui.MenuItem('Download Log',width=miw + 80, height=30)
        log_download_menu.set_on_click_listener(self.on_log_download_clicked)
        stats_download_menu = gui.MenuItem('Download Stats',width=miw + 80, height=30)
        stats_download_menu.set_on_click_listener(self.on_stats_download_clicked)
        
        # editor menu
        editor_menu=gui.MenuItem('Editor',width=miw,height=30)
        editor_run_menu=gui.MenuItem('Run',width=miw,height=30)
        editor_run_menu.set_on_click_listener(self.on_editor_run_menu_clicked)
        editor_exit_menu=gui.MenuItem('Exit',width=miw,height=30)
        editor_exit_menu.set_on_click_listener(self.on_editor_exit_menu_clicked)  


        #options menu
        options_menu=gui.MenuItem('Options',width=miw,height=30)
        options_manager_menu=gui.MenuItem('Manager',width=miw,height=30)
        options_manager_menu.set_on_click_listener(self.on_options_manager_menu_clicked)
        options_autostart_menu=gui.MenuItem('Autostart',width=miw,height=30)
        options_autostart_menu.set_on_click_listener(self.on_options_autostart_menu_clicked)        
        options_email_menu=gui.MenuItem('Email',width=miw,height=30)
        options_email_menu.set_on_click_listener(self.on_options_email_menu_clicked)

        # Pi menu
        pi_menu=gui.MenuItem('Pi',width=miw,height=30)
        pi_reboot_menu=gui.MenuItem('Reboot',width=miw,height=30)
        pi_reboot_menu.set_on_click_listener(self.pi_reboot_menu_clicked)
        pi_shutdown_menu=gui.MenuItem('Shutdown',width=miw,height=30)
        pi_shutdown_menu.set_on_click_listener(self.pi_shutdown_menu_clicked)
        
        # list of profiles
        self.profile_list = gui.ListView(width=250, height=300)
        self.profile_list.set_on_selection_listener(self.on_profile_selected)

         
        #status and buttons

        self.profile_name = gui.Label('Selected Profile: ',width=400, height=20)
        
        self.pp_state_display = gui.Label('',width=400, height=20)
        
        self.run_pp = gui.Button('Run',width=80, height=30)
        self.run_pp.set_on_click_listener(self.on_run_button_pressed)
        
        self.exit_pp = gui.Button('Exit',width=80, height=30)
        self.exit_pp.set_on_click_listener(self.on_exit_button_pressed)

        self.refresh = gui.Button('Refresh List',width=120, height=30)
        self.refresh.set_on_click_listener(self.on_refresh_profiles_pressed)
        

        # Build the layout

        # buttons
        button_frame.append(self.run_pp)
        button_frame.append(self.exit_pp)
        button_frame.append(self.refresh)
        
        # middle frame
        middle_frame.append(menubar)
        middle_frame.append(self.pp_state_display)
        middle_frame.append(self.profile_list)
        middle_frame.append(button_frame)
        middle_frame.append(self.profile_name)


        # menus
        profile_menu.append(profile_import_menu)
        profile_menu.append(profile_upload_menu)
        profile_menu.append(profile_download_menu)
        profile_menu.append(profile_manage_menu)
        
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
        pi_menu.append(pi_shutdown_menu)
        
        menu.append(profile_menu)
        menu.append(media_menu)
        menu.append(livetracks_menu)
        menu.append(logs_menu)
        menu.append(editor_menu)
        menu.append(options_menu)
        menu.append(pi_menu)

        menubar.append(menu)
        

        
        # root.append(top_frame)
        root.append(middle_frame)
        

        # display the initial list of profiles
        self.display_profiles()

        # kick of regular display of Pi Presents running state
        self.display_state()

        # returning the root widget
        return root




    # ******************
    # Pi Reboot
    # ******************

    def pi_reboot_menu_clicked(self,widget):
        subprocess.call (['sudo','reboot'])

    def pi_shutdown_menu_clicked(self,widget):
        subprocess.call (['sudo','shutdown','now','SHUTTING DOWN'])

        
    # ******************
    # MANAGER OPTIONS
    # ******************


    def on_options_autostart_menu_clicked(self,widget):
        self.options_autostart_dialog=AutostartOptionsDialog(self.pp_home_dir,self.pp_profiles_dir)
        self.options_autostart_dialog.show(self)


    def on_options_manager_menu_clicked(self,widget):
        self.options_manager_dialog=ManagerOptionsDialog(self.pp_home_dir,self.pp_profiles_dir,
                                                         callback=self.options_manager_callback)
        self.options_manager_dialog.show(self)

    def options_manager_callback(self):
        # and display the new list of profiles after editing options
        self.read_options(self.options_file_path)
        self.display_profiles()


    def on_options_email_menu_clicked(self,widget):
        self.options_email_dialog=EmailOptionsDialog(callback=self.options_email_callback)
        self.options_email_dialog.show(self)

    def options_email_callback(self):
        self.mailer.read_config()


    # ******************
    #MEDIA
    # ******************
    
     # import 
    def on_media_import_clicked(self,widget):
        if not os.path.exists(self.top_dir):
            OKDialog('Import Media','Cannot find import starting directory: '+ self.top_dir).show(self)
            return              
        fileselectionDialog = FileSelectionDialog('Import Media', 'Select files to import',True, self.top_dir,
                                                      allow_file_selection=True, allow_folder_selection=False,
                                                  callback=self.on_media_import_dialog_confirm)
        fileselectionDialog.show(self)


    def on_media_import_dialog_confirm(self,filelist):
        if len(filelist)==0:
            OKDialog('Import Media','No file selected').show(self)
            return    
        self.import_list=filelist
        import_from1=filelist[0]
        self.import_to=self.media_dir
        if not import_from1.startswith(self.top_dir):
            OKDialog('Import Media','Access to import source prohibited: ' + import_from1).show(self)
            return
        if not os.path.exists(self.import_to):
            OKDialog('Import Media','Media directory does not exist: ' + self.import_to).show(self)
            return

        for item in self.import_list:
            self.current_item=item
            if os.path.isdir(item):
                OKDialog('Import Media','Cannot import a directory, ignoring: '+ item).show(self)
                continue
            from_head,from_tail=os.path.split(item)
            to_path=os.path.join(self.import_to,from_tail)                  
            if os.path.exists(to_path):
                OKCancelDialog('Import Media','Item already exists: ' + self.current_item +'<br>Overwrite?',callback=self.do_import_media_item).show(self)
            else:
                self.do_import_media_item(True)


    def do_import_media_item(self,result):
        if result is True:
            shutil.copy2(self.current_item, self.import_to)
        return
            




    #upload


    def on_media_upload_clicked(self,widget):
        self.media_upload_dialog=AdaptableDialog(width=300,height=200,title='<b>Upload Media</b>',
                                                   message='Select Media to Upload',
                                                 cancel_name='Done')
        self.media_upload_button=gui.FileUploader(self.upload_dir+'/',width=250,height=30,multiple_selection_allowed=False)
        self.media_upload_button.set_on_success_listener(self.on_media_upload_success)
        self.media_upload_button.set_on_failed_listener(self.on_media_upload_failed)
        self.media_upload_status=gui.Label('', width=450, height=30)
        self.media_upload_dialog.append_field(self.media_upload_button)
        self.media_upload_dialog.append_field(self.media_upload_status)
        self.media_upload_dialog.show(self)
      
    def on_media_upload_success(self,widget,filelist):
        if len(filelist)==0:
            OKDialog('Upload Media','No file selected').show(self)
            return
        self.upload_list=filelist
        self.upload_to=self.media_dir
        if not os.path.exists(self.upload_to):
            OKDialog('Upload Media','Media directory does not exist: ' + self.upload_to).show(self)
            return

        item=self.upload_list
        self.current_item=self.upload_list
        if os.path.isdir(item):
            OKDialog('Upload Media','Cannot upload a directory, ignoring: '+ item).show(self)
            return
        from_head,from_tail=os.path.split(item)
        self.to_path=os.path.join(self.upload_to,from_tail)                  
        if os.path.exists(self.to_path):
            OKCancelDialog('Upload Media','Item already exists: ' + self.current_item +'<br>Overwrite?',callback=self.do_upload_media_item).show(self)
        else:
            self.do_upload_media_item(True)


##        for item in self.upload_list:
##            self.current_item=item
##            if os.path.isdir(item):
##                OKDialog('Upload Media','Cannot upload a directory, ignoring: '+ item).show(self)
##                continue
##            from_head,from_tail=os.path.split(item)
##            to_path=os.path.join(self.upload_to,from_tail)                  
##            if os.path.exists(to_path):
##                OKCancelDialog('Upload Media','Item already exists: ' + self.current_item +'<br>Overwrite?',callback=self.do_upload_media_item).show(self)
##            else:
##                self.do_upload_media_item(True)


    def do_upload_media_item(self,result):
        if result is True:
            if os.path.exists(self.to_path):
                os.remove(self.to_path)
            shutil.move(self.upload_dir+os.sep+self.current_item, self.upload_to)
            self.media_upload_status.set_text('File upload successful')
        else:
            os.remove(self.upload_dir+os.sep+self.current_item)




    def on_media_upload_failed(self,widget,result):
        self.media_upload_status.set_text('ERROR: File upload failed')
        OKDialog('Import Media','File Upload Failed').show(self._base_app_instance)


    #manage

    def on_media_manage_clicked(self,widget):
        self.manage_media_dialog=FileManager("Manage Media",self.media_dir,False,self.finished_manage_media)
        self.manage_media_dialog.show(self)

    def finished_manage_media(self):
        pass



    # *********************
    # LIVE TRACKS
    # *********************


     # import 
    def on_livetracks_import_clicked(self,widget):
        if not os.path.exists(self.top_dir):
            OKDialog('Import Live Tracks','Cannot find import starting directory: '+self.top_dir).show(self)
            return              
        fileselectionDialog = FileSelectionDialog('Import Live Tracks', 'Select files to import',True, self.top_dir,
                                                      allow_file_selection=True, allow_folder_selection=False,
                                                  callback=self.on_livetracks_import_dialog_confirm)

        fileselectionDialog.show(self)


    def on_livetracks_import_dialog_confirm(self,filelist):
        if len(filelist)==0:
            OKDialog('Import Live Tracks','No file selected').show(self)
            return    
        self.import_list=filelist
        import_from1=filelist[0]
        self.import_to=self.livetracks_dir
        if not import_from1.startswith(self.top_dir):
            OKDialog('Import Live Tracks','Access to source prohibited: ' + import_from1).show(self)
            return
        if not os.path.exists(self.import_to):
            OKDialog('Import Live Tracks','Live Tracks directory does not exist: ' + self.import_to).show(self)
            return
        for item in self.import_list:
            self.current_item=item
            if os.path.isdir(item):
                OKDialog('Import Live Tracks','Cannot import a directory, ignoring: '+ item).show(self)
                continue
            from_head,from_tail=os.path.split(item)
            to_path=os.path.join(self.import_to,from_tail)                  
            if os.path.exists(to_path):
                OKCancelDialog('Import Live Tracks','Item already exists: ' + self.current_item +'<br>Overwrite?',callback=self.do_import_livetracks_item).show(self)
            else:
                self.do_import_livetracks_item(True)


    def do_import_livetracks_item(self,result):
        if result is True:
            shutil.copy2(self.current_item, self.import_to)
        return
 


    #upload

    def on_livetracks_upload_clicked(self,widget):
        self.livetracks_upload_dialog=AdaptableDialog(width=500,height=200,title='<b>Upload Live Tracks</b>',
                                                   message='Select Live Tracks to Upload',
                                                      cancel_name='Done')
        self.livetracks_upload_button=gui.FileUploader(self.upload_dir+'/',width=250,height=30,
                                                       multiple_selection_allowed=False)
        self.livetracks_upload_button.set_on_success_listener(self.on_livetracks_upload_success)
        self.livetracks_upload_button.set_on_failed_listener(self.on_livetracks_upload_failed)
        self.livetracks_upload_status=gui.Label('', width=450, height=30)
        self.livetracks_upload_dialog.append_field(self.livetracks_upload_button)
        self.livetracks_upload_dialog.append_field(self.livetracks_upload_status)
 
        self.livetracks_upload_dialog.show(self)
      
    def on_livetracks_upload_success(self,widget,filelist):
        if len(filelist)==0:
            OKDialog('Upload Livetracks','No file selected').show(self)
            return
        self.upload_list=filelist
        self.upload_to=self.livetracks_dir
        if not os.path.exists(self.upload_to):
            OKDialog('Upload Livetracks','Livetracks directory does not exist: ' + self.upload_to).show(self)
            return

        item=self.upload_list
        self.current_item=self.upload_list
        if os.path.isdir(item):
            OKDialog('Upload Livetracks','Cannot upload a directory, ignoring: '+ item).show(self)
            return
        from_head,from_tail=os.path.split(item)
        self.to_path=os.path.join(self.upload_to,from_tail)                  
        if os.path.exists(self.to_path):
            OKCancelDialog('Upload Livetracks','Item already exists: ' + self.current_item +'<br>Overwrite?',callback=self.do_upload_livetracks_item).show(self)
        else:
            self.do_upload_livetracks_item(True)


##        for item in self.upload_list:
##            self.current_item=item
##            if os.path.isdir(item):
##                OKDialog('Upload Livetracks','Cannot upload a directory, ignoring: '+ item).show(self)
##                continue
##            from_head,from_tail=os.path.split(item)
##            to_path=os.path.join(self.upload_to,from_tail)                  
##            if os.path.exists(to_path):
##                OKCancelDialog('Upload Livetracks','Item already exists: ' + self.current_item +'<br>Overwrite?',callback=self.do_upload_media_item).show(self)
##            else:
##                self.do_upload_livetracks_item(True)


    def do_upload_livetracks_item(self,result):
        if result is True:
            if os.path.exists(self.to_path):
                os.remove(self.to_path)
            shutil.move(self.upload_dir+os.sep+self.current_item, self.upload_to)
            self.livetracks_upload_status.set_text('File upload successful')
        else:
            os.remove(self.upload_dir+os.sep+self.current_item)



    def on_livetracks_upload_failed(self,result):
        self.livetracks_upload_status.set_text('ERROR: File upload failed')
        OKDialog('Upload Live Tracks','File upload failed').show(self._base_app_instance)



    #manage

    def on_livetracks_manage_clicked(self,widget):
        self.manage_livetracks_dialog=FileManager("Manage Live Tracks",self.livetracks_dir,False,
                                                  self.finished_manage_livetracks)
        self.manage_livetracks_dialog.show(self)

    def finished_manage_livetracks(self):
        pass


    # ******************        
    #PROFILES
    # ******************

    # import
    def on_profile_import_clicked(self,widget):
        if not os.path.exists(self.top_dir):
            OKDialog('Import Profile','Cannot find import directory').show(self)
            return 
        fileselectionDialog = FileSelectionDialog('Import Profile', 'Select a Profile to import',False,self.top_dir,
                                                      allow_file_selection=False,allow_folder_selection=True,
                                                  callback=self.on_profile_import_dialog_confirm)
        fileselectionDialog.show(self)


    def on_profile_import_dialog_confirm(self,filelist):
        if len(filelist)==0:
            OKDialog('Import Profile','No profile selected').show(self)
            return    
        self.import_from=filelist[0]
        self.from_basename=os.path.basename(self.import_from)
        self.import_to=self.pp_profiles_dir+os.sep+self.from_basename
        # print self.import_from, self.import_to, self.top_dir
        if not self.import_from.startswith(self.top_dir):
            OKDialog('Import Profile','Access to import source prohibited: ' + self.import_from).show(self)
            return
        if not os.path.isdir(self.import_from):
            OKDialog('Import Profile','Profile is not a directory: ' + self.import_from).show(self)
            return
        if not os.path.exists(self.import_from + os.sep + 'pp_showlist.json'):
            OKDialog('Import Profile','Profile does not have pp_showlist.json: ' + self.import_from).show(self)            
            return
        if os.path.exists(self.import_to):
            OKCancelDialog('Import Profile','Profile already exists, overwrite?',self.import_profile_confirm).show(self)

        else:
            self.import_profile_confirm(True)


    def import_profile_confirm(self,result):            
        if result is True:
            if os.path.exists(self.import_to):
                shutil.rmtree(self.import_to)
            # print self.import_from,self.import_to
            shutil.copytree(self.import_from, self.import_to)
            self.profile_count=self.display_profiles()



    # download
    def on_profile_download_clicked(self,widget):
        if self.current_profile != '':
            dest=self.download_dir+os.sep+self.current_profile_name
            # print 'temp',dest
            
            base=self.pp_home_dir+os.sep+'pp_profiles/'+self.current_profile
            # print 'proflie',base
            shutil.make_archive(dest,'zip',base)
            self.profile_download_dialog=AdaptableDialog(width=500,height=200,title='<b>Download Profile</b>',
                                                           message='',confirm_name='Done')
            self.profile_download_button = gui.FileDownloader('<br>Click Link to Download', dest+'.zip', width=200, height=80)
            self.profile_download_status=gui.Label('', width=450, height=30)
            self.profile_download_status.set_text('Selected Profile: '+ self.current_profile)
            self.profile_download_dialog.append_field(self.profile_download_status)
            self.profile_download_dialog.append_field(self.profile_download_button)
            self.profile_download_dialog.show(self)
            self.profile_download_dialog.set_on_confirm_dialog_listener(self.on_profile_download_dialog_done)
        else:
            OKDialog('Download Profile', 'No profile selected').show(self)


    # NO WAY TO DELETE THE ZIP except on _done


    def on_profile_download_dialog_done(self,widget):
        shutil.rmtree(self.download_dir)
        os.makedirs(self.download_dir)
        self.profile_download_dialog.hide()      


    # upload
    def on_profile_upload_clicked(self,widget):
        self.profile_upload_dialog=AdaptableDialog(width=500,height=200,title='<b>Upload Profile</b>',
                                                     message='Select Profile to Upload',
                                                   cancel_name='Done')
        self.profile_upload_button=gui.FileUploader(self.upload_dir+os.sep,width=250,height=30,multiple_selection_allowed=False)
        self.profile_upload_button.set_on_success_listener(self.on_profile_upload_success)
        self.profile_upload_button.set_on_failed_listener(self.on_profile_upload_failed)
        self.profile_upload_status=gui.Label('', width=450, height=30)
        self.profile_upload_dialog.append_field(self.profile_upload_button)
        self.profile_upload_dialog.append_field(self.profile_upload_status)
        self.profile_upload_dialog.show(self)


    def on_profile_upload_success(self,widget,filename):

        #filename is leafname of uploaded file
        # uploaded zip file goes into as specified in the widget constructor
        self.profile_upload_filename=filename    # xxxx.zip
        self.profile_upload_directory='/'+self.profile_upload_filename.split('.')[0]  # /xxxx
        source_file_path =self.upload_dir+os.sep+self.profile_upload_filename   
        # unzip it into  a directory in pp_temp with the uploaded filename
        if not zipfile.is_zipfile(source_file_path):
            self.profile_upload_status.set_text('ERROR: Uploaded file is not a Zip archive')
            os.remove(source_file_path)
            return
        zzip=zipfile.ZipFile(source_file_path)
        zzip.extractall(self.upload_dir+self.profile_upload_directory)
        os.remove(source_file_path)
        
        # check temp directory is a profile
        if not os.path.exists(self.upload_dir+self.profile_upload_directory+os.sep+'pp_showlist.json'):
            self.profile_upload_status.set_text('ERROR: Uploaded Zip is not a profile')
            shutil.rmtree(self.upload_dir+self.profile_upload_directory)
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
            shutil.move(self.upload_dir+self.profile_upload_directory, self.pp_profiles_dir)
            self.profile_count=self.display_profiles()
            self.profile_upload_status.set_text('Profile upload successful: '+self.profile_upload_filename)
        else:
            self.profile_upload_status.set_text('Profile upload cancelled')
            shutil.rmtree(self.upload_dir+self.profile_upload_directory)

    def on_profile_upload_failed(self,filename):
        self.profile_upload_status.set_text(' Upload of Zip File Failed: ' + filename )
        self.profile_upload_filename=filename    # xxxx.zip
        source_file_path =self.upload_dir+os.sep+self.profile_upload_filename   
        if os.path.exists(source_file_path):
            os.remove(source_file_path)           


    #manage

    def on_profiles_manage_clicked(self,widget):
        self.manage_media_dialog=FileManager("Manage Profiles",self.pp_profiles_dir,True,self.finished_manage_profiles)
        self.manage_media_dialog.show(self)

    def finished_manage_profiles(self):
        self.display_profiles()


    # ******************
    # PROFILES LIST
    # ******************

    def on_refresh_profiles_pressed(self,widget):
        self.display_profiles()
        self.profile_name.set_text('Selected Profile:')

    
    def display_profiles(self):
        self.current_profile=''
        self.profile_list.empty()
        us_items = os.listdir(self.pp_profiles_dir)
        items=sorted(us_items)
        i=0
        for item in items:
            if os.path.isdir(self.pp_profiles_dir+ os.sep+item) is True and os.path.exists(self.pp_profiles_dir+ os.sep + item + os.sep + 'pp_showlist.json') is True:
                obj= gui.ListItem(item,width=200, height=20)
                self.profile_objects.append(obj)
                self.profile_list.append(obj,key=i)
                i+=1
        return


    def on_profile_selected(self,widget,key):
        self.current_profile_name=self.profile_list.children[key].get_text()
        if self.pp_profiles_offset !='':
            self.current_profile=self.pp_profiles_offset + os.sep + self.current_profile_name
        else:
            self.current_profile=self.current_profile_name
        self.profile_name.set_text('Selected Profile:   '+ self.current_profile_name)



    # ******************
    # LOGS
    # ******************

    def on_log_download_clicked(self,widget):
        self.on_logs_download_clicked('pp_log.txt','Log')
        
    def on_stats_download_clicked(self,widget):
        self.on_logs_download_clicked('pp_stats.txt','Statistics')
        
    # download
    def on_logs_download_clicked(self,log_file,name):
        self.logs_dir=self.manager_dir+os.sep+'pp_logs'
        self.logs_download_dialog=AdaptableDialog(width=500,height=200,title='<b>Download ' + name+ '</b>',
                                                       message='',confirm_name='Done')
        self.logs_download_button = gui.FileDownloader('<br>Click Link to Start Download',self.logs_dir+os.sep+log_file, width=200, height=80)
        self.logs_download_status=gui.Label('', width=450, height=30)
        self.logs_download_dialog.append_field(self.logs_download_status)
        self.logs_download_status.set_text('Download: '+log_file)
        self.logs_download_dialog.append_field(self.logs_download_button)

        self.logs_download_dialog.show(self)
        self.logs_download_dialog.set_on_confirm_dialog_listener(self.on_logs_download_dialog_confirm)


    def on_logs_download_dialog_confirm(self,widget):
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
            


    def on_run_button_pressed(self,widget):
        if os.name== 'nt':
            OKDialog('Run Pi Presents','Failed, server on Windows').show(self)
            return
        if self.current_profile != '':
            command = self.manager_dir+'/pipresents.py'
            success=self.pp.run_pp(command,self.pp_home_dir,self.current_profile,self.pp_options)
            if success is False:
                OKDialog('Run Pi Presents','Error: Pi Presents already Running').show(self)
                return
        else:
            OKDialog('Run Pi Presents','Error: No profile selected').show(self)



    def on_exit_button_pressed(self,widget):
        if os.name== 'nt':
            OKDialog('Run Pi Presents','Failed, server on Windows').show(self)
            return
        success=self.pp.exit_pp()
        if success is False:
            OKDialog('Exit Pi Presents','Pi Presents Not Running').show(self)


    # ******************
    # RUNNING Editor
    # ******************

    def ed_display_state(self):
        if os.name== 'nt':
            OKDialog('Run Editor','Failed, server on Windows').show(self) 
        else:
            my_state=self.ed.am_i_running()
            # Poll state of Editor
            pid,user=self.pp.is_ed_running()
            if pid!=-1:
                self.ed_state_display.set_text('<b>'+self.unit +  ':</b>   RUNNING  Web Editor as '+user)   
            else:
                self.ed_state_display.set_text('<b>' +self.unit + ':</b>   STOPPED   (' + self.ed.lookup_state(my_state)+')')
        Timer(0.5,self.ed_display_state).start()  
            


    def on_editor_run_menu_clicked(self,widget):
        if os.name== 'nt':
            OKDialog('Run Pi Presents','Failed, server on Windows').show(self)
            return
        command = self.manager_dir+'/pp_web_editor.py'
        self.ed_options=''
        # run editor if it is not already running
        self.ed.run_ed(command,self.ed_options)
        # and show a dialog to open a browser tab
        OKDialog('Open Editor Page',' <br><a href="http://'+self.ip+':'+self.editor_port +'"target="_blank">Click to Open Editor Page</a> ').show(self)


    def on_editor_exit_menu_clicked(self,widget):
        if os.name== 'nt':
            OKDialog('Run Pi Presents','Failed, server on Windows').show(self)
            return
        success=self.ed.exit_ed()
        if success is False:
            OKDialog('Exit Editor','Error: Editor Not Running').show(self)


# ******************
# File Manager
# ******************

class RenameDialog(AdaptableDialog):
    def __init__(self, title,file_dir,filename,callback):
        self.filename=filename
        self.file_dir=file_dir
        self.callback=callback
        self.width=400
        self.height=200
        super(RenameDialog, self).__init__('<b>'+title+'</b>','',width=self.width,height=self.height,
                                           confirm_name='Ok',cancel_name='Cancel')

        self.spacer=gui.Label('',width=400, height=30)
        self.append_field(self.spacer,key='spacer')

        self.name_field=gui.TextInput(single_line=True,width=self.width-100,height=30)
        self.name_field.set_text(self.filename)
        self.append_field(self.name_field,'name_field')
        


    def confirm_dialog(self):
        new_name=self.get_field('name_field').get_value()
        files_in_dir = os.listdir(self.file_dir)
        if new_name in files_in_dir:
            OKDialog('Rename File','File already exists').show(self._base_app_instance)
            return
        else:
            # print self.file_dir + os.sep+ self.filename
            os.rename(self.file_dir + os.sep+ self.filename,self.file_dir + os.sep + new_name)
            self.hide()
            self.callback()
            


        
class FileManager(AdaptableDialog):
    
    def __init__(self, title, media_dir, is_profile, callback):

        self.title=title
        self.is_profile=is_profile
        self.current_media=media_dir
        root_width= 550
        root_height=500
        self.callback=callback
        self.current_media_name=''

        super(FileManager, self).__init__('<b>'+title+'</b>','',
                                          width=root_width,height=root_height,
                                          cancel_name='Done')
        self.style['display'] = 'block'
        self.style['overflow'] = 'hidden'
        self.style['margin'] = '0px auto'
        
        self._frame=gui.VBox(width=root_width, height=400)

        self.append_field(self._frame,key='frame')

        self.spacer=gui.Label('\n',width=400, height=20)
        self._frame.append(self.spacer,key='spacer')
        
        self.media_list = gui.ListView(width=250, height=300)
        self.media_list.set_on_selection_listener(self.on_media_selected)
        self._frame.append(self.media_list,key='media_list')

        self.buttons_frame= gui.HBox(width=280, height=30)
        self._frame.append(self.buttons_frame,key='buttons_frame')
        
        self.media_name=gui.Label('Selected Item: ',width=400, height=20)
        self._frame.append(self.media_name,key='media_name')

        self.delete_media = gui.Button('Delete',width=80, height=30)
        self.delete_media.set_on_click_listener(self.on_delete_media_button_pressed)
        self.buttons_frame.append(self.delete_media,key='delete_media')
        
        self.rename_media = gui.Button('Rename',width=80, height=30)
        self.rename_media.set_on_click_listener(self.on_rename_media_button_pressed)
        self.buttons_frame.append(self.rename_media,key='rename_media')

        self.deleteall_media = gui.Button('Delete All',width=80, height=30)
        self.deleteall_media.set_on_click_listener(self.on_deleteall_media_button_pressed)
        self.buttons_frame.append(self.deleteall_media,key='deleteall_media')
        
        self.display_media()

     

    def on_refresh_media_pressed(self,widget):
        self.display_media()

    
    def display_media(self):
        self.media_list.empty()
        self.current_media_name=''
        items=sorted(os.listdir(self.current_media))
        i=0
        for item in items:
            if (self.is_profile is False and os.path.isdir(self.current_media+ os.sep+item) is False) or (self.is_profile is True and os.path.isdir(self.current_media+ os.sep+item) is True and os.path.exists(self.current_media+ os.sep + item + os.sep + 'pp_showlist.json') is True):
                obj= gui.ListItem(item,width=200, height=20)
                self.media_list.append(obj,key=i)
                i+=1
        return


    def on_media_selected(self,widget,key):
        self.current_media_name=self.media_list.children[key].get_text()
        self.media_name.set_text('Selected File:   '+ self.current_media_name)


    def cancel_dialog(self):
        self.hide()
        self.callback()

    def on_delete_media_button_pressed(self,widget):
        OKCancelDialog('Delete Item','Delete '+self.current_media_name +'<br>Are you sure?',callback=self.on_delete_media_confirm).show(self._base_app_instance)
        return

    def on_deleteall_media_button_pressed(self,widget):
        OKCancelDialog('DELETE ALL ITEMS','DELETE ALL ITEMS<br>Are you sure?',callback=self.on_deleteall_media_confirm).show(self._base_app_instance)
        return
    
    def on_deleteall_media_confirm(self,result):
        if result is False:
            return
        for item in os.listdir(self.current_media):
            # print self.current_media+os.sep+item
            os.remove(self.current_media+os.sep+item)
        self.display_media()
        


    def on_delete_media_confirm(self,result):
        if result is False:
            return
        # print self.current_media+os.sep+self.current_media_name
        if self.is_profile is True:
            shutil.rmtree(self.current_media+os.sep+self.current_media_name)
        else:
            os.remove(self.current_media+os.sep+self.current_media_name)        
        self.display_media()
        self.media_name.set_text('Selected File:')

    def on_rename_media_button_pressed(self,widget):
        if self.current_media_name=='':
            # second level
            OKDialog('Rename','No File Selected').show(self._base_app_instance )
            return
        # second level
        self.rename_item_dialog=RenameDialog("Rename File",self.current_media,self.current_media_name,self.rename_done)
        self.rename_item_dialog.show(self._base_app_instance )

    def rename_done(self):
        self.display_media()        




    # ******************
    # READ SAVE OPTIONS, used by edit dialogs
    # ******************

class Options(object):

    config=None

    def read_options(self,options_file=None):
        if options_file != None:
            Options.options_file=options_file
            
        """reads options from options file """
        Options.config=ConfigParser.ConfigParser()
        Options.config.read(Options.options_file)
        
        self.config=Options.config
        self.pp_profiles_offset =self.config.get('manager-editable','profiles_offset',0)
        self.media_offset =self.config.get('manager-editable','media_offset',0)
        self.livetracks_offset =self.config.get('manager-editable','livetracks_offset',0)
        self.pp_options = self.config.get('manager-editable','options',0)

        self.pp_home_dir =self.config.get('manager','home',0)
        self.top_dir = self.config.get('manager','import_top',0)
        self.unit=self.config.get('network','unit')

        self.autostart_path=self.config.get('manager-editable','autostart_path')
        self.autostart_options = self.config.get('manager-editable','autostart_options',0)

        self.pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'+self.pp_profiles_offset
        self.media_dir=self.pp_home_dir+self.media_offset
        self.livetracks_dir=self.pp_home_dir+self.livetracks_offset

        self.editor_port= self.config.get('editor','port')
        # self.print_paths()


    def print_paths(self):
        print 'home',self.pp_home_dir
        print 'profiles',self.pp_profiles_offset, self.pp_profiles_dir
        print 'media', self.media_offset, self.media_dir
        print 'livetracks', self.livetracks_offset, self.livetracks_dir
        print 'top',self.top_dir


    def save_options(self):
        """ save the output of the options edit dialog to file"""
        # print 'saved',self.pp_profiles_offset
        self.config.set('manager-editable','media_offset',self.media_offset)
        self.config.set('manager-editable','livetracks_offset',self.livetracks_offset)
        self.config.set('manager-editable','profiles_offset',self.pp_profiles_offset)
        self.config.set('manager-editable','options',self.pp_options)

        self.config.set('manager-editable','autostart_path',self.autostart_path)        
        self.config.set('manager-editable','autostart_options',self.autostart_options)
        
        with open(Options.options_file, 'wb') as config_file:
            self.config.write(config_file)
    
    # ******************
    # EMAIL OPTIONS
    # ******************

class EmailOptionsDialog(AdaptableDialog,Mailer):
    def __init__(self, title='Title', message='Message',callback=None,**kwargs):
        self.callback=callback
        dialog_width=450
        super(EmailOptionsDialog, self).__init__(title='<b>Email Options</b>',message='Edit then click OK or Cancel',
                                                     width=dialog_width,height=500,
                                                     confirm_name='OK',cancel_name='Cancel')
        self.read_config() # no arguemnt because file is read elsewhere
        self.email_allowed_field= gui.TextInput(single_line=True,width=250, height=30)
        email_allowed='yes'if self.email_allowed is True else'no'
        self.email_allowed_field.set_text(email_allowed)
        self.append_field_with_label('Allow Email Alerts',self.email_allowed_field,
                                                       None,width=dialog_width-20,key='email_allowed_field') 

        self.email_to_field= gui.TextInput(single_line=False,width=250, height=90)
        self.email_to_field.set_text(self.email_to)
        self.append_field_with_label('To',self.email_to_field,
                                                       None,width=dialog_width-20,key='email_to_field')

        self.email_with_ip_field= gui.TextInput(single_line=True,width=250, height=30)
        email_with_ip='yes'if self.email_with_ip is True else'no'
        self.email_with_ip_field.set_text(email_with_ip)
        self.append_field_with_label('Email with IP',self.email_with_ip_field,
                                                       None,width=dialog_width-20,key='email_with_ip_field')

        self.email_at_start_field= gui.TextInput(single_line=True,width=250, height=30)
        email_at_start='yes'if self.email_at_start is True else 'no'
        self.email_at_start_field.set_text(email_at_start)
        self.append_field_with_label('Email at Start',self.email_at_start_field,
                                                       None,width=dialog_width-20,key='email_at_start_field')

        self.email_on_error_field= gui.TextInput(single_line=True,width=250, height=30)
        email_on_error='yes' if self.email_on_error is True else 'no'
        self.email_on_error_field.set_text(email_on_error)
        self.append_field_with_label('Email on Error',self.email_on_error_field,
                                                        None,width=dialog_width-20,key='email_on_error_field')
  
        self.email_on_terminate_field= gui.TextInput(single_line=True,width=250, height=30)
        email_on_terminate='yes' if self.email_on_terminate is True else 'no'
        self.email_on_terminate_field.set_text(email_on_terminate)
        self.append_field_with_label('Email on Terminate',self.email_on_terminate_field,
                                                        None,width=dialog_width-20,key='email_on_terminate_field')

        self.log_on_error_field= gui.TextInput(single_line=True,width=250, height=30)
        log_on_error='yes' if self.log_on_error is True else 'no'
        self.log_on_error_field.set_text(log_on_error)
        self.append_field_with_label('Log on Error',self.log_on_error_field,
                                                       None,width=dialog_width-20,key='log_on_error_field')
  

    

    def confirm_dialog(self):
        email_allowed=self.get_field('email_allowed_field').get_value()
        if email_allowed not in ('yes','no'):
            OKDialog('Email Options','Allow Email must be Yes or No').show(self._base_app_instance)
            return
        
        email_to=self.get_field('email_to_field').get_value()

        email_with_ip=self.get_field('email_with_ip_field').get_value()
        if email_with_ip not in ('yes','no'):
            OKDialog('Email Options','Email with IP must be Yes or No').show(self._base_app_instance)
            return

        email_at_start=self.get_field('email_at_start_field').get_value()
        if email_at_start not in ('yes','no'):
            OKDialog('Email Options','Email at Start must be Yes or No').show(self._base_app_instance)
            return

        email_on_error=self.get_field('email_on_error_field').get_value()
        if email_on_error not in ('yes','no'):
            OKDialog('Email Options','Email on Error Start must be Yes or No').show(self._base_app_instance)
            return

        email_on_terminate=self.get_field('email_on_terminate_field').get_value()
        if email_on_terminate not in ('yes','no'):
            OKDialog('Email Options','Email on Terminate must be Yes or No').show(self._base_app_instance)
            return

        log_on_error=self.get_field('log_on_error_field').get_value()
        if log_on_error not in ('yes','no'):
            OKDialog('Email Options','Log on Error must be Yes or No').show(self._base_app_instance)
            return

        # all correct so save
        self.email_allowed = True if email_allowed == 'yes' else False
        self.email_to=email_to
        self.email_with_ip = True if email_with_ip == 'yes' else False
        self.email_at_start = True if email_at_start == 'yes' else False
        self.email_on_error = True if email_on_error == 'yes' else False
        self.email_on_terminate = True if email_on_terminate == 'yes' else False
        self.log_on_error = True if log_on_error == 'yes' else False
        self.save_config()
        self.hide()
        if self.callback!=None:
            self.callback()
        



class AutostartOptionsDialog(AdaptableDialog,Options):
    def __init__(self, pp_home_dir,pp_profiles_dir,title='Title', message='Message',**kwargs):
        self.pp_home_dir = pp_home_dir
        self.pp_profiles_dir = pp_profiles_dir
        dialog_width=450
        super(AutostartOptionsDialog, self).__init__(title='<b>AutostartOptions</b>',message='Edit then click OK or Cancel',
                                                     width=450,height=300,
                                                     confirm_name='Ok',cancel_name='Cancel')           
        self.read_options()
        self.autostart_path_field= gui.TextInput(single_line=True,width=250, height=30)
        self.autostart_path_field.set_text(self.autostart_path)
        self.append_field_with_label('Autostart Profile',self.autostart_path_field,
                                                        None,width=dialog_width-20,key='autostart_path_field')

         
        self.autostart_options_field= gui.TextInput(single_line=True,width=250, height=30)
        self.autostart_options_field.set_text(self.autostart_options)
        self.append_field_with_label('Autostart Options',self.autostart_options_field,
                                                        None,width=dialog_width-20,key='autostart_options_field')



    def confirm_dialog(self):
        result=self.get_field('autostart_path_field').get_value()            
        autostart_profile_path=self.pp_home_dir+os.sep+'pp_profiles'+os.sep+result
        if not os.path.exists(autostart_profile_path):
            OKDialog('Autostart Options','Profile does not exist: ' + autostart_profile_path).show(self._base_app_instance)
            return
        else:
            autostart_path=result

        autostart_options=self.get_field('autostart_options_field').get_value()

        # all OK save the options
        self.autostart_path=autostart_path
        self.autostart_options =autostart_options
        self.save_options()
        self.hide()
        



class ManagerOptionsDialog(AdaptableDialog,Options):
    def __init__(self, pp_home_dir,pp_profiles_dir,title='Title', message='Message',callback=None,**kwargs):

        #parent,text,field,button,width=300,key=''
        dialog_width=450
        super(ManagerOptionsDialog, self).__init__(title='<b>Manager Options</b>',message='Edit then click OK or Cancel',
                                                     width=450,height=300,
                                                     confirm_name='Ok',cancel_name='Cancel')

        self.pp_home_dir = pp_home_dir
        self.pp_profiles_dir = pp_profiles_dir
        self.callback=callback
        
        self.read_options()
        # self.options_manager_dialog.style['background-color'] = 'LightGray'
        self.media_field= gui.TextInput(single_line=True,width=250, height=30)
        self.media_field.set_text(self.media_offset)
        self.append_field_with_label('Media Offset',self.media_field,
                                                        None,width=dialog_width-20,key='media_field')

        self.livetracks_field= gui.TextInput(single_line=True,width=250, height=30)
        self.livetracks_field.set_text(self.livetracks_offset)
        self.append_field_with_label('Live Tracks Offset',self.livetracks_field,
                                                         None,width=dialog_width-20,key='livetracks_field')
        
        self.profiles_field= gui.TextInput(single_line=True,width=250, height=30)
        self.profiles_field.set_text(self.pp_profiles_offset)
        self.append_field_with_label('Profiles Offset',self.profiles_field,
                                                       None,width=dialog_width-20,key='profiles_field')       
        
        self.options_field= gui.TextInput(single_line=True,width=250, height=30)
        self.options_field.set_text(self.pp_options)
        self.append_field_with_label('Pi Presents Options',self.options_field,
                                                       None,width=dialog_width-20,key='options_field')   
      

    def confirm_dialog(self):
        media_offset=self.get_field('media_field').get_value()
        media_dir=self.pp_home_dir+media_offset
        if not os.path.exists(media_dir):
            OKDialog('Manager Options','Media Directory does not exist: ' + media_dir).show(self._base_app_instance)
            return

        livetracks_offset=self.get_field('livetracks_field').get_value()
        livetracks_dir=self.pp_home_dir+livetracks_offset
        if not os.path.exists(livetracks_dir):
            OKDialog('Manager Options','Live Tracks Directory does not exist: ' + livetracks_dir).show(self._base_app_instance)
            return
        
        pp_profiles_offset=self.get_field('profiles_field').get_value()
        pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'+pp_profiles_offset
        if not os.path.exists(pp_profiles_dir):
            OKDialog('Manager Options','Profiles Directory does not exist: ' + pp_profiles_dir).show(self._base_app_instance)
            return

        pp_options=self.get_field('options_field').get_value() 

        # all OK save the options
        self.pp_profiles_offset = pp_profiles_offset
        self.media_offset = media_offset
        self.livetracks_offset = livetracks_offset
        self.pp_options = pp_options

        self.save_options()
        self.hide()
        if self.callback != None:
            self.callback()
        



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
            command = ['python',command, '-r']
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
        elif code==0: return 'Running'
        elif code==100: return 'Normal Exit'
        elif code==101: return 'Terminated'
        elif code==102: return 'Error Detected'
        else: return 'Unknown Code'


    def exit_ed(self):
        pid,user=self.is_ed_running()
        if pid !=-1:
            subprocess.call(['pkill', '-f', '/pipresents/pp_web_editor.py'])
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

    def run_pp(self,command,pp_home,current_profile,pp_options):
        PiPresents.my_pp=None
        pp_home=pp_home[:-8]
        pid,user,running_profile=self.is_pp_running()
        # print pid,user,running_profile
        if pid ==-1:
            options_list= pp_options.split(' ')
            command = ['python',command,'-o',pp_home,'-p',current_profile,'--manager']
            if options_list[0] != '':
                command = command + options_list
            print 'COMMAND',command
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
        elif code==101: return 'Terminated'
        elif code==102: return 'Error Detected'
        else: return 'Unknown Code'


    def exit_pp(self):
        pid,user,running_profile=self.is_pp_running()

        if pid !=-1:
            subprocess.call(['pkill' ,'-f' ,'/pipresents/pipresents.py'])
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

class Autostart(Options,object):

    def autostart(self):
        # get directory holding the code
        self.manager_dir=sys.path[0]
            
        if not os.path.exists(self.manager_dir + os.sep + 'pp_manager.py'):
            print >> sys.stderr, 'Manager: Bad Application Directory'
            exit()

        self.options_file_path=self.manager_dir+os.sep+'pp_config'+os.sep+'pp_web.cfg'
        if not os.path.exists(self.options_file_path):
            print >> sys.stderr, 'Manager: web options file not found'
            exit()

        # read the options
        self.read_options(self.options_file_path)


        # and construct the paths
        self.pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'
        
        #start the Pi Presents Driver
        pp_auto=PiPresents()
        # and initialise its class variables
        pp_auto.init(self.manager_dir)


        if self.autostart_path != '' and os.name !='nt':
            autostart_profile_path= self.pp_home_dir+os.sep+'pp_profiles'+ self.autostart_path
            if False:
            #if not os.path.exists(autostart_profile_path):
                print >> sys.stderr, 'Manager: Autostart Profile does not exist: ' + autostart_profile_path
            else:
                command =self.manager_dir+'/pipresents.py'
                success=pp_auto.run_pp(command,self.pp_home_dir,self.autostart_path,self.autostart_options)
                if success is True:
                    print >> sys.stderr, 'Manager: Auto-Started profile ',autostart_profile_path
                    return self.autostart_path
                else:
                    print >> sys.stderr, 'Manager: FAILED, Pi Presents AUTO Not Started'
                    return ''
        else:
            return ''

        


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
                print >> sys.stderr,'Manager: Failed to connect to email SMTP server ' + str(tries) +  '\n ' +str(error)
                tries +=1
                if tries >5:
                    print >> sys.stderr,'Manager: Failed to connect to email SMTP server after ' + str(tries)
                    return False

    def send_email(mailer,reason,subject,message):
        if try_connect(mailer) is False:
            return False
        else:
            success,error = mailer.send(subject,message)
            if success is False:
                print >> sys.stderr, 'Manager: Failed to send email: ' + str(error)
                success,error=mailer.disconnect()
                if success is False:
                    print >> sys.stderr,'Manager: Failed disconnect after send:' + str(error)
                return False
            else:
                print >> sys.stderr,'Manager: Sent email for ' + reason
                success,error=mailer.disconnect()
                if success is False:
                    print >> sys.stderr,'Manager: Failed disconnect ' + str(error)
                return True


    print >> sys.stderr, '\n *** Pi Presents Manager Started ***'

    # wait for environment variables to stabilize. Required for Jessie autostart
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


    #create upload and download directories if necessary
    upload_dir='/tmp/pipresents/upload'
    download_dir='/tmp/pipresents/download'
    if os.path.exists('/tmp/pipresents'):
        shutil.rmtree('/tmp/pipresents')
    os.makedirs(upload_dir)
    os.makedirs(download_dir)


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
        mailer.read_config(options_file=email_file_path)    
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
    # remi.server.DEBUG_MODE = 0

    # start the web server to serve the Pi Presents Manager App
    start(PPManager,address=ip, port=network.manager_port,
          username=network.manager_username,
          password=network.manager_password,
          multiple_instance=False,enable_file_cache=True,
          update_interval=0.2, start_browser=False,debug=False)





