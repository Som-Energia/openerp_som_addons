# -*- coding: utf-8 -*-
import logging
from tools import config
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating giscedata_facturacio_switching_error_data.xml")
    load_data_records(
        cursor,
        'som_facturacio_switching',
        'giscedata_facturacio_switching_error_data.xml',
        ['giscedata_facturacio_switching.error_phase_3_code_043'],
        mode='update'
    )
    logger.info("XMLs succesfully updated.")

    # Run the script: manual_migration.py


def down(cursor, installed_version):
    pass


migrate = up
