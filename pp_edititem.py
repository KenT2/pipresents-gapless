from Tkinter import Frame,Button,Label,OptionMenu,Entry,Spinbox,StringVar,Checkbutton,Text,BooleanVar
from Tkinter import END,LEFT,TOP,X,BOTTOM,YES,ACTIVE,RAISED, FLAT,INSERT,DISABLED,N,S,E,W
from tkColorChooser import askcolor
import ttk
import tkFont
import os
import string
import ttkSimpleDialog as ttkSimpleDialog
import tkFileDialog
from ScrolledText import ScrolledText
from pp_utils import Monitor
from tkconversions import *


class FontChooser( ttkSimpleDialog.Dialog ):
    BASIC = 1
    ALL   = 2

    def __init__( self, parent, defaultfont=None, showstyles=None ):
        self._family       = StringVar(  value='Century Schoolbook L')
        self._sizeString   = StringVar(  value='20'          )
        self._weight       = StringVar(  value=tkFont.NORMAL )
        self._slant        = StringVar(  value=tkFont.ROMAN  )
        self._isUnderline  = BooleanVar( value=False         )
        self._isOverstrike = BooleanVar( value=False         )
        if defaultfont:
            self._initialize( defaultfont )

        self._currentFont  = tkFont.Font( font=self.getFontTuple() )

        self._showStyles   = showstyles

        self.sampleText      = None

        ttkSimpleDialog.Dialog.__init__( self, parent, 'Font Chooser' )

    def _initialize( self, aFont ):
        if not isinstance( aFont, tkFont.Font ):
            aFont = tkFont.Font( font=aFont )

        fontOpts = aFont.actual( )

        self._family.set(       fontOpts[ 'family'     ] )
        self._sizeString.set(   fontOpts[ 'size'       ] )
        self._weight.set(       fontOpts[ 'weight'     ] )
        self._slant.set(        fontOpts[ 'slant'      ] )
        self._isUnderline.set(  fontOpts[ 'underline'  ] )
        self._isOverstrike.set( fontOpts[ 'overstrike' ] )

    def body( self, master ):
        theRow = 0

        ttkLabel( master, text="Font Family" ).grid( row=theRow, column=0 )
        ttkLabel( master, text="Font Size" ).grid( row=theRow, column=2 )

        theRow += 1

        # Font Families
        fontList = ttk.Combobox( master,  height=10, textvariable=self._family )
        fontList.grid( row=theRow, column=0, columnspan=2, sticky=N+S+E+W, padx=10 )
        rawfamilyList = list(tkFont.families( ))
        rawfamilyList.sort()
        # print rawfamilyList
        familyList=[]
        for family in rawfamilyList:
            if family[0] == '@':
                continue
            familyList.append(family)
        fontList.configure( values=familyList )
        fontList.bind('<<ComboboxSelected>>', self.selectionChanged)

        # Font Sizes
        sizeList = ttk.Combobox( master,  height=10, width=5, textvariable=self._sizeString )
        sizeList.grid( row=theRow, column=2, columnspan=2, sticky=N+S+E+W, padx=10 )
        sizes=[]
        for size in xrange( 10,50 ):
            sizes.append( str(size) )
        sizeList.configure( values=sizes)
        sizeList.bind('<<ComboboxSelected>>', self.selectionChanged)

        # Styles
        if self._showStyles is not None:
            theRow += 1
            if self._showStyles in ( FontChooser.ALL, FontChooser.BASIC ):
                ttkLabel( master, text='Styles', anchor=W ).grid( row=theRow, column=0, pady=10, sticky=W )

                theRow += 1

                ttkCheckbutton( master, text="bold", command=self.selectionChanged, offvalue='normal', onvalue='bold', variable=self._weight ).grid(row=theRow, column=0)
                ttkCheckbutton( master, text="italic", command=self.selectionChanged, offvalue='roman', onvalue='italic', variable=self._slant ).grid(row=theRow, column=1)

        if self._showStyles == FontChooser.ALL:
            ttkCheckbutton( master, text="underline", command=self.selectionChanged, offvalue=False, onvalue=True, variable=self._isUnderline ).grid(row=theRow, column=2)
            ttkCheckbutton( master, text="overstrike", command=self.selectionChanged, offvalue=False, onvalue=True, variable=self._isOverstrike ).grid(row=theRow, column=3)

        # Sample Text
            theRow += 1

            ttkLabel( master, text='Sample Text', anchor=W ).grid( row=theRow, column=0, pady=10, sticky=W )

            theRow += 1

            self.sampleText = Text( master, height=11, width=70 )
            self.sampleText.insert( INSERT,'ABC...XYZ\nabc....xyz', 'fontStyle' )
            self.sampleText.config( state=DISABLED )
            self.sampleText.tag_config( 'fontStyle', font=self._currentFont )
            self.sampleText.grid( row=theRow, column=0, columnspan=4, padx=10 )

    def apply( self ):
        self.result = self.getFontTuple( )

    def selectionChanged( self, something=None ):
        self._currentFont.configure( family=self._family.get(),
                                     size=self._sizeString.get(),
                                     weight=self._weight.get(),
                                     slant=self._slant.get(),
                                     underline=self._isUnderline.get(),
                                     overstrike=self._isOverstrike.get() )

        if self.sampleText:
            self.sampleText.tag_config( 'fontStyle', font=self._currentFont )

    def getFontString( self ):
        family = self._family.get()
        size   = int(self._sizeString.get())

        styleList = [ ]
        if self._weight.get() == tkFont.BOLD:
            styleList.append( 'bold' )
        if self._slant.get() == tkFont.ITALIC:
            styleList.append( 'italic' )
        if self._isUnderline.get():
            styleList.append( 'underline' )
        if self._isOverstrike.get():
            styleList.append( 'overstrike' )

        if len(styleList) == 0:
            return family+ ' ' + str(size)
        else:
            xx=''
            for x in styleList:
                xx=xx+' '+ x
            return family + ' ' +str(size) +' '+xx

    def getFontTuple( self ):
        family = self._family.get()
        size   = int(self._sizeString.get())

        styleList = [ ]
        if self._weight.get() == tkFont.BOLD:
            styleList.append( 'bold' )
        if self._slant.get() == tkFont.ITALIC:
            styleList.append( 'italic' )
        if self._isUnderline.get():
            styleList.append( 'underline' )
        if self._isOverstrike.get():
            styleList.append( 'overstrike' )

        if len(styleList) == 0:
            return family, size
        else:
            return family, size, ' '.join( styleList )

def askChooseFont( parent, defaultfont=None, showstyles=FontChooser.ALL ):
    return  FontChooser( parent, defaultfont=defaultfont, showstyles=showstyles ).result


__doc__ = info = '''
This script replaces the one written by Sunjay Varma - www.sunjay-varma.com

This script has two main classes:
Tab - Basic tab used by TabBar for main functionality
TabBar - The tab bar that is placed above tab bodies (Tabs), based on ttk.Notebook
'''

# a base tab class
class Tab(ttkFrame):
    def __init__(self, master, name):
        ttkFrame.__init__(self, master)
        self.tab_name = name

# the bulk of the logic is in the actual tab bar
class TabBar(ttk.Notebook):
    
    def __init__(self, master=None, init_name=None):
        ttk.Notebook.__init__(self, master)
        self.tabnames = {}
    
    def show(self):
        self.pack(side=TOP, expand=YES, fill=X)

    def add(self, tab,text):
        self.tabnames[tab.tab_name] = tab   # add it to the list of tabs
        ttk.Notebook.add(self, tab, text=text)

    def delete(self, tabname):
        self.forget(tabnames[tabname])

    def switch_tab(self, name):
        self.select(tabnames[name])


# *************************************
# EDIT SHOW AND TRACK CONTENT
# ************************************

class EditItem(ttkSimpleDialog.Dialog):

    def __init__(self, parent, title, field_content, record_specs,field_specs,show_refs,initial_media_dir,pp_home_dir,initial_tab):
        self.mon=Monitor()
        # save the extra arg to instance variable
        self.field_content = field_content   # dictionary - the track parameters to be edited
        self.record_specs= record_specs # list of field names and seps/tabs in the order that they appear
        self.field_specs=field_specs  # dictionary of specs referenced by field name
        
        self.show_refs=show_refs
        self.show_refs.append('')
        self.initial_media_dir=initial_media_dir
        self.pp_home_dir=pp_home_dir
        self.initial_tab=initial_tab
        
        # list of stringvars from which to get edited values (for optionmenu only??)
        self.entries=[]

        # and call the base class _init_which calls body immeadiately and apply on OK pressed
        ttkSimpleDialog.Dialog.__init__(self, parent, title)

    def body(self,root):
        self.root=root
        bar = TabBar(root, init_name=self.initial_tab)
        self.body_fields(root,bar)
        # bar.config(bd=1, relief=RIDGE)   # add some border
        bar.show()

        
    def body_fields(self, master,bar):
        # get fields for this record using the record type in the loaded record
        record_fields=self.record_specs[self.field_content['type']]
        #print "Generating fields: {0} record_fields for {1}".format(len(record_fields), self.field_content['type'])

        # init results of building the form
        self.tab_row=1 # row on form
        self.fields=[]  # generated by body_fields - list of field objects in record  fields order, not for sep or tab
        self.entries=[]   # generated by body_fields - list of stringvars in record fields order, used option-menus only
        
        # populate the dialog box using the record fields to determine the order
        for field in record_fields:
            #print "BODY_FIELDS: {0}, {1}".format(field, len(record_fields))
            # get list of values where required
            values=[]
            if self.field_specs[field]['shape']in("option-menu",'spinbox'):
                # print 'should be field name', field
                # print 'should be shape',self.field_specs[field]['shape']
                if field in ('sub-show','start-show'):
                    values=self.show_refs                    
                else:
                    values=self.field_specs[field]['values']
            else:
                values=[]
            # make the entry
            obj=self.make_entry(master,field,self.field_specs[field],values,bar)
            if obj is not  None:
                #print "Making entry row {0}: {1}".format(len(self.fields), field, self.field_specs[field])
                self.fields.append(obj)
        return None # No initial focus



    # create an entry in a dialog box
    def make_entry(self,master,field,field_spec,values,bar):
        # print 'make entry',len(self.fields),field,field_spec
        if field_spec['shape']=='tab':
            self.current_tab = Tab(master, field_spec['name'])
            bar.add(self.current_tab,field_spec['text'])
            self.tab_row=1
            return None
        elif field_spec['shape']=='sep':
            ttkLabel(self.current_tab,text='', anchor=W).grid(row=self.tab_row,column=0,sticky=W)
            self.tab_row+=1
            return None

        else:

            # print 'replace param in make entry',field
            # print 'content', field, self.field_content[field]
            # is it in the field content dictionary
            if not field in self.field_content:
                self.mon.log(self,"Value for field not found in opened file: " + field)
                return None
            else:
                # write the label
                ttkLabel(self.current_tab,text=field_spec['text'], anchor=W).grid(row=self.tab_row,column=0,sticky=W)
                
                # make the editable field
                if field_spec['shape']in ('entry','colour','browse','font'):
                    obj=ttkEntry(self.current_tab,width=40,font='arial 11')
                    obj.insert(END,self.field_content[field])
                    
                elif field_spec['shape']=='text':
                    obj=ScrolledText(self.current_tab,height=8,width=40,font='arial 11')
                    obj.insert(END,self.field_content[field])
                    
                elif field_spec['shape']=='spinbox':
                    obj=ttk.Combobox( master,  height=10, textvariable=self._family )
                    obj.grid( row=theRow, column=0, columnspan=2, sticky=N+S+E+W, padx=10 )
                    #obj=Spinbox(self.current_tab,values=values,wrap=True)
                    obj.insert(END,self.field_content[field])
                    
                elif field_spec['shape']=='option-menu': 
                    self.option_val = StringVar(self.current_tab)    
                    self.option_val.set(self.field_content[field])
                    obj = ttkCombobox(self.current_tab, textvariable=self.option_val)
                    obj['values'] = values
                    self.entries.append(self.option_val)
                    
                else:
                    self.mon.log(self,"Uknown shape for: " + field)
                    return None
                
                # Read-only items
                if field_spec['read-only']=='yes':
                    obj.config(state=DISABLED)

                # Required-entry items
                if field_spec['must']=='yes':
                    print "Found 'must' in {0}".format(field)
                    obj.configure(background='lemon chiffon') # reserve pink for validation errors (future)?
                else:
                    obj.configure(background='white')

                obj.grid(row=self.tab_row,column=1,sticky=W)

                # display buttons where required
                if field_spec['shape']=='browse':
                    but=ttkButton(self.current_tab,width=1,height=1,bg='dark grey',command=(lambda o=obj: self.browse(o)))
                    but.grid(row=self.tab_row,column=2,sticky=W)
                    
                elif field_spec['shape']=='colour':
                    but=ttkButton(self.current_tab,width=1,height=1,bg='dark grey',command=(lambda o=obj: self.pick_colour(o)))
                    but.grid(row=self.tab_row,column=2,sticky=W)
                    
                elif field_spec['shape']=='font':
                    but=ttkButton(self.current_tab,width=1,height=1,bg='dark grey',command=(lambda o=obj: self.pick_font(o)))
                    but.grid(row=self.tab_row,column=2,sticky=W)

                self.tab_row+=1    
                return obj


    def apply(self):
        # get list of fields in the record in the same order as the form was generated
        record_fields=self.record_specs[self.field_content['type']]
        
        field_index=0 # index to self.fields - not incremented for tab and sep
        entry_index=0  # index of stringvars for option_menu
        print "-------------------------------------"

        for field in record_fields:
            # print field
            # get the details of this field
            field_spec=self.field_specs[field]
            #print  'reading row',field_index,field_spec['shape']
            
            # and get the value
            if field_spec['shape']not in ('sep','tab'):
                #print "Applying row {0} '{1}' ({2}, {3}). {4} entries".format(field_index, field, self.field_content[field], 
                #    field_spec['shape'], len(self.entries))

                
                if field_spec['shape']=='text':
                    self.field_content[field]=self.fields[field_index].get(1.0,END).rstrip('\n')
                    
                elif field_spec['shape']=='option-menu':
                    self.field_content[field]=self.entries[entry_index].get()
                    entry_index+=1
                else:
                    self.field_content[field]=self.fields[field_index].get().strip()
                    
                # print self.field_content[field]    
                field_index +=1
                
        self.result=True
        return self.result
        


    def pick_colour(self,obj):
        rgb,colour=askcolor()
        # print rgb,colour
        if colour is not None:
            obj.delete(0,END)
            obj.insert(END,colour)
            
    def pick_font(self,obj):
        font=askChooseFont(self.root)
        # print font
        if font is not None:
            obj.delete(0,END)
            obj.insert(END,font)

    def browse(self,obj):
        # print "initial directory ", self.options.initial_media_dir
        file_path=tkFileDialog.askopenfilename(initialdir=self.initial_media_dir, multiple=False)
        if file_path=='':
            return
        file_path=os.path.normpath(file_path)
        # print "file path ", file_path
        relpath = os.path.relpath(file_path,self.pp_home_dir)
        # print "relative path ",relpath
        common = os.path.commonprefix([file_path,self.pp_home_dir])
        # print "common ",common
        if common.endswith("pp_home") is False:
            obj.delete(0,END)
            obj.insert(END,file_path)
        else:
            location = "+" + os.sep + relpath
            location = string.replace(location,'\\','/')
            # print "location ",location
            obj.delete(0,END)
            obj.insert(END,location)

    def enter_keypressed(self, event=None):
        ''' Check what control has focus. If it's not a text widget, close (accept) the window.
            (Enter key is needed by text widget to enter a new line)
            The dropdown widget handles and consumes enter key to close its dropdown (accept).
        '''
        ctl = self.focus_get()
        if isinstance(ctl, Text) or isinstance(ctl, ScrolledText):
            return
        else:
            #return ttkSimpleDialog.Dialog.ok(self, event)
            return self.ok(event)

    def escape_keypressed(self, event=None):
        ''' Check what control has focus. If it's not a text widget, close (cancel) the window.
            (Actually, I'm not sure what the issue is with the text widget with regards to the
            Escape key, so we'll comment out the special handling for now.)
            The dropdown widget handles and consumes escape key to close its dropdown (cancel).
        '''
        #ctl = self.focus_get()
        #if isinstance(ctl, Text) or isinstance(ctl, ScrolledText):
        #    return
        #else:
        #    return self.cancel()
        return self.cancel(event)

    def buttonbox(self):
        '''add modified button box.
        This function was originally here to 'override the standard [buttonbox] to get rid of 
        key bindings which cause trouble with text widget'.
        My opinion (drewkeller) is Escape-to-close and Enter-to-accept are the standard GUI 
        expectations of a dialog like this, so they would be correct.
        Issues with the text widget can be handled in keypress handlers.
        '''
        box = ttkFrame(self)
        w = ttkButton(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = ttkButton(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)
        self.bind("<Return>", self.enter_keypressed)
        self.bind("<Escape>", self.escape_keypressed)
        box.pack()


