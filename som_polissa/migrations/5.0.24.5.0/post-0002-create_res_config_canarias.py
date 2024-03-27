# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    module = 'som_polissa'

    # Crear variables de configuració
    data_file = 'som_polissa_data.xml'
    data_records = ['fp_canarias_vivienda_id', 'fp_canarias_id', 'fp_pdlc_vivienda_id',
                    'fp_pdlc_id']
    logger.info("Updating records from XML {}".format(data_file))
    load_data_records(cursor, module, data_file, data_records, mode='update')
    logger.info("XML records successfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
