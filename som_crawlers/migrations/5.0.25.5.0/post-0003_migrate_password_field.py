# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import column_exists, change_column_type


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info(
        "Migrating password from VARCHAR(30) to VARCHAR(100)..."
    )
    if column_exists(cursor, 'som_crawlers_config', 'contrasenya'):
        change_column_type(
            cursor, {
                'som_crawlers_config': [
                    ('contrasenya', 'VARCHAR(100)')
                ]
            }
        )
        logger.info("Column type changed to VARCHAR(100) successfully!")
    else:
        logger.info(
            "Skipping password field migration: column som_crawlers_config.contrasenya not found"
        )


def down(cursor, installed_version):
    pass


migrate = up
