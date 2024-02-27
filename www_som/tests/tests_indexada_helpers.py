# -*- coding: utf-8 -*-
from som_indexada.tests.test_wizard_change_to_indexada import TestChangeToIndexada
from datetime import datetime, timedelta


class TestIndexadaHelpers(TestChangeToIndexada):
    def test_change_to_indexada_www__with_indexada_exception(self):
        polissa_obj = self.pool.get("giscedata.polissa")
        polissa_id = self.get_contract_id(self.txn, xml_id="polissa_tarifa_018")
        self.switch(self.txn, "comer")
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        self.activar_polissa_CUPS(self.txn, context=None)
        polissa_obj.send_signal(self.cursor, self.uid, [polissa_id], ["validar", "contracte"])
        context = {"active_id": polissa_id, "change_type": "from_period_to_index"}
        self.create_case_and_step(self.cursor, self.uid, polissa_id, "M1", "01")

        helper = self.pool.get("som.indexada.webforms.helpers")

        result = helper.change_to_indexada_www(self.cursor, self.uid, polissa_id, context)

        self.assertEqual(result["error"], u"Pòlissa 0018 with simultaneous ATR")

    def test_change_to_indexada_www__to_indexed(self):
        polissa_id = self.open_polissa("polissa_tarifa_018")
        polissa_obj = self.pool.get("giscedata.polissa")
        modcon_obj = self.pool.get("giscedata.polissa.modcontractual")
        IrModel = self.pool.get("ir.model.data")

        context = {"active_id": polissa_id, "change_type": "from_period_to_index"}

        helper = self.pool.get("som.indexada.webforms.helpers")

        helper.change_to_indexada_www(self.cursor, self.uid, polissa_id, context)

        modcontactual_id = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["modcontractuals_ids"]
        )["modcontractuals_ids"][0]
        prev_modcontactual_id = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["modcontractuals_ids"]
        )["modcontractuals_ids"][1]

        new_pricelist_id = IrModel._get_obj(
            self.cursor, self.uid, "som_indexada", "pricelist_indexada_20td_peninsula"
        ).id

        modcon_act = modcon_obj.read(
            self.cursor,
            self.uid,
            modcontactual_id,
            [
                "data_inici",
                "data_final",
                "mode_facturacio",
                "mode_facturacio_generacio",
                "llista_preu",
                "active",
                "state",
                "modcontractual_ant",
            ],
        )
        modcon_act.pop("id")
        modcon_act["llista_preu"] = modcon_act["llista_preu"][0]
        modcon_act["modcontractual_ant"] = modcon_act["modcontractual_ant"][0]

        self.assertEquals(
            modcon_act,
            {
                "data_inici": datetime.strftime(datetime.today() + timedelta(days=1), "%Y-%m-%d"),
                "data_final": datetime.strftime(datetime.today() + timedelta(days=365), "%Y-%m-%d"),
                "mode_facturacio": "index",
                "mode_facturacio_generacio": "index",
                "llista_preu": new_pricelist_id,
                "active": True,
                "state": "pendent",
                "modcontractual_ant": prev_modcontactual_id,
            },
        )
