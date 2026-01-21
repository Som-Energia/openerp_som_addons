#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

dbconfig = None
try:
    import dbconfig
except ImportError:
    pass
from datetime import date
from yamlns import namespace as ns
import erppeek_wst
import generationkwh.investmentmodel as gkwh
from generationkwh.testutils import assertNsEqual


@unittest.skipIf(not dbconfig, "depends on ERP")
class Account_Invoice_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Investment = self.erp.GenerationkwhInvestment
        self.Invoice = self.erp.AccountInvoice
        self.MailMockup = self.erp.GenerationkwhMailmockup
        self.currentYear = str(date.today().year)
        self.Investment.dropAll()
        self.MailMockup.activate()

    def tearDown(self):
        self.MailMockup.deactivate()
        self.erp.rollback()
        self.erp.close()

    assertNsEqual=assertNsEqual

    def test__get_investment__found(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        #create invoice
        invoice_ids, errs = self.Investment.create_initial_invoices([investment_id])

        investment_from_invoice = self.Invoice.get_investment(invoice_ids[0])

        self.assertEqual(investment_id, investment_from_invoice)

    def test__get_investment__otherJournalsIgnored(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        #create invoice
        invoice_ids,errs = self.Investment.create_initial_invoices([investment_id])
        invoice = self.Invoice.write(invoice_ids[0], dict(
            journal_id = 2 # random
            ))
        investment_from_invoice = self.Invoice.get_investment(invoice_ids[0])

        self.assertFalse(investment_from_invoice)

    def test__get_investment__notFound(self):
        invoice_id = 23132 # random
        investment_id = self.Invoice.get_investment(invoice_id)
        self.assertFalse(investment_id)

    def test__is_investment_payment_invoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        #create invoice
        invoice_ids,errs = self.Investment.create_initial_invoices([investment_id])

        self.assertTrue(self.Invoice.is_investment_payment(invoice_ids[0]))

    def test__is_investment_payment_null_invoice(self):
        invoice_id = 999999999 # does not exists
        self.assertFalse(self.Invoice.is_investment_payment(invoice_id))

    def test__is_investment_payment_unamed_invoice(self):
        invoice_id = 325569 # name null
        self.assertFalse(self.Invoice.is_investment_payment(invoice_id))

    def test__is_investment_payment_amortization_invoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2014-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        #create invoice
        self.Investment.mark_as_invoiced(investment_id)
        self.Investment.mark_as_paid([investment_id], '2014-01-01')
        amortinv_ids,errs = self.Investment.amortize('2017-01-02',[investment_id])
        self.assertFalse(self.Invoice.is_investment_payment(amortinv_ids[0]))

    def test__paymentWizard(self):

        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            self.currentYear + '-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        invoice_ids, errors = self.Investment.create_initial_invoices([investment_id])
        self.Investment.open_invoices(invoice_ids)

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(
            invoice_ids[0], 'movement description')

        invoice = self.Invoice.read(invoice_ids[0], ['residual'])
        self.assertEqual(invoice['residual'], 0.0)

    def test__paymentWizard__unpay(self):

        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.121',
            'ES7712341234161234567890',
        )
        invoice_ids, errors = self.Investment.create_initial_invoices([investment_id])
        self.Investment.open_invoices(invoice_ids)
        self.Investment.invoices_to_payment_order(invoice_ids, gkwh.investmentPaymentMode)
        self.erp.GenerationkwhPaymentWizardTesthelper.pay(invoice_ids[0], 'a payment')

        self.erp.GenerationkwhPaymentWizardTesthelper.unpay(invoice_ids[0], 'an unpayment')

        invoice = self.Invoice.read(invoice_ids[0], ['residual'])
        self.assertEqual(invoice['residual'], 1000.0)

    def test__accounting__openInvestmentInvoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
 
        invoice_ids, errors = self.Investment.investment_payment([investment_id])

        investment_name = self.Investment.read(investment_id,['name'])['name']

        self.assertAccountingByInvoice(invoice_ids[0], u"""
        movelines:
        - account_id: 163500000000 {surname}, {name}
          amount_to_pay: 4000.0
          credit: 4000.0
          debit: 0.0
          invoice: 'CI: {investment_name}-JUST'
          journal_id: Factures GenerationkWh
          name: 'Inversió {investment_name} '
          payment_type: Recibo domiciliado
          product_id: '[GENKWH_AE] Accions Energètiques Generation kWh'
          quantity: 40.0
          ref: {investment_name}-JUST
          move_state: posted
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: -4000.0
          credit: 0.0
          debit: 4000.0
          invoice: 'CI: {investment_name}-JUST'
          journal_id: Factures GenerationkWh
          name: {investment_name}-JUST
          payment_type: Recibo domiciliado
          product_id: false
          quantity: 1.0
          ref: {investment_name}-JUST
          move_state: posted
        """.format(
            investment_name = investment_name,
            **self.personalData
        ))

    def test__accounting__paidInvestmentInvoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        invoice_ids, errors = self.Investment.investment_payment([investment_id])

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(
            invoice_ids[0], 'payment movement')

        investment_name = self.Investment.read(investment_id,['name'])['name']
        self.assertAccountingByInvoice(invoice_ids[0], u"""
        movelines:
        # Open
        - account_id: 163500000000 {surname}, {name}
          amount_to_pay: 4000.0
          credit: 4000.0
          debit: 0.0
          invoice: 'CI: {investment_name}-JUST'
          journal_id: Factures GenerationkWh
          name: 'Inversió {investment_name} '
          payment_type: Recibo domiciliado
          product_id: '[GENKWH_AE] Accions Energètiques Generation kWh'
          quantity: 40.0
          ref: {investment_name}-JUST
          move_state: posted
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: 0.0 # TURNED ZERO
          credit: 0.0
          debit: 4000.0
          invoice: 'CI: {investment_name}-JUST'
          journal_id: Factures GenerationkWh
          name: {investment_name}-JUST
          payment_type: Recibo domiciliado
          product_id: false
          quantity: 1.0
          ref: {investment_name}-JUST
          move_state: posted
        # Pay
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: 0.0
          credit: 4000.0
          debit: 0.0
          invoice: false
          journal_id: Factures GenerationkWh
          name: payment movement
          payment_type: []
          product_id: false
          quantity: false
          ref: {investment_name}-JUST
          move_state: posted
        - account_id: 555000000004 CAIXA GKWH
          amount_to_pay: -4000.0
          credit: 0.0
          debit: 4000.0
          invoice: false
          journal_id: Factures GenerationkWh
          name: payment movement
          payment_type: []
          product_id: false
          quantity: false
          ref: {investment_name}-JUST
          move_state: posted
        """.format(
            investment_name = investment_name,
            **self.personalData
        ))

    def test__accounting__unpaidInvestmentInvoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        invoice_ids, errors = self.Investment.investment_payment([investment_id])

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(
            invoice_ids[0], 'a payment')

        self.erp.GenerationkwhPaymentWizardTesthelper.unpay(
            invoice_ids[0], 'an unpayment')

        investment_name = self.Investment.read(investment_id,['name'])['name']
        self.assertAccountingByInvoice(invoice_ids[0], u"""
        movelines:
        # Open
        - account_id: 163500000000 {surname}, {name}
          amount_to_pay: 4000.0
          credit: 4000.0
          debit: 0.0
          invoice: 'CI: {investment_name}-JUST'
          journal_id: Factures GenerationkWh
          name: 'Inversió {investment_name} '
          payment_type: Recibo domiciliado
          product_id: '[GENKWH_AE] Accions Energètiques Generation kWh'
          quantity: 40.0
          ref: {investment_name}-JUST
          move_state: posted
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: -4000.0 # CHANGED, Not zero anymore
          credit: 0.0
          debit: 4000.0
          invoice: 'CI: {investment_name}-JUST'
          journal_id: Factures GenerationkWh
          name: {investment_name}-JUST
          payment_type: Recibo domiciliado
          product_id: false
          quantity: 1.0
          ref: {investment_name}-JUST
          move_state: posted
        # Pay
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: -4000.0 # CHANGED, Not zero anymore
          credit: 4000.0
          debit: 0.0
          invoice: false
          journal_id: Factures GenerationkWh
          name: a payment
          payment_type: []
          product_id: false
          quantity: false
          ref: {investment_name}-JUST
          move_state: posted
        - account_id: 555000000004 CAIXA GKWH
          amount_to_pay: -4000.0 # CHANGED, Not zero anymore
          credit: 0.0
          debit: 4000.0
          invoice: false
          journal_id: Factures GenerationkWh
          name: a payment
          payment_type: []
          product_id: false
          quantity: false
          ref: {investment_name}-JUST
          move_state: posted
        # Unpay
        - account_id: 555000000004 CAIXA GKWH
          amount_to_pay: 4000.0
          credit: 4000.0
          debit: 0.0
          invoice: false
          journal_id: Factures GenerationkWh
          name: an unpayment
          payment_type: []
          product_id: false
          quantity: false
          ref: {investment_name}-JUST
          move_state: posted
        - account_id: 4100{nsoci:>08} {surname}, {name}
          amount_to_pay: -4000.0
          credit: 0.0
          debit: 4000.0
          invoice: false
          journal_id: Factures GenerationkWh
          name: an unpayment
          payment_type: []
          product_id: false
          quantity: false
          ref: {investment_name}-JUST
          move_state: posted
        """.format(
            investment_name = investment_name,
            **self.personalData
        ))

    def test_invoiceState_paidInvestmentInvoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            self.currentYear + '-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        invoice_ids, errors = self.Investment.investment_payment([investment_id])

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(
            invoice_ids[0], 'movement description')

        invoice_state = self.Invoice.read(invoice_ids[0],['state'])
        invoicens = ns(
                state = invoice_state['state'])
        self.assertNsEqual(invoicens, """
            state: paid""")

    def test_invoiceState_paidAmortizationInvoice(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2000-01-03')
        amortization_ids, errors = self.Investment.amortize(
            '2003-01-02', [id])

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(
            amortization_ids[0], 'amortize movement')

        invoice_state = self.Invoice.read(amortization_ids[0],['state'])
        invoicens = ns(
                state = invoice_state['state'])
        self.assertNsEqual(invoicens, """
            state: paid""")

    @unittest.skip("Not implemented")
    def _test__accounting__unpaidInvestmentInvoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        invoice_ids, errors = self.Investment.investment_payment([investment_id])

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(
            invoice_ids[0], 'movement description')

        self.erp.GenerationkwhUnpaymentWizardTesthelper.unpay(invoice_ids)

        investment_name = self.Investment.read(investment_id,['name'])['name']
        self.assertAccountingByInvoice(invoice_ids[0], """
        """.format(
            investment_name = investment_name,
            **self.personalData
        ))

    def test__accounting__openAmortizationInvoice__withoutIRPF(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
 
        self.Investment.mark_as_invoiced(investment_id)
        self.Investment.mark_as_paid([investment_id], '2017-01-02')
        amortization_ids, errors = self.Investment.amortize(
            '2019-01-02', [investment_id])

        investment_name = self.Investment.read(investment_id,['name'])['name']

        self.assertAccountingByInvoice(amortization_ids[0], u"""
        movelines:
        - account_id: 163500000000 {surname}, {name}
          amount_to_pay: -160.0
          credit: 0.0
          debit: 160.0
          invoice: 'SI: {investment_name}'
          journal_id: Factures GenerationkWh
          name: 'Amortització fins a 02/01/2019 de {investment_name} '
          payment_type: Transferencia
          product_id: '[GENKWH_AMOR] Amortització Generation kWh'
          quantity: 1.0
          ref: {investment_name}-AMOR2019
          move_state: posted
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: 160.0
          credit: 160.0
          debit: 0.0
          invoice: 'SI: {investment_name}'
          journal_id: Factures GenerationkWh
          name: {investment_name}-AMOR2019
          payment_type: Transferencia
          product_id: false
          quantity: 1.0
          ref: {investment_name}-AMOR2019
          move_state: posted
        """.format(
            investment_name = investment_name,
            **self.personalData
        ))

    def test__accounting__paidAmortizationInvoice(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
 
        self.Investment.mark_as_invoiced(investment_id)
        self.Investment.mark_as_paid([investment_id], '2017-01-02')
        amortization_ids, errors = self.Investment.amortize(
            '2019-01-02', [investment_id])

        investment_name = self.Investment.read(investment_id,['name'])['name']

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(
            amortization_ids[0], 'movement description')

        self.assertAccountingByInvoice(amortization_ids[0], u"""
        movelines:
        - account_id: 163500000000 {surname}, {name}
          amount_to_pay: -160.0
          credit: 0.0
          debit: 160.0
          invoice: 'SI: {investment_name}'
          journal_id: Factures GenerationkWh
          name: 'Amortització fins a 02/01/2019 de {investment_name} '
          payment_type: Transferencia
          product_id: '[GENKWH_AMOR] Amortització Generation kWh'
          quantity: 1.0
          ref: {investment_name}-AMOR2019
          move_state: posted
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: 0.0 # CHANGED!!
          credit: 160.0
          debit: 0.0
          invoice: 'SI: {investment_name}'
          journal_id: Factures GenerationkWh
          name: {investment_name}-AMOR2019
          payment_type: Transferencia
          product_id: false
          quantity: 1.0
          ref: {investment_name}-AMOR2019
          move_state: posted
        - account_id: 4100000{nsoci:>05} {surname}, {name}
          amount_to_pay: 0.0
          credit: 0.0
          debit: 160.0
          invoice: false
          journal_id: Factures GenerationkWh
          name: movement description
          payment_type: []
          product_id: false
          quantity: false
          ref: {investment_name}-AMOR2019
          move_state: posted
        - account_id: 555000000004 CAIXA GKWH
          amount_to_pay: 160.0
          credit: 160.0
          debit: 0.0
          invoice: false
          journal_id: Factures GenerationkWh
          name: movement description
          payment_type: []
          product_id: false
          quantity: false
          ref: {investment_name}-AMOR2019
          move_state: posted
        """.format(
            investment_name = investment_name,
            **self.personalData
        ))

    def assertAccountingByInvoice(self, invoice_id, expected):
        invoice = self.Invoice.read(invoice_id, [
            'name',
            'journal_id',
        ])

        result = self.movelines([
            ('journal_id','=',invoice['journal_id'][0]),
            ('ref','=',invoice.get('name','caca')),
        ])
        self.assertNsEqual(result, expected)


    def movelines(self, conditions):
        fields = [
            "account_id",
            "amount_to_pay",
            "invoice",
            "journal_id",
            "debit",
            "name",
            "credit",
            "payment_type",
            "product_id",
            "quantity",
            "ref",
            "move_id",
            ]
        fks = [
            "invoice",
            "journal_id",
            "account_id",
            "product_id",
            "payment_type",
            ]
        line_ids = self.erp.AccountMoveLine.search(conditions)
        result = ns(movelines=[])
        movelines = result.movelines
        lines = self.erp.AccountMoveLine.read(
            sorted(line_ids),fields,order='id')
        for line in lines:
            moveline = ns(sorted(line.items()))
            del moveline.id
            move = self.erp.AccountMove.read(moveline.move_id[0], ['state'])
            moveline.move_state = move['state']
            del moveline.move_id
            for field in fks:
                moveline[field]=moveline[field] and moveline[field][1]
            movelines.append(moveline)
        return result



    def test__investment_last_moveline__paid(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        invoice_ids, errors = self.Investment.investment_payment([investment_id])

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(
            invoice_ids[0], 'payment 1')

        ml_id = self.Invoice.investment_last_moveline(invoice_ids[0])
        self.assertMoveLineEqual(ml_id, """
            id: {id}
            name: payment 1
            credit: 4000.0
            debit: 0.0
            """.format(id=ml_id))


    def test__investment_last_moveline__unpaid(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        invoice_ids, errors = self.Investment.investment_payment([investment_id])

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(
            invoice_ids[0], 'payment 1')

        self.erp.GenerationkwhPaymentWizardTesthelper.unpay(
            invoice_ids[0], 'unpayment 1')

        ml_id = self.Invoice.investment_last_moveline(invoice_ids[0])
        self.assertMoveLineEqual(ml_id, """
            id: {id}
            name: unpayment 1
            debit: 4000.0
            credit: 0.0
            """.format(id=ml_id))

    def test__investment_last_moveline__repaid(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        invoice_ids, errors = self.Investment.investment_payment([investment_id])

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(
            invoice_ids[0], 'payment 1')

        self.erp.GenerationkwhPaymentWizardTesthelper.unpay(
            invoice_ids[0], 'unpayment 1')

        self.erp.GenerationkwhPaymentWizardTesthelper.pay(
            invoice_ids[0], 'payment 2')

        ml_id = self.Invoice.investment_last_moveline(invoice_ids[0])
        self.assertMoveLineEqual(ml_id, """
            id: {id}
            name: payment 2
            credit: 4000.0
            debit: 0.0
            """.format(id=ml_id))


    def assertMoveLineEqual(self, ml_id, expected):
        self.assertNsEqual(self.erp.AccountMoveLine.read(ml_id, [
            'name',
            'debit',
            'credit',
            ]), expected)




unittest.TestCase.__str__ = unittest.TestCase.id

if __name__=='__main__':
    unittest.main()

# vim: et ts=4 sw=4
