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
        env_ids = env_obj.search(cursor, uid, [('lot_enviament','=', lot_enviament_id)])
        wiz_obj = self.openerp.pool.get('wizard.infoenergia.send.reports')
        ctx = {
            'active_id': lot_enviament_id, 'active_ids': [lot_enviament_id],
            'from_model':'som.infoenergia.lot.enviament'
        }

        wiz_id = wiz_obj.create(cursor, uid, {},context=ctx)
        wiz_obj.send_reports(cursor, uid, [wiz_id], context=ctx)
        mocked_send_reports.assert_called_with(cursor, uid, env_ids, context={'allow_reenviar':False})

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

        env_ids = env_obj.search(cursor, uid, [('lot_enviament','=', lot_enviament_id)])
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


class WizardCancelFromCSVTests(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

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