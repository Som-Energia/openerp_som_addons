# -*- coding: utf-8 -*-
"""Database-free behavioral tests of the production energy detail template."""
from __future__ import absolute_import
import ast
from copy import deepcopy
import os
import unittest

import cssutils
from lxml import html
from lxml.cssselect import CSSSelector
from mako.lookup import TemplateLookup
from mako.template import Template
from yamlns import namespace as ns


class ComponentData(dict):
    __getattr__ = dict.__getitem__


class TestsInvoiceDetailsTdEnergy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        addon_path = os.path.dirname(os.path.dirname(__file__))
        template_path = os.path.join(
            addon_path, 'report', 'components', 'invoice_details_td_energy',
            'invoice_details_td_energy.mako',
        )
        cls.lookup = TemplateLookup(
            directories=[os.path.dirname(addon_path)], input_encoding='utf-8')
        cls.template = Template(filename=template_path, input_encoding='utf-8',
                                lookup=cls.lookup)
        cls.composed_template = Template(
            text=u'<table id="invoice_detail_td">'
            '<%include file="/giscedata_facturacio_comer_som/report/components/'
            'invoice_details_td_energy/invoice_details_td_energy.mako" args="id=id.energy"/>'
            '<%include file="/giscedata_facturacio_comer_som/report/components/'
            'invoice_details_td_other_concepts/invoice_details_td_other_concepts.mako" '
            'args="id=id.other_concepts"/></table>',
            lookup=cls.lookup, input_encoding='utf-8')
        cls.stylesheet = cssutils.parseFile(os.path.join(
            addon_path, 'report', 'components', 'invoice_details_td', 'invoice_details_td.css'))

    def composed_data(self, periods=3, tax=False, ordinary=False,
                      complementary=True, adjustment=True, generation=False,
                      amount=7.43, reactive_last=False, donation=True,
                      final_concept='energia', block_count=2):
        """Run the actual aggregator with synthetic prepared component boundaries."""
        addon_path = os.path.dirname(os.path.dirname(__file__))
        with open(os.path.join(addon_path, 'giscedata_facturacio_report.py')) as source:
            tree = ast.parse(source.read())
        report_class = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                            and node.name == 'GiscedataFacturacioFacturaReport')
        method = next(node for node in report_class.body if isinstance(node, ast.FunctionDef)
                      and node.name == 'get_component_invoice_details_td_data')
        selected = ast.parse('class Report(object):\n    pass\n')
        selected.body[0].body = [method]
        namespace = dict(is_TD=lambda pol: True, has_iva_column=lambda fact: tax)
        exec(compile(selected, '<production invoice details aggregator>', 'exec'), namespace)
        report = namespace['Report']()
        # All unrelated components share one inert boundary; energy/other data
        # are concrete prepared values. Routing itself executes production code.
        for node in ast.walk(method):
            if isinstance(node, ast.Attribute) and node.attr.startswith('get_sub_component_'):
                setattr(report, node.attr, lambda *args: dict(is_visible=False))
        showing_periods = ['P%s' % period for period in range(1, periods + 1)]
        energy = dict(
            showing_periods=showing_periods, iva_column=tax,
            energy_lines_data=[dict(self.energy_data())] if ordinary else [],
            auvi_energy_lines_data=[], mag_line_data=False, indexed=False,
            adjustment_services=dict(total=amount, iva='21%',
                                     is_generation_adjustment=generation) if adjustment else None,
            header_multi=3 * int(ordinary) + int(adjustment))
        blocks = []
        if complementary is True:
            dates = [('2025-08-03', '2025-08-06'), ('2025-08-07', '2025-08-10')]
            for start, end in dates[:block_count]:
                blocks.append(dict(
                    type='energia', units='kWh', data_inici=start, data_fi=end,
                    total=2.71, iva='21%', P1=dict(
                        quantity=13, price_unit_multi=0.20846, price_subtotal=2.71,
                        price_tolls=0.014, tolls=0.182,
                        price_charges=0.019, charges=0.247)))
        if blocks:
            concept = 'reactiva' if reactive_last else final_concept
            blocks[-1]['type'] = concept
            blocks[-1]['units'] = {'energia': 'kWh', 'potencia': 'kW', 'reactiva': 'kVArh'}[concept]
        other = dict(
            showing_periods=showing_periods, iva_column=tax, number_of_columns=periods + 1,
            header_multi=int(donation), last_row='donatiu' if donation else 'compl',
            bosocial_lines=[], altres_lines=[],
            donatiu_lines=[dict(quantity=13, price_unit_multi=0.007,
                                price_subtotal=0.091)] if donation else [],
            iese_lines=[], lloguer_lines=[], igic_lines=[],
            iva_lines=[dict(name='Synthetic VAT', base=19.37, amount=4.07,
                            disclaimer_21_to_5=False, disclaimer_21_to_10=False)])
        if complementary is not None:
            other['compl_info'] = dict(
                expedient='ABC/1234567890/ZZZ', tipus='06', energy_lines_data=blocks)
        if complementary == 'hidden':
            other['compl_info'] = False
        calls = []

        def prepared_other(*args):
            calls.append('other_concepts')
            return deepcopy(other)

        report.get_sub_component_invoice_details_td_energy_data = lambda *args: deepcopy(energy)
        report.get_sub_component_invoice_details_td_other_concepts_data = prepared_other
        report.get_matrix_show_periods = lambda pol: showing_periods
        pol = ComponentData(cups=ComponentData(id_provincia=ComponentData(id=1)))
        data = report.get_component_invoice_details_td_data(ComponentData(amount_total=29.41), pol)
        self.assertEqual(calls, ['other_concepts'])
        # Match the real namespace boundary before any template consumes data.
        return ns.loads(ns(data).dump())

    def composed_rows(self, **kwargs):
        data = self.composed_data(**kwargs)
        output = self.composed_template.render_unicode(
            id=data, _=lambda value: value,
            formatLang=lambda value, digits=2: u'%.*f' % (digits, value))
        return data, html.fromstring(output).xpath('./tr')

    def bottom_borders(self, rows):
        """Resolve explicit row borders from real CSS, not browser layout/painting."""
        borders = {}
        table = rows[0].getparent()
        for rule in self.stylesheet.cssRules:
            if rule.type != rule.STYLE_RULE:
                continue
            border = rule.style.getPropertyValue('border-bottom')
            if border:
                for element in CSSSelector(rule.selectorText)(table):
                    borders[element] = border
        return [(index, borders[row]) for index, row in enumerate(rows) if row in borders]

    def test_closing_separator_is_below_deferred_adjustment_not_above(self):
        data, rows = self.composed_rows(donation=False, tax=True)
        self.assertEqual(self.bottom_borders(rows),
                         [(6, '1.8px solid black'), (14, '1.8px solid black')])
        self.assertIn(u'Energia [kWh]', self.cell_text(rows[7]))
        self.assertIn(u"Serveis d'Ajust", self.cell_text(rows[14]))
        self.assertIn('Synthetic VAT', self.cell_text(rows[15]))
        self.assertEqual(data.energy.header_multi, 0)
        self.assert_adjustment(self.logical_rows(rows)[:15], 3, True, standalone=True)

    def test_separator_follows_adjustment_for_each_final_concept_and_layout(self):
        for concept in ('energia', 'potencia', 'reactiva'):
            for periods in (3, 6):
                for tax in (False, True):
                    for ordinary in (False, True):
                        for block_count in (1, 2):
                            data, rows = self.composed_rows(
                                final_concept=concept, block_count=block_count,
                                donation=False, periods=periods, tax=tax, ordinary=ordinary,
                                generation=periods == 6,
                                amount=-2.19 if periods == 6 else 7.43)
                            offset = 3 * int(ordinary)
                            final_rows = 3 if concept == 'reactiva' else 7
                            index = offset + 7 * (block_count - 1) + final_rows
                            expected = [(index, '1.8px solid black')]
                            if block_count == 2:
                                expected.insert(0, (offset + 6, '1.8px solid black'))
                            self.assertEqual(self.bottom_borders(rows), expected)
                            texts = [self.cell_text(row) for row in rows]
                            self.assertEqual([i for i, text in enumerate(texts)
                                              if u"Serveis d'Ajust" in text], [index])
                            self.assertIn('Synthetic VAT', texts[index + 1])
                            logical = self.logical_rows(rows)
                            self.assertEqual([len(row) for row in logical],
                                             [periods + 3 + int(tax)] * len(rows))
                            self.assert_adjustment(
                                logical[:index + 1], periods, tax, standalone=True,
                                generation=periods == 6,
                                total=u'-2.19 €(2)' if periods == 6 else u'7.43 €(2)')
                            self.assertEqual(data.energy.header_multi, offset)

    def test_existing_separators_stay_when_adjustment_is_not_deferred(self):
        for concept in ('energia', 'potencia', 'reactiva'):
            for periods in (3, 6):
                data, rows = self.composed_rows(
                    final_concept=concept, periods=periods,
                    donation=False, adjustment=False, ordinary=True)
                last_index = 3 + 7 + (3 if concept == 'reactiva' else 7) - 1
                self.assertEqual(self.bottom_borders(rows),
                                 [(9, '1.8px solid black'), (last_index, '1.8px solid black')])
                self.assertFalse(data.energy.get('defer_adjustment_services'))
                self.assertIn('Synthetic VAT', self.cell_text(rows[last_index + 1]))
                self.assertEqual([len(row) for row in self.logical_rows(rows)],
                                 [periods + 3] * len(rows))
        for complementary in (None, False, 'hidden'):
            for ordinary in (False, True):
                data, rows = self.composed_rows(
                    complementary=complementary, donation=False, ordinary=ordinary)
                # No complementary border exists to transfer; normal SA is unchanged.
                self.assertEqual(self.bottom_borders(rows), [])
                index = 3 * int(ordinary)
                self.assert_adjustment(self.logical_rows(rows)[:index + 1], 3, False,
                                       standalone=not ordinary)
                self.assertEqual(data.energy.header_multi, index + 1)

    def test_donation_closing_border_is_not_duplicated_on_adjustment(self):
        # last_row=donatiu never gave complementary blocks a closing border.
        # Preserve that policy instead of inventing another separator above donation.
        for concept in ('energia', 'potencia', 'reactiva'):
            for adjustment in (False, True):
                data, rows = self.composed_rows(
                    final_concept=concept, adjustment=adjustment,
                    donation=True, periods=6, tax=True)
                index = 7 + (3 if concept == 'reactiva' else 7) + int(adjustment)
                self.assertEqual(self.bottom_borders(rows), [(index, '1.8px solid black')])
                self.assertIn(u'Donatiu voluntari', self.cell_text(rows[index]))
                self.assertIn('Synthetic VAT', self.cell_text(rows[index + 1]))
                if adjustment:
                    self.assertIn(u"Serveis d'Ajust", self.cell_text(rows[index - 1]))
                    self.assert_adjustment(self.logical_rows(rows)[:index], 6, True,
                                           standalone=True)
                self.assertEqual(data.energy.header_multi, 0)

    def test_complementary_adjustment_follows_last_charges_before_donation_and_tax(self):
        data, rows = self.composed_rows(tax=True)
        texts = [self.cell_text(row) for row in rows]
        adjustment_index = next(i for i, text in enumerate(texts) if u"Serveis d'Ajust" in text)
        charges_index = max(i for i, text in enumerate(texts) if u'Càrrecs' in text)
        self.assertEqual(adjustment_index, charges_index + 2)
        self.assertIn(u'Donatiu voluntari', texts[adjustment_index + 1])
        self.assertIn('Synthetic VAT', texts[adjustment_index + 2])
        logical = self.logical_rows(rows)
        self.assert_adjustment(logical[:adjustment_index + 1], 3, True, standalone=True)
        self.assertEqual(data.energy.header_multi, 0)

    def test_deferred_adjustment_matrix_preserves_columns_and_ordinary_rowspan(self):
        for periods in (3, 6):
            for tax in (False, True):
                for ordinary in (False, True):
                    data, rows = self.composed_rows(
                        periods=periods, tax=tax, ordinary=ordinary,
                        generation=periods == 6, amount=-2.19 if periods == 6 else 7.43)
                    logical = self.logical_rows(rows)
                    texts = [self.cell_text(row) for row in rows]
                    indices = [i for i, text in enumerate(texts) if u"Serveis d'Ajust" in text]
                    self.assertEqual(indices, [14 + 3 * int(ordinary)])
                    index = indices[0]
                    self.assertEqual([len(row) for row in logical],
                                     [periods + 3 + int(tax)] * len(rows))
                    self.assert_adjustment(
                        logical[:index + 1], periods, tax, standalone=True,
                        generation=periods == 6,
                        total=u'-2.19 €(2)' if periods == 6 else u'7.43 €(2)')
                    self.assertEqual(len(rows[index].xpath('.//sup[text()="(2)"]')), 1)
                    self.assertEqual(data.energy.header_multi, 3 * int(ordinary))
                    self.assertTrue(data.energy.defer_adjustment_services)
                    self.assertEqual(data.other_concepts.deferred_adjustment_services,
                                     data.energy.adjustment_services)
                    if ordinary:
                        self.assertEqual(logical[0][0].get('rowspan'), '3')
                        self.assert_energy(logical, periods, tax)
                    self.assertIn(u'Donatiu voluntari', texts[index + 1])
                    self.assertIn('Synthetic VAT', texts[index + 2])

    def test_without_rendered_complementary_blocks_adjustment_keeps_original_position(self):
        # Absent info, empty block list, and explicitly hidden info render no blocks.
        for complementary in (None, False, 'hidden'):
            for ordinary in (False, True):
                for tax in (False, True):
                    for periods in (3, 6):
                        data, rows = self.composed_rows(
                            complementary=complementary, ordinary=ordinary,
                            tax=tax, periods=periods)
                        texts = [self.cell_text(row) for row in rows]
                        index = 3 * int(ordinary)
                        self.assertEqual(
                            [i for i, text in enumerate(texts) if u"Serveis d'Ajust" in text],
                            [index])
                        logical = self.logical_rows(rows)
                        self.assert_adjustment(logical[:index + 1], periods, tax,
                                               standalone=not ordinary)
                        self.assertFalse(data.energy.get('defer_adjustment_services'))
                        self.assertNotIn('deferred_adjustment_services', data.other_concepts)
                        self.assertEqual(data.energy.header_multi, index + 1)
                        self.assertIn(u'Donatiu voluntari', texts[index + 1])
                        self.assertIn('Synthetic VAT', texts[index + 2])

    def test_no_adjustment_does_not_add_a_deferred_row(self):
        for complementary in (True, False, None):
            data, rows = self.composed_rows(
                complementary=complementary, adjustment=False, ordinary=True, tax=True)
            texts = [self.cell_text(row) for row in rows]
            self.assertEqual([text for text in texts if u"Serveis d'Ajust" in text], [])
            self.assertEqual(len(rows), 19 if complementary else 5)
            self.assertEqual(data.energy.header_multi, 3)
            self.assertNotIn('deferred_adjustment_services', data.other_concepts)
            logical = self.logical_rows(rows)
            self.assertEqual([len(row) for row in logical], [7] * len(rows))
            self.assert_energy(logical, 3, True)

    def test_adjustment_follows_final_reactive_block_without_tolls_or_charges(self):
        data, rows = self.composed_rows(reactive_last=True, periods=6, tax=True)
        texts = [self.cell_text(row) for row in rows]
        self.assertIn(u'Energia reactiva', texts[7])
        self.assertIn(u"Serveis d'Ajust", texts[10])
        self.assertIn(u'Donatiu voluntari', texts[11])
        self.assertTrue(data.energy.defer_adjustment_services)
        logical = self.logical_rows(rows)
        self.assert_adjustment(logical[:11], 6, True, standalone=True)

    def energy_data(self, auvi=False, discount=False):
        period = 'Linia energia autoconsumida P1' if auvi else 'P1'
        return ComponentData({
            period: {'quantity': 20.0, 'price_unit_multi': 0.175,
                     'price_subtotal': 3.50},
            'origin': u'real', 'date_from': '04/02/2025',
            'date_to': '19/02/2025', 'total': 3.50, 'iva': '21%',
            'has_discount': discount,
        })

    def render_rows(self, periods=3, tax=False, energy=None, auvi=None,
                    adjustment=None, indexed=False):
        energy = energy or []
        auvi = auvi or []
        data = ComponentData(
            showing_periods=['P%s' % p for p in range(1, periods + 1)],
            iva_column=tax, energy_lines_data=energy,
            auvi_energy_lines_data=auvi, mag_line_data=False,
            adjustment_services=adjustment, indexed=indexed,
            header_multi=3 * (len(energy) + len(auvi)) + bool(adjustment),
        )
        output = self.template.render_unicode(
            id=data, _=lambda value: value,
            formatLang=lambda value, digits=2: u'%.*f' % (digits, value),
        )
        return html.fromstring(u'<table>%s</table>' % output).xpath('./tr')

    def logical_rows(self, rows):
        """Expand both spans, retaining the cell occupying each column."""
        occupied = {}
        result = []
        for row_index, row in enumerate(rows):
            column = 0
            for cell in row.xpath('./td'):
                while (row_index, column) in occupied:
                    column += 1
                colspan = int(cell.get('colspan', 1))
                rowspan = int(cell.get('rowspan', 1))
                for row_offset in range(rowspan):
                    for column_offset in range(colspan):
                        position = (row_index + row_offset,
                                    column + column_offset)
                        self.assertNotIn(position, occupied)
                        occupied[position] = cell
                column += colspan
            columns = sorted(col for row_number, col in occupied
                             if row_number == row_index)
            self.assertEqual(columns, list(range(len(columns))))
            result.append([occupied[row_index, col] for col in columns])
        return result

    def cell_text(self, cell):
        return u' '.join(cell.text_content().split())

    def assert_energy(self, rows, periods, tax, start=0, auvi=False):
        self.assertEqual(self.cell_text(rows[start][2]), '20')
        self.assertEqual(self.cell_text(rows[start + 1][2]), '0.175')
        subtotal = '3.5' if auvi else u'3.50 €'
        self.assertEqual(self.cell_text(rows[start + 2][2]), subtotal)
        self.assertEqual(self.cell_text(rows[start + 2][periods + 2]),
                         u'3.50 €')
        if tax:
            self.assertEqual(self.cell_text(rows[start + 2][-1]), '21%')

    def test_ordinary_energy_baseline(self):
        rows = self.logical_rows(self.render_rows(
            tax=True, energy=[self.energy_data()],
        ))
        self.assertEqual(len(rows), 3)
        self.assertEqual([len(row) for row in rows], [7, 7, 7])
        self.assert_energy(rows, 3, True)

    def assert_adjustment(self, rows, periods, tax, total=u'7.43 €(2)',
                          tax_rate='21%', standalone=False, generation=False):
        self.assertEqual([len(row) for row in rows],
                         [periods + 3 + int(tax)] * len(rows))
        adjustment_row = rows[-1]
        description = u"Serveis d'Ajust segons preu REE pel periode facturat"
        if generation:
            description += u', aplicat a assignació GenerationkWh'
        self.assertEqual(self.cell_text(adjustment_row[1]), description)
        if standalone:
            self.assertIs(adjustment_row[0], adjustment_row[1])
        else:
            self.assertEqual(self.cell_text(adjustment_row[0]),
                             u'Facturació per electricitat utilitzada')
            self.assertIs(adjustment_row[0], rows[0][0])
        self.assertEqual([self.cell_text(cell)
                          for cell in adjustment_row[2:periods + 2]],
                         [''] * periods)
        self.assertEqual(self.cell_text(adjustment_row[periods + 2]), total)
        if tax:
            self.assertEqual(self.cell_text(adjustment_row[periods + 3]),
                             tax_rate)

    def test_standalone_adjustment_without_tax(self):
        rows = self.logical_rows(self.render_rows(
            adjustment=ComponentData(total=7.43, iva='21%'),
        ))
        self.assertEqual(len(rows), 1)
        self.assert_adjustment(rows, 3, False, standalone=True)

    def test_standalone_adjustment_with_tax(self):
        for periods in (3, 6):
            rows = self.logical_rows(self.render_rows(
                periods=periods, tax=True,
                adjustment=ComponentData(total=12.68, iva='10%'),
            ))
            self.assertEqual(len(rows), 1)
            self.assert_adjustment(rows, periods, True, total=u'12.68 €(2)',
                                   tax_rate='10%', standalone=True)

    def test_standalone_generation_adjustment_six_periods_without_tax(self):
        rows = self.logical_rows(self.render_rows(
            periods=6, adjustment=ComponentData(
                total=-2.19, iva='21%', is_generation_adjustment=True,
            ),
        ))
        self.assertEqual(len(rows), 1)
        self.assert_adjustment(rows, 6, False, total=u'-2.19 €(2)',
                               standalone=True, generation=True)

    def check_prior_energy(self, tax, auvi=False, indexed=False,
                           discount=False, mixed=False):
        for periods in (3, 6):
            energy = self.energy_data(discount=discount)
            auvi_energy = self.energy_data(auvi=True, discount=discount)
            regular_lines = [energy] if not auvi or mixed else []
            auvi_lines = [auvi_energy] if auvi or mixed else []
            rows = self.logical_rows(self.render_rows(
                periods=periods, tax=tax, energy=regular_lines,
                auvi=auvi_lines, indexed=indexed,
                adjustment=ComponentData(total=7.43, iva='21%'),
            ))
            self.assertEqual(len(rows), 7 if mixed else 4)
            self.assert_adjustment(rows, periods, tax)
            self.assert_energy(rows, periods, tax, auvi=bool(auvi_lines))
            if mixed:
                self.assert_energy(rows, periods, tax, start=3)
            if indexed:
                self.assertEqual(self.cell_text(rows[1][1]),
                                 u"Preu mitjà de l'energia [€/kWh]")
            if discount:
                self.assertIn(u'subjectes a descompte',
                              self.cell_text(rows[0][1]))

    def test_adjustment_after_ordinary_energy_without_tax(self):
        self.check_prior_energy(tax=False)

    def test_adjustment_after_ordinary_energy_with_tax(self):
        self.check_prior_energy(tax=True)

    def test_adjustment_after_indexed_discounted_energy(self):
        self.check_prior_energy(tax=True, indexed=True, discount=True)

    def test_adjustment_after_auvi_energy_without_tax(self):
        self.check_prior_energy(tax=False, auvi=True)

    def test_adjustment_after_auvi_energy_with_tax(self):
        self.check_prior_energy(tax=True, auvi=True, discount=True)

    def test_adjustment_after_auvi_and_ordinary_energy(self):
        self.check_prior_energy(tax=True, mixed=True)


if __name__ == '__main__':
    unittest.main()
