# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_data
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    pool = pooler.get_pool(cursor.dbname)
    for model_name in (
        'res.partner.creditcard',
        'giscedata.polissa',
        'giscedata.polissa.modcontractual',
        'giscedata.facturacio.factura',
    ):
        pool.get(model_name)._auto_init(cursor, {})

    load_data(
        cursor, 'som_card_payment', 'views/giscedata_polissa_view.xml',
        idref=None, mode='update'
    )
    load_data(
        cursor, 'som_card_payment', 'views/giscedata_facturacio_factura_view.xml',
        idref=None, mode='update'
    )
    load_data(
        cursor, 'som_card_payment', 'data/cron_data.xml',
        idref=None, mode='update'
    )


def down(cursor, installed_version):
    pass


migrate = up
