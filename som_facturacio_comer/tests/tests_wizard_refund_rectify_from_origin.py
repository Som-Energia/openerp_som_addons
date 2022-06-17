# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
import mock
from datetime import datetime, timedelta
from .. import wizard

class TestRefundRectifyFromOrigin(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def test_refund_rectify_by_origin_notInInvoice(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get('giscedata.facturacio.factura')
        wiz_obj = self.pool.get('wizard.refund.rectify.from.origin')
        imd_obj = self.pool.get('ir.model.data')

        fact_cli_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'factura_0001'
        )[1]
        ctx = {'active_id': fact_cli_id, 'active_ids': [fact_cli_id]}

        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)

        wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        self.assertTrue("no es de tipus in_invoice, no s\'actua" in wiz.info)

    def test_refund_rectify_by_origin_notEnforceFromAccount(self):
        cursor = self.cursor
        uid = self.uid

        temp_obj = self.pool.get('poweremail.templates')
        wiz_obj = self.pool.get('wizard.refund.rectify.from.origin')
        imd_obj = self.pool.get('ir.model.data')

        temp_id = temp_obj.search(cursor, uid, [], limit=1)[0]
        temp_obj.write(cursor, uid, temp_id, {'enforce_from_account': False})
        ctx = {}

        wiz_id = wiz_obj.create(cursor, uid, {'send_mail': True, 'email_template': temp_id}, context=ctx)

        with self.assertRaises(Exception) as e:
            wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)
        self.assertEqual(e.exception.message, "warning -- Error\n\nLa plantilla no té indicat el compte des del qual enviar")

    def test_refund_rectify_by_origin_notPaymentOrder(self):
        cursor = self.cursor
        uid = self.uid

        wiz_obj = self.pool.get('wizard.refund.rectify.from.origin')
        imd_obj = self.pool.get('ir.model.data')

        ctx = {}

        wiz_id = wiz_obj.create(cursor, uid, {'open_invoices': True}, context=ctx)

        with self.assertRaises(Exception) as e:
            wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)
        self.assertEqual(e.exception.message, "warning -- Error\n\nPer remesar les factures a pagar cal una ordre de pagament")


    def test_refund_rectify_by_origin_nothingToRefundOneDraft(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get('giscedata.facturacio.factura')
        wiz_obj = self.pool.get('wizard.refund.rectify.from.origin')
        imd_obj = self.pool.get('ir.model.data')

        fact_prov_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'factura_0003'
        )[1]
        fact_info = fact_obj.read(cursor, uid, fact_prov_id, ['origin', 'polissa_id', 'data_inici', 'data_final'])
        f_cli_ids = fact_obj.search(cursor, uid, [
            ('data_inici','<', fact_info['data_final']), ('data_final','>', fact_info['data_inici']), ('type','=','out_invoice')
        ])
        self.assertEqual(fact_obj.read(cursor, uid, f_cli_ids[0], ['state'])['state'], 'draft')
        ctx = {'active_id': fact_prov_id, 'active_ids': [fact_prov_id]}

        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)

        wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)

        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        self.assertEqual(
            "Pòlissa {0} per factura amb origen {1}: S'han eliminat 1 factures en esborrany"
            "\nLa factura amb origen {1} no té res per abonar i rectificar, no s'actua".format(fact_info['polissa_id'][1],fact_info['origin']),
            wiz.info
        )

    @mock.patch.object(wizard.wizard_refund_rectify_from_origin.WizardRefundRectifyFromOrigin,"refund_rectify_if_needed")
    @mock.patch.object(wizard.wizard_refund_rectify_from_origin.WizardRefundRectifyFromOrigin,"recarregar_lectures_between_dates")
    def test_refund_rectify_by_origin_refundOne(self, mock_lectures, mock_refund):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get('giscedata.facturacio.factura')
        wiz_obj = self.pool.get('wizard.refund.rectify.from.origin')
        imd_obj = self.pool.get('ir.model.data')

        fact_prov_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'factura_0003'
        )[1]
        fact_info = fact_obj.read(cursor, uid, fact_prov_id, ['origin', 'polissa_id', 'data_inici', 'data_final'])
        f_cli_ids = fact_obj.search(cursor, uid, [
            ('data_inici','<', fact_info['data_final']), ('data_final','>', fact_info['data_inici']), ('type','=','out_invoice')
        ])
        self.assertEqual(len(f_cli_ids), 1)
        fact_obj.write(cursor, uid, f_cli_ids[0], {'state':'open'})

        ctx = {'active_id': fact_prov_id, 'active_ids': [fact_prov_id]}

        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)
        mock_lectures.side_effect = lambda *x: 3
        mock_refund.side_effect = lambda *x: [[5],'']

        wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)
        mock_lectures.assert_called_with(cursor, uid, [wiz_id], fact_info['polissa_id'][0], fact_info['data_inici'], fact_info['data_final'], ctx)
        mock_refund.assert_called_with(cursor, uid, [wiz_id], f_cli_ids, ctx)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        self.assertEqual(wiz.info, "S'han esborrat 3 lectures de la pòlissa {} i s'han generat 1 factures".format(fact_info['polissa_id'][1]))

    @mock.patch.object(wizard.wizard_refund_rectify_from_origin.WizardRefundRectifyFromOrigin,"recarregar_lectures_between_dates")
    def test_refund_rectify_by_origin_noLectures(self, mock_lectures):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get('giscedata.facturacio.factura')
        wiz_obj = self.pool.get('wizard.refund.rectify.from.origin')
        imd_obj = self.pool.get('ir.model.data')

        fact_prov_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'factura_0003'
        )[1]
        fact_info = fact_obj.read(cursor, uid, fact_prov_id, ['origin', 'polissa_id', 'data_inici', 'data_final'])
        f_cli_ids = fact_obj.search(cursor, uid, [
            ('data_inici','<', fact_info['data_final']), ('data_final','>', fact_info['data_inici']), ('type','=','out_invoice')
        ])
        self.assertEqual(len(f_cli_ids), 1)
        fact_obj.write(cursor, uid, f_cli_ids[0], {'state':'open'})

        ctx = {'active_id': fact_prov_id, 'active_ids': [fact_prov_id]}

        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)
        mock_lectures.side_effect = lambda *x: 0

        wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)
        mock_lectures.assert_called_with(cursor, uid, [wiz_id], fact_info['polissa_id'][0], fact_info['data_inici'], fact_info['data_final'], ctx)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        self.assertEqual(wiz.info, "La pòlissa {}, que té la factura amb origen {}, "
            "no té lectures per esborrar. No s'hi actua.".format(fact_info['polissa_id'][1], fact_info['origin']))

    def test_get_factures_client_by_dates_toRefundOne(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get('giscedata.facturacio.factura')
        wiz_obj = self.pool.get('wizard.refund.rectify.from.origin')
        imd_obj = self.pool.get('ir.model.data')

        fact_prov_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'factura_0003'
        )[1]
        fact_info = fact_obj.read(cursor, uid, fact_prov_id, ['origin', 'polissa_id', 'data_inici', 'data_final'])
        f_cli_ids = fact_obj.search(cursor, uid, [
            ('data_inici','<', fact_info['data_final']), ('data_final','>', fact_info['data_inici']), ('type','=','out_invoice')
        ])
        self.assertEqual(len(f_cli_ids), 1)
        fact_obj.write(cursor, uid, f_cli_ids[0], {'state':'open'})
        ctx = {'active_id': fact_prov_id, 'active_ids': [fact_prov_id]}

        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)

        result = wiz_obj.get_factures_client_by_dates(
            cursor, uid, wiz_id, fact_info['polissa_id'][0], fact_info['data_inici'], fact_info['data_final'], context=ctx
        )
        self.assertEqual(result[0], f_cli_ids)

    def test_get_factures_client_by_dates_toRefundTwo(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get('giscedata.facturacio.factura')
        wiz_obj = self.pool.get('wizard.refund.rectify.from.origin')
        imd_obj = self.pool.get('ir.model.data')

        fact_prov_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'factura_0003'
        )[1]
        fact_info = fact_obj.read(cursor, uid, fact_prov_id, ['origin', 'polissa_id', 'data_inici', 'data_final'])
        f_cli_ids = fact_obj.search(cursor, uid, [('type','=','out_invoice')])
        first_inici = datetime.strptime(fact_info['data_inici'],'%Y-%m-%d') - timedelta(days=2)
        first_final = first_inici + timedelta(days=7)
        second_inici =  first_final + timedelta(days=1)
        fact_obj.write(cursor, uid, f_cli_ids[0], {
            'polissa_id': fact_info['polissa_id'][0], 'data_inici': first_inici.strftime('%Y-%m-%d'),
            'data_final': first_final.strftime('%Y-%m-%d'), 'state': 'open'
        })
        fact_obj.write(cursor, uid, f_cli_ids[1], {
            'polissa_id':fact_info['polissa_id'][0], 'data_inici': second_inici.strftime('%Y-%m-%d'),
            'data_final': fact_info['data_final'], 'state': 'open'
        })

        fact_obj.write(cursor, uid, f_cli_ids[0], {'state':'open'})
        ctx = {'active_id': fact_prov_id, 'active_ids': [fact_prov_id]}

        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)

        result = wiz_obj.get_factures_client_by_dates(
            cursor, uid, wiz_id, fact_info['polissa_id'][0], fact_info['data_inici'], fact_info['data_final'], context=ctx
        )
        self.assertEqual(sorted(result[0]), sorted(f_cli_ids[:2]))

    def test_dummy(self):
        self.assertEqual(1,1)
