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

    logger.info("Updating XML giscedata_polissa_view.xml")
    record_names = [
        'view_giscedata_polissa_deute_som_tree',
        'action_giscedata_polissa_deute_som_tree'
    ]
    load_data_records(cursor, 'som_facturacio_comer', 'giscedata_polissa_view.xml', record_names)
    logger.info("XMLs succesfully updatd.")



def down(cursor, installed_version):
    pass


migrate = up