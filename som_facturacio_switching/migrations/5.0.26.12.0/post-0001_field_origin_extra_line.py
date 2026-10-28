# -*- coding: utf-8 -*-
from oopgrade.oopgrade import MigrationHelper
from tools import config


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    mh = MigrationHelper(cursor, 'som_facturacio_switching')
    mh.init_model('giscedata.facturacio.extra')

def down(cursor, installed_version):
    pass


migrate = up
