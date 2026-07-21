# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info('Creating combined contract summary report XML')
    load_data(
        cursor,
        'som_polissa_condicions_generals',
        'report/giscedata_polissa_contract_summary_full_report.xml',
        idref=None,
        mode='update'
    )


def down(cursor, installed_version):
    pass


migrate = up
