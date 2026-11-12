# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Initializing new fields")
    pool.get("giscedata.crm.lead")._auto_init(
        cursor, context={'module': 'som_leads_polissa'}
    )

    logger.info("Updating XML and CSV files")

    list_of_records = [
        "giscedata_crm_leads_som_view",
    ]

    load_data_records(
        cursor,
        'som_leads_polissa',
        'views/giscedata_crm_lead_view.xml',
        list_of_records,
        mode='update'
    )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
