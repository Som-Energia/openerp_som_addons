# -*- coding: utf-8 -*-
from __future__ import absolute_import

from oopgrade.oopgrade import MigrationHelper
from tools import config


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    mh = MigrationHelper(cursor, module_name='giscedata_facturacio_indexada_som')
    mh.update_xml('indexed_formula_data.xml')


def down(cursor, installed_version):
    pass


migrate = up
