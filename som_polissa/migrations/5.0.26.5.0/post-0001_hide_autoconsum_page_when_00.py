# -*- coding: utf-8 -*-
from __future__ import absolute_import
from oopgrade.oopgrade import MigrationHelper
from tools import config


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    module = 'som_polissa'
    file = 'views/giscedata_polissa_view.xml'
    update_records = ['view_som_giscedata_polissa_form']
    mg = MigrationHelper(cursor, module)
    mg.update_xml_records(xml_path=file, update_record_ids=update_records)


def down(cursor, installed_version):
    pass


migrate = up
