# coding=utf-8
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Loading XML with new AUVIDI categories")
    load_data(
        cursor, 'som_auvidi', 'giscedata_serveis_generacio_data.xml',
        idref=None, mode='init'
    )
    logger.info("XMLs succesfully loaded.")


def down(cursor, installed_version):
    pass


migrate = up
