# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XMLs")
    list_of_records = [
        "som_sw_act_m105_ct_traspas",
        "sw_act_m105_acord_repartiment_autoconsum",
    ]
    load_data_records(
        cursor,
        'som_switching',
        'giscedata_switching_activation_data.xml',
        list_of_records,
        mode='update',
    )


def down(cursor, installed_version):
    pass


migrate = up
