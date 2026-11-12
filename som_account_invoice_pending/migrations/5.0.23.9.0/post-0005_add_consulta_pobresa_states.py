# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    #  Actualitzar una part de l'XML (cal posar la id del record)
    logger.info("Updating XMLs")
    list_of_records = [
        "pendent_monitori_default_pending_state",
        "pendent_monitori_bo_social_pending_state",
    ]
    load_data_records(
        cursor, 'som_account_invoice_pending', 'data/som_account_invoice_pending_data.xml',
        list_of_records, mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
