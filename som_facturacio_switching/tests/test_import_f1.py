# -*- coding: utf-8 -*-
import unittest

from destral import testing
from destral.transaction import Transaction
from expects import *
from datetime import datetime, timedelta
from giscedata_facturacio_switching.tests.test_import_f1 import TestImportF1
from addons import get_module_resource

class TestImportF1Som(TestImportF1):

    def test_validation_3035S_ok(self):
        line_obj = self.openerp.pool.get(
            'giscedata.facturacio.importacio.linia'
        )
        imd_obj = self.openerp.pool.get('ir.model.data')
        error_obj = self.openerp.pool.get(
            'giscedata.facturacio.switching.error'
        )
        err_template_obj = self.openerp.pool.get('giscedata.facturacio.switching.error.template')
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            err_template_id = imd_obj.get_object_reference(cursor, uid, 'som_facturacio_switching', 'error_phase_3_code_S35')[1]
            err_template_obj.write(cursor, uid, err_template_id, {'level':'critical'})

            self.set_comer_and_distri_for_polissa(txn, "polissa_tarifa_018", "4321", "1234")
            self.canvi_potencies(txn, "polissa_tarifa_018", 5.75, {'P1': 4.75, "P2": 5.75})
            self.activar_polissa(txn, polissa_ref="polissa_tarifa_018")
            xml_path = get_module_resource('giscedata_facturacio_switching', 'tests', 'fixtures', "test_20TD.xml")
            with open(xml_path, 'r') as f:
                xml_file = f.read()

            import_id = imd_obj.get_object_reference(cursor, uid, 'giscedata_facturacio_switching', 'f1_import_01')[1]
            line_id = line_obj.create_from_xml(cursor, uid, import_id, 'Import Name', xml_file)
            line_obj.process_line_sync(cursor, uid, line_id)

            line_vals = line_obj.read(cursor, uid, line_id)
            expect(line_vals['state']).to(equal('valid'))
            expect(line_vals['import_phase']).to(equal(40))

            error_codes = []
            error_3035S_id = None
            for error_id in line_vals['error_ids']:
                error_code = error_obj.read(cursor, uid, error_id, ['name', 'level'])
                if error_code['name'] == '3035S':
                    error_3035S_id = error_code['id']
                error_code.pop('id')
                error_codes.append(error_code)

            expect(error_codes).not_to(
                contain({'name': '3035S', 'level': 'warning'})
            )
            expect(error_codes).not_to(
                contain({'name': '3035S', 'level': 'critical'})
            )
            self.assertIsNone(error_3035S_id)

    def test_validation_3035S_error(self):
        line_obj = self.openerp.pool.get(
            'giscedata.facturacio.importacio.linia'
        )
        imd_obj = self.openerp.pool.get('ir.model.data')
        error_obj = self.openerp.pool.get(
            'giscedata.facturacio.switching.error'
        )
        err_template_obj = self.openerp.pool.get('giscedata.facturacio.switching.error.template')
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            err_template_id = imd_obj.get_object_reference(cursor, uid, 'som_facturacio_switching', 'error_phase_3_code_S35')[1]
            err_template_obj.write(cursor, uid, err_template_id, {'level':'critical'})

            self.set_comer_and_distri_for_polissa(txn, "polissa_tarifa_018", "4321", "1234")
            self.canvi_potencies(txn, "polissa_tarifa_018", 5.75, {'P1': 4.75, "P2": 5.75})
            self.activar_polissa(txn, polissa_ref="polissa_tarifa_018")
            xml_path = get_module_resource('giscedata_facturacio_switching', 'tests', 'fixtures', "test_20TD.xml")
            with open(xml_path, 'r') as f:
                xml_file = f.read()
                xml_file = xml_file.replace(
                    "<Lectura>330.00</Lectura>",
                    "<Lectura>430.00</Lectura>"
                )

            import_id = imd_obj.get_object_reference(cursor, uid, 'giscedata_facturacio_switching', 'f1_import_01')[1]
            line_id = line_obj.create_from_xml(cursor, uid, import_id, 'Import Name', xml_file)
            line_obj.process_line_sync(cursor, uid, line_id)

            line_vals = line_obj.read(cursor, uid, line_id)
            expect(line_vals['state']).to(equal('erroni'))
            expect(line_vals['import_phase']).to(equal(30))

            error_codes = []
            error_3035S_id = None
            for error_id in line_vals['error_ids']:
                error_code = error_obj.read(cursor, uid, error_id, ['name', 'level'])
                if error_code['name'] == '3035S':
                    error_3035S_id = error_code['id']
                error_code.pop('id')
                error_codes.append(error_code)

            expect(error_codes).to(
                contain({'name': '3035S', 'level': 'critical'})
            )

            self.assertIsNotNone(error_3035S_id)

    def test_validation_3035S_ok_within_tolerance(self):
        line_obj = self.openerp.pool.get(
            'giscedata.facturacio.importacio.linia'
        )
        imd_obj = self.openerp.pool.get('ir.model.data')
        error_obj = self.openerp.pool.get(
            'giscedata.facturacio.switching.error'
        )
        err_template_obj = self.openerp.pool.get('giscedata.facturacio.switching.error.template')
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            err_template_id = imd_obj.get_object_reference(cursor, uid, 'som_facturacio_switching', 'error_phase_3_code_S35')[1]
            err_template_obj.write(cursor, uid, err_template_id, {'level':'critical'})

            self.set_comer_and_distri_for_polissa(txn, "polissa_tarifa_018", "4321", "1234")
            self.canvi_potencies(txn, "polissa_tarifa_018", 5.75, {'P1': 4.75, "P2": 5.75})
            self.activar_polissa(txn, polissa_ref="polissa_tarifa_018")
            xml_path = get_module_resource('giscedata_facturacio_switching', 'tests', 'fixtures', "test_20TD.xml")
            with open(xml_path, 'r') as f:
                xml_file = f.read()
                xml_file = xml_file.replace(
                    "<Lectura>330.00</Lectura>",
                    "<Lectura>329.00</Lectura>"
                )
                xml_file = xml_file.replace(
                    "<Lectura>220.00</Lectura>",
                    "<Lectura>221.00</Lectura>"
                )

            import_id = imd_obj.get_object_reference(cursor, uid, 'giscedata_facturacio_switching', 'f1_import_01')[1]
            line_id = line_obj.create_from_xml(cursor, uid, import_id, 'Import Name', xml_file)
            line_obj.process_line_sync(cursor, uid, line_id)

            line_vals = line_obj.read(cursor, uid, line_id)
            expect(line_vals['state']).to(equal('valid'))
            expect(line_vals['import_phase']).to(equal(40))

            error_codes = []
            error_3035S_id = None
            for error_id in line_vals['error_ids']:
                error_code = error_obj.read(cursor, uid, error_id, ['name', 'level'])
                if error_code['name'] == '3035S':
                    error_3035S_id = error_code['id']
                error_code.pop('id')
                error_codes.append(error_code)

            expect(error_codes).not_to(
                contain({'name': '3035S', 'level': 'critical'})
            )

            self.assertIsNone(error_3035S_id)

    def test_validation_3035S_error_one_within_tolerance(self):
        line_obj = self.openerp.pool.get(
            'giscedata.facturacio.importacio.linia'
        )
        imd_obj = self.openerp.pool.get('ir.model.data')
        error_obj = self.openerp.pool.get(
            'giscedata.facturacio.switching.error'
        )
        err_template_obj = self.openerp.pool.get('giscedata.facturacio.switching.error.template')
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            err_template_id = imd_obj.get_object_reference(cursor, uid, 'som_facturacio_switching', 'error_phase_3_code_S35')[1]
            err_template_obj.write(cursor, uid, err_template_id, {'level':'critical'})

            self.set_comer_and_distri_for_polissa(txn, "polissa_tarifa_018", "4321", "1234")
            self.canvi_potencies(txn, "polissa_tarifa_018", 5.75, {'P1': 4.75, "P2": 5.75})
            self.activar_polissa(txn, polissa_ref="polissa_tarifa_018")
            self.clean_hash_lines(txn)
            xml_path = get_module_resource('giscedata_facturacio_switching', 'tests', 'fixtures', "test_20TD.xml")
            with open(xml_path, 'r') as f:
                xml_file = f.read()
                xml_file = xml_file.replace(
                    "<Lectura>330.00</Lectura>",
                    "<Lectura>329.00</Lectura>"
                )
                xml_file = xml_file.replace(
                    "<Lectura>220.00</Lectura>",
                    "<Lectura>222.00</Lectura>"
                )

            import_id = imd_obj.get_object_reference(cursor, uid, 'giscedata_facturacio_switching', 'f1_import_01')[1]
            line_id = line_obj.create_from_xml(cursor, uid, import_id, 'Import Name', xml_file)
            line_obj.process_line_sync(cursor, uid, line_id)

            line_vals = line_obj.read(cursor, uid, line_id)
            expect(line_vals['state']).to(equal('erroni'))
            expect(line_vals['import_phase']).to(equal(30))

            error_codes = []
            error_3035S_id = None
            for error_id in line_vals['error_ids']:
                error_code = error_obj.read(cursor, uid, error_id, ['name', 'level'])
                if error_code['name'] == '3035S':
                    error_3035S_id = error_code['id']
                error_code.pop('id')
                error_codes.append(error_code)

            expect(error_codes).to(
                contain({'name': '3035S', 'level': 'critical'})
            )

            self.assertIsNotNone(error_3035S_id)
