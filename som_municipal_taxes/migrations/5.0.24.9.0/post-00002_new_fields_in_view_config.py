# -*- encoding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pooler.get_pool(cursor.dbname)

    views = [
        'views/som_municipal_taxes_config_view.xml',
    ]

    for view in views:
        # Crear les diferents vistes
        logger.info("Updating XML {}".format(view))
        load_data(cursor, 'som_municipal_taxes', view, idref=None, mode='update')
        logger.info("XMLs succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
