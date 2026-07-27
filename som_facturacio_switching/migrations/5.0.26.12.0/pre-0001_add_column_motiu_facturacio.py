# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import column_exists, add_columns


def up(cursor, installed_version):
    if not installed_version:
        return

    # Nova Instancia de Logger.
    logger = logging.getLogger('openerp.migration')

    # CREAR a la base de dades
    logger.info('Create new field motiu_facturacio in giscedata_facturacio_importacio_linia ...')
    if not column_exists(cursor, 'giscedata_facturacio_importacio_linia', 'motiu_facturacio'):
        add_columns(cursor, {
            'giscedata_facturacio_importacio_linia': [('motiu_facturacio', 'VARCHAR(4)')]
        })
        logger.info('Cap afegit a la taula giscedata_facturacio_importacio_linia.')


def down(cursor, installed_version):
    pass


migrate = up