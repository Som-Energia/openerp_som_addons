# -*- encoding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)

    #  Actualitzar un no mòdul al crear-lo i afegir una columna
    logger.info("Creating table: som.municipal.taxes.config")
    pool.get("som.municipal.taxes.config")._auto_init(
        cursor, context={'module': 'som_municipal_taxes'}
    )
    logger.info("Table created succesfully.")

    views = [
        'data/som_municipal_taxes_data.xml',
        'views/som_municipal_taxes_config_view.xml',
        'wizard/wizard_creacio_remesa_pagament_taxes.xml',
        'security/som_municipal_taxes_security.xml',
        'security/ir.model.access.csv',
    ]

    for view in views:
        # Crear les diferents vistes
        logger.info("Updating XML {}".format(view))
        load_data(cursor, 'som_municipal_taxes', view, idref=None, mode='update')
        logger.info("XMLs succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
