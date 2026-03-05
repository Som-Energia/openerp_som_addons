# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XML and CSV files")
    data_file = 'som_dashboard_gc_tasca_1.xml'
    xml_records = [
        'action_draft_atr_cases_dashboard',
        'action_ms_with_attachments_dashboard',
        'action_ms_without_attachments_dashboard',
    ]
    load_data_records(cursor, 'som_dashboard', data_file, xml_records, mode='update')
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
