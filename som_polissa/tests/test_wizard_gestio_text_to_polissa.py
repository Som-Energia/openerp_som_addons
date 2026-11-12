# -*- coding: utf-8 -*-
from destral import testing


class TestWizardGestioTextToPolissa(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestWizardGestioTextToPolissa, self).setUp()
        self.pool = self.openerp.pool

    def test_wizard_gestio_text_to_polissa__from_polissa(self):
        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("wizard.gestio.text.to.polissa")
        pol_o = self.pool.get("giscedata.polissa")

        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]

        wiz_init = {"comment": "comentari test 1", "field_to_write": "info_gestions_massives"}
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={"active_ids": [pol_id], "from_model": "giscedata.polissa"},
        )

        wiz_o.modify_gestio_to_polissa(
            self.cursor,
            self.uid,
            [wiz_id],
            {"active_ids": [pol_id], "from_model": "giscedata.polissa"},
        )
        new_comment = pol_o.read(self.cursor, self.uid, pol_id, ["info_gestions_massives"])[
            "info_gestions_massives"
        ]
        self.assertEqual(new_comment, "comentari test 1\n")

    def test_wizard_gestio_text_to_polissa__from_polissa__manyPolisses(self):
        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("wizard.gestio.text.to.polissa")
        pol_o = self.pool.get("giscedata.polissa")

        pol_id_1 = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]

        pol_id_2 = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0002"
        )[1]

        pol_ids = [pol_id_1, pol_id_2]

        wiz_init = {"comment": "comentari test 1", "field_to_write": "info_gestions_massives"}
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={"active_ids": pol_ids, "from_model": "giscedata.polissa"},
        )

        wiz_o.modify_gestio_to_polissa(
            self.cursor,
            self.uid,
            [wiz_id],
            {"active_ids": pol_ids, "from_model": "giscedata.polissa"},
        )
        new_comments = pol_o.read(self.cursor, self.uid, pol_ids, ["info_gestions_massives"])
        self.assertEqual(
            [x["info_gestions_massives"] for x in new_comments],
            ["comentari test 1\n", "comentari test 1\n"],
        )

    def test_wizard_gestio_text_to_polissa__from_polissa_gest_endarrerida(self):
        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("wizard.gestio.text.to.polissa")
        pol_o = self.pool.get("giscedata.polissa")

        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]
        pol_o.write(self.cursor, self.uid, pol_id, {"info_gestio_endarrerida": "previous text"})

        wiz_init = {"comment": "comentari test 1", "field_to_write": "info_gestio_endarrerida"}
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={"active_ids": [pol_id], "from_model": "giscedata.polissa"},
        )

        wiz_o.modify_gestio_to_polissa(
            self.cursor,
            self.uid,
            [wiz_id],
            {"active_ids": [pol_id], "from_model": "giscedata.polissa"},
        )
        new_comment = pol_o.read(
            self.cursor, self.uid, pol_id, ["info_gestio_endarrerida", "info_gestions_massives"]
        )
        self.assertEqual(new_comment["info_gestio_endarrerida"], "comentari test 1\nprevious text")
        self.assertEqual(new_comment["info_gestions_massives"], False)

    def test_wizard_gestio_text_to_polissa__replace_polissa_gest_endarrerida(self):
        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("wizard.gestio.text.to.polissa")
        pol_o = self.pool.get("giscedata.polissa")

        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]
        pol_o.write(self.cursor, self.uid, pol_id, {"info_gestio_endarrerida": "previous text"})

        wiz_init = {
            "comment": "comentari test 1",
            "field_to_write": "info_gestio_endarrerida",
            "option": "substituir",
        }
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={"active_ids": [pol_id], "from_model": "giscedata.polissa"},
        )

        wiz_o.modify_gestio_to_polissa(
            self.cursor,
            self.uid,
            [wiz_id],
            {"active_ids": [pol_id], "from_model": "giscedata.polissa"},
        )
        new_comment = pol_o.read(
            self.cursor, self.uid, pol_id, ["info_gestio_endarrerida", "info_gestions_massives"]
        )
        self.assertEqual(new_comment["info_gestio_endarrerida"], "comentari test 1")
        self.assertEqual(new_comment["info_gestions_massives"], False)

    def test_wizard_gestio_text_to_polissa__delete_polissa_gest_endarrerida(self):
        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("wizard.gestio.text.to.polissa")
        pol_o = self.pool.get("giscedata.polissa")

        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]
        pol_o.write(self.cursor, self.uid, pol_id, {"info_gestio_endarrerida": "previous text"})

        wiz_init = {
            "comment": "",
            "field_to_write": "info_gestio_endarrerida",
            "option": "eliminar",
        }
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={"active_ids": [pol_id], "from_model": "giscedata.polissa"},
        )

        wiz_o.modify_gestio_to_polissa(
            self.cursor,
            self.uid,
            [wiz_id],
            {"active_ids": [pol_id], "from_model": "giscedata.polissa"},
        )
        new_comment = pol_o.read(
            self.cursor, self.uid, pol_id, ["info_gestio_endarrerida", "info_gestions_massives"]
        )
        self.assertEqual(new_comment["info_gestio_endarrerida"], "")
        self.assertEqual(new_comment["info_gestions_massives"], False)

    def test_get_polissa_ids_from_contracte_lot(self):
        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("wizard.gestio.text.to.polissa")
        clot_o = self.pool.get("giscedata.facturacio.contracte_lot")

        clot_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "cont_lot_0001"
        )[1]
        clot = clot_o.browse(self.cursor, self.uid, clot_id)

        wiz_init = {"field_to_write": "info_gestio_endarrerida"}
        context = {"active_ids": [clot_id], "from_model": "giscedata.facturacio.contracte_lot"}
        wiz_id = wiz_o.create(self.cursor, self.uid, wiz_init, context=context)

        result = wiz_o.get_polisses_ids(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(result, [clot.polissa_id.id])
