# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_data_records
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Starting 'Flux Solar ocult a la OV' semantic id creation migration script")
    load_data_records(cursor, "som_polissa", "som_polissa_data.xml", ["categ_flux_solar_ocult_ov"])
    logger.info("Finishing 'Flux Solar ocult a la OV' semantic id creation migration script")


def down(cursor, installed_version):
    pass


migrate = up
