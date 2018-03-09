import evdev
from select import select
from Tkinter import Tk, StringVar,Frame,Label,Button,Scrollbar,Listbox,Entry,Text
from Tkinter import Y,END,TOP,BOTH,LEFT,RIGHT,VERTICAL,SINGLE,NONE,NORMAL,DISABLED

class InputDevice(object):

    def __init__(self):
        # root is the Tkinter root widget
        self.root = Tk()
        self.root.title("Input Device Utility")

        # self.root.configure(background='grey')

        self.root.resizable(False,False)

        # define response to main window closing
        self.root.protocol ("WM_DELETE_WINDOW", self.app_exit)

        self.my_device =''
        self.my_device_display = StringVar()
        self.device_list=[]
        self.matches=0


        # overall display
        root_frame=Frame(self.root)
        root_frame.pack(side=LEFT)

        devices_frame=Frame(root_frame,padx=5,pady=10)
        devices_frame.pack(side=LEFT)
        
        devices_label = Label(devices_frame, text="Devices in dev/input")
        devices_label.pack(side=TOP)
        
        devices_list_frame=Frame(devices_frame,padx=5,pady=10)
        devices_list_frame.pack(side=TOP)

        selected_device_title=Label(devices_frame,text='Selected device')
        selected_device_title.pack(side=TOP)
        self.selected_device_var=StringVar()
        selected_device=Label(devices_frame,textvariable=self.selected_device_var,fg="red")
        selected_device.pack(side=TOP)

        events_frame=Frame(root_frame,padx=5,pady=10)
        events_frame.pack(side=LEFT)
        events_title=Label(events_frame,text='Received Events')
        events_title.pack(side=TOP)
        events_list_frame=Frame(events_frame,padx=5,pady=10)
        events_list_frame.pack(side=TOP)


        # list of devices
        scrollbar = Scrollbar(devices_list_frame, orient=VERTICAL)
        self.devices_display = Listbox(devices_list_frame, selectmode=SINGLE, height=20,
                                     width = 60, bg="white",activestyle=NONE,
                                     fg="black", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.devices_display.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.devices_display.pack(side=LEFT, fill=BOTH, expand=1)
        self.devices_display.bind("<ButtonRelease-1>", self.e_select_device)

        # events display
        scrollbar = Scrollbar(events_list_frame, orient=VERTICAL)
        self.events_display = Text(events_list_frame,width=40,height=20, wrap='word', font="arial 11",padx=5,yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.events_display.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.events_display.pack(side=LEFT, fill=BOTH, expand=1)
        self.events_display.config(state=NORMAL)
        self.events_display.delete(1.0, END)
        self.events_display.config(state=DISABLED)


        self.selected_device_index=-1
        self.matches=0
        
        self.get_all_devices()
        self.refresh_devices_display()


        self.root.after(10,self.event_loop)

        # and enter Tkinter event loop
        self.root.mainloop()        



    # ***************************************
    # INIT AND EXIT
    # ***************************************
    def app_exit(self):
        self.root.destroy()
        exit()

    def event_loop(self):
        if self.matches>0:
            self.get_events()
        self.root.after(10,self.event_loop)

    def refresh_devices_display(self):
        self.devices_display.delete(0,self.devices_display.size())
        for device in self.all_devices:
            self.devices_display.insert(END, device[0]+ ' ' +device[1])        
        if self.selected_device_index >= 0:
            self.devices_display.itemconfig(self.selected_device_index,fg='red')            
            self.devices_display.see(self.selected_device_index)


    def e_select_device(self,event):
        self.selected_device_index=-1
        if len(self.all_devices)>0:
            self.selected_device_index=int(event.widget.curselection()[0])
            selected_device=self.all_devices[self.selected_device_index]
            self.selected_device_name=selected_device[0]
            self.selected_device_var.set(self.selected_device_name)
            self.get_matching_devices()
            self.refresh_devices_display()


    def get_all_devices(self):
        self.all_devices=[]
        devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
        for device in devices:
            self.all_devices.append([device.name,device.fn])
            

    def get_matching_devices(self):
        self.matches=0
        self.matching_devices=[]
        devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
        for device in devices:
            if self.selected_device_name in device.name:
                device_ref = evdev.InputDevice(device.fn)
                self.matching_devices.append(device_ref)
                self.matches+=1

              
    def get_events(self):
        r,w,x = select(self.matching_devices, [], [],0)
        if r == []:
            return
        for event in r[0].read():
            if event.type == evdev.ecodes.EV_KEY:
                key_event = evdev.categorize(event)
                if key_event.keystate == 1:
                    key_text='Down'
                else:
                    key_text='Up'
                # print key_event.keycode,key_text
                if type(key_event.keycode) is list:
                    code_text=', '.join(key_event.keycode)
                else:
                    code_text=key_event.keycode
                                        
                self.events_display.config(state=NORMAL)
                self.events_display.insert(END,'\n'+ code_text + ' ' + key_text)
                self.events_display.config(state=DISABLED)
                self.events_display.see(END)


# ***************************************
# MAIN
# ***************************************


if __name__  ==  "__main__":
    idd = InputDevice()

