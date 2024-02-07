# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_data
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Update giscedata_cups_view.xml")
    load_data(
        cursor, 'som_polissa', 'giscedata_cups_view.xml', idref=None, mode='update'
    )
    logger.info("End updating giscedata_cups_view.xml")


def down(cursor, installed_version):
    pass


migrate = up
