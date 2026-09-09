# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
import mock
from som_polissa.exceptions import exceptions


class TestCardPaymentHelper(testing.OOTestCaseWithCursor):
    def test_convert_policy_delegates_unchanged_result_and_copied_context(self):
        helper = self.openerp.pool.get("som.card.payment.helper")
        domain = mock.Mock()
        result = {"status": "complete", "invoices": {"migrated": [7]}}

        def mutate_context(cursor, uid, polissa_id, card_data, context=None):
            context["mutated_by_domain"] = True
            return result

        domain.convert_to_recurring_card.side_effect = mutate_context
        context = {"lang": "en_US"}

        with mock.patch.object(helper.pool, "get", return_value=domain):
            actual = helper.convert_policy(
                self.cursor, self.uid, 42, {"token": "token"}, context=context
            )

        self.assertEqual(actual, result)
        self.assertEqual(context, {"lang": "en_US"})

    def test_convert_policy_preserves_som_polissa_exception_response(self):
        helper = self.openerp.pool.get("som.card.payment.helper")
        domain = mock.Mock()
        domain.convert_to_recurring_card.side_effect = exceptions.PolissaNotActive("P-42")

        with mock.patch.object(helper.pool, "get", return_value=domain):
            result = helper.convert_policy(
                self.cursor, self.uid, 42, {"token": "token"}, context={}
            )

        self.assertEqual(result["code"], "PolissaNotActive")
        self.assertEqual(result["polissa_number"], "P-42")
