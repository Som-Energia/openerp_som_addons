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

    logger.info("Creating XMLs records")
    list_of_records = ["ir_attachment_vat_dni_category"]
    load_data_records(
        cursor, "som_polissa", "som_polissa_data.xml", list_of_records, mode="init"
    )
    logger.info("XMLs records succesfully created.")


def down(cursor, installed_version):
    pass


migrate = up
