# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Updating giscedata_polissa table from giscedata_facturacio_som")
    pool.get("giscedata.polissa")._auto_init(cursor, context={'module': 'giscedata_facturacio_som'})
    logger.info("Updating createdted succesfully.")

    logger.info("Updating XML giscedata_polissa_view.xml")
    load_data_records(
        cursor, 'giscedata_facturacio_som', 'giscedata_polissa_view.xml',
        ['view_giscedata_polissa_facturacio_bloquejada_form',
         'view_giscedata_polissa_facturacio_bloquejada_tree'],
        mode='update'
    )
    logger.info("XML succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
