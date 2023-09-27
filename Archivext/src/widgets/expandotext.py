# -*- coding: utf-8 -*-
# !python3

import tkinter as tk


class ExpandoText(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        self.height = 0

    def insert(self, *args, **kwargs):
        result = super().insert(*args, **kwargs)
        self.resize()
        return result

    def resize(self):
        self.update()
        height = self.count("1.0", "end", "displaylines")
        width = self.cget("width")
        if height == 1:
            width = len(self.get("1.0", "end")) + 1
        self.configure(height=height, width=width)
        self.height = height
