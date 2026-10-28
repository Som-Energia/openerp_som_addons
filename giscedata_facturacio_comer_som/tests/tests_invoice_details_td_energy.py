# -*- coding: utf-8 -*-
"""Database-free behavioral tests of the production energy detail template."""
import os
import unittest

from lxml import html
from mako.template import Template


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
        cls.template = Template(filename=template_path, input_encoding='utf-8')

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
