# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Restoring cups.helper access rules")
    load_data(
        cursor, 'www_som', 'security/ir.model.access.csv',
        idref=None, mode='update'
    )


def down(cursor, installed_version):
    pass


migrate = up
