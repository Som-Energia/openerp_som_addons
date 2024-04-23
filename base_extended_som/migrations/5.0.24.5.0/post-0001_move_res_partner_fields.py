# -*- encoding: utf-8 -*-
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Moving ir_model_data/ir_model_fields")
    cursor.execute('''
        UPDATE  ir_model_data
        SET module = 'base_extended_som'
        WHERE id IN (
            SELECT data.id
            FROM ir_model_fields fields
            INNER JOIN ir_model_data data on data.res_id = fields.id
            WHERE fields.model = 'res.partner'
            AND data.model = 'ir.model.fields'
            AND fields.name in (
                'www_email', 'www_soci', 'www_street', 'www_zip',
                'www_mobile', 'www_phone', 'www_provincia', 'www_municipi'
            )
        )
    ''')
    logger.info("Moved succesfully.")


def down(cursor, installed_version):
    pass


migrate = up
