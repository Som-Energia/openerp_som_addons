# -*- coding: utf-8 -*-
import pooler
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Updating XML files")
    data_files = [
        'report/som_polissa_report.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_polissa', data_file,
            idref=None, mode='update'
        )

    logger.info("Updating CSV security files")
    security_files = [
        'security/ir.model.access.csv',
    ]
    for security_file in security_files:
        load_data(
            cursor, 'som_polissa', security_file,
            idref=None, mode='update'
        )

    pool.get('report.backend.mandat.sepa')._auto_init(
        cursor, context={'module': 'som_polissa'}
    )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
