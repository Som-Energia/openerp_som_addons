from destral import testing
from destral.transaction import Transaction
from osv import osv


class TestsGurbServices(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def activar_polissa_CUPS(self, context=None):
        if context is None:
            context = {}
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get("ir.model.data")
        polissa_obj = self.openerp.pool.get("giscedata.polissa")
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", context.get("polissa_xml_id", "polissa_0001")
        )[1]
        polissa_obj.send_signal(cursor, uid, [polissa_id], [
            "validar", "contracte"
        ])

    def test_add_service_to_contract(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        pol_o = self.openerp.pool.get("giscedata.polissa")

        gurb_cups_id = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        pricelist_id = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "pricelist_gurb_demo"
        )[1]
        product_id = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "product_gurb"
        )[1]
        pol_id = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]

        self.activar_polissa_CUPS()
        gurb_cups_o.add_service_to_contract(
            self.cursor, self.uid, [gurb_cups_id], pricelist_id, product_id, '2023-01-01'
        )

        pol_br = pol_o.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(len(pol_br.serveis), 1)
        self.assertEqual(pol_br.serveis[0].llista_preus.id, pricelist_id)
        self.assertEqual(pol_br.serveis[0].producte.id, product_id)
        self.assertEqual(pol_br.serveis[0].polissa_id.id, pol_id)

    def test_fail_add_service_to_unactivated_contract(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")

        gurb_cups_id = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        pricelist_id = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "pricelist_gurb_demo"
        )[1]
        product_id = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "product_gurb"
        )[1]

        with self.assertRaises(osv.except_osv):
            gurb_cups_o.add_service_to_contract(
                self.cursor, self.uid, [gurb_cups_id], pricelist_id, product_id, '2023-01-01'
            )
