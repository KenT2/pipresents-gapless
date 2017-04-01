import os
import ConfigParser
import copy
from Tkinter import NW,CENTER
from PIL import Image
from PIL import ImageTk
from pp_utils import Monitor


class ScreenDriver(object):
    canvas = None  ##The Pi presents canvas, click areas are draawn on this, not individual show canvases.
    image_obj=[]
    
    def __init__(self):
        self.mon=Monitor()


    # read screen.cfg    
    def read(self,pp_dir,pp_home,pp_profile):
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        # try inside profile
        tryfile=pp_profile+os.sep+'pp_io_config'+os.sep+'screen.cfg'
        # self.mon.log(self,"Trying screen.cfg in profile at: "+ tryfile)
        if os.path.exists(tryfile):
            filename=tryfile
        else:
            #give congiparser an empty filename so it returns an empty config.
            filename=''
        ScreenDriver.config = ConfigParser.ConfigParser()
        ScreenDriver.config.read(filename)
        if filename != '':
            self.mon.log(self,"screen.cfg read from "+ filename)
        return 'normal','screen.cfg read'

    def click_areas(self):
        return ScreenDriver.config.sections()

    def get(self,section,item):
        return ScreenDriver.config.get(section,item)

    def is_in_config(self,section,item):
        return ScreenDriver.config.has_option(section,item)

    
    # make click areas on the screen, bind them to their symbolic name, and create a callback if it is clicked.
    # click areas must be polygon as outline rectangles are not filled as far as find_closest goes
    # canvas is the PiPresents canvas
    def make_click_areas(self,canvas,callback):
        ScreenDriver.canvas=canvas
        self.callback=callback
        reason=''
        ScreenDriver.image_obj=[]
        for area in self.click_areas():
            reason,message,points = self.parse_points(self.get(area,'points'),self.get(area,'name'))
            if reason == 'error':
                break

            # calculate centre of polygon
            vertices = len(points)/2
            # print area, 'vertices',vertices
            sum_x=0
            sum_y=0
            for i in range(0,vertices):
                # print i
                sum_x=sum_x+int(points[2*i])
                # print int(points[2*i])
                sum_y=sum_y+int(points[2*i+1])
                # print int(points[2*i+1])
            polygon_centre_x=sum_x/vertices
            polygon_centre_y=sum_y/vertices

            
            ScreenDriver.canvas.create_polygon(points,
                                       fill=self.get (area,'fill-colour'),
                                       outline=self.get (area,'outline-colour'),
                                       tags=("pp-click-area",self.get(area,'name')),
                                       state='hidden')

            # image for the button
            if not self.is_in_config(area,'image'):
                reason='error'
                message='missing image fields in screen.cfg, see 1.3 release notes'
                break
            image_name=self.get(area,'image')
            if image_name !='':
                image_width = int(self.get(area,'image-width'))
                image_height = int(self.get(area,'image-height'))
                image_path=self.complete_path(image_name)
                if os.path.exists(image_path) is True:
                    self.pil_image=Image.open(image_path)
                else:
                    image_path=self.pp_dir+os.sep+'pp_resources'+os.sep+'button.jpg'
                    if os.path.exists(image_path) is True:
                        self.mon.warn(self,'Default button image used for '+ area)
                        self.pil_image=Image.open(image_path)
                    else:
                        self.mon.warn(self,'Button image does not exist for '+ area)
                        self.pil_image=None
                        
                if self.pil_image is not None:
                    self.pil_image=self.pil_image.resize((image_width-1,image_height-1))                 
                    self.photo_image_id=ImageTk.PhotoImage(self.pil_image)
                    image_id=self.canvas.create_image(polygon_centre_x,polygon_centre_y,
                                             image=self.photo_image_id,
                                             anchor=CENTER,
                                            tags=('pp-click-area',self.get(area,'name')),
                                            state='hidden')
                    del self.pil_image
                    ScreenDriver.image_obj.append(self.photo_image_id)

            # write the label at the centroid
            if self.get(area,'text') != '':
                ScreenDriver.canvas.create_text(polygon_centre_x,polygon_centre_y,
                                        text=self.get(area,'text'),
                                        fill=self.get(area,'text-colour'),
                                        font=self.get(area,'text-font'),
                                        tags=('pp-click-area',self.get(area,'name')),
                                        state='hidden')
                
            ScreenDriver.canvas.bind('<Button-1>',self.click_pressed)
                                 
        if reason == 'error':
            return 'error',message
        else:
            return 'normal','made click areas'
                                        
     # callback for click on screen
    def click_pressed(self,event):
        overlapping =  event.widget.find_overlapping(event.x-5,event.y-5,event.x+5,event.y+5)
        for item in overlapping:
            # print ScreenDriver.canvas.gettags(item)
            if ('pp-click-area' in ScreenDriver.canvas.gettags(item)) and ScreenDriver.canvas.itemcget(item,'state') == 'normal':
                self.mon.log(self, "Click on screen: "+ ScreenDriver.canvas.gettags(item)[1])
                self.callback(ScreenDriver.canvas.gettags(item)[1],'SCREEN')
                # need break as find_overlapping returns two results for each click, one with 'current' one without.
                break

    def is_click_area(self,test_area):
        click_areas=ScreenDriver.canvas.find_withtag('pp-click-area')
        for area in click_areas:        
            if test_area in ScreenDriver.canvas.gettags(area):
                return True
        return False
                                                      

    # use links with the symbolic name of click areas to enable the click areas in a show
    def enable_click_areas(self,links):
        for link in links:
            if self.is_click_area(link[0]) and link[1] != 'null':
                # print 'enabling link ',link[0]
                ScreenDriver.canvas.itemconfig(link[0],state='normal')


    def hide_click_areas(self,links):
        # hide  click areas
        for link in links:
            if self.is_click_area(link[0]) and link[1] != 'null':
                # print 'disabling link ',link[0]
                ScreenDriver.canvas.itemconfig(link[0],state='hidden')

        # this does not seem to change the colour of the polygon
        # ScreenDriver.canvas.itemconfig('pp-click-area',state='hidden')
        ScreenDriver.canvas.update_idletasks( )
        

    def parse_points(self,points_text,area):
        if points_text.strip() == '':
            return 'error','No points in click area: '+area,[]
        if '+' in points_text:
            # parse  x+y+width*height
            fields=points_text.split('+')
            if len(fields) != 3:
                return 'error','Do not understand click area points: '+area,[]
            dimensions=fields[2].split('*')
            if len(dimensions)!=2:
                return 'error','Do not understand click area points: '+area,[]
            
            if not fields[0].isdigit():
                return 'error','x1 is not a positive integer in click area: '+area,[]
            else:
                x1=int(fields[0])
            
            if not fields[1].isdigit():
                return 'error','y1 is not a positive integer in click area: '+area,[]
            else:
                y1=int(fields[1])
                
            if not dimensions[0].isdigit():
                return 'error','width1 is not a positive integer in click area: '+area,[]
            else:
                width=int(dimensions[0])
                
            if not dimensions[1].isdigit():
                return 'error','height is not a positive integer in click area: '+area,[]
            else:
                height=int(dimensions[1])

            return 'normal','',[str(x1),str(y1),str(x1+width),str(y1),str(x1+width),str(y1+height),str(x1),str(y1+height)]
            
        else:
            # parse unlimited set of x,y,coords
            points=points_text.split()
            if len(points) < 6:
                return 'error','Less than 3 vertices in click area: '+area,[]
            if len(points)%2 != 0:
                return 'error','Odd number of points in click area: '+area,[]      
            for point in points:
                if not point.isdigit():
                    return 'error','point is not a positive integer in click area: '+area,[]
            return 'normal','parsed points OK',points


    def complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file != '' and track_file[0]=="+":
            track_file=self.pp_home+track_file[1:]
        elif track_file[0] == "@":
            track_file=self.pp_profile+track_file[1:]
        return track_file   
