# coding=utf-8
from oopgrade import DataMigration
from addons import get_module_resource


def up(cursor, installed_version):
    if not installed_version:
        return
    data_path = get_module_resource(
        'account_invoice_som', 'account_invoice_som_data.xml'
    )
    with open(data_path, 'r') as f:
        data_xml = f.read()
    dm = DataMigration(data_xml, cursor, 'account_invoice_som', {
        'poweremail.templates': ['name']
    })
    dm.migrate()

migrate = up

