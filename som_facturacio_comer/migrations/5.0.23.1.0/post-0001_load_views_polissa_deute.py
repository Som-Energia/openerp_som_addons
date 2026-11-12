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

    logger.info("Updating Table")
    pool.get("giscedata.polissa")._auto_init(cursor, context={"module": "som_facturacio_comer"})
    logger.info("Updating XML giscedata_polissa_view.xml")
    load_data(
        cursor, "som_facturacio_comer", "giscedata_polissa_view.xml", idref=None, mode="update"
    )
    logger.info("XMLs succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
