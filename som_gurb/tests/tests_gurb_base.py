from destral import testing
from destral.transaction import Transaction


class TestsGurbBase(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def activar_polissa_CUPS(self, set_gurb_category=False, context=None):
        if context is None:
            context = {}
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get("ir.model.data")
        polissa_obj = self.openerp.pool.get("giscedata.polissa")
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", context.get("polissa_xml_id", "polissa_tarifa_018")
        )[1]
        polissa_obj.send_signal(cursor, uid, [polissa_id], [
            "validar", "contracte"
        ])
        # Set GURB category to contract
        if set_gurb_category:
            imd_obj = self.openerp.pool.get("ir.model.data")
            gurb_categ_id = imd_obj.get_object_reference(
                self.cursor, self.uid, "som_gurb", "categ_gurb_pilot"  # TODO: Use the real category
            )[1]
            polissa_obj.write(
                self.cursor, self.uid, polissa_id, {"category_id": [(4, gurb_categ_id)]}
            )

    def get_references(self):
        imd_o = self.openerp.pool.get("ir.model.data")

        vals = {}

        vals['owner_gurb_cups_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        vals['gurb_cups_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002"
        )[1]
        vals['cups_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_cups", "cups_tarifa_018"
        )[1]
        vals['pricelist_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "pricelist_gurb_demo"
        )[1]
        vals['pricelist_version_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "version_pricelist_gurb_demo"
        )[1]
        vals['product_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "product_gurb"
        )[1]
        vals['owner_product_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "product_owner_gurb"
        )[1]
        vals['owner_pol_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]
        vals['pol_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        vals['gurb_cups_beta_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_beta_0001"
        )[1]
        vals['gurb_cups_beta_2_id'] = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_beta_0002"
        )[1]

        return vals

    def create_new_gurb_cups_beta(
        self, gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw, context=None
    ):
        context = {"active_id": gurb_cups_id}
        wiz_o = self.openerp.pool.get("wizard.gurb.create.new.beta")

        vals = {
            "start_date": start_date,
            "beta_kw": new_beta_kw,
            "extra_beta_kw": new_extra_beta_kw,
        }

        wiz_id = wiz_o.create(self.cursor, self.uid, vals, context=context)
        wiz_o.create_new_beta(self.cursor, self.uid, [wiz_id], context=context)
