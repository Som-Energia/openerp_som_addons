# -*- coding: utf-8 -*-
from osv import osv, fields
from yamlns import namespace as ns
import pooler
from generationkwh.isodates import isodate
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def investmentAmortization_notificationData_asDict(self, cursor, uid, ids):
        return dict(self.investmentAmortization_notificationData(cursor, uid, ids))

    def investmentAmortization_notificationData(self, cursor, uid, ids):
        def dateFormat(dateIso):
            return isodate(dateIso).strftime("%d/%m/%Y")
        def moneyFormat(amount):
            return "{:,.2f}".format(amount).replace(',','X').replace('.',',').replace('X','.')

        report = ns()
        pool = pooler.get_pool(cursor.dbname)
        Invoice = pool.get('account.invoice')
        Partner = pool.get('res.partner')
        InvoiceLine = pool.get('account.invoice.line')
        Investment = pool.get('generationkwh.investment')
        IrModelData = pool.get('ir.model.data')

        account_id = ids[0]

        if not ids: raise Exception("No invoice provided")

        invoice = Invoice.read(cursor, uid, account_id, [
            'date_invoice',
            'partner_id',
            'name',
            'member_id',
            'invoice_line',
            'amount_total',
            'name',
            'partner_bank',
            'origin',
            'type',
            ])

        if not invoice:
            raise Exception("Invoice {} not found".format(account_id))

        if not invoice['partner_id']:
            raise Exception("No partner related to invoice {}".format(account_id))
        partner = Partner.read(cursor, uid, invoice['partner_id'][0], [
            'vat',
            'name',
        ])

        invoice_line = InvoiceLine.read(cursor, uid, invoice['invoice_line'][0],['note'])
        mutable_information = ns.loads(invoice_line['note'] or '{}')

        date_invoice = datetime.strptime(invoice['date_invoice'], '%Y-%m-%d')
        previous_year = (date_invoice + timedelta(weeks=-52)).year
        investment_id = Investment.search(cursor, uid, [('name','=', invoice['origin'])])
        investment_obj = Investment.read(cursor, uid, investment_id)
        member_id = investment_obj[0]['member_id'][0]

        irpf_values = Investment.get_irpf_amounts(cursor, uid, investment_id[0], member_id, previous_year)
        amort_product_id = IrModelData.get_object_reference(cursor, uid, 'som_generationkwh', 'genkwh_product_amortization')[1]
        amort_value = 0
        for line_id in invoice['invoice_line']:
            line = InvoiceLine.browse(cursor, uid, line_id)
            if line.product_id.id == amort_product_id:
                amort_value += line.price_subtotal

        investment_gkwh_ids = Investment.search(cursor, uid, [
            ('member_id', '=', member_id),
            ('emission_id.type', '=', 'genkwh')
        ])

        report.receiptDate = dateFormat(invoice['date_invoice'])
        # TODO: non spanish vats not covered by tests
        report.ownerNif = partner['vat'][2:] if partner['vat'][:2]=='ES' else partner['vat']
        report.inversionName = mutable_information.investmentName
        report.ownerName = partner['name']
        report.inversionPendingCapital = moneyFormat(float(mutable_information.pendingCapital))
        report.inversionInitialAmount = moneyFormat(mutable_information.investmentInitialAmount)
        report.inversionPurchaseDate = dateFormat(mutable_information.investmentPurchaseDate)
        report.inversionExpirationDate = dateFormat(mutable_information.investmentLastEffectiveDate)
        report.amortizationAmount = moneyFormat(invoice['amount_total'])
        report.amortizationName = invoice['name']
        report.inversionBankAccount = invoice['partner_bank'][1]
        report.amortizationTotalPayments = mutable_information.amortizationTotalNumber
        report.amortizationDate = dateFormat(mutable_information.amortizationDate)
        report.amortizationNumPayment = mutable_information.amortizationNumber
        report.irpfAmount = irpf_values['irpf_amount']
        report.irpfAmountLiqTotal = (-1 * irpf_values['irpf_amount'])
        report.irpfSaving = irpf_values['irpf_saving']
        report.previousYear = previous_year
        report.amortValue = amort_value
        report.amortValueUnsigned = abs(amort_value)
        report.invoiceType = invoice['type']
        # no està ben calculat -> ens basem millor en irpfSaving
        # report.totalAmountSaving = irpf_values['total_amount_saving']
        report.totalGenerationKwh = irpf_values['total_generation_kwh']
        report.totalGenerationAmount = irpf_values['total_generation_amount']
        report.totalAmountNoGeneration = irpf_values['total_amount_no_generation']
        report.totalContractsWithGkWh = irpf_values['total_contracts_with_gkWh']

        report.countInvestmentsGkwh = len(investment_gkwh_ids)
        report.savingActualInvestment = irpf_values['irpf_actual_saving']

        return report

AccountInvoice()
# vim: et ts=4 sw=4
