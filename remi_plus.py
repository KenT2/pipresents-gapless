#! /usr/bin/env python
import remi.gui as gui
from remi import start, App

# *****************************************
#  Main page version of add_field_with_label
# *****************************************

def append_with_label(parent,text,field,button,width=300,key=''):
    fields_spacing = 5   #horizontal spacing
    field_height = int(gui.from_pix(field.style['height']))
    field_width = int(gui.from_pix(field.style['width']))
    label = gui.Label(text,width=width-field_width - 3*fields_spacing-20, height=field_height)
    _container = gui.Widget(width=width, height=field_height)
    _container.set_layout_orientation(gui.Widget.LAYOUT_HORIZONTAL)
    _container.style['margin']='4px'
    _container.append(label,key='lbl' + str(key))
    _container.append(field,key='field'+str(key))
    if button is not None:
        _container.append(button,key='button'+str(key))
    parent.append(_container,key=key)


# *****************************************
#  Dialog
# *****************************************

class Dialog(gui.Widget):
    """Dialog widget. It can be customized to create personalized dialog windows.
    """

    @gui.decorate_constructor_parameter_types([])
    def __init__(self,  **kwargs):
        """
        Args:
            kwargs: See Widget.__init__()
        """
        super(Dialog, self).__init__(**kwargs)
        self._base_app_instance = None
        self._old_root_widget = None

        #****************************
        #   _base_app_instance is the App instance stored by the Dialog class
        #   use self.show(self) when showing from an App
        #   use self.show(_base_app_instance) when showing from a dialog
        #****************************

    def show(self, base_app_instance):
        self._base_app_instance = base_app_instance
        self._old_root_widget = self._base_app_instance.root
        self._base_app_instance.set_root_widget(self)

    def hide(self):
        # print '!!!hide called'
        self._base_app_instance.set_root_widget(self._old_root_widget)



class AdaptableDialog(Dialog):

    """
    provides flexibility in the use of the Ok and cancel buttons
    defines a vertical container with optional Ok and Cancel buttons
    Args:
        title (str): The title of the dialog.
        message (str): The message description.
        _name  - If non-blank display confirm or cancel buttons with the provided name
        kwargs: See Widget.__init__()
    """

    EVENT_ONCONFIRM = 'confirm_dialog'
    EVENT_ONCANCEL = 'cancel_dialog'

    @gui.decorate_constructor_parameter_types([str, str,bool,bool,bool,bool,str,str,int])
    def __init__(self, title='', message='',confirm_name='',cancel_name='',frame_height=0,**kwargs):
        """
        Args:
            title (str): The title of the dialog.
            message (str): The message description.
            
            kwargs: See Widget.__init__()
        """
        super(AdaptableDialog, self).__init__(**kwargs)
        self.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)
        self.style['display'] = 'block'
        self.style['overflow'] = 'auto'
        self.style['margin'] = '0px auto'


        
        if len(title) > 0:
            t = gui.Label(title)
            t.add_class('DialogTitle')
            self.append(t)

        if len(message) > 0:
            m = gui.Label('<br>'+message)
            m.style['margin'] = '5px'
            self.append(m)

        # container for user widgets
        if frame_height !=0:
            self._container = gui.Widget(height=frame_height)
        else:
            self._container = gui.Widget()        
        self._container.style['display'] = 'block'
        self._container.style['overflow'] = 'auto'
        self._container.style['margin'] = '5px'
        self._container.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)
        self.append(self._container)

        if cancel_name !='' or confirm_name !='':
            hlay = gui.Widget(height=35)
            hlay.style['display'] = 'block'
            hlay.style['overflow'] = 'visible'


        if confirm_name !='':
            self.conf = gui.Button(confirm_name)
            self.conf.set_size(100, 30)
            self.conf.style['margin'] = '3px'
            self.conf.style['float'] = 'right'
            self.conf.attributes[self.EVENT_ONCLICK] = "sendCallback('%s','%s');" % (self.identifier, self.EVENT_ONCONFIRM)
            hlay.append(self.conf)
            
        if cancel_name != '':
            self.cancel = gui.Button(cancel_name)
            self.cancel.set_size(100, 30)
            self.cancel.style['margin'] = '3px'
            self.cancel.style['float'] = 'right'
            self.cancel.attributes[self.EVENT_ONCLICK] = "sendCallback('%s','%s');" % (self.identifier, self.EVENT_ONCANCEL)
            hlay.append(self.cancel)
            
        if cancel_name !='' or confirm_name !='':
            self.append(hlay)

        self.inputs = {}

        
    def append_field_with_label(self,text,field,button=None,width=300,key=''):
        key = field.identifier if key == '' else key
        self.inputs[key] = field
        label = gui.Label(text)
        label.style['margin'] = '0px 5px'
        label.style['min-width'] = '30%'
        _row = gui.HBox()
        _row.style['justify-content'] = 'space-between'
        _row.style['overflow'] = 'auto'
        _row.style['padding'] = '3px'
        _row.append(label, key='lbl' + key)
        _row.append(self.inputs[key], key=key)
        if button is not None:
            _row.append(button,key='button'+str(key))
        self._container.append(_row,key=key)




    def append_field(self,field,key=''):

        key = field.identifier if key == '' else key
        self.inputs[key] = field
        _row = gui.HBox()
        _row.style['justify-content'] = 'space-between'
        _row.style['overflow'] = 'auto'
        _row.style['padding'] = '3px'
        _row.append(self.inputs[key], key=key)
        self._container.append(_row, key=key)
        

    def get_field(self, key):
        """
        Args:
            key (str): The unique string identifier of the required field.

        Returns:
            Widget field instance added previously with methods GenericDialog.add_field or
            GenericDialog.add_field_with_label.
        """
        return self.inputs[key]
    

    # override these in a subclass if there is a need for a conditional self.hide() or to get the input value

    def confirm_dialog(self):
        """Event generated by the OK button click.
        """
        # print '\nAdaptable Dialog OK - hide'
        self.hide()
        return self.eventManager.propagate(self.EVENT_ONCONFIRM, ())


    def cancel_dialog(self):
        """Event generated by the Cancel button click."""
        # print '\nAdaptable Dialog Cancel - hide'
        self.hide()
        return self.eventManager.propagate(self.EVENT_ONCANCEL, ())
    

    @gui.decorate_set_on_listener("confirm_dialog", "(self,emitter)")
    def set_on_confirm_dialog_listener(self, callback, *userdata):
        """Registers the listener for the GenericDialog.confirm_dialog event.

        Note: The prototype of the listener have to be like my_on_confirm_dialog(self, widget).

        Args:
            callback (function): Callback function pointer.
        """
        self.eventManager.register_listener(self.EVENT_ONCONFIRM, callback, *userdata)


    @gui.decorate_set_on_listener("cancel_dialog", "(self,emitter)")
    def set_on_cancel_dialog_listener(self, callback, *userdata):
        """Registers the listener for the GenericDialog.cancel_dialog event.

        Note: The prototype of the listener have to be like my_on_cancel_dialog(self, widget).

        Args:
            callback (function): Callback function pointer.
        """
        self.eventManager.register_listener(self.EVENT_ONCANCEL, callback, *userdata)


class InputDialog(AdaptableDialog):
    """Input Dialog widget. It can be used to query simple and short textual input to the user.
    The user can confirm or dismiss the dialog with the common buttons Cancel/Ok.
    The Ok button click emits the 'confirm_dialog' event.
    """
    
    def __init__(self, title='Title', message='Message', initial_value='', confirm_name='OK',cancel_name='Cancel',callback=None,**kwargs):
        
        """
        Args:
            title (str): The title of the dialog.
            message (str): The message description.
            initial_value (str): The default content for the TextInput field.
            kwargs: See Widget.__init__()
        """
        super(InputDialog, self).__init__(title, message, confirm_name, cancel_name, **kwargs)
        self.callback=callback
        self.input_text = gui.TextInput()
        self.append_field(self.input_text,'textinput')
        self.input_text.set_text(initial_value)


    def confirm_dialog(self):
        """Event called pressing on OK button.
            overrides confirm_dialog of Adaptable Dialog
        """ 
        result=self.input_text.get_text()
        self.hide()
        if self.callback==None:
            return result
        else:
            self.callback(result)


class FileSelectionDialog(AdaptableDialog):
    """file selection dialog, it opens a new webpage allows the OK/CANCEL functionality
    implementing the "confirm_dialog" and "cancel_dialog" events."""

    def __init__(self, title='File dialog', message='Select files and folders',
                 multiple_selection=True, selection_folder='.',
                 allow_file_selection=True, allow_folder_selection=True,
                 confirm_name='OK',cancel_name='Cancel',callback=None,**kwargs):
        super(FileSelectionDialog, self).__init__(title, message,confirm_name,cancel_name, **kwargs)

        self.callback=callback
        self.style['width'] = '475px'
        self.fileFolderNavigator = gui.FileFolderNavigator(multiple_selection, selection_folder,
                                                       allow_file_selection,
                                                      allow_folder_selection)
        self.append_field(self.fileFolderNavigator,'fileFolderNavigator')


    def confirm_dialog(self):
        #overides Adaptable Dialog
        # print 'file dialog - hide'
        params = self.fileFolderNavigator.get_selection_list()
        # print 'params',params
        self.hide()
        if self.callback==None:
            return params
        else:
            self.callback(params)



class OKCancelDialog(AdaptableDialog):

    def __init__(self, title, text,callback,width=500, height=200):
        self.ok_cancel_callback=callback
        super(OKCancelDialog, self).__init__(width=width, height=height, title='<b>'+title+'</b>', message=text,confirm_name='OK',cancel_name='Cancel')
        self.set_on_confirm_dialog_listener(self.confirm_it)
        self.set_on_cancel_dialog_listener(self.cancel_it)

        
    def confirm_it(self,widget):
        self.ok_cancel_callback(True)


    def cancel_it(self,widget):
        self.ok_cancel_callback(False)

        

class OKDialog(AdaptableDialog):

    def __init__(self, title, message,width=500, height=200):
        super(OKDialog, self).__init__(width=width, height=height, frame_height=height-300,title='<b>'+title+'</b>',
                                       message=message,confirm_name='OK')


class ReportDialog(AdaptableDialog):

    def __init__(self, title):
        self.text=''
        super(ReportDialog, self).__init__(title,'',width=600,height=500,confirm_name='Done')
        self.textb = gui.TextInput(width=550,height=400,single_line=False)
        self.append_field(self.textb,'text')
        # self.set_on_confirm_dialog_listener(self.confirm)


    def confirm_dialog(self):
        # print 'report dialog - hide'
        self.hide()


    def append_line(self,text):
        self.text +=text+'\n'
        self.textb.set_value(self.text)  

#  ****************************************************
# TabView - a framework for a Tabbed Editor
#  ****************************************************

"""
The TabView constucts a container.
The container has a tab bar, tab title and a frame (self.tab_frame).
The tab_frame can contain one of many panels depending on the tab selected
add_tab adds a button to the tab bar, and creates and returns a panel 

"""

class TabView(gui.Widget):
    def __init__(self, frame_width,frame_height,bar_height,**kwargs):
        super(TabView, self).__init__(**kwargs)
        
        self.bar_width=0
        self.bar_height=bar_height
        self.frame_width=frame_width
        self.frame_height=frame_height
        
        self.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)

        
        #dictionary to  lookup panel object given key
        self.panel_obj=dict()
        self.tab_titles=dict()
        
        #tab bar
        self.tab_bar=gui.Widget(width=self.bar_width,height=self.bar_height)
        self.tab_bar.set_layout_orientation(gui.Widget.LAYOUT_HORIZONTAL)


        # frame to which the panel overwriting the previous. needed to make formatting work?

    # Adds a tab to the Tab Bar, constucts a panel and returns the panel's object
    def add_tab(self, w,key,title):
        tab_button = self._tab_button(w, self.bar_height, title,'button',key)
        self.bar_width+=w
        self.tab_bar.append(tab_button,key=key)
        panel_obj=gui.Widget(width=self.frame_width,height=self.frame_height) #0
        panel_obj.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)
        self.panel_obj[key]=panel_obj
        self.tab_titles[key]=title
        # print 'add tab',title,key,panel_obj
        return panel_obj

    def construct_tabview(self):
        # make tab bar as wide as the frame
        if self.bar_width<self.frame_width:
            blank_width=self.frame_width-self.bar_width
            but=gui.Button('',width=blank_width,height=self.bar_height)
            self.tab_bar.append(but,key='xxblank')
            self.bar_width=self.frame_width
            
        self.tab_bar.style['width']=gui.to_pix(self.bar_width)
        self.tab_title=gui.Label('fred',width=self.frame_width-30,height=20)
        self.tab_title.style['margin']='2px'
        
        # frame for the tab panel, different tabs are switched into this frame.
        self.tab_frame=gui.Widget(width=self.frame_width,height=self.frame_height) #0
        self.tab_frame.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)
        
        # add the bar, panels and title to the subclassed Widget
        self.append(self.tab_bar,key='tab_bar')
        self.append(self.tab_title,key='tab_title')
        self.append(self.tab_frame,key='tab_frame')
        self.set_size(self.bar_width,self.frame_height + 100)
        return self

    # only valid after contruct_tabview
    def get_width(self):
        return self.bar_width

    def _tab_button(self,w,h,label,base_name,key):
        # create a button that returns the key to on_click_listener
        but=gui.Button(label,width=w,height=h,key=key)
        but.style['font-weight']= '400'
        but.style['font-size']= '12px'
        but.set_on_click_listener(self.on_tab_button_pressed, key)
        return but


    def on_tab_button_pressed(self,widget,key):
        self.show(key)

    # show a tab, also internal callback for button presses
    def show(self,key):
        panel_obj=self.panel_obj[key]
        # print 'switch tab',key,panel_obj
        self.tab_frame.append(panel_obj,key='tab_frame')
        self.tab_title.set_text('<b>'+self.tab_titles[key]+'</b>')
        



# *****************************************
# Test App to show a TabView in a dialog
# *****************************************

class Tabbed(App):

    def __init__(self, *args):
        super(Tabbed, self).__init__(*args)


    def main(self):

        # trivial main page
        # ********************
        root = gui.VBox(width=600,height=200) #1

        # button 
        button_tabbed_dialog = gui.Button( 'Open Tabbed Editor',width=250, height=30)
        button_tabbed_dialog.set_on_click_listener(self.on_tabbed_dialog_button_clicked)
        root.append(button_tabbed_dialog)

        # and fields in main page    
        self.t1f1_field=gui.Label('Tab1 Field 1: ',width=400,height=30)
        root.append(self.t1f1_field)
        
        self.t2f1_field=gui.Label('Tab2 Field 1: ',width=400,height=30)
        root.append(self.t2f1_field)


        # dialog to contain the TabView
        # ***********************************
        self.tabbed_dialog=AdaptableDialog(width=450,height=300,title='<b>Tabbed Editor</b>',
                                             message='',autohide_ok=False)
        self.tabbed_dialog.set_on_confirm_dialog_listener(self.tabbed_dialog_confirm)

        # construct a Tabview - frame_width,frame_height,bar height
        frame_width=400
        self.tabview=TabView(frame_width,100,30)

        # add tabs - tab width,key,title
        self.panel1=self.tabview.add_tab(100,'tab1','Tab 1')
        self.panel2=self.tabview.add_tab(100,'tab2','Tab 2')

        # and finish building the tabview
        self.tabview.construct_tabview()

        # add some fields to the tab panels
        self.t1field1=gui.TextInput(width=300, height=35)
        self.t1field1.set_text('Content of Tab 1 field 1')
        append_with_label(self.panel1,'Field 1',self.t1field1,None,width=frame_width)
 
        self.t2field1=gui.TextInput(width=250, height=30)
        self.t2field1.set_text('Content of Tab 2 field 1')
        self.panel2.append(self.t2field1)

        # add the tabview to the dialog
        self.tabbed_dialog.append_field(self.tabview,'tab_view')
        
        return root


    def on_tabbed_dialog_button_clicked(self,widget):
        self.tabbed_dialog.show(self)
        self.tabview.show('tab1')


    def tabbed_dialog_confirm(self,widget):
        OKCancelDialog('Tabbed Editor','Really  save the changes',self.conf_continue).show(self)

    def conf_continue(self,result):
        if result is True:
            # print 'dialog confirm'
            result=self.t1field1.get_value()
            self.t1f1_field.set_text('Tab1 Field1: '+result)
            
            result=self.t2field1.get_value()
            self.t2f1_field.set_text('Tab2 Field1: '+result)
            self.tabbed_dialog.hide()
            OKDialog('Tabbed Editor','Saved').show(self)
        else:
            OKDialog('Tabbed Editor','Not Saved').show(self)
           


#
# ***************************************
# MAIN
# ***************************************

if __name__  ==  "__main__":
    # setting up remi debug level 
    #       2=all debug messages   1=error messages   0=no messages
    import remi.server
    remi.server.DEBUG_MODE = 2

    # start the web server to serve the App
    start(Tabbed,address='127.0.0.1', port=8082,
          multiple_instance=False,enable_file_cache=True,
          update_interval=0.1, start_browser=True)
