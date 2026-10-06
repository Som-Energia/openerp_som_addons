# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating sign lead wizard buttons")

    load_data_records(
        cursor,
        'som_leads_polissa',
        'wizard/wizard_generar_lead_per_firmar_view.xml',
        ['view_wizard_generar_lead_per_firmar_som_form'],
        mode='update'
    )

    logger.info("Sign lead wizard buttons updated")


def down(cursor, installed_version):
    pass


migrate = up
