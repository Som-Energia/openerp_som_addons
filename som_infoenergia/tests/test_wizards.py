# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction

from expects import *
import osv
import base64

import csv
import os
import mock


class WizardSendReportsTests(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @mock.patch('som_infoenergia.som_infoenergia_enviament.SomInfoenergiaEnviament.send_reports')
    def test_send_reports_from_lot(self, mocked_send_reports):
        imd_obj = self.openerp.pool.get('ir.model.data')
        env_obj = self.openerp.pool.get('som.infoenergia.enviament')
        cursor = self.cursor
        uid = self.uid
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        env_ids = env_obj.search(cursor, uid, [('lot_enviament','=', lot_enviament_id), ('estat', '=', 'obert')])
        wiz_obj = self.openerp.pool.get('wizard.infoenergia.send.reports')
        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
            'from_model':'som.infoenergia.lot.enviament'
        }

        wiz_id = wiz_obj.create(cursor, uid, {},context=ctx)
        wiz_obj.send_reports(cursor, uid, [wiz_id], context=ctx)
        mocked_send_reports.assert_called_with(cursor, uid, env_ids, context={'allow_reenviar':False})

    @mock.patch('som_infoenergia.som_infoenergia_enviament.SomInfoenergiaEnviament.send_reports')
    def test_send_reports_from_lot_max_one(self, mocked_send_reports):
        imd_obj = self.openerp.pool.get('ir.model.data')
        env_obj = self.openerp.pool.get('som.infoenergia.enviament')
        cursor = self.cursor
        uid = self.uid
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        env_ids = env_obj.search(cursor, uid, [('lot_enviament','=', lot_enviament_id), ('estat', '=', 'obert')])
        wiz_obj = self.openerp.pool.get('wizard.infoenergia.send.reports')
        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
            'from_model':'som.infoenergia.lot.enviament'
        }
        self.assertTrue(len(env_ids) > 1)
        wiz_id = wiz_obj.create(cursor, uid, {'n_max_mails':1},context=ctx)
        wiz_obj.send_reports(cursor, uid, [wiz_id], context=ctx)
        mocked_send_reports.assert_called_with(cursor, uid, env_ids[:1], context={'allow_reenviar':False})


    @mock.patch('som_infoenergia.som_infoenergia_enviament.SomInfoenergiaEnviament.send_reports')
    def test_send_reports_from_enviament(self, mocked_send_reports):
        imd_obj = self.openerp.pool.get('ir.model.data')
        cursor = self.cursor
        uid = self.uid
        enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'enviament_obert_amb_attach'
        )[1]

        wiz_obj = self.openerp.pool.get('wizard.infoenergia.send.reports')
        ctx = {
            'active_id': enviament_id, 'active_ids': [enviament_id],
            'from_model':'som.infoenergia.enviament'
        }

        wiz_id = wiz_obj.create(cursor, uid, {},context=ctx)
        wiz_obj.send_reports(cursor, uid, [wiz_id], context=ctx)
        mocked_send_reports.assert_called_with(cursor, uid, [enviament_id], context={'allow_reenviar':False})


    @mock.patch('som_infoenergia.som_infoenergia_enviament.SomInfoenergiaEnviament.send_reports')
    def test_send_reports_from_test_lot_missing_email(self, mocked_send_reports):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        cursor = self.cursor
        uid = self.uid
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        lot_env_obj.write(cursor, uid, lot_enviament_id, {'is_test': True})
        wiz_obj = self.openerp.pool.get('wizard.infoenergia.send.reports')
        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
            'from_model':'som.infoenergia.lot.enviament'
        }

        wiz_id = wiz_obj.create(cursor, uid, {},context=ctx)
        with self.assertRaises(osv.osv.except_osv) as error_email:
            wiz_obj.send_reports(cursor, uid, [wiz_id], context=ctx)
        self.assertEqual(error_email.exception.value, "Cal indicar l'email destinatari de l'enviament")
        mocked_send_reports.assert_not_called()

    @mock.patch('som_infoenergia.som_infoenergia_enviament.SomInfoenergiaEnviament.send_reports')
    def test_send_reports_from_test_lot(self, mocked_send_reports):
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.infoenergia.enviament')
        cursor = self.cursor
        uid = self.uid
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        lot_env_obj.write(cursor, uid, lot_enviament_id, {'is_test': True})

        env_ids = env_obj.search(cursor, uid, [('lot_enviament','=', lot_enviament_id), ('estat', '=', 'obert')])
        wiz_obj = self.openerp.pool.get('wizard.infoenergia.send.reports')
        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
            'from_model':'som.infoenergia.lot.enviament'
        }
        vals = {
            'email_to':'test@test.com', 'email_subject':'TEST',
            'allow_reenviar':False
        }
        wiz_id = wiz_obj.create(cursor, uid, vals.copy(),context=ctx)
        wiz_obj.send_reports(cursor, uid, [wiz_id], context=ctx)
        mocked_send_reports.assert_called_with(cursor, uid, env_ids, context=vals)


class WizardMultipleStateChange(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_multiple_state_change(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        cursor = self.cursor
        uid = self.uid
        enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'enviament_obert_amb_attach'
        )[1]
        wiz_obj = self.openerp.pool.get('wizard.infoenergia.multiple.state.change')
        ctx = {
            'active_id': enviament_id, 'active_ids': [enviament_id],
        }
        vals = {'new_state':'esborrany', 'message':''}
        wiz_id = wiz_obj.create(cursor, uid, vals,context=ctx)

        wiz_obj.multiple_state_change(cursor, uid, [wiz_id], context=ctx)

        env_obj = self.openerp.pool.get('som.infoenergia.enviament')
        env_data = env_obj.read(cursor, uid, enviament_id, ['estat', 'info'])
        self.assertTrue('Obert -> Esborrany' in env_data['info'])
        self.assertEqual('esborrany', env_data['estat'])



class WizardCancelFromCSVTestsAndAddContractsLot(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_wizard_invalid_active_id__exception_raises(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        cursor = self.cursor
        uid = self.uid
        wiz_obj = self.openerp.pool.get('wizard.infoenergia.add.contracts.lot')

        wiz_id = wiz_obj.create(cursor, uid, {},{})
        with self.assertRaises(osv.osv.except_osv) as e:
            wiz_obj.add_contracts_lot(cursor, uid, [wiz_id], {})
        self.assertEqual(e.exception.value, "S'ha de seleccionar un lot")

        wiz_id = wiz_obj.create(cursor, uid, {},{})
        with self.assertRaises(osv.osv.except_osv) as e:
            wiz_obj.add_contracts_lot(cursor, uid, [wiz_id], {'active_ids': [wiz_id, 2]})
        self.assertEqual(e.exception.value, "S'ha de seleccionar un lot")


    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_wizard_invalid_active_id__access_fare(self, mocked_create_enviaments_from_object_list):
        imd_obj = self.openerp.pool.get('ir.model.data')
        cursor = self.cursor
        uid = self.uid
        wiz_obj = self.openerp.pool.get('wizard.infoenergia.add.contracts.lot')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        expected_ids = pol_obj.search(cursor, uid, [('tarifa','ilike','%2.0%')])

        context = {'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id]}
        wiz_id = wiz_obj.create(
            cursor, uid, {'access_fare':'2.0'},
            context=context
        )
        wiz_obj.add_contracts_lot(cursor, uid, [wiz_id], context)

        mocked_create_enviaments_from_object_list.assert_called_with(cursor, uid, lot_enviament_id, expected_ids, {'from_model': 'polissa_id'})

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_wizard_invalid_active_id__invalid_cateogry(self, mocked_create_enviaments_from_object_list):
        imd_obj = self.openerp.pool.get('ir.model.data')
        cursor = self.cursor
        uid = self.uid
        wiz_obj = self.openerp.pool.get('wizard.infoenergia.add.contracts.lot')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]

        context = {'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id]}
        wiz_id = wiz_obj.create(
            cursor, uid, {'category':'InexistantCategory'},
            context=context
        )
        wiz_obj.add_contracts_lot(cursor, uid, [wiz_id], context)

        mocked_create_enviaments_from_object_list.assert_called_with(cursor, uid, lot_enviament_id, [], {'from_model': 'polissa_id'})


    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_wizard_invalid_active_id__no_filters(self, mocked_create_enviaments_from_object_list):
        imd_obj = self.openerp.pool.get('ir.model.data')
        cursor = self.cursor
        uid = self.uid
        wiz_obj = self.openerp.pool.get('wizard.infoenergia.add.contracts.lot')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        lot_enviament_id = imd_obj.get_object_reference(
            cursor, uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        expected_ids = pol_obj.search(cursor, uid, [])

        context = {'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id]}
        wiz_id = wiz_obj.create(
            cursor, uid, {},
            context=context
        )
        wiz_obj.add_contracts_lot(cursor, uid, wiz_id, context)

        mocked_create_enviaments_from_object_list.assert_called_with(cursor, uid, lot_enviament_id, expected_ids, {'from_model': 'polissa_id'})

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.cancel_enviaments_from_polissa_names')
    def test_cancel_from_csv__one(self, mock_cancel):
        wiz_obj = self.openerp.pool.get('wizard.cancel.from.csv')
        imd_obj = self.openerp.pool.get('ir.model.data')
        env_obj = self.openerp.pool.get('som.infoenergia.enviament')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        csv_content = "0001"
        encoded_csv = base64.b64encode(csv_content)
        vals = {
            'csv_file': encoded_csv,
            'reason': 'Test'
        }
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }
        env_ids = env_obj.search(self.cursor, self.uid, [('lot_enviament', '=', lot_enviament_id), ('polissa_id.name', '=', '0001')])
        wiz_id = wiz_obj.create(self.cursor, self.uid, vals,context=ctx)

        wiz_obj.cancel_from_file(self.cursor, self.uid, [wiz_id], context=ctx)

        mock_cancel.assert_called_with(self.cursor, self.uid, lot_enviament_id, ["0001"], ctx)
        self.assertTrue(
            "Cancel·lats enviaments des de CSV amb 1 línies"
            in lot_env_obj.read(self.cursor, self.uid, lot_enviament_id, ['info'])['info']
        )

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.cancel_enviaments_from_polissa_names')
    def test_cancel_from_csv__many(self, mock_cancel):
        wiz_obj = self.openerp.pool.get('wizard.cancel.from.csv')
        imd_obj = self.openerp.pool.get('ir.model.data')
        env_obj = self.openerp.pool.get('som.infoenergia.enviament')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        csv_content = "0001\n0002"
        encoded_csv = base64.b64encode(csv_content)
        vals = {
            'csv_file': encoded_csv,
            'reason': 'Test'
        }
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }
        env_ids = env_obj.search(self.cursor, self.uid, [('lot_enviament', '=', lot_enviament_id), ('polissa_id.name', '=', '0001')])
        wiz_id = wiz_obj.create(self.cursor, self.uid, vals,context=ctx)

        wiz_obj.cancel_from_file(self.cursor, self.uid, [wiz_id], context=ctx)

        mock_cancel.assert_called_with(self.cursor, self.uid, lot_enviament_id, ["0001", "0002"], ctx)

        self.assertTrue(
            "Cancel·lats enviaments des de CSV amb 2 línies"
            in lot_env_obj.read(self.cursor, self.uid, lot_enviament_id, ['info'])['info']
        )

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_create_enviaments_from_csv__infoenergia_none(self, mock_create):
        wiz_obj = self.openerp.pool.get('wizard.create.enviaments.from.csv')
        imd_obj = self.openerp.pool.get('ir.model.data')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        csv_content = ""
        encoded_csv = base64.b64encode(csv_content)
        vals = {
            'csv_file': encoded_csv,
        }
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }

        wiz_id = wiz_obj.create(self.cursor, self.uid, vals, context=ctx)

        wiz_obj.create_from_file(self.cursor, self.uid, [wiz_id], context=ctx)

        mock_create.assert_called_with(self.cursor, self.uid, lot_enviament_id, [], {'from_model': 'polissa_id'})
        wiz_info = wiz_obj.read(self.cursor, self.uid, [wiz_id], ['info'])[0]['info']
        self.assertEqual(wiz_info, "Es crearan els enviaments de 0 pòlisses en segon pla")

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_create_enviaments_from_csv__infoenergia_one(self, mock_create):
        wiz_obj = self.openerp.pool.get('wizard.create.enviaments.from.csv')
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0002'
        )[1]
        pol_name = pol_obj.read(self.cursor, self.uid, pol_id, ['name'])['name']
        csv_content = "{}".format(pol_name)
        encoded_csv = base64.b64encode(csv_content)
        vals = {
            'csv_file': encoded_csv,
        }

        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }

        wiz_id = wiz_obj.create(self.cursor, self.uid, vals, context=ctx)

        wiz_obj.create_from_file(self.cursor, self.uid, [wiz_id], context=ctx)

        mock_create.assert_called_with(self.cursor, self.uid, lot_enviament_id, [pol_id], {'from_model': 'polissa_id'})
        wiz_info = wiz_obj.read(self.cursor, self.uid, [wiz_id], ['info'])[0]['info']
        self.assertEqual(wiz_info, "Es crearan els enviaments de 1 pòlisses en segon pla")

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_create_enviaments_from_csv__infoenergia_many(self, mock_create):
        wiz_obj = self.openerp.pool.get('wizard.create.enviaments.from.csv')
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0001'
        )[1]
        pol_id_2 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0002'
        )[1]
        pol_id_3 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0003'
        )[1]
        pol_name_2 = pol_obj.read(self.cursor, self.uid, pol_id_2, ['name'])['name']
        pol_name_3 = pol_obj.read(self.cursor, self.uid, pol_id_3, ['name'])['name']
        csv_content = "{}\n{}".format(pol_name_2, pol_name_3)
        encoded_csv = base64.b64encode(csv_content)
        vals = {
            'csv_file': encoded_csv,
        }

        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }

        wiz_id = wiz_obj.create(self.cursor, self.uid, vals, context=ctx)

        wiz_obj.create_from_file(self.cursor, self.uid, [wiz_id], context=ctx)

        mock_create.assert_called_with(self.cursor, self.uid, lot_enviament_id, [pol_id_2, pol_id_3], {'from_model': 'polissa_id'})
        wiz_info = wiz_obj.read(self.cursor, self.uid, [wiz_id], ['info'])[0]['info']
        self.assertEqual(wiz_info, "Es crearan els enviaments de 2 pòlisses en segon pla")



    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_create_enviaments_from_csv__massive_extra_info(self, mock_create):
        wiz_obj = self.openerp.pool.get('wizard.create.enviaments.from.csv')
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.enviament.massiu')
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0002'
        )[1]
        pol_id_2 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0002'
        )[1]
        pol_id_3 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0003'
        )[1]
        pol_name_2 = pol_obj.read(self.cursor, self.uid, pol_id_2, ['name'])['name']
        pol_name_3 = pol_obj.read(self.cursor, self.uid, pol_id_3, ['name'])['name']
        csv_content = "polissa,extra_info,k\n{},Info 1,234\n{},Info 2,213".format(pol_name_2, pol_name_3)
        encoded_csv = base64.b64encode(csv_content)
        vals = {
            'csv_file': encoded_csv,
        }

        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }
        wiz_id = wiz_obj.create(self.cursor, self.uid, vals, context=ctx)

        wiz_obj.create_from_file(self.cursor, self.uid, [wiz_id], context=ctx)

        mock_create.assert_called_with(self.cursor, self.uid, lot_enviament_id, [pol_id_2, pol_id_3],
            {'from_model': 'polissa_id', 'extra_text': {'0002': {'k': '234', 'extra_info': 'Info 1'},
             '0003': {'k': '213', 'extra_info': 'Info 2'}}})
        wiz_info = wiz_obj.read(self.cursor, self.uid, [wiz_id], ['info'])[0]['info']
        self.assertEqual(wiz_info, "Es crearan els enviaments de 2 pòlisses en segon pla")


    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_create_enviaments_from_csv__massive_extra_info(self, mock_create):
        wiz_obj = self.openerp.pool.get('wizard.create.enviaments.from.csv')
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.enviament.massiu')
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0002'
        )[1]
        pol_id_2 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0002'
        )[1]
        pol_id_3 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0003'
        )[1]
        pol_name_2 = pol_obj.read(self.cursor, self.uid, pol_id_2, ['name'])['name']
        pol_name_3 = pol_obj.read(self.cursor, self.uid, pol_id_3, ['name'])['name']
        csv_content = "polissa,extra_info,k\n{},Info 1,234\n{},Info 2,213".format(pol_name_2, pol_name_3)
        encoded_csv = base64.b64encode(csv_content)
        vals = {
            'csv_file': encoded_csv,
        }

        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }
        wiz_id = wiz_obj.create(self.cursor, self.uid, vals, context=ctx)

        wiz_obj.create_from_file(self.cursor, self.uid, [wiz_id], context=ctx)

        mock_create.assert_called_with(self.cursor, self.uid, lot_enviament_id, [pol_id_2, pol_id_3],
            {'from_model': 'polissa_id', 'extra_text': {'0002': {'k': '234', 'extra_info': 'Info 1'},
             '0003': {'k': '213', 'extra_info': 'Info 2'}}})
        wiz_info = wiz_obj.read(self.cursor, self.uid, [wiz_id], ['info'])[0]['info']
        self.assertEqual(wiz_info, "Es crearan els enviaments de 2 pòlisses en segon pla")

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_create_enviaments_from_csv__massive_extra_info_without_header(self, mock_create):
        wiz_obj = self.openerp.pool.get('wizard.create.enviaments.from.csv')
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.enviament.massiu')
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0002'
        )[1]
        pol_id_2 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0002'
        )[1]
        pol_id_3 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0003'
        )[1]
        pol_name_2 = pol_obj.read(self.cursor, self.uid, pol_id_2, ['name'])['name']
        pol_name_3 = pol_obj.read(self.cursor, self.uid, pol_id_3, ['name'])['name']
        csv_content = "{},Info 1,234\n{},Info 2,213".format(pol_name_2, pol_name_3)
        encoded_csv = base64.b64encode(csv_content)
        vals = {
            'csv_file': encoded_csv,
        }

        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }
        wiz_id = wiz_obj.create(self.cursor, self.uid, vals, context=ctx)

        wiz_obj.create_from_file(self.cursor, self.uid, [wiz_id], context=ctx)

        mock_create.assert_called_with(self.cursor, self.uid, lot_enviament_id, [pol_id_2, pol_id_3],
            {'from_model': 'polissa_id'})
        wiz_info = wiz_obj.read(self.cursor, self.uid, [wiz_id], ['info'])[0]['info']
        self.assertEqual(wiz_info, "Es crearan els enviaments de 2 pòlisses en segon pla")

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_create_enviaments_from_csv__massive_extra_info_with_semicolon(self, mock_create):
        wiz_obj = self.openerp.pool.get('wizard.create.enviaments.from.csv')
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        lot_env_obj = self.openerp.pool.get('som.infoenergia.lot.enviament')
        env_obj = self.openerp.pool.get('som.enviament.massiu')
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0002'
        )[1]
        pol_id_2 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0002'
        )[1]
        pol_id_3 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0003'
        )[1]
        pol_name_2 = pol_obj.read(self.cursor, self.uid, pol_id_2, ['name'])['name']
        pol_name_3 = pol_obj.read(self.cursor, self.uid, pol_id_3, ['name'])['name']
        csv_content = "polissa;extra_info;k\n{};Info 1;234\n{};Info 2;213".format(pol_name_2, pol_name_3)
        encoded_csv = base64.b64encode(csv_content)
        vals = {
            'csv_file': encoded_csv,
        }

        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }
        wiz_id = wiz_obj.create(self.cursor, self.uid, vals, context=ctx)

        wiz_obj.create_from_file(self.cursor, self.uid, [wiz_id], context=ctx)

        mock_create.assert_called_with(self.cursor, self.uid, lot_enviament_id, [pol_id_2, pol_id_3],
            {'from_model': 'polissa_id', 'extra_text': {'0002': {'k': '234', 'extra_info': 'Info 1'},
             '0003': {'k': '213', 'extra_info': 'Info 2'}}})
        wiz_info = wiz_obj.read(self.cursor, self.uid, [wiz_id], ['info'])[0]['info']
        self.assertEqual(wiz_info, "Es crearan els enviaments de 2 pòlisses en segon pla")




class WizardCreateEnviamentsFromPartner(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_wizard_create_enviaments_from_partner(self, mock_add_partners):
        imd_obj = self.openerp.pool.get('ir.model.data')
        cursor = self.cursor
        uid = self.uid
        wiz_obj = self.openerp.pool.get('wizard.add.partners.lot')
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0002'
        )[1]
        partner_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_polissa_soci', 'res_partner_soci'
        )[1]
        vals = {'vat':'ES97053918J'}
        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }
        wiz_id = wiz_obj.create(self.cursor, self.uid, vals, context=ctx)

        wiz_obj.add_partners_lot(self.cursor, self.uid, [wiz_id], context=ctx)

        mock_add_partners.assert_called_with(self.cursor, self.uid, lot_enviament_id, [partner_id],
            {'from_model': 'partner_id'})

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_wizard_create_enviaments_from_partner_esSocia(self, mock_add_partners):
        imd_obj = self.openerp.pool.get('ir.model.data')
        cursor = self.cursor
        uid = self.uid
        wiz_obj = self.openerp.pool.get('wizard.add.partners.lot')
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0002'
        )[1]
        soci_obj = self.openerp.pool.get('somenergia.soci')
        soci_ids = soci_obj.search(self.cursor, self.uid, [('data_baixa_soci','=',False)])
        partner_ids = [ x['partner_id'][0] for x in soci_obj.read(cursor, uid, soci_ids, ['partner_id']) ]
        vals = {'es_soci': True}
        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }
        wiz_id = wiz_obj.create(self.cursor, self.uid, vals, context=ctx)

        wiz_obj.add_partners_lot(self.cursor, self.uid, [wiz_id], context=ctx)

        args, kwargs = mock_add_partners.call_args
        self.assertEqual(args[2], lot_enviament_id)
        self.assertEqual(sorted(args[3]), sorted(partner_ids))
        self.assertEqual(args[4], {'from_model': 'partner_id'})

    @mock.patch('som_infoenergia.som_infoenergia_lot.SomInfoenergiaLotEnviament.create_enviaments_from_object_list')
    def test_wizard_create_enviaments_from_partner_teaportacions(self, mock_add_partners):
        imd_obj = self.openerp.pool.get('ir.model.data')
        cursor = self.cursor
        uid = self.uid
        wiz_obj = self.openerp.pool.get('wizard.add.partners.lot')
        lot_enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_infoenergia', 'lot_enviament_0002'
        )[1]
        gen_obj = self.openerp.pool.get('generationkwh.investment')
        gen_ids = gen_obj.search(self.cursor, self.uid, [('emission_id.type','=','apo')])
        member_ids = [x['member_id'][0] for x in gen_obj.read(self.cursor, self.uid, gen_ids, ['member_id']) ]
        soci_obj = self.openerp.pool.get('somenergia.soci')
        partner_ids = [ x['partner_id'][0] for x in soci_obj.read(cursor, uid, member_ids, ['partner_id']) ]
        vals = {'te_aportacions': True}
        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
        }
        wiz_id = wiz_obj.create(self.cursor, self.uid, vals, context=ctx)

        wiz_obj.add_partners_lot(self.cursor, self.uid, [wiz_id], context=ctx)

        args, kwargs = mock_add_partners.call_args
        self.assertEqual(args[2], lot_enviament_id)
        self.assertEqual(sorted(args[3]), sorted(partner_ids))
        self.assertEqual(args[4], {'from_model': 'partner_id'})