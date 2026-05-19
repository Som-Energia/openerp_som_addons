# -*- coding: utf-8 -*-

import csv
import os
import xml.etree.ElementTree as ET

from destral import testing


class TestIndexedEstimateUISecurity(testing.OOTestCaseWithCursor):
    def _module_path(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    def _parse_xml(self, relative_path):
        full_path = os.path.join(self._module_path(), relative_path)
        self.assertTrue(os.path.exists(full_path), full_path)
        return ET.parse(full_path).getroot()

    def test_manifest_loads_new_ui_and_security_data_files(self):
        module_path = self._module_path()
        manifest_path = os.path.join(module_path, '__terp__.py')
        self.assertTrue(os.path.exists(manifest_path), manifest_path)

        namespace = {}
        manifest = eval(open(manifest_path).read(), {}, namespace)
        update_xml = manifest.get('update_xml', [])

        expected_files = [
            'security/som_simulacions_security.xml',
            'security/ir.model.access.csv',
            'views/parameter_views.xml',
            'views/simulation_views.xml',
            'views/menu.xml',
        ]
        for expected_file in expected_files:
            self.assertIn(expected_file, update_xml)

    def test_manifest_and_demo_xml_define_demo_seed_data(self):
        module_path = self._module_path()
        manifest_path = os.path.join(module_path, '__terp__.py')
        namespace = {}
        manifest = eval(open(manifest_path).read(), {}, namespace)

        demo_xml = manifest.get('demo_xml', [])
        expected_demo_files = [
            'demo/annual_coeff_demo.xml',
            'demo/energy_price_demo.xml',
            'demo/simulation_request_demo.xml',
        ]
        for expected_file in expected_demo_files:
            self.assertIn(expected_file, demo_xml)

        coeff_root = self._parse_xml('demo/annual_coeff_demo.xml')
        coeff_records = coeff_root.findall(
            ".//record[@model='som.simulacio.annual.coeff']")
        self.assertEqual(3, len(coeff_records))
        coeff_sum = 0.0
        for record in coeff_records:
            ratio_node = record.find("field[@name='ratio']")
            coeff_sum += float(ratio_node.text)
        self.assertAlmostEqual(1.0, coeff_sum, places=6)

        prices_root = self._parse_xml('demo/energy_price_demo.xml')
        price_records = prices_root.findall(
            ".//record[@model='som.simulacio.energy.price.monthly']")
        self.assertEqual(3, len(price_records))

        request_root = self._parse_xml('demo/simulation_request_demo.xml')
        request_records = request_root.findall(
            ".//record[@model='som.simulacio.request']")
        self.assertEqual(1, len(request_records))

    def test_parameter_views_define_expected_models_and_fields(self):
        root = self._parse_xml('views/parameter_views.xml')
        model_names = [
            node.text
            for node in root.findall(".//field[@name='model']")
        ]
        values = [
            node.attrib.get('name')
            for node in root.findall(".//*[@name]")
        ]

        self.assertIn('som.simulacio.energy.price.monthly', model_names)
        self.assertIn('som.simulacio.annual.coeff', model_names)
        self.assertIn('year', values)
        self.assertIn('month', values)
        self.assertIn('period', values)
        self.assertIn('tariff_code', values)
        self.assertIn('price', values)
        self.assertIn('ratio', values)

    def test_simulation_views_define_request_action_and_readonly_result_history(self):
        root = self._parse_xml('views/simulation_views.xml')
        model_names = [
            node.text
            for node in root.findall(".//field[@name='model']")
        ]

        self.assertIn('som.simulacio.request', model_names)
        self.assertIn('som.simulacio.result', model_names)

        run_button = root.find(".//button[@name='compute_indexed_estimate']")
        self.assertTrue(run_button is not None)

        untaxed_total_field = root.find(".//field[@name='untaxed_total']")
        self.assertEqual('1', untaxed_total_field.attrib.get('readonly'))

    def test_menu_wires_simulacions_indexed_hierarchy_and_actions(self):
        root = self._parse_xml('views/menu.xml')

        menu_ids = [
            node.attrib.get('id')
            for node in root.findall('.//menuitem')
        ]
        self.assertIn('menu_simulacions_indexed_root', menu_ids)
        self.assertIn('menu_simulacio_request', menu_ids)
        self.assertIn('menu_simulacio_result', menu_ids)
        self.assertIn('menu_simulacio_energy_price', menu_ids)
        self.assertIn('menu_simulacio_annual_coeff', menu_ids)

        action_ids = [
            node.attrib.get('id')
            for node in root.findall(".//record[@model='ir.actions.act_window']")
        ]
        self.assertIn('act_simulacio_request', action_ids)
        self.assertIn('act_simulacio_result', action_ids)
        self.assertIn('act_energy_price_monthly', action_ids)
        self.assertIn('act_annual_coeff', action_ids)

    def test_security_groups_and_acl_matrix_match_expected_permissions(self):
        root = self._parse_xml('security/som_simulacions_security.xml')
        group_ids = [
            node.attrib.get('id')
            for node in root.findall(".//record[@model='res.groups']")
        ]
        self.assertIn('group_simulacio_user', group_ids)
        self.assertIn('group_simulacio_manager', group_ids)

        acl_path = os.path.join(self._module_path(), 'security/ir.model.access.csv')
        self.assertTrue(os.path.exists(acl_path), acl_path)
        with open(acl_path) as acl_file:
            rows = list(csv.DictReader(acl_file))

        by_id = dict((row['id'], row) for row in rows)
        self.assertIn('access_simulacio_request_user', by_id)
        self.assertIn('access_simulacio_request_manager', by_id)
        self.assertIn('access_simulacio_result_user', by_id)
        self.assertIn('access_simulacio_result_manager', by_id)
        self.assertIn('access_energy_price_manager', by_id)
        self.assertIn('access_annual_coeff_manager', by_id)

        self.assertEqual('0', by_id['access_energy_price_manager']['perm_unlink'])
        self.assertEqual('0', by_id['access_annual_coeff_manager']['perm_unlink'])

        self.assertEqual('1', by_id['access_simulacio_request_user']['perm_read'])
        self.assertEqual('1', by_id['access_simulacio_request_user']['perm_create'])
        self.assertEqual('0', by_id['access_simulacio_request_user']['perm_unlink'])
        self.assertEqual('1', by_id['access_energy_price_manager']['perm_write'])
        self.assertEqual('0', by_id['access_energy_price_manager']['perm_unlink'])

    def test_module_has_translation_baseline_file(self):
        i18n_path = os.path.join(self._module_path(), 'i18n', 'ca_ES.po')
        self.assertTrue(os.path.exists(i18n_path), i18n_path)

        pot_path = os.path.join(self._module_path(), 'i18n', 'som_simulacions.pot')
        self.assertTrue(os.path.exists(pot_path), pot_path)
