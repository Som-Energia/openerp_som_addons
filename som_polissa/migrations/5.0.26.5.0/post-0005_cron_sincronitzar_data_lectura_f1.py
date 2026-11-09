# -*- encoding: utf-8 -*-

from oopgrade.oopgrade import MigrationHelper
from tools import config


def up(cursor, installed_version):
    if not installed_version and config.updating_all:
        return

    helper = MigrationHelper(cursor, module_name='som_polissa')
    helper.update_xml_records(xml_path='/data/som_polissa_data.xml',
        init_record_ids=[
            'ir_cron_sincronitzar_data_lectura_f1',
        ])


def down(cursor, installed_version):
    pass


migrate = up