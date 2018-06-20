import csv
import logging
from datetime import datetime, timedelta

from enerdata.datetime.timezone import TIMEZONE
from enerdata.profiles.profile import REEProfile, Coefficent


logger = logging.getLogger('openerp' + __name__)


class REEInitalProfile(REEProfile):
    def __init__(self, path):
        self.path = path

    def get(self, year, month):
        key = '%(year)s%(month)02i' % locals()
        if key in self._CACHE:
            logger.debug('Using CACHE for REEProfile {0}'.format(key))
            return self._CACHE[key]
        with open(self.path, 'r') as m:
            reader = csv.reader(m, delimiter=';')
            header = 2
            cofs = []
            for vals in reader:
                if header:
                    header -= 1
                    continue
                if int(vals[0]) != month:
                    continue
                dt = datetime(
                    year, int(vals[0]), int(vals[1])
                )
                day = TIMEZONE.localize(dt) + timedelta(hours=int(vals[2]))
                cofs.append(Coefficent(
                    TIMEZONE.normalize(day), dict(
                        (k, float(vals[i])) for i, k in enumerate('ABCD', 3)
                    ))
                )
            self._CACHE[key] = cofs
            return cofs
