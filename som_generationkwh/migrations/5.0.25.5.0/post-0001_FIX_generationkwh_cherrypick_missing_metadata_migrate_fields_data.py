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
    pool.get("giscedata.facturacio.factura")._auto_init(
        cursor, context={'module': 'som_generationkwh'}
    )
    pool.get("giscedata.polissa.tarifa.periodes")._auto_init(
        cursor, context={'module': 'som_generationkwh'}
    )
    pool.get("giscedata.polissa")._auto_init(
        cursor, context={'module': 'som_generationkwh'}
    )
    pool.get("generationkwh.mailmockup")._auto_init(
        cursor, context={'module': 'som_generationkwh'}
    )
    pool.get("generationkwh.investment")._auto_init(
        cursor, context={'module': 'som_generationkwh'}
    )
    pool.get("somenergia.soci")._auto_init(
        cursor, context={'module': 'som_generationkwh'}
    )
    pool.get("generationkwh.kwh.per.share")._auto_init(
        cursor, context={'module': 'som_generationkwh'}
    )

    logger.info("Updating XML files")
    data_files = [
        'som_generationkwh_data.xml',
        'wizard/wizard_baixa_soci.xml',
    ]
    for data_file in data_files:
        load_data(
            cursor, 'som_generationkwh', data_file,
            idref=None, mode='update'
        )
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
