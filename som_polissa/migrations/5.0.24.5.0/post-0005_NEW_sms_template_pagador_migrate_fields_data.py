# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Initializing new fields")

    pool = pooler.get_pool(cursor.dbname)
    pool.get("giscedata.autoconsum.generador")._auto_init(
        cursor, context={'module': 'som_polissa'}
    )
    pool.get("giscedata.cups.ps")._auto_init(
        cursor, context={'module': 'som_polissa'}
    )
    pool.get("giscedata.polissa")._auto_init(
        cursor, context={'module': 'som_polissa'}
    )

    logger.info("Updating XML files")
    data_files = [
        'data/som_polissa_data.xml',
        'data/som_polissa_templates.xml',
        'report/som_polissa_report.xml',
        'views/giscedata_autoconsum_view.xml',
        'views/giscedata_cups_view.xml',
        'views/giscedata_polissa_view.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_polissa', data_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
