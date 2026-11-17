# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return
    logger = logging.getLogger('openerp.migration')
    for filename in (
            'security/price_change_security.xml',
            'data/price_change_campaign.xml'):
        load_data(cursor, 'som_polissa_condicions_generals', filename,
                  idref=None, mode='update')
    # The historical canviPreusBackend is noupdate and deliberately untouched.
    logger.info('Installed opt-in price-change campaign template and permissions')


def down(cursor, installed_version):
    pass


migrate = up
