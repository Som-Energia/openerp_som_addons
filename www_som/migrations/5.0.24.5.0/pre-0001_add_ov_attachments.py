# -*- encoding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data, add_columns
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    wiz_obj = pool.get('wizard.import.ref.cadastral.from.csv')
    wiz_obj._auto_init(cursor, context={'module': 'som_polissa'})

    logger.info("Adding column ov_available to ir_attachment_category")
    add_columns(
        cursor, {
            'ir_attachment_category': [
                ('ov_available', 'boolean')
            ]
        }
    )
    logger.info("Column added succesfully.")

    logger.info("Update XMLs")
    load_data(
        cursor, 'som_polissa', "ir_attachment_view.xml", idref=None, mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
