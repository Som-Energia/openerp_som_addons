# -*- coding: utf-8 -*-
"""Database-free tests; all dates, identifiers and amounts are fictitious."""
from __future__ import absolute_import

import ast
from copy import deepcopy
from datetime import datetime, timedelta
import imp
import os
import unittest
from lxml import html
from mako.lookup import TemplateLookup
from yamlns import namespace as ns

MODULE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_helper():
    return imp.load_source('complementary_blocks',
                           os.path.join(MODULE, 'complementary_blocks.py'))


def synthetic_blocks(periods=3, concept='energia'):
    blocks = []
    for index in range(4):
        start = datetime(2025, 7, 3) + timedelta(days=index * 4)
        block = dict(data_inici=start.strftime('%Y-%m-%d'),
                     data_fi=(start + timedelta(days=3)).strftime('%Y-%m-%d'),
                     type=concept, units={'energia': 'kWh', 'potencia': 'kW',
                                          'reactiva': 'kVArh'}[concept], iva='21', total=1.37)
        for period in range(1, periods + 1):
            block['P%s' % period] = dict(
                quantity=3.0 if concept == 'potencia' else 2.0,
                price_unit_multi=0.217654321, price_subtotal=1.37 / periods,
                price_tolls=0.001 if concept == 'potencia' else 0.002,
                price_charges=0.002 if concept == 'potencia' else 0.003,
                tolls=0.003 if concept == 'potencia' else 0.004, charges=0.006)
        blocks.append(block)
    return blocks


class TestsComplementaryBlocks(unittest.TestCase):
    def test_equal_power_merges_without_adding_kw(self):
        blocks = synthetic_blocks(concept='potencia')[:2]
        original = deepcopy(blocks)
        result = load_helper().merge_complementary_blocks(blocks, ['safe'] * 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['P1']['quantity'], 3)
        self.assertAlmostEqual(result[0]['total'], 2.74)
        self.assertAlmostEqual(result[0]['P1']['price_subtotal'], 2.74 / 3)
        self.assertEqual(result[0]['data_fi'], '2025-07-10')
        self.assertEqual(blocks, original)
        result[0]['P1']['quantity'] = 999
        self.assertEqual(blocks, original)

    def test_power_compatibility_uses_every_exact_kw_and_price(self):
        helper = load_helper()
        for periods in (3, 6):
            for period in range(1, periods + 1):
                for field in ('quantity', 'price_unit_multi', 'price_tolls', 'price_charges'):
                    blocks = synthetic_blocks(periods, 'potencia')[:2]
                    blocks[1]['P%s' % period][field] += 0.000000001
                    self.assertEqual(
                        helper.merge_complementary_blocks(blocks, ['safe'] * 2), blocks,
                        (periods, period, field))
        for field, value in (
                ('data_inici', '2025-07-08'), ('data_inici', '2025-07-06'),
                ('units', 'W'), ('iva', '10'), ('type', 'energia')):
            blocks = synthetic_blocks(concept='potencia')[:2]
            blocks[1][field] = value
            self.assertEqual(helper.merge_complementary_blocks(blocks, ['safe'] * 2), blocks)
        blocks = synthetic_blocks(6, 'potencia')[:2]
        del blocks[1]['P6']
        self.assertEqual(helper.merge_complementary_blocks(blocks, ['safe'] * 2), blocks)
        blocks = synthetic_blocks(concept='potencia')[:2]
        self.assertEqual(helper.merge_complementary_blocks(blocks, ['safe', None]), blocks)

    def test_power_negative_amounts_and_three_six_periods_keep_kw(self):
        helper = load_helper()
        for periods in (3, 6):
            for quantity in (3, -3):
                blocks = synthetic_blocks(periods, 'potencia')
                for block in blocks:
                    block['total'] *= -1
                    for period in range(1, periods + 1):
                        values = block['P%s' % period]
                        values['quantity'] = quantity
                        for field in ('price_subtotal', 'tolls', 'charges',
                                      'price_tolls', 'price_charges'):
                            values[field] *= -1
                original = deepcopy(blocks)
                result = helper.merge_complementary_blocks(blocks, ['safe'] * 4)
                self.assertEqual(len(result), 1)
                for period in range(1, periods + 1):
                    self.assertEqual(result[0]['P%s' % period]['quantity'], quantity)
                    self.assertAlmostEqual(result[0]['P%s' % period]['price_subtotal'],
                                           -5.48 / periods)
                self.assertAlmostEqual(result[0]['total'], -5.48)
                self.assertEqual(blocks, original)

    def test_energy_and_reactive_quantities_remain_additive(self):
        for concept in ('energia', 'reactiva'):
            blocks = synthetic_blocks(6, concept)
            blocks[1]['P6']['quantity'] = 5
            result = load_helper().merge_complementary_blocks(blocks, ['safe'] * 4)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['P1']['quantity'], 8)
            self.assertEqual(result[0]['P6']['quantity'], 11)
            self.assertAlmostEqual(result[0]['total'], 5.48)

    def test_four_blocks_sum_original_amounts_without_mutation(self):
        helper = load_helper()
        blocks = synthetic_blocks()
        original = deepcopy(blocks)
        merged = helper.merge_complementary_blocks(blocks, ['safe'] * 4)
        self.assertEqual(type(merged), list)
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
    methods = ('get_sub_component_expedient_data', 'get_component_amount_destination_td_data',
               'fill_all_components_data')
    report = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                  and node.name == 'GiscedataFacturacioFacturaReport')
    selected.body[0].body = [node for node in report.body
                             if isinstance(node, ast.FunctionDef) and node.name in methods]
    selected.body.extend(node for node in tree.body if isinstance(node, ast.FunctionDef)
                         and node.name == 'get_iva_line')
    namespace = dict(datetime=datetime, timedelta=timedelta, is_TD=lambda pol: True, ns=ns)
    helper_path = os.path.join(MODULE, 'complementary_blocks.py')
    if os.path.exists(helper_path):
        namespace['merge_complementary_blocks'] = load_helper().merge_complementary_blocks
    exec(compile(selected, path, 'exec'), namespace)
    return namespace['Report']()


def source_fixture(periods=3, concept='energia'):
    report = production_report()
    lines = []
    for block in synthetic_blocks(periods, concept):
        for period in range(1, periods + 1):
            lines.append(Record(id=len(lines) + 1, tipus=concept, name='Synthetic ' + concept,
                                product_id=Record(id=period, name='P%s' % period),
                                data_desde=block['data_inici'], data_fins=block['data_fi'],
                                uos_id=Record(id=1, name=block['units']),
                                multi=4, uom_multi_id=Record(id=2, name='Days'),
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
    def test_power_roundtrip_chart_and_actual_mako_keep_three_kw(self):
        template = TemplateLookup(
            directories=[os.path.dirname(MODULE)], input_encoding='utf-8').get_template(
                '/giscedata_facturacio_comer_som/report/components/'
                'invoice_details_td_other_concepts/invoice_details_td_other_concepts.mako')
        for periods in (3, 6):
            for sign in (1, -1):
                report, fact, pol, lines = source_fixture(periods, 'potencia')
                for line in lines:
                    line['price_subtotal'] *= sign
                original = deepcopy(lines)
                data = report.get_sub_component_expedient_data(fact, pol, lines)
                self.assertEqual(len(data['energy_lines_data']), 1)
                reference = deepcopy(data)
                reference['energy_lines_data'] = reference.pop('original_energy_lines_data')
                report.get_sub_component_invoice_details_td_other_concepts_data = (
                    lambda fact, pol: dict(compl_info=reference))
                chart = report.get_component_amount_destination_td_data(fact, pol)
                self.assertEqual(chart['pie_tolls'], 0)
                self.assertEqual(chart['pie_charges'], sign * 0.04 * periods)
                report.get_sub_component_invoice_details_td_other_concepts_data = (
                    lambda fact, pol: dict(compl_info=data))
                self.assertEqual(report.get_component_amount_destination_td_data(fact, pol), chart)
                report.cleanup_data = lambda fact: None
                result = report.fill_all_components_data(
                    {'other': report.get_sub_component_invoice_details_td_other_concepts_data},
                    fact, pol, {})
                restored = result['other']['compl_info']
                report.get_sub_component_invoice_details_td_other_concepts_data = (
                    lambda fact, pol: dict(compl_info=restored))
                self.assertEqual(report.get_component_amount_destination_td_data(fact, pol), chart)
                block = restored['energy_lines_data'][0]
                self.assertEqual(len(restored['original_energy_lines_data']), 4)
                self.assertAlmostEqual(float(block['total']), sign * 5.48)
                for period in range(1, periods + 1):
                    self.assertEqual(block['P%s' % period]['quantity'], 3)
                    self.assertEqual(float(block['P%s' % period]['price_unit_multi']), 0.217654321)
                view = ns(
                    compl_info=restored, showing_periods=report.get_matrix_show_periods(pol),
                    iva_column=True, header_multi=0, number_of_columns=periods + 1,
                    last_row='compl', bosocial_lines=[], altres_lines=[], donatiu_lines=[],
                    iese_lines=[], lloguer_lines=[], iva_lines=[], igic_lines=[])
                output = template.render_unicode(
                    id=view, _=lambda value: value,
                    formatLang=lambda value, digits=2: u'%.*f' % (digits, value))
                rows = html.fromstring(u'<table>%s</table>' % output).xpath('./tr')
                self.assertEqual(len(rows), 7)
                self.assertIn(u'Potència [kW]', rows[0].text_content())
                self.assertEqual([cell.text_content().strip()
                                  for cell in rows[0].xpath('./td')[2:periods + 2]],
                                 ['3.00'] * periods)
                self.assertEqual(rows[2].xpath('./td')[periods + 1].text_content().strip(),
                                 u'5.48 €' if sign > 0 else u'-5.48 €')
                self.assertEqual(lines, original)

    def test_power_source_quantity_units_tax_and_prices_still_control_compatibility(self):
        for field, value in (
                ('quantity', 3.000000001), ('uos_id', Record(id=5, name='W')),
                ('invoice_line_tax_id', [Record(id=10, name='IVA 10')]),
                ('product_id', Record(id=42, name='P2')),
                ('price_unit_multi', 0.217654322), ('price_tolls', 0.001000001),
                ('price_charges', 0.002000001)):
            report, fact, pol, lines = source_fixture(6, 'potencia')
            lines[7][field] = value
            data = report.get_sub_component_expedient_data(fact, pol, lines)
            self.assertEqual(len(data['energy_lines_data']), 3, field)
        report, fact, pol, lines = source_fixture(concept='potencia')
        fact.pool['giscedata.facturacio.importacio.linia'].rows.append(
            Record(id=2, num_expedient='ABC/1234567891/ZZZ', type_factura='C'))
        data = report.get_sub_component_expedient_data(fact, pol, lines)
        self.assertEqual(len(data['energy_lines_data']), 4)
        self.assertNotIn('original_energy_lines_data', data)

    def test_power_temporal_basis_changes_or_unknowns_refuse_fusion(self):
        for field, value in (
                ('multi', 8), ('multi', 4.000000001), ('multi', 0),
                ('uom_multi_id', Record(id=3, name='Months')), ('uom_multi_id', False)):
            report, fact, pol, lines = source_fixture(concept='potencia')
            lines[4][field] = value
            data = report.get_sub_component_expedient_data(fact, pol, lines)
            self.assertEqual(len(data['energy_lines_data']), 3, (field, value))

    def test_hidden_power_quantities_and_duplicate_sources_refuse_fusion(self):
        report, fact, pol, lines = source_fixture(concept='potencia')
        duplicate = deepcopy(lines[0])
        lines[0]['quantity'] = 1
        duplicate['quantity'] = 2
        duplicate['id'] = 100
        lines.append(duplicate)
        data = report.get_sub_component_expedient_data(fact, pol, lines)
        self.assertEqual(len(data['energy_lines_data']), 2)
        self.assertEqual(data['energy_lines_data'][0]['P1']['quantity'], 3)
        # Even identical duplicate powers in every date group are uncertain:
        # do not invent a single source power from legacy aggregated quantities.
        report, fact, pol, lines = source_fixture(concept='potencia')
        for line in list(lines):
            if line.product_id.name == 'P1':
                line['quantity'] = 1.5
                duplicate = deepcopy(line)
                duplicate['id'] += 100
                lines.append(duplicate)
        data = report.get_sub_component_expedient_data(fact, pol, lines)
        self.assertEqual(len(data['energy_lines_data']), 4)

    def test_real_power_source_keeps_kw_when_four_blocks_merge(self):
        report, fact, pol, lines = source_fixture(concept='potencia')
        original = deepcopy(lines)
        data = report.get_sub_component_expedient_data(fact, pol, lines)
        blocks = data['energy_lines_data']
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]['P1']['quantity'], 3)
        self.assertEqual(blocks[0]['data_inici'], '2025-07-03')
        self.assertEqual(blocks[0]['data_fi'], '2025-07-18')
        self.assertAlmostEqual(blocks[0]['total'], 5.48)
        self.assertAlmostEqual(blocks[0]['P1']['tolls'], 0.012)
        self.assertAlmostEqual(blocks[0]['P1']['charges'], 0.024)
        self.assertEqual(data['original_energy_lines_data'],
                         synthetic_blocks(concept='potencia'))
        self.assertEqual(lines, original)

    def test_merged_payload_survives_real_report_serialization(self):
        report, fact, pol, lines = source_fixture()
        original = deepcopy(lines)
        data = report.get_sub_component_expedient_data(fact, pol, lines)
        report.get_sub_component_invoice_details_td_other_concepts_data = (
            lambda fact, pol: dict(compl_info=data))
        chart = report.get_component_amount_destination_td_data(fact, pol)
        cleanup_calls = []
        report.cleanup_data = lambda fact: cleanup_calls.append(fact.id)
        result = report.fill_all_components_data(
            {'other': report.get_sub_component_invoice_details_td_other_concepts_data},
            fact, pol, {})
        restored = result['other']['compl_info']
        blocks = restored['energy_lines_data']
        self.assertEqual(type(data['energy_lines_data']), list)
        self.assertEqual(type(data['energy_lines_data'][0]), dict)
        self.assertEqual(type(data['original_energy_lines_data']), list)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]['data_inici'], '2025-07-03')
        self.assertEqual(blocks[0]['data_fi'], '2025-07-18')
        self.assertEqual(blocks[0]['P1']['quantity'], 8)
        self.assertAlmostEqual(float(blocks[0]['total']), 5.48)
        self.assertAlmostEqual(float(blocks[0]['P1']['price_subtotal']), 5.48 / 3)
        self.assertEqual(len(restored['original_energy_lines_data']), 4)
        report.get_sub_component_invoice_details_td_other_concepts_data = (
            lambda fact, pol: dict(compl_info=restored))
        self.assertEqual(report.get_component_amount_destination_td_data(fact, pol), chart)
        self.assertEqual(chart['pie_tolls'], 0)
        self.assertEqual(chart['pie_charges'], 0.12)
        self.assertEqual(chart['pie_energy'], 49.88)
        self.assertEqual(chart['pie_total'], 50)
        self.assertEqual(cleanup_calls, [fact.id, fact.id])
        data['energy_lines_data'][0]['P1']['quantity'] = 999
        self.assertEqual(data['original_energy_lines_data'][0]['P1']['quantity'], 2)
        self.assertEqual(lines, original)

    def test_source_construction_baseline(self):
        report, fact, pol, lines = source_fixture()
        result = report.get_sub_component_expedient_data(fact, pol, lines)
        self.assertEqual(result['expedient'], 'ABC/1234567890/ZZZ')
        self.assertEqual(result['tipus'], '06')
        self.assertAlmostEqual(sum(b['total'] for b in result['energy_lines_data']), 5.48)
        self.assertEqual(set(result), set(['expedient', 'tipus', 'energy_lines_data',
                                           'original_energy_lines_data']))
        self.assertEqual(result['original_energy_lines_data'], synthetic_blocks())

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
        data['energy_lines_data'] = data.pop('original_energy_lines_data')
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
        report.cleanup_data = lambda fact: None
        result = report.fill_all_components_data(
            {'other': report.get_sub_component_invoice_details_td_other_concepts_data},
            fact, pol, {})
        restored = result['other']['compl_info']
        self.assertEqual(len(restored['energy_lines_data']), 1)
        self.assertAlmostEqual(float(restored['energy_lines_data'][0]['total']), -5.48)
        self.assertEqual(restored['energy_lines_data'][0]['P6']['quantity'], 8)
        self.assertEqual(len(restored['original_energy_lines_data']), 4)
        report.get_sub_component_invoice_details_td_other_concepts_data = (
            lambda fact, pol: dict(compl_info=restored))
        self.assertEqual(report.get_component_amount_destination_td_data(fact, pol), chart)
        data['energy_lines_data'] = data.pop('original_energy_lines_data')
        report.get_sub_component_invoice_details_td_other_concepts_data = (
            lambda fact, pol: dict(compl_info=data))
        self.assertEqual(report.get_component_amount_destination_td_data(fact, pol), chart)
        self.assertEqual(lines, original)

    def test_unmerged_six_period_payload_survives_real_report_serialization(self):
        report, fact, pol, lines = source_fixture(6)
        fact.pool['giscedata.facturacio.importacio.linia.factura'].rows = []
        data = report.get_sub_component_expedient_data(fact, pol, lines)
        self.assertEqual(set(data), set(['expedient', 'tipus', 'energy_lines_data']))
        self.assertEqual(data['energy_lines_data'], synthetic_blocks(6))
        report.get_sub_component_invoice_details_td_other_concepts_data = (
            lambda fact, pol: dict(compl_info=data))
        chart = report.get_component_amount_destination_td_data(fact, pol)
        report.cleanup_data = lambda fact: None
        result = report.fill_all_components_data(
            {'other': report.get_sub_component_invoice_details_td_other_concepts_data},
            fact, pol, {})
        restored = result['other']['compl_info']
        self.assertEqual(set(restored), set(data))
        self.assertEqual(len(restored['energy_lines_data']), 4)
        self.assertEqual(restored['energy_lines_data'][0]['P6']['quantity'], 2)
        self.assertAlmostEqual(sum(float(b['total']) for b in restored['energy_lines_data']),
                               5.48)
        report.get_sub_component_invoice_details_td_other_concepts_data = (
            lambda fact, pol: dict(compl_info=restored))
        self.assertEqual(report.get_component_amount_destination_td_data(fact, pol), chart)
        self.assertEqual(chart['pie_charges'], 0.24)

    def test_unmerged_public_dictionaries_are_unchanged(self):
        report, fact, pol, lines = source_fixture()
        # No safe F1 type: legacy fallback remains 11, no speculative fusion.
        fact.pool['giscedata.facturacio.importacio.linia.factura'].rows = []
        result = report.get_sub_component_expedient_data(fact, pol, lines)
        self.assertEqual(result, dict(expedient='ABC/1234567890/ZZZ', tipus='11',
                                      energy_lines_data=synthetic_blocks()))


if __name__ == '__main__':
    unittest.main()
