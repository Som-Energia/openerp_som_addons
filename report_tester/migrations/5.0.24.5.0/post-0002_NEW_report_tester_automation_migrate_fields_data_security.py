# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Initializing new fields")

    pool = pooler.get_pool(cursor.dbname)
    pool.get("report.test")._auto_init(
        cursor, context={'module': 'report_tester'}
    )

    pool.get("report.test.group")._auto_init(
        cursor, context={'module': 'report_tester'}
    )

    pool.get("report.tester.automation")._auto_init(
        cursor, context={'module': 'report_tester'}
    )

    logger.info("Updating XML files")
    data_files = [
        'data/report_tester_data.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'report_tester', data_file,
            idref=None, mode='update'
        )

    logger.info("Updating CSV security files")
    security_files = [
        'security/ir.model.access.csv',
    ]
    for security_file in security_files:
        load_data(
            cursor, 'report_tester', security_file,
            idref=None, mode='update'
        )

    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
