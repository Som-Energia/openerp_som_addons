# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML and CSV files")

    load_data(
        cursor, 'som_leads_polissa', 'security/ir.model.access.csv',
        idref=None, mode='update'
    )
    load_data(
        cursor, 'som_leads_polissa', 'data/giscedata_crm_lead_data.xml',
        idref=None, mode='init'
    )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
