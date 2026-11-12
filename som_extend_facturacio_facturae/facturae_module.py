# -*- encoding: utf-8 -*-

from osv import osv
from facturae import facturae


class AccountInvoiceFacturae(osv.osv):

    _name = "account.invoice.facturae"
    _inherit = "account.invoice.facturae"

    def facturae_issue_data(self, cursor, uid, invoice, context=None):
        issuedata = super(AccountInvoiceFacturae, self).facturae_issue_data(
            cursor, uid, invoice, context=context
        )

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        fact_ids = fact_obj.search(cursor, uid, [("invoice_id", "=", invoice.id)])
        if fact_ids:
            factura = fact_obj.read(cursor, uid, fact_ids[0], ["data_inici", "data_final"])
            invoicing_period = facturae.InvoicingPeriod()
            invoicing_period.feed(
                {
                    "startdate": factura["data_inici"],
                    "enddate": factura["data_final"],
                }
            )

            issuedata.feed(
                {
                    "invoicingperiod": invoicing_period,
                }
            )

        return issuedata


AccountInvoiceFacturae()
