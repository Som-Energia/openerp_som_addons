
from tests_gurb_base import TestsGurbBase


class TestsGurbInitialQuota(TestsGurbBase):
    def test_gurb_cups_percentage(self):
        context = {}
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        self.openerp.pool.get("account.invoice")

        references = self.get_references()
        gurb_cups_id = references["gurb_cups_id"]

        gurb_cups_o.create_initial_invoices(self.cursor, self.uid, gurb_cups_id, context=context)

        gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id, ["invoice_reference"], context=context
        )['invoice_reference'][1]

        # invoice_br = account_invoice_o.browse(self.cursor, self.uid, invoice_id, context=context)
        # read_vals = [
        #     "partner_id",
        #     "invoice_lines",
        #     "account_id",
        #     "address_invoice_id",
        #     "journal_id",
        #     "reference_type",
        # ]
