# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from destral.transaction import Transaction
from datetime import date
import unittest
from l10n_ES_remesas.wizard.export_remesas import FakeInvoice


def EqualFakeInvoice(obj1, obj2, msg=None):
    """
    Compares obj1 an obj2 of type FakeInvoice
    :param obj1:
    :param obj2:
    :raises: self.failureException
    """
    fields = ["mandate_id", "date_invoice", "name", "number", "company_id"]
    error_fields = []
    for field in fields:
        obj1_val = getattr(obj1, field, "No1")
        obj2_val = getattr(obj2, field, "No2")
        if obj1_val != obj2_val:
            error_fields.append((field, obj1_val, obj2_val))
    if len(error_fields):
        msg_list = "\n".join(["* field '{}': '{}'!='{}'".format(*f) for f in error_fields])
        raise unittest.TestCase.failureException("No Equal FakeInvoice:\n{}".format(msg_list))


class ExportRemesesWizard(testing.OOTestCase):
    def setUp(self):
        self.addTypeEqualityFunc(FakeInvoice, EqualFakeInvoice)

    def test_is_equal_fakeinvoice(self):
        vals = (1, "2016-10-26", "test1", "1", 1)
        obj1 = FakeInvoice(*vals)
        obj2 = FakeInvoice(*vals)

        self.assertEqual(obj1, obj2)

        vals_full = list(vals)
        for i in range(0, len(vals)):
            vals1 = list(vals)
            vals1[i] = "error"
            vals_full[i] = "error"
            obj = FakeInvoice(*vals1)
            with self.assertRaises(AssertionError):
                self.assertEqual(obj, obj1)

        full = FakeInvoice(*vals_full)
        with self.assertRaises(AssertionError):
            self.assertEqual(obj1, full)

    def test_get_invoice(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            pool = self.openerp.pool
            imd_obj = pool.get("ir.model.data")

            payorder_obj = pool.get("payment.order")
            payline_obj = pool.get("payment.line")
            paymandate_obj = pool.get("payment.mandate")
            pool.get("res.partner.bank")

            wiz_obj = pool.get("wizard.payment.file.spain")

            account_id = imd_obj.get_object_reference(cursor, uid, "account", "a_sale")[1]
            currency_id = imd_obj.get_object_reference(cursor, uid, "base", "EUR")[1]
            remesa1_id = imd_obj.get_object_reference(
                cursor, uid, "account_payment", "payment_order_demo"
            )[1]
            country_id = imd_obj.get_object_reference(cursor, uid, "base", "es")[1]

            remesa = payorder_obj.browse(cursor, uid, remesa1_id)
            iban = "ES6415383216135305497255"
            acc_number = iban[4:]
            remesa.mode.bank_id.write({"acc_number": acc_number, "iban": iban})
            remesa.mode.bank_id.partner_id.write({"vat": "ES11111111H"})

            remesa = payorder_obj.browse(cursor, uid, remesa1_id)

            mandate_vals = {
                "debtor_name": "Partner Test",
                "debtor_vat": "ES11111111H",
                "debtor_address": "Here",
                "debtor_state": 17,
                "debtor_country": country_id,
                "debtor_iban": iban,
                # 'reference': 'res.partner,{}'.format(
                #    remesa.mode.bank_id.partner_id.id
                # ),
                "notes": "PAYMENT TEST LINE",
                "name": "abcdef123456789",
                "creditor_code": "123456789",
                "date": date.today().strftime("%Y-%m-%d"),
            }

            paymandate_obj.create(cursor, uid, mandate_vals)

            # Create payment line
            # payment line with invoice
            vals = {
                "name": "000001/F",
                "order_id": remesa1_id,
                "currency": currency_id,
                "partner_id": remesa.mode.bank_id.partner_id.id,
                "company_currency": currency_id,
                "bank_id": remesa.mode.bank_id.id,
                "state": "normal",
                "amount_currency": -1 * 100,
                "account_id": account_id,
                "communication": "PAYMENT TEST LINE",
                "comm_text": "PAYMENT TEST LINE",
                "move_line_ids": [1],
            }

            payline_id = payline_obj.create(cursor, uid, vals)

            # Gets invoice from id
            payment_line_from_id = wiz_obj.get_invoice(cursor, uid, payline_id)
            self.assertIsInstance(payment_line_from_id, FakeInvoice)

            # Gets invoice from object
            payline = payline_obj.browse(cursor, uid, payline_id)
            payment_line_from_obj = wiz_obj.get_invoice(cursor, uid, payline)
            self.assertIsInstance(payment_line_from_obj, FakeInvoice)

            self.assertEqual(payment_line_from_obj, payment_line_from_id)

            payment_line_from_obj.mandate_id = payline.mandate
            payment_line_from_obj.date_invoice = payline.create_date
            payment_line_from_obj.name = payline.name
            payment_line_from_obj.number = payline.name
            payment_line_from_obj.company_id = payline.order_id.user_id.company_id
