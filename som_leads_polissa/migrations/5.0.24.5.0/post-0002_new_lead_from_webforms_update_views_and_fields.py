# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Initializing new fields")
    pool.get("res.partner")._auto_init(
        cursor, context={'module': 'som_leads_polissa'}
    )

    logger.info("Updating XML and CSV files")

    data_files = [
        'data/giscedata_crm_lead_data.xml',
        'security/ir.model.access.csv',
        'views/giscedata_crm_lead_view.xml',
        'views/res_partner_view.xml',
    ]

    for data_file in data_files:
        load_data(
            cursor, 'som_leads_polissa', data_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
