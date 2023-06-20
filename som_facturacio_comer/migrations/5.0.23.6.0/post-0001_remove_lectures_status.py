# -*- coding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data, load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

   ##UPATAR UN XML SENCER##
    logger.info("Updating XML som_facturacio_comer/giscedata_facturacio_view.xml")
    load_data(
        cursor, 'som_facturacio_comer', 'wizard/giscedata_facturacio_view.xml', idref=None, mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up