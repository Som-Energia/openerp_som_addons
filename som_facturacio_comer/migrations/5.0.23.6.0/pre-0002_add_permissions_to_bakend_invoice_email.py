# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_access_rules_from_model_name
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating Permissions")
    models = [
        "model_report_backend_invoice_email"
    ]
    load_access_rules_from_model_name(
        cursor, 'som_facturacio_comer', models
    )
    logger.info("Permissions succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
