# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import date, timedelta

import mock
from destral import testing
from destral.transaction import Transaction
from giscedata_facturacio.report.utils import get_comming_atr_price


class TestReportBackendCCPPIgnoreModcon(testing.OOTestCase):
    def get_ref(self, module, ref):
        IrModel = self.openerp.pool.get("ir.model.data")
        return IrModel._get_obj(self.cursor, self.uid, module, ref).id

    def setUp(self):
        self.maxDiff = None
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.pol_obj = self.openerp.pool.get("giscedata.polissa")
        self.tax_obj = self.openerp.pool.get('account.tax')
        self.conf_obj = self.openerp.pool.get('res.config')
        self.backend_obj = self.openerp.pool.get(
            "report.backend.condicions.particulars.ignore.modcon")
        self.pricelist_obj = self.openerp.pool.get("product.pricelist")
        self.wiz_change_to_index_obj = self.openerp.pool.get("wizard.change.to.indexada")
        self.contract_20TD_id = self.get_ref("giscedata_polissa", "polissa_tarifa_018")

    def tearDown(self):
        self.txn.stop()

    def test_get_polissa_data_with_modcon_keeps_current(self):
        self.pol_obj.send_signal(
            self.cursor, self.uid, [self.contract_20TD_id], ["validar", "contracte"])
        context = {"active_id": self.contract_20TD_id, "change_type": "from_period_to_index"}
        wiz_id = self.wiz_change_to_index_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_change_to_index_obj.change_to_indexada(
            self.cursor, self.uid, [wiz_id], context=context)

        pol_20td = self.pol_obj.browse(self.cursor, self.uid, self.contract_20TD_id)

        result = self.backend_obj.get_polissa_data(self.cursor, self.uid, pol_20td, context={})

        pricelist_id = self.get_ref("giscedata_facturacio", "pricelist_tarifas_electricidad_venda")
        pricelist_name = self.pricelist_obj.browse(self.cursor, self.uid, pricelist_id).name

        self.assertEqual(result['pricelist'], pricelist_id)
        self.assertEqual(result['tarifa_mostrar'], pricelist_name)

    def test_get_prices_data_with_keeps_current(self):
        # Get prices data needs this configuration setted
        self.conf_obj.set(
            self.cursor, self.uid, 'default_iva_21_tax_id',
            self.tax_obj.search(self.cursor, self.uid, [("name", "=", "IVA 21%")])[0],
        )
        self.conf_obj.set(
            self.cursor, self.uid, 'default_iese_tax_id',
            self.tax_obj.search(self.cursor, self.uid, [
                ("name", "=", "Impuesto especial sobre la electricidad")
            ])[0],
        )

        self.pol_obj.send_signal(
            self.cursor, self.uid, [self.contract_20TD_id], ["validar", "contracte"])
        context = {"active_id": self.contract_20TD_id, "change_type": "from_period_to_index"}
        wiz_id = self.wiz_change_to_index_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_change_to_index_obj.change_to_indexada(
            self.cursor, self.uid, [wiz_id], context=context)

        pol_20td = self.pol_obj.browse(self.cursor, self.uid, self.contract_20TD_id)

        result = self.backend_obj.get_prices_data(self.cursor, self.uid, pol_20td, context={})

        self.assertEqual(result['mostra_indexada'], False)

    def test_ignored_modcon_does_not_hide_future_prices_of_current_pricelist(self):
        self.pol_obj.send_signal(
            self.cursor, self.uid, [self.contract_20TD_id], ['validar', 'contracte'])
        context = {'active_id': self.contract_20TD_id, 'change_type': 'from_period_to_index'}
        wiz_id = self.wiz_change_to_index_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_change_to_index_obj.change_to_indexada(
            self.cursor, self.uid, [wiz_id], context=context)
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20TD_id)
        current_pricelist_id = pol.llista_preu.id
        self.assertNotEqual(current_pricelist_id, pol.modcontractuals_ids[0].llista_preu.id)
        future_date = date.today() + timedelta(days=30)
        current_end = future_date - timedelta(days=1)
        module = 'som_polissa_condicions_generals.models.report_backend_ccpp'

        def get_prices(cursor, uid, policy, period, kind, context, with_taxes=True):
            price_date = context['date']
            if hasattr(price_date, 'date'):
                price_date = price_date.date()
            return (2.0 if price_date >= future_date else 1.0, 0)

        for has_future in [True, False]:
            versions = mock.Mock()
            versions.search.side_effect = [[1], [2] if has_future else []]
            versions.read.side_effect = [
                [{'date_start': '2020-01-01', 'date_end': current_end.strftime('%Y-%m-%d')}],
                [{'date_start': future_date.strftime('%Y-%m-%d'), 'date_end': False}],
            ]
            pricelists = mock.Mock()
            pricelists.browse.return_value = pol.llista_preu
            helper_policy = mock.Mock()
            helper_policy.llista_preu = pol.llista_preu
            helper_policy.modcontractual_activa.data_final = (
                date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            helper_policy.pool.get.side_effect = {
                'product.pricelist.version': versions,
                'product.pricelist': pricelists,
            }.__getitem__

            def get_versions(cursor, uid, policy, context):
                return get_comming_atr_price(cursor, uid, helper_policy, context)

            with mock.patch(module + '.get_comming_atr_price', side_effect=get_versions), \
                    mock.patch(module + '.get_atr_price', side_effect=get_prices), \
                    mock.patch.object(self.pol_obj, 'get_simplified_taxes',
                                      return_value={'IVA': 0.21, 'IE': 0.0511}):
                result = self.backend_obj.get_prices_data(self.cursor, self.uid, pol, context={})

            self.assertEqual(len(result['pricelists']), 2 if has_future else 1)
            self.assertFalse(result['mostra_indexada'])
            self.assertIn(current_end.strftime('%d/%m/%Y'),
                          result['pricelists'][0]['text_vigencia'])
            self.assertEqual(result['pricelists'][0]['energy_prices_untaxed']['P1'], 1.0)
            self.assertEqual(versions.search.call_count, 2)
            pricelists.browse.assert_called_once_with(self.cursor, self.uid, current_pricelist_id)
            if has_future:
                self.assertIn(future_date.strftime('%d/%m/%Y'),
                              result['pricelists'][1]['text_vigencia'])
                self.assertEqual(result['pricelists'][1]['energy_prices_untaxed']['P1'], 2.0)
