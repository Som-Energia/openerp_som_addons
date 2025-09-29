# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import delete_record


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Deleting sw_act_r105_cac")
    delete_record(cursor, 'som_switching', ['sw_act_r105_cac'])
    logger.info("Successfully deleted.")


def down(cursor, installed_version):
    pass


migrate = up
