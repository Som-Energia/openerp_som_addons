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

    def get_references(self):
        imd_o = self.openerp.pool.get("ir.model.data")

        vals = {}

        vals['gurb_cups_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        vals['pricelist_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "pricelist_gurb_demo"
        )[1]
        vals['product_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "product_gurb"
        )[1]
        vals['pol_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]

        return vals

    def add_service_to_contract(self, start_date='2023-01-01', context=None):
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        vals = self.get_references()

        self.activar_polissa_CUPS()
        gurb_cups_o.add_service_to_contract(
            self.cursor,
            self.uid,
            [vals['gurb_cups_id']], vals['pricelist_id'],
            vals['product_id'],
            start_date,
        )

    def test_add_service_to_contract(self):
        pol_o = self.openerp.pool.get("giscedata.polissa")
        self.add_service_to_contract()
        vals = self.get_references()

        pol_br = pol_o.browse(self.cursor, self.uid, vals['pol_id'])
        self.assertEqual(len(pol_br.serveis), 1)
        self.assertEqual(pol_br.serveis[0].llista_preus.id, vals['pricelist_id'])
        self.assertEqual(pol_br.serveis[0].producte.id, vals['product_id'])
        self.assertEqual(pol_br.serveis[0].polissa_id.id, vals['pol_id'])

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

    def test_get_vals_linia_no_pricelist(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        pol_o = self.openerp.pool.get("giscedata.polissa")
        fact_services_o = self.openerp.pool.get("giscedata.facturacio.services")
        fact_o = self.openerp.pool.get("giscedata.facturacio.factura")

        vals = self.get_references()
        pol_br = pol_o.browse(self.cursor, self.uid, vals['pol_id'])
        factura_id = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001"
        )[1]
        fact_br = fact_o.browse(self.cursor, self.uid, factura_id)
        self.add_service_to_contract(start_date="2016-01-01")

        n_lines = 0
        for line in fact_services_o._get_vals_linia(
            self.cursor, self.uid, pol_br.serveis[0], fact_br
        ):
            n_lines += 1
            self.assertEqual(line["quantity"], 2.0)  # Number of betas
            self.assertEqual(line["multi"], 0)  # Service days invoiced

        self.assertEqual(n_lines, 1)

    def test_get_vals_linia_full_period(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        pol_o = self.openerp.pool.get("giscedata.polissa")
        fact_services_o = self.openerp.pool.get("giscedata.facturacio.services")
        fact_o = self.openerp.pool.get("giscedata.facturacio.factura")

        vals = self.get_references()
        pol_br = pol_o.browse(self.cursor, self.uid, vals['pol_id'])
        pricelist_br = pol_o.browse(self.cursor, self.uid, vals['pricelist_id'])
        pricelist_br.date_start = "2016-01-01"
        factura_id = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001"
        )[1]
        fact_br = fact_o.browse(self.cursor, self.uid, factura_id)
        self.add_service_to_contract(start_date="2016-01-01")

        n_lines = 0
        for line in fact_services_o._get_vals_linia(
            self.cursor, self.uid, pol_br.serveis[0], fact_br
        ):
            n_lines += 1
            self.assertEqual(line["quantity"], 2.0)  # Number of betas
            self.assertEqual(line["multi"], 20)  # Service days invoiced

        self.assertEqual(n_lines, 0)
