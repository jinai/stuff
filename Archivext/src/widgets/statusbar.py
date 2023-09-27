# -*- coding: utf-8 -*-
# !python3

import os
import tkinter as tk
from tkinter import ttk

import utils
from widgets.frameseparator import FrameSeparator
from widgets.infowindow import InfoWindow


class StatusBar(ttk.Frame):
    def __init__(self, master, **opts):
        ttk.Frame.__init__(self, master, **opts)
        self.master = master
        self.border = FrameSeparator(self, orient="horizontal")
        self.border.pack(side="top")
        self.frame = ttk.Frame(self)
        self.frame.pack(fill="both", expand=True)
        self.frame.grid_columnconfigure(0, weight=1)
        self.label_main = ttk.Label(self.frame)
        self.label_main.grid(row=0, column=0, sticky="ew", padx=(2, 0))
        self.sep1 = FrameSeparator(self.frame, orient="vertical", color="#DFDFDF")
        self.sep1.grid(row=0, column=1, sticky="ns", padx=5)
        self.label_amount = ttk.Label(self.frame)
        self.label_amount.grid(row=0, column=2, sticky="ew")
        self.sep2 = FrameSeparator(self.frame, orient="vertical", color="#DFDFDF")
        self.sep2.grid(row=0, column=3, sticky="ns", padx=5)
        self.label_location = ttk.Label(self.frame, cursor="hand2")
        self.label_location.grid(row=0, column=4, sticky="ew")
        self.sep3 = FrameSeparator(self.frame, orient="vertical", color="#DFDFDF")
        self.sep3.grid(row=0, column=5, sticky="ns", padx=5)
        self.info_icon = tk.PhotoImage(file=utils.fix_path("data/img/info.png"))
        self.label_info = ttk.Label(self.frame, image=self.info_icon, cursor="hand2")
        self.label_info.grid(row=0, column=6)
        self.sizegrip = ttk.Sizegrip(self.frame)
        self.sizegrip.grid(row=0, column=7, sticky="es", padx=(10, 0))

        self._textvar_main = tk.StringVar()
        self._textvar_amount = tk.StringVar()
        self._textvar_location = tk.StringVar()
        self.label_main.configure(textvariable=self._textvar_main)
        self.label_amount.configure(textvariable=self._textvar_amount)
        self.label_location.configure(textvariable=self._textvar_location)
        self.label_location.bind("<Button-1>", self.location_click)
        self.label_info.bind("<Button-1>", self.info_click)

        self._default_text = ""
        self._clear_id = None
        self._info_window = None

    def set(self, new_text, clear_after=10000):
        self._textvar_main.set(new_text)
        if clear_after > 0:
            self.schedule_clear(clear_after)
        else:
            self.unschedule_clear()

    def clear(self):
        self._textvar_main.set(self._default_text)

    def schedule_clear(self, delay):
        self.unschedule_clear()
        self._clear_id = self.after(delay, self.clear)

    def unschedule_clear(self):
        id = self._clear_id
        self._clear_id = None
        if id:
            self.after_cancel(id)

    def set_default_text(self, new_text):
        self._default_text = new_text

    def set_amount(self, new_text):
        self._textvar_amount.set(new_text)

    def set_location(self, new_text):
        self._textvar_location.set(new_text)

    def location_click(self, event):
        try:
            os.startfile(self._textvar_location.get())
        except OSError:
            pass

    def info_click(self, event):
        if self._info_window and self._info_window.winfo_exists():
            self._info_window.lift()
        else:
            self._info_window = InfoWindow(self, is_transient=True, centered=True)
            self._info_window.spawn()
