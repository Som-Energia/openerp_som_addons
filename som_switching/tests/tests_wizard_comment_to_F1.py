# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction


class TestMultipleCommentF1(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def test__multiple_comment_F1__oneF1(self):
        """
        Test per afegir un comentari en una sola F1
        """
        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("wizard.comment.to.F1")
        inv_o = self.pool.get("giscedata.facturacio.importacio.linia")

        inv_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_02_f1_import_01"
        )[1]

        wiz_init = {"comment": ""}
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={"active_ids": [inv_id], "from_model": "giscedata.facturacio.importacio.linia"},
        )
        wiz_o.write(self.cursor, self.uid, [wiz_id], {"comment": "comentari test 1"})

        wiz_o.modify_text_F1(
            self.cursor,
            self.uid,
            [wiz_id],
            {"active_ids": [inv_id], "from_model": "giscedata.facturacio.importacio.linia"},
        )
        new_comment = inv_o.read(self.cursor, self.uid, inv_id, ["user_observations"])[
            "user_observations"
        ]
        self.assertEqual(new_comment, "comentari test 1\n")

    def test__multiple_comment_to_F1__manyF1(self):
        """
        Test per afegir un comentari en més d'una F1
        """
        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("wizard.comment.to.F1")
        inv_o = self.pool.get("giscedata.facturacio.importacio.linia")

        inv_id_1 = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_02_f1_import_01"
        )[1]
        inv_id_2 = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_03_f1_import_01"
        )[1]

        wiz_init = {"comment": ""}
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={
                "active_ids": [inv_id_1, inv_id_2],
                "from_model": "giscedata.facturacio.importacio.linia",
            },
        )
        wiz_o.write(self.cursor, self.uid, [wiz_id], {"comment": "comentari test 1"})

        wiz_o.modify_text_F1(
            self.cursor,
            self.uid,
            [wiz_id],
            {
                "active_ids": [inv_id_1, inv_id_2],
                "from_model": "giscedata.facturacio.importacio.linia",
            },
        )
        new_comment_1 = inv_o.read(self.cursor, self.uid, inv_id_1, ["user_observations"])[
            "user_observations"
        ]
        new_comment_2 = inv_o.read(self.cursor, self.uid, inv_id_2, ["user_observations"])[
            "user_observations"
        ]
        self.assertEqual(new_comment_1, "comentari test 1\n")
        self.assertEqual(new_comment_2, "comentari test 1\n")

    def test__multiple_comment_to_F1__appendComment(self):
        """
        Test per afegir un comentari en una sola F1
        """
        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("wizard.comment.to.F1")
        inv_o = self.pool.get("giscedata.facturacio.importacio.linia")

        inv_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_02_f1_import_01"
        )[1]
        inv_o.write(self.cursor, self.uid, inv_id, {"user_observations": "comentari test 2"})

        wiz_init = {"comment": ""}
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={"active_ids": [inv_id], "from_model": "giscedata.facturacio.importacio.linia"},
        )
        wiz_o.write(self.cursor, self.uid, [wiz_id], {"comment": "comentari test 1"})

        wiz_o.modify_text_F1(
            self.cursor,
            self.uid,
            [wiz_id],
            {"active_ids": [inv_id], "from_model": "giscedata.facturacio.importacio.linia"},
        )
        new_comment = inv_o.read(self.cursor, self.uid, inv_id, ["user_observations"])[
            "user_observations"
        ]
        self.assertEqual(new_comment, "comentari test 1\ncomentari test 2")

    def test__multiple_comment_to_F1__replaceComment(self):
        """
        Test per afegir un comentari en una sola F1
        """
        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("wizard.comment.to.F1")
        inv_o = self.pool.get("giscedata.facturacio.importacio.linia")

        inv_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_02_f1_import_01"
        )[1]
        inv_o.write(self.cursor, self.uid, inv_id, {"user_observations": "comentari test 2"})

        wiz_init = {"comment": "comentari test 1", "option": "substituir"}
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={"active_ids": [inv_id], "from_model": "giscedata.facturacio.importacio.linia"},
        )

        wiz_o.modify_text_F1(
            self.cursor,
            self.uid,
            [wiz_id],
            {"active_ids": [inv_id], "from_model": "giscedata.facturacio.importacio.linia"},
        )
        new_comment = inv_o.read(self.cursor, self.uid, inv_id, ["user_observations"])[
            "user_observations"
        ]
        self.assertEqual(new_comment, "comentari test 1")

    def test__multiple_comment_to_F1__deleteComment(self):
        """
        Test per afegir un comentari en una sola F1
        """
        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("wizard.comment.to.F1")
        inv_o = self.pool.get("giscedata.facturacio.importacio.linia")

        inv_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_02_f1_import_01"
        )[1]
        inv_o.write(self.cursor, self.uid, inv_id, {"user_observations": "comentari test 2"})

        wiz_init = {"comment": "", "option": "eliminar"}
        wiz_id = wiz_o.create(
            self.cursor,
            self.uid,
            wiz_init,
            context={"active_ids": [inv_id], "from_model": "giscedata.facturacio.importacio.linia"},
        )

        wiz_o.modify_text_F1(
            self.cursor,
            self.uid,
            [wiz_id],
            {"active_ids": [inv_id], "from_model": "giscedata.facturacio.importacio.linia"},
        )
        new_comment = inv_o.read(self.cursor, self.uid, inv_id, ["user_observations"])[
            "user_observations"
        ]
        self.assertEqual(new_comment, "")
