# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction

from expects import *
import osv
import unittest
import csv
import os
import mock


class LotEnviamentTests(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @mock.patch('os.unlink')
    def _attach_csv(self, cursor, uid, lot_enviament_id, csv_path, mocked):
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        return lot_env_obj._attach_csv(cursor, uid, lot_enviament_id, csv_path)

    def _read_csv(self, csv_path):
        results = []
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                results.append(row)
        return results

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_csv')
    def test_create_enviaments_from_attached_csv(self, mocked_create_enviaments_from_csv):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.infoenergia.enviament')

        cursor = self.cursor
        uid = self.uid

        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        lot_enviament = lot_env_obj.browse(cursor, uid, lot_enviament_id)

        script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in

        rel_path = 'T1_2020_minimal.csv'
        abs_file_path = os.path.join(script_dir, rel_path)

        attach_id = self._attach_csv(cursor, uid, lot_enviament_id, abs_file_path)

        lot_enviament.create_enviaments_from_attached_csv(attach_id, {})

        mocked_create_enviaments_from_csv.assert_called_with(cursor, uid, [lot_enviament_id], [{'report': '0001.pdf','text': 'First;Text', 'contractid': '0001'}],{})

    def test_create_single_enviament_polissaNotFound(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.infoenergia.enviament')

        cursor = self.cursor
        uid = self.uid

        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        lot_enviament = lot_env_obj.browse(cursor, uid, lot_enviament_id)

        env_data = {'contractid':'wrong', 'cups': '1',
                'potencia':'2', 'tarifa':'2.0A','informe':'M2',
                'text':'Text', 'valid':'True', 'report':'wrong.pdf'}

        pre_enviaments = env_obj.search(cursor, uid,
            [("lot_enviament", "=", lot_enviament_id),
                ('estat','=','error')]
        )
        lot_enviament.create_single_enviament(env_data, {})
        post_enviaments = env_obj.search(cursor, uid,
            [("lot_enviament", "=", lot_enviament_id),
            ('estat', "=", 'error')]
        )
        self.assertTrue(len(pre_enviaments) < len(post_enviaments))
        envs_info = env_obj.read(cursor, uid, post_enviaments, ['info','estat'])
        for e_info in envs_info:
            self.assertTrue('error' == e_info['estat'])
            self.assertTrue(('No s\'ha trobat la pòlissa ') in e_info['info'])

    def test_create_single_enviament_updateEnviament(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.infoenergia.enviament')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        cursor = self.cursor
        uid = self.uid
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        pol_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        pol_name = pol_obj.read(cursor, uid, pol_id, ['name'])['name']
        lot_enviament = lot_env_obj.browse(cursor, uid, lot_enviament_id)
        lot_enviament.create_single_enviament_from_object(pol_id, context={'tipus': 'infoenergia'})

        csv_updated_data = {'contractid': pol_name, 'cups': '1',
                'potencia':'2', 'tarifa':'2.0A','informe':'M2',
                'text':'Updated Text', 'valid':'True', 'report':'0001.pdf'}

        lot_enviament.create_single_enviament(csv_updated_data, context={'path_pdf': 'test_path', 'tipus':'infoenergia'})

        updated_env = env_obj.search(cursor, uid,
            [("lot_enviament", "=", lot_enviament_id),
                ('pdf_filename','=','test_path/0001.pdf')]
        )
        self.assertEqual(len(updated_env),1)
        self.assertEqual(env_obj.read(cursor, uid, updated_env, ['body_text'])[0]['body_text'], 'Updated Text')

    def test_create_single_enviament_polissaInactive(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.infoenergia.enviament')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        cursor = self.cursor
        uid = self.uid

        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        lot_enviament = lot_env_obj.browse(cursor, uid, lot_enviament_id)

        pol_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        pol_obj.write(cursor, uid, pol_id, {'name':'inactive','active':False})
        pol_name = pol_obj.read(cursor, uid, pol_id, ['name'])['name']

        csv_data = {'contractid':pol_name, 'cups': '1',
                'potencia':'2', 'tarifa':'2.0A','informe':'M2',
                'text':'Text', 'valid':'True', 'report':'{}.pdf'.format(pol_name)}

        lot_enviament.create_single_enviament(csv_data, {})
        post_enviaments = env_obj.search(cursor, uid,
            [("lot_enviament", "=", lot_enviament_id),
            ('estat', "=", 'cancellat'), ('polissa_id','=', pol_id),
            ('info','ilike','La pòlissa {} està donada de baixa'.format(pol_name))
            ])
        self.assertEqual(len(post_enviaments), 1)

    def test_create_single_enviament_from_object(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.infoenergia.enviament')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        cursor = self.cursor
        uid = self.uid
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        lot_enviament = lot_env_obj.browse(cursor, uid, lot_enviament_id)
        pol_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0005'
        )[1]
        enviaments_in_lot = env_obj.search(cursor, uid, [('lot_enviament','=',lot_enviament_id),('polissa_id','=',pol_id)])
        self.assertEqual(len(enviaments_in_lot), 0)
        pol_name = pol_obj.read(cursor, uid, pol_id, ['name'])['name']

        lot_enviament.create_single_enviament_from_object(pol_id, context={'tipus': 'infoenergia'})

        post_enviaments = env_obj.search(cursor, uid,
            [("lot_enviament", "=", lot_enviament_id),
            ('estat', "=", 'preesborrany'), ('polissa_id','=', pol_id),
            ('info','ilike','Enviament creat des de polissa_id')
            ])
        self.assertEqual(len(post_enviaments), 1)

    def test_create_single_enviament_from_object_lot_tipus_altres_from_pol(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.enviament.massiu')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        cursor = self.cursor
        uid = self.uid
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0002'
        )[1]
        lot_enviament = lot_env_obj.browse(cursor, uid, lot_enviament_id)
        pol_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0005'
        )[1]
        enviaments_in_lot = env_obj.search(cursor, uid, [('lot_enviament','=',lot_enviament_id),('polissa_id','=',pol_id)])
        self.assertEqual(len(enviaments_in_lot), 0)
        pol_name = pol_obj.read(cursor, uid, pol_id, ['name'])['name']

        lot_enviament.create_single_enviament_from_object(pol_id, context={'tipus': 'altres', 'from_model': 'polissa_id'})

        post_enviaments = env_obj.search(cursor, uid,
            [("lot_enviament", "=", lot_enviament_id),
            ('estat', "=", 'obert'), ('polissa_id','=', pol_id),
            ('info','ilike','Enviament creat des de polissa_id')
            ])
        self.assertEqual(len(post_enviaments), 1)

    def test_create_single_enviament_from_object_lot_tipus_altres_from_partner(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.enviament.massiu')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        cursor = self.cursor
        uid = self.uid
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0002'
        )[1]
        lot_enviament = lot_env_obj.browse(cursor, uid, lot_enviament_id)
        partner_id = imd_obj.get_object_reference(
            cursor, uid, 'base', 'res_partner_5'
        )[1]
        enviaments_in_lot = env_obj.search(cursor, uid, [('lot_enviament','=',lot_enviament_id),('partner_id','=', partner_id)])
        self.assertEqual(len(enviaments_in_lot), 0)

        lot_enviament.create_single_enviament_from_object(partner_id, context={'tipus': 'altres', 'from_model': 'partner_id'})

        post_enviaments = env_obj.search(cursor, uid,
            [("lot_enviament", "=", lot_enviament_id),
            ('estat', "=", 'obert'), ('partner_id','=', partner_id),
            ('info','ilike','Enviament creat des de partner_id')
            ])
        self.assertEqual(len(post_enviaments), 1)

    def test_create_single_enviament_from_object_lot_tipus_altres_from_partner_already_exist(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.enviament.massiu')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        cursor = self.cursor
        uid = self.uid
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0002'
        )[1]
        lot_enviament = lot_env_obj.browse(cursor, uid, lot_enviament_id)
        partner_id = imd_obj.get_object_reference(
            cursor, uid, 'base', 'res_partner_agrolait'
        )[1]
        enviaments_in_lot = env_obj.search(cursor, uid, [('lot_enviament','=',lot_enviament_id),('partner_id','=', partner_id)])
        self.assertEqual(len(enviaments_in_lot), 1)

        lot_enviament.create_single_enviament_from_object(partner_id, context={'tipus': 'altres', 'from_model': 'partner_id'})

        post_enviaments = env_obj.search(cursor, uid,
            [("lot_enviament", "=", lot_enviament_id),
            ('estat', "=", 'enviat'), ('partner_id','=', partner_id),
            ])
        self.assertEqual(len(post_enviaments), 1)

    def test_ff_totals_ff_progress_altres(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        cursor = self.cursor
        uid = self.uid
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0004'
        )[1]
        lot_enviament = lot_env_obj.browse(cursor, uid, lot_enviament_id)

        self.assertEqual(lot_enviament.total_enviaments, 4)
        self.assertEqual(lot_enviament.total_env_csv, 0)
        self.assertEqual(lot_enviament.total_enviats, 1)
        self.assertEqual(lot_enviament.total_encuats, 1)
        self.assertEqual(lot_enviament.total_oberts, 1)
        self.assertEqual(lot_enviament.total_esborrany, 0)
        self.assertEqual(lot_enviament.total_preesborrany, 0)
        self.assertEqual(lot_enviament.total_cancelats, 1)
        self.assertEqual(lot_enviament.total_errors, 0)
        self.assertEqual(lot_enviament.env_csv_progress, 0)
        self.assertEqual(lot_enviament.pdf_download_progress, 0)
        self.assertEqual(lot_enviament.env_sending_progress, 25)

    def test_ff_totals_ff_progress_infoenergia(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        cursor = self.cursor
        uid = self.uid
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0003'
        )[1]
        lot_enviament = lot_env_obj.browse(cursor, uid, lot_enviament_id)

        self.assertEqual(lot_enviament.total_preesborrany, 0)
        self.assertEqual(lot_enviament.total_esborrany, 1)
        self.assertEqual(lot_enviament.total_oberts, 2)
        self.assertEqual(lot_enviament.total_enviats, 0)
        self.assertEqual(lot_enviament.total_cancelats, 0)
        self.assertEqual(lot_enviament.total_errors, 0)
        self.assertEqual(lot_enviament.total_encuats, 0)
        self.assertEqual(lot_enviament.total_enviaments, 3)
        self.assertEqual(lot_enviament.total_env_csv, 2)
        self.assertEqual(lot_enviament.env_csv_progress, 66.66666666666666)
        self.assertEqual(lot_enviament.pdf_download_progress, 66.66666666666666)
        self.assertEqual(lot_enviament.env_sending_progress, 0)

