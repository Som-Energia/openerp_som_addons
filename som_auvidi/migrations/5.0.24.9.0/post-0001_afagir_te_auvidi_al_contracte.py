# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Update models giscedata.polissa and giscedata.polissa.modcontractual")
    pool.get('giscedata.polissa')._auto_init(cursor, context={'module': 'som_auvidi'})
    pool.get('giscedata.polissa.modcontractual')._auto_init(cursor, context={'module': 'som_auvidi'})
    logger.info("Models updated")

    logger.info("Updating XML giscedata_polissa_view.xml")
    load_data(
        cursor, "som_auvidi",
        "giscedata_polissa_view.xml", mode="init"
    )
    logger.info("XMLs succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
