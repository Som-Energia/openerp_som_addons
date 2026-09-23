# -*- coding: utf-8 -*-
from __future__ import absolute_import

from oopgrade.oopgrade import MigrationHelper
from tools import config


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    module = 'som_leads_polissa'
    xml_path = 'views/giscedata_crm_lead_view.xml'
    record_ids = ['giscedata_crm_leads_som_view', 'giscedata_crm_leads_switching_form_som_view']
    mh = MigrationHelper(cursor, module)
    mh.update_xml_records(xml_path=xml_path, update_record_ids=record_ids)


def down(cursor, installed_version):
    pass


migrate = up
