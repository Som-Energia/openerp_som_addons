# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating models")
    pool = pooler.get_pool(cursor.dbname)
    pool.get("report.backend.condicions.particulars.ignore.modcon")._auto_init(
        cursor, context={'module': 'som_polissa_condicions_generals'}
    )

    logger.info("Updating XML files")
    data_files = [
        'report/giscedata_polissa_condicions_generals_ignore_modcon_report.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_polissa_condicions_generals', data_file,
            idref=None, mode='update'
        )

    logger.info("Updating CSV security files")
    security_files = [
        'security/ir.model.access.csv',
    ]
    for security_file in security_files:
        load_data(
            cursor, 'som_polissa_condicions_generals', security_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
