# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import delete_record


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Deleting deprecated records")
    list_of_records = ["sw_not_m1_02_rebuig_57"]
    delete_record(
        cursor,
        'som_switching',
        list_of_records,
    )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
