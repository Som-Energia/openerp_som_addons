# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from datetime import date

import mock
from destral import testing
from destral.transaction import Transaction
from giscedata_facturacio.report.utils import get_atr_price
from som_indexada.utils import get_preus as get_indexed_preus
from som_indexada.utils import calculate_new_indexed_prices
from som_indexada.taxes import get_simplified_taxes


BACKEND_MODULE = 'som_polissa_condicions_generals.report_backend_mailcanvipreus'


class TestReportBackendMailcanvipreus(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.addCleanup(self.txn.stop)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pol_obj = self.openerp.pool.get('giscedata.polissa')
        self.backend = self.openerp.pool.get('report.backend.mailcanvipreus.pdf')
        imd_obj = self.openerp.pool.get('ir.model.data')
        self.pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_tarifa_018'
        )[1]
        conf_obj = self.openerp.pool.get('res.config')
        conf_obj.set(self.cursor, self.uid, 'serveis_ajust_estimated_kwh_price', '0')
        conf_obj.set(
            self.cursor, self.uid, 'som_indexada_consum_tipus',
            "{'2.0TD': {'preu_sense_F': 100}}",
        )
        tax_obj = self.openerp.pool.get('account.tax')
        for key, name in [
                ('default_iva_21_tax_id', 'IVA 21%'),
                ('default_iese_tax_id', 'Impuesto especial sobre la electricidad')]:
            tax_id = tax_obj.search(self.cursor, self.uid, [('name', '=', name)])[0]
            conf_obj.set(self.cursor, self.uid, key, str(tax_id))

        for target, value in [
            (BACKEND_MODULE + '.get_atr_price', (1.0, 0)),
            ('som_indexada.utils.get_atr_price', (1.0, 0)),
        ]:
            patcher = mock.patch(target, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

        for obj, method, value in [
            (self.pol_obj, 'get_simplified_taxes', {'IVA': 0.21, 'IE': 0.0511}),
            (self.backend, 'get_bo_social_price', 2.0),
            (self.backend, 'get_text_legal', ''),
            (self.backend, 'has_gurb', []),
        ]:
            patcher = mock.patch.object(obj, method, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _check_draft_get_data(self, mode):
        self.pol_obj.write(
            self.cursor, self.uid, self.pol_id, {'mode_facturacio': mode}
        )
        pol = self.pol_obj.browse(self.cursor, self.uid, self.pol_id)
        self.assertEqual(pol.state, 'esborrany')
        self.assertFalse(pol.modcontractuals_ids)

        result = self.backend.get_data(
            self.cursor, self.uid, self.pol_id,
            context={'avoid_formatting': True},
        )

        self.assertIs(result['modcon'], False)
        self.assertEqual(result['mode_facturacio'], mode)
        self.assertEqual(result['preus_antics']['te']['P1'], 1.0)
        self.assertEqual(result['preus_nous']['tp']['P1'], 1.0)
        self.assertGreater(result['preu_nou'], 0)
        pol = self.pol_obj.browse(self.cursor, self.uid, self.pol_id)
        self.assertEqual(pol.state, 'esborrany')
        self.assertFalse(pol.modcontractuals_ids)

    def test_get_data_draft_without_modcon_atr(self):
        self._check_draft_get_data('atr')

    def test_get_data_draft_without_modcon_index(self):
        self._check_draft_get_data('index')

    def _get_policy(self, mode, pending_mode=None):
        pol = mock.Mock()
        pol.llista_preu.id = 30
        pol.mode_facturacio = mode
        pol.tarifa.get_periodes.return_value = {'P1': 1}
        pol.modcontractuals_ids = []
        if pending_mode:
            pending = mock.Mock(state='pendent', mode_facturacio=pending_mode)
            pending.llista_preu.id = 20
            active = mock.Mock(state='actiu', mode_facturacio=mode)
            active.llista_preu.id = 10
            pol.modcontractuals_ids = [pending, active]
        return pol

    def _check_pricelist(self, mode, pending_mode, expected):
        pol = self._get_policy(mode, pending_mode)
        for get_prices in [self.backend.get_preus, get_indexed_preus]:
            context = {}
            get_prices(self.cursor, self.uid, pol, context=context)
            selected = 30 if get_prices is get_indexed_preus and expected is None else expected
            self.assertEqual(context.get('force_pricelist'), selected)

        context = {'potencia_anual': True}
        total = self.backend.calcularPreuTotal(
            self.cursor, self.uid, pol, {'P1': 3}, {'P1': 2},
            afegir_servei_ajust=False, bo_social_separat=False,
            context=context,
        )
        self.assertEqual(total, 5.0)
        self.assertEqual(context.get('force_pricelist'), expected)

    def test_prices_without_modcon_use_policy_pricelist(self):
        for mode in ['atr', 'index']:
            self._check_pricelist(mode, None, None)

    def test_prices_pending_index_keep_previous_pricelist(self):
        self._check_pricelist('atr', 'index', 10)

    def test_prices_pending_atr_use_pending_pricelist(self):
        self._check_pricelist('index', 'atr', 20)

    def test_prices_active_modcon_do_not_force_pricelist(self):
        pol = self._get_policy('atr', 'index')
        pol.modcontractuals_ids[0].state = 'actiu'
        for get_prices in [self.backend.get_preus, get_indexed_preus]:
            context = {}
            get_prices(self.cursor, self.uid, pol, context=context)
            if get_prices is get_indexed_preus:
                self.assertEqual(context['force_pricelist'], 30)
            else:
                self.assertNotIn('force_pricelist', context)

    def test_indexed_estimation_with_real_tax_engine_and_social_charge(self):
        tax_obj = self.openerp.pool.get('account.tax')
        conf_obj = self.openerp.pool.get('res.config')
        ie_id = tax_obj.create(self.cursor, self.uid, {
            'name': 'IE estimation code', 'type': 'code', 'amount': 0.4864,
            'python_compute': 'result = price_unit * 0.05', 'factor': 0.1,
            'include_base_amount': True, 'sequence': 1,
        })
        iva_id = tax_obj.create(self.cursor, self.uid, {
            'name': 'IVA estimation 5%', 'type': 'percent', 'amount': 0.05,
            'sequence': 2,
        })
        conf_obj.set(self.cursor, self.uid, 'default_iese_tax_id', str(ie_id))
        conf_obj.set(self.cursor, self.uid, 'default_iva_21_tax_id', str(iva_id))
        conf_obj.set(self.cursor, self.uid, 'invoice_active_bo_social', '1')
        conf_obj.set(self.cursor, self.uid, 'invoice_start_date_bo_social', '2020-01-01')
        conf_obj.set(self.cursor, self.uid, 'giscedata_exclude_tariff_apply_bo_social', '[]')
        imd_obj = self.openerp.pool.get('ir.model.data')
        social_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_repercusio_bo_social', 'bosocial_BS01'
        )[1]
        self.openerp.pool.get('product.product').write(
            self.cursor, self.uid, social_id, {'taxes_id': [(6, 0, [iva_id])]}
        )
        self.pol_obj.write(
            self.cursor, self.uid, self.pol_id,
            {'mode_facturacio': 'index', 'fiscal_position_id': False}
        )
        pol = self.pol_obj.browse(self.cursor, self.uid, self.pol_id)
        for factor in [0.1, 0]:
            tax_obj.write(self.cursor, self.uid, ie_id, {'factor': factor})
            with mock.patch('som_indexada.utils.get_preus', side_effect=[
                    {'factor_k': 0.005, 'tp': {}}, {'factor_k': 0.007, 'tp': {}}]), \
                    mock.patch('som_indexada.utils.get_fs_from_k_change', return_value={}), \
                    mock.patch.object(self.openerp.pool.get('product.pricelist'),
                                      'price_get', return_value={pol.llista_preu.id: 0.02}):
                result = calculate_new_indexed_prices(self.cursor, self.uid, pol)
            energy = result['import_energia_anual_nova']
            self.assertAlmostEqual(result['import_bo_social_anual_nova'], 7.3)
            self.assertAlmostEqual(result['import_total_anual_nova'], energy + 7.3)
            self.assertAlmostEqual(result['ie'], 5 * factor, places=3)
            self.assertAlmostEqual(result['iva'], 5, places=3)
            self.assertAlmostEqual(
                result['import_total_anual_nova_amb_impost'],
                energy * (1 + 0.05 * factor) * 1.05 + 7.3 * 1.05, places=4
            )

    def test_indexed_estimation_after_automatic_renewal_without_future_modcon(self):
        year = date.today().year
        self.pol_obj.write(self.cursor, self.uid, self.pol_id, {
            'mode_facturacio': 'index', 'renovacio_auto': True,
        })
        self.pol_obj.send_signal(
            self.cursor, self.uid, [self.pol_id], ['validar', 'contracte']
        )
        pol = self.pol_obj.browse(self.cursor, self.uid, self.pol_id)
        modcon_obj = self.openerp.pool.get('giscedata.polissa.modcontractual')
        modcon_obj.write(self.cursor, self.uid, pol.modcontractual_activa.id, {
            'data_inici': '{}-01-01'.format(year),
            'data_final': '{}-12-31'.format(year),
        })
        pol = self.pol_obj.browse(self.cursor, self.uid, self.pol_id)
        original_modcons = [modcon.id for modcon in pol.modcontractuals_ids]
        self.openerp.pool.get('giscedata.cups.ps').write(
            self.cursor, self.uid, pol.cups.id, {'conany_kwh': 1000}
        )
        conf_obj = self.openerp.pool.get('res.config')
        conf_obj.set(self.cursor, self.uid, 'invoice_active_bo_social', '1')
        conf_obj.set(self.cursor, self.uid, 'invoice_start_date_bo_social', '2020-01-01')
        conf_obj.set(self.cursor, self.uid, 'giscedata_exclude_tariff_apply_bo_social', '[]')
        imd_obj = self.openerp.pool.get('ir.model.data')
        factor_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_indexada', 'product_factor_k'
        )[1]
        social_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_repercusio_bo_social', 'bosocial_BS01'
        )[1]
        contexts = []

        def price_get(cursor, uid, pricelist_ids, product_id, *args, **kwargs):
            ctx = kwargs.get('context', args[-1] if isinstance(args[-1], dict) else {})
            contexts.append(dict(ctx))
            self.assertEqual(pricelist_ids, [pol.llista_preu.id])
            future = ctx['date'] > '{}-12-31'.format(year)
            if product_id == factor_id:
                price = 0.007 if future else 0.005
            elif product_id == social_id:
                price = 0.02 if future else 0.01
            else:
                price = 20 if future else 10
            return {pol.llista_preu.id: price}

        with mock.patch('som_indexada.utils.date') as clock, \
                mock.patch('som_indexada.utils.get_atr_price', wraps=get_atr_price), \
                mock.patch('som_indexada.utils.get_fs_from_k_change', return_value={}), \
                mock.patch.object(self.openerp.pool.get('product.pricelist'),
                                  'price_get', side_effect=price_get):
            # Keep the existing +60-day horizon and land exactly on January 1.
            clock.today.return_value = date(year, 11, 2)
            result = calculate_new_indexed_prices(self.cursor, self.uid, pol)
        self.assertAlmostEqual(result['import_energia_anual_antiga'], 105.075)
        self.assertAlmostEqual(result['import_energia_anual_nova'], 107.105)
        self.assertAlmostEqual(result['import_bo_social_anual_antiga'], 3.65)
        self.assertAlmostEqual(result['import_bo_social_anual_nova'], 7.3)
        self.assertAlmostEqual(
            result['import_potencia_anual_nova'],
            result['import_potencia_anual_antiga'] * 2
        )
        self.assertTrue(any(ctx['date'] == '{}-01-01'.format(year + 1) for ctx in contexts))
        self.assertGreater(
            result['import_total_anual_nova_amb_impost'], result['import_total_anual_nova']
        )
        self.assertEqual(
            [modcon.id for modcon in
             self.pol_obj.browse(self.cursor, self.uid, self.pol_id).modcontractuals_ids],
            original_modcons
        )

    def test_period_report_with_generation_without_future_modcon(self):
        year = date.today().year
        future_date = '{}-01-01'.format(year + 1)
        self.pol_obj.write(self.cursor, self.uid, self.pol_id, {
            'mode_facturacio': 'atr', 'renovacio_auto': True,
        })
        self.pol_obj.send_signal(
            self.cursor, self.uid, [self.pol_id], ['validar', 'contracte']
        )
        pol = self.pol_obj.browse(self.cursor, self.uid, self.pol_id)
        self.openerp.pool.get('giscedata.polissa.modcontractual').write(
            self.cursor, self.uid, pol.modcontractual_activa.id, {
                'data_inici': '{}-01-01'.format(year),
                'data_final': '{}-12-31'.format(year),
            }
        )
        imd_obj = self.openerp.pool.get('ir.model.data')
        member_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
        )[1]
        self.openerp.pool.get('generationkwh.assignment').create(
            self.cursor, self.uid, {
                'contract_id': self.pol_id, 'member_id': member_id, 'priority': 1,
            }
        )
        pol = self.pol_obj.browse(self.cursor, self.uid, self.pol_id)
        self.assertTrue(pol.te_assignacio_gkwh)
        original_modcons = [modcon.id for modcon in pol.modcontractuals_ids]
        line = mock.Mock()
        line.factura_id.tarifa_acces_id = pol.tarifa
        line.factura_id.invoice_id.date_invoice = date.today().strftime('%Y-%m-%d')
        line.factura_id.type = 'out_invoice'
        line.factura_line_id.product_id.name = 'P1'
        line.factura_line_id.quantity = 10
        context = {
            'avoid_formatting': True, 'lang': 'ca_ES', 'force_pricelist': pol.llista_preu.id,
        }

        def price_get(cursor, uid, policy, period, kind, context, with_taxes=False):
            return (2.0 if context['date'] >= future_date else 1.0, 0)

        def real_taxes(cursor, uid, pol_id, context=None):
            return get_simplified_taxes(cursor, uid, self.pol_obj, pol_id, context=context)

        owner_obj = self.openerp.pool.get('generationkwh.invoice.line.owner')
        with mock.patch(BACKEND_MODULE + '.date') as clock, \
                mock.patch(BACKEND_MODULE + '.get_atr_price', side_effect=price_get), \
                mock.patch.object(self.backend, 'get_price_change_date',
                                  return_value=future_date), \
                mock.patch.object(self.pol_obj, 'get_simplified_taxes',
                                  side_effect=real_taxes), \
                mock.patch.object(self.pol_obj, 'get_generationkwh_use',
                                  wraps=self.pol_obj.get_generationkwh_use) as use, \
                mock.patch.object(owner_obj, 'browse', return_value=[line]):
            clock.today.return_value = date(year, 11, 2)
            result = self.backend.get_data(self.cursor, self.uid, self.pol_id, context=context)

        estimation = result['gkwh_estimation']
        self.assertEqual(estimation['origen'], 'partial_data')
        self.assertEqual(estimation['consum_total'], 120)
        self.assertEqual(estimation['preu_vell'], 120)
        self.assertEqual(estimation['preu_nou'], 240)
        self.assertEqual(result['preus_nous_generation']['P1'], 2)
        self.assertNotIn('date', use.call_args[1]['context'])
        self.assertEqual(use.call_args[1]['context']['lang'], 'ca_ES')
        self.assertEqual(use.call_args[1]['context']['force_pricelist'], pol.llista_preu.id)
        self.assertNotIn('date', context)
        self.assertEqual(
            [modcon.id for modcon in
             self.pol_obj.browse(self.cursor, self.uid, self.pol_id).modcontractuals_ids],
            original_modcons
        )

    def test_generation_without_history_does_not_change_pricing_context(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.pol_id)
        for context in [None, False, {'date': '2027-01-01', 'lang': 'ca_ES'}]:
            original_context = dict(context or {})
            with mock.patch.object(self.pol_obj, 'generationkwh_anual_estimation',
                                   return_value=(False, 'no_data')) as estimate, \
                    mock.patch.object(self.backend, 'calcularPreuTotal') as prices:
                result = self.backend.get_gkwh_estimation(
                    self.cursor, self.uid, pol, context=context
                )
            self.assertEqual(result['gkwh_estimation']['origen'], 'no_data')
            self.assertIs(result['gkwh_estimation']['preu_nou'], False)
            expected_context = dict(original_context)
            expected_context.pop('date', None)
            estimate.assert_called_once_with(
                self.cursor, self.uid, self.pol_id, context=expected_context
            )
            self.assertFalse(prices.called)
            self.assertEqual(context or {}, original_context)
