# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Initializing conditional report test refresh fields")
    pool = pooler.get_pool(cursor.dbname)
    pool.get('report.test.group')._auto_init(
        cursor, context={'module': 'report_tester'}
    )
    pool.get('wizard.report.test.group.csv')._auto_init(
        cursor, context={'module': 'report_tester'}
    )
    logger.info("Updating report test views and registering group list actions")
    data_files = [
        'views/report_test_view.xml',
        'wizard/wizard_report_test_group_execute_tests.xml',
        'wizard/wizard_report_test_group_view_tests.xml',
        'wizard/wizard_report_test_group_accept_tests.xml',
        'wizard/wizard_report_test_group_csv.xml',
        'views/report_test_group_view.xml',
        'security/ir.model.access.csv',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'report_tester', data_file,
            idref=None, mode='update'
        )


def down(cursor, installed_version):
    pass


migrate = up
