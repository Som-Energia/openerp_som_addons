# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating access CSV")
    load_data(
        cursor, 'som_l10n_ES_aeat_mod347', 'security/ir.model.access.csv',
        idref=None, mode='update'
    )
    logger.info("CSV succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
