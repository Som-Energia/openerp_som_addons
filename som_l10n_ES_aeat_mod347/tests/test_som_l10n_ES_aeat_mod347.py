# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction

import mock


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
