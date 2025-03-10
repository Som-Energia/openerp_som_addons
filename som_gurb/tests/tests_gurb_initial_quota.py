from tests_gurb_base import TestsGurbBase


class TestsGurbInitialQuota(TestsGurbBase):
    def test_gurb_cups_initial_invoice(self):
        context = {}

        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        invoice_o = self.openerp.pool.get("account.invoice")
        pol_o = self.openerp.pool.get("giscedata.polissa")

        references = self.get_references()
        gurb_cups_id = references["owner_gurb_cups_id"]
        self.activar_polissa_CUPS(context={"polissa_xml_id": "polissa_0001"})
        invoice_ids, errors = gurb_cups_o.create_initial_invoices(
            self.cursor, self.uid, gurb_cups_id, context=context
        )
        invoice_id = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id, ["initial_invoice_id"], context=context
        )["initial_invoice_id"][0]

        pol_id = references["owner_pol_id"]
        pol_br = pol_o.browse(self.cursor, self.uid, pol_id, context=context)
        invoice_br = invoice_o.browse(self.cursor, self.uid, invoice_id, context=context)

        iva_21_tax_id = imd_o.get_object_reference(
            self.cursor, self.uid, "l10n_chart_ES", "iva_rep_21"
        )[1]

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(invoice_ids), 1)
        self.assertEqual(invoice_ids[0], invoice_id)
        self.assertEqual(invoice_br.partner_id.id, pol_br.titular.id)
        self.assertEqual(len(invoice_br.invoice_line), 1)
        self.assertEqual(invoice_br.invoice_line[0].quantity, 1)
        self.assertEqual(invoice_br.invoice_line[0].price_unit, 3.75)
        self.assertEqual(invoice_br.invoice_line[0].price_subtotal, 3.75)
        self.assertEqual(len(invoice_br.invoice_line[0].invoice_line_tax_id), 1)
        self.assertEqual(invoice_br.invoice_line[0].invoice_line_tax_id[0].id, iva_21_tax_id)

    def test_gurb_cups_initial_invoice_already_exists(self):
        context = {}

        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")

        references = self.get_references()
        gurb_cups_id = references["owner_gurb_cups_id"]
        self.activar_polissa_CUPS(context={"polissa_xml_id": "polissa_0001"})
        gurb_cups_o.create_initial_invoices(self.cursor, self.uid, gurb_cups_id, context=context)
        invoice_id = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id, ["initial_invoice_id"], context=context
        )["initial_invoice_id"][0]

        gurb_cups_br = gurb_cups_o.browse(self.cursor, self.uid, gurb_cups_id, context=context)

        self.assertEqual(gurb_cups_br.initial_invoice_id.id, invoice_id)

        invoice_ids, errors = gurb_cups_o.create_initial_invoices(
            self.cursor, self.uid, gurb_cups_id, context=context
        )

        self.assertEqual(len(invoice_ids), 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0],
            "[GURB CUPS ID 1]: La factura d'inscripci\xc3\xb3 ja existeix."
        )
