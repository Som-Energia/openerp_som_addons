# coding=utf-8
from oopgrade import DataMigration
from addons import get_module_resource


def up(cursor, installed_version):
    if not installed_version:
        return
    data_path = get_module_resource(
        'som_generationkwh', 'som_generationkwh_data.xml'
    )
    with open(data_path, 'r') as f:
        data_xml = f.read()
    dm = DataMigration(data_xml, cursor, 'som_generationkwh', {
        'account.account': ['code']
    })
    dm.migrate()

    dm = DataMigration(data_xml, cursor, 'som_generationkwh', {
        'account.journal': ['code']
    })
    dm.migrate()

    dm = DataMigration(data_xml, cursor, 'som_generationkwh', {
        'product.product': ['name']
    })
    dm.migrate()

    dm = DataMigration(data_xml, cursor, 'som_generationkwh', {
        'payment.mode': ['name']
    })
    dm.migrate()

migrate = up
