"""
This example writes values of counters to the screen directly using Tkinter.

The counters are written direct to the Tkinter canvas that is used by
Pi Presents to display its output.

There is also an example of how to send debugging text to the terminal window.

"""
# ------ load the counter manager module
from pp_countermanager import CounterManager

# import constants from Tkinter
from Tkinter import NW

# class name must be the same as the nae in the .cfg file
class krt_quiz(object):

    def __init__(self,root,canvas,plugin_params,track_params,show_params,pp_dir,pp_home,pp_profile):
        # called when a player is executed for a track
        self.root=root
        self.canvas=canvas
        self.plugin_params=plugin_params
        self.track_params=track_params
        self.show_params=show_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        # plugin must keep track of the Tkinter objects it creates.
        self.plugin_objects=[]
        # plugin must keep track of the PIL image files it creates
        self.plugin_images=[]

        # ------ Make an instance of CounterManager
        self.cm=CounterManager()


    def load(self,track_file,liveshow,track_type):
        # Called in advance, while the previous track is being shown (frozen) as track loading can take a while.
        # Use load to modify the track file or track file name that is about to be loaded
        # must return the track file whether modified, replaced  or unaltered
        # return 'normal' if no error encountered, otherwise return 'error'
        return 'normal','',track_file



    def show(self):

        #  Draw objects direct to the screen setting their state
        #  to 'normal' so they are displayed
        #
        #  Determine whether drawing to the screen should happen repeatedly
        #  in the track by calling the redraw method
        #   = 0  do not redraw
        #   > 0 redraw at intervals (mS.)
        #  return the above value

        # ------ get the value of the quiz counters using get_counter() function
        # ------ status is 'error' if counter does not exist, value_text contains an error message
        status,correct=self.cm.get_counter('correct')
        status,questions=self.cm.get_counter('questions')
        
        my_text= 'Your score is '+ correct + ' out of '+ questions
        plugin_obj1=self.canvas.create_text(100,200,
                                        anchor=NW,
                                      text=my_text,
                                      fill='yellow',
                                      font='arial 20 bold',
                                     state = 'hidden'
                                )
        self.plugin_objects.append(plugin_obj1)
        

        if int(questions) == 2 and int(correct) == 2:
            my_text= 'Well done every question correct'      

            plugin_obj2=self.canvas.create_text(100,300,
                                        anchor=NW,
                                      text=my_text,
                                      fill='green',
                                      font='arial 20 bold',
                                     state = 'hidden'
                                )
            self.plugin_objects.append(plugin_obj2)


        if int(questions) == 2 and int(correct) < 2:
            wrong = int(questions) - int(correct)
            
            my_text= str(wrong) + ' questions wrong. Back to school for you'      

            plugin_obj3=self.canvas.create_text(100,300,
                                        anchor=NW,
                                      text=my_text,
                                      fill='red',
                                      font='arial 20 bold',
                                     state = 'hidden'
                                )
            self.plugin_objects.append(plugin_obj3)

  
        
        # make any objects that have been drawn visible
        for plugin_object in self.plugin_objects:
            self.canvas.itemconfig(plugin_object,state='normal')
            
        return 0

    def redraw(self):
        pass
    

    def hide(self):
        # called to delete the previous track's plugin objects
        for plugin_object in self.plugin_objects:
            self.canvas.itemconfig(plugin_object,state='hidden')
            self.canvas.delete(plugin_object)
        # and delete any PIL image files
        for plugin_image in self.plugin_images:
            plugin_image=None

                      
                       
                               

