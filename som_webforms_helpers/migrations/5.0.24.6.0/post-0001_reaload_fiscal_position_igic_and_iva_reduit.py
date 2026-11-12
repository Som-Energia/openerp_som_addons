# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML som_webforms_helpers_data.xml selected variables")
    load_data_records(
        cursor, 'som_webforms_helpers', 'som_webforms_helpers_data.xml',
        ['iva_reduit_get_tariff_prices_end_date', 'fiscal_position_igic'],
        mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
