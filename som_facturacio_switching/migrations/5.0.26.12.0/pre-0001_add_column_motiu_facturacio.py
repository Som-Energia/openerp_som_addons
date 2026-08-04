# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from oopgrade.oopgrade import column_exists


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info('Create new field motiu_facturacio in giscedata_facturacio_importacio_linia ...')
    if not column_exists(cursor, 'giscedata_facturacio_importacio_linia', 'motiu_facturacio'):
        query = """
            ALTER TABLE giscedata_facturacio_importacio_linia
                ADD COLUMN motiu_facturacio varchar(4) DEFAULT '01'
        """
        cursor.execute(query)
        logger.info('Cap afegit a la taula giscedata_facturacio_importacio_linia.')


def down(cursor, installed_version):
    pass


migrate = up
