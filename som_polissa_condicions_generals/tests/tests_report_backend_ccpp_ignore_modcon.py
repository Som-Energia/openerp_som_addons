# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestReportBackendCCPPIgnoreModcon(testing.OOTestCase):
    def get_ref(self, module, ref):
        IrModel = self.openerp.pool.get("ir.model.data")
        return IrModel._get_obj(self.cursor, self.uid, module, ref).id

    def setUp(self):
        self.maxDiff = None
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.pol_obj = self.openerp.pool.get("giscedata.polissa")
        self.backend_obj = self.openerp.pool.get(
            "report.backend.condicions.particulars.ignore.modcon")
        self.pricelist_obj = self.openerp.pool.get("product.pricelist")
        self.wiz_change_to_index_obj = self.openerp.pool.get("wizard.change.to.indexada")
        self.contract_20TD_id = self.get_ref("giscedata_polissa", "polissa_tarifa_018")

    def tearDown(self):
        self.txn.stop()

    def test_get_polissa_data_with_modcon_keeps_current(self):
        self.pol_obj.send_signal(
            self.cursor, self.uid, [self.contract_20TD_id], ["validar", "contracte"])
        context = {"active_id": self.contract_20TD_id, "change_type": "from_period_to_index"}
        wiz_id = self.wiz_change_to_index_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_change_to_index_obj.change_to_indexada(
            self.cursor, self.uid, [wiz_id], context=context)

        pol_20td = self.pol_obj.browse(self.cursor, self.uid, self.contract_20TD_id)

        result = self.backend_obj.get_polissa_data(self.cursor, self.uid, pol_20td, context={})

        pricelist_id = self.get_ref("giscedata_facturacio", "pricelist_tarifas_electricidad_venda")
        pricelist_name = self.pricelist_obj.browse(self.cursor, self.uid, pricelist_id).name

        self.assertEqual(result['pricelist'], pricelist_id)
        self.assertEqual(result['tarifa_mostrar'], pricelist_name)
