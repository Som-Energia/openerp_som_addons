# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from destral import testing
from destral.transaction import Transaction


class TestProviders(testing.OOTestCase):
    def test_provider_code_implementation(self):
        with Transaction().start(self.database) as txn:
            cursor, uid, pool = txn.cursor, txn.user, txn.pool
            provider_obj = pool.get('powersms.provider')
            providers = provider_obj.search(
                cursor, uid, [], context={'active_test': False}
            )
            self.assertTrue(providers)
            for p_id in providers:
                self.assertTrue(hasattr(provider_obj, provider_obj._get_provider_function(cursor, uid, p_id)))

    def test_provider_code_implementation_reverse(self):
        with Transaction().start(self.database) as txn:
            cursor, uid, pool = txn.cursor, txn.user, txn.pool
            provider_obj = pool.get('powersms.provider')
            provider_pattern_methods = [
                m for m in dir(provider_obj) if m.startswith('send_sms_') and m != 'send_sms_default'
            ]
            self.assertTrue(provider_pattern_methods)
            for _method in provider_pattern_methods:
                self.assertTrue(
                    provider_obj.search(cursor, uid, [('function_pattern_code', '=', _method.replace('send_sms_', ''))])
                )


