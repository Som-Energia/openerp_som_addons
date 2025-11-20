from destral import testing


class TestUpdatePendingStates(testing.OOTestCaseWithCursor):

    def test_change_tariff(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get("ir.model.data")
        wiz_obj = self.openerp.pool.get("wizard.change.tariff")
        pp_obj = self.openerp.pool.get("product.pricelist")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        pol_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', "polissa_0001"
        )[1]
        pp_id = pp_obj.search(cursor, uid, [('name', '=', '2.0TD_SOM_SOCIAL')])[0]
        wiz_id = wiz_obj.create(cursor, uid, {'pricelist': pp_id})
        pol = pol_obj.browse(cursor, uid, pol_id)
        self.assertTrue(pol.llista_preu.id != pp_id)

        wiz_id.change_tariff(cursor, uid)

        self.assertTrue(pol.llista_preu.id == pp_id)
