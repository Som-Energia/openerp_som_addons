# coding=utf-8

import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info('Creating process step column')
    cursor.execute(
        """
        ALTER TABLE giscedata_atc
        ADD COLUMN process_step VARCHAR(10)
        """
    )


def down(cursor, installed_version):
    pass


migrate = up
