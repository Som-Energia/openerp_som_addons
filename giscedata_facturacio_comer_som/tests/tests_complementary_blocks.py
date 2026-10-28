# -*- coding: utf-8 -*-
"""Database-free tests; all dates, identifiers and amounts are fictitious."""
from __future__ import absolute_import

import ast
from copy import deepcopy
from datetime import datetime, timedelta
import imp
import os
import unittest

MODULE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_helper():
    return imp.load_source('complementary_blocks',
                           os.path.join(MODULE, 'complementary_blocks.py'))


def synthetic_blocks(periods=3):
    blocks = []
    for index in range(4):
        start = datetime(2025, 7, 3) + timedelta(days=index * 4)
        block = dict(data_inici=start.strftime('%Y-%m-%d'),
                     data_fi=(start + timedelta(days=3)).strftime('%Y-%m-%d'),
                     type='energia', units='kWh', iva='21', total=1.37)
        for period in range(1, periods + 1):
            block['P%s' % period] = dict(
                quantity=2.0, price_unit_multi=0.217654321,
                price_subtotal=1.37 / periods, price_tolls=0.002,
                price_charges=0.003, tolls=0.004, charges=0.006)
        blocks.append(block)
    return blocks


class TestsComplementaryBlocks(unittest.TestCase):
    def test_four_blocks_sum_original_amounts_without_mutation(self):
        helper = load_helper()
        blocks = synthetic_blocks()
        original = deepcopy(blocks)
        merged = helper.merge_complementary_blocks(blocks, ['safe'] * 4)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['data_inici'], '2025-07-03')
        self.assertEqual(merged[0]['data_fi'], '2025-07-18')
        self.assertEqual(merged[0]['P1']['quantity'], 8.0)
        self.assertAlmostEqual(merged[0]['total'], 5.48)
        self.assertAlmostEqual(merged[0]['P1']['price_subtotal'], 5.48 / 3)
        self.assertAlmostEqual(merged[0]['P1']['tolls'], 0.016)
        self.assertAlmostEqual(merged[0]['P1']['charges'], 0.024)
        self.assertEqual(merged[0]['P1']['price_unit_multi'], 0.217654321)
        self.assertEqual(blocks, original)
        merged[0]['P1']['quantity'] = 999
        self.assertEqual(blocks, original)

    def test_empty_single_and_six_period_negative_amounts(self):
        helper = load_helper()
        self.assertEqual(helper.merge_complementary_blocks([], []), [])
        blocks = synthetic_blocks(6)
        self.assertEqual(helper.merge_complementary_blocks(blocks[:1], ['safe']), blocks[:1])
        for block in blocks:
            block['total'] *= -1
            for period in range(1, 7):
                block['P%s' % period]['price_subtotal'] *= -1
        result = helper.merge_complementary_blocks(blocks, ['safe'] * 4)
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0]['total'], -5.48)
        self.assertAlmostEqual(result[0]['P6']['price_subtotal'], -5.48 / 6)

    def test_incompatible_blocks_remain_separate(self):
        helper = load_helper()
        changes = [('iva', '10'), ('type', 'potencia'), ('units', 'kW'),
                   ('data_inici', '2025-07-08'), ('data_inici', '2025-07-06')]
        for field, value in changes:
            blocks = synthetic_blocks()[:2]
            blocks[1][field] = value
            self.assertEqual(helper.merge_complementary_blocks(blocks, ['safe'] * 2), blocks)
        for field in ('price_unit_multi', 'price_tolls', 'price_charges'):
            blocks = synthetic_blocks()[:2]
            blocks[1]['P2'][field] += 0.000000001
            self.assertEqual(helper.merge_complementary_blocks(blocks, ['safe'] * 2), blocks)
        blocks = synthetic_blocks()[:2]
        del blocks[1]['P3']
        self.assertEqual(helper.merge_complementary_blocks(blocks, ['safe'] * 2), blocks)
        blocks = synthetic_blocks()[:2]
        for signatures in (['safe', None], [None, None],
                           ['ABC/1234567890/ZZZ', 'ABC/1234567891/ZZZ']):
            self.assertEqual(helper.merge_complementary_blocks(blocks, signatures), blocks)

    def test_missing_source_signatures_never_discard_blocks(self):
        blocks = synthetic_blocks()
        self.assertEqual(load_helper().merge_complementary_blocks(blocks, ['safe']), blocks)


class Record(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


class SourceModel(object):
    """One in-memory ORM boundary for source-construction tests."""

    def __init__(self, rows):
        self.rows = rows

    def search(self, *args, **kwargs):
        return [row['id'] for row in self.rows]

    def read(self, cursor, uid, ids, fields):
        if isinstance(ids, int):
            return next(row for row in self.rows if row['id'] == ids)
        return self.rows

    def browse(self, *args):
        return self.rows


def production_report():
    """Compile unchanged production method bodies without booting OpenERP.

    Only ORM/service boundaries are replaced; data construction and chart maths
    execute the real source. Destral remains necessary for ORM integration.
    """
    path = os.path.join(MODULE, 'giscedata_facturacio_report.py')
    with open(path) as source:
        tree = ast.parse(source.read())
    selected = ast.parse('class Report(object):\n    pass\n')
    methods = ('get_sub_component_expedient_data', 'get_component_amount_destination_td_data')
    report = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                  and node.name == 'GiscedataFacturacioFacturaReport')
    selected.body[0].body = [node for node in report.body
                             if isinstance(node, ast.FunctionDef) and node.name in methods]
    selected.body.extend(node for node in tree.body if isinstance(node, ast.FunctionDef)
                         and node.name == 'get_iva_line')
    namespace = dict(datetime=datetime, timedelta=timedelta, is_TD=lambda pol: True)
    helper_path = os.path.join(MODULE, 'complementary_blocks.py')
    if os.path.exists(helper_path):
        namespace['merge_complementary_blocks'] = load_helper().merge_complementary_blocks
    exec(compile(selected, path, 'exec'), namespace)
    return namespace['Report']()


def source_fixture(periods=3):
    report = production_report()
    lines = []
    for block in synthetic_blocks(periods):
        for period in range(1, periods + 1):
            lines.append(Record(id=len(lines) + 1, tipus='energia', name='Synthetic energy',
                                product_id=Record(id=period, name='P%s' % period),
                                data_desde=block['data_inici'], data_fins=block['data_fi'],
                                uos_id=Record(id=1),
                                invoice_line_tax_id=[Record(id=21, name='IVA 21')],
                                **block['P%s' % period]))
    models = {
        'giscedata.facturacio.extra': SourceModel([Record(id=1, origin_invoice='SYNTHETIC')]),
        'giscedata.facturacio.importacio.linia': SourceModel([
            Record(id=1, num_expedient='ABC/1234567890/ZZZ', type_factura='C')]),
        'giscedata.facturacio.importacio.linia.factura': SourceModel([
            Record(id=1, tipo_factura='06')]),
        'giscedata.facturacio.factura.linia': SourceModel(lines),
        'res.config': type('Config', (object,), {'get': lambda *args: "{'r': 1}"})()}
    fact = Record(id=1, number='SYNTHETIC', pool=models, linia_ids=[], amount_total=50,
                  total_lloguers=0, amount_tax=0, total_atr=0, total_cargos=0)
    pol = Record(id=1, cups=Record(id=1))
    report.cursor = report.uid = None
    report.get_tarifa_elect_atr = lambda fact, name: name
    report.get_atr_price = lambda fact, tariff, line: (
        line.price_tolls if 'peajes' in tariff else line.price_charges)
    report.get_matrix_show_periods = lambda pol: ['P%s' % p for p in range(1, periods + 1)]
    for suffix in ('power_tolls', 'energy_tolls', 'power_charges', 'energy_charges',
                   'power_discount_BOE17_2021', 'energy_discount_BOE17_2021'):
        setattr(report, 'get_sub_component_invoice_details_td_%s_data' % suffix,
                lambda *args: dict(is_visible=True, total=0))
    return report, fact, pol, lines


class TestsComplementaryProductionMethods(unittest.TestCase):
    def test_source_construction_baseline(self):
        report, fact, pol, lines = source_fixture()
        result = report.get_sub_component_expedient_data(fact, pol, lines)
        self.assertEqual(result['expedient'], 'ABC/1234567890/ZZZ')
        self.assertEqual(result['tipus'], '06')
        self.assertAlmostEqual(sum(b['total'] for b in result['energy_lines_data']), 5.48)
        self.assertEqual(set(result), set(['expedient', 'tipus', 'energy_lines_data']))

    def test_real_source_method_merges_and_chart_retains_original_rounding(self):
        report, fact, pol, lines = source_fixture()
        data = report.get_sub_component_expedient_data(fact, pol, lines)
        blocks = data['energy_lines_data']
        self.assertEqual(len(blocks), 1)
        report.get_sub_component_invoice_details_td_other_concepts_data = (
            lambda fact, pol: dict(compl_info=data))
        chart = report.get_component_amount_destination_td_data(fact, pol)
        self.assertEqual(chart['pie_tolls'], 0.0)
        self.assertEqual(chart['pie_charges'], 0.12)
        self.assertEqual(chart['pie_energy'], 49.88)
        self.assertEqual(chart['pie_total'], 50)
        self.assertEqual(set(blocks[0]), set(synthetic_blocks()[0]))
        self.assertEqual(lines[0]['quantity'], 2.0)
        # Compare the actual chart consumer on original and merged data.
        data['energy_lines_data'] = blocks.original_blocks
        self.assertEqual(report.get_component_amount_destination_td_data(fact, pol), chart)
        # Demonstrate why rounding the merged values would be a regression.
        # Intentionally exercise the legacy chart's Python 2 rounding semantics.
        # pylint: disable=round-builtin
        self.assertAlmostEqual(sum(round(blocks[0][p]['tolls'], 2)
                                   for p in ('P1', 'P2', 'P3')), 0.06)
        self.assertAlmostEqual(sum(round(blocks[0][p]['charges'], 2)
                                   for p in ('P1', 'P2', 'P3')), 0.06)
        # pylint: enable=round-builtin

    def test_hidden_source_conflicts_refuse_fusion(self):
        for field, value in (
                ('data_fins', '2025-07-05'), ('price_unit_multi', 0.217654322),
                ('price_tolls', 0.002000001), ('price_charges', 0.003000001),
                ('tipus', 'altres'), ('uos_id', Record(id=2)),
                ('invoice_line_tax_id', [Record(id=10, name='IVA 10')])):
            report, fact, pol, lines = source_fixture()
            duplicate = deepcopy(lines[0])
            duplicate['id'] = 100
            duplicate[field] = value
            lines.append(duplicate)
            result = report.get_sub_component_expedient_data(fact, pol, lines)
            self.assertEqual(len(result['energy_lines_data']), 2, field)
            self.assertEqual(result['energy_lines_data'][0]['data_inici'], '2025-07-03')
            self.assertEqual(result['energy_lines_data'][1]['data_inici'], '2025-07-07')

    def test_differing_source_metadata_prices_and_periods(self):
        for field, value in (
                ('price_unit_multi', 0.217654322), ('price_tolls', 0.002000001),
                ('price_charges', 0.003000001), ('uos_id', Record(id=2)),
                ('invoice_line_tax_id', [Record(id=22, name='IVA 21')]),
                ('product_id', Record(id=101, name='P1'))):
            report, fact, pol, lines = source_fixture()
            lines[3][field] = value
            result = report.get_sub_component_expedient_data(fact, pol, lines)
            self.assertEqual(len(result['energy_lines_data']), 3, field)
        report, fact, pol, lines = source_fixture(6)
        del lines[6]
        result = report.get_sub_component_expedient_data(fact, pol, lines)
        self.assertEqual(len(result['energy_lines_data']), 3)

    def test_multiple_origins_or_expedients_remain_unmerged(self):
        for model_name, extra in (
                ('giscedata.facturacio.extra', Record(id=2, origin_invoice='SYNTHETIC-2')),
                ('giscedata.facturacio.importacio.linia',
                 Record(id=2, num_expedient='ABC/1234567891/ZZZ', type_factura='C')),
                ('giscedata.facturacio.importacio.linia.factura',
                 Record(id=2, tipo_factura='11'))):
            report, fact, pol, lines = source_fixture()
            fact.pool[model_name].rows.append(extra)
            result = report.get_sub_component_expedient_data(fact, pol, lines)
            self.assertEqual(len(result['energy_lines_data']), 4, model_name)
            self.assertEqual(type(result['energy_lines_data']), list)

    def test_missing_origin_or_expedient_remains_unmerged(self):
        for model_name, field in (
                ('giscedata.facturacio.extra', 'origin_invoice'),
                ('giscedata.facturacio.importacio.linia', 'num_expedient')):
            report, fact, pol, lines = source_fixture()
            fact.pool[model_name].rows[0][field] = False
            result = report.get_sub_component_expedient_data(fact, pol, lines)
            self.assertEqual(len(result['energy_lines_data']), 4, field)

    def test_six_period_negative_source_amounts_and_chart(self):
        report, fact, pol, lines = source_fixture(6)
        for line in lines:
            line['price_subtotal'] *= -1
        original = deepcopy(lines)
        data = report.get_sub_component_expedient_data(fact, pol, lines)
        blocks = data['energy_lines_data']
        self.assertEqual(len(blocks), 1)
        self.assertAlmostEqual(blocks[0]['total'], -5.48)
        self.assertEqual(blocks[0]['P6']['quantity'], 8)
        self.assertEqual(blocks[0]['P6']['price_tolls'], -0.002)
        report.get_sub_component_invoice_details_td_other_concepts_data = (
            lambda fact, pol: dict(compl_info=data))
        chart = report.get_component_amount_destination_td_data(fact, pol)
        self.assertEqual(chart['pie_tolls'], 0)
        self.assertEqual(chart['pie_charges'], -0.24)
        data['energy_lines_data'] = blocks.original_blocks
        self.assertEqual(report.get_component_amount_destination_td_data(fact, pol), chart)
        self.assertEqual(lines, original)

    def test_unmerged_public_dictionaries_are_unchanged(self):
        report, fact, pol, lines = source_fixture()
        # No safe F1 type: legacy fallback remains 11, no speculative fusion.
        fact.pool['giscedata.facturacio.importacio.linia.factura'].rows = []
        result = report.get_sub_component_expedient_data(fact, pol, lines)
        self.assertEqual(result, dict(expedient='ABC/1234567890/ZZZ', tipus='11',
                                      energy_lines_data=synthetic_blocks()))


if __name__ == '__main__':
    unittest.main()
