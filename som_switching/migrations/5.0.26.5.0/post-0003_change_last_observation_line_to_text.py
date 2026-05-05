# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import column_exists, change_column_type


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info(
        "Migrating last_observation_line from VARCHAR(100) to TEXT..."
    )
    if column_exists(cursor, 'giscedata_facturacio_importacio_linia', 'last_observation_line'):
        change_column_type(
            cursor, {
                'giscedata_facturacio_importacio_linia': [
                    ('last_observation_line', 'TEXT')
                ]
            }
        )
    logger.info("Column type changed to TEXT successfully!")


def down(cursor, installed_version):
    pass


migrate = up
