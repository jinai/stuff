# -*- coding: utf-8 -*-
# !python3

import logging
import webbrowser

import pyperclip

import utils
from widgets.popup import Popup
from widgets.sigdetails import SigDetails
from widgets.treelist import Treelist

logger = logging.getLogger(__name__)


class Siglist(Treelist):
    def __init__(self, master, *, signalements, statusbar, **kwargs):
        super().__init__(master, **kwargs)
        self.signalements = signalements
        self.statusbar = statusbar
        self._keys = [
            lambda x: 0,
            lambda x: x.datetime(),
            lambda x: x.auteur.lower(),
            lambda x: x.code,
            lambda x: x.flag.lower(),
            lambda x: x.desc.lower(),
            lambda x: x.statut.lower(),
            lambda x: str(x.respo)
        ]
        self._last_popup_rightclick = None
        self._last_selected_item = None
        self._dialogs = []
        self.tree.bind('<Double-1>', self.on_doubleclick)
        self.tree.bind('<Button-3>', self.on_rightclick)
        self.tree.bind('<Return>', self.details)
        self.tree.bind('<Control-c>', lambda _: self.copy(with_load=True))
        self.tree.bind('<Control-x>', lambda _: self.copy())
        self.tree.bind('<Control-l>', lambda _: self.open_urls())
        self.tree.bind('<FocusOut>', self.remove_popups)
        self.tree.bind('<<TreeviewSelect>>', self.selection_handler)

    def get_selected_sigs(self):
        selected = []
        for item in self.tree.selection():
            index = int(self.tree.item(item)['values'][0]) - 1
            selected.append(self.signalements[index])
        return selected

    def on_doubleclick(self, event):
        if self.tree.identify_region(event.x, event.y) == "cell":
            column = int(self.tree.identify("column", event.x, event.y)[1:]) - 1
            if column == 3:  # Copy code
                # Clipboard
                item = self.tree.identify("item", event.x, event.y)
                value = str(self.tree.item(item)['values'][column])
                pyperclip.copy(value)
                # Popup
                x, y = self.master.winfo_pointerx(), self.master.winfo_pointery()
                msg = utils.text_ellipsis(value, width=30)
                Popup('"{}" copié dans le presse-papiers'.format(msg), x, y, offset=(10, -20))
            else:

                self.details(event)

    def on_rightclick(self, event):
        if self.tree.identify_region(event.x, event.y) == "cell":
            item = self.tree.identify("item", event.x, event.y)
            column = int(self.tree.identify("column", event.x, event.y)[1:]) - 1
            value = str(self.tree.item(item)['values'][column])
            x, y = self.tree.bbox(item, self.headers[column])[:2]
            x = x + self.winfo_rootx()
            y = y + self.winfo_rooty() - 2
            self.remove_popups()
            self._last_popup_rightclick = Popup(value, x, y, persistent=True, txt_color="#575757",
                                                bg_color="white", border_color="#767676", border_width=1)

    def details(self, event):
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item)['values']
            values[0] = str(values[0])  # Treeviews force str to int if it's a digit
            title = "Signalement #{num}".format(num=values[0])
            dialog = SigDetails(self, dialog_title=title, values=values, centered=False, is_modal=False,
                                is_transient=True)
            self._dialogs.append(dialog)
            dialog.spawn()

    def copy(self, with_load=False):
        selection = self.tree.selection()
        if len(selection) == 1:
            item = selection[0]
            cmd = "/load " if with_load else ""
            cmd += self.tree.item(item)['values'][3]
            logger.info("Copying '{}' to the clipboard".format(cmd))
            pyperclip.copy(cmd)
            try:
                x, y = self.tree.bbox(item, self.headers[3])[:2]
                x = x + self.winfo_rootx()
                y = y + self.winfo_rooty()
                Popup('"{}" copié dans le presse-papiers'.format(cmd), x, y, offset=(0, -21))
            except ValueError:
                pass

    def open_urls(self):
        for sig in self.get_selected_sigs():
            urls = utils.extract_urls(str(sig))
            if urls:
                logger.info("Opening {} URLs for sig #{}".format(len(urls), self.signalements.index(sig) + 1))
            for url in urls:
                webbrowser.open_new_tab(url)

    def remove_popups(self, event=None):
        if self._last_popup_rightclick:
            self._last_popup_rightclick.destroy()

    def selection_handler(self, event):
        self._last_selected_item = self.tree.focus()
        self.remove_popups()
        sel = self.tree.selection()
        if sel:
            plural = "" if len(sel) == 1 else "s"
            self.statusbar.set("{0} signalement{1} sélectionné{1}".format(len(sel), plural), clear_after=0)
        else:
            self.statusbar.clear()

    def close_dialogs(self):
        for dialog in self._dialogs:
            dialog.cancel()

    def populate(self):
        for i, sig in enumerate(self.signalements):
            f = list(sig.fields())
            f[-1] = ", ".join(f[-1])
            self.insert(f)

    def refresh(self):
        self.close_dialogs()
        self.clear()
        self.populate()
        self._matches_label.set('')
