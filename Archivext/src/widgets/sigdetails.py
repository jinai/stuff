# -*- coding: utf-8 -*-
# !python3

import logging
import tkinter as tk
import tkinter.ttk as ttk
import webbrowser

import pyperclip

import utils
from widgets.dialogbase import DialogBase
from widgets.expandotext import ExpandoText

logger = logging.getLogger(__name__)


class SigDetails(DialogBase):
    def __init__(self, master, *, values, **kwargs):
        super().__init__(master, **kwargs)
        self.num = values[0]
        self.date = values[1]
        self.auteur = values[2]
        self.code = values[3]
        self.flag = values[4]
        self.desc = values[5]
        self.statut_raw = values[6]
        self.respo_raw = values[7]
        self.statut = ""
        self.comment = ""
        self.respo = []
        self.urls = []
        self.parse_status()
        self.parse_respo()
        self.parse_urls()

    def body(self, main_frame):
        date_frame = ttk.Frame(main_frame)
        date_label = ttk.Label(date_frame, text="Date :")
        date_label.pack(side="left")
        date_value = ttk.Label(date_frame, text=self.date, foreground="gray40")
        date_value.pack(side="left")

        auteur_frame = ttk.Frame(main_frame)
        auteur_label = ttk.Label(auteur_frame, text="Auteur :")
        auteur_label.pack(side="left")
        auteur_value = ttk.Label(auteur_frame, text=self.auteur, foreground="gray40")
        auteur_value.pack(side="left")

        code_frame = ttk.Frame(main_frame)
        code_label = ttk.Label(code_frame, text="Code :")
        code_label.pack(side="left")
        code_value = ttk.Label(code_frame, text=self.code, foreground="gray40")
        code_value.pack(side="left")
        self.copy_icon = tk.PhotoImage(file=utils.fix_path("data/img/copy.png"))
        copy_button = ttk.Button(code_frame, image=self.copy_icon, command=lambda: self.copy_code(copy_button),
                                 takefocus=False)
        copy_button.pack(side="left", padx=(2, 0))

        flag_frame = ttk.Frame(main_frame)
        flag_label = ttk.Label(flag_frame, text="Flag :")
        flag_label.pack(side="left")
        flag_value = ttk.Label(flag_frame, text=self.flag, foreground="gray40")
        flag_value.pack(side="left")

        desc_frame = ttk.Frame(main_frame)
        desc_label = ttk.Label(desc_frame, text="Raison :")
        desc_label.pack(side="left", anchor="nw")
        desc_text = ExpandoText(desc_frame, width=40, height=1, wrap="word", font="TkDefaultFont", relief="flat",
                                foreground="gray40", background=ttk.Style().lookup("TFrame", "background"))
        desc_text.pack(side="left", anchor="w")

        statut_frame = ttk.Frame(main_frame)
        statut_label = ttk.Label(statut_frame, text="Statut :")
        statut_label.pack(side="left")
        statut_value = ttk.Label(statut_frame, text=self.statut, foreground="dark green")
        statut_value.pack(side="right")

        respo_frame = ttk.Frame(main_frame)
        respo_label = ttk.Label(respo_frame, text="Respo :")
        respo_label.pack(side="left")
        respo_value = ttk.Label(respo_frame, text=self.respo, foreground="dark red")
        respo_value.pack(side="left")

        comment_frame = ttk.Frame(main_frame)
        comment_label = ttk.Label(comment_frame, text="Notes :")
        comment_label.pack(side="left", anchor="nw")
        comment_text = ExpandoText(comment_frame, width=38, height=1, wrap="word", font="TkDefaultFont", relief="flat",
                                   foreground="gray40", background=ttk.Style().lookup("TFrame", "background"))
        comment_text.pack(side="left", anchor="w")

        date_frame.grid(row=0, column=0, sticky="w")
        code_frame.grid(row=0, column=1, sticky="w", padx=(5, 0))
        auteur_frame.grid(row=1, column=0, sticky="w")
        flag_frame.grid(row=1, column=1, sticky="w", padx=(5, 0))
        desc_frame.grid(row=2, columnspan=2, sticky="nsew", pady=(0, 10))
        statut_frame.grid(row=3, column=0, sticky="w")
        respo_frame.grid(row=3, column=1, sticky="w", padx=(5, 0))
        comment_frame.grid(row=4, columnspan=2, sticky="nsew", padx=(0, 0))
        main_frame.columnconfigure(0, minsize=150)

        self.update_idletasks()
        desc_text.insert(tk.INSERT, self.desc)
        desc_text.configure(state="disabled")
        desc_text.bind('<Control-Key-a>', self.select_all)
        desc_text.bind('<Double-1>', self.select_all)
        comment_text.insert(tk.INSERT, self.comment)
        comment_text.configure(state="disabled")
        comment_text.bind('<Control-Key-a>', self.select_all)
        comment_text.bind('<Double-1>', self.select_all)

        return comment_text

    def buttonbox(self):
        box = ttk.Frame(self)
        box.pack(pady=(15, 10))
        url_button = ttk.Button(box, text="Ouvrir URLs", width=12, command=self.open_urls, state="disabled")
        url_button.pack(side="left", padx=4)
        if self.urls:
            url_button.configure(state="enabled")
        close_button = ttk.Button(box, text="Fermer", width=12, command=self.cancel)
        close_button.pack(side="right", padx=4)

    def parse_status(self, comment_sep="//"):
        statut, *comment = [x.strip() for x in self.statut_raw.split(comment_sep, 1)]
        self.statut = statut
        self.comment = comment[0] if comment else ""

    def parse_respo(self):
        respo = [r.strip() for r in self.respo_raw.split(",")]
        self.respo = utils.special_join(respo, ", ", " et ")

    def parse_urls(self):
        self.urls = utils.extract_urls(self.desc + " " + self.comment)

    def copy_code(self, button):
        logger.info("Copying '{}' to the clipboard".format(self.code))
        pyperclip.copy(self.code)
        self.copy_icon = tk.PhotoImage(file=utils.fix_path("data/img/copy2.png"))
        button.configure(image=self.copy_icon)

    def open_urls(self):
        for url in self.urls:
            webbrowser.open_new_tab(url)

    def select_all(self, event):
        event.widget.tag_add(tk.SEL, "1.0", tk.END + "-1c")
        event.widget.mark_set(tk.INSERT, tk.END + "-1c")
        event.widget.see(tk.INSERT)
        return "break"
