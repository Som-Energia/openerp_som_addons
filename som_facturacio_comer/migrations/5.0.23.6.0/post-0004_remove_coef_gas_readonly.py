# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    logger.info("Creating pooler")
    pooler.get_pool(cursor.dbname)

    logger.info("Updating XML som_facturacio_comer/giscedata_polissa_view.xml")
    load_data(
        cursor,
        "som_facturacio_comer",
        "giscedata_polissa_view.xml",
        idref=None,
        mode="update",
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
