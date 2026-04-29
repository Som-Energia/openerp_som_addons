# -*- coding: utf-8 -*-
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Deactivating bosocial_BS01 product and product_uom_day")

    cursor.execute("""
        SELECT imd.res_id, imd.model
        FROM ir_model_data imd
        WHERE imd.module = 'som_polissa_soci'
          AND imd.name IN ('bosocial_BS01', 'categ_bo_social', 'product_uom_day', 'categ_uom_day')
    """)
    records = cursor.fetchall()
    logger.info("Found %d records in ir_model_data", len(records))

    for res_id, model in records:
        if model == 'product.product':
            cursor.execute("""
                UPDATE product_product
                SET active = false
                WHERE id = %s
            """, (res_id,))
        elif model == 'product.uom':
            cursor.execute("""
                UPDATE product_uom
                SET active = false
                WHERE id = %s
            """, (res_id,))

    cursor.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'som_polissa_soci'
          AND name IN ('bosocial_BS01', 'categ_bo_social', 'product_uom_day', 'categ_uom_day')
    """)

    logger.info("bosocial_BS01 and product_uom_day deactivated.")


def down(cursor, installed_version):
    pass


migrate = up
