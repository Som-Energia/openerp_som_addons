# -*- coding: utf-8 -*-
from __future__ import absolute_import

import ast
import inspect

from addons import get_module_resource
from destral import testing
from oopgrade.oopgrade import load_data


XML_IDS = (
    'tarifa_20TD_SOM_SOCIAL',
    'tarifa_20TD_SOM_INSULAR_SOCIAL',
    'tarifa_indexada_20TD_peninsula_social',
    'tarifa_indexada_20TD_balears_social',
    'tarifa_indexada_20TD_canaries_social',
)


class TestSocialTariffIntegration(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestSocialTariffIntegration, self).setUp()
        self.imd = self.openerp.pool.get('ir.model.data')
        self.pricelist = self.openerp.pool.get('product.pricelist')
        self.polissa = self.openerp.pool.get('giscedata.polissa')
        self.ids = [self._reference('som_tarifa_social', name)
                    for name in XML_IDS]

    def _reference(self, module, name):
        return self.imd.get_object_reference(
            self.cursor, self.uid, module, name,
        )[1]

    def _configure_prices(self):
        regular_id = self._reference(
            'som_indexada', 'pricelist_periodes_20td_peninsula',
        )
        self.pricelist.write(self.cursor, self.uid, [self.ids[0]], {
            'mesos_renovacio': 3, 'next_pricelist_id': regular_id,
        })
        version = self.openerp.pool.get('product.pricelist.version')
        version_id = version.create(self.cursor, self.uid, {
            'name': 'Cross-module update test',
            'pricelist_id': self.ids[0], 'date_start': '2026-01-01',
        })
        self.openerp.pool.get('product.pricelist.item').create(
            self.cursor, self.uid, {
                'name': 'Configured social discount',
                'price_version_id': version_id, 'base': -1,
                'base_pricelist_id': regular_id, 'price_discount': -0.153,
            },
        )

    def _snapshot(self):
        versions = self.openerp.pool.get('product.pricelist.version')
        items = self.openerp.pool.get('product.pricelist.item')
        version_ids = versions.search(self.cursor, self.uid, [
            ('pricelist_id', 'in', self.ids),
        ], context={'active_test': False})
        item_ids = items.search(self.cursor, self.uid, [
            ('price_version_id', 'in', version_ids),
        ])
        return {
            'aliases': self.imd.search_reader(self.cursor, self.uid, [
                ('module', 'in', ['www_som', 'som_tarifa_social']),
                ('name', 'in', list(XML_IDS)),
            ], ['module', 'name', 'res_id', 'noupdate']),
            'pricelists': self.pricelist.read(
                self.cursor, self.uid, self.ids,
                ['name', 'mesos_renovacio', 'next_pricelist_id', 'version_id'],
            ),
            'versions': versions.read(
                self.cursor, self.uid, version_ids,
                ['pricelist_id', 'date_start', 'date_end', 'active'],
            ),
            'rules': items.read(
                self.cursor, self.uid, item_ids,
                ['price_version_id', 'base_pricelist_id', 'price_discount'],
            ),
        }

    def _reload_module_data(self, module):
        with open(get_module_resource(module, '__terp__.py'), 'rb') as source:
            manifest = ast.literal_eval(source.read())
        loads, unlink_mark = self.imd.loads, self.imd.unlink_mark
        try:
            # Model metadata is initialized by the module loader. Keep it
            # marked as loaded here to isolate resource loading and tariff
            # cleanup, rather than deleting unrelated model metadata.
            self.imd.loads = dict(loads)
            self.imd.unlink_mark = {}
            for ref in self.imd.search_reader(
                    self.cursor, self.uid, [('module', '=', module)],
                    ['name', 'model', 'res_id']):
                key = (module, ref['name'])
                if ref['name'] in XML_IDS:
                    self.imd.loads.pop(key, None)
                else:
                    self.imd.loads[key] = (ref['model'], ref['res_id'])
            for kind in ('init_xml', 'update_xml'):
                for filename in manifest.get(kind, []):
                    load_data(
                        self.cursor, module, filename,
                        idref=None, mode='update',
                    )
            self.imd._process_end(self.cursor, self.uid, [module])
        finally:
            self.imd.loads, self.imd.unlink_mark = loads, unlink_mark

    def test_legacy_aliases_resolve_to_owned_pricelists(self):
        for name, pricelist_id in zip(XML_IDS, self.ids):
            self.assertEqual(self._reference('www_som', name), pricelist_id)
        legacy = self.imd.search_reader(self.cursor, self.uid, [
            ('module', '=', 'www_som'), ('name', 'in', list(XML_IDS)),
        ], ['noupdate'])
        self.assertEqual(len(legacy), 5)
        self.assertTrue(all(ref['noupdate'] for ref in legacy))
        self.assertEqual(set(self.polissa.mapping_tarifa_social(
            self.cursor, self.uid,
        ).values()), set(self.ids))

    def test_www_model_inherits_social_tariff_methods(self):
        for name in (
                'mapping_tarifa_social', 'mapping_tarifa_no_social',
                'get_pricelist_from_tariff_and_location_no_social',
                'get_new_tariff_change_social_or_regular'):
            self.assertTrue(inspect.getsourcefile(
                getattr(self.polissa, name),
            ).endswith('som_tarifa_social/models/giscedata_polissa.py'))

    def test_www_update_does_not_rewrite_social_tariff_fields(self):
        label = 'Locally configured social tariff'
        self.pricelist.write(self.cursor, self.uid, [self.ids[0]], {
            'nom_comercial': label,
        })

        self._reload_module_data('www_som')

        self.assertEqual(self.pricelist.read(
            self.cursor, self.uid, self.ids[0], ['nom_comercial'],
        )['nom_comercial'], label)

    def _assert_updates_preserve_data(self, modules):
        self._configure_prices()
        before = self._snapshot()
        for module in modules:
            self._reload_module_data(module)
        self.assertEqual(self._snapshot(), before)

    def test_www_update_preserves_ids_and_pricing(self):
        self._assert_updates_preserve_data(['www_som'])

    def test_owner_update_preserves_ids_and_pricing(self):
        self._assert_updates_preserve_data(['som_tarifa_social'])

    def test_updates_in_both_orders_preserve_ids_and_pricing(self):
        self._assert_updates_preserve_data([
            'www_som', 'som_tarifa_social', 'som_tarifa_social', 'www_som',
        ])

    def test_www_caller_can_use_legacy_social_tariff_reference(self):
        polissa_id = self._reference('giscedata_polissa', 'polissa_tarifa_018')
        self.polissa.write(self.cursor, self.uid, polissa_id, {
            'llista_preu': self._reference(
                'som_indexada', 'pricelist_periodes_20td_peninsula',
            ),
            'tarifa': self._reference('giscedata_polissa', 'tarifa_20TD'),
            'mode_facturacio': 'atr',
        })
        self.polissa.send_signal(
            self.cursor, self.uid, [polissa_id], ['validar', 'contracte'],
        )

        target_id = self.polissa.get_new_tariff_change_social_or_regular(
            self.cursor, self.uid, polissa_id, 'to_social', context=None,
        )

        self.assertEqual(target_id, self._reference('www_som', XML_IDS[0]))
