# -*- coding: utf-8 -*-
from __future__ import absolute_import
from tools import config
from oopgrade.oopgrade import MigrationHelper


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    module_name = 'som_switching'
    wizard_model = 'wizard.r101.from.multiple.contracts'
    view_file = 'wizard/wizard_create_r1_from_multiple_contracts_view.xml'
    record_ids = ['view_wizard_create_r1_multiple_contracts_form']

    helper = MigrationHelper(cursor, module_name=module_name)
    helper.init_model(model_name=wizard_model)
    helper.update_xml_records(xml_path=view_file, update_record_ids=record_ids)


def down(cursor, installed_version):
    pass


migrate = up