# -*- coding: utf-8 -*-
# !python3

import logging
import tkinter as tk
import tkinter.ttk as ttk

import archives
import utils
from _meta import __appname__, __version__
from widgets import dialogbase, searchbar, siglist, statusbar
from widgets.updater import Updater


class Archivext(tk.Tk):
    def __init__(self, *, auto_import=True, auto_update=True):
        super().__init__()
        self.app_title = "{} {}".format(__appname__, __version__)
        self.auto_import = auto_import
        self.auto_update = auto_update
        self.welcome_msg = ""
        arch_directory = utils.get_app_directory() / "archives"
        arch_pattern = "archives_{0}{0}{0}{0}.txt".format("[0-9]")
        self.archives = archives.Archives(arch_directory, arch_pattern)
        self.signalements = []

        # Rendering
        try:
            self.tk.call('encoding', 'system', 'utf-8')
            path = utils.fix_path("data/img/archivext.ico")
            self.iconbitmap(path, default=path)
        except Exception as e:
            logging.error(e)

        self.title(self.app_title)
        self._setup_widgets()
        self.update_idletasks()

        # Bindings
        self.bind('<Control-f>', lambda _: self.search())
        self.bind('<Control-q>', lambda _: self.exit())
        self.main_frame.bind('<Button-1>', lambda _: self.clear_focus())
        self.protocol("WM_DELETE_WINDOW", self.exit)

        # Imports
        if self.auto_import:
            self.import_archives()

        # Warnings
        if self.welcome_msg:
            dialog_title = self.app_title
            info = dialogbase.WelcomeDialog(self, dialog_title=dialog_title, body_text=self.welcome_msg,
                                            button_text="OK",
                                            is_modal=True, is_transient=True, centered=True)
            info.spawn()

        # Updates
        if self.auto_update:
            self.updater.run()

    def _setup_widgets(self):
        self.statusbar = statusbar.StatusBar(self)
        self.statusbar.pack(side="bottom", fill="x")
        self.statusbar.set_amount(f"{len(self.signalements)} signalements")
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill='both', expand=True)

        # -------------------------------------------- UPDATE & SEARCH --------------------------------------------- #

        btn_text = "Rechercher mises à jour"
        self.updater = Updater(self.main_frame, button_text=btn_text, archives=self.archives, statusbar=self.statusbar,
                               callback=self.import_archives)

        self.frame_search = ttk.Frame(self.main_frame)
        self.label_matches = ttk.Label(self.frame_search, foreground="grey40")
        self.label_matches.pack(side="left", padx=(0, 5))
        placeholder_options = {
            "text": " Rechercher"
        }
        icon_options = {
            "path": utils.fix_path("data/img/eye.png"),
            "alt": utils.fix_path("data/img/eye2.png")
        }
        self.searchbar = searchbar.SearchBar(self.frame_search, placeholder_options=placeholder_options,
                                             icon_options=icon_options, width=40)
        self.searchbar.pack(side="right")

        # ---------------------------------------------- SIGNALEMENTS ---------------------------------------------- #

        headers = ['Date', 'Auteur', 'Code', 'Flag', 'Description', 'Statut', 'Respomap(s)']
        column_widths = [55, 85, 100, 80, 400, 350, 100]
        sort_keys = [
            lambda x: (int(x[0].split("/")[2]), int(x[0].split("/")[1]), int(x[0].split("/")[0])),
            lambda x: x[0].lower(),
            lambda x: x[0].lower(),
            lambda x: x[0].lower(),
            lambda x: x[0].lower(),
            lambda x: x[0].lower(),
            lambda x: x[0].lower(),
        ]
        stretch_bools = [False, False, False, False, True, True, True]
        index_options = {
            "show": True,
            "header": "#",
            "width": 35,
            "sort": lambda x: int(x[0]),
            "stretch": False
        }
        exclude = [placeholder_options["text"]]
        search_tags = ["num", "date", "auteur", "code", "flag", "desc", "statut", "respo"]
        self.tree_sig = siglist.Siglist(self.main_frame, signalements=self.signalements, statusbar=self.statusbar,
                                        headers=headers, sort_keys=sort_keys, stretch_bools=stretch_bools, height=25,
                                        index_options=index_options, sortable=True, column_widths=column_widths,
                                        match_template="{} sur {}", search_excludes=exclude, search_tags=search_tags)
        self.searchbar.entry.configure(textvariable=self.tree_sig._search_query)
        self.label_matches.configure(textvariable=self.tree_sig._matches_label)

        # ------------------------------------------- WIDGETS PLACEMENT -------------------------------------------- #

        self.updater.grid(row=0, column=0, sticky="nsw", padx=(4, 0), pady=(4, 0))
        self.frame_search.grid(row=0, column=2, sticky="e", padx=(0, 17), pady=(5, 0))
        self.tree_sig.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=(5, 0), pady=(4, 5))

        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="_")

        # Needed to rewrite the placeholder because we hooked an empty StringVar that erased it
        self.searchbar.focus_out(None)

    def import_archives(self):
        self.archives.fetch()
        self.signalements = self.archives.signalements
        if self.signalements:
            self.refresh(scroll="down")
            self.statusbar.set_amount(f"{len(self.signalements)} signalements")
            self.statusbar.set_location(self.archives.dir_path)

    def search(self):
        self.searchbar.focus()
        self.searchbar.select_range(0, 'end')

    def refresh(self, archives=False, scroll=None):
        logging.debug("Refreshing {} sigs".format(len(self.signalements)))
        self.tree_sig.signalements = self.signalements
        self.tree_sig.refresh()
        if archives:
            self.archives.fetch()
        self.tree_sig.search()
        if scroll == "down":
            self.tree_sig.scroll_down()
        elif scroll == "up":
            self.tree_sig.scroll_up()

    def clear_focus(self):
        self.tree_sig.deselect_all()
        self.main_frame.focus_force()

    def exit(self):
        self.destroy()
        logging.info("Exiting {}\n".format(__appname__))
        logging.shutdown()


if __name__ == '__main__':
    log_level = utils.init_logging()
    logging.info("Starting {} {} [log_level={}]".format(__appname__, __version__, log_level))

    app = Archivext()
    app.mainloop()
