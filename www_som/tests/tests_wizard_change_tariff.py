from destral import testing


class TestWizardChangeTariff(testing.OOTestCaseWithCursor):

    def test_change_tariff(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get("ir.model.data")
        wiz_obj = self.openerp.pool.get("wizard.change.tariff")
        pp_obj = self.openerp.pool.get("product.pricelist")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        pol_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', "polissa_tarifa_018"
        )[1]
        pol_obj.send_signal(cursor, uid, [pol_id], ['validar', 'contracte'])
        pp_id = pp_obj.search(cursor, uid, [('name', '=', '2.0TD_SOM_SOCIAL')])[0]
        wiz_id = wiz_obj.create(cursor, uid, {
            'pricelist_id': pp_id,
            'polissa_id': pol_id,
        })
        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        pol = pol_obj.browse(cursor, uid, pol_id)
        self.assertTrue(pol.llista_preu.id != pp_id)

        wiz.change_tariff(context={'active_id': pol_id})

        self.assertTrue(pol.llista_preu.id == pp_id)
