# -*- encoding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data, load_data_records, add_columns


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

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
