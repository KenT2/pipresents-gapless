import os
import ConfigParser
from pp_utils import Monitor


class ScreenDriver:
    config=None

    def __init__(self):
        self.mon=Monitor()
        self.mon.on()

        
    #read screen.cfg    
    def read(self,pp_dir,pp_home,pp_profile):
        if ScreenDriver.config==None:
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
                        self.mon.log(self,"screen.cfg not found at "+ tryfile)
                        self.mon.err(self,"screen.cfg not found")
                        return False   
            ScreenDriver.config = ConfigParser.ConfigParser()
            ScreenDriver.config.read(filename)
            self.mon.log(self,"screen.cfg read from "+ filename)
            return True


    def click_areas(self):
        return ScreenDriver.config.sections()

    def get(self,section,item):
        return ScreenDriver.config.get(section,item)
    
    # make click areas on the screen, bind them to their symbolic name, and create a callback if it is clicked.
    # click areas must be polygon as outline rectangles are not filled as far as find_closest goes
    def make_click_areas(self,canvas,callback):
        self.canvas=canvas
        self.callback=callback
        reason=''
        for area in self.click_areas():
            reason,message,points = self.parse_points(self.get(area,'points'),self.get(area,'name'))
            if reason =='error':
                break
            self.canvas.create_polygon(points,
                                              fill=self.get (area,'fill-colour'),
                                              outline=self.get (area,'outline-colour'),
                                              tags=("pp-click-area",self.get(area,'name')),
                                              state='hidden')
            # write the label at the centroid
            if self.get(area,'text')<>'':
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
                self.canvas.create_text(text_centre_x,text_centre_y,
                                        text=self.get(area,'text'),
                                        fill=self.get(area,'text-colour'),
                                        font=self.get(area,'text-font'),
                                        tags=('pp-click-area',self.get(area,'name')),
                                        state='hidden')
            self.canvas.bind('<Button-1>',self.click_pressed)
                                                      
        if reason=='error':
            return 'error',message
        else:
            return 'normal',''
                                        
     # callback for click on screen
    def click_pressed(self,event):
        overlapping =  event.widget.find_overlapping(event.x-5,event.y-5,event.x+5,event.y+5)
        for item in overlapping:
            #print self.canvas.gettags(item)
            if ('pp-click-area' in self.canvas.gettags(item)) and self.canvas.itemcget(item,'state')=='normal':
                self.mon.log(self, "Click on screen: "+ self.canvas.gettags(item)[1])
                self.callback(self.canvas.gettags(item)[1],'front','screen')                                                     
                                                      

    # use links to enable and hide the click areas in a show
    def enable_click_areas(self,links,canvas):
        for link in links:
            #print 'trying link ',link[0] 
            if not('key-' in link[0]) and link[1]<>'null':
            # if not('key-' in link[0]) and link[1]<>'null' and link[0]<>'pp-auto':
                # print 'enabling link ',link[0]
                canvas.itemconfig(link[0],state='normal')

    def hide_click_areas(self,canvas):
        # this does not seem to change the colour of the polygon
        canvas.itemconfig('pp-click-area',state='hidden')
        canvas.update_idletasks( )
        

    def parse_points(self,points_text,area):
        if points_text.strip()=='':
            return 'error','No points in click area: '+area,[]
        points=points_text.split()
        if len(points)<6:
            return 'error','Less than 3 vertices in click area: '+area,[]
        if len(points)%2<>0:
            return 'error','Odd number of points in click area: '+area,[]      
        for point in points:
            if not point.isdigit():
                return 'error','point is not a positive integer in click area: '+area,[]
        return 'normal','parsed points OK',points

