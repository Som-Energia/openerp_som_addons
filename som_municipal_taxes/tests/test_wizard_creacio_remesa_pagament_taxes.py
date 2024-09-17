# -*- coding: utf-8 -*-
from destral import testing


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
            "quarter": 'T1',
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

        payment_orders = order_o.search(self.cursor, self.uid, [], limit=1, order="id desc")
        po = order_o.browse(self.cursor, self.uid, payment_orders[0])
        self.assertEqual(len(po.line_ids), 1)

    def test_create_remesa_pagaments__error_ja_pagat(self):
        wiz_o = self.pool.get("wizard.creacio.remesa.pagament.taxes")
        order_o = self.pool.get("payment.order")
        wiz_init = {
            "account": 7,
            "payment_mode": 1,
            "year": 2016,
            "quarter": 'T1',
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
        wiz_o.create_remesa_pagaments(
            self.cursor,
            self.uid,
            [wiz_id],
            {},
        )

        payment_orders = order_o.search(self.cursor, self.uid, [], limit=1, order="id desc")
        po = order_o.browse(self.cursor, self.uid, payment_orders[0])
        self.assertEqual(len(po.line_ids), 1)
