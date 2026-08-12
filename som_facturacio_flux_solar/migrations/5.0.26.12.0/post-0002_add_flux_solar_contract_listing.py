# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from tools import config
from oopgrade.oopgrade import MigrationHelper


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return None

    mh = MigrationHelper(cursor, module_name='som_facturacio_flux_solar')
    mh.update_xml(xml_path='giscedata_bateria_virtual.xml')
    return True


def down(cursor, installed_version):
    pass


migrate = up
