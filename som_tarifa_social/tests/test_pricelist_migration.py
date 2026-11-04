# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from addons import MigrationManager
from destral import testing
from oopgrade.oopgrade import load_data
from tools import cache, config


ROOT = os.path.dirname(os.path.dirname(__file__))


class TestPricelistMigration(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestPricelistMigration, self).setUp()
        self.imd = self.openerp.pool.get('ir.model.data')
        self.pricelist = self.openerp.pool.get('product.pricelist')
        self.xml_id = 'tarifa_20TD_SOM_SOCIAL'
        self.name = '2.0TD_SOM_SOCIAL'
        self.imd.unlink(self.cursor, self.uid, self.imd.search(
            self.cursor, self.uid, [
                ('module', 'in', ['www_som', 'som_tarifa_social']),
                ('name', '=', self.xml_id),
            ],
        ))
        cache.clean_caches_for_db(self.cursor.dbname)

    def _run(self, stage='pre'):
        path = os.path.join(
            ROOT, 'installation', '5.0.24.5.1',
            '{}-0001_reconcile_social_pricelist_ids.py'.format(stage),
        )
        namespace = {'__file__': path}
        with open(path, 'rb') as source:
            exec(compile(source.read(), path, 'exec'), namespace)
        namespace['migrate'](self.cursor, None)

    def _alias(self, module, pricelist_id, model='product.pricelist'):
        return self.imd.create(self.cursor, self.uid, {
            'module': module, 'name': self.xml_id,
            'model': model, 'res_id': pricelist_id, 'noupdate': False,
        })

    def _lookup(self, module):
        return self.imd.get_object_reference(
            self.cursor, self.uid, module, self.xml_id,
        )[1]

    def _candidate(self):
        ids = self.pricelist.search(
            self.cursor, self.uid, [('name', '=', self.name)],
            context={'active_test': False},
        )
        self.assertEqual(len(ids), 1)
        return ids[0]

    def _reload_xml(self):
        load_data(
            self.cursor, 'som_tarifa_social',
            'data/pricelist_social_data.xml', idref=None, mode='init',
        )

    def test_existing_legacy_record_is_reused_before_xml(self):
        pricelist_id = self._candidate()
        legacy_id = self._alias('www_som', pricelist_id)
        regular_id = self.imd.get_object_reference(
            self.cursor, self.uid, 'som_indexada',
            'pricelist_periodes_20td_peninsula',
        )[1]
        self.pricelist.write(self.cursor, self.uid, [pricelist_id], {
            'mesos_renovacio': 3, 'next_pricelist_id': regular_id,
        })
        version_obj = self.openerp.pool.get('product.pricelist.version')
        version_id = version_obj.create(self.cursor, self.uid, {
            'name': 'Migration preservation test',
            'pricelist_id': pricelist_id,
            'date_start': '2026-01-01',
        })
        item_obj = self.openerp.pool.get('product.pricelist.item')
        item_id = item_obj.create(self.cursor, self.uid, {
            'name': 'Configured social tariff rule',
            'price_version_id': version_id,
            'base': -1, 'base_pricelist_id': regular_id,
            'price_discount': -0.153,
        })
        item_fields = ['price_version_id', 'base_pricelist_id', 'price_discount']
        before_item = item_obj.read(
            self.cursor, self.uid, item_id, item_fields,
        )

        self._run()
        self._reload_xml()
        self._run('post')

        self.assertEqual(self._lookup('som_tarifa_social'), pricelist_id)
        self.assertEqual(self._lookup('www_som'), pricelist_id)
        self.assertTrue(self.imd.read(
            self.cursor, self.uid, legacy_id, ['noupdate'],
        )['noupdate'])
        self.assertEqual(self.pricelist.read(
            self.cursor, self.uid, pricelist_id, ['mesos_renovacio'],
        )['mesos_renovacio'], 3)
        self.assertEqual(version_obj.read(
            self.cursor, self.uid, version_id, ['pricelist_id'],
        )['pricelist_id'][0], pricelist_id)
        self.assertEqual(self.pricelist.read(
            self.cursor, self.uid, pricelist_id, ['next_pricelist_id'],
        )['next_pricelist_id'][0], regular_id)
        self.assertEqual(item_obj.read(
            self.cursor, self.uid, item_id, item_fields,
        ), before_item)

    def test_legacy_alias_survives_cleanup_without_legacy_xml(self):
        pricelist_id = self._candidate()
        self._alias('www_som', pricelist_id)
        self._run()
        loads, unlink_mark = self.imd.loads, self.imd.unlink_mark
        try:
            self.imd.loads = {}
            self.imd.unlink_mark = {}
            self.imd._process_end(self.cursor, self.uid, ['www_som'])
        finally:
            self.imd.loads, self.imd.unlink_mark = loads, unlink_mark

        self.assertEqual(self._lookup('www_som'), pricelist_id)
        self.assertTrue(self.pricelist.search(
            self.cursor, self.uid, [('id', '=', pricelist_id)],
            context={'active_test': False},
        ))

    def test_dangling_legacy_id_reuses_unique_named_record(self):
        pricelist_id = self._candidate()
        metadata_id = self._alias('www_som', 2147483647)
        self.assertEqual(self._lookup('www_som'), 2147483647)

        self._run()

        self.assertEqual(self._lookup('www_som'), pricelist_id)
        self.assertEqual(self._lookup('som_tarifa_social'), pricelist_id)
        self.assertEqual(self.imd.read(
            self.cursor, self.uid, metadata_id, ['res_id'],
        )['res_id'], pricelist_id)

    def test_missing_record_is_created_by_xml_then_aliased(self):
        self.pricelist.write(self.cursor, self.uid, [self._candidate()], {
            'name': 'Unrelated retained test pricelist',
        })
        self._alias('www_som', 2147483647)
        self._alias('som_tarifa_social', 2147483646)

        self._run()
        self._reload_xml()
        self._run('post')

        self.assertEqual(
            self._lookup('som_tarifa_social'), self._candidate(),
        )
        self.assertEqual(self._lookup('www_som'), self._candidate())

    def test_conflicting_existing_records_are_not_merged(self):
        pricelist_id = self._candidate()
        other_id = self.pricelist.copy(self.cursor, self.uid, pricelist_id)
        self._alias('www_som', pricelist_id)
        self._alias('som_tarifa_social', other_id)

        with self.assertRaises(ValueError):
            self._run()

        self.assertEqual(self._lookup('www_som'), pricelist_id)
        self.assertEqual(self._lookup('som_tarifa_social'), other_id)

    def test_ambiguous_name_recovery_is_rejected(self):
        self.pricelist.copy(self.cursor, self.uid, self._candidate(), {
            'name': self.name,
        })
        self._alias('www_som', 2147483647)

        with self.assertRaises(ValueError):
            self._run()

    def test_valid_new_identity_repairs_dangling_legacy_identity(self):
        pricelist_id = self._candidate()
        self._alias('som_tarifa_social', pricelist_id)
        self._alias('www_som', 2147483647)

        self._run()

        self.assertEqual(self._lookup('www_som'), pricelist_id)
        self.assertEqual(self._lookup('som_tarifa_social'), pricelist_id)

    def test_later_conflict_does_not_partially_repair_earlier_tariffs(self):
        metadata_id = self._alias('www_som', self._candidate())
        self.imd.unlink(self.cursor, self.uid, self.imd.search(
            self.cursor, self.uid, [
                ('module', '=', 'www_som'),
                ('name', '=', 'tarifa_indexada_20TD_canaries_social'),
            ],
        ))
        self.imd.create(self.cursor, self.uid, {
            'module': 'www_som',
            'name': 'tarifa_indexada_20TD_canaries_social',
            'model': 'res.partner', 'res_id': 1,
        })

        with self.assertRaises(ValueError):
            self._run()

        self.assertFalse(self.imd.search(self.cursor, self.uid, [
            ('module', '=', 'som_tarifa_social'),
            ('name', '=', self.xml_id),
        ]))
        self.assertFalse(self.imd.read(
            self.cursor, self.uid, metadata_id, ['noupdate'],
        )['noupdate'])

    def test_wrong_external_id_model_is_rejected(self):
        self._alias('www_som', 1, model='res.partner')

        with self.assertRaises(ValueError):
            self._run()

    def test_repeated_execution_preserves_metadata_ids(self):
        self._alias('www_som', self._candidate())
        self._run()
        self._reload_xml()
        self._run('post')
        before = self.imd.search_reader(self.cursor, self.uid, [
            ('module', 'in', ['www_som', 'som_tarifa_social']),
            ('name', '=', self.xml_id),
        ], ['id', 'module', 'res_id', 'noupdate'])

        self._run()
        self._run('post')

        after = self.imd.search_reader(self.cursor, self.uid, [
            ('module', 'in', ['www_som', 'som_tarifa_social']),
            ('name', '=', self.xml_id),
        ], ['id', 'module', 'res_id', 'noupdate'])
        self.assertEqual(before, after)

    def test_post_stage_requires_xml_to_have_created_missing_records(self):
        self.pricelist.write(self.cursor, self.uid, [self._candidate()], {
            'name': 'Unrelated retained test pricelist',
        })

        with self.assertRaises(ValueError):
            self._run('post')

    def test_installation_hooks_run_through_module_migration_loader(self):
        pricelist_id = self._candidate()
        self._alias('www_som', pricelist_id)
        package = type('MigrationPackage', (object,), {})()
        package.name = 'som_tarifa_social'
        self.cursor.execute(
            'SELECT id FROM ir_module_module WHERE name = %s',
            (package.name,),
        )
        package.id = self.cursor.fetchone()[0]
        package.state = 'to install'
        package.installed_version = None
        package.data = {'version': '24.5.1'}
        self.cursor.execute(
            'DELETE FROM ir_module_migration '
            'WHERE module_id = %s AND version = %s',
            (package.id, '5.0.24.5.1'),
        )
        interactive = config.get('run_scripts_interactive')
        try:
            config['run_scripts_interactive'] = False
            manager = MigrationManager(self.cursor, [package])
            manager.migrate_module(package, 'pre', installing=True)
            self._reload_xml()
            manager.migrate_module(package, 'post', installing=True)
        finally:
            config['run_scripts_interactive'] = interactive

        self.assertEqual(self._lookup('som_tarifa_social'), pricelist_id)
        self.assertEqual(self._lookup('www_som'), pricelist_id)
        self.cursor.execute(
            'SELECT count(*) FROM ir_module_migration '
            'WHERE module_id = %s AND version = %s',
            (package.id, '5.0.24.5.1'),
        )
        self.assertEqual(self.cursor.fetchone()[0], 2)
