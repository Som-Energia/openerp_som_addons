# coding=utf-8
import logging

from oopgrade.oopgrade import MigrationHelper
from tools import config


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info('Updating motiu_facturacio on giscedata_facturacio_importacio_linia table')

    query = '''
        UPDATE giscedata_facturacio_importacio_linia AS f1
        SET motiu_facturacio = foo.tipo_factura
        FROM (
            SELECT f1.id AS f1_id, COALESCE(fact.tipo_factura, '01') AS tipo_factura 
            FROM giscedata_facturacio_importacio_linia f1 
            LEFT JOIN account_invoice ai on ai.origin = f1.invoice_number_text 
            LEFT JOIN giscedata_facturacio_factura fact on fact.invoice_id = ai.id
        ) AS foo
        WHERE f1.id = foo.f1_id
    '''
    cursor.execute(query)

    module = 'som_facturacio_switching'
    mh = MigrationHelper(cursor, module)

    mh.init_model('giscedata.facturacio.importacio.linia')
    file = 'giscedata_facturacio_importacio_linia_view.xml'
    views = [
        'view_importacio_linia_auto_tarifa_codi_rect_anul_form',
        'action_importacio_linia_expedients_inspeccio_frau_som',
        'menu_importacio_linia_abonament_expedients_som',
    ]
    mh.update_xml_records(xml_path=file, init_record_ids=views)


def down(cursor, installed_version):
    pass


migrate = up
