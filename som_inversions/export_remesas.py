# -*- coding: utf-8 -*-
import pooler
import base64
import netsvc
import copy
from tools.translate import _
from osv import osv

from l10n_ES_remesas.wizard.export_remesas import FakeInvoice
from l10n_ES_remesas.wizard.export_remesas import NoInvoiceException
from datetime import datetime


class WizardExportPaymentFile(osv.osv_memory):

    _name = "wizard.payment.file.spain"
    _inherit = "wizard.payment.file.spain"

    def get_investment_fake_invoice(self, cursor, uid, line, context=None):
        """
        Gets Fake invoice for investment line
        :param line: payment.line instance
        :return: FakeInvoice object
        :raises: NoInvoiceException when invoice can not be found
        """
        try:
            invoice = line.ml_inv_ref
            if not line.ml_inv_ref:
                # This is an investment
                # fake invoice to create a SEPA file
                mandate_obj = self.pool.get("payment.mandate")
                mandate_search = [
                    ("notes", "=", line.communication),
                    ("debtor_iban", "=", line.bank_id.iban),
                ]
                m_ids = mandate_obj.search(cursor, uid, mandate_search)
                if m_ids:
                    mandate = mandate_obj.browse(cursor, uid, m_ids[0])
                    date_invoice = datetime.strptime(line.create_date, "%Y-%m-%d %H:%M:%S")

                    f_invoice = FakeInvoice(
                        mandate,
                        date_invoice.date(),
                        line.name,
                        line.name,
                        line.order_id.user_id.company_id,
                    )
                    invoice = copy.copy(f_invoice)

            return invoice
        except Exception, e:
            raise NoInvoiceException(e, line_id=line.id)

    def get_invoice(self, cursor, uid, line, context=None):
        """
        Handles payment lines of investments
        :param line: payment.line instance or id
        :return: Invoice object. May be an "account.invoice" instance or a
        FakeInvoice
        :raises: NoInvoiceException when invoice can not be found
        """
        try:
            return super(WizardExportPaymentFile, self).get_invoice(
                cursor, uid, line, context=context
            )
        except NoInvoiceException, e:
            line_obj = self.pool.get("payment.line")
            if isinstance(line, (int, long)):
                pline = line_obj.browse(cursor, uid, line, context=context)
            else:
                pline = line
            return self.get_investment_fake_invoice(cursor, uid, pline, context=None)


WizardExportPaymentFile()
