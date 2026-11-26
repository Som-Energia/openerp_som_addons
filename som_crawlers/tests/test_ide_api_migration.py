# -*- coding: utf-8 -*-
from __future__ import absolute_import

import imp
import os

from destral import testing
from destral.transaction import Transaction


class IdeApiMigrationTests(testing.OOTestCase):
    def setUp(self):
        self.data = self.openerp.pool.get('ir.model.data')
        self.task = self.openerp.pool.get('som.crawlers.task')
        self.step = self.openerp.pool.get('som.crawlers.task.step')

    def api_references(self, cursor, uid):
        ids = self.data.search(cursor, uid, [
            ('module', '=', 'som_crawlers'),
            ('model', 'in', ['som.crawlers.task', 'som.crawlers.task.step']),
        ])
        rows = self.data.read(cursor, uid, ids, ['model', 'name', 'res_id'])
        return [
            row for row in rows
            if any(portal + '_api_' in row['name'] for portal in (
                'iberdrola', 'conquense', 'anselmo',
            ))
        ]

    def clear_reference_cache(self, database):
        self.data.get_object_reference.clear_cache(database)
        self.data._get_id.clear_cache(database)

    def test_upgrade_creates_api_tasks_before_steps_and_is_idempotent(self):
        path = os.path.join(
            os.path.dirname(__file__), '..', 'migrations', '5.0.25.5.0',
            'post-0005_ADD_api_iberdrola_migrate_fields_data.py',
        )
        migration = imp.load_source('test_ide_api_tasks_migration', path)
        original_loads = self.data.loads.copy()
        database = None
        try:
            with Transaction().start(self.database) as txn:
                cursor, uid = txn.cursor, txn.user
                database = cursor.dbname
                rows = self.api_references(cursor, uid)
                task_names = {}
                links = {}
                for row in rows:
                    if row['model'] == 'som.crawlers.task':
                        task_names[row['res_id']] = row['name']
                for row in rows:
                    if row['model'] == 'som.crawlers.task.step':
                        task_id = self.step.read(cursor, uid, row['res_id'], ['task_id'])
                        links[row['name']] = task_names[task_id['task_id'][0]]
                self.assertEqual(len(task_names), 54)
                self.assertEqual(len(links), 105)
                task_count = len(self.task.search(cursor, uid, []))
                step_count = len(self.step.search(cursor, uid, []))

                # Reproduce an existing installation without the new API tasks.
                self.step.unlink(cursor, uid, [
                    row['res_id'] for row in rows if row['model'] == 'som.crawlers.task.step'
                ])
                self.task.unlink(cursor, uid, list(task_names))
                remaining = self.data.search(cursor, uid, [
                    ('id', 'in', [row['id'] for row in rows]),
                ])
                if remaining:
                    self.data.unlink(cursor, uid, remaining)
                self.data.loads = {}
                self.clear_reference_cache(database)
                self.assertEqual(self.api_references(cursor, uid), [])
                self.assertEqual(
                    self.task.search(cursor, uid, [('id', 'in', list(task_names))]), []
                )

                migration.up(cursor, '5.0.25.5.0')

                created = self.api_references(cursor, uid)
                self.assertEqual(
                    sorted(row['name'] for row in created), sorted(row['name'] for row in rows)
                )
                for step_name, task_name in links.items():
                    task_id = self.data.get_object_reference(
                        cursor, uid, 'som_crawlers', task_name
                    )[1]
                    step_id = self.data.get_object_reference(
                        cursor, uid, 'som_crawlers', step_name
                    )[1]
                    step = self.step.read(cursor, uid, step_id, ['task_id'])
                    self.assertEqual(step['task_id'][0], task_id)

                migration.up(cursor, '5.0.25.5.0')

                self.assertEqual(
                    sorted(row['id'] for row in self.api_references(cursor, uid)),
                    sorted(row['id'] for row in created),
                )
                self.assertEqual(len(self.task.search(cursor, uid, [])), task_count)
                self.assertEqual(len(self.step.search(cursor, uid, [])), step_count)
        finally:
            self.data.loads = original_loads
            if database:
                self.clear_reference_cache(database)
