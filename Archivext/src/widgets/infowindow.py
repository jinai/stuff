# -*- coding: utf-8 -*-
# !python3

import tkinter as tk
import tkinter.ttk as ttk
import webbrowser

from _meta import __version__, __author__, __email__, __date__
from widgets import hyperlinkmanager
from widgets.dialogbase import DialogBase
from widgets.expandotext import ExpandoText


class InfoWindow(DialogBase):
    def __init__(self, master, **kwargs):
        super().__init__(master, dialog_title="À propos", **kwargs)
        self.master = master

    def body(self, container):
        self.textbox = ExpandoText(container, width=50, wrap="word", font="TkDefaultFont", relief="flat",
                                   background=ttk.Style().lookup("TFrame", "background"))
        self.textbox.pack(fill="both", expand=True)
        self.hyperman = hyperlinkmanager.HyperlinkManager(self.textbox)
        self.update_idletasks()
        self.textbox.insert(tk.INSERT, f"Version : {__version__} ({__date__})\n")
        self.textbox.insert(tk.INSERT, f"Auteur : {__author__}\n")
        self.textbox.insert(tk.INSERT, "Site web : ")
        self.textbox.insert(tk.INSERT, "https://respomap.herokuapp.com/\n",
                            self.hyperman.add(self._click_handler, "website"))
        self.textbox.insert(tk.INSERT, "Email : ")
        self.textbox.insert(tk.INSERT, f"{__email__}\n", self.hyperman.add(self._click_handler, "email"))
        self.textbox.config(state="disabled")

    def _click_handler(self, index, name):
        if name == "website":
            webbrowser.open("https://respomap.herokuapp.com/")
        if name == "email":
            webbrowser.open(f"mailto:{__email__}")

    def buttonbox(self):
        box = ttk.Frame(self)
        box.pack(pady=(15, 10))
        w = ttk.Button(box, text="Fermer", width=12, command=self.ok)
        w.pack(padx=4)
