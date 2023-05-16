# coding=utf-8
from oopgrade import oopgrade


def up(cursor, installed_version):
    if not installed_version:
        return

    module = 'giscedata_facturacio_importacio_linia'

    oopgrade.load_data(
        cursor, module, 'giscedata_facturacio_importacio_linia_view.xml', mode='update'
    )

def down(cursor, installed_version):
    if not installed_version:
        return

    module = 'giscedata_facturacio_importacio_linia'

    oopgrade.load_data(
        cursor, module, 'giscedata_facturacio_importacio_linia_view.xml', mode='update'
    )

migrate = up
