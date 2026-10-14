# -*- coding: utf-8 -*-
from __future__ import absolute_import


def migrate(cursor, installed_version):
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_f1_normal_cups_fecha_hasta
        ON public.giscedata_facturacio_importacio_linia
        (cups_text, fecha_factura_hasta DESC)
        WHERE type_factura = 'N'
    """)
