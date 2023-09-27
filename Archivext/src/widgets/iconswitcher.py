# -*- coding: utf-8 -*-
# !python3

import tkinter as tk
import tkinter.ttk as ttk


class IconSwitcher(ttk.Frame):
    def __init__(self, *args, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)
        self.icons = []
        self.named_icons = {}
        self.current = -1
        self.icon_static = None
        self.icon_animated = None
        self.after_id = None

    def add(self, path, name=None):
        icon = LabelGif(self)
        icon.from_path(path)
        self.icons.append(icon)
        if name:
            self.named_icons[name] = icon
            icon.name = name

    def current_name(self):
        if self.icons:
            return self.icons[self.current].name

    def select(self, name, hide_delay=0):
        i = self.icons.index(self.named_icons[name])
        self.switch(i, hide_delay)

    def cycle(self, hide_delay=0):
        if self.icons:
            index = self.current + 1
            if index == len(self.icons):
                index = 0
            self.switch(index, hide_delay)

    def switch(self, index, hide_delay=0):
        self.hide()
        self.current = index
        icon = self.icons[self.current]
        icon.pack()
        icon.play()
        if hide_delay > 0:
            self.after_id = self.after(hide_delay, self.hide)

    def hide(self):
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None
        icon = self.icons[self.current]
        icon.pack_forget()
        icon.stop()


class LabelGif(ttk.Label):
    def __init__(self, master, frame_delay=70):
        ttk.Label.__init__(self, master)
        self.master = master
        self.frame_delay = frame_delay  # Milliseconds
        self.path = None
        self.base64 = None
        self.frames = []
        self.current_frame = 0
        self.after_id = None

    def from_path(self, path):
        self.base64 = None
        self.path = path
        self.frame0 = tk.PhotoImage(file=path, format="gif -index 0")
        self.load_frames()

    def from_string(self, base64):
        self.path = None
        self.base64 = base64
        self.frame0 = tk.PhotoImage(data=base64, format="gif -index 0")
        self.load_frames()

    def load_frames(self):
        self.frames = [self.frame0]
        i = 1
        try:
            while True:
                if self.path:
                    self.frames.append(tk.PhotoImage(file=self.path, format="gif -index " + str(i)))
                else:
                    self.frames.append(tk.PhotoImage(data=self.base64, format="gif -index " + str(i)))
                i += 1
        except tk.TclError:
            pass  # No more frames

    def play(self):
        self.configure(image=self.frames[self.current_frame])
        self.current_frame += 1
        if self.current_frame == len(self.frames):
            self.current_frame = 0
        self.after_id = self.after(self.frame_delay, self.play)

    def stop(self):
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None
            self.current_frame = 0

    def reverse(self):
        self.frames = self.frames[::-1]
