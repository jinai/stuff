# -*- coding: utf-8 -*-
# !python3

import logging

import utils
from signalement import Signalement

logger = logging.getLogger(__name__)


class Archives():

    def __init__(self, dir_path, pattern):
        self.dir_path = dir_path
        self.pattern = pattern
        self.signalements = []

    @property
    def files(self):
        return list(self.dir_path.glob(self.pattern))

    def fetch(self):
        self.signalements = []
        for file in self.files:
            logger.info("Reading \"{}\"".format(file))
            try:
                f = open(file, 'r', encoding='utf-8')
            except IOError as e:
                logger.error(e)
            else:
                try:
                    raw_text = "".join(f.readlines()[2:])
                    self.signalements.extend(self.parse(raw_text, file))
                except (IOError, IndexError) as e:
                    logger.error(e)
                finally:
                    f.close()

    def parse(self, text, file, *, line_sep='\n', col_sep='|'):
        signalements = []
        year = utils.extract_numbers(str(file))[0]
        if not isinstance(text, str):
            return signalements
        for line in text.split(line_sep):
            if line.strip() != '':
                values = [elem.strip() for elem in line.split(col_sep)]
                values[0] = values[0] + "/" + year[2:]
                values[4] = [respo.strip() for respo in values[4].split(",")] if values[4] else []
                respo = values.pop(4)
                values.append(respo)
                s = Signalement(*values)
                signalements.append(s)
        return signalements

    def get_hash(self):
        hash = utils.hash_files(self.files)
        return hash

    def __len__(self):
        return len(self.signalements)

    def __iter__(self):
        return iter(self.signalements)

    def __repr__(self):
        return repr(self.signalements)

    def __str__(self):
        return "Sigs: {}".format(len(self.signalements))
