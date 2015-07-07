
from Tkinter import *
import ttk
import Tkinter
import traceback

class ttkCombobox(ttk.Combobox):
    def __init__(self, parent, **kwargs):
       ttk.Combobox.__init__(self, parent, **kwargs)
       self['values'] = []

    def __call__(self, *args):
       self['values'] = args

class ttkLabel(ttk.Label):
    def __init__(self, parent, **kwargs):
       ttk.Label.__init__(self, parent, **kwargs)

class ttkCheckbutton(ttk.Checkbutton):
    def __init__(self, parent, **kwargs):
       ttk.Checkbutton.__init__(self, parent, **kwargs)

class ttkEntry(ttk.Entry):

    def __init__(self, parent, **kwargs):
       kwargs.pop('bg', None)
       ttk.Entry.__init__(self, parent, **kwargs)

class ttkSpinbox(Spinbox):
	def __init__(self, parent, **kwargs):
		kwargs.pop('height', None)
		Spinbox.__init__(self, parent, **kwargs)

class ttkListbox(ttk.Treeview):

	def __init__(self, parent, **kwargs):
		if kwargs['selectmode'] == SINGLE: kwargs['selectmode'] = BROWSE
		# get rid of keys that Treeview doesn't understand
		kwargs.pop('width', None)
		kwargs.pop('bg', None)
		kwargs.pop('fg', None)
		kwargs.pop('activestyle', None)
		ttk.Treeview.__init__(self, parent, **kwargs)

	def delete(self, start, end):
		children = self.get_children()
		copy = children[:]
		if end == END:
			end = len(self.get_children()) - 1
		for index in range(start, end):
			item = copy[index]
			ttk.Treeview.delete(self,item)
		#traceback.print_stack()
		return

	def pack(self, **kwargs):
		ttk.Treeview.pack(self, **kwargs)

	def insert(self, pos, text, **kwargs):
		ttk.Treeview.insert(self, '', pos, text=text)

	def size(self):
		children = ttk.Treeview.get_children(self)
		return len(children)

	def select(self, selector):
	        index = None
	        if isinstance(selector, int):
	                index = selector
        	elif isinstance(selector, str) or isinstance(selector, unicode):
        	        index = self.indexof(selector)
	        if index != None:
        		item = self.get_children()[index]
        		self.see(index)
		        return self.selection_set(item)
	        else:
	                return None
		
	def indexof(self, text):
	        index = -1
	        items = self.get_children(None)
	        i = 0
	        for thisitem in items:
	                if self.item(thisitem)["text"] == text:
	                        index = i
       	                i += 1
	        return index
	        
	def selection_clear(self):
	        items = self.selection()
	        return self.selection_remove(items)

	def curselection(self):
		items = self.selection()
		indexes = []
		for item in items:
			indexes.append(self.index(item))
		return indexes

	def itemconfig(self, *args, **kwargs):
		# PiPresents removes/reinserts everything in the listbox and then uses 
		#   the foreground color = red to show a selection instead of actually
		#   'pseudo-select' an item in the Listbox.
		# Well, we are going to actually select it, if that's what it looks 
		#   like we are trying to do.
		fg = kwargs['fg']
		if fg == 'red':
			index = args[0]
			self.selection_set(self.item_at(index))
		pass

	def see(self, index):
		item = self.get_children()[index]
		ttk.Treeview.see(self, item)

	# Helpers

	def item_at(self, index):
		return self.get_children()[index]

	def clear(self):
		self.delete(0, END)


class ttkButton(ttk.Button):

	def __init__(self, parent, **kwargs):
		kwargs.pop('height', None)
		#kwargs.pop('width', None)
		kwargs.pop('bg', None)
		kwargs.pop('fg', None)
		kwargs.pop('font', None)
		kwargs.pop('-relief', None)
		kwargs.pop('relief', None)
		ttk.Button.__init__(self, parent, **kwargs)

class ttkFrame(ttk.Frame):

	def __init__(self, parent, **kwargs):
		kwargs.pop('padx', None)
		kwargs.pop('pady', None)
		ttk.Frame.__init__(self, parent, **kwargs)
	
