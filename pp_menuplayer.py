import os
from Tkinter import N, CENTER, LEFT, NW, W
from PIL import Image
from PIL import ImageTk
from pp_player import Player
from pp_utils import parse_rectangle, calculate_text_position

class MenuPlayer(Player):

    """
        A special player that displays a menu as the first track of MenuShow

        __init_ just makes sure that all the things the player needs are available
        load and unload loads and unloads the track
        show  - shows the track,close closes the track after pause at end
        input-pressed  - receives user input while the track is playing.
        highlight_menu_entry - a special method for menuplayer
    """
 
    def __init__(self,
                 show_id,
                 showlist,
                 root,
                 canvas,
                 show_params,
                 track_params ,
                 pp_dir,
                 pp_home,
                 pp_profile,
                 end_callback,
                 command_callback):

        # initialise items common to all players   
        Player.__init__( self,
                         show_id,
                         showlist,
                         root,
                         canvas,
                         show_params,
                         track_params ,
                         pp_dir,
                         pp_home,
                         pp_profile,
                         end_callback,
                         command_callback)

        self.mon.trace(self,'')      

        
        # and initialise things for this player
        self.display_guidelines=track_params['menu-guidelines']
        self.play_state='initialised'
        self.menu_entry_id=[]
        self.menu_text_obj = None
        self.hint_text_obj = None



    # LOAD - loads the images and text
    def load(self,track,loaded_callback,enable_menu):  
        # instantiate arguments
        self.track=track                   # not used
        self.loaded_callback=loaded_callback   #callback when loaded
        
        self.mon.trace(self,'')

        # do common bits of  load
        Player.pre_load(self)   

        # bodge for menuplayer, pass medialist through track parameters
        if 'medialist_obj' in self.show_params:
            self.medialist=self.show_params['medialist_obj']
        else:
            self.mon.err(self,'A Menu Track must be run from a Menu Show')
            self.play_state='load-failed'
            if self.loaded_callback is not  None:
                self.loaded_callback('error','A Menu Track must be run from a Menu Show')
                return
        
        # load the images and text
        status,message=Player.load_x_content(self,enable_menu)
        if status == 'error':
            self.mon.err(self,message)
            self.play_state='load-failed'
            if self.loaded_callback is not  None:
                self.loaded_callback('error',message)
                return
        else:
            self.play_state='loaded'
            if self.loaded_callback is not None:
                self.loaded_callback('loaded','menu track loaded')

            
 
    # UNLOAD - abort a load when omplayer is loading or loaded
    def unload(self):
        self.mon.trace(self, '')
        # nothing to do for Menuplayer
        self.mon.log(self,">unload received from show Id: "+ str(self.show_id))
        self.play_state='unloaded'


     # SHOW - show the menu from its loaded state 
    def show(self,ready_callback,finished_callback,closed_callback):
                         
        # instantiate arguments
        self.ready_callback=ready_callback         # callback when ready to show an image - 
        self.finished_callback=finished_callback         # callback when finished showing 
        self.closed_callback=closed_callback            # callback when closed - not used by imageplayer
        
        self.mon.trace(self,'')
        
        self.quit_signal=False
        
        # do common bits
        Player.pre_show(self)
        
        self.start_dwell()


    # CLOSE - nothing tt do in menuplayer - x content is removed by ready callback and hide
    def close(self,closed_callback):
        self.mon.trace(self,'') 

        self.closed_callback=closed_callback
        self.mon.log(self,">close received from show Id: "+ str(self.show_id))
        self.play_state='closed'
        if self.closed_callback is not None:
            self.closed_callback('normal','menuplayer closed')



    def input_pressed(self,symbol):   
        self.mon.trace(self,symbol) 
        if symbol == 'stop':
            self.stop()


    def stop(self):
        self.quit_signal=True



# ******************************************
# Sequencing
# ********************************************

    def start_dwell(self):
        self.play_state='showing'
        self.tick_timer=self.canvas.after(100, self.do_dwell)


        
    def do_dwell(self):
        if self.quit_signal is True:
            self.quit_signal=False
            self.mon.log(self,"quit received")
            if self.finished_callback is not  None:
                self.finished_callback('pause_at_end','user quit')
                # use finish so that the show will call close 
        else:
            self.tick_timer=self.canvas.after(100, self.do_dwell)



# *********************
# Displaying things
# *********************

    def load_track_content(self):

        self.menu_text_obj=None
        self.hint_text_obj=None
            
        reason,message=self.display_menu()
        if reason=='error':
            return reason,message

        # display menu text if enabled
        if self.track_params['track-text'] != '':
            x,y,anchor,justify=calculate_text_position(self.track_params['track-text-x'],self.track_params['track-text-y'],
                                     self.show_canvas_x1,self.show_canvas_y1,
                                     self.show_canvas_centre_x,self.show_canvas_centre_y,
                                     self.show_canvas_x2,self.show_canvas_y2,self.track_params['track-text-justify'])
            
            self.menu_text_obj=self.canvas.create_text(x,y,
                                                       anchor=anchor,
                                                       justify=justify,
                                                       text=self.track_params['track-text'],
                                                       fill=self.track_params['track-text-colour'],
                                                       font=self.track_params['track-text-font'])

        # display instructions (hint)
        hint_text=self.track_params['hint-text']
        if hint_text != '':
            x,y,anchor,justify=calculate_text_position(self.track_params['hint-x'],self.track_params['hint-y'],
                                     self.show_canvas_x1,self.show_canvas_y1,
                                     self.show_canvas_centre_x,self.show_canvas_centre_y,
                                     self.show_canvas_x2,self.show_canvas_y2,self.track_params['hint-justify'])            
            self.hint_text_obj=self.canvas.create_text(x,y,
                                                       anchor=anchor,
                                                       justify=justify,
                                                       text=hint_text,
                                                       fill=self.track_params['hint-colour'],
                                                       font=self.track_params['hint-font'])
            
        self.canvas.itemconfig(self.menu_text_obj,state='hidden')
        self.canvas.itemconfig(self.hint_text_obj,state='hidden')
        return 'normal','menu content loaded'


    def show_track_content(self):
        self.canvas.itemconfig(self.menu_text_obj,state='normal')
        self.canvas.itemconfig(self.hint_text_obj,state='normal')
        

    def hide_track_content(self):
        self.mon.trace(self,'') 
        self.canvas.itemconfig(self.menu_text_obj,state='hidden')
        self.canvas.itemconfig(self.hint_text_obj,state='hidden')
        self.canvas.delete(self.menu_text_obj)
        self.canvas.delete(self.hint_text_obj)
        self.hide_menu_entries()
        self.canvas.update_idletasks()




# *********************
# Displaying the menu entries
# *********************

    def display_menu(self):

        if self.medialist.anon_length()==0:
            return 'error','no tracks to show in menu'

        # calculate menu geometry
        reason,message=self.calculate_geometry()
        if reason == 'error':
            return reason,message
        
        # display the menu entries
        self.display_menu_entries()
        self.canvas.update_idletasks( )
        return 'normal',''


    def display_menu_entries(self):
        # init the loop
        column_index=0
        row_index=0
        self.menu_length=1
        
        # id store is a list of elements each being a list of the three ids of the elements of the entry
        self.menu_entry_id=[]
        # offsets for the above
        self.icon_id_index=0 # rectangle around the icon - object
        self.image_id_index=1 # icon image - needed for tkinter - PIL image
        self.text_id_index=3 # the text - need when no icon is displayed - object
        # and 5 other to do with the strip

        # select the start of the medialist
        self.medialist.start()

        # loop through menu entries
        while True:
            # display the entry
            # calculate top left corner of entry
            self.calculate_entry_position(column_index,row_index)

            # display the button strip
            top_id,bottom_id,left_id,right_id,rectangle_id=self.display_entry_strip()

            # display the selected entry highlight
            icon_id=self.display_icon_rectangle()

            # display the image in the icon
            image_id,photo_image_id=self.display_icon_image()

            if self.track_params['menu-text-mode'] != 'none':
                text_id=self.display_icon_text()
            else:
                text_id=None

            # append id's to the list
            self.menu_entry_id.append([icon_id,image_id,photo_image_id,text_id,top_id,bottom_id,left_id,right_id,rectangle_id])
            
            # and loop
            if self.medialist.at_end():
                break
            self.menu_length+=1
            self.medialist.next('ordered')

            if self.direction == 'horizontal':
                column_index+=1
                if column_index>=self.menu_columns:
                    column_index=0
                    row_index+=1
            else:
                row_index+=1
                if row_index>=self.menu_rows:
                    row_index=0
                    column_index+=1
                    

    def hide_menu_entries(self):
        # print 'HIDE MENU ENTRIES'
        for entry in self.menu_entry_id:
            #0 icon_id   polygon
            self.canvas.itemconfig(entry[0],state='hidden')
            self.canvas.delete(entry[0])
            #1image_id image
            self.canvas.itemconfig(entry[1],state='hidden')
            self.canvas.delete(entry[1])
            #2 photo_image_id, the image behind tge image_id
            entry[2]=None
            #3 text_id text
            self.canvas.itemconfig(entry[3],state='hidden')
            self.canvas.delete(entry[3])
            #4 top_id  line
            self.canvas.itemconfig(entry[4],state='hidden')
            self.canvas.delete(entry[4])
            #5 bottom_id  line
            self.canvas.itemconfig(entry[5],state='hidden')
            self.canvas.delete(entry[5])
            #6 left_id  line
            self.canvas.itemconfig(entry[6],state='hidden')
            self.canvas.delete(entry[6])
            #7 right_id line
            self.canvas.itemconfig(entry[7],state='hidden')
            self.canvas.delete(entry[7])
            #8 rectangle_id  rectangle (strip)
            self.canvas.itemconfig(entry[8],state='hidden')
            self.canvas.delete(entry[8])



    def print_geometry(self,total_width,total_height):
        print 'list length',self.list_length
        print 'menu width: ', self.menu_width
        print 'columns', self.menu_columns
        print 'icon width: ', self.icon_width
        print 'horizontal padding: ', self.menu_horizontal_padding
        print 'text width: ', self.text_width
        print 'entry width: ', self.entry_width
        print 'total width: ', total_width
        print 'x separation: ', self.x_separation
        print ''
        print 'menu height', self.menu_height
        print 'rows: ', self.menu_rows
        print 'icon height', self.icon_height
        print 'vertical padding: ', self.menu_vertical_padding        
        print 'text height', self.text_height
        print 'entry height', self.entry_height
        print 'total height', total_height
        print 'y separation', self.y_separation

        
    # ------------------------------------------------------------------
    # calculate menu entry size and separation between menu entries
    # ------------------------------------------------------------------
    def calculate_geometry(self):

        self.display_strip=self.track_params['menu-strip']
        self.canvas_width=int(self.canvas['width'])
        self.canvas_height=int(self.canvas['height'])
        
        if self.display_strip == 'yes':
            self.strip_padding=int(self.track_params['menu-strip-padding'])
        else:
            self.strip_padding=0

        # parse the menu window
        reason,message,self.menu_x_left,self.menu_y_top,self.menu_x_right,self.menu_y_bottom=self.parse_menu_window(self.track_params['menu-window'])
        if reason == 'error':
            return 'error',"Menu Window error: "+ message

        if self.track_params['menu-icon-mode'] == 'none' and self.track_params['menu-text-mode'] == 'none':
            return 'error','Icon and Text are both None'
        if self.track_params['menu-icon-mode'] == 'none' and self.track_params['menu-text-mode'] == 'overlay':
            return 'error','cannot overlay none icon'

        self.direction=self.track_params['menu-direction']
        
        self.menu_width=self.menu_x_right - self.menu_x_left
        self.menu_height=self.menu_y_bottom - self.menu_y_top

        self.list_length=self.medialist.anon_length()

        # get or calculate rows and columns
        if self.direction == 'horizontal':
            if self.track_params['menu-columns'] == '':
                return 'error','blank columns for horizontal direction'
            self.menu_columns=int(self.track_params['menu-columns'])
            self.menu_rows=self.list_length//self.menu_columns
            if self.list_length % self.menu_columns != 0:
                self.menu_rows+=1
        else:
            if self.track_params['menu-rows'] == '':
                return 'error','blank rows for vertical direction'
            self.menu_rows=int(self.track_params['menu-rows'])
            self.menu_columns=self.list_length//self.menu_rows
            if self.list_length % self.menu_rows != 0:
                self.menu_columns+=1
                
        self.x_separation=int(self.track_params['menu-horizontal-separation'])
        self.y_separation=int(self.track_params['menu-vertical-separation'])

        # get size of padding depending on exitence of icon and text
        if self.track_params['menu-icon-mode'] in ('thumbnail','bullet') and self.track_params['menu-text-mode']  ==  'right':
            self.menu_horizontal_padding=int(self.track_params['menu-horizontal-padding'])
        else:
            self.menu_horizontal_padding=0

        if self.track_params['menu-icon-mode'] in ('thumbnail','bullet') and self.track_params['menu-text-mode']  ==  'below':
            self.menu_vertical_padding=int(self.track_params['menu-vertical-padding'])
        else:
            self.menu_vertical_padding=0
            
        # calculate size of icon depending on use
        if self.track_params['menu-icon-mode'] in ('thumbnail','bullet'):
            self.icon_width=int(self.track_params['menu-icon-width'])
            self.icon_height=int(self.track_params['menu-icon-height'])
        else:
            self.icon_width=0
            self.icon_height=0

        # calculate size of text box depending on mode
        if self.track_params['menu-text-mode'] != 'none':
            self.text_width=int(self.track_params['menu-text-width'])
            self.text_height=int(self.track_params['menu-text-height'])
        else:
            self.text_width=0
            self.text_height=0
            
        # calculate size of entry box by combining text and icon sizes
        if self.track_params['menu-text-mode'] == 'right':
            self.entry_width=self.icon_width+self.menu_horizontal_padding+self.text_width
            self.entry_height=max(self.text_height,self.icon_height)
        elif self.track_params['menu-text-mode'] == 'below':
            self.entry_width=max(self.text_width,self.icon_width)
            self.entry_height=self.icon_height + self.menu_vertical_padding + self.text_height 
        else:
            # no text or overlaid text
            if self.track_params['menu-icon-mode'] in ('thumbnail','bullet'):
                # icon only
                self.entry_width=self.icon_width
                self.entry_height=self.icon_height
            else:
                # text only
                self.entry_width=self.text_width
                self.entry_height=self.text_height

        if self.entry_width<=self.menu_horizontal_padding:
            return 'error','entry width is zero'

        if self.entry_height<=self.menu_vertical_padding:
            return 'error','entry height is zero'

        # calculate totals for debugging puropses
        total_width=self.menu_columns * self.entry_width +(self.menu_columns-1)*self.x_separation
        total_height=self.menu_rows * self.entry_height + (self.menu_rows-1)*self.y_separation
        
        # self.print_geometry(total_width,total_height)   


        # display guidelines and debgging text if there is a problem     
        if total_width>self.menu_width and self.display_guidelines != 'never':
            self.display_guidelines='always'
            self.mon.log(self,'\nMENU IS WIDER THAN THE WINDOW')
            self.print_geometry(total_width,total_height)


        if total_height>self.menu_height and self.display_guidelines != 'never':
            self.display_guidelines='always'
            self.mon.log(self,'\nMENU IS TALLER THAN THE WINDOW')
            self.print_geometry(total_width,total_height)            

        # display calculated total rectangle guidelines for debugging
        if self.display_guidelines == 'always':
            points=[self.menu_x_left + self.show_canvas_x1,
                    self.menu_y_top + self.show_canvas_y1,
                    self.menu_x_left+total_width + self.show_canvas_x1,
                    self.menu_y_top+total_height + self.show_canvas_y1]

            # and display the icon rectangle
            self.canvas.create_rectangle(points,
                                         outline='blue',
                                         fill='')

        
        # display menu rectangle guidelines for debugging
        if self.display_guidelines == 'always':
            points=[self.menu_x_left + self.show_canvas_x1,
                    self.menu_y_top + self.show_canvas_y1,
                    self.menu_x_right + self.show_canvas_x1,
                    self.menu_y_bottom + self.show_canvas_y1]
            self.canvas.create_rectangle(points,
                                         outline='red',
                                         fill='')
                
        return 'normal',''

    def calculate_entry_position(self,column_index,row_index):
        self.entry_x=self.menu_x_left+ column_index*(self.x_separation+self.entry_width)
        self.entry_y=self.menu_y_top+ row_index*(self.y_separation+self.entry_height)

            
    def display_entry_strip(self):
        if self.display_strip == 'yes':
            if self.direction == 'vertical':
                # display the strip
                strip_points=[self.entry_x - self.strip_padding -1  + self.show_canvas_x1,
                              self.entry_y - self.strip_padding - 1 + self.show_canvas_y1,
                              self.entry_x+ self.entry_width + self.strip_padding - 1 + self.show_canvas_x1,
                              self.entry_y+self.entry_height+ self.strip_padding - 1 + self.show_canvas_y1]
                rectangle_id=self.canvas.create_rectangle(strip_points,
                                                          outline='',
                                                          fill='gray',
                                                          stipple='gray12')

                top_l_points=[self.entry_x - self.strip_padding + self.show_canvas_x1,
                              self.entry_y - self.strip_padding + self.show_canvas_y1,
                              self.entry_x + self.entry_width + self.strip_padding  + self.show_canvas_x1,
                              self.entry_y - self.strip_padding + self.show_canvas_y1]
                
                top_id=self.canvas.create_line(top_l_points,
                                               fill='light gray')
                
                bottom_l_points=[self.entry_x - self.strip_padding + self.show_canvas_x1,
                                 self.entry_y + self.entry_height + self.strip_padding + self.show_canvas_y1,
                                 self.entry_x+ self.entry_width + self.strip_padding  + self.show_canvas_x1,
                                 self.entry_y+ self.entry_height + self.strip_padding + self.show_canvas_y1]
                
                bottom_id=self.canvas.create_line(bottom_l_points,
                                                  fill='dark gray')

                left_l_points=[self.entry_x - self.strip_padding + self.show_canvas_x1,
                               self.entry_y - self.strip_padding + self.show_canvas_y1,
                               self.entry_x - self.strip_padding + self.show_canvas_x1,
                               self.entry_y + self.entry_height + self.strip_padding + self.show_canvas_y1]
                
                left_id=self.canvas.create_line(left_l_points,
                                                fill='gray')
                right_id=None

            else:
                # display the strip vertically
                strip_points=[self.entry_x - self.strip_padding +1 + self.show_canvas_x1 ,
                              self.entry_y - self.strip_padding +1 + self.show_canvas_y1,
                              self.entry_x+self.entry_width + self.strip_padding -1 + self.show_canvas_x1,
                              self.entry_y + self.entry_height+ self.strip_padding -1 + self.show_canvas_y1]
                
                rectangle_id=self.canvas.create_rectangle(strip_points,
                                                          outline='',
                                                          fill='gray',
                                                          stipple='gray12')

                top_l_points=[self.entry_x - self.strip_padding + self.show_canvas_x1,
                              self.entry_y - self.strip_padding + self.show_canvas_y1,
                              self.entry_x + self.entry_width + self.strip_padding + self.show_canvas_x1,
                              self.entry_y - self.strip_padding + self.show_canvas_y1]
                
                top_id=self.canvas.create_line(top_l_points,
                                               fill='light gray')
                
                left_l_points=[self.entry_x - self.strip_padding + self.show_canvas_x1,
                               self.entry_y - self.strip_padding + self.show_canvas_y1,
                               self.entry_x - self.strip_padding + self.show_canvas_x1,
                               self.entry_y + self.entry_height+ self.strip_padding + self.show_canvas_y1]
                
                left_id=self.canvas.create_line(left_l_points,
                                                fill='gray')

                right_l_points=[self.entry_x +self.entry_width + self.strip_padding + self.show_canvas_x1,
                                self.entry_y - self.strip_padding + self.show_canvas_y1,
                                self.entry_x +self.entry_width + self.strip_padding + self.show_canvas_x1,
                                self.entry_y + self.entry_height+ self.strip_padding + self.show_canvas_y1]
                
                right_id=self.canvas.create_line(right_l_points,
                                                 fill='dark gray')

                bottom_id=None

        else:
            top_id = None
            bottom_id = None
            left_id = None
            right_id = None
            rectangle_id = None
                
        return top_id,bottom_id,left_id,right_id,rectangle_id


    # display the rectangle that goes arond the icon when the entry is selected
    def display_icon_rectangle(self):
        if self.track_params['menu-icon-mode'] in ('thumbnail','bullet'):

            # calculate icon parameters
            if self.icon_width<self.text_width and self.track_params['menu-text-mode'] == 'below':
                self.icon_x_left=self.entry_x+abs(self.icon_width-self.text_width)/2
            else:
                self.icon_x_left=self.entry_x
                
            self.icon_x_right=self.icon_x_left+self.icon_width

            if self.icon_height<self.text_height and self.track_params['menu-text-mode'] == 'right':
                self.icon_y_top=self.entry_y+abs(self.icon_height-self.text_height)/2
            else:
                self.icon_y_top=self.entry_y
                
            self.icon_y_bottom=self.icon_y_top+self.icon_height

            
            points=[self.icon_x_left + self.show_canvas_x1,
                    self.icon_y_top + self.show_canvas_y1,
                    self.icon_x_right + self.show_canvas_x1,
                    self.icon_y_top + self.show_canvas_y1,
                    self.icon_x_right + self.show_canvas_x1,
                    self.icon_y_bottom + self.show_canvas_y1,
                    self.icon_x_left + self.show_canvas_x1,
                    self.icon_y_bottom + self.show_canvas_y1]

            # display guidelines make it white when not selected for debugging
            if self.display_guidelines == 'always':
                outline='white'
            else:
                outline=''

            # and display the icon rectangle
            icon_id=self.canvas.create_polygon(points,
                                               outline=outline,
                                               fill='')


        else:
            # not using icon so set starting point for text to zero icon size
            self.icon_x_right=self.entry_x
            self.icon_y_bottom=self.entry_y
            icon_id=None
        return icon_id
    

    # display the image in a menu entry
    def  display_icon_image(self):
        image_id=None
        photo_image_id=None
        if self.track_params['menu-icon-mode'] == 'thumbnail':
            # try for the thumbnail
            if self.medialist.selected_track()['thumbnail'] != '' and os.path.exists(self.complete_path(self.medialist.selected_track()['thumbnail'])):
                self.pil_image=Image.open(self.complete_path(self.medialist.selected_track()['thumbnail']))
            else:
                # cannot find thumbnail get the image if its an image track
                if self.medialist.selected_track()['type']  == 'image':
                    self.track=self.complete_path(self.medialist.selected_track()['location'])
                else:
                    self.track=''
                    
                if self.medialist.selected_track()['type'] == 'image' and os.path.exists(self.track) is True: 
                    self.pil_image=Image.open(self.track)
                else:
                    # use a standard thumbnail
                    icon_type=self.medialist.selected_track()['type']
                    standard=self.pp_dir+os.sep+'pp_resources'+os.sep+icon_type+'.png'
                    if os.path.exists(standard) is True:
                        self.pil_image=Image.open(standard)
                        self.mon.warn(self,'Default thumbnail used for '+self.medialist.selected_track()['title'])
                    else:
                        self.pil_image=None

            # display the image                
            if self.pil_image  is not  None:
                self.pil_image=self.pil_image.resize((self.icon_width-2,self.icon_height-2))                 
                photo_image_id=ImageTk.PhotoImage(self.pil_image)
                image_id=self.canvas.create_image(self.icon_x_left+1 + self.show_canvas_x1,
                                         self.icon_y_top+1 + self.show_canvas_y1,
                                         image=photo_image_id,
                                         anchor=NW)
                del self.pil_image
            else:
                image_id=None
                    
        elif self.track_params['menu-icon-mode']  == 'bullet':
            bullet=self.complete_path(self.track_params['menu-bullet'])                  
            if os.path.exists(bullet) is True:
                self.pil_image=Image.open(bullet)
            else:
                bullet=self.pp_dir+os.sep+'pp_resources'+os.sep+'bullet.png'
                if os.path.exists(bullet) is True:
                    self.mon.warn(self,'Default bullet used for '+self.medialist.selected_track()['title'])
                    self.pil_image=Image.open(bullet)
                else:
                    self.pil_image=None
                    
            if self.pil_image is not None:
                self.pil_image=self.pil_image.resize((self.icon_width-2,self.icon_height-2))                 
                photo_image_id=ImageTk.PhotoImage(self.pil_image)
                image_id=self.canvas.create_image(self.icon_x_left+1 + self.show_canvas_x1,
                                         self.icon_y_top+1 + self.show_canvas_y1,
                                         image=photo_image_id,
                                         anchor=NW)
                del self.pil_image
        else:
            image_id=None
        return image_id,photo_image_id

            
    # display the text of a menu entry
    def display_icon_text(self):
        text_mode=self.track_params['menu-text-mode']
        if self.track_params['menu-icon-mode'] in ('thumbnail','bullet'):
            if text_mode == 'right':
                if self.icon_height>self.text_height:
                    text_y_top=self.entry_y+abs(self.icon_height-self.text_height)/2
                else:
                    text_y_top=self.entry_y
                text_y_bottom=text_y_top+self.text_height
                
                text_x_left=self.icon_x_right+self.menu_horizontal_padding
                text_x_right=text_x_left+self.text_width
                
                text_x=text_x_left
                text_y=text_y_top+(self.text_height/2)

            elif text_mode == 'below':
                text_y_top=self.icon_y_bottom+self.menu_vertical_padding
                text_y_bottom=text_y_top+self.text_height
                
                if self.icon_width>self.text_width:
                    text_x_left=self.entry_x+abs(self.icon_width-self.text_width)/2
                else:
                    text_x_left=self.entry_x
                text_x_right=text_x_left+self.text_width
                
                text_x=text_x_left+(self.text_width/2)
                text_y=text_y_top

            else:
                # icon with text_mode=overlay or none
                text_x_left=self.icon_x_left
                text_x_right= self.icon_x_right
                text_y_top=self.icon_y_top
                text_y_bottom=self.icon_y_bottom
                text_x=(text_x_left+text_x_right)/2
                text_y=(text_y_top+text_y_bottom)/2                    

        else:
            # no icon text only
            text_y_top=self.entry_y
            text_y_bottom=text_y_top+self.text_height
            text_x_left=self.entry_x
            text_x_right=text_x_left+self.text_width
            text_x=self.entry_x
            text_y=self.entry_y+self.text_height/2


        # display the guidelines for debugging
        if self.display_guidelines == 'always':
            points=[text_x_left + self.show_canvas_x1,
                    text_y_top + self.show_canvas_y1,
                    text_x_right + self.show_canvas_x1,
                    text_y_top + self.show_canvas_y1,
                    text_x_right + self.show_canvas_x1,
                    text_y_bottom + self.show_canvas_y1,
                    text_x_left + self.show_canvas_x1,
                    text_y_bottom + self.show_canvas_y1]
            self.canvas.create_polygon(points,
                                       fill= '' ,
                                       outline='white')

        # display the text
        if text_mode == 'below' and self.track_params['menu-icon-mode']  in ('thumbnail','bullet'):
            anchor=N
            justify=CENTER
        elif text_mode == 'overlay' and self.track_params['menu-icon-mode']  in ('thumbnail','bullet'):
            anchor=CENTER
            justify=CENTER
        else:
            anchor=W
            justify=LEFT
        text_id=self.canvas.create_text(text_x + self.show_canvas_x1,
                                        text_y + self.show_canvas_y1,
                                        text=self.medialist.selected_track()['title'],
                                        anchor=anchor,
                                        fill=self.track_params['entry-colour'],
                                        font=self.track_params['entry-font'],
                                        width=self.text_width,
                                        justify=justify)
        return text_id
    

    def highlight_menu_entry(self,index,state):
        if self.track_params['menu-icon-mode'] != 'none':
            if state is True:
                self.canvas.itemconfig(self.menu_entry_id[index][self.icon_id_index],
                                       outline=self.track_params['entry-select-colour'],
                                       width=4)
            else:
                self.canvas.itemconfig(self.menu_entry_id[index][self.icon_id_index],
                                       outline='',
                                       width=1)
        else:
            if state is True:
                self.canvas.itemconfig(self.menu_entry_id[index][self.text_id_index],
                                       fill=self.track_params['entry-select-colour'])
                self.canvas.update_idletasks( )
            else:
                self.canvas.itemconfig(self.menu_entry_id[index][self.text_id_index],
                                       fill=self.track_params['entry-colour'])
                

    
    def parse_menu_window(self,line):
        if line != '':
            fields = line.split()
            if len(fields) not in  (1,2,4):
                return 'error','wrong number of fields',0,0,0,0
            if len(fields) in (1,4):
                if fields[0] == 'fullscreen':
                    return 'normal','',0,0,self.canvas_width - 1, self.canvas_height - 1
                else:
                    status,message,x1,y1,x2,y2 = parse_rectangle (' '.join(fields))
                    if status != 'error':
                        return 'normal','',x1,y1,x2,y2
                    else:
                        return 'error',message,0,0,0,0                   
            if len(fields) == 2:                    
                if fields[0].isdigit() and fields[1].isdigit():
                    return 'normal','',int(fields[0]),int(fields[1]),self.canvas_width, self.canvas_height
                else:
                    return 'error','dimension is not a number',0,0,0,0                    
        else:
            return 'error','line is blank',0,0,0,0



