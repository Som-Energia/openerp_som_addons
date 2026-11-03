# -*- coding: utf-8 -*-
from __future__ import absolute_import

import imp
import os

from destral import testing
import mock


class TestCardPaymentTranslations(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestCardPaymentTranslations, self).setUp()
        module_path = os.path.dirname(os.path.dirname(__file__))
        self.migration = imp.load_source(
            'som_card_payment_translation_migration',
            os.path.join(
                module_path, 'migrations', '5.0.25.5.0', 'post-0002_load_translations.py'
            ),
        )

    def _assert_upgrade_translations(self, language, expected):
        translation_obj = self.openerp.pool.get('ir.translation')
        translation_ids = translation_obj.search(
            self.cursor, self.uid,
            [('lang', '=', language), ('type', '=', 'code'), ('src', 'in', list(expected))],
        )
        # Simulate an installed module without the validation translations.
        translation_obj.unlink(self.cursor, self.uid, translation_ids)

        self.migration.up(self.cursor, '5.0.25.5.0')

        for source, translated in expected.items():
            self.cursor.execute(
                "SELECT value FROM ir_translation WHERE lang = %s AND type = 'code' AND src = %s",
                (language, source),
            )
            values = [row[0] for row in self.cursor.fetchall()]
            self.assertTrue(values, source)
            self.assertEqual(set(values), set([translated]))

    def test_upgrade_loads_catalan_validation_errors(self):
        self._assert_upgrade_translations('ca_ES', {
            'Invalid card data': u'Dades de targeta no vàlides',
            'Missing required card fields: %s': u'Falten camps obligatoris de la targeta: %s',
            'Card token conflict': u'Conflicte de token de targeta',
            'Multiple stored cards match the same payer and card data.': (
                u'Diverses targetes desades coincideixen amb el mateix pagador '
                u'i les mateixes dades de targeta.'
            ),
        })

    def test_upgrade_loads_spanish_validation_errors(self):
        self._assert_upgrade_translations('es_ES', {
            'Invalid card data': u'Datos de tarjeta no válidos',
            'Missing required card fields: %s': u'Faltan campos obligatorios de la tarjeta: %s',
            'Card token conflict': u'Conflicto de token de tarjeta',
            'Multiple stored cards match the same payer and card data.': (
                u'Varias tarjetas guardadas coinciden con el mismo pagador '
                u'y los mismos datos de tarjeta.'
            ),
        })

    def test_translation_migration_skips_fresh_install(self):
        with mock.patch.object(self.migration, 'trans_load') as load_translations:
            self.migration.up(self.cursor, False)

        load_translations.assert_not_called()
