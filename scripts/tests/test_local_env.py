# -*- coding: utf-8 -*-
from __future__ import absolute_import

import unittest

import check_local_env


class TestLocalEnvironment(unittest.TestCase):
    def test_imports_every_requested_module(self):
        imported = []

        def importer(name):
            imported.append(name)
            return object()

        self.assertEqual(check_local_env.check_modules(['one', 'two'], importer), [])
        self.assertEqual(imported, ['one', 'two'])

    def test_reports_all_missing_modules(self):
        def importer(name):
            raise ImportError('missing {}'.format(name))

        errors = check_local_env.check_modules(['one', 'two'], importer)
        self.assertEqual(len(errors), 2)
        self.assertIn('one: missing one', errors)
        self.assertIn('two: missing two', errors)

    def test_reports_broken_imports_not_just_missing_packages(self):
        def importer(name):
            raise RuntimeError('incompatible dependency')

        errors = check_local_env.check_modules(['one'], importer)
        self.assertEqual(errors, ['one: incompatible dependency'])

    def test_checks_pins_and_skips_comments(self):
        requested = []
        errors = check_local_env.check_requirements([
            '# tools', '', '  ', 'tool==1.0\n', 'other==2.0',
        ], requested.append)
        self.assertEqual(errors, [])
        self.assertEqual(requested, ['tool==1.0', 'other==2.0'])

    def test_reports_incompatible_versions(self):
        def require(requirement):
            raise RuntimeError('wrong version')

        errors = check_local_env.check_requirements(['tool==1.0'], require)
        self.assertEqual(errors, ['tool==1.0: wrong version'])


if __name__ == '__main__':
    unittest.main()
