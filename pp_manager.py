#! /usr/bin/env python
import remi.gui as gui
from remi import start, App
from remi_plus import OKDialog, OKCancelDialog

import subprocess
import sys, os, shutil
import ConfigParser
import zipfile
from threading import Timer




class PPManager(App):

    def __init__(self, *args):
        super(PPManager, self).__init__(*args)


    def main(self):
        # get directory holding the code
        self.manager_dir=sys.path[0]
            
        if not os.path.exists(self.manager_dir + os.sep + 'pp_manager.py'):
            print 'Pi Presents Manager - Bad Application Directory'
            exit()

        # create an options file if necessary
        self.options_file_path=self.manager_dir+os.sep+'pp_config'+os.sep+'pp_web.cfg'
        if not os.path.exists(self.options_file_path):
            print 'Pi Presents Manager - Cannot find web options file'
            exit()

        # read the options
        self.options_config=self.read_options(self.options_file_path)
        self.get_options(self.options_config)
        # print 'options got'

        #create upload directory if necessary
        self.upload_dir_path=self.pp_home_dir+os.sep+'pp_temp'
        if not os.path.exists(self.upload_dir_path):
            os.makedirs(self.upload_dir_path)

        self.pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'+self.pp_profiles_offset
        if not os.path.exists(self.pp_profiles_dir):
            print 'Profiles directory does not exist: ' + self.pp_profiles_dir
            exit()

        #init variables
        self.profile_objects=[]
        self.current_profile=''

        # Initialise an instance of the Pi Presents and Web Editor driver classes
        self.pp=PiPresents()
        self.ed = WebEditor()


        # root and frames
        root = gui.VBox(width=450,height=600) #10
        top_frame=gui.VBox(width=450,height=40) #1
        middle_frame=gui.VBox(width=450,height=500) #5
        button_frame=gui.HBox(width=250,height=40) #10

        # menu
        menu = gui.Menu(width=430, height=30)
        
        # media menu
        media_menu = gui.MenuItem('Media',width=100, height=30)        
        media_copy_menu = gui.MenuItem('Copy',width=100, height=30)
        media_upload_menu = gui.MenuItem('Upload',width=100, height=30)
        media_copy_menu.set_on_click_listener(self, 'on_media_copy_clicked')
        media_upload_menu.set_on_click_listener(self, 'on_media_upload_clicked')
        
        #profile menu
        profile_menu = gui.MenuItem( 'Profile',width=100, height=30)        
        profile_copy_menu = gui.MenuItem('Copy',width=100, height=30)
        profile_copy_menu.set_on_click_listener(self, 'on_profile_copy_clicked')
        profile_upload_menu = gui.MenuItem('Upload',width=100, height=30)
        profile_upload_menu.set_on_click_listener(self, 'on_profile_upload_clicked')
        profile_download_menu = gui.MenuItem('Download',width=100, height=30)
        profile_download_menu.set_on_click_listener(self, 'on_profile_download_clicked')

        # editor menu
        editor_menu=gui.MenuItem('Editor',width=100,height=30)
        editor_run_menu=gui.MenuItem('Run',width=100,height=30)
        editor_run_menu.set_on_click_listener(self,'on_editor_run_menu_clicked')
        editor_exit_menu=gui.MenuItem('Exit',width=100,height=30)
        editor_exit_menu.set_on_click_listener(self,'on_editor_exit_menu_clicked')  


        #options menu
        options_menu=gui.MenuItem('Options',width=100,height=30)
        options_manager_menu=gui.MenuItem('Manager',width=100,height=30)
        options_manager_menu.set_on_click_listener(self,'on_options_manager_menu_clicked')
        options_autostart_menu=gui.MenuItem('Autostart',width=100,height=30)
        options_autostart_menu.set_on_click_listener(self,'on_options_autostart_menu_clicked')        

        
        # list of profiles
        self.profile_list = gui.ListView(width=300, height=300)
        self.profile_list.set_on_selection_listener(self,'on_profile_selected')

         
        #status and buttons

        self.profile_name = gui.Label('Selected Profile: ',width=400, height=20)
        
        self.pp_state_display = gui.Label('',width=400, height=20)
        
        self.run_pp = gui.Button('Run',width=80, height=30)
        self.run_pp.set_on_click_listener(self, 'on_run_button_pressed')
        
        self.exit_pp = gui.Button('Exit',width=80, height=30)
        self.exit_pp.set_on_click_listener(self, 'on_exit_button_pressed')

        self.refresh = gui.Button('Refresh List',width=120, height=30)
        self.refresh.set_on_click_listener(self, 'on_refresh_pressed')
        
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
        profile_menu.append(profile_copy_menu)
        profile_menu.append(profile_upload_menu)
        profile_menu.append(profile_download_menu)
        
        media_menu.append(media_copy_menu)
        media_menu.append(media_upload_menu)

        editor_menu.append(editor_run_menu)
        editor_menu.append(editor_exit_menu)
        
        options_menu.append(options_manager_menu)
        options_menu.append(options_autostart_menu)

        menu.append(profile_menu)
        menu.append(media_menu)
        menu.append(editor_menu)
        menu.append(options_menu)
        
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
    # OPTIONS
    # ******************


    def read_options(self,options_file):
        """reads options from options file """
        config=ConfigParser.ConfigParser()
        config.read(options_file)
        return config
    

    def get_options(self,config):

        self.pp_profiles_offset =config.get('manager-editable','profiles_offset',0)
        self.media_offset =config.get('manager-editable','media_offset',0)
        self.use_sudo=config.get('manager-editable','use_sudo')
        self.options = config.get('manager-editable','options',0)

        self.pp_home_dir =config.get('manager','home',0)
        self.top_dir = config.get('manager','copy-top',0)
        self.unit=config.get('manager','unit')

        self.autostart_path=config.get('manager-editable','autostart_path')
        self.autostart_use_sudo=config.get('manager-editable','autostart_use_sudo')
        self.autostart_options = config.get('manager-editable','autostart_options',0)

        self.pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'+self.pp_profiles_offset
        if self.use_sudo == 'yes':
            self.sudo=True
        else:
            self.sudo=False
        self.media_dir=self.pp_home_dir+self.media_offset
        # self.print_paths()


    def print_paths(self):
        print 'home',self.pp_home_dir
        print 'profiles',self.pp_profiles_offset, self.pp_profiles_dir
        print 'media', self.media_offset, self.media_dir
        print 'top',self.top_dir



    def save_options(self,config,options_file):
        """ save the output of the options edit dialog to file"""
        
        config.set('manager-editable','media_offset',self.media_offset)
        config.set('manager-editable','profiles_offset',self.pp_profiles_offset)
        config.set('manager-editable','use_sudo',self.use_sudo)
        config.set('manager-editable','options',self.options)

        config.set('manager-editable','autostart_path',self.autostart_path)        
        config.set('manager-editable','autostart_use_sudo',self.autostart_use_sudo)
        config.set('manager-editable','autostart_options',self.autostart_options)
        
        with open(options_file, 'wb') as config_file:
            config.write(config_file)
    


    def on_options_autostart_menu_clicked(self):
        self.options_autostart_dialog=gui.GenericDialog(width=450,height=300,title='Auotstart Options',
                                            message='Edit then click OK or Cancel',autohide_ok=False)
             
        self.autostart_path_field= gui.TextInput(width=250, height=30)
        self.autostart_path_field.set_text(self.autostart_path)
        self.options_autostart_dialog.add_field_with_label('autostart_path_field','Autostart Profile Path',self.autostart_path_field)

        self.autostart_sudo_dropdown = gui.DropDown(width=250, height=30)
        c0 = gui.DropDownItem( 'no',width=100, height=20)
        c1 = gui.DropDownItem( 'yes',width=100, height=20)
        self.autostart_sudo_dropdown.append(c0)
        self.autostart_sudo_dropdown.append(c1)
        self.autostart_sudo_dropdown.set_value(self.autostart_use_sudo)
        self.options_autostart_dialog.add_field_with_label('autostart_sudo_dropdown','Autostart Use SUDO',self.autostart_sudo_dropdown)
        
        self.autostart_options_field= gui.TextInput(width=250, height=30)
        self.autostart_options_field.set_text(self.autostart_options)
        self.options_autostart_dialog.add_field_with_label('autostart_options_field','Autostart Options',self.autostart_options_field)

        self.autostart_error=gui.Label('',width=440,height=30)
        self.options_autostart_dialog.add_field('autostart_error',self.autostart_error)

        self.options_autostart_dialog.set_on_confirm_dialog_listener(self,'on_options_autostart_dialog_confirm')
        self.options_autostart_dialog.show(self)


    def on_options_manager_menu_clicked(self):
        self.options_manager_dialog=gui.GenericDialog(width=450,height=300,title='Manager Options',
                                                      message='Edit then click OK or Cancel',autohide_ok=False)

        self.media_field= gui.TextInput(width=250, height=30)
        self.media_field.set_text(self.media_offset)
        self.media_field.set_on_enter_listener(self,'dummy_enter')
        self.options_manager_dialog.add_field_with_label('media_field','Media Offset',self.media_field)

        self.sudo_dropdown = gui.DropDown(width=250, height=30)
        c0 = gui.DropDownItem('no',width=200,height=20)
        c1 = gui.DropDownItem('yes',width=200, height=20)
        self.sudo_dropdown.append(c0)
        self.sudo_dropdown.append(c1)
        self.sudo_dropdown.set_value(self.use_sudo)
        self.options_manager_dialog.add_field_with_label('sudo_dropdown','Use SUDO',self.sudo_dropdown)
        
        self.profiles_field= gui.TextInput(width=250, height=30)
        self.profiles_field.set_text(self.pp_profiles_offset)
        self.options_manager_dialog.add_field_with_label('profiles_field','Profiles Offset',self.profiles_field)
        
        self.options_field= gui.TextInput(width=250, height=30)
        self.options_field.set_text(self.options)
        self.options_manager_dialog.add_field_with_label('options_field','Pi Presents Options',self.options_field)

        self.options_error=gui.Label('',width=440,height=30)
        self.options_manager_dialog.add_field('options_error',self.options_error)
        
        self.options_manager_dialog.set_on_confirm_dialog_listener(self,'on_options_manager_dialog_confirm')
        self.options_manager_dialog.show(self)


    def dummy_enter(self):
        # fudge to stop enter key making the text disapppear in single line text input
        pass


    def on_options_autostart_dialog_confirm(self):

        result=self.options_autostart_dialog.get_field('autostart_sudo_dropdown').get_value()
        # print 'AUTO SUDO',result
        if result not in ('yes','no'):
            self.autostart_error.set_text('Use SUDO is not yes or no: ' + result)
            return
        else:
            self.autostart_use_sudo=result

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



    def on_options_manager_dialog_confirm(self):

        result=self.options_manager_dialog.get_field('sudo_dropdown').get_value()
        # print 'SUDO',result
        if result not in ('yes','no'):
            self.options_error.set_text('Use SUDO is not yes or no: ' + result)
            return
        else:
            self.use_sudo=result

        media_offset=self.options_manager_dialog.get_field('media_field').get_value()
        media_dir=self.pp_home_dir+media_offset
        if not os.path.exists(media_dir):
            self.options_error.set_text('Media Directory does not exist: ' + media_dir)
            return
        else:
            self.media_offset=media_offset
        
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





    # ******************
    #MEDIA
    # ******************
    
     # copy  
    def on_media_copy_clicked(self):
        fileselectionDialog = gui.FileSelectionDialog('Copy Media', 'Select files to copy',True, self.top_dir)
        fileselectionDialog.set_on_confirm_value_listener(self, 'on_media_copy_dialog_confirm')
        fileselectionDialog.set_on_cancel_dialog_listener(self, 'on_media_copy_dialog_cancel')
        fileselectionDialog.show(self)

    def on_media_copy_dialog_cancel(self):
        self.update_status('Media copy cancelled: ')

    def on_media_copy_dialog_confirm(self, filelist):
        if len(filelist)==0:
            self.update_status('FAILED: Copy Media')
            OKDialog('Copy Media','Error: No file selected').show(self)
            return    
        self.copy_list=filelist
        copy_from1=filelist[0]
        self.copy_to=self.media_dir
        if not copy_from1.startswith(self.top_dir):
            self.update_status('FAILED: Copy Media')
            OKDialog('Copy Media','Error: Access to source prohibited: ' + copy_from1).show(self)
            return
        if not os.path.exists(self.copy_to):
            self.update_status('FAILED: Copy Media')
            OKDialog('Copy Media',' Error: Media directory does not exist: ' + self.copy_to).show(self)
            return

        # print self.copy_list, self.copy_to
        OKCancelDialog('Copy Media','Files will be ovewritten even if newer',self.copy_media_confirm).show(self)

    def copy_media_confirm(self,result):
        if result:
            for item in self.copy_list:
                if os.path.isdir(item):
                    self.update_status('FAILED: Copy Media')
                    OKDialog('Copy Media',' Error: Cannot copy a directory').show(self)
                else:
                    shutil.copy2(item, self.copy_to)
            self.update_status('Media copy sucessful: ')
        else:
            self.update_status('Media copy cancelled: ')


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


    # ******************        
    #PROFILES
    # ******************

    # copy
    def on_profile_copy_clicked(self):
        fileselectionDialog = gui.FileSelectionDialog('Copy Profile', 'Select a Profile to copy',False,self.top_dir)
        fileselectionDialog.set_on_confirm_value_listener(self, 'on_profile_copy_dialog_confirm')
        fileselectionDialog.set_on_cancel_dialog_listener(self, 'on_profile_copy_dialog_cancel')
        fileselectionDialog.show(self)

    def on_profile_copy_dialog_cancel(self):
        self.update_status('Profile copy cancelled: ')

    def on_profile_copy_dialog_confirm(self, filelist):
        if len(filelist)==0:
            self.update_status('FAILED: Copy Profile')
            OKDialog('Copy Profile','Error: No profile selected').show(self)
            return    
        self.copy_from=filelist[0]
        self.from_basename=os.path.basename(self.copy_from)
        self.copy_to=self.pp_profiles_dir+os.sep+self.from_basename
        # print self.copy_from, self.copy_to, self.top_dir
        if not self.copy_from.startswith(self.top_dir):
            self.update_status('FAILED: Copy Profile')
            OKDialog('Copy Profile','Error: Access to source prohibited: ' + self.copy_from).show(self)
            return
        if not os.path.isdir(self.copy_from):
            self.update_status('FAILED: Copy Profile')
            OKDialog('Copy Profile','Error: Source is not a directory: ' + self.copy_from).show(self)
            return
        if not os.path.exists(self.copy_from + os.sep + 'pp_showlist.json'):
            self.update_status('FAILED: Copy Profile')
            OKDialog('Copy Profile','Error: Source is not a profile: ' + self.copy_from).show(self)            
            return
        if os.path.exists(self.copy_to):
            OKCancelDialog('Copy Profile','Profile already exists, overwrite?',self.copy_profile_confirm).show(self)

        else:
            self.copy_profile_confirm(True)


    def copy_profile_confirm(self,result):            
        if result:
            if os.path.exists(self.copy_to):
                shutil.rmtree(self.copy_to)
            # print self.copy_from,self.copy_to
            shutil.copytree(self.copy_from, self.copy_to)
            self.profile_count=self.display_profiles()

            self.update_status('Profile copy successful ')
        else:
            self.update_status('Profile copy cancelled ')


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

    def on_refresh_pressed(self):
        self.display_profiles()

    
    def display_profiles(self):
        self.profile_list.empty()
        items = os.listdir(self.pp_profiles_dir)
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
                self.pp_state_display.set_text('<b>'+self.unit +  ':</b>   RUNNING   '+ profile +' as '+user)   
            else:
                self.pp_state_display.set_text('<b>' +self.unit + ':</b>   STOPPED   (' + self.pp.lookup_state(my_state)+')')
        Timer(0.5,self.display_state).start()  
            


    def on_run_button_pressed(self):
        if os.name== 'nt':
            self.update_status('FAILED, Server on Windows')
            return
        if self.current_profile != '':
            command = self.manager_dir+'/pipresents.py'
            success=self.pp.run_pp(self.sudo,command,self.current_profile,self.options)
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
            # Poll state of Pi Presents
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
        success=self.ed.run_ed(command,self.ed_options)
        if success is True:
            OKDialog('Run Editor','Open new tab to run the editor').show(self)
        else:
            OKDialog('Run Editor','Error: Editor already Running').show(self)


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
# Editor Driver
# ******************
      
class WebEditor(object):
    my_ed=None

    # run when every instance is started
    def __init__(self):
        pass

    # run once when Manager is started
    def init(self):
        WebEditor.my_ed=None
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
        if pid !=-1:
            if user=='root':
                subprocess.call(["./exit_ed.sh","sudo_exit"])
            else:
                subprocess.call(["./exit_ed.sh","exit"])
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

    # run when every instance is started
    def __init__(self):
        pass

    # run once when Manager is started
    def init(self):
        PiPresents.my_pp=None
        pass

    def run_pp(self,sudo,command,current_profile,options):
        PiPresents.my_pp=None
        pid,user,running_profile=self.is_pp_running()
        # print pid,user,running_profile
        if pid ==-1:
            options_list= options.split(' ')
            command = ['python',command,'-p',current_profile,'--manager']
            if sudo is True:
                command=['sudo']+command
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
        if pid !=-1:
            if user=='root':
                subprocess.call(["./exit_pp.sh","sudo_exit"])
            else:
                subprocess.call(["./exit_pp.sh","exit"])
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
            print 'Pi Presents Manager - Bad Application Directory'
            exit()

        self.options_file_path=self.manager_dir+os.sep+'pp_config'+os.sep+'pp_web.cfg'
        if not os.path.exists(self.options_file_path):
            print 'Pi Presents Manager - web options file not found'
            exit()

        # read the options
        config=self.autostart_read_options(self.options_file_path)
        self.autostart_get_options(config)

        # and construct the paths
        self.pp_profiles_dir=self.pp_home_dir+os.sep+'pp_profiles'
        
        #start the Pi Presents Driver
        pp_auto=PiPresents()
        # and initialise its class variables
        pp_auto.init()


        if self.autostart_path != '' and os.name !='nt':
            autostart_profile_path= self.pp_home_dir+os.sep+'pp_profiles'+os.sep+self.autostart_path
            if not os.path.exists(autostart_profile_path):
                print 'Autostart - Profile does not exist: ' + autostart_profile_path
            else:
                command =self.manager_dir+'/pipresents.py'
                success=pp_auto.run_pp(self.sudo,command,self.autostart_path,self.autostart_options)
                if success is True:
                    print 'Pi Presents AUTO Started'
                else:
                    print 'FAILED, Pi Presents AUTO Not Started'

    def autostart_read_options(self,options_file):
        """reads options from options file """
        config=ConfigParser.ConfigParser()
        config.read(options_file)
        return config
    

    def autostart_get_options(self,config):
        self.autostart_path=config.get('manager-editable','autostart_path')
        self.autostart_use_sudo=config.get('manager-editable','autostart_use_sudo')
        self.autostart_options = config.get('manager-editable','autostart_options',0)
        self.pp_home_dir =config.get('manager','home',0)
        
        if self.autostart_use_sudo == 'yes':
            self.sudo=True
        else:
            self.sudo=False
        # self.print_paths()

# ***************************************
# MAIN
# ***************************************

if __name__  ==  "__main__":

    # get directory holding the code
    manager_dir=sys.path[0]

    options_file_path=manager_dir+os.sep+'pp_config'+os.sep+'pp_web.cfg'
    if not os.path.exists(options_file_path):
        print 'Pi Presents Manager - Cannot find Web Options file'
        exit()

    """reads options from options file to interface"""
    config=ConfigParser.ConfigParser()
    config.read(options_file_path)
        
    ip =config.get('network','ip',0)
    port=int(config.get('manager','port',0))
    username=config.get('manager','username',0)
    password=config.get('manager','password',0)
    # print ip

    print 'Pi Presents Manager Started'

    # Autostart Pi Presents if necessary
    auto=Autostart()
    auto.autostart()

    # setting up remi debug level 
    #       2=all debug messages   1=error messages   0=no messages
    import remi.server
    remi.server.DEBUG_MODE = 0

    # start the web server to serve the Pi Presents Manager App
    start(PPManager,address=ip, port=port,username=username,password=password,
          multiple_instance=False,enable_file_cache=True,
          update_interval=0.1, start_browser=False)




