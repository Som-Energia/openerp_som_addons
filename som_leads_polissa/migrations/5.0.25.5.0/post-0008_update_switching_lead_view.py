# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating switching lead view")

    load_data_records(
        cursor,
        'som_leads_polissa',
        'views/giscedata_crm_lead_view.xml',
        ['giscedata_crm_leads_switching_som_view'],
        mode='update'
    )

    logger.info("Switching lead view updated")


def down(cursor, installed_version):
    pass


migrate = up
