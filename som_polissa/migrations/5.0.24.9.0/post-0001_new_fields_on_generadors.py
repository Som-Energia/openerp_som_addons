# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data
from tools import config


def up(cursor, installed_version):
    if not installed_version:
        return
    if config.updating_all:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Creating new fields on model giscedata.autoconsum.generador")
    pool.get("giscedata.autoconsum.generador")._auto_init(
        cursor, context={'module': 'som_polissa'}
    )
    logger.info("Fields created successfully")

    logger.info("Updating XML giscedata_autoconsum_view.xml")
    load_data(
        cursor, 'som_polissa', 'giscedata_autoconsum_view.xml', idref=None,
        mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
