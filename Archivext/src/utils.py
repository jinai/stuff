# -*- coding: utf-8 -*-
# !python3

import argparse
import hashlib
import logging
import os
import re
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from threading import Timer

import urlmarker
from _meta import __appname__

logger = logging.getLogger(__name__)


# frozen = 'not'
# if getattr(sys, 'frozen', False):
#     # we are running in a bundle
#     frozen = 'ever so'
#     bundle_dir = sys._MEIPASS
# else:
#     # we are running in a normal Python environment
#     bundle_dir = os.path.dirname(os.path.abspath(__file__))
# print('we are', frozen, 'frozen')
# print('bundle dir is', bundle_dir)
# print('sys.argv[0] is', sys.argv[0])
# print('sys.executable is', sys.executable)
# print('os.getcwd is', os.getcwd())


def fix_path(path):
    if not os.path.isabs(path):
        wd = getattr(sys, "_MEIPASS", "")
        return os.path.join(wd, path)


def init_logging(file=True):
    log_level = get_log_level()
    logger = logging.getLogger()
    logger.setLevel(log_level)
    fmt = "{asctime}.{msecs:03.0f} ⠶ {levelname:<5} ⠶ {name} ⠶ {message}"
    datefmt = "%d/%m/%Y %H:%M:%S"
    fmt = logging.Formatter(fmt=fmt, datefmt=datefmt, style="{")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    if file:
        log_dir = get_app_directory()
        created_dir = create_directory(log_dir)

        path = log_dir / "{}.log".format(__appname__.lower())
        file_handler = TimedRotatingFileHandler(filename=path, when="midnight", encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
        if created_dir:
            logger.info("Created directory '{}'".format(log_dir))

    return logging._levelToName[log_level]


def create_directory(dirname):
    try:
        os.makedirs(dirname)
        return True
    except OSError:
        return False  # Directory already exists


def get_app_directory():
    return Path.home() / "Documents" / __appname__


def get_log_level():
    parser = argparse.ArgumentParser(__name__)
    parser.add_argument('--log-level',
                        default=logging.DEBUG,
                        dest='log_level',
                        type=lambda arg: logging._checkLevel(arg.upper()),
                        nargs='?',
                        help='Set the logging output level. {0}'.format([key for key in logging._nameToLevel]))
    parsed_args = parser.parse_args()
    return parsed_args.log_level


def text_ellipsis(text, *, width, placeholder="..."):
    if not isinstance(text, str) or width < len(placeholder):
        raise ValueError
    if len(text) <= width:
        return text
    return text[:width - len(placeholder)] + placeholder


def extract_urls(text):
    return re.findall(urlmarker.URL_REGEX, text)


def extract_numbers(text):
    return re.findall("\d+", text)


def sequence_chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def special_join(seq, sep, last_sep):
    result = ""
    if len(seq) == 0:
        return result
    elif len(seq) == 1:
        return str(seq[0])
    for index, elem in enumerate(seq):
        result += elem
        if index < len(seq) - 2:
            result += sep
        elif index == len(seq) - 2:
            result += last_sep

    return result


def replace_all(text, replace_list):
    result = text
    for old, new in replace_list:
        result = result.replace(old, new)
    return result


def debounce(func, wait, widget):
    def debounced(*args, **kwargs):
        def call_func():
            func(*args, **kwargs)

        try:
            debounced.timer.cancel()
        except AttributeError:
            pass

        debounced.timer = Timer(wait / 1000, lambda: func(*args, **kwargs))
        debounced.timer.start()

    return debounced


def hash_files(filenames):
    hash = hashlib.md5()
    blocksize = 64 * 1024
    for file in filenames:
        with open(file, "rb") as fp:
            while True:
                data = fp.read(blocksize)
                if not data:
                    break
                hash.update(data)
    return hash.hexdigest()


def parse_version(v):
    return tuple([int(x) for x in v.split(".")])
