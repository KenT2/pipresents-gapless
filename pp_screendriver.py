import os
import ConfigParser
from pp_utils import Monitor


class ScreenDriver(object):
    config=None
    canvas = None  ##The Pi presents canvas, click areas are draawn on this, not individual show canvases.

    def __init__(self):
        self.mon=Monitor()


    # read screen.cfg    
    def read(self,pp_dir,pp_home,pp_profile):
        if ScreenDriver.config is None:
            # try inside profile
            tryfile=pp_profile+os.sep+"screen.cfg"
            # self.mon.log(self,"Trying screen.cfg in profile at: "+ tryfile)
            if os.path.exists(tryfile):
                filename=tryfile
            else:
                # try inside pp_home
                # self.mon.log(self,"screen.cfg not found at "+ tryfile+ " trying pp_home")
                tryfile=pp_home+os.sep+"screen.cfg"
                if os.path.exists(tryfile):
                    filename=tryfile
                else:
                    # try inside pipresents
                    # self.mon.log(self,"screen.cfg not found at "+ tryfile + " trying inside pipresents")
                    tryfile=pp_dir+os.sep+'pp_home'+os.sep+"screen.cfg"
                    if os.path.exists(tryfile):
                        filename=tryfile
                    else:
                        self.mon.err(self,"screen.cfg not found at " + tryfile)
                        return 'error','scrren.cfg not found'   
            ScreenDriver.config = ConfigParser.ConfigParser()
            ScreenDriver.config.read(filename)
            self.mon.log(self,"screen.cfg read from "+ filename)
            return 'normal','screen.cfg read'


    def click_areas(self):
        return ScreenDriver.config.sections()

    def get(self,section,item):
        return ScreenDriver.config.get(section,item)
    
    # make click areas on the screen, bind them to their symbolic name, and create a callback if it is clicked.
    # click areas must be polygon as outline rectangles are not filled as far as find_closest goes
    # canvas is the PiPresents canvas
    def make_click_areas(self,canvas,callback):
        ScreenDriver.canvas=canvas
        self.callback=callback
        reason=''
        for area in self.click_areas():
            reason,message,points = self.parse_points(self.get(area,'points'),self.get(area,'name'))
            if reason == 'error':
                break
            ScreenDriver.canvas.create_polygon(points,
                                       fill=self.get (area,'fill-colour'),
                                       outline=self.get (area,'outline-colour'),
                                       tags=("pp-click-area",self.get(area,'name')),
                                       state='hidden')
            # write the label at the centroid
            if self.get(area,'text') != '':
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
                text_centre_x=sum_x/vertices
                text_centre_y=sum_y/vertices
                ScreenDriver.canvas.create_text(text_centre_x,text_centre_y,
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
                self.callback(ScreenDriver.canvas.gettags(item)[1],'front','screen')
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
                print 'disabling link ',link[0]
                ScreenDriver.canvas.itemconfig(link[0],state='hidden')

        # this does not seem to change the colour of the polygon
        # ScreenDriver.canvas.itemconfig('pp-click-area',state='hidden')
        ScreenDriver.canvas.update_idletasks( )
        

    def parse_points(self,points_text,area):
        if points_text.strip() == '':
            return 'error','No points in click area: '+area,[]
        points=points_text.split()
        if len(points) < 6:
            return 'error','Less than 3 vertices in click area: '+area,[]
        if len(points)%2 != 0:
            return 'error','Odd number of points in click area: '+area,[]      
        for point in points:
            if not point.isdigit():
                return 'error','point is not a positive integer in click area: '+area,[]
        return 'normal','parsed points OK',points

