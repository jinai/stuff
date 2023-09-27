# -*- coding: utf-8 -*-
# !python3

import logging
import threading
import tkinter as tk
import tkinter.ttk as ttk
import webbrowser
from tkinter.scrolledtext import ScrolledText

import requests
from requests import HTTPError, Timeout, RequestException

import utils
from _meta import __version__
from widgets.dialogbase import DialogBase
from widgets.expandotext import ExpandoText
from widgets.iconswitcher import LabelGif

logger = logging.getLogger(__name__)


class UpdateWindow(DialogBase):
    def __init__(self, master, *, update_url, changelog_url, remote_version, **kwargs):
        super().__init__(master, dialog_title="Mise à jour", **kwargs)
        self.master = master
        self.update_url = update_url
        self.changelog_url = changelog_url
        self.remote_version = remote_version
        self.message = f"Une nouvelle version est disponible.\n\n" \
                       f"Version installée : {__version__}\n" \
                       f"Version disponible : {self.remote_version}"

        self.download_thread = None
        self.result = None
        self._check_result_id = None

    def body(self, container):
        self.text_message = ExpandoText(container, width=50, wrap="word", font="TkDefaultFont", relief="flat",
                                        background=ttk.Style().lookup("TFrame", "background"))
        self.text_message.pack(fill="both", expand=True)
        self.update_idletasks()
        self.text_message.insert(tk.INSERT, self.message)
        self.text_message.config(state="disabled")
        mono = ("Lucida Sans Typewriter", 8)
        self.text_changelog = ScrolledText(container, width=88, height=15, wrap="word", font=mono)
        self.text_changelog.pack(fill="both", expand=True, pady=(10, 0))
        self.loading_gif = LabelGif(self.text_changelog)
        self.loading_gif.place(relx=0.5, rely=0.5, anchor="center")
        self.loading_gif.configure(background=self.text_changelog.cget("background"))
        self.loading_gif.from_path(utils.fix_path("data/img/loading.gif"))
        self.loading_gif.play()
        self.text_changelog.config(state="disabled")

    def ok(self):
        webbrowser.open(self.update_url)
        super().ok()

    def buttonbox(self):
        box = ttk.Frame(self)
        box.pack(pady=(15, 10))
        button_ok = ttk.Button(box, text="Télécharger", width=12, command=self.ok, default="active")
        button_ok.pack(side="left", padx=4)
        button_cancel = ttk.Button(box, text="Annuler", width=12, command=self.cancel)
        button_cancel.pack(side="right", padx=4)

    def load_changelog(self):
        logger.info("Loading changelog")
        self.download_thread = threading.Thread(target=self.download)
        self.download_thread.start()
        self._check_result_id = self.after(100, self._check_result)

    def download(self):
        logger.info("Starting download thread")
        try:
            logger.info(f"Downloading {self.changelog_url}")
            r = requests.get(self.changelog_url, timeout=4)
            r.raise_for_status()
            self.result = str(r.text)
        except HTTPError as e:
            logger.error(e)
        except (Timeout, RequestException) as e:
            logger.error(f"{e} URL: {self.changelog_url}")
        logger.info("Stopping download thread")

    def _check_result(self):
        if self.download_thread.is_alive():
            self._check_result_id = self.after(100, self._check_result)
            return

        if self.result:
            self.text_changelog.config(state="normal")
            self.text_changelog.insert(tk.INSERT, self.result)
            self.text_changelog.config(state="disabled")

        self.stop()

    def stop(self):
        self.result = None
        if self._check_result_id:
            self.after_cancel(self._check_result_id)
            self._check_result_id = None
        if self.loading_gif.winfo_exists():
            self.loading_gif.destroy()
        if self.download_thread:
            self.download_thread.join()

    def destroy(self):
        self.stop()
        super().destroy()
