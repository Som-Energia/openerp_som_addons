# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Initializing GURB coefficient file and agreement date fields")
    pool = pooler.get_pool(cursor.dbname)
    for model in ['som.gurb.cau', 'wizard.create.coeficients.file']:
        pool.get(model)._auto_init(cursor, context={'module': 'som_gurb'})

    for data_file in [
        'views/som_gurb_cau_view.xml',
        'wizard/wizard_create_coef_file_view.xml',
    ]:
        load_data(cursor, 'som_gurb', data_file, idref=None, mode='update')

    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
