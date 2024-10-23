# -*- coding: utf-8 -*-

from destral import testing
import mock
from som_municipal_taxes.models.som_municipal_taxes_config import SomMunicipalTaxesConfig


class TestWizardPresentacioRedsaras(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestWizardPresentacioRedsaras, self).setUp()
        self.pool = self.openerp.pool

    @mock.patch.object(SomMunicipalTaxesConfig, "encuar_crawlers")
    def test_enviar_redsaras_ok(self, encuar_crawlers):
        wiz_o = self.pool.get("wizard.presentacio.redsaras")
        wiz_init = {
            "year": 2016,
            "quarter": 1,
        }
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={},
        )

        wiz_o.enviar_redsaras(
            self.cursor,
            self.uid,
            [wiz_id],
            {},
        )

        state = wiz_o.read(self.cursor, self.uid, wiz_id, ['state'])[0]['state']
        self.assertEqual(state, 'done')

    @mock.patch.object(SomMunicipalTaxesConfig, "encuar_crawlers")
    def test_enviar_redsaras_no_municipis(self, encuar_crawlers):
        imd_obj = self.openerp.pool.get('ir.model.data')
        config_obj = self.openerp.pool.get('som.municipal.taxes.config')
        municipal_config_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_municipal_taxes',
            'ajuntament_girona'
        )[1]
        config_obj.write(self.cursor, self.uid, municipal_config_id, {'red_sara': 0})
        wiz_o = self.pool.get("wizard.presentacio.redsaras")
        wiz_init = {
            "year": 2016,
            "quarter": 1,
        }
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={},
        )

        wiz_o.enviar_redsaras(
            self.cursor,
            self.uid,
            [wiz_id],
            {},
        )

        state = wiz_o.read(self.cursor, self.uid, wiz_id, ['state'])[0]['state']
        self.assertEqual(state, 'cancel')
