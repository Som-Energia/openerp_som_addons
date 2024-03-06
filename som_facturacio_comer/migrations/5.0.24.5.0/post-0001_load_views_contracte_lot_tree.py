# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    logger.info("Updating XML record for view polisses.facturacio.contracte.lot.som.tree")
    load_data_records(
        cursor, "som_facturacio_comer", "giscedata_facturacio_contracte_lot_view.xml",
        ["view_giscedata_facturacio_contracte_lot_som_tree"], idref=None, mode="update"
    )

    logger.info("XML record succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
