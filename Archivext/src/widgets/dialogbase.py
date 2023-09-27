# -*- coding: utf-8 -*-
# !python3

import tkinter as tk
import tkinter.ttk as ttk


class DialogBase(tk.Toplevel):
    def __init__(self, master, *, dialog_title=None, can_resize=True, is_modal=False, is_transient=False,
                 centered=False, stay_centered=False):
        super().__init__()
        self.withdraw()
        self.master = master
        self.dialog_title = dialog_title
        self.can_resize = can_resize
        self.is_modal = is_modal
        self.is_transient = is_transient
        self.centered = centered
        self.stay_centered = stay_centered
        self.result = None

    #
    # construction hooks

    def spawn(self):
        self.attributes('-alpha', 0.0)
        self.deiconify()
        self.title(self.dialog_title)
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=5, pady=(5, 0))
        self.initial_focus = self.body(main_frame)
        self.buttonbox()
        if not self.initial_focus:
            self.initial_focus = self
        self.initial_focus.focus_set()
        self.initial_focus.focus_force()
        self.protocol("WM_DELETE_WINDOW", lambda *_: self.cancel())
        self.bind("<Return>", lambda *_: self.ok())
        self.bind("<Escape>", lambda *_: self.cancel())
        self.master_window = self.master.winfo_toplevel()
        if self.centered:
            self.center()
            if self.stay_centered:
                self.config_bind_id = self.master_window.bind("<Configure>", lambda _: self.center(), add="+")
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.resizable(width=self.can_resize, height=self.can_resize)
        self.attributes('-alpha', 1.0)
        if self.is_transient:
            self.transient(self.master_window)
        if self.is_modal:
            self.master_window.wm_attributes("-disabled", True)
            self.grab_set()
            self.wait_window(self)

    def center(self, reference_widget=None):
        self.update_idletasks()
        if reference_widget is None:
            reference_widget = self.master_window
        width = self.winfo_width()
        frm_width = self.winfo_rootx() - self.winfo_x()
        win_width = width + (2 * frm_width)
        height = self.winfo_height()
        titlebar_height = self.winfo_rooty() - self.winfo_y()
        win_height = height + titlebar_height + frm_width
        x = reference_widget.winfo_rootx() + (reference_widget.winfo_width() // 2) - (win_width // 2)
        y = reference_widget.winfo_rooty() + (reference_widget.winfo_height() // 2) - (win_height // 2) - 9
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def body(self, container):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        box = ttk.Frame(self)
        box.pack(pady=(15, 10))
        button_ok = ttk.Button(box, text="OK", width=10, command=self.ok, default="active")
        button_ok.pack(side="left", padx=4)
        button_cancel = ttk.Button(box, text="Annuler", width=10, command=self.cancel)
        button_cancel.pack(side="right", padx=4)

    #
    # standard button semantics

    def ok(self):
        if not self.validate():
            self.initial_focus.focus_set()  # put focus back
            return

        self.apply()
        self.cancel()

    def cancel(self):
        # put focus back to the parent window
        if self.is_modal:
            self.master_window.wm_attributes("-disabled", False)
        if self.centered and self.stay_centered:
            self.master_window.unbind("<Configure>", self.config_bind_id)
        self.destroy()

    #
    # command hooks

    def validate(self):
        return True  # override

    def apply(self):
        pass  # override


class WelcomeDialog(DialogBase):
    def __init__(self, master, *, body_text='', button_text="OK", font=None, **kwargs):
        super().__init__(master, **kwargs)
        self.body_text = body_text
        self.button_text = button_text
        self.font = font

    def body(self, container):
        container.configure(width=500)
        self.msg = tk.Message(container, text=self.body_text, width=500)
        if self.font:
            self.msg.config(font=self.font)
        self.msg.pack(fill="both", expand=True)
        return self.msg

    def buttonbox(self):
        box = ttk.Frame(self)
        box.pack(pady=(15, 10))
        button = ttk.Button(box, text=self.button_text, command=self.ok)
        button.pack(side="left", padx=4)
