# -*- coding: utf-8 -*-
from __future__ import absolute_import


def migrate(cursor, installed_version):
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS giscedata_facturacio_importacio_linia_cups_text_fecha_factura_h
        ON public.giscedata_facturacio_importacio_linia
        (cups_text, fecha_factura_hasta DESC)
        WHERE type_factura = 'N'
    """)
