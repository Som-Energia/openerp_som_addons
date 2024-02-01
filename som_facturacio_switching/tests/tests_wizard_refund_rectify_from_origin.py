# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import mock
from datetime import datetime, timedelta
from .. import wizard


class TestRefundRectifyFromOrigin(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def test_refund_rectify_by_origin_notEmailTemplates(self):
        cursor = self.cursor
        uid = self.uid

        wiz_obj = self.pool.get("wizard.refund.rectify.from.origin")

        ctx = {}

        wiz_data = {
            "actions": "open-group-order-send",
        }
        wiz_id = wiz_obj.create(cursor, uid, wiz_data, context=ctx)

        with self.assertRaises(Exception) as e:
            wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)
        self.assertEqual(
            e.exception.message,
            "warning -- Error\n\nPer enviar el correu cal indicar les plantilles",
        )

    def test_refund_rectify_by_origin_notEnforceFromAccountPaymentTemplate(self):
        cursor = self.cursor
        uid = self.uid

        temp_obj = self.pool.get("poweremail.templates")
        acc_obj = self.pool.get("poweremail.core_accounts")
        wiz_obj = self.pool.get("wizard.refund.rectify.from.origin")

        temp_ids = temp_obj.search(cursor, uid, [], limit=2)
        temp_pay_id = temp_ids[0]
        temp_refund_id = temp_ids[-1]
        acc_id = acc_obj.search(cursor, uid, [], limit=1)[0]

        temp_obj.write(cursor, uid, temp_pay_id, {"enforce_from_account": False})
        temp_obj.write(cursor, uid, temp_refund_id, {"enforce_from_account": acc_id})
        ctx = {}

        wiz_data = {
            "actions": "open-group-order-send",
            "email_template_to_pay": temp_pay_id,
            "email_template_to_refund": temp_refund_id,
        }
        wiz_id = wiz_obj.create(cursor, uid, wiz_data, context=ctx)

        with self.assertRaises(Exception) as e:
            wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)
        self.assertEqual(
            e.exception.message,
            "warning -- Error\n\nLa plantilla de pagament no té indicat el compte des del qual enviar",
        )

    def test_refund_rectify_by_origin_notEnforceFromAccountRefundTemplate(self):
        cursor = self.cursor
        uid = self.uid

        temp_obj = self.pool.get("poweremail.templates")
        acc_obj = self.pool.get("poweremail.core_accounts")
        wiz_obj = self.pool.get("wizard.refund.rectify.from.origin")

        temp_ids = temp_obj.search(cursor, uid, [], limit=2)
        temp_pay_id = temp_ids[0]
        temp_refund_id = temp_ids[-1]
        acc_id = acc_obj.search(cursor, uid, [], limit=1)[0]

        temp_obj.write(cursor, uid, temp_pay_id, {"enforce_from_account": acc_id})
        temp_obj.write(cursor, uid, temp_refund_id, {"enforce_from_account": False})
        ctx = {}

        wiz_data = {
            "actions": "open-group-order-send",
            "email_template_to_pay": temp_pay_id,
            "email_template_to_refund": temp_refund_id,
        }
        wiz_id = wiz_obj.create(cursor, uid, wiz_data, context=ctx)

        with self.assertRaises(Exception) as e:
            wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)
        self.assertEqual(
            e.exception.message,
            "warning -- Error\n\nLa plantilla de cobrament no té indicat el compte des del qual enviar",
        )

    def test_refund_rectify_by_origin_notPaymentOrder(self):
        cursor = self.cursor
        uid = self.uid

        wiz_obj = self.pool.get("wizard.refund.rectify.from.origin")

        ctx = {}

        wiz_id = wiz_obj.create(cursor, uid, {"actions": "open-group-order"}, context=ctx)

        with self.assertRaises(Exception) as e:
            wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)
        self.assertEqual(
            e.exception.message,
            "warning -- Error\n\nPer remesar les factures a pagar cal una ordre de pagament",
        )

    def test_refund_rectify_by_origin_nothingToRefundOneDraft(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        wiz_obj = self.pool.get("wizard.refund.rectify.from.origin")
        imd_obj = self.pool.get("ir.model.data")

        fact_prov_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0003"
        )[1]
        f1_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio_switching", "line_01_f1_import_01"
        )[1]
        fact_info = fact_obj.read(
            cursor,
            uid,
            fact_prov_id,
            ["origin", "polissa_id", "data_inici", "data_final", "cups_id"],
        )
        f1_obj.write(
            cursor,
            uid,
            [f1_id],
            {
                "invoice_number_text": fact_info["origin"],
                "cups_id": fact_info["cups_id"][0],
                "fecha_factura_desde": fact_info["data_inici"],
                "fecha_factura_hasta": fact_info["data_final"],
            },
        )
        f_cli_ids = fact_obj.search(
            cursor,
            uid,
            [
                ("data_inici", "<", fact_info["data_final"]),
                ("data_final", ">", fact_info["data_inici"]),
                ("type", "=", "out_invoice"),
            ],
        )
        self.assertEqual(fact_obj.read(cursor, uid, f_cli_ids[0], ["state"])["state"], "draft")
        ctx = {"active_id": f1_id, "active_ids": [f1_id]}

        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)

        wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)

        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        self.assertEqual(
            "Pòlissa {0} per l'F1 amb origen {1}: S'han eliminat 1 factures en esborrany"
            "\nL'F1 amb origen {1} no té res per abonar i rectificar perquè no hi ha factura"
            " generada, no s'actua".format(fact_info["polissa_id"][1], fact_info["origin"]),
            wiz.info,
        )

    @mock.patch.object(
        wizard.wizard_refund_rectify_from_origin.WizardRefundRectifyFromOrigin,
        "refund_rectify_if_needed",
    )
    @mock.patch.object(
        wizard.wizard_refund_rectify_from_origin.WizardRefundRectifyFromOrigin,
        "delete_draft_invoices_if_needed",
    )
    @mock.patch.object(
        wizard.wizard_refund_rectify_from_origin.WizardRefundRectifyFromOrigin,
        "recarregar_lectures_between_dates",
    )
    def test_refund_rectify_by_origin_refundOne(self, mock_lectures, mock_delete, mock_refund):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        wiz_obj = self.pool.get("wizard.refund.rectify.from.origin")
        imd_obj = self.pool.get("ir.model.data")

        fact_prov_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0003"
        )[1]
        f1_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio_switching", "line_01_f1_import_01"
        )[1]
        fact_info = fact_obj.read(
            cursor,
            uid,
            fact_prov_id,
            ["origin", "polissa_id", "data_inici", "data_final", "cups_id"],
        )

        f1_obj.write(
            cursor,
            uid,
            [f1_id],
            {
                "invoice_number_text": fact_info["origin"],
                "cups_id": fact_info["cups_id"][0],
                "fecha_factura_desde": fact_info["data_inici"],
                "fecha_factura_hasta": fact_info["data_final"],
            },
        )

        f_cli_ids = fact_obj.search(
            cursor,
            uid,
            [
                ("data_inici", "<", fact_info["data_final"]),
                ("data_final", ">", fact_info["data_inici"]),
                ("type", "=", "out_invoice"),
            ],
        )
        self.assertEqual(len(f_cli_ids), 1)
        fact_obj.write(
            cursor,
            uid,
            f_cli_ids[0],
            {
                "state": "open",
                "polissa_id": fact_info["polissa_id"][0],
                "cups_id": fact_info["cups_id"][0],
            },
        )

        ctx = {"active_id": f1_id, "active_ids": [f1_id]}

        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)
        mock_lectures.side_effect = lambda *x: 3
        mock_refund.side_effect = lambda *x: [5]
        mock_delete.side_effect = lambda *x: [""]

        wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)
        mock_lectures.assert_called_with(
            cursor,
            uid,
            [wiz_id],
            fact_info["polissa_id"][0],
            fact_info["data_inici"],
            fact_info["data_final"],
            ctx,
        )
        mock_refund.assert_called_with(cursor, uid, f_cli_ids, ctx)
        mock_delete.assert_called_with(cursor, uid, [5], f_cli_ids, ctx)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        self.assertEqual(
            wiz.info,
            "S'han esborrat 3 lectures de la pòlissa {} i s'han generat 1 factures\n\nLa pòlissa {} té "
            "alguna factura inicial oberta. No continua el procés".format(
                fact_info["polissa_id"][1], fact_info["polissa_id"][1]
            ),
        )

    @mock.patch.object(
        wizard.wizard_refund_rectify_from_origin.WizardRefundRectifyFromOrigin,
        "recarregar_lectures_between_dates",
    )
    def test_refund_rectify_by_origin_noLectures(self, mock_lectures):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.refund.rectify.from.origin")
        imd_obj = self.pool.get("ir.model.data")
        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")

        fact_prov_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0003"
        )[1]
        f1_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio_switching", "line_01_f1_import_01"
        )[1]
        fact_info = fact_obj.read(
            cursor,
            uid,
            fact_prov_id,
            ["origin", "polissa_id", "data_inici", "data_final", "cups_id"],
        )
        f1_obj.write(
            cursor,
            uid,
            [f1_id],
            {
                "invoice_number_text": fact_info["origin"],
                "cups_id": fact_info["cups_id"][0],
                "fecha_factura_desde": fact_info["data_inici"],
                "fecha_factura_hasta": fact_info["data_final"],
            },
        )
        f_cli_ids = fact_obj.search(
            cursor,
            uid,
            [
                ("data_inici", "<", fact_info["data_final"]),
                ("data_final", ">", fact_info["data_inici"]),
                ("type", "=", "out_invoice"),
            ],
        )
        self.assertEqual(len(f_cli_ids), 1)
        fact_obj.write(cursor, uid, f_cli_ids[0], {"state": "open"})

        ctx = {"active_id": f1_id, "active_ids": [f1_id]}

        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)
        mock_lectures.side_effect = lambda *x: 0

        wiz_obj.refund_rectify_by_origin(cursor, uid, wiz_id, context=ctx)
        mock_lectures.assert_called_with(
            cursor,
            uid,
            [wiz_id],
            fact_info["polissa_id"][0],
            fact_info["data_inici"],
            fact_info["data_final"],
            ctx,
        )
        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        self.assertEqual(
            wiz.info,
            "La pòlissa {}, que té l'F1 amb origen {}, "
            "no té lectures per esborrar. No s'hi actua.".format(
                fact_info["polissa_id"][1], fact_info["origin"]
            ),
        )

    def test_get_factures_client_by_dates_toRefundOne(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.refund.rectify.from.origin")
        imd_obj = self.pool.get("ir.model.data")

        fact_prov_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0003"
        )[1]
        fact_info = fact_obj.read(
            cursor, uid, fact_prov_id, ["origin", "polissa_id", "data_inici", "data_final"]
        )
        f_cli_ids = fact_obj.search(
            cursor,
            uid,
            [
                ("data_inici", "<", fact_info["data_final"]),
                ("data_final", ">", fact_info["data_inici"]),
                ("type", "=", "out_invoice"),
            ],
        )
        self.assertEqual(len(f_cli_ids), 1)
        fact_obj.write(cursor, uid, f_cli_ids[0], {"state": "open"})
        ctx = {"active_id": fact_prov_id, "active_ids": [fact_prov_id]}

        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)

        result = wiz_obj.get_factures_client_by_dates(
            cursor,
            uid,
            wiz_id,
            fact_info["polissa_id"][0],
            fact_info["data_inici"],
            fact_info["data_final"],
            context=ctx,
        )
        self.assertEqual(result[0], f_cli_ids)

    def test_get_factures_client_by_dates_toRefundTwo(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.refund.rectify.from.origin")
        imd_obj = self.pool.get("ir.model.data")

        fact_prov_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0003"
        )[1]
        fact_info = fact_obj.read(
            cursor, uid, fact_prov_id, ["origin", "polissa_id", "data_inici", "data_final"]
        )
        f_cli_ids = fact_obj.search(cursor, uid, [("type", "=", "out_invoice")])
        first_inici = datetime.strptime(fact_info["data_inici"], "%Y-%m-%d") - timedelta(days=2)
        first_final = first_inici + timedelta(days=7)
        second_inici = first_final + timedelta(days=1)
        fact_obj.write(
            cursor,
            uid,
            f_cli_ids[0],
            {
                "polissa_id": fact_info["polissa_id"][0],
                "data_inici": first_inici.strftime("%Y-%m-%d"),
                "data_final": first_final.strftime("%Y-%m-%d"),
                "state": "open",
            },
        )
        fact_obj.write(
            cursor,
            uid,
            f_cli_ids[1],
            {
                "polissa_id": fact_info["polissa_id"][0],
                "data_inici": second_inici.strftime("%Y-%m-%d"),
                "data_final": fact_info["data_final"],
                "state": "open",
            },
        )

        fact_obj.write(cursor, uid, f_cli_ids[0], {"state": "open"})
        ctx = {"active_id": fact_prov_id, "active_ids": [fact_prov_id]}

        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)

        result = wiz_obj.get_factures_client_by_dates(
            cursor,
            uid,
            wiz_id,
            fact_info["polissa_id"][0],
            fact_info["data_inici"],
            fact_info["data_final"],
            context=ctx,
        )
        self.assertEqual(sorted(result[0]), sorted(f_cli_ids[:2]))
