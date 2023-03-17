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

    def test_migration_post_0001_set_lleidanet_provider_for_existing_acc(self):
        import six
        if six.PY2:
            import imp
            from addons import get_module_resource
            script = get_module_resource(
                'powersms', 'migrations', '5.0.23.1.0',
                'post-0001-set_lleidanet_provider_for_existing_acc.py'
            )
            mod = imp.load_source('powersms', script)
            with Transaction().start(self.database) as txn:
                cursor, uid, pool = txn.cursor, txn.user, txn.pool
                imd_obj = pool.get('ir.model.data')
                acc_obj = pool.get('powersms.core_accounts')
                cursor.execute(
                    "ALTER TABLE powersms_core_accounts DROP COLUMN provider_id"
                )
                cursor.execute(
                    "DROP TABLE powersms_provider"
                )
                mod.up(cursor, True)
                provider_obj = pool.get('powersms.provider')
                providers = provider_obj.search(
                    cursor, uid, [], context={'active_test': False}
                )
                self.assertTrue(providers)
                for p_id in providers:
                    self.assertTrue(hasattr(provider_obj, provider_obj._get_provider_function(cursor, uid, p_id)))
                account_id = imd_obj.get_object_reference(cursor, uid, 'powersms', 'sms_account_som')[1]
                lleidanet_prov_id = imd_obj.get_object_reference(
                    cursor, uid, 'powersms', 'powersms_provider_lleidanet'
                )[1]
                provider_on_account = acc_obj.read(cursor, uid, account_id, ['provider_id'])['provider_id']
                self.assertTrue(provider_on_account)
                provider_on_account = provider_on_account[0]
                self.assertEqual(provider_on_account, lleidanet_prov_id)
