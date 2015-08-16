# Based on example code at http://effbot.org/tkinterbook/tkinter-application-windows.htm
from Tkinter import *
import ttk
import Tkinter
from tkconversions import CRITICAL_COLOR, ERROR_COLOR, WARNING_COLOR

class StatusBar(ttk.Frame):

    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.label = ttk.Label(self, relief=SUNKEN, anchor=W)
        self.label.pack(fill=X)
        self.defaultbackground = ttk.Style().lookup('TLabel', 'background')

    def bind(self, sequence=None, func=None, add=None):
        self.label.bind(sequence, func, add)

    def set(self, format, *args, **kwargs):
        self.label.config(kwargs, text=format.format(*args))
        self.label.update_idletasks()
        
    def set_info(self, format, *args, **kwargs):
        self.label.config(kwargs, background=self.defaultbackground, text=format.format(*args))
        self.label.update_idletasks()
        
    def set_critical(self, format, *args, **kwargs):
        self.label.config(kwargs, background=CRITICAL_COLOR, text=format.format(*args))
        self.label.update_idletasks()
    
    def set_error(self, format, *args, **kwargs):
        self.label.config(kwargs, background=ERROR_COLOR, text=format.format(*args))
        self.label.update_idletasks()

    def set_warning(self, format, *args, **kwargs):
        self.label.config(kwargs, background=WARNING_COLOR, text=format.format(*args))
        self.label.update_idletasks()
    
    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()
