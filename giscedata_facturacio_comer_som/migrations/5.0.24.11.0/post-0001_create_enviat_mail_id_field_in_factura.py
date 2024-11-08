# -*- coding: utf-8 -*-
from tools import config
from oopgrade.oopgrade import add_columns_fk, column_exists


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    if not column_exists(cursor, 'giscedata_facturacio_factura', 'enviat_mail_id'):
        new_column_spec = [('enviat_mail_id', 'int', 'poweremail_mailbox', 'id', 'set null')]
        add_columns_fk(cursor, {'giscedata_facturacio_factura': new_column_spec})
    else:
        return

    # ToDo load the view
    # view = "ir/ir.xml"
    # view_record = ["act_report_xml_view"]
    # load_data_records(cursor, 'base', view, view_record, mode='update')

    # ToDo migrate the data


def down(cursor, installed_version):
    pass


migrate = up
