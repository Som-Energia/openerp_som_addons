# -*- coding: utf-8 -*-
import logging

from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info('Creating contract summary report backend model')

    pool = pooler.get_pool(cursor.dbname)
    pool.get('report.backend.contract.summary')._auto_init(
        cursor, context={'module': 'som_polissa_condicions_generals'}
    )

    logger.info('Updating contract summary report XML')
    load_data(
        cursor,
        'som_polissa_condicions_generals',
        'report/giscedata_polissa_contract_summary_report.xml',
        idref=None,
        mode='update'
    )

    logger.info('Updating contract summary security CSV')
    load_data(
        cursor,
        'som_polissa_condicions_generals',
        'security/ir.model.access.csv',
        idref=None,
        mode='update'
    )

    logger.info('Contract summary migration completed successfully.')


def down(cursor, installed_version):
    pass


migrate = up
