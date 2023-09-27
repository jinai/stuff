# -*- coding: utf-8 -*-
# !python3

import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk
from builtins import isinstance


class EnhancedEntry(ttk.Entry):
    def __init__(self, master, ph_text="", ph_color="#ABADB3", ph_slant="roman", image=None, compound="right",
                 blend=False, padding=None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.ph_text = ph_text
        self.ph_color = ph_color
        self.ph_slant = ph_slant
        self.image = None
        self.compound = compound
        self.blend = blend
        self.padding = padding
        self._ph_visible = False
        self._original_font = tkfont.Font(font=self.cget("font"))
        self._original_color = self.cget("foreground")
        self._layout_name = "Enhanced_{}.TEntry".format(self.winfo_id())
        self._style = ttk.Style()
        self._set_layout()
        self.configure(image=image, padding=padding)
        self.bind("<FocusIn>", self.focus_in, add="+")
        self.bind("<FocusOut>", self.focus_out, add="+")
        self.focus_out()



    # def __getitem__(self, key):
    #     return self.cget(key)
    #
    # def __setitem__(self, key, value):
    #     self.configure({key: value})

    def focus_in(self, event=None):
        if super().get() == self.ph_text and self._ph_visible:
            self.delete(0, "end")
        self.configure(foreground=self._original_color)
        font = tkfont.Font(font=self._original_font)
        font.configure(slant=self.ph_slant)
        self.configure(font=font)
        self._ph_visible = False

    def focus_out(self, event=None):
        if self.get() == "" and self.ph_text:
            super().configure(foreground=self.ph_color)
            font = tkfont.Font(font=self._original_font)
            font.configure(slant=self.ph_slant)
            self.configure(font=font)
            self.insert(0, self.ph_text)
            self._ph_visible = True

    # def set_ph_text(self, ph_text):
    #     self.ph_text = ph_text
    #     if self._ph_visible:
    #         self.delete(0, "end")
    #         self.insert(0, self.ph_text)

    # def show_placeholder(self):
    #     self.delete(0, "end")
    #     self.configure(foreground=self.ph_color)
    #     self.set_slant(self.ph_slant)
    #     self.insert(0, self.ph_text)
    #     self._ph_visible = True

    # def set_padding(self, padding=None):
    #     if padding is None:
    #         self.padding = Padding.default_for("TEntry")
    #         self.padding.adjust(left="+2", right="+2")
    #     else:
    #         self.padding = Padding.parse(padding)
    #
    #     if self.image and not self.blend:
    #         # Make room for the image so that the text doesn't go over it
    #         self.padding.adjust(**{self.compound: self.image.width()})
    #     self._style.configure(self._layout_name, padding=self.padding)

    def _set_layout(self):
        self._style.layout(self._layout_name, [
            ("Entry.field", {
                "sticky": "nswe",
                "children": [
                    ("Entry.padding", {
                        "sticky": "nswe",
                        "expand": 1,
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

    def get(self):
        if self._ph_visible:
            return ""
        return super().get()

    def insert(self, index, string):
        if self._ph_visible:
            self.delete(0, "end")
        super().insert(index, string)

    def cget(self, key):
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
                return self.padding.adjust(**{self.compound: -1 * self.image.width()})
            return self.padding
        else:
            return super().cget(key)

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)

        if "ph_text" in kwargs:
            self.ph_text = kwargs.pop("ph_text")
            if self._ph_visible:
                self.delete(0, "end")
                self.insert(0, self.ph_text)

        if "ph_color" in kwargs:
            self.ph_color = kwargs.pop("ph_color")
            if self._ph_visible:
                self.configure(foreground=self.ph_color)

        if "ph_slant" in kwargs:
            self.ph_slant = kwargs.pop("ph_slant")
            if self._ph_visible:
                font = tkfont.Font(font=self._original_font)
                font.configure(slant=self.ph_slant)
                self.configure(font=font)

        if "padding" in kwargs:
            new_padding = kwargs.pop("padding")
            if new_padding is None:
                new_padding = Padding.default_for("TEntry")
                new_padding.adjust(left="+2", right="+2")
            else:
                new_padding = Padding.parse(new_padding)
            if self.image and not self.blend:
                # Make room for the image so that the text doesn't go over it
                new_padding.adjust(**{self.compound: self.image.width()})

            self.padding = new_padding
            self._style.configure(self._layout_name, padding=self.padding)

        if "image" in kwargs:
            new_image = kwargs.pop("image")
            if new_image is None:
                new_image = ""  # Needed for tkinter or it raises an error
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
            self.image = new_image
            self._style.configure(self._layout_name, image=self.image, padding=self.padding)

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

        return super().configure(**kwargs)

    config = configure

    def keys(self):
        """Return a list of all resource names of this widget."""
        keys = super().keys()
        keys.extend(["ph_text", "ph_color", "ph_slant", "image", "compound", "padding"])
        return keys


class Padding():
    """
    Based on: `ttk:widget manual page <https://www.tcl.tk/man/tcl8.6/TkCmd/ttk_widget.htm#M-padding>`_.

    This class represents the internal padding for a widget. The padding is a list of up to four length specifications *left top right bottom*.
    If fewer than four elements are specified, *bottom* defaults to *top*, *right* defaults to *left*, and *top* defaults to *left*.
    In other words:
        - a list of three numbers specify the left, vertical, and right padding;
        - a list of two numbers specify the horizontal and the vertical padding;
        - a single number specifies the same padding all the way around the widget.
    """

    def __init__(self, left=0, top=0, right=0, bottom=0):
        """
        Initializes paddings.
        Standard usage is through `Padding.from_string()` or `Padding.from_seq()`.
        """
        for x in (left, top, right, bottom):
            if x < 0:
                raise ValueError('Invalid padding "{}": paddings must be non-negative integers.'.format(x))

        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def adjust(self, **kwargs):
        """Adjust paddings by a certain amount. It never goes under zero."""
        for key, value in kwargs.items():
            current = self.__dict__[key]
            self.__dict__[key] = max(current + int(value), 0)
        return self

    @classmethod
    def default_for(cls, style_name):
        p = ttk.Style().lookup(style_name, "padding")
        if isinstance(p, tuple):
            # Depending on the python version it can return a string or a tuple of pixel objects
            p = " ".join([str(x) for x in p])
        return cls.from_string(p)

    @classmethod
    def parse(cls, padding):
        if isinstance(padding, Padding):
            return padding
        elif isinstance(padding, str):
            return cls.from_string(padding)
        elif isinstance(padding, (list, tuple)):
            return cls.from_seq(padding)
        else:
            raise ValueError("Invalid padding format.")

    @classmethod
    def from_string(cls, padding_str):
        """Construct a padding object from a string of paddings"""
        return Padding.from_seq([int(x) for x in padding_str.split()])

    @classmethod
    def from_seq(cls, values):
        """Construct a padding object from a sequence of paddings."""
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
        """Output format required for ttk style layouts."""
        return "{} {} {} {}".format(self.left, self.top, self.right, self.bottom)

    def __repr__(self):
        return "Padding(left={}, top={}, right={}, bottom={})".format(self.left, self.top, self.right, self.bottom)


def _flip(compound):
    if compound == tk.LEFT:
        return tk.RIGHT
    return tk.LEFT


if __name__ == "__main__":
    app = tk.Tk()
    # app.geometry("200x150")
    frame = ttk.Frame(app)
    frame.pack(padx=20, pady=20, fill="both", expand=True)
    ph_text = "Search"
    e1 = EnhancedEntry(frame, width=30, image=tk.PhotoImage(file="../data/img/search.gif"), ph_text=ph_text,
                       padding="100 1 10 1")
    e1.pack()
    e2 = EnhancedEntry(frame, image=tk.PhotoImage(file="../data/img/gradient2.png"), ph_text="", blend=False, width=0)
    e2.pack(pady=1)
    e3 = EnhancedEntry(frame, ph_text=ph_text, blend=True,)# image=tk.PhotoImage(file="../data/img/gradient3.png"))
    e3.pack(pady=1)
    e4 = ttk.Entry(frame, width=30)
    e4.pack()
    btn = ttk.Button(frame, text="Adjust", command=lambda: e2.configure(padding=e2.cget("padding").adjust(top="+2", bottom="+2")))
    btn.pack(fill="x")
    btn2 = ttk.Button(frame, text="Print padding", command=lambda: print(e2.cget("padding")))
    btn2.pack(fill="x")

    app.mainloop()
