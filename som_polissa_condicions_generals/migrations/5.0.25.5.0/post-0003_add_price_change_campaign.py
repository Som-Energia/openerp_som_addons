# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return
    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)
    for model in ('som.infoenergia.lot.enviament', 'som.enviament.massiu'):
        pool.get(model)._auto_init(cursor, context={})
    for filename in (
            'security/price_change_security.xml',
            'data/price_change_campaign.xml',
            'data/price_change_views.xml'):
        load_data(cursor, 'som_polissa_condicions_generals', filename,
                  idref=None, mode='update')
    # The historical canviPreusBackend is noupdate and deliberately untouched.
    logger.info('Installed opt-in price-change campaign template and permissions')


def down(cursor, installed_version):
    pass


migrate = up
