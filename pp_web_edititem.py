#! /usr/bin/env python

import os
import string
import remi.gui as gui
from remi_plus import TabView, append_with_label, OKDialog, OKCancelDialog,AdaptableDialog,FileSelectionDialog
from pprint import pprint
from pp_utils import calculate_relative_path

# !!! do not use self.container in dialog sub-classes


# *************************************
# EDIT SHOW AND TRACK CONTENT
# ************************************

class WebEditItem(AdaptableDialog):
    
    def __init__(self, title, field_content, record_specs,field_specs,show_refs,initial_media_dir,
                        pp_home_dir,pp_profile_dir,initial_tab,callback):

        self.callback=callback
        self.frame_width=800   # frame for 2 columns
        self.col_width=400     # width of a column
        self.field_width= 200  # width of data field, label must fit in col_width-field_width- 15
        self.fields_height=300
        self.rows_in_col=15
        self.tab_height=100
        self.okcancel_height=100


        super(WebEditItem, self).__init__('<b>'+title+'</b>','',width=self.frame_width+700,height=self.fields_height+self.tab_height+self.okcancel_height,
                                          confirm_name='OK',cancel_name='Cancel')

        self.field_content = field_content   # dictionary - the track parameters to be edited and returned
                                                                 # key is field name e.g. omx-window
        self.record_specs= record_specs  # list of field names and seps/tabs in the order that they appear
        self.field_specs=field_specs          # dictionary of specs referenced by field name
        
        self.show_refs=show_refs            # used for droppdown of list of shows
        self.show_refs.append('')
        
        self.initial_media_dir=initial_media_dir
        self.pp_home_dir=pp_home_dir
        self.pp_profile_dir=pp_profile_dir
        self.initial_tab=initial_tab


        # create a Tabbed Editor
        self.tabview= TabView(self.frame_width,self.fields_height,30)


        # tabs are created dynamically from pp_definitions.py
        # get fields for this record using the record type in the loaded record
        record_fields=self.record_specs[self.field_content['type']]

        # init results of building the form
        self.tab_row=1 # row on form
        self.field_objs=[]  # list of field objects in record fields order, not for sep or tab
        self.field_index=0 # index to self.field_objs incremented after each field except tab and sep
                                        # can be used as an index to self.field_objs and self.button_objs
        self.button_objs=[]   # list of button objects in record field order , not for sep or tab =None for non-buttons
        
        self.col_row=0
        self.current_col=None
        self.col_1=None
        # populate the dialog box using the record fields to determine the order
        for field in record_fields:
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
            obj,button=self.make_entry(field,self.field_specs[field],values)
            if obj is not  None:
                self.field_objs.append(obj)
                self.button_objs.append(button)
                self.field_index +=1

        #construct the tabview
        self.tabview.construct_tabview()
        
        # frame for tabbed editor
        self.root_frame = gui.HBox(width=self.tabview.get_width() + 100, height=self.fields_height+self.tab_height) #1
        self.root_frame.append(self.tabview,key='switch')
        self.append_field(self.root_frame,'cont')

        #adjust width of dialog box
        self.style['width']=gui.to_pix(self.tabview.get_width() + 100)
         
        return None

    def show_tab(self,key):
        self.tabview.show(key)      


    # create an entry in an editor panel
    def make_entry(self,field,field_spec,values):
        # print 'make entry',self.field_index,field,field_spec
        if self.col_row >= self.rows_in_col:
            self.current_col=self.col_1
        
        # print 'make entry',self.col_row, self.current_col        
        
        if field_spec['shape']=='tab':
            width=len(field_spec['text'])*8+4
            self.current_tab = self.tabview.add_tab(width,field_spec['name'],field_spec['text'])
            # print 'make tab', field_spec['name']
            self.current_tab.set_layout_orientation(gui.Widget.LAYOUT_HORIZONTAL)
            self.col_0=gui.Widget(width=self.frame_width/2) #0
            self.col_0.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)
            self.col_1=gui.Widget(width=self.frame_width/2) #0
            self.col_1.set_layout_orientation(gui.Widget.LAYOUT_VERTICAL)

            self.current_tab.append(self.col_0,key='col_0')
            self.current_tab.append(self.col_1,key='col_1')

            self.current_col=self.col_0
            self.col_row=1
            # print '\nNEW TAB',self.col_row
            self.tab_row=1
            return None,None
        
        elif field_spec['shape']=='sep':
            self.current_col.append(gui.Label('',width=self.field_width,height=10))
            self.tab_row+=1
            self.col_row+=1
            return None,None

        else:

            # print 'replace param in make entry',field
            # print 'content', field, self.field_content[field]
            # is it in the field content dictionary
            if not field in self.field_content:
                print "Value for field not found in opened file: " + field
                return None,None
            else:

                # bodge  - assumes only type is read only
                if field_spec['read-only']=='yes':
                    obj=(gui.Label(self.field_content[field],width=self.field_width,height=20))
                    obj.style['font-weight']='bold'

                
                elif field_spec['shape']in ('entry','browse','font','colour'):
                    obj=gui.TextInput(single_line=True,width=self.field_width,height=20)
                    obj.set_value(self.field_content[field])
                    
                elif field_spec['shape']=='text':
                    obj=gui.TextInput(width=self.field_width,height=110,single_line=False)
                    obj.set_value(self.field_content[field])
                    # extra lines
                    self.col_row+=5

                elif field_spec['shape']=='spinbox':
                    print 'spinbox not implemented'
                    return None,None

                    
                elif field_spec['shape']=='option-menu':
                    obj=gui.DropDown(width=self.field_width,height=25)
                    for key, value in enumerate(values):
                        item=gui.DropDownItem(value,width=self.field_width,height=25)
                        obj.append(item, key=key)
                    content=self.field_content[field]
                    if self.field_content[field] not in values:
                        obj.style['color'] = 'red'
                        content=values[0]
                    obj.set_value(content)
                    # print self.field_content[field],obj.get_value(),values


                else:
                    print"Uknown shape for: " + field
                    return None,None
                
                # create buttons where required
                if field_spec['shape']=='browse':
                    button=self.browse_button(20,20,'','browse_button',self.field_index,field_spec['text'])
                    
                elif field_spec['shape']=='colour':
                    if ColourMap().exists(self.field_content[field]) is True:
                        colour=ColourMap().lookup(self.field_content[field])
                    else:
                        colour=self.field_content[field]
                    button= gui.ColorPicker(colour,width=20, height=20)
                    button.set_on_change_listener(self.color_picker_changed)
                    
                else:
                    button=None

                append_with_label(self.current_col,field_spec['text'],obj,button,width=self.col_width)
                self.tab_row+=1
                self.col_row+=1
                return obj,button

    def confirm_dialog(self):
        # OK button is pressed so update the field values in the profile
        # self.field_content - dictionary - the track parameters to be edited and returned
        # key is field name e.g. omx-window
                                                                     
        # get list of fields in the record in the same order as the form was generated
        record_fields=self.record_specs[self.field_content['type']]
        
        field_index=0 # index to self.field_objs - not incremented for tab and sep

        for field in record_fields:
            # get the details of this field
            field_spec=self.field_specs[field]
            #print  'reading row',field_index,field_spec['shape']
            
            # and get the value
            if field_spec['shape']not in ('sep','tab'):

                #bodge for type which is a label
                if field_spec['read-only']=='yes':
                    self.field_content[field]=self.field_objs[field_index].get_text().strip()

                # get result of button from button and also put it in field
                elif field_spec['shape'] in ('colour'):
                    # button is actually a color picker
                    self.field_content[field]=self.button_objs[field_index].get_value().strip()
                    self.field_objs[field_index].set_value(self.field_content[field])

                else:
                    self.field_content[field]=str(self.field_objs[field_index].get_value()).strip()
                    # print field_spec['shape'],field_spec['text']+':  ',self.field_content[field]

                    
                # print field_spec['shape'],field_spec['text']+':  ',self.field_content[field]    
                field_index +=1
        # print 'edit item hide'
        self.hide()
        self.callback()



# browse button

    def browse_button(self,w,h,label,base_name,field_index,title):
        # create a button that returns the key to on_click_listener
        bname=base_name+str(field_index)
        but=gui.Button(label,width=w,height=h)
        # f = lambda  _bname=field_index: self.open_fileselection_dialog( _bname)
        # fname='self.'+base_name+'_' + str(field_index)
        # setattr(self, fname, f)
        but.set_on_click_listener(self.open_fileselection_dialog,field_index,title)
        return but


    def open_fileselection_dialog(self,widget,browse_field_index,title):
        self.browse_field_index=browse_field_index
        self.file_dialog=FileSelectionDialog(title,'Select File',False, self.initial_media_dir,callback=self.on_fileselection_dialog_callback)
        self.file_dialog.show(self._base_app_instance)
    

    def on_fileselection_dialog_callback(self,flist):
        # a list() of filenames and folders is returned
        if len(flist)==0:
            OKDialog('Select File','nothing selected').show(self._base_app_instance)
            return
        file_path=os.path.normpath(flist[0])
        # print "file path ", file_path

        result=calculate_relative_path(file_path,self.pp_home_dir,self.pp_profile_dir)
        self.field_objs[self.browse_field_index].set_value(result)
        

        
# colour picker

    def color_picker_changed(self,widget,result):
        self.update_colour_fields()
        # print 'colour picked',result


    def update_colour_fields(self):
        # copy result of colour picker into the text field
        record_fields=self.record_specs[self.field_content['type']]
        field_index=0 # index to self.field_objs - not incremented for tab and sep
        for field in record_fields:
            field_spec=self.field_specs[field]
            if field_spec['shape']not in ('sep','tab'):
                if field_spec['shape'] in ('colour'):
                    self.field_objs[field_index].set_value(self.button_objs[field_index].get_value())
                field_index +=1


# ****************************************************
# convert colour string to hex rgb string
# ****************************************************

class ColourMap(object):

    def init(self):

        ColourMap.colour_map=dict(snow='#fffafa',ghostwhite='#f8f8ff',whitesmoke='#f5f5f5',gainsboro='#dcdcdc',
            floralwhite='#fffaf0',oldlace='#fdf5e6',linen='#faf0e6',antiquewhite='#faebd7',
            papayawhip='#ffefd5',blanchedalmond='#ffebcd',bisque='#ffe4c4',peachpuff='#ffdab9',
            navajowhite='#ffdead',moccasin='#ffe4b5',cornsilk='#fff8dc',ivory='#fffff0',
            lemonchiffon='#fffacd',seashell='#fff5ee',honeydew='#f0fff0',mintcream='#f5fffa',
            azure='#f0ffff',aliceblue='#f0f8ff',lavender='#e6e6fa',lavenderblush='#fff0f5',
            mistyrose='#ffe4e1',white='#ffffff',black='#000000',darkslategray='#2f4f4f',
            dimgray='#696969',slategray='#708090',lightslategray='#778899',gray='#bebebe',
            lightgray='#d3d3d3',midnightblue='#191970',navy='#000080',navyblue='#000080',
            cornflowerblue='#6495ed',darkslateblue='#483d8b',slateblue='#6a5acd',mediumslateblue='#7b68ee',
            lightslateblue='#8470ff',mediumblue='#0000cd',royalblue='#4169e1',blue='#0000ff',
            dodgerblue='#1e90ff',deepskyblue='#00bfff',skyblue='#87ceeb',lightskyblue='#87cefa',
            steelblue='#4682b4',lightsteelblue='#b0c4de',lightblue='#add8e6',powderblue='#b0e0e6',
            paleturquoise='#afeeee',darkturquoise='#00ced1',mediumturquoise='#48d1cc',turquoise='#40e0d0',
            cyan='#00ffff',lightcyan='#e0ffff',cadetblue='#5f9ea0',mediumaquamarine='#66cdaa')
        
        dict1=dict(aquamarine='#7fffd4',darkgreen='#006400',darkolivegreen='#556b2f',darkseagreen='#8fbc8f',
                seagreen='#2e8b57',mediumseagreen='#3cb371',lightseagreen='#20b2aa',palegreen='#98fb98',
                springgreen='#00ff7f',lawngreen='#7cfc00',green='#00ff00',chartreuse='#7fff00',
                mediumspringgreen='#00fa9a',greenyellow='#adff2f',limegreen='#32cd32',yellowgreen='#9acd32',
                forestgreen='#228b22',olivedrab='#6b8e23',darkkhaki='#bdb76b',khaki='#f0e68c',
                palegoldenrod='#eee8aa',lightgoldenrodyellow='#fafad2',lightyellow='#ffffe0',yellow='#ffff00',
                gold='#ffd700',lightgoldenrod='#eedd82',goldenrod='#daa520',darkgoldenrod='#b8860b',
                rosybrown='#bc8f8f',indianred='#cd5c5c',saddlebrown='#8b4513',sienna='#a0522d',
                peru='#cd853f',burlywood='#deb887',beige='#f5f5dc',wheat='#f5deb3',
                sandybrown='#f4a460',tan='#d2b48c',chocolate='#d2691e',firebrick='#b22222',
                brown='#a52a2a',darksalmon='#e9967a',salmon='#fa8072',lightsalmon='#ffa07a',
                orange='#ffa500',darkorange='#ff8c00',coral='#ff7f50',lightcoral='#f08080',
                tomato='#ff6347',orangered='#ff4500',red='#ff0000',hotpink='#ff69b4',
                deeppink='#ff1493',pink='#ffc0cb',lightpink='#ffb6c1',palevioletred='#db7093',
                maroon='#b03060',mediumvioletred='#c71585',violetred='#d02090',magenta='#ff00ff',
                violet='#ee82ee',plum='#dda0dd',orchid='#da70d6',mediumorchid='#ba55d3',
                darkorchid='#9932cc',darkviolet='#9400d3',blueviolet='#8a2be2',purple='#a020f0',
                mediumpurple='#9370db',thistle='#d8bfd8',snow1='#fffafa',snow2='#eee9e9')
        ColourMap.colour_map.update(dict1)
        

        dict2=dict(snow3='#cdc9c9',snow4='#8b8989',seashell1='#fff5ee',seashell2='#eee5de',
                seashell3='#cdc5bf',seashell4='#8b8682',antiquewhite1='#ffefdb',antiquewhite2='#eedfcc',
                antiquewhite3='#cdc0b0',antiquewhite4='#8b8378',bisque1='#ffe4c4',bisque2='#eed5b7',
                bisque3='#cdb79e',bisque4='#8b7d6b',peachpuff1='#ffdab9',peachpuff2='#eecbad',
                peachpuff3='#cdaf95',peachpuff4='#8b7765',navajowhite1='#ffdead',navajowhite2='#eecfa1',
                navajowhite3='#cdb38b',navajowhite4='#8b795e',lemonchiffon1='#fffacd',lemonchiffon2='#eee9bf',
                lemonchiffon3='#cdc9a5',lemonchiffon4='#8b8970',cornsilk1='#fff8dc',cornsilk2='#eee8cd',
                cornsilk3='#cdc8b1',cornsilk4='#8b8878',ivory1='#fffff0',ivory2='#eeeee0',
                ivory3='#cdcdc1',ivory4='#8b8b83',honeydew1='#f0fff0',honeydew2='#e0eee0',
                honeydew3='#c1cdc1',honeydew4='#838b83',lavenderblush1='#fff0f5',lavenderblush2='#eee0e5',
                lavenderblush3='#cdc1c5',lavenderblush4='#8b8386',mistyrose1='#ffe4e1',mistyrose2='#eed5d2',
                mistyrose3='#cdb7b5',mistyrose4='#8b7d7b',azure1='#f0ffff',azure2='#e0eeee',
                azure3='#c1cdcd',azure4='#838b8b',slateblue1='#836fff',slateblue2='#7a67ee',
                slateblue3='#6959cd',slateblue4='#473c8b',royalblue1='#4876ff',royalblue2='#436eee',
                royalblue3='#3a5fcd',royalblue4='#27408b',blue1='#0000ff',blue2='#0000ee',
                blue3='#0000cd',blue4='#00008b',dodgerblue1='#1e90ff',dodgerblue2='#1c86ee',
                dodgerblue3='#1874cd',dodgerblue4='#104e8b',steelblue1='#63b8ff',steelblue2='#5cacee',
                steelblue3='#4f94cd',steelblue4='#36648b',deepskyblue1='#00bfff',deepskyblue2='#00b2ee')

        ColourMap.colour_map.update(dict2)

        dict3 = dict (deepskyblue3='#009acd',deepskyblue4='#00688b',skyblue1='#87ceff',skyblue2='#7ec0ee',
                skyblue3='#6ca6cd',skyblue4='#4a708b',lightskyblue1='#b0e2ff',lightskyblue2='#a4d3ee',
                lightskyblue3='#8db6cd',lightskyblue4='#607b8b',slategray1='#c6e2ff',slategray2='#b9d3ee',
                slategray3='#9fb6cd',slategray4='#6c7b8b',lightsteelblue1='#cae1ff',lightsteelblue2='#bcd2ee',
                lightsteelblue3='#a2b5cd',lightsteelblue4='#6e7b8b',lightblue1='#bfefff',lightblue2='#b2dfee',
                lightblue3='#9ac0cd',lightblue4='#68838b',lightcyan1='#e0ffff',lightcyan2='#d1eeee',
                lightcyan3='#b4cdcd',lightcyan4='#7a8b8b',paleturquoise1='#bbffff',paleturquoise2='#aeeeee',
                paleturquoise3='#96cdcd',paleturquoise4='#668b8b',cadetblue1='#98f5ff',cadetblue2='#8ee5ee',
                cadetblue3='#7ac5cd',cadetblue4='#53868b',turquoise1='#00f5ff',turquoise2='#00e5ee',
                turquoise3='#00c5cd',turquoise4='#00868b',cyan1='#00ffff',cyan2='#00eeee',
                cyan3='#00cdcd',cyan4='#008b8b',darkslategray1='#97ffff',darkslategray2='#8deeee',
                darkslategray3='#79cdcd',darkslategray4='#528b8b',aquamarine1='#7fffd4',aquamarine2='#76eec6',
                aquamarine3='#66cdaa',aquamarine4='#458b74',darkseagreen1='#c1ffc1',darkseagreen2='#b4eeb4',
                darkseagreen3='#9bcd9b',darkseagreen4='#698b69',seagreen1='#54ff9f',seagreen2='#4eee94',
                seagreen3='#43cd80',seagreen4='#2e8b57',palegreen1='#9aff9a',palegreen2='#90ee90',
                palegreen3='#7ccd7c',palegreen4='#548b54',springgreen1='#00ff7f',springgreen2='#00ee76',
                springgreen3='#00cd66',springgreen4='#008b45',green1='#00ff00',green2='#00ee00')

        ColourMap.colour_map.update(dict3)

        
                 
        dict3a=dict(green3='#00cd00',green4='#008b00',chartreuse1='#7fff00',chartreuse2='#76ee00',
            chartreuse3='#66cd00',chartreuse4='#458b00',olivedrab1='#c0ff3e',olivedrab2='#b3ee3a',
            olivedrab3='#9acd32',olivedrab4='#698b22',darkolivegreen1='#caff70',darkolivegreen2='#bcee68',
            darkolivegreen3='#a2cd5a',darkolivegreen4='#6e8b3d',khaki1='#fff68f',khaki2='#eee685',
            khaki3='#cdc673',khaki4='#8b864e',lightgoldenrod1='#ffec8b',lightgoldenrod2='#eedc82',
            lightgoldenrod3='#cdbe70',lightgoldenrod4='#8b814c',lightyellow1='#ffffe0',lightyellow2='#eeeed1',
            lightyellow3='#cdcdb4',lightyellow4='#8b8b7a',yellow1='#ffff00',yellow2='#eeee00',
            yellow3='#cdcd00',yellow4='#8b8b00',gold1='#ffd700',gold2='#eec900',
            gold3='#cdad00',gold4='#8b7500',goldenrod1='#ffc125',goldenrod2='#eeb422',
            goldenrod3='#cd9b1d',goldenrod4='#8b6914',darkgoldenrod1='#ffb90f',darkgoldenrod2='#eead0e',
            darkgoldenrod3='#cd950c',darkgoldenrod4='#8b6508',rosybrown1='#ffc1c1',rosybrown2='#eeb4b4',
            rosybrown3='#cd9b9b',rosybrown4='#8b6969',indianred1='#ff6a6a',indianred2='#ee6363',
            indianred3='#cd5555',indianred4='#8b3a3a',sienna1='#ff8247',sienna2='#ee7942',
            sienna3='#cd6839',sienna4='#8b4726',burlywood1='#ffd39b',burlywood2='#eec591',
            burlywood3='#cdaa7d',burlywood4='#8b7355',wheat1='#ffe7ba',wheat2='#eed8ae')

        ColourMap.colour_map.update(dict3a)

        
              
        dict4=dict(wheat3='#cdba96',wheat4='#8b7e66',tan1='#ffa54f',tan2='#ee9a49',
                tan3='#cd853f',tan4='#8b5a2b',chocolate1='#ff7f24',chocolate2='#ee7621',
                chocolate3='#cd661d',chocolate4='#8b4513',firebrick1='#ff3030',firebrick2='#ee2c2c',
                firebrick3='#cd2626',firebrick4='#8b1a1a',brown1='#ff4040',brown2='#ee3b3b',
                brown3='#cd3333',brown4='#8b2323',salmon1='#ff8c69',salmon2='#ee8262',
                salmon3='#cd7054',salmon4='#8b4c39',lightsalmon1='#ffa07a',lightsalmon2='#ee9572',
                lightsalmon3='#cd8162',lightsalmon4='#8b5742',orange1='#ffa500',orange2='#ee9a00',
                orange3='#cd8500',orange4='#8b5a00',darkorange1='#ff7f00',darkorange2='#ee7600',
                darkorange3='#cd6600',darkorange4='#8b4500',coral1='#ff7256',coral2='#ee6a50',
                coral3='#cd5b45',coral4='#8b3e2f',tomato1='#ff6347',tomato2='#ee5c42',
                tomato3='#cd4f39',tomato4='#8b3626',orangered1='#ff4500',orangered2='#ee4000',
                orangered3='#cd3700',orangered4='#8b2500',red1='#ff0000',red2='#ee0000',
                red3='#cd0000',red4='#8b0000',deeppink1='#ff1493',deeppink2='#ee1289',
                deeppink3='#cd1076',deeppink4='#8b0a50',hotpink1='#ff6eb4',hotpink2='#ee6aa7',
                hotpink3='#cd6090',hotpink4='#8b3a62',pink1='#ffb5c5',pink2='#eea9b8')

        ColourMap.colour_map.update(dict4)

        
           
        dict5=dict(pink3='#cd919e',pink4='#8b636c',lightpink1='#ffaeb9',lightpink2='#eea2ad',
                lightpink3='#cd8c95',lightpink4='#8b5f65',palevioletred1='#ff82ab',palevioletred2='#ee799f',
                palevioletred3='#cd6889',palevioletred4='#8b475d',maroon1='#ff34b3',maroon2='#ee30a7',
                maroon3='#cd2990',maroon4='#8b1c62',violetred1='#ff3e96',violetred2='#ee3a8c',
                violetred3='#cd3278',violetred4='#8b2252',magenta1='#ff00ff',magenta2='#ee00ee',
                magenta3='#cd00cd',magenta4='#8b008b',orchid1='#ff83fa',orchid2='#ee7ae9',
                orchid3='#cd69c9',orchid4='#8b4789',plum1='#ffbbff',plum2='#eeaeee',
                plum3='#cd96cd',plum4='#8b668b',mediumorchid1='#e066ff',mediumorchid2='#d15fee',
                mediumorchid3='#b452cd',mediumorchid4='#7a378b',darkorchid1='#bf3eff',darkorchid2='#b23aee',
                darkorchid3='#9a32cd',darkorchid4='#68228b',purple1='#9b30ff',purple2='#912cee',
                purple3='#7d26cd',purple4='#551a8b',mediumpurple1='#ab82ff',mediumpurple2='#9f79ee',
                mediumpurple3='#8968cd',mediumpurple4='#5d478b',thistle1='#ffe1ff',thistle2='#eed2ee',
                thistle3='#cdb5cd',thistle4='#8b7b8b',gray0='#000000',gray1='#030303')
           
        ColourMap.colour_map.update(dict5)
        

        dict6=dict(gray2='#050505',gray3='#080808',gray4='#0a0a0a',gray5='#0d0d0d',
                gray6='#0f0f0f',gray7='#121212',gray8='#141414',gray9='#171717',
                gray10='#1a1a1a',gray11='#1c1c1c',gray12='#1f1f1f',gray13='#212121',
                gray14='#242424',gray15='#262626',gray16='#292929',gray17='#2b2b2b',
                gray18='#2e2e2e',gray19='#303030',gray20='#333333',gray21='#363636',
                gray22='#383838',gray23='#3b3b3b',gray24='#3d3d3d',gray25='#404040',
                gray26='#424242',gray27='#454545',gray28='#474747',gray29='#4a4a4a',
                gray30='#4d4d4d',gray31='#4f4f4f',gray32='#525252',gray33='#545454',
                gray34='#575757',gray35='#595959',gray36='#5c5c5c',gray37='#5e5e5e',
                gray38='#616161',gray39='#636363',gray40='#666666',gray41='#696969',
                gray42='#6b6b6b',gray43='#6e6e6e',gray44='#707070',gray45='#737373',
                gray46='#757575',gray47='#787878',gray48='#7a7a7a',gray49='#7d7d7d',
                gray50='#7f7f7f',gray51='#828282',gray52='#858585',gray53='#878787',
                gray54='#8a8a8a',gray55='#8c8c8c',gray56='#8f8f8f',gray57='#919191',
                gray58='#949494',gray59='#969696',gray60='#999999',gray61='#9c9c9c',
                gray62='#9e9e9e',gray63='#a1a1a1',gray64='#a3a3a3',gray65='#a6a6a6',
                gray66='#a8a8a8',gray67='#ababab',gray68='#adadad',gray69='#b0b0b0',
                gray70='#b3b3b3',gray71='#b5b5b5',gray72='#b8b8b8',gray73='#bababa',
                gray74='#bdbdbd',gray75='#bfbfbf',gray76='#c2c2c2',gray77='#c4c4c4',
                gray78='#c7c7c7',gray79='#c9c9c9',gray80='#cccccc',gray81='#cfcfcf',
                gray82='#d1d1d1',gray83='#d4d4d4',gray84='#d6d6d6',gray85='#d9d9d9',
                gray86='#dbdbdb',gray87='#dedede',gray88='#e0e0e0',gray89='#e3e3e3',
                gray90='#e5e5e5',gray91='#e8e8e8',gray92='#ebebeb',gray93='#ededed',
                gray94='#f0f0f0',gray95='#f2f2f2',gray96='#f5f5f5',gray97='#f7f7f7',
                gray98='#fafafa',gray99='#fcfcfc',gray100='#ffffff',darkgray='#a9a9a9',
                darkblue='#00008b',darkcyan='#008b8b',darkmagenta='#8b008b',darkred='#8b0000',
                lightgreen='#90ee90' )
           
        ColourMap.colour_map.update(dict6)


    def lookup ( self, colour_name ):
        return ColourMap.colour_map[colour_name.lower()]

    def exists(self,colour_name):
        return ColourMap.colour_map.has_key(colour_name)

# ****************************************************
# one off conversion of COLOURS to dictionary source - used offline
# dictionary needs splitting into chunks before use.
# ****************************************************

    COLOURS  =  [
      '\xFF\xFA\xFAsnow',               '\xF8\xF8\xFFGhostWhite',
      '\xF5\xF5\xF5WhiteSmoke',         '\xDC\xDC\xDCgainsboro',
      '\xFF\xFA\xF0FloralWhite',        '\xFD\xF5\xE6OldLace',
      '\xFA\xF0\xE6linen',              '\xFA\xEB\xD7AntiqueWhite',
      '\xFF\xEF\xD5PapayaWhip',         '\xFF\xEB\xCDBlanchedAlmond',
      '\xFF\xE4\xC4bisque',             '\xFF\xDA\xB9PeachPuff',
      '\xFF\xDE\xADNavajoWhite',        '\xFF\xE4\xB5moccasin',
      '\xFF\xF8\xDCcornsilk',           '\xFF\xFF\xF0ivory',
      '\xFF\xFA\xCDLemonChiffon',       '\xFF\xF5\xEEseashell',
      '\xF0\xFF\xF0honeydew',           '\xF5\xFF\xFAMintCream',
      '\xF0\xFF\xFFazure',              '\xF0\xF8\xFFAliceBlue',
      '\xE6\xE6\xFAlavender',           '\xFF\xF0\xF5LavenderBlush',
      '\xFF\xE4\xE1MistyRose',          '\xFF\xFF\xFFwhite',
      '\x00\x00\x00black',              '\x2F\x4F\x4FDarkSlateGray',
      '\x69\x69\x69DimGray',            '\x70\x80\x90SlateGray',
      '\x77\x88\x99LightSlateGray',     '\xBE\xBE\xBEgray',
      '\xD3\xD3\xD3LightGray',          '\x19\x19\x70MidnightBlue',
      '\x00\x00\x80navy',               '\x00\x00\x80NavyBlue',
      '\x64\x95\xEDCornflowerBlue',     '\x48\x3D\x8BDarkSlateBlue',
      '\x6A\x5A\xCDSlateBlue',          '\x7B\x68\xEEMediumSlateBlue',
      '\x84\x70\xFFLightSlateBlue',     '\x00\x00\xCDMediumBlue',
      '\x41\x69\xE1RoyalBlue',          '\x00\x00\xFFblue',
      '\x1E\x90\xFFDodgerBlue',         '\x00\xBF\xFFDeepSkyBlue',
      '\x87\xCE\xEBSkyBlue',            '\x87\xCE\xFALightSkyBlue',
      '\x46\x82\xB4SteelBlue',          '\xB0\xC4\xDELightSteelBlue',
      '\xAD\xD8\xE6LightBlue',          '\xB0\xE0\xE6PowderBlue',
      '\xAF\xEE\xEEPaleTurquoise',      '\x00\xCE\xD1DarkTurquoise',
      '\x48\xD1\xCCMediumTurquoise',    '\x40\xE0\xD0turquoise',
      '\x00\xFF\xFFcyan',               '\xE0\xFF\xFFLightCyan',
      '\x5F\x9E\xA0CadetBlue',          '\x66\xCD\xAAMediumAquamarine',
      '\x7F\xFF\xD4aquamarine',         '\x00\x64\x00DarkGreen',
      '\x55\x6B\x2FDarkOliveGreen',     '\x8F\xBC\x8FDarkSeaGreen',
      '\x2E\x8B\x57SeaGreen',           '\x3C\xB3\x71MediumSeaGreen',
      '\x20\xB2\xAALightSeaGreen',      '\x98\xFB\x98PaleGreen',
      '\x00\xFF\x7FSpringGreen',        '\x7C\xFC\x00LawnGreen',
      '\x00\xFF\x00green',              '\x7F\xFF\x00chartreuse',
      '\x00\xFA\x9AMediumSpringGreen',  '\xAD\xFF\x2FGreenYellow',
      '\x32\xCD\x32LimeGreen',          '\x9A\xCD\x32YellowGreen',
      '\x22\x8B\x22ForestGreen',        '\x6B\x8E\x23OliveDrab',
      '\xBD\xB7\x6BDarkKhaki',          '\xF0\xE6\x8Ckhaki',
      '\xEE\xE8\xAAPaleGoldenrod',
      '\xFA\xFA\xD2LightGoldenrodYellow',
      '\xFF\xFF\xE0LightYellow',        '\xFF\xFF\x00yellow',
      '\xFF\xD7\x00gold',               '\xEE\xDD\x82LightGoldenrod',
      '\xDA\xA5\x20goldenrod',          '\xB8\x86\x0BDarkGoldenrod',
      '\xBC\x8F\x8FRosyBrown',          '\xCD\x5C\x5CIndianRed',
      '\x8B\x45\x13SaddleBrown',        '\xA0\x52\x2Dsienna',
      '\xCD\x85\x3Fperu',               '\xDE\xB8\x87burlywood',
      '\xF5\xF5\xDCbeige',              '\xF5\xDE\xB3wheat',
      '\xF4\xA4\x60SandyBrown',         '\xD2\xB4\x8Ctan',
      '\xD2\x69\x1Echocolate',          '\xB2\x22\x22firebrick',
      '\xA5\x2A\x2Abrown',              '\xE9\x96\x7ADarkSalmon',
      '\xFA\x80\x72salmon',             '\xFF\xA0\x7ALightSalmon',
      '\xFF\xA5\x00orange',             '\xFF\x8C\x00DarkOrange',
      '\xFF\x7F\x50coral',              '\xF0\x80\x80LightCoral',
      '\xFF\x63\x47tomato',             '\xFF\x45\x00OrangeRed',
      '\xFF\x00\x00red',                '\xFF\x69\xB4HotPink',
      '\xFF\x14\x93DeepPink',           '\xFF\xC0\xCBpink',
      '\xFF\xB6\xC1LightPink',          '\xDB\x70\x93PaleVioletRed',
      '\xB0\x30\x60maroon',             '\xC7\x15\x85MediumVioletRed',
      '\xD0\x20\x90VioletRed',          '\xFF\x00\xFFmagenta',
      '\xEE\x82\xEEviolet',             '\xDD\xA0\xDDplum',
      '\xDA\x70\xD6orchid',             '\xBA\x55\xD3MediumOrchid',
      '\x99\x32\xCCDarkOrchid',         '\x94\x00\xD3DarkViolet',
      '\x8A\x2B\xE2BlueViolet',         '\xA0\x20\xF0purple',
      '\x93\x70\xDBMediumPurple',       '\xD8\xBF\xD8thistle',
      '\xFF\xFA\xFAsnow1',              '\xEE\xE9\xE9snow2',
      '\xCD\xC9\xC9snow3',              '\x8B\x89\x89snow4',
      '\xFF\xF5\xEEseashell1',          '\xEE\xE5\xDEseashell2',
      '\xCD\xC5\xBFseashell3',          '\x8B\x86\x82seashell4',
      '\xFF\xEF\xDBAntiqueWhite1',      '\xEE\xDF\xCCAntiqueWhite2',
      '\xCD\xC0\xB0AntiqueWhite3',      '\x8B\x83\x78AntiqueWhite4',
      '\xFF\xE4\xC4bisque1',            '\xEE\xD5\xB7bisque2',
      '\xCD\xB7\x9Ebisque3',            '\x8B\x7D\x6Bbisque4',
      '\xFF\xDA\xB9PeachPuff1',         '\xEE\xCB\xADPeachPuff2',
      '\xCD\xAF\x95PeachPuff3',         '\x8B\x77\x65PeachPuff4',
      '\xFF\xDE\xADNavajoWhite1',       '\xEE\xCF\xA1NavajoWhite2',
      '\xCD\xB3\x8BNavajoWhite3',       '\x8B\x79\x5ENavajoWhite4',
      '\xFF\xFA\xCDLemonChiffon1',      '\xEE\xE9\xBFLemonChiffon2',
      '\xCD\xC9\xA5LemonChiffon3',      '\x8B\x89\x70LemonChiffon4',
      '\xFF\xF8\xDCcornsilk1',          '\xEE\xE8\xCDcornsilk2',
      '\xCD\xC8\xB1cornsilk3',          '\x8B\x88\x78cornsilk4',
      '\xFF\xFF\xF0ivory1',             '\xEE\xEE\xE0ivory2',
      '\xCD\xCD\xC1ivory3',             '\x8B\x8B\x83ivory4',
      '\xF0\xFF\xF0honeydew1',          '\xE0\xEE\xE0honeydew2',
      '\xC1\xCD\xC1honeydew3',          '\x83\x8B\x83honeydew4',
      '\xFF\xF0\xF5LavenderBlush1',     '\xEE\xE0\xE5LavenderBlush2',
      '\xCD\xC1\xC5LavenderBlush3',     '\x8B\x83\x86LavenderBlush4',
      '\xFF\xE4\xE1MistyRose1',         '\xEE\xD5\xD2MistyRose2',
      '\xCD\xB7\xB5MistyRose3',         '\x8B\x7D\x7BMistyRose4',
      '\xF0\xFF\xFFazure1',             '\xE0\xEE\xEEazure2',
      '\xC1\xCD\xCDazure3',             '\x83\x8B\x8Bazure4',
      '\x83\x6F\xFFSlateBlue1',         '\x7A\x67\xEESlateBlue2',
      '\x69\x59\xCDSlateBlue3',         '\x47\x3C\x8BSlateBlue4',
      '\x48\x76\xFFRoyalBlue1',         '\x43\x6E\xEERoyalBlue2',
      '\x3A\x5F\xCDRoyalBlue3',         '\x27\x40\x8BRoyalBlue4',
      '\x00\x00\xFFblue1',              '\x00\x00\xEEblue2',
      '\x00\x00\xCDblue3',              '\x00\x00\x8Bblue4',
      '\x1E\x90\xFFDodgerBlue1',        '\x1C\x86\xEEDodgerBlue2',
      '\x18\x74\xCDDodgerBlue3',        '\x10\x4E\x8BDodgerBlue4',
      '\x63\xB8\xFFSteelBlue1',         '\x5C\xAC\xEESteelBlue2',
      '\x4F\x94\xCDSteelBlue3',         '\x36\x64\x8BSteelBlue4',
      '\x00\xBF\xFFDeepSkyBlue1',       '\x00\xB2\xEEDeepSkyBlue2',
      '\x00\x9A\xCDDeepSkyBlue3',       '\x00\x68\x8BDeepSkyBlue4',
      '\x87\xCE\xFFSkyBlue1',           '\x7E\xC0\xEESkyBlue2',
      '\x6C\xA6\xCDSkyBlue3',           '\x4A\x70\x8BSkyBlue4',
      '\xB0\xE2\xFFLightSkyBlue1',      '\xA4\xD3\xEELightSkyBlue2',
      '\x8D\xB6\xCDLightSkyBlue3',      '\x60\x7B\x8BLightSkyBlue4',
      '\xC6\xE2\xFFSlateGray1',         '\xB9\xD3\xEESlateGray2',
      '\x9F\xB6\xCDSlateGray3',         '\x6C\x7B\x8BSlateGray4',
      '\xCA\xE1\xFFLightSteelBlue1',    '\xBC\xD2\xEELightSteelBlue2',
      '\xA2\xB5\xCDLightSteelBlue3',    '\x6E\x7B\x8BLightSteelBlue4',
      '\xBF\xEF\xFFLightBlue1',         '\xB2\xDF\xEELightBlue2',
      '\x9A\xC0\xCDLightBlue3',         '\x68\x83\x8BLightBlue4',
      '\xE0\xFF\xFFLightCyan1',         '\xD1\xEE\xEELightCyan2',
      '\xB4\xCD\xCDLightCyan3',         '\x7A\x8B\x8BLightCyan4',
      '\xBB\xFF\xFFPaleTurquoise1',     '\xAE\xEE\xEEPaleTurquoise2',
      '\x96\xCD\xCDPaleTurquoise3',     '\x66\x8B\x8BPaleTurquoise4',
      '\x98\xF5\xFFCadetBlue1',         '\x8E\xE5\xEECadetBlue2',
      '\x7A\xC5\xCDCadetBlue3',         '\x53\x86\x8BCadetBlue4',
      '\x00\xF5\xFFturquoise1',         '\x00\xE5\xEEturquoise2',
      '\x00\xC5\xCDturquoise3',         '\x00\x86\x8Bturquoise4',
      '\x00\xFF\xFFcyan1',              '\x00\xEE\xEEcyan2',
      '\x00\xCD\xCDcyan3',              '\x00\x8B\x8Bcyan4',
      '\x97\xFF\xFFDarkSlateGray1',     '\x8D\xEE\xEEDarkSlateGray2',
      '\x79\xCD\xCDDarkSlateGray3',     '\x52\x8B\x8BDarkSlateGray4',
      '\x7F\xFF\xD4aquamarine1',        '\x76\xEE\xC6aquamarine2',
      '\x66\xCD\xAAaquamarine3',        '\x45\x8B\x74aquamarine4',
      '\xC1\xFF\xC1DarkSeaGreen1',      '\xB4\xEE\xB4DarkSeaGreen2',
      '\x9B\xCD\x9BDarkSeaGreen3',      '\x69\x8B\x69DarkSeaGreen4',
      '\x54\xFF\x9FSeaGreen1',          '\x4E\xEE\x94SeaGreen2',
      '\x43\xCD\x80SeaGreen3',          '\x2E\x8B\x57SeaGreen4',
      '\x9A\xFF\x9APaleGreen1',         '\x90\xEE\x90PaleGreen2',
      '\x7C\xCD\x7CPaleGreen3',         '\x54\x8B\x54PaleGreen4',
      '\x00\xFF\x7FSpringGreen1',       '\x00\xEE\x76SpringGreen2',
      '\x00\xCD\x66SpringGreen3',       '\x00\x8B\x45SpringGreen4',
      '\x00\xFF\x00green1',             '\x00\xEE\x00green2',
      '\x00\xCD\x00green3',             '\x00\x8B\x00green4',
      '\x7F\xFF\x00chartreuse1',        '\x76\xEE\x00chartreuse2',
      '\x66\xCD\x00chartreuse3',        '\x45\x8B\x00chartreuse4',
      '\xC0\xFF\x3EOliveDrab1',         '\xB3\xEE\x3AOliveDrab2',
      '\x9A\xCD\x32OliveDrab3',         '\x69\x8B\x22OliveDrab4',
      '\xCA\xFF\x70DarkOliveGreen1',    '\xBC\xEE\x68DarkOliveGreen2',
      '\xA2\xCD\x5ADarkOliveGreen3',    '\x6E\x8B\x3DDarkOliveGreen4',
      '\xFF\xF6\x8Fkhaki1',             '\xEE\xE6\x85khaki2',
      '\xCD\xC6\x73khaki3',             '\x8B\x86\x4Ekhaki4',
      '\xFF\xEC\x8BLightGoldenrod1',    '\xEE\xDC\x82LightGoldenrod2',
      '\xCD\xBE\x70LightGoldenrod3',    '\x8B\x81\x4CLightGoldenrod4',
      '\xFF\xFF\xE0LightYellow1',       '\xEE\xEE\xD1LightYellow2',
      '\xCD\xCD\xB4LightYellow3',       '\x8B\x8B\x7ALightYellow4',
      '\xFF\xFF\x00yellow1',            '\xEE\xEE\x00yellow2',
      '\xCD\xCD\x00yellow3',            '\x8B\x8B\x00yellow4',
      '\xFF\xD7\x00gold1',              '\xEE\xC9\x00gold2',
      '\xCD\xAD\x00gold3',              '\x8B\x75\x00gold4',
      '\xFF\xC1\x25goldenrod1',         '\xEE\xB4\x22goldenrod2',
      '\xCD\x9B\x1Dgoldenrod3',         '\x8B\x69\x14goldenrod4',
      '\xFF\xB9\x0FDarkGoldenrod1',     '\xEE\xAD\x0EDarkGoldenrod2',
      '\xCD\x95\x0CDarkGoldenrod3',     '\x8B\x65\x08DarkGoldenrod4',
      '\xFF\xC1\xC1RosyBrown1',         '\xEE\xB4\xB4RosyBrown2',
      '\xCD\x9B\x9BRosyBrown3',         '\x8B\x69\x69RosyBrown4',
      '\xFF\x6A\x6AIndianRed1',         '\xEE\x63\x63IndianRed2',
      '\xCD\x55\x55IndianRed3',         '\x8B\x3A\x3AIndianRed4',
      '\xFF\x82\x47sienna1',            '\xEE\x79\x42sienna2',
      '\xCD\x68\x39sienna3',            '\x8B\x47\x26sienna4',
      '\xFF\xD3\x9Bburlywood1',         '\xEE\xC5\x91burlywood2',
      '\xCD\xAA\x7Dburlywood3',         '\x8B\x73\x55burlywood4',
      '\xFF\xE7\xBAwheat1',             '\xEE\xD8\xAEwheat2',
      '\xCD\xBA\x96wheat3',             '\x8B\x7E\x66wheat4',
      '\xFF\xA5\x4Ftan1',               '\xEE\x9A\x49tan2',
      '\xCD\x85\x3Ftan3',               '\x8B\x5A\x2Btan4',
      '\xFF\x7F\x24chocolate1',         '\xEE\x76\x21chocolate2',
      '\xCD\x66\x1Dchocolate3',         '\x8B\x45\x13chocolate4',
      '\xFF\x30\x30firebrick1',         '\xEE\x2C\x2Cfirebrick2',
      '\xCD\x26\x26firebrick3',         '\x8B\x1A\x1Afirebrick4',
      '\xFF\x40\x40brown1',             '\xEE\x3B\x3Bbrown2',
      '\xCD\x33\x33brown3',             '\x8B\x23\x23brown4',
      '\xFF\x8C\x69salmon1',            '\xEE\x82\x62salmon2',
      '\xCD\x70\x54salmon3',            '\x8B\x4C\x39salmon4',
      '\xFF\xA0\x7ALightSalmon1',       '\xEE\x95\x72LightSalmon2',
      '\xCD\x81\x62LightSalmon3',       '\x8B\x57\x42LightSalmon4',
      '\xFF\xA5\x00orange1',            '\xEE\x9A\x00orange2',
      '\xCD\x85\x00orange3',            '\x8B\x5A\x00orange4',
      '\xFF\x7F\x00DarkOrange1',        '\xEE\x76\x00DarkOrange2',
      '\xCD\x66\x00DarkOrange3',        '\x8B\x45\x00DarkOrange4',
      '\xFF\x72\x56coral1',             '\xEE\x6A\x50coral2',
      '\xCD\x5B\x45coral3',             '\x8B\x3E\x2Fcoral4',
      '\xFF\x63\x47tomato1',            '\xEE\x5C\x42tomato2',
      '\xCD\x4F\x39tomato3',            '\x8B\x36\x26tomato4',
      '\xFF\x45\x00OrangeRed1',         '\xEE\x40\x00OrangeRed2',
      '\xCD\x37\x00OrangeRed3',         '\x8B\x25\x00OrangeRed4',
      '\xFF\x00\x00red1',               '\xEE\x00\x00red2',
      '\xCD\x00\x00red3',               '\x8B\x00\x00red4',
      '\xFF\x14\x93DeepPink1',          '\xEE\x12\x89DeepPink2',
      '\xCD\x10\x76DeepPink3',          '\x8B\x0A\x50DeepPink4',
      '\xFF\x6E\xB4HotPink1',           '\xEE\x6A\xA7HotPink2',
      '\xCD\x60\x90HotPink3',           '\x8B\x3A\x62HotPink4',
      '\xFF\xB5\xC5pink1',              '\xEE\xA9\xB8pink2',
      '\xCD\x91\x9Epink3',              '\x8B\x63\x6Cpink4',
      '\xFF\xAE\xB9LightPink1',         '\xEE\xA2\xADLightPink2',
      '\xCD\x8C\x95LightPink3',         '\x8B\x5F\x65LightPink4',
      '\xFF\x82\xABPaleVioletRed1',     '\xEE\x79\x9FPaleVioletRed2',
      '\xCD\x68\x89PaleVioletRed3',     '\x8B\x47\x5DPaleVioletRed4',
      '\xFF\x34\xB3maroon1',            '\xEE\x30\xA7maroon2',
      '\xCD\x29\x90maroon3',            '\x8B\x1C\x62maroon4',
      '\xFF\x3E\x96VioletRed1',         '\xEE\x3A\x8CVioletRed2',
      '\xCD\x32\x78VioletRed3',         '\x8B\x22\x52VioletRed4',
      '\xFF\x00\xFFmagenta1',           '\xEE\x00\xEEmagenta2',
      '\xCD\x00\xCDmagenta3',           '\x8B\x00\x8Bmagenta4',
      '\xFF\x83\xFAorchid1',            '\xEE\x7A\xE9orchid2',
      '\xCD\x69\xC9orchid3',            '\x8B\x47\x89orchid4',
      '\xFF\xBB\xFFplum1',              '\xEE\xAE\xEEplum2',
      '\xCD\x96\xCDplum3',              '\x8B\x66\x8Bplum4',
      '\xE0\x66\xFFMediumOrchid1',      '\xD1\x5F\xEEMediumOrchid2',
      '\xB4\x52\xCDMediumOrchid3',      '\x7A\x37\x8BMediumOrchid4',
      '\xBF\x3E\xFFDarkOrchid1',        '\xB2\x3A\xEEDarkOrchid2',
      '\x9A\x32\xCDDarkOrchid3',        '\x68\x22\x8BDarkOrchid4',
      '\x9B\x30\xFFpurple1',            '\x91\x2C\xEEpurple2',
      '\x7D\x26\xCDpurple3',            '\x55\x1A\x8Bpurple4',
      '\xAB\x82\xFFMediumPurple1',      '\x9F\x79\xEEMediumPurple2',
      '\x89\x68\xCDMediumPurple3',      '\x5D\x47\x8BMediumPurple4',
      '\xFF\xE1\xFFthistle1',           '\xEE\xD2\xEEthistle2',
      '\xCD\xB5\xCDthistle3',           '\x8B\x7B\x8Bthistle4',
      '\x00\x00\x00gray0',              '\x03\x03\x03gray1',
      '\x05\x05\x05gray2',              '\x08\x08\x08gray3',
      '\x0A\x0A\x0Agray4',              '\x0D\x0D\x0Dgray5',
      '\x0F\x0F\x0Fgray6',              '\x12\x12\x12gray7',
      '\x14\x14\x14gray8',              '\x17\x17\x17gray9',
      '\x1A\x1A\x1Agray10',             '\x1C\x1C\x1Cgray11',
      '\x1F\x1F\x1Fgray12',             '\x21\x21\x21gray13',
      '\x24\x24\x24gray14',             '\x26\x26\x26gray15',
      '\x29\x29\x29gray16',             '\x2B\x2B\x2Bgray17',
      '\x2E\x2E\x2Egray18',             '\x30\x30\x30gray19',
      '\x33\x33\x33gray20',             '\x36\x36\x36gray21',
      '\x38\x38\x38gray22',             '\x3B\x3B\x3Bgray23',
      '\x3D\x3D\x3Dgray24',             '\x40\x40\x40gray25',
      '\x42\x42\x42gray26',             '\x45\x45\x45gray27',
      '\x47\x47\x47gray28',             '\x4A\x4A\x4Agray29',
      '\x4D\x4D\x4Dgray30',             '\x4F\x4F\x4Fgray31',
      '\x52\x52\x52gray32',             '\x54\x54\x54gray33',
      '\x57\x57\x57gray34',             '\x59\x59\x59gray35',
      '\x5C\x5C\x5Cgray36',             '\x5E\x5E\x5Egray37',
      '\x61\x61\x61gray38',             '\x63\x63\x63gray39',
      '\x66\x66\x66gray40',             '\x69\x69\x69gray41',
      '\x6B\x6B\x6Bgray42',             '\x6E\x6E\x6Egray43',
      '\x70\x70\x70gray44',             '\x73\x73\x73gray45',
      '\x75\x75\x75gray46',             '\x78\x78\x78gray47',
      '\x7A\x7A\x7Agray48',             '\x7D\x7D\x7Dgray49',
      '\x7F\x7F\x7Fgray50',             '\x82\x82\x82gray51',
      '\x85\x85\x85gray52',             '\x87\x87\x87gray53',
      '\x8A\x8A\x8Agray54',             '\x8C\x8C\x8Cgray55',
      '\x8F\x8F\x8Fgray56',             '\x91\x91\x91gray57',
      '\x94\x94\x94gray58',             '\x96\x96\x96gray59',
      '\x99\x99\x99gray60',             '\x9C\x9C\x9Cgray61',
      '\x9E\x9E\x9Egray62',             '\xA1\xA1\xA1gray63',
      '\xA3\xA3\xA3gray64',             '\xA6\xA6\xA6gray65',
      '\xA8\xA8\xA8gray66',             '\xAB\xAB\xABgray67',
      '\xAD\xAD\xADgray68',             '\xB0\xB0\xB0gray69',
      '\xB3\xB3\xB3gray70',             '\xB5\xB5\xB5gray71',
      '\xB8\xB8\xB8gray72',             '\xBA\xBA\xBAgray73',
      '\xBD\xBD\xBDgray74',             '\xBF\xBF\xBFgray75',
      '\xC2\xC2\xC2gray76',             '\xC4\xC4\xC4gray77',
      '\xC7\xC7\xC7gray78',             '\xC9\xC9\xC9gray79',
      '\xCC\xCC\xCCgray80',             '\xCF\xCF\xCFgray81',
      '\xD1\xD1\xD1gray82',             '\xD4\xD4\xD4gray83',
      '\xD6\xD6\xD6gray84',             '\xD9\xD9\xD9gray85',
      '\xDB\xDB\xDBgray86',             '\xDE\xDE\xDEgray87',
      '\xE0\xE0\xE0gray88',             '\xE3\xE3\xE3gray89',
      '\xE5\xE5\xE5gray90',             '\xE8\xE8\xE8gray91',
      '\xEB\xEB\xEBgray92',             '\xED\xED\xEDgray93',
      '\xF0\xF0\xF0gray94',             '\xF2\xF2\xF2gray95',
      '\xF5\xF5\xF5gray96',             '\xF7\xF7\xF7gray97',
      '\xFA\xFA\xFAgray98',             '\xFC\xFC\xFCgray99',
      '\xFF\xFF\xFFgray100',            '\xA9\xA9\xA9DarkGray',
      '\x00\x00\x8BDarkBlue',           '\x00\x8B\x8BDarkCyan',
      '\x8B\x00\x8BDarkMagenta',        '\x8B\x00\x00DarkRed',
      '\x90\xEE\x90LightGreen' ]
    
    def convert(self):

        def twodigithex( number ):
            return '%02x' % number

        with open('C:\Users\Ken\Documents\Develop\colors.txt', 'wb') as colour:
            colour.write('dict(')
            
            # convert colours
            count=0
            for  index in range ( len ( ColourMap.COLOURS ) ):
                colorString  =  ColourMap.COLOURS [ index ]
                red    =  ord ( colorString[0] ) <<8/256
                green  =  ord ( colorString[1] ) <<8/256
                blue   =  ord ( colorString[2] ) <<8/256
                colour_name  =  colorString[3:].lower()
                print red,green,blue, type(red)
                
                code='#'+twodigithex(red)+twodigithex(green)+twodigithex(blue)
                colour.write(colour_name)
                colour.write("='")
                colour.write(code)
                colour.write("',")
                print red,green,blue,colour_name,code
                count+=1
                if count==4:
                    count=0
                    colour.write('\n')
            colour.write(')')       




