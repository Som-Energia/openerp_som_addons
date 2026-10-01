# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from destral.transaction import Transaction


class TestWizardBankAccountChange(testing.OOTestCase):

    def test_default_checks(self):
        wizard_obj = self.openerp.pool.get('wizard.bank.account.change')

        with Transaction().start(self.database) as txn:
            defaults = wizard_obj.default_get(
                txn.cursor,
                txn.user,
                [
                    'print_mandate',
                    'update_fact_pagades',
                    'update_fact_no_pagades',
                    'update_fact_emeses_6_months',
                ],
            )

        self.assertFalse(defaults['print_mandate'])
        self.assertFalse(defaults['update_fact_pagades'])
        self.assertTrue(defaults['update_fact_no_pagades'])
        self.assertFalse(defaults['update_fact_emeses_6_months'])
