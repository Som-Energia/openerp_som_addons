# -*- coding: utf-8 -*-
import datetime
from destral import testing
from osv.osv import except_osv

from som_municipal_taxes.wizard.wizard_creacio_remesa_pagament_taxes import get_dates_from_quarter


class TestWizardCreacioRemesaPagamentTaxes(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestWizardCreacioRemesaPagamentTaxes, self).setUp()
        self.pool = self.openerp.pool

    def test_create_remesa_pagaments__ok(self):
        wiz_o = self.pool.get("wizard.creacio.remesa.pagament.taxes")
        order_o = self.pool.get("payment.order")
        wiz_init = {
            "account": 7,
            "payment_mode": 1,
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

    def test_create_remesa_pagaments__error_ja_pagat(self):
        wiz_o = self.pool.get("wizard.creacio.remesa.pagament.taxes")

        wiz_init = {
            "account": 7,
            "payment_mode": 1,
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
