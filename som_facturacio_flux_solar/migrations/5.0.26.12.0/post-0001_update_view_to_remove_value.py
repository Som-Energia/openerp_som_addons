# -*- encoding: utf-8 -*-
from tools import config
from oopgrade.oopgrade import MigrationHelper


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return None

    module = 'som_facturacio_flux_solar'
    xml_file = 'giscedata_bateria_virtual.xml'
    mh = MigrationHelper(cursor, module_name=module)
    mh.update_xml(xml_path=xml_file)
    return True


def down(cursor, installed_version):
    pass


migrate = up
