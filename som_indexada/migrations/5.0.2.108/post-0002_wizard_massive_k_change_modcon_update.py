# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating XML wizard/wizard_massive_k_change.xml view")

    data_records = ['view_wizard_massive_k_change_form']
    load_data_records(
        cursor, 'som_indexada', 'wizard/wizard_massive_k_change.xml', data_records, mode="update"
    )
    logger.info("View succesfully updated")


def down(cursor, installed_version):
    pass


migrate = up
