# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    load_data(
        cursor, 'som_card_payment', 'views/giscedata_polissa_view.xml',
        idref=None, mode='update'
    )


def down(cursor, installed_version):
    pass


migrate = up
