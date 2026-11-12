# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating lead payment view fields")

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

    logger.info("Lead payment view fields updated")


def down(cursor, installed_version):
    pass


migrate = up
