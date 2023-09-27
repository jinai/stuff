# -*- coding: utf-8 -*-
# !python3

import tkinter as tk


class HyperlinkManager(object):
    """
    A class to easily add clickable hyperlinks to Text widgets.

    Usage:
        callback = lambda: webbrowser.open("https://www.google.com/")
        text = tk.Text(...)
        hyperman = HyperlinkManager(text)
        text.insert(tk.INSERT, "click me", hyperman.add(callback))
    Source:
        http://effbot.org/zone/tkinter-text-hyperlink.htm
    """

    def __init__(self, text):
        self.text = text
        self.text.tag_config("hyper", foreground="blue", underline=1)
        self.text.tag_bind("hyper", "<Enter>", self._enter)
        self.text.tag_bind("hyper", "<Leave>", self._leave)
        self.text.tag_bind("hyper", "<Button-1>", self._click)
        self.links = {}

    def reset(self):
        self.links.clear()

    def add(self, callback, callback_name=None):
        tag = "hyper-%d" % len(self.links)
        self.links[tag] = (callback, callback_name)
        return "hyper", tag

    def _enter(self, event):
        self.text.config(cursor="hand2")

    def _leave(self, event):
        self.text.config(cursor="")

    def _click(self, event):
        for tag in self.text.tag_names(tk.CURRENT):
            if (tag[:6] == "hyper-"):
                callback, callback_name = self.links[tag]
                callback(tag, callback_name)
                return
