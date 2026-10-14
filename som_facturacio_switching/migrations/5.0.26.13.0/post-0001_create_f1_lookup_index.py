# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    logging.getLogger('openerp.migration').info(
        "Creating F1 lookup index for som_facturacio_switching"
    )
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS giscedata_facturacio_importacio_linia_cups_text_fecha_factura_h
        ON public.giscedata_facturacio_importacio_linia
        (cups_text, fecha_factura_hasta DESC)
        WHERE type_factura = 'N'
    """)


def down(cursor, installed_version):
    pass


migrate = up
