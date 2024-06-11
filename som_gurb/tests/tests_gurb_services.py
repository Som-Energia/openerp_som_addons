from osv import osv
from datetime import datetime, timedelta
from tests_gurb_base import TestsGurbBase


class TestsGurbServices(TestsGurbBase):

    def add_service_to_contract(self, owner=False, start_date='2023-01-01', context=None):
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        vals = self.get_references()

        context = {"polissa_xml_id": "polissa_0001" if owner else "polissa_tarifa_018"}
        self.activar_polissa_CUPS(context=context)
        gurb_cups_id = vals['owner_gurb_cups_id'] if owner else vals['gurb_cups_id']
        gurb_cups_o.add_service_to_contract(
            self.cursor,
            self.uid,
            [gurb_cups_id],
            start_date,
        )

    def create_new_pricelist_version(self, start_date, pricelist_id):
        context = {}

        pl_o = self.openerp.pool.get("product.pricelist")
        pl_vers_o = self.openerp.pool.get("product.pricelist.version")

        pl_v_id = pl_o.read(self.cursor, self.uid, pricelist_id, ["version_id"])["version_id"]

        write_version_vals = {
            "date_end": datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=1),
        }

        pl_vers_o.write(self.cursor, self.uid, pl_v_id, write_version_vals, context=context)

        create_item_vals = {
            "name": "GURB Demo Pricelist Item",
            "base_price": 0.1,
            "price_surcharge": 0.0,
            "sequence": 11,
            "product_id": self.get_references()['product_id']
        }

        create_version_vals = {
            "name": "Version - {}".format(start_date),
            "active": True,
            "pricelist_id": pricelist_id,
            "date_start": start_date,
            "items_id": [
                (0, 0, create_item_vals)
            ]
        }

        pl_vers_o.create(self.cursor, self.uid, create_version_vals, context=context)

    def test_add_service_to_owner_contract(self):
        pol_o = self.openerp.pool.get("giscedata.polissa")
        self.add_service_to_contract(owner=True)
        vals = self.get_references()

        pol_br = pol_o.browse(self.cursor, self.uid, vals['owner_pol_id'])
        self.assertEqual(len(pol_br.serveis), 1)
        self.assertEqual(pol_br.serveis[0].llista_preus.id, vals['pricelist_id'])  # TODO: Revisar
        self.assertEqual(pol_br.serveis[0].producte.id, vals['owner_product_id'])
        self.assertEqual(pol_br.serveis[0].polissa_id.id, vals['owner_pol_id'])

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

        with self.assertRaises(osv.except_osv):
            gurb_cups_o.add_service_to_contract(
                self.cursor, self.uid, [gurb_cups_id], '2023-01-01'
            )

    def test_get_vals_linia_full_period(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        pol_o = self.openerp.pool.get("giscedata.polissa")
        fact_services_o = self.openerp.pool.get("giscedata.facturacio.services")
        fact_o = self.openerp.pool.get("giscedata.facturacio.factura")

        vals = self.get_references()
        pol_br = pol_o.browse(self.cursor, self.uid, vals['owner_pol_id'])
        factura_id = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001"
        )[1]
        fact_br = fact_o.browse(self.cursor, self.uid, factura_id)
        self.add_service_to_contract(owner=True, start_date="2016-01-01")

        n_lines = 0
        for line in fact_services_o._get_vals_linia(
            self.cursor, self.uid, pol_br.serveis[0], fact_br
        ):
            n_lines += 1
            self.assertEqual(line["quantity"], 2.5)  # Number of betas
            self.assertEqual(line["multi"], 60)  # Service days invoiced

        self.assertEqual(n_lines, 1)

    def test_get_vals_linia_beta_change(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        pol_o = self.openerp.pool.get("giscedata.polissa")
        fact_services_o = self.openerp.pool.get("giscedata.facturacio.services")
        fact_o = self.openerp.pool.get("giscedata.facturacio.factura")

        vals = self.get_references()
        pol_br = pol_o.browse(self.cursor, self.uid, vals['owner_pol_id'])
        factura_id = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001"
        )[1]
        fact_br = fact_o.browse(self.cursor, self.uid, factura_id)
        self.add_service_to_contract(owner=True, start_date="2016-01-01")
        self.create_new_gurb_cups_beta(vals["owner_gurb_cups_id"], "2016-02-01", 1.5, 0.5)

        lines = []
        for line in fact_services_o._get_vals_linia(
            self.cursor, self.uid, pol_br.serveis[0], fact_br
        ):
            lines.append(line)

        self.assertEqual(lines[1]["data_desde"], "2016-01-01")  # Line start date
        self.assertEqual(lines[1]["data_fins"], "2016-01-31")  # Line end date
        self.assertEqual(lines[1]["quantity"], 2.5)  # Number of betas
        self.assertEqual(lines[1]["multi"], 31)  # Service days invoiced

        self.assertEqual(lines[0]["data_desde"], "2016-02-01")  # Line start date
        self.assertEqual(lines[0]["data_fins"], "2016-02-29")  # Line end date
        self.assertEqual(lines[0]["quantity"], 1.5)  # Number of betas
        self.assertEqual(lines[0]["multi"], 29)  # Service days invoiced

        self.assertEqual(len(lines), 2)

    def test_get_vals_linia_price_change(self):
        context = {}
        imd_o = self.openerp.pool.get("ir.model.data")
        pol_o = self.openerp.pool.get("giscedata.polissa")
        fact_services_o = self.openerp.pool.get("giscedata.facturacio.services")
        fact_o = self.openerp.pool.get("giscedata.facturacio.factura")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        gurb_o = self.openerp.pool.get("som.gurb")

        ref = self.get_references()
        pol_br = pol_o.browse(self.cursor, self.uid, ref['owner_pol_id'], context=context)
        factura_id = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001"
        )[1]
        fact_br = fact_o.browse(self.cursor, self.uid, factura_id)
        self.add_service_to_contract(owner=True, start_date="2016-01-01")

        gurb_cups_id = ref["owner_gurb_cups_id"]
        gurb_id = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id, ["gurb_id"], context=context
        )["gurb_id"][0]

        pricelist_id = gurb_o.read(
            self.cursor, self.uid, gurb_id, ["pricelist_id"], context=context
        )["pricelist_id"][0]

        self.create_new_pricelist_version("2016-02-15", pricelist_id)

        lines = []
        for line in fact_services_o._get_vals_linia(
            self.cursor, self.uid, pol_br.serveis[0], fact_br
        ):
            lines.append(line)

        self.assertEqual(lines[1]["data_desde"], "2016-02-15")  # Line start date
        self.assertEqual(lines[1]["data_fins"], "2016-02-29")  # Line end date
        self.assertEqual(lines[1]["quantity"], 2.5)  # Number of betas
        self.assertEqual(lines[1]["multi"], 15)  # Service days invoiced

        self.assertEqual(lines[0]["data_desde"], "2016-01-01")  # Line start date
        self.assertEqual(lines[0]["data_fins"], "2016-02-14")  # Line end date
        self.assertEqual(lines[0]["quantity"], 2.5)  # Number of betas
        self.assertEqual(lines[0]["multi"], 45)  # Service days invoiced

        self.assertEqual(len(lines), 2)

    def test_get_vals_linia_beta_change_price_change(self):
        context = {}
        imd_o = self.openerp.pool.get("ir.model.data")
        pol_o = self.openerp.pool.get("giscedata.polissa")
        fact_services_o = self.openerp.pool.get("giscedata.facturacio.services")
        fact_o = self.openerp.pool.get("giscedata.facturacio.factura")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        gurb_o = self.openerp.pool.get("som.gurb")

        ref = self.get_references()
        pol_br = pol_o.browse(self.cursor, self.uid, ref['owner_pol_id'], context=context)
        factura_id = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001"
        )[1]
        fact_br = fact_o.browse(self.cursor, self.uid, factura_id)
        self.add_service_to_contract(owner=True, start_date="2016-01-01")

        gurb_cups_id = ref["owner_gurb_cups_id"]
        gurb_id = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id, ["gurb_id"], context=context
        )["gurb_id"][0]

        pricelist_id = gurb_o.read(
            self.cursor, self.uid, gurb_id, ["pricelist_id"], context=context
        )["pricelist_id"][0]

        self.create_new_pricelist_version("2016-02-15", pricelist_id)
        self.create_new_gurb_cups_beta(gurb_cups_id, "2016-02-01", 1.5, 0.5)

        lines = []
        for line in fact_services_o._get_vals_linia(
            self.cursor, self.uid, pol_br.serveis[0], fact_br
        ):
            lines.append(line)

        self.assertEqual(lines[0]["data_desde"], "2016-02-01")  # Line start date
        self.assertEqual(lines[0]["data_fins"], "2016-02-14")  # Line end date
        self.assertEqual(lines[0]["quantity"], 1.5)  # Number of betas
        self.assertEqual(lines[0]["multi"], 14)  # Service days invoiced

        self.assertEqual(lines[1]["data_desde"], "2016-01-01")  # Line start date
        self.assertEqual(lines[1]["data_fins"], "2016-01-31")  # Line end date
        self.assertEqual(lines[1]["quantity"], 2.5)  # Number of betas
        self.assertEqual(lines[1]["multi"], 31)  # Service days invoiced

        self.assertEqual(lines[2]["data_desde"], "2016-02-15")  # Line start date
        self.assertEqual(lines[2]["data_fins"], "2016-02-29")  # Line end date
        self.assertEqual(lines[2]["quantity"], 1.5)  # Number of betas
        self.assertEqual(lines[2]["multi"], 15)  # Service days invoiced

        self.assertEqual(len(lines), 3)
