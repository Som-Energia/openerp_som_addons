# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import ast
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import create_migration_script as migration


class CapturedOutput(object):
    def __init__(self):
        self.value = ''

    def write(self, value):
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        self.value += value

    def flush(self):
        pass


class MigrationResourceOrderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix='migration-order-')
        self.original_directory = os.getcwd()
        self.original_branch = migration.get_current_branch
        self.original_modified = migration.get_modified_files
        self.original_stdout = sys.stdout
        self.output = CapturedOutput()
        sys.stdout = self.output
        migration.get_current_branch = lambda: 'TEST_manifest_order'
        self.script = os.path.abspath(migration.__file__)
        if self.script.endswith('.pyc'):
            self.script = self.script[:-1]
        os.chdir(self.directory)

    def tearDown(self):
        sys.stdout = self.original_stdout
        migration.get_current_branch = self.original_branch
        migration.get_modified_files = self.original_modified
        os.chdir(self.original_directory)
        shutil.rmtree(self.directory)

    def write(self, path, content):
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        with io.open(path, 'w', encoding='utf-8') as output:
            output.write(content)

    def manifest(self, update=None, init=None, module='fixture'):
        self.write(os.path.join(module, '__terp__.py'), repr({
            'init_xml': init or [], 'update_xml': update or [],
        }))

    def files(self, data=None, security=None, py=None):
        return {'data': data or [], 'security': security or [], 'py': py or [], 'po': []}

    def migration_directory(self, module='fixture'):
        return os.path.join(module, 'migrations', migration.TARGET_VERSION)

    def generated_source(self):
        directory = self.migration_directory()
        files = os.listdir(directory)
        self.assertEqual(len(files), 1)
        with io.open(os.path.join(directory, files[0]), encoding='utf-8') as source:
            return source.read()

    def generated_resources(self):
        source = self.generated_source()
        for node in ast.walk(ast.parse(source.encode('utf-8'))):
            if isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == 'data_files'
                    for target in node.targets):
                return ast.literal_eval(node.value)
        self.fail('Generated migration has no data_files assignment')

    def test_tasks_precede_steps_despite_alphabetical_diff_order(self):
        self.manifest(['config.xml', 'tasks.xml', 'steps.xml'])
        changed = self.files(data=['config.xml', 'steps.xml', 'tasks.xml'])

        migration.create_migration_script('fixture', changed)

        self.assertEqual(self.generated_resources(), ['config.xml', 'tasks.xml', 'steps.xml'])

    def test_xml_and_security_csv_keep_interleaved_manifest_order(self):
        expected = ['groups.xml', 'security/access.csv', 'tasks.xml', 'steps.xml']
        self.manifest(expected)
        changed = self.files(
            data=['steps.xml', 'tasks.xml', 'groups.xml'], security=['security/access.csv'],
        )

        migration.create_migration_script('fixture', changed)

        self.assertEqual(self.generated_resources(), expected)
        self.assertNotIn('for security_file', self.generated_source())

    def test_init_xml_precedes_update_xml_and_only_changed_resources_load(self):
        self.manifest(
            init=['unchanged_init.xml', 'groups.xml'],
            update=['unchanged.xml', 'tasks.xml', 'steps.xml'],
        )

        result = migration.get_ordered_data_files('fixture', self.files(
            data=['steps.xml', 'tasks.xml', 'groups.xml'],
        ))

        self.assertEqual(result, ['groups.xml', 'tasks.xml', 'steps.xml'])

    def test_explicit_repeated_manifest_entries_keep_their_order(self):
        self.manifest(['config.xml', 'tasks.xml', 'config.xml', 'steps.xml'])

        result = migration.get_ordered_data_files('fixture', self.files(
            data=['steps.xml', 'config.xml'],
        ))

        self.assertEqual(result, ['config.xml', 'config.xml', 'steps.xml'])

    def test_security_only_changes_generate_a_migration(self):
        self.manifest(['security/access.csv'])
        changed = self.files(security=['security/access.csv'])
        migration.get_modified_files = lambda: {'fixture': changed}

        migration.main()

        self.assertEqual(self.generated_resources(), ['security/access.csv'])
        self.assertIn('from oopgrade.oopgrade import load_data', self.generated_source())

    def test_model_only_changes_do_not_need_a_resource_manifest(self):
        self.write('fixture/model.py', (
            "class Record(object):\n"
            "    _name = 'fixture.record'\n"
            "    _columns = {}\n"
        ))

        migration.create_migration_script('fixture', self.files(py=['model.py']))

        self.assertIn('fixture.record', self.generated_source())
        self.assertNotIn('data_files =', self.generated_source())

    def test_model_initialization_still_precedes_data_loading(self):
        self.manifest(['data.xml'])
        self.write('fixture/model.py', (
            "class Record(object):\n"
            "    _name = 'fixture.record'\n"
            "    _columns = {}\n"
        ))

        migration.create_migration_script(
            'fixture', self.files(data=['data.xml'], py=['model.py']),
        )

        source = self.generated_source()
        self.assertLess(source.index('._auto_init('), source.index('for data_file in'))

    def test_empty_selection_does_not_read_a_manifest(self):
        self.assertEqual(migration.get_ordered_data_files('missing', self.files()), [])

    def test_unlisted_resource_stops_generation_without_creating_directories(self):
        self.manifest(['known.xml'])

        with self.assertRaises(migration.MigrationOrderError) as error:
            migration.create_migration_script('fixture', self.files(data=['unknown.xml']))

        self.assertIn('unknown.xml', str(error.exception))
        self.assertFalse(os.path.exists(self.migration_directory()))

    def test_unlisted_security_csv_also_requires_manual_review(self):
        self.manifest(['groups.xml'])

        with self.assertRaises(migration.MigrationOrderError):
            migration.create_migration_script(
                'fixture', self.files(security=['security/unknown.csv']),
            )

        self.assertFalse(os.path.exists(self.migration_directory()))

    def test_invalid_selection_does_not_replace_an_existing_script(self):
        self.manifest(['known.xml'])
        path = os.path.join(
            self.migration_directory(), 'post-0001_TEST_manifest_order_migrate_data.py',
        )
        self.write(path, '# original migration\n')

        with self.assertRaises(migration.MigrationOrderError):
            migration.create_migration_script(
                'fixture', self.files(data=['unknown.xml']), replace=True,
            )

        with io.open(path, encoding='utf-8') as source:
            self.assertEqual(source.read(), '# original migration\n')

    def test_missing_manifest_needs_manual_review(self):
        with self.assertRaises(migration.MigrationOrderError):
            migration.get_ordered_data_files('missing', self.files(data=['data.xml']))

    def test_manifest_is_never_executed(self):
        self.write('fixture/__terp__.py', "__import__('os').system('touch EXECUTED')")

        with self.assertRaises(migration.MigrationOrderError):
            migration.get_ordered_data_files('fixture', self.files(data=['data.xml']))

        self.assertFalse(os.path.exists('EXECUTED'))

    def test_invalid_manifest_and_resource_types_are_rejected(self):
        for content in (
            'not valid python !', '[]', "{'update_xml': 'data.xml'}",
            "{'update_xml': [123]}", "{'init_xml': None}",
        ):
            self.write('fixture/__terp__.py', content)
            with self.assertRaises(migration.MigrationOrderError):
                migration.get_ordered_data_files('fixture', self.files(data=['data.xml']))

    def test_dry_run_reports_the_same_order_without_writing(self):
        self.manifest(['config.xml', 'tasks.xml', 'steps.xml'])
        changed = self.files(data=['steps.xml', 'config.xml', 'tasks.xml'])

        migration.create_migration_script('fixture', changed, dry_run=True)

        self.assertIn('config.xml, tasks.xml, steps.xml', self.output.value)
        self.assertFalse(os.path.exists(self.migration_directory()))
        migration.create_migration_script('fixture', changed)
        self.assertEqual(self.generated_resources(), ['config.xml', 'tasks.xml', 'steps.xml'])

    def test_existing_script_is_preserved_unless_replace_is_explicit(self):
        self.manifest(['data.xml'])
        path = os.path.join(
            self.migration_directory(), 'post-0001_TEST_manifest_order_migrate_data.py',
        )
        self.write(path, '# original migration\n')

        migration.create_migration_script('fixture', self.files(data=['data.xml']))

        with io.open(path, encoding='utf-8') as source:
            self.assertEqual(source.read(), '# original migration\n')
        migration.create_migration_script(
            'fixture', self.files(data=['data.xml']), replace=True,
        )
        self.assertEqual(self.generated_resources(), ['data.xml'])

    def test_ambiguous_module_stops_all_modules_before_writing(self):
        self.manifest(['data.xml'], module='a_valid')
        self.manifest([], module='z_invalid')
        migration.get_modified_files = lambda: {
            'a_valid': self.files(data=['data.xml']),
            'z_invalid': self.files(data=['missing.xml']),
        }

        with self.assertRaises(migration.MigrationOrderError):
            migration.main()

        self.assertFalse(os.path.exists(self.migration_directory('a_valid')))
        self.assertFalse(os.path.exists(self.migration_directory('z_invalid')))

    def test_resource_names_are_quoted_as_valid_python_literals(self):
        resource = "data/O'Brien.xml"
        self.manifest([resource])

        migration.create_migration_script('fixture', self.files(data=[resource]))

        self.assertEqual(self.generated_resources(), [resource])

    def init_git_fixture(self):
        subprocess.check_call(['git', 'init', '-q', '--initial-branch=main'])
        subprocess.check_call(['git', 'add', '.'])
        subprocess.check_call([
            'git', '-c', 'user.name=Test Fixture', '-c', 'user.email=test@example.invalid',
            '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null',
            'commit', '-qm', 'baseline',
        ])
        subprocess.check_call(['git', 'checkout', '-qb', 'TEST_manifest_order'])

    def test_cli_generates_in_manifest_order_from_real_git_diff(self):
        self.manifest(['config.xml', 'tasks.xml', 'steps.xml'])
        for path in ('config.xml', 'tasks.xml', 'steps.xml'):
            self.write('fixture/' + path, '<openerp/>\n')
        self.init_git_fixture()
        for path in ('config.xml', 'tasks.xml', 'steps.xml'):
            self.write('fixture/' + path, '<openerp/>\n<!-- changed -->\n')

        subprocess.check_output([sys.executable, self.script, '--dry-run'])
        self.assertFalse(os.path.exists(self.migration_directory()))
        subprocess.check_output([sys.executable, self.script])

        self.assertEqual(self.generated_resources(), ['config.xml', 'tasks.xml', 'steps.xml'])

    def test_cli_reports_ambiguous_order_without_traceback_or_output_files(self):
        self.manifest([])
        self.write('fixture/unknown.xml', '<openerp/>\n')
        self.init_git_fixture()
        self.write('fixture/unknown.xml', '<openerp/>\n<!-- changed -->\n')

        for arguments in ([], ['--dry-run']):
            process = subprocess.Popen(
                [sys.executable, self.script] + arguments,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            _, stderr = process.communicate()

            self.assertEqual(process.returncode, 2)
            self.assertIn('not declared', stderr.decode('utf-8'))
            self.assertNotIn('Traceback', stderr.decode('utf-8'))
            self.assertFalse(os.path.exists(self.migration_directory()))


if __name__ == '__main__':
    unittest.main()
