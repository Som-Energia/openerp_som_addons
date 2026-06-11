# -*- coding: utf-8 -*-
import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Removing ir_model_data ")

    fields = ['field_giscedata_facturacio_contracte_lot_tarifaATR',
              'field_giscedata_facturacio_contracte_lot_llista_preu']
    for field in fields:
        sql = """SELECT id, res_id FROM ir_model_data WHERE name='{}'""".format(field)
        cursor.execute(sql)
        camp = cursor.fetchOne()
        if camp:
            sql = """DELETE FROM ir_model_data WHERE name = '{}' """.format(camp[0])
            cursor.execute(sql)
            sql = """DELETE FROM ir_model_fields WHERE id = {} """.format(camp[1])
            cursor.execute(sql)


def down(cursor, installed_version):
    pass


migrate = up
