# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XMLs")
    list_of_records = [
        "sw_not_m2_05_motius_nofiticar",
        "sw_not_m2_05_motiu_06",
        "sw_not_m2_05_motiu_07",
    ]
    load_data_records(
        cursor,
        'som_switching',
        'giscedata_switching_notification_data.xml',
        list_of_records,
        mode='update',
    )


def down(cursor, installed_version):
    pass


migrate = up
