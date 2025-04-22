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
    pool.get("report.test")._auto_init(
        cursor, context={'module': 'report_tester'}
    )

    logger.info("Updating XML and CSV files")
    data_files = [
        'security/ir.model.access.csv',
        'views/report_test_view.xml',
        'wizard/wizard_report_test_attach_to_invoice.xml',
        'wizard/wizard_report_test_group_view_tests.xml',
        'wizard/wizard_report_test_view_attached.xml',
    ]

    for data_file in data_files:
        load_data(
            cursor, 'report_tester', data_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
