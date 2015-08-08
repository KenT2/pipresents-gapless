
from Tkinter import *
import ttk
import Tkinter as tk
import traceback
import colorsys
import pprint

class ttkStyle(ttk.Style):
    def theme_use(self, name, *args, **kwargs):
        ttk.Style.theme_use(self, *args, **kwargs)
        # fix weird frame colors
        #bg = self.lookup('.', 'background') # background, selectbackground
        #self.map('TFrame', background=[('disabled', bg), ('active', bg)])
        # differentiate between focused and unfocused Treeview
        bg = self.lookup('Treeview', 'background', state=['selected'] ) # background, selectbackground
        halfbg = self.adjust_saturation(bg, .5)
        self.map('Treeview', 
            background = [
              ('selected','focus', bg),
              ('selected','!focus', halfbg)])

    def adjust_saturation(self, color, amount):
        r,g,b = self.html_to_rgb(color)
        h,s,v = colorsys.rgb_to_hsv(r,g,b)
        s *= min(amount, 1.0)
        r,g,b = colorsys.hsv_to_rgb(h,s,v)
        return self.rgb_to_html(r,g,b)

    def html_to_rgb(self, html):
        html = html.replace("#","")
        r, g, b = html[:2], html[2:4], html[4:]
        r, g, b = [(int(n, 16))/255.0 for n in (r, g, b)]
        return r, g, b

    def rgb_to_html(self, r,g,b):
        return "#{0:02x}{1:02x}{2:02x}".format(int(r*255),int(g*255),int(b*255))

class ttkMenu(tk.Menu):
    def __init__(self, parent, *args, **kwargs):
        kwargs.pop('tearoff', 0)
        tk.Menu.__init__(self, parent, *args, tearoff=0, **kwargs)
        self.bind("<Escape>", self.release)

    def release(self, event=None):
        self.unpost()
        self.grab_release()

    def add_submenu(self, label, underline, **kwargs):
        parent = self
        accelerator = kwargs.pop('accelerator', None)
        if not accelerator: accelerator = label[underline].lower()
        menu = ttkMenu(parent)
        parent.add_cascade(menu=menu, label=label, underline=underline, accelerator=accelerator)
        return menu

    def add_section(self, menu, title, use_sep):
        ''' Add a separator, a title (disabled), and a set of commands from a menu into this menu. '''
        if use_sep:
            self.add_separator()
        if title:
            tk.Menu.add_command(self, label=title)
            self.entryconfigure(self.index(title), state=DISABLED)
        count = menu.index(END)+1
        for i in range(0, count):  # i would have thought it should be count-1, but that doesn't work
            self.add_command(
                label     = menu.entrycget(i, 'label'), 
                underline = menu.entrycget(i, 'underline'), 
                command   = menu.entrycget(i, 'command'),
                state     = menu.entrycget(i, 'state')
                )

    def add_command(self, label, underline, command, **kwargs):
        parent = self
        #char = label[underline].lower()
        tk.Menu.add_command(self, label=label, underline=underline, command=command, **kwargs)

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
        selectmode = kwargs.pop('selectmode', None)
        if selectmode and selectmode == SINGLE: kwargs['selectmode'] = BROWSE
        # get rid of keys that Treeview doesn't understand
        kwargs.pop('width', None)
        kwargs.pop('bg', None)
        kwargs.pop('fg', None)
        kwargs.pop('activestyle', None)
        # Set a context menu and bind it to right click
        self.on_item_popup = kwargs.pop('on_item_popup', None)
        self.off_item_popup = kwargs.pop('off_item_popup', None)
        self.scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL)
        ttk.Treeview.__init__(self, parent, yscrollcommand=self.scrollbar.set, **kwargs)
        self.scrollbar.config(command=self.yview)
        if self.on_item_popup or self.off_item_popup:
            self.bind("<ButtonPress-3><ButtonRelease-3>", self.show_popup)
        self.bind("<Up>", self.up_keypressed)
        self.bind("<Down>", self.down_keypressed)

    def up_keypressed(self, event=None):
        if len(self.selection()) == 0:
            children = self.get_children()
            if len(children) > 0:
                self.select(len(children)-1)

    def down_keypressed(self, event=None):
        if len(self.selection()) == 0:
            if len(self.get_children()) > 0:
                self.select(self.item_at(0))

    def show_popup(self, event=None, menu=None):
        if not event: return
        if menu:
            menu.tk_popup(event.x_root, event.y_root)
        else:
            iid = self.identify_row(event.y)
            if iid:
                # if the mouse is over an item, select it before showing the context menu.
                # unfortunately, the item loses focus so its highlight color is the 'not focused'
                # color. Moving the focusing calls after the popup would fix this, but then
                # the keyboard isn't focused to the popup menu.
                self.selection_set(iid)
                self.focus_set()
                self.focus(iid)
                if self.on_item_popup:
                    self.on_item_popup.tk_popup(event.x_root, event.y_root)
            else:
                # if the mouse is not over an item, don't do anything
                if self.off_item_popup:
                    self.off_item_popup.tk_popup(event.x_root, event.y_root)

    def delete(self, start, end):
        children = self.get_children()
        copy = children[:]
        if end == END:
            end = len(copy)
        for index in range(start, end):
            item = copy[index]
            ttk.Treeview.delete(self,item)
        #traceback.print_stack()
        return

    def pack(self, **kwargs):
        self.scrollbar.pack(side=RIGHT, fill=Y)
        ttk.Treeview.pack(self, **kwargs)

    def insert(self, index, text, *args, **kwargs):
        # item id of the parent item. Use '' to make a top level item.
        parent = kwargs.pop('parent', '')
        ttk.Treeview.insert(self, parent, index, text=text, *args, **kwargs)

    def add(self, parent, index, **kwargs):
        # set parent to '' to add to top level
        ttk.Treeview.insert(self, parent, index, **kwargs)

    def has_tag(self, item, tag):
        tags = self.item(item, option='tags')
        return tag in tags

    def add_tag(self, item, tag):
        tags = list(self.item(item, option='tags'))
        if not tag in tags:
            tags.append(tag)
        self.item(item, tags=tuple(tags))

    def remove_tag(self, item, tag):
        tags = list(self.item(item, option='tags'))
        if tag in tags:
            tags.remove(tag)
        self.item(item, tags=tuple(tags))

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
    
