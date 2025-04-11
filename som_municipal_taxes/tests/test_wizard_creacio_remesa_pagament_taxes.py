# -*- coding: utf-8 -*-
import datetime
from destral import testing
import mock
import pandas as pd
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
        order_o = self.pool.get("payment.order")
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

        po = order_o.browse(self.cursor, self.uid, order_id)
        self.assertEqual(len(po.line_ids), 0)

    @mock.patch.object(FacturacioExtra, "get_states_invoiced")
    def test__crear_factures__ok(self, get_states_invoiced_mock):
        get_states_invoiced_mock.return_value = ['draft', 'open', 'paid']
        wiz_o = self.pool.get("wizard.creacio.remesa.pagament.taxes")
        order_o = self.pool.get("payment.order")
        payment_mode_id = self.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "account_invoice_som", "payment_mode_0001"
        )[1]

        # Create the wizard
        wiz_id = wiz_o.create(
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
        dades = {
            'base_compres': [100, 150],
            'base_vendes': [200, 250],
            'base_impost': [300, 400],
            'tax': [True, False],
            'TOVP': [1.5, 2.0]
        }
        # Crear un MultiIndex per a les files
        index = pd.MultiIndex.from_tuples(
            [
                ('Alegría-Dulantzi', '01001', 2016, '1T'),
                ('Olot', '17114', 2016, '2T')
            ],
            names=['municipi', 'ine', 'any', 'trimestre']
        )
        # Crear el DataFrame amb les dades i el MultiIndex
        totals_by_city = pd.DataFrame(dades, index=index)

        # Call the method to create invoices
        order_id, info = wiz_o.crear_factures(
            self.cursor,
            self.uid,
            wiz_id,
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
        self.assertEqual(po.total, 3.5)

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
