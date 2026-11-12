# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from destral.transaction import Transaction

import mock


class Soml10nEsAeatMod347AmountExclusions(testing.OOTestCaseWithCursor):
    def test_donation_amount_exclusions_are_grouped_by_invoice_and_quarter(self):
        calculator = self.openerp.pool.get(
            "l10n.es.aeat.mod347.calculate_records"
        )
        account_obj = mock.Mock()
        account_obj.search.return_value = [99]

        invoice_obj = mock.Mock()
        invoice_obj.search.return_value = [101, 102]
        invoice_first = mock.Mock()
        invoice_first.id = 101
        invoice_first.period_id.quarter = "FIRST"
        invoice_second = mock.Mock()
        invoice_second.id = 102
        invoice_second.period_id.quarter = "SECOND"
        invoice_obj.browse.return_value = [invoice_first, invoice_second]

        invoice_line_obj = mock.Mock()
        invoice_line_obj.search.return_value = [201, 202, 203]
        invoice_line_obj.read.return_value = [
            {"invoice_id": (101, "INV/101"), "price_subtotal": 10.0},
            {"invoice_id": (101, "INV/101"), "price_subtotal": 2.5},
            {"invoice_id": (102, "INV/102"), "price_subtotal": 7.5},
        ]
        models = {
            "account.account": account_obj,
            "account.invoice": invoice_obj,
            "account.invoice.line": invoice_line_obj,
        }

        with mock.patch.object(
            calculator.pool, "get", side_effect=lambda model: models[model]
        ):
            exclusions = calculator._get_mod347_amount_exclusions(
                self.cursor,
                self.uid,
                [1, 2],
                "out_invoice",
                [301, 302],
                sii_send_invoices=True,
            )

        self.assertEqual(exclusions["total"], 20.0)
        self.assertEqual(
            exclusions["quarters"], {"FIRST": 12.5, "SECOND": 7.5}
        )
        self.assertEqual(exclusions["invoices"], {101: 12.5, 102: 7.5})
        self.assertIn(
            ("sii_registered", "=", True), invoice_obj.search.call_args[0][2]
        )


class Soml10nEsAeatMod347Report(testing.OOTestCase):
    def test_notify_clients_from_347_report__when_no_report(self):
        report347_obj = self.openerp.pool.get("l10n.es.aeat.mod347.report")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            report_id = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "aeat_347_report_1"
            )[1]

            report = report347_obj.browse(cursor, uid, report_id)
            report.write({"state": "draft"})
            report347_obj.unlink(cursor, uid, [report_id])

            ret_value = report347_obj.send_email_clients_import_over_limit(cursor, uid, [report_id])
            self.assertFalse(ret_value)

    def test_notify_clients_from_347_report__when_report_not_calculated(self):
        report347_obj = self.openerp.pool.get("l10n.es.aeat.mod347.report")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            report_id = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "aeat_347_report_1"
            )[1]

            report = report347_obj.browse(cursor, uid, report_id)
            report.write({"state": "draft"})

            ret_value = report347_obj.send_email_clients_import_over_limit(cursor, uid, [report_id])
            self.assertFalse(ret_value)

    def test_notify_clients_from_347_report__when_report_has_no_partners(self):
        report347_obj = self.openerp.pool.get("l10n.es.aeat.mod347.report")
        partner_obj = self.openerp.pool.get("l10n.es.aeat.mod347.partner_record")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            report_id = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "aeat_347_report_1"
            )[1]
            partner_id_1 = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "aeat_347_partner_record_1"
            )[1]
            partner_id_2 = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "aeat_347_partner_record_2"
            )[1]

            partner_obj.unlink(cursor, uid, [partner_id_1, partner_id_2])

            ret_value = report347_obj.send_email_clients_import_over_limit(cursor, uid, [report_id])
            self.assertFalse(ret_value)

    def test_notify_clients_from_347_report__when_report_has_no_client_partners(self):
        report347_obj = self.openerp.pool.get("l10n.es.aeat.mod347.report")
        partner_obj = self.openerp.pool.get("l10n.es.aeat.mod347.partner_record")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            report_id = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "aeat_347_report_1"
            )[1]
            partner_id_1 = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "aeat_347_partner_record_1"
            )[1]

            partner_obj.unlink(cursor, uid, [partner_id_1])

            ret_value = report347_obj.send_email_clients_import_over_limit(cursor, uid, [report_id])
            self.assertFalse(ret_value)

    @mock.patch(
        "som_l10n_ES_aeat_mod347.som_l10n_ES_aeat_mod347.SomL10nEsAeatMod347Helper.send_email"
    )
    def test_notify_clients_from_347_report__when_report_with_client_partners(self, mock_function):
        report347_obj = self.openerp.pool.get("l10n.es.aeat.mod347.report")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            report_id = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "aeat_347_report_1"
            )[1]
            from_email_id = imd_obj.get_object_reference(
                cursor, uid, "base_extended_som", "info_energia_from_email"
            )[1]
            template_id = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "email_model_347_resum"
            )[1]
            partner_record_id = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "aeat_347_partner_record_1"
            )[1]

            ret_value = report347_obj.send_email_clients_import_over_limit(cursor, uid, [report_id])

            self.assertTrue(ret_value)

            expected_ctx = {"email_from": from_email_id, "template_id": template_id}
            mock_function.assert_called_with(cursor, uid, mock.ANY, partner_record_id, expected_ctx)


class Soml10nEsAeatMod347Partner(testing.OOTestCase):
    def test_notify_clients_from_347_partner__when_no_partners(self):
        partner_record_obj = self.openerp.pool.get("l10n.es.aeat.mod347.partner_record")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            ret_value = partner_record_obj.send_annual_import_summary_email(cursor, uid, [])
            self.assertFalse(ret_value)

    def test_notify_clients_from_347_partner__when_report_not_calculated(self):
        partner_record_obj = self.openerp.pool.get("l10n.es.aeat.mod347.partner_record")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            partner_record_id = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "aeat_347_partner_record_1"
            )[1]

            report = partner_record_obj.browse(cursor, uid, partner_record_id).report_id
            report.write({"state": "draft"})

            ret_value = partner_record_obj.send_annual_import_summary_email(
                cursor, uid, [partner_record_id]
            )
            self.assertFalse(ret_value)

    @mock.patch(
        "som_l10n_ES_aeat_mod347.som_l10n_ES_aeat_mod347.SomL10nEsAeatMod347Helper.send_email"
    )
    def test_notify_clients_from_347_partner__when_report_with_partners(self, mock_function):
        partner_record_obj = self.openerp.pool.get("l10n.es.aeat.mod347.partner_record")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            from_email_id = imd_obj.get_object_reference(
                cursor, uid, "base_extended_som", "info_energia_from_email"
            )[1]
            template_id = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "email_model_347_resum"
            )[1]
            partner_record_id = imd_obj.get_object_reference(
                cursor, uid, "som_l10n_ES_aeat_mod347", "aeat_347_partner_record_1"
            )[1]

            ret_value = partner_record_obj.send_annual_import_summary_email(
                cursor, uid, [partner_record_id]
            )

            self.assertTrue(ret_value)

            expected_ctx = {"email_from": from_email_id, "template_id": template_id}
            mock_function.assert_called_with(cursor, uid, mock.ANY, partner_record_id, expected_ctx)
