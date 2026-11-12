# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    logger.info("Creating pooler")
    pooler.get_pool(cursor.dbname)

    logger.info("Updating XML giscedata_facturacio_contracte_lot_view.xml")
    load_data_records(
        cursor, "som_empowering",
        "res_partner_view.xml",
        ["view_partner_empowering_form"], mode="update"
    )
    logger.info("XMLs succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
