# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import mock
from destral import testing
from destral.transaction import Transaction
from som_indexada.utils import get_preus as get_indexed_preus


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
            self.assertEqual(context.get('force_pricelist'), expected)

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
            self.assertNotIn('force_pricelist', context)
