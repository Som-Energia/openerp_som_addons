# -*- encoding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data, load_data_records, add_columns
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    wiz_obj = pool.get('wizard.import.ref.cadastral.from.csv')
    wiz_obj._auto_init(cursor, context={'module': 'www_som'})

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
    load_data(cursor, 'www_som', "ir_attachment_view.xml", idref=None, mode='update')
    load_data_records(
        cursor, "www_som", "www_som_data.xml",
        ["ir_attachment_category_ov_fiscal"], mode="update",
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
