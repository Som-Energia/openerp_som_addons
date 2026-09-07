# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
import mock


class TestCardPaymentHelper(testing.OOTestCaseWithCursor):
    def test_convert_policy_delegates_unchanged_result_and_copied_context(self):
        helper = self.openerp.pool.get("som.card.payment.helper")
        domain = mock.Mock()
        result = {"status": "complete", "invoices": {"migrated": [7]}}
        domain.convert_to_recurring_card.return_value = result
        context = {"lang": "en_US"}

        with mock.patch.object(helper.pool, "get", return_value=domain):
            actual = helper.convert_policy(
                self.cursor, self.uid, 42, {"token": "token"}, context=context
            )

        self.assertEqual(actual, result)
        domain.convert_to_recurring_card.assert_called_once_with(
            self.cursor, self.uid, 42, {"token": "token"}, context={"lang": "en_US"}
        )
        self.assertEqual(context, {"lang": "en_US"})
