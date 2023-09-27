# -*- coding: utf-8 -*-
# !python3

# Taken from ttkwidgets : https://github.com/RedFantom/ttkwidgets

import tkinter.ttk as ttk


class AutoHideScrollbar(ttk.Scrollbar):
    """Scrollbar that automatically hides when not needed."""

    def __init__(self, master=None, **kwargs):
        ttk.Scrollbar.__init__(self, master, **kwargs)
        self._pack_kw = {}
        self._place_kw = {}
        self._layout = 'place'

    def set(self, lo, hi):
        """Set the fractional values of the slider position."""
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            if self._layout == 'place':
                self.place_forget()
            elif self._layout == 'pack':
                self.pack_forget()
            else:
                self.grid_remove()
        else:
            if self._layout == 'place':
                self.place(**self._place_kw)
            elif self._layout == 'pack':
                self.pack(**self._pack_kw)
            else:
                self.grid()
        ttk.Scrollbar.set(self, lo, hi)

    def _get_info(self, layout):
        """Alternative to pack_info and place_info in case of bug."""
        info = str(self.tk.call(layout, 'info', self._w)).split("-")
        dic = {}
        for i in info:
            if i:
                key, val = i.strip().split()
                dic[key] = val
        return dic

    def place(self, **kw):
        """Place a widget in the parent widget."""
        ttk.Scrollbar.place(self, **kw)
        try:
            self._place_kw = self.place_info()
        except TypeError:
            # bug in some tkinter versions
            self._place_kw = self._get_info("place")
        self._layout = 'place'

    def pack(self, **kw):
        """Pack a widget in the parent widget."""
        ttk.Scrollbar.pack(self, **kw)
        try:
            self._pack_kw = self.pack_info()
        except TypeError:
            # bug in some tkinter versions
            self._pack_kw = self._get_info("pack")
        self._layout = 'pack'

    def grid(self, **kw):
        """Position a widget in the parent widget in a grid."""
        ttk.Scrollbar.grid(self, **kw)
        self._layout = 'grid'
