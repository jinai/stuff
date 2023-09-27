# -*- coding: utf-8 -*-
# !python3

import json
import logging
import os
import threading
import time
import tkinter.ttk as ttk
from urllib.parse import urljoin

import requests
from requests import HTTPError, Timeout, RequestException

import utils
from _meta import __version__
from widgets.iconswitcher import IconSwitcher
from widgets.updatewindow import UpdateWindow

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class Updater(ttk.Frame):
    def __init__(self, master, *, button_text, archives, callback, timeout=8, statusbar, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.button_text = button_text
        self.archives = archives
        self.callback = callback
        self.timeout = timeout
        self.statusbar = statusbar
        self.base_url = "https://respomap.herokuapp.com/"
        self.meta_url = urljoin(self.base_url, "/meta.json")
        self.meta = None
        self.download_thread = None
        self.running = threading.Event()
        self.result = None
        self._check_result_id = None
        self.progressbar_step = 10
        self.setup()

    def setup(self):
        s = ttk.Style()
        s.layout("Text.Horizontal.TProgressbar",
                 [("Horizontal.Progressbar.trough",
                   {"children": [("Horizontal.Progressbar.pbar",
                                  {"side": "left", "sticky": "ns"})],
                    "sticky": "nswe"}),
                  ("Horizontal.Progressbar.label", {"sticky": ""})])
        self.frame_button_progress = ttk.Frame(self)
        self.frame_button_progress.pack(side="left", fill="both", expand=True)
        self.frame_button_progress.grid_columnconfigure(0, minsize=140)
        self.frame_button_progress.grid_rowconfigure(0, minsize=25)  # Button is 23px in height + 1 padding all around
        self.button = ttk.Button(self.frame_button_progress, text=self.button_text, command=self.run, takefocus=False)
        self.button.grid(row=0, column=0, sticky="nsew")
        self.progressbar = ttk.Progressbar(self.frame_button_progress, orient="horizontal", mode="determinate",
                                           style="Text.Horizontal.TProgressbar")
        self.icon = IconSwitcher(self)
        self.icon.pack(side="right", padx=(5, 0))
        self.icon.add(utils.fix_path("data/img/loading.gif"), name="loading")
        self.icon.add(utils.fix_path("data/img/success.gif"), name="success")
        self.icon.add(utils.fix_path("data/img/fail.gif"), name="fail")

    def set_button_text(self, text):
        self.button.configure(text=text)

    def set_pbar_text(self, text):
        geometry = self.winfo_toplevel().winfo_geometry()
        ttk.Style().configure('Text.Horizontal.TProgressbar', text=text)
        self.winfo_toplevel().geometry(geometry)  # Hack needed otherwise the window somehow gets bigger by a few pixels

    def run(self):
        if not self.running.is_set():
            logger.info("Running update check")
            self.running.set()
            self.button.grid_remove()
            self.progressbar.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
            self.set_pbar_text("Vérification en cours")
            self.statusbar.set("Mise à jour...", clear_after=0)
            self.icon.select("loading")
            self.download_thread = threading.Thread(target=self.download)
            self.download_thread.start()
            self._check_result_id = self.after(100, self._check_result)

    def _download_file(self, url, *, timeout):
        logger.info(f"Downloading {url}")
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except HTTPError as e:
            logger.error(e)
            self.statusbar.set(f"Erreur {e.response.status_code} pendant le téléchargement de {url}", clear_after=0)
        except Timeout as e:
            logger.error(f"{e} URL: {url}")
            self.statusbar.set(f"Délai dépassé pendant le téléchargement de {url}", clear_after=0)
        except RequestException as e:
            logger.error(f"{e} URL: {url}")
            self.statusbar.set(f"Erreur inconnue, voir logs dans {utils.get_app_directory()}", clear_after=0)

    def download(self):
        logger.debug("Starting download thread")
        local_hash = self.archives.get_hash()
        target_dir = self.archives.dir_path
        logger.debug(f"Local hash is {local_hash}")
        r = self._download_file(self.meta_url, timeout=self.timeout)
        if r and self.running.is_set():
            self.meta = json.loads(r.text)
            remote_hash = self.meta["archives"]["hash"]
            logger.debug(f"Remote hash is {remote_hash}")
            if local_hash != remote_hash:
                logger.info("Archives update found")
                if utils.create_directory(target_dir):
                    logger.info(f"Created directory '{target_dir}'")
                self.progressbar.configure(maximum=len(self.meta["archives"]["files"] * self.progressbar_step))
                downloaded = 0
                i = 0
                while i < len(self.meta["archives"]["files"]) and self.running.is_set():
                    file = self.meta["archives"]["files"][i]
                    filename = os.path.basename(file)
                    self.set_pbar_text(filename)
                    url = urljoin(self.base_url, file)
                    r = self._download_file(url, timeout=self.timeout)
                    if not r:
                        break
                    try:
                        with open(os.path.join(target_dir, filename), "w", encoding="utf-8") as f:
                            f.write(r.text)
                        downloaded += 1
                        if not self.running.is_set():
                            break
                        for _ in range(self.progressbar_step):
                            self.progressbar.step()
                            self.progressbar.update()
                            time.sleep(0.1 / self.progressbar_step)
                    except OSError as e:
                        logger.error(e)
                        d = utils.get_app_directory()
                        self.statusbar.set(f"Problème d'écriture sur le disque, voir logs dans {d}", clear_after=0)
                        break
                    i += 1
                self.result = downloaded
            else:
                self.result = -1  # Sentinel value
                logger.info("Archives already up to date")

        logger.debug("Stopping download thread")

    def _check_result(self):
        if self.download_thread.is_alive():
            self._check_result_id = self.after(100, self._check_result)
            return

        if self.meta is None or self.result is None or (0 <= self.result < len(self.meta["archives"]["files"])):
            self.icon.select("fail", hide_delay=3000)
        else:
            self.icon.select("success", hide_delay=3000)
            self.statusbar.clear()
            if self.result > 0:
                self.callback()

        self.stop()
        self.check_software_update()

    def stop(self):
        self.running.clear()
        self.result = None
        if self._check_result_id:
            self.after_cancel(self._check_result_id)
            self._check_result_id = None
        if self.progressbar.winfo_viewable():
            self.progressbar.grid_remove()
        if not self.button.winfo_viewable():
            self.button.grid()
        if self.icon.current_name() == "loading":
            self.icon.hide()
        if self.download_thread:
            self.download_thread.join()

    def check_software_update(self):
        if self.meta is None:
            return
        local_version = __version__
        remote_version = self.meta["version"]
        update_url = urljoin(self.base_url, self.meta["file"])
        changelog_url = urljoin(self.base_url, self.meta["changelog"])
        if utils.parse_version(remote_version) > utils.parse_version(local_version):
            logger.info(f"A software update is available (v{local_version} to v{remote_version})")
            update = UpdateWindow(self, update_url=update_url, changelog_url=changelog_url,
                                  remote_version=remote_version, can_resize=False, is_modal=False, is_transient=True,
                                  centered=True, stay_centered=True)
            update.spawn()
            update.load_changelog()
        else:
            self.set_button_text("Programme à jour")
            self.after(3000, lambda: self.set_button_text(self.button_text))


    def destroy(self):
        self.stop()
        super().destroy()
