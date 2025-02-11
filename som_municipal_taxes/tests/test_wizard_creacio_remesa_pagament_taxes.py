# -*- coding: utf-8 -*-
import datetime
from destral import testing
from osv.osv import except_osv
import mock

from som_municipal_taxes.wizard.wizard_creacio_remesa_pagament_taxes import get_dates_from_quarter
from giscedata_facturacio.facturacio_extra import FacturacioExtra


class TestWizardCreacioRemesaPagamentTaxes(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestWizardCreacioRemesaPagamentTaxes, self).setUp()
        self.pool = self.openerp.pool

    @mock.patch.object(FacturacioExtra, "get_states_invoiced")
    def test_create_remesa_pagaments__ok(self, get_states_invoiced_mock):
        get_states_invoiced_mock.return_value = ['draft', 'open', 'paid']
        wiz_o = self.pool.get("wizard.creacio.remesa.pagament.taxes")
        order_o = self.pool.get("payment.order")

        payment_mode_id = self.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "account_invoice_som", "payment_mode_0001"
        )[1]
        wiz_init = {
            "account": 7,
            "payment_mode": payment_mode_id,
            "year": 2016,
            "quarter": 1,
        }
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={},
        )
        order_id = wiz_o.create_remesa_pagaments(
            self.cursor,
            self.uid,
            [wiz_id],
            {},
        )

        state = wiz_o.read(self.cursor, self.uid, wiz_id, ['state'])[0]['state']
        self.assertEqual(state, 'done')
        po = order_o.browse(self.cursor, self.uid, order_id)
        self.assertEqual(len(po.line_ids), 1)

    @mock.patch.object(FacturacioExtra, "get_states_invoiced")
    def test_create_remesa_pagaments__error_ja_pagat(self, get_states_invoiced_mock):
        get_states_invoiced_mock.return_value = ['draft', 'open', 'paid']
        wiz_o = self.pool.get("wizard.creacio.remesa.pagament.taxes")
        payment_mode_id = self.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "account_invoice_som", "payment_mode_0001"
        )[1]
        wiz_init = {
            "account": 7,
            "payment_mode": payment_mode_id,
            "year": 2016,
            "quarter": 1,
        }
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={},
        )
        wiz_o.create_remesa_pagaments(
            self.cursor,
            self.uid,
            [wiz_id],
            {},
        )

        with self.assertRaises(except_osv) as validate_error:
            wiz_id = wiz_o.create(
                self.cursor,
                self.uid,
                wiz_init,
                context={},
            )
            wiz_o.create_remesa_pagaments(
                self.cursor,
                self.uid,
                [wiz_id],
                {},
            )
            self.assertIn("Ja s'ha pagat el trimestre", validate_error.exception.message)

    @mock.patch.object(FacturacioExtra, "get_states_invoiced")
    def test__crear_factures__ok(self, get_states_invoiced_mock):
        get_states_invoiced_mock.return_value = ['draft', 'open', 'paid']
        wiz_o = self.pool.get("wizard.creacio.remesa.pagament.taxes")
        order_o = self.pool.get("payment.order")
        payment_mode_id = self.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "account_invoice_som", "payment_mode_0001"
        )[1]

        # Create the wizard
        wiz_o.create(
            self.cursor,
            self.uid,
            {
                "account": 7,
                "payment_mode": payment_mode_id,
                "year": 2016,
                "quarter": 1,
            },
            context={},
        )

        # Mock totals_by_city data
        totals_by_city = [
            ["City1", "Province1", 1, 44001, 1500, "01001"],
            ["City2", "Province2", 1, 2000, 2500, "17114"],
        ]

        # Call the method to create invoices
        order_id, info = wiz_o.crear_factures(
            self.cursor,
            self.uid,
            totals_by_city,
            payment_mode_id,  # payment_mode_id
            7,  # account_id
            2016,  # year
            context={},
        )

        # Verify the payment order was created
        po = order_o.browse(self.cursor, self.uid, order_id)
        self.assertIsNotNone(po)
        self.assertEqual(po.state, 'draft')
        self.assertEqual(po.mode.id, payment_mode_id)

        # Verify the invoices were created and linked to the payment order
        invoice_ids = po.line_ids
        self.assertGreater(len(invoice_ids), 0)

        for invoice in invoice_ids:
            self.assertEqual(invoice.ml_inv_ref.state, 'open')
            self.assertEqual(invoice.ml_inv_ref.account_id.id, 7)
            self.assertEqual(invoice.ml_inv_ref.currency_id.code, 'EUR')

        # Verify the info message
        self.assertIn("S'ha creat la remesa amb", info)

    def test_get_dates_from_quarter(self):
        assert get_dates_from_quarter(2024, 1) == (
            datetime.date(2024, 1, 1),
            datetime.date(2024, 3, 31),
        )
        assert get_dates_from_quarter(2023, 4) == (
            datetime.date(2023, 10, 1),
            datetime.date(2023, 12, 31),
        )
        assert get_dates_from_quarter(1984, 5) == (
            datetime.date(1984, 1, 1),
            datetime.date(1984, 12, 31),
        )
