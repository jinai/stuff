# -*- coding: utf-8 -*-
# !python3

import tkinter as tk
import tkinter.ttk as ttk

from widgets.enhancedentry import EnhancedEntry

search_icon = """
        iVBORw0KGgoAAAANSUhEUgAAABIAAAAQCAYAAAAbBi9cAAAABHNCSVQICAgIfAhkiAAA
        AAlwSFlzAAAchAAAHIQBhemxiwAAAB90RVh0U29mdHdhcmUATWFjcm9tZWRpYSBGaXJl
        d29ya3MgOLVo0ngAAAHZSURBVDiNlZOxaxNxFMc/75eYFApFtF2tBUc3qYKLOJkuxSzi
        4BBrsCTB09X/wMli0kt6XmMXHZRCCw7ipB2cxE7JVv8FoYKxibl7Drk7f5wXwe907/3e
        +/y+78c7wVLL95fMOPdQ0RKwCPJTCHvAm+DXwHccZ0hKqgqAxAl3a7uuKhtAIV0c6SiH
        lmu1am8qKIK4UwC2vkmoVxqN6lEaZFq+v6QqT63iY4HHiF4T0VURfWmdndGcPM+6IR+9
        STGGhCZ3yVmvfLVq3m62u18QNiYWuO66O8uNxt3PNshEDxvP+SQFAaBRW3sGHP7pCkvp
        GgOci4NAzacs2yKiih4kCWUxAyQncZAzweks0MS6zMXfoej3v0GqfSu+lQXxPG9ehVXL
        Yj9dY0T0deJY5c5mu/tIVZP98jxvfqT5V8BClBoUZLybBkmz2SyaU7M94IKVP1T0wKjM
        RU4WrLOhKuUH9XvvJpdbC9npbF8MkI/A2azRMpTAkoUEqNWqPaNyGeHDlMYBYP9nRRH2
        Wu3uSjJausN1d5YxYUmR80p4jEi/IOPdUZC/KsIeUEyahf36+lo5E/QvtTovbgi6D8wA
        72dnzM1KpXLy3yCAVru7Ygz3g9GP247jDOM3+g3jWbxvrZAt0QAAAABJRU5ErkJggg==
    """

user_icon = """
    iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAA
    AlwSFlzAAAAZAAAAGQBeJH1SwAAAB90RVh0U29mdHdhcmUATWFjcm9tZWRpYSBGaXJld2
    9ya3MgOLVo0ngAAAEUSURBVDiNnZGxSgNREEXPfW4+QMEmED/B2FnaaSN+gxrS7IKNTcD
    SlBGLJWX8AC2tLAKWloJVWrVIowHLgG8sNpuYdcnuemGKGeaeuTAio37/pmHOroF9AImh
    PJ0wbI1+75kZAMoxPwMby1hN5GlG0elbFuCWqMnljBnA1lnj6u88A0hj58nMDsoAVskKA
    RLDFYCHYoCnA5rk7H34wJ8XAsKwNZKnKekO+JrVrQ/8zlm7/Z4HUN6wjNI3BgBxPKirRh
    fjkOSNj4iXZJNtYA/4BN3L6yKKTsbzBHE8qCvgCWiUu61Xee2G4fEYwKlGt7wZwLbMfV+
    mnZvFrigdLQCwWR2w8Dhg+g/A3OOAXkXIVFgvbX4AipxU64CPlasAAAAASUVORK5CYII=
"""

key_icon = """
    iVBORw0KGgoAAAANSUhEUgAAABIAAAAQCAYAAAAbBi9cAAAABHNCSVQICAgIfAhkiAAA
    AAlwSFlzAAAAZAAAAGQBeJH1SwAAAB90RVh0U29mdHdhcmUATWFjcm9tZWRpYSBGaXJl
    d29ya3MgOLVo0ngAAAE6SURBVDiNldO9TgJBFIbh9wyUWpiYYAmlhV6FidFaC0NIjEJY
    A2LLJdBjMsVG6aisiYmF90Bhi6HS2BlCocweC9lk3R9cTjU5M3nmm5ldYUX1fb8iznRR
    joES8I4w0kLQu240JgCqCoBkIvb+UNAHYCNleiaipy2v/rgS6vt+RRZmHEMCER3+ppAq
    MCtg9j3v/BXApEHiTDeeRESHLa9ea3n1GjAENh3aDedToeWd5KmjcFDMWLCdsFWqt/ZO
    QAT0bNkt/QdNgN1YT4AqaLT3Fg4SR7N2UAa2MjaI5xylQtYOyo7gGdjJoXw643oJKIKU
    8yBIcHLTbE7/QDmQOfAFMgW1ziz22l7jKbqgmAMZB99y0OlcfKyKWHQEoyykfXWZ+QvF
    y5B85rBe8iKQ8R2tkySaKL7zWknC+gHrnW5qvA6S/QAAAABJRU5ErkJggg==
"""


class Example(ttk.Frame):
    def __init__(self, master, **kwargs):
        ttk.Frame.__init__(self, master, **kwargs)
        self.padding_var = tk.StringVar()
        self.eval_var = tk.StringVar()
        self.placeholder = "Search"
        self.padding = "7 3"
        self.search_icon = tk.PhotoImage(data=search_icon)  # Image.open(BytesIO(base64.b64decode(search_icon)))
        self.user_icon = tk.PhotoImage(data=user_icon)  # Image.open(BytesIO(base64.b64decode(user_icon)))
        self.key_icon = tk.PhotoImage(data=key_icon)  # Image.open(BytesIO(base64.b64decode(key_icon)))
        self.setup()
        self.reset_padding()

    def query_callback(self, name, index, mode):
        print("==========")
        print("Query: '{}'".format(self.query.get()))
        print("Placeholder: {}".format(self.searchbar._ph_visible))
        print("Trace info: {}".format(self.query.trace_info()))
        print(self.searchbar.cget("textvariable"))
        print("==========")

    def setup(self):
        self.query = tk.StringVar(value=self.placeholder)
        self.searchbar = EnhancedEntry(self, image=self.search_icon, ph_text=self.placeholder, padding=self.padding,
                                       blend=True)
        self.searchbar.configure(textvariable=self.query)
        self.query.trace("w", self.query_callback)
        # var = tk.StringVar(name=self.query._name)
        # print(var._tclCommands)
        # var.set("test")
        self.searchbar.pack(fill="x", pady=(0, 20))
        self.padding_frame = ttk.Frame(self)
        self.padding_frame.pack(pady=3)
        self.padding_label = ttk.Label(self.padding_frame, text="Padding: ")
        self.padding_label.pack(side="left")
        self.padding_value = ttk.Label(self.padding_frame, textvariable=self.padding_var)
        self.padding_value.pack(side="left")

        self.adjust_frame = ttk.Frame(self)
        self.adjust_frame.pack(fill="x", expand=True)
        adjust = lambda side, sign="+": lambda: self.adjust_padding(side, sign)
        self.left = ttk.LabelFrame(self.adjust_frame, text="Left", labelanchor="n", padding=3)
        self.left.pack(side="left", fill="x", expand=True)
        self.plus_left = ttk.Button(self.left, text="+", width=3, command=adjust("left"))
        self.plus_left.pack(side="left", fill="x", expand=True)
        self.min_left = ttk.Button(self.left, text="-", width=3, command=adjust("left", "-"))
        self.min_left.pack(side="right", fill="x", expand=True)

        self.top = ttk.LabelFrame(self.adjust_frame, text="Top", labelanchor="n", padding=3)
        self.top.pack(side="left", fill="x", expand=True, padx=3)
        self.plus_top = ttk.Button(self.top, text="+", width=3, command=adjust("top"))
        self.plus_top.pack(side="left", fill="x", expand=True)
        self.min_top = ttk.Button(self.top, text="-", width=3, command=adjust("top", "-"))
        self.min_top.pack(side="right", fill="x", expand=True)

        self.right = ttk.LabelFrame(self.adjust_frame, text="Right", labelanchor="n", padding=3)
        self.right.pack(side="left", fill="x", expand=True)
        self.plus_right = ttk.Button(self.right, text="+", width=3, command=adjust("right"))
        self.plus_right.pack(side="left", fill="x", expand=True)
        self.min_right = ttk.Button(self.right, text="-", width=3, command=adjust("right", "-"))
        self.min_right.pack(side="right", fill="x", expand=True)

        self.bottom = ttk.LabelFrame(self.adjust_frame, text="Bottom", labelanchor="n", padding=3)
        self.bottom.pack(side="left", fill="x", expand=True, padx=(3, 0))
        self.plus_bottom = ttk.Button(self.bottom, text="+", width=3, command=adjust("bottom"))
        self.plus_bottom.pack(side="left", fill="x", expand=True)
        self.min_bottom = ttk.Button(self.bottom, text="-", width=3, command=adjust("bottom", "-"))
        self.min_bottom.pack(side="right", fill="x", expand=True)

        self.reset_button = ttk.Button(self, text="Reset padding", command=self.reset_padding)
        self.reset_button.pack(fill="x", pady=3)

        self.eval_frame = ttk.Frame(self)
        self.eval_frame.pack(fill="x")
        self.eval_button = ttk.Button(self.eval_frame, text="eval()", command=self.eval_)
        self.eval_button.pack(side="left")
        self.eval_label = ttk.Label(self.eval_frame, text=":")
        self.eval_label.pack(side="left")
        self.eval_result = ttk.Label(self.eval_frame, textvariable=self.eval_var)
        self.eval_result.pack(side="left")

        self.login_button = ttk.Button(self, text="Login window", command=self.login_window)
        self.login_button.pack(fill="x", pady=(10, 0))
        # self.after(100, self.login_button.invoke)

    def login_window(self):
        self.login_toplevel = tk.Toplevel(self)
        self.login_toplevel.wm_title("Example - Login window")
        container = ttk.Frame(self.login_toplevel)
        container.pack(fill="both", expand=True, padx=40, pady=20)
        # login_label = ttk.Label(container, text="LOGIN", justify="center")
        # login_label.pack(pady=(0, 20))
        # font = tkfont.Font(font=login_label['font']).copy()
        # font.configure(size=16)
        # login_label.configure(font=font)
        padding = "8 5"
        username_input = EnhancedEntry(container, ph_text="Username", image=self.user_icon, padding=padding)
        username_input.pack(fill="x", padx=1)
        password_input = EnhancedEntry(container, show="•", ph_text="Password", image=self.key_icon,
                                       padding=padding)
        password_input.pack(fill="x", padx=1, pady=3)
        login_button = ttk.Button(container, text="Login")
        login_button.pack(fill="x", pady=(10, 0), ipady=3)
        self.login_toplevel.update_idletasks()
        self.login_toplevel.minsize(width=self.login_toplevel.winfo_reqwidth() + 100,
                                    height=self.login_toplevel.winfo_reqheight())

    def adjust_padding(self, side, op="+"):
        sign = 1 if op == "+" else -1
        padding = self.searchbar.cget("padding").adjust(**{side: sign})
        self.searchbar.configure(padding=padding)
        self.padding_var.set(padding)

    def reset_padding(self):
        self.searchbar.configure(padding=self.padding)
        self.padding_var.set(self.searchbar.cget("padding"))

    def eval_(self):
        try:
            self.eval_var.set(str(eval(self.searchbar.get())))
        except Exception as e:
            self.eval_var.set(e)


if __name__ == '__main__':
    root = tk.Tk()
    root.wm_title("Example - Searchbar")
    example = Example(root)
    example.pack(fill="x", expand=False, padx=20, pady=20)
    root.update_idletasks()
    root.minsize(width=root.winfo_reqwidth(), height=root.winfo_reqheight())
    root.mainloop()
