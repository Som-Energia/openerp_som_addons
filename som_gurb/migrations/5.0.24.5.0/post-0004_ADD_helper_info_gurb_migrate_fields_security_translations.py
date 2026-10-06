# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data
from tools.translate import trans_load
from tools import config
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Initializing new fields")

    pool = pooler.get_pool(cursor.dbname)
    pool.get("som.gurb.www")._auto_init(
        cursor, context={'module': 'som_gurb'}
    )

    logger.info("Updating CSV security files")
    security_files = [
        'security/ir.model.access.csv',
    ]
    for security_file in security_files:
        load_data(
            cursor, 'som_gurb', security_file,
            idref=None, mode='update'
        )

    logger.info("Updating translations")
    trans_load(cursor, "{}/{}/i18n/es_ES.po".format(config['addons_path'], "som_gurb"), 'es_ES')  # noqa: E501
    logger.info("Translations succesfully updated.")
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
