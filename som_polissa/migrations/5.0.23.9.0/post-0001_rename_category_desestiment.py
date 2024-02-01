# -*- encoding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")

    logger.info("Creating pooler")
    pooler.get_pool(cursor.dbname)

    # UPDATAR UNA PART DE L'XML (POSAR LA ID)
    logger.info("Updating XMLs")
    list_of_records = [
        "giscedata_facturacio_bateria_virtual.categ_desestiment",
    ]
    load_data_records(cursor, "som_polissa", "som_polissa_data.xml", list_of_records, mode="update")
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
