# -*- encoding: utf-8 -*-
import logging
from oopgrade.oopgrade import column_exists, change_column_type


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info(
        "Increase 'usuari' column size from 20 to 100..."
    )
    if column_exists(cursor, 'som_crawlers_config', 'usuari'):
        change_column_type(
            cursor, {
                'som_crawlers_config': [
                    ('usuari', 'VARCHAR(100) USING (usuari::VARCHAR(100))')
                ]
            }
        )
    logger.info("Column size increased successfully!")


def down(cursor, installed_version):
    pass


migrate = up
