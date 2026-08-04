# -*- encoding: utf-8 -*-
from tools import config
from oopgrade.oopgrade import MigrationHelper


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return None

    module = 'som_switching'
    xml_file = 'wizard/wizard_create_atc_from_polissa.xml'
    record_ids = [
        'view_wizard_som_switching_create_atc_from_polissa_form',
    ]

    mh = MigrationHelper(cursor, module_name=module)
    mh.update_xml_records(xml_path=xml_file, init_record_ids=record_ids)

    return True


def down(cursor, installed_version):
    pass


migrate = up
