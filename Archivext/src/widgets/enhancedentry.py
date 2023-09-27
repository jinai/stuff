# -*- coding: utf-8 -*-
# !python3

import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk


class EnhancedEntry(ttk.Entry):
    def __init__(self, master, ph_text="", ph_color="#ABADB3", ph_slant="roman", image=None, compound="right",
                 blend=False, padding=None, image_padding=None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.ph_text = ph_text
        self.ph_color = ph_color
        self.ph_slant = ph_slant
        self.image = None
        self.compound = compound
        self.blend = blend
        self.padding = padding
        self.image_padding = image_padding

        # Internal variables that are not intended to be accessed using cget()
        self._ph_visible = False
        self._original_font = tkfont.Font(font=self.cget("font"))
        self._original_color = self.cget("foreground")

        # Config and bindings
        self._set_layout()
        self.configure(padding=padding, image=image, image_padding=image_padding)
        self.bind("<FocusIn>", self.focus_in, add="+")
        self.bind("<FocusOut>", self.focus_out, add="+")
        self.focus_out()

    def focus_in(self, event=None):
        print("focus_in: '{}'".format(super().get()))
        if self.ph_text:
            if super().get() == self.ph_text and self._ph_visible:
                with NoTrace(self.cget("textvariable")):
                    self.delete(0, "end")
                self._ph_visible = False
            self.configure(foreground=self._original_color)
            font = tkfont.Font(font=self._original_font)
            font.configure(slant=self.ph_slant)
            self.configure(font=font)

    def focus_out(self, event=None):
        print("focus_out: '{}'".format(super().get()))
        if self.get() == "" and self.ph_text:
            self._ph_visible = True
            super().configure(foreground=self.ph_color)
            font = tkfont.Font(font=self._original_font)
            font.configure(slant=self.ph_slant)
            self.configure(font=font)
            with NoTrace(self.cget("textvariable")):
                self.insert(0, self.ph_text)

    def get(self):
        print(f"\tget(): ph_visible={self._ph_visible}")
        if self._ph_visible:
            return ""
        return super().get()

    def insert(self, index, string):
        print(f"\tinsert(): {index} {string} (ph_visible={self._ph_visible})")
        if self._ph_visible:
            self.delete(0, "end")
        super().insert(index, string)

    def _set_layout(self):
        self._layout_name = "Enhanced_{}.TEntry".format(self.winfo_id())
        ttk.Style().layout(self._layout_name, [
            ("Entry.field", {
                "sticky": "nswe",
                "children": [
                    ("Entry.padding", {
                        "sticky": "nswe",
                        "children": [
                            ("Entry.textarea", {
                                "side": _flip(self.compound),
                                "sticky": "nswe",
                                "expand": 1
                            })
                        ]
                    }),
                    ("Entry.image", {
                        "side": self.compound,
                        "sticky": "we",
                    })
                ]
            })
        ])
        self.configure(style=self._layout_name)

    def cget(self, key):
        """
        Query widget options.

        To get the list of options for this widget, call :meth:`~EnhancedEntry.keys`.
        See :meth:`~EnhancedEntry.__init__` for a description of this widget's specific options.

        :param key: Option name
        :type key: str
        :return: Value of the option
        """
        if key == "ph_text":
            return self.ph_text
        elif key == "ph_color":
            return self.ph_color
        elif key == "ph_slant":
            return self.ph_slant
        elif key == "image":
            return self.image
        elif key == "compound":
            return self.compound
        elif key == "blend":
            return self.blend
        elif key == "padding":
            if self.image and not self.blend:
                # Actual padding without image
                return self.padding.clone().adjust(**{self.compound: -1 * self.image.width()})
            return self.padding
        elif key == "image_padding":
            return self.image_padding
        else:
            return super(EnhancedEntry, self).cget(key)

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)

        if "padding" in kwargs:
            new_padding = kwargs.pop("padding")
            if new_padding is None:
                new_padding = Padding.default_for("TEntry").adjust(left="+2", right="+2")
            else:
                new_padding = Padding.parse(new_padding)
            if self.image and not self.blend:
                # If blend mode is off, add as much pixels as the image width on the side it appears at
                # so that the text doesn't go over it
                new_padding.adjust(**{self.compound: self.image.width()})

            self.padding = new_padding
            ttk.Style().configure(self._layout_name, padding=self.padding)

        if "image" in kwargs:
            new_image = kwargs.pop("image")
            if not self.blend:
                # Adjust padding to accomodate new image
                delta = 0
                if self.image and new_image:
                    # Replacing image
                    delta = new_image.width() - self.image.width()
                elif self.image:
                    # Removing image
                    delta = -1 * self.image.width()
                elif not self.image and new_image:
                    # Adding image
                    delta = new_image.width()
                self.padding.adjust(**{self.compound: delta})
            # self.image = _pad_image(new_image, Padding.parse("10"))
            self.image = new_image
            ttk.Style().configure(self._layout_name, image=self.image, padding=self.padding)

        if "compound" in kwargs:
            new_compound = kwargs.pop("compound")
            if new_compound == _flip(self.compound):
                self.padding.left, self.padding.right = self.padding.right, self.padding.left
            self.compound = new_compound
            self._set_layout()

        if "blend" in kwargs:
            new_blend = kwargs.pop("blend")
            if self.image:
                if not self.blend and new_blend:
                    # Enable blending
                    self.padding.adjust(**{self.compound: self.image.width()})
                if self.blend and not new_blend:
                    # Disable blending
                    self.padding.adjust(**{self.compound: -1 * self.image.width()})
            self.blend = new_blend

        if "image_padding" in kwargs:
            new_img_padding = kwargs.pop("image_padding")
            # TODO

        return super().configure(**kwargs)


class NoTrace(object):
    def __init__(self, varname):
        self.varname = varname
        self.var = tk.StringVar(name=self.varname)
        # self.var = varname
        self.trace_info = self.var.trace_vinfo()
        print(f"\t\t\tvarname: {self.varname}")
        print(f"\t\t\tTRACE INFO: {self.trace_info}")
        print(f"\t\t\t_tclCommands: {self.var._tclCommands}")

    @property
    def mode(self):
        return self.trace_info[0][0] if self.trace_info else None

    @property
    def callback_name(self):
        return self.trace_info[0][1] if self.trace_info else None

    def __enter__(self):
        if self.mode == "w":
            print(f"__enter__: val={self.var.get()}")
            self.var._tclCommands.remove(self.callback_name)
            # self.var._tk.call('trace', 'remove', 'variable', self.varname, "write", self.callback_name)
            # self.var._tk.call("trace", "vdelete", self.var, "w", self.callback_name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mode == "w":
            print(f"__exit__: val={self.var.get()}")
            self.var._tclCommands.add(self.callback_name)
            # self.var._tk.call("trace", "add", "variable", self.varname, "write", self.callback_name)
            # self.var._tk.call("trace", "variable", self.var, "w", self.callback_name)


class Padding(object):
    def __init__(self, left=0, top=0, right=0, bottom=0):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def adjust(self, **kwargs):
        """
        Example ::
            >>> p = Padding.parse("1 1 1 1")
            >>> p.adjust(left="+2", top="-1", right=1, bottom=-2)
            >>> print(p)
            3 0 2 -1
        """
        for key, value in kwargs.items():
            current = self.__dict__[key]
            self.__dict__[key] = current + int(value)
        return self

    def clone(self):
        return Padding(self.left, self.top, self.right, self.bottom)

    @classmethod
    def default_for(cls, style_name):
        p = ttk.Style().lookup(style_name, "padding")
        if not p:
            return
        if isinstance(p, tuple):
            # Depending on the python version it can return a string or a tuple of pixel objects
            p = " ".join([str(x) for x in p])
        return cls.from_string(p)

    @classmethod
    def parse(cls, padding):
        if isinstance(padding, Padding):
            return padding.clone()
        elif isinstance(padding, str):
            return cls.from_string(padding)
        elif isinstance(padding, (list, tuple)):
            return cls.from_seq(padding)
        else:
            raise ValueError("Invalid padding format.")

    @classmethod
    def from_string(cls, padding_str):
        return Padding.from_seq([int(x) for x in padding_str.split()])

    @classmethod
    def from_seq(cls, values):
        n = len(values)
        if not 1 <= n <= 4:
            raise ValueError("Paddings take at least one argument and at most four: left, top, right and bottom.")

        if n == 1:
            values.extend([values[0], values[0], values[0]])
        elif n == 2:
            values.extend([values[0], values[1]])
        elif n == 3:
            values.append(values[1])

        return cls(*values)

    def __str__(self):
        return "{} {} {} {}".format(self.left, self.top, self.right, self.bottom)

    def __repr__(self):
        return "Padding(left={}, top={}, right={}, bottom={})".format(self.left, self.top, self.right, self.bottom)


def _flip(compound):
    if compound == tk.LEFT:
        return tk.RIGHT
    return tk.LEFT
