# coding=utf-8
from oopgrade import oopgrade


def up(cursor, installed_version):
    if not installed_version:
        return

    module = "giscedata_facturacio_importacio_linia"

    oopgrade.rename_columns(
        cursor, {module: [("codi_rectificada_anulada", "codi_rectificada_anulada_pre_camp_gisce")]}
    )


def down(cursor, installed_version):
    if not installed_version:
        return
    oopgrade.rename_columns(
        cursor,
        {
            "giscedata_facturacio_importacio_linia": [
                ("codi_rectificada_anulada_pre_camp_gisce", "codi_rectificada_anulada")
            ]
        },
    )


migrate = up
