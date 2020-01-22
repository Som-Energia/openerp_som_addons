# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
import netsvc
import time
import random
from generationkwh.testutils import assertNsEqual
from datetime import datetime, timedelta, date
from yamlns import namespace as ns
import generationkwh.investmentmodel as gkwh

class InvestmentTests(testing.OOTestCase):

    def setUp(self):
        self.MailMockup = self.openerp.pool.get('generationkwh.mailmockup')
        self.PEAccounts = self.openerp.pool.get('poweremail.core_accounts')
        self.Investment = self.openerp.pool.get('generationkwh.investment')
        self.IrModelData = self.openerp.pool.get('ir.model.data')
        self.Partner = self.openerp.pool.get('res.partner')
        self.Invoice = self.openerp.pool.get('account.invoice')
        self.InvoiceLine = self.openerp.pool.get('account.invoice.line')
        self.Emission = self.openerp.pool.get('generationkwh.emission')
        self.maxDiff = None

    def tearDown(self):
        pass

    assertNsEqual=assertNsEqual

    def assertInvoiceInfoEqual(self, cursor, uid, invoice_id, expected):
        def proccesLine(line):
            line = ns(line)
            line.product_id = line.product_id[1]
            line.account_id = line.account_id[1]
            line.uos_id = line.uos_id[1]
            line.note = ns.loads(line.note) if line.note else line.note
            del line.id
            return line

        invoice = ns(self.Invoice.read(cursor, uid, invoice_id, [
            'amount_total',
            'amount_untaxed',
            'partner_id',
            'type',
            'name',
            'number',
            'journal_id',
            'account_id',
            'partner_bank',
            'payment_type',
            'date_invoice',
            'invoice_line',
            'check_total',
            'origin',
            'sii_to_send',
            'mandate_id',
            'state',
        ]))
        invoice.journal_id = invoice.journal_id[1]
        invoice.mandate_id = invoice.mandate_id and invoice.mandate_id[0]
        invoice.partner_bank = invoice.partner_bank[1] if invoice.partner_bank else "None"
        invoice.account_id = invoice.account_id[1]
        invoice.invoice_line = [
            proccesLine(line)
            for line in self.InvoiceLine.read(cursor, uid, invoice.invoice_line, [])
            ]
        self.assertNsEqual(invoice, expected)

    def assertLogEquals(self, log, expected):
        for x in log.splitlines():
            self.assertRegexpMatches(x,
                u'\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}.\\d+ [^]]+\\] .*',
                u"Linia de log con formato no estandard"
            )

        logContent = ''.join(
                x.split('] ')[1]+'\n'
                for x in log.splitlines()
                if u'] ' in x
                )
        self.assertMultiLineEqual(logContent, expected)

    def assertMailLogEqual(self, log, expected):
        self.assertNsEqual(log or '{}', expected)

    def _generationMailAccount(self, cursor, uid):
        return self.PEAccounts.search(cursor, uid, [
           ('name','=','Generation kWh')
            ])[0]

    def _invertirMailAccount(self, cursor, uid):
        return self.PEAccounts.search(cursor, uid, [
           ('email_id','=','invertir@somenergia.coop')
            ])[0]

    def test_mark_as_signed_allOk_GKWH(self):
        """
        Checks if signed_date change
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            inv_0001 = self.Investment.browse(cursor, uid, inv_id)
            self.assertEquals(inv_0001.signed_date, False)

            self.Investment.mark_as_signed(cursor, uid, inv_id, '2017-01-06')

            inv_0001 = self.Investment.browse(cursor, uid, inv_id)
            self.assertEquals(inv_0001.signed_date, '2017-01-06')

    def test_mark_as_signed_allOk_APO(self):
        """
        Checks if signed_date change
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            inv_0001 = self.Investment.browse(cursor, uid, inv_id)
            self.assertEquals(inv_0001.signed_date, False)

            self.Investment.mark_as_signed(cursor, uid, inv_id, '2017-01-06')

            inv_0001 = self.Investment.read(cursor, uid, inv_id)
            inv_0001.pop('actions_log')
            inv_0001.pop('log')
            inv_0001.pop('id')
            id_emission, name_emission = inv_0001.pop('emission_id')
            self.assertEqual(name_emission, "Aportacions")
            self.assertEquals(inv_0001,
                {
                    'first_effective_date': False,
                    'move_line_id': False,
                    'last_effective_date': False,
                    'nshares': 10,
                    'signed_date': '2017-01-06',
                    'draft': True,
                    'purchase_date': False,
                    'member_id': (1, u'Gil, Pere'),
                    'active': True,
                    'order_date': '2019-10-01',
                    'amortized_amount': 0.0,
                    'name': u'APO00001'
                })

    def test_create_from_form_allOk_APO(self):
        """
        Checks if investment aportacio is created
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-06',
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo')

            inv_0001 = self.Investment.read(cursor, uid, inv_id)
            inv_0001.pop('actions_log')
            inv_0001.pop('log')
            inv_0001.pop('id')
            id_emission, name_emission = inv_0001.pop('emission_id')
            self.assertEqual(name_emission, "Aportacions")
            self.assertEquals(inv_0001,
                {
                    'first_effective_date': False,
                    'move_line_id': False,
                    'last_effective_date': False,
                    'nshares': 40,
                    'signed_date': False,
                    'draft': True,
                    'purchase_date': False,
                    'member_id': (1, u'Gil, Pere'),
                    'active': True,
                    'order_date': '2017-01-06',
                    'amortized_amount': 0.0,
                    'name': u'APO005000'
                })
            self.MailMockup.deactivate(cursor, uid)

    def test__create_from_form__whenNotAMember_GKWH(self):
        with self.assertRaises(Exception) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_noinversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_genkwh',
                    )
        self.assertEqual(ctx.exception.message,'Not a member')

    def test__create_from_form__whenNotAMember_APO(self):
        with self.assertRaises(Exception) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_noinversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo',
                    )

        self.assertEqual(ctx.exception.message,'Not a member')

    def test__create_from_form__withNonDivisibleAmount_APO(self):
        with self.assertRaises(Exception) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    4003,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo',
                    )

        self.assertEqual(ctx.exception.message,'Invalid amount')

    def test__create_from_form__withNonDivisibleAmount_GKWH(self):
        with self.assertRaises(Exception) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    4003,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_genkwh',
                    )

        self.assertEqual(ctx.exception.message,'Invalid amount')

    def test__create_from_form__withNegativeAmount_APO(self):
        with self.assertRaises(Exception) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    -400,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo',
                    )

        self.assertEqual(ctx.exception.message,'Invalid amount')

    def test__create_from_form__withNegativeAmount_GKWH(self):
        with self.assertRaises(Exception) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    -400,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_genkwh',
                    )

        self.assertEqual(ctx.exception.message,'Invalid amount')

    def test__create_from_form__withZeroAmount_APO(self):
        with self.assertRaises(Exception) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    0,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo',
                    )

        self.assertEqual(ctx.exception.message,'Invalid amount')

    def test__create_from_form__withZeroAmount_GKWH(self):
        with self.assertRaises(Exception) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    0,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_genkwh',
                    )

        self.assertEqual(ctx.exception.message,'Invalid amount')

    def test__create_from_form__withBadIban_APO(self):
        with self.assertRaises(Exception) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    3000,
                    '10.10.23.123',
                    'ES77123412341612345678ZZ',
                    'emissio_apo',
                    )

        self.assertEqual(ctx.exception.message,'Wrong iban')

    def test__create_from_form__withBadIban_GKWH(self):
        with self.assertRaises(Exception) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    3000,
                    '10.10.23.123',
                    'ES77123412341612345678ZZ',
                    'emissio_gkwh',
                    )

        self.assertEqual(ctx.exception.message,'Wrong iban')

    def test__create_from_form__sendsCreationEmailAPO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-06',
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo')

            self.assertMailLogEqual(self.MailMockup.log(cursor, uid), """\
                logs:
                - model: generationkwh.investment
                  id: {id}
                  template: aportacio_mail_creacio
                  from_id: [ {account_id} ]
                """.format(
                    id=inv_id,
                    account_id = self._invertirMailAccount(cursor, uid),
                ))
            self.MailMockup.deactivate(cursor, uid)

    def test__create_from_form__sendsCreationEmailGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-06',
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_genkwh')

            self.assertMailLogEqual(self.MailMockup.log(cursor, uid), """\
                logs:
                - model: generationkwh.investment
                  id: {id}
                  template: generationkwh_mail_creacio
                  from_id: [ {account_id} ]
                """.format(
                    id=inv_id,
                    account_id = self._generationMailAccount(cursor, uid),
                ))
            self.MailMockup.deactivate(cursor, uid)

    def test__create_from_form__ibanIsSet(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            inv_id = self.Investment.create_from_form(cursor, uid,
                partner_id,
                '2017-01-01', # order_date
                2000,
                '10.10.23.1',
                'ES7712341234161234567890',
            )
            partner = self.Partner.browse(cursor, uid, partner_id)
            self.assertTrue(partner.bank_inversions)

    def test__create_initial_invoices__AllOkGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]
            iban = 'ES7712341234161234567890'
            id = self.Investment.create_from_form(cursor, uid,
                partner_id,
                '2017-01-01', # order_date
                2000,
                '10.10.23.1',
                iban,
                'emissio_genkwh',
                )

            invoice_ids, errs =  self.Investment.create_initial_invoices(cursor, uid, [id])

            self.assertFalse(errs)
            self.assertTrue(invoice_ids)
            investment = self.Investment.browse(cursor, uid, id)
            mandate_id = self.Investment.get_or_create_payment_mandate(cursor, uid,
                partner_id, iban, investment.emission_id.mandate_name, gkwh.creditorCode)
            partner_data = self.Partner.browse(cursor, uid, partner_id)
            self.assertInvoiceInfoEqual(cursor, uid, invoice_ids[0], u"""\
                account_id: 410000{num_soci:0>6s} {p.name}
                amount_total: 2000.0
                amount_untaxed: 2000.0
                check_total: 2000.0
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: 163500{num_soci:0>6s} {p.name}
                  name: 'Inversió {investment_name} '
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'CI: {investment_name}-JUST'
                  origin: false
                  price_unit: 100.0
                  price_subtotal: 2000.0
                  note: false
                  quantity: 20.0
                  product_id: '[GENKWH_AE] Accions Energètiques Generation kWh'
                  invoice_line_tax_id: []
                journal_id: Factures GenerationkWh
                mandate_id: {mandate_id}
                name: {investment_name}-JUST
                number: {investment_name}-JUST
                origin: {investment_name}
                partner_bank: {iban}
                partner_id:
                - {p.id}
                - {p.name}
                payment_type:
                - 2
                - Recibo domiciliado
                sii_to_send: false
                type: out_invoice
                state: draft
                """.format(
                invoice_date=datetime.today().strftime("%Y-%m-%d"),
                id=invoice_ids[0],
                iban='ES77 1234 1234 1612 3456 7890',
                year=2018,
                investment_name=investment.name,
                p=partner_data,
                num_soci= partner_data.ref[1:],
                investment_id=id,
                mandate_id=mandate_id,
                ))

    def test__create_initial_invoices__AllOkAPO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]

            invoice_ids, errs =  self.Investment.create_initial_invoices(cursor, uid, [id])

            self.assertFalse(errs)
            self.assertTrue(invoice_ids)
            investment = self.Investment.browse(cursor, uid, id)
            iban = 'ES7712341234161234567890'
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]
            emission_data = investment.emission_id
            mandate_id = self.Investment.get_or_create_payment_mandate(cursor, uid,
                partner_id, iban, emission_data.mandate_name, gkwh.creditorCode)
            partner_data = self.Partner.browse(cursor, uid, partner_id)
            self.assertInvoiceInfoEqual(cursor, uid, invoice_ids[0], u"""\
                account_id: 410000{num_soci:0>6s} {p.name}
                amount_total: 1000.0
                amount_untaxed: 1000.0
                check_total: 1000.0
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: 163000{num_soci:0>6s} {p.name}
                  name: 'Inversió {investment_name} '
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'CI: {investment_name}-JUST'
                  origin: false
                  price_unit: 100.0
                  price_subtotal: 1000.0
                  note: false
                  quantity: 10.0
                  product_id: '[APO_AE] Aportacions'
                  invoice_line_tax_id: []
                journal_id: Factures Liquidació Aportacions
                mandate_id: {mandate_id}
                name: {investment_name}-JUST
                number: {investment_name}-JUST
                origin: {investment_name}
                partner_bank: {iban}
                partner_id:
                - {p.id}
                - {p.name}
                payment_type:
                - 2
                - Recibo domiciliado
                sii_to_send: false
                type: out_invoice
                state: draft
                """.format(
                invoice_date=datetime.today().strftime("%Y-%m-%d"),
                id=invoice_ids[0],
                iban='ES77 1234 1234 1612 3456 7890',
                year=2018,
                investment_name=investment.name,
                p=partner_data,
                num_soci= partner_data.ref[1:],
                investment_id=id,
                mandate_id=mandate_id,
                ))

# vim: et ts=4 sw=4
