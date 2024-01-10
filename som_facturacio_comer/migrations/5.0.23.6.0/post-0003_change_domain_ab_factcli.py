# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Updating XML giscedata_facturacio_view.xml")
    load_data_records(
        cursor, 'som_facturacio_comer', "giscedata_facturacio_view.xml", ["giscedata_facturacio.action_factura_tree"], mode='update'
    )
    logger.info("XMLs succesfully updatd.")



def down(cursor, installed_version):
    pass


migrate = up