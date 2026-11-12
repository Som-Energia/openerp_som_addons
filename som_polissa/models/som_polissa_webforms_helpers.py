from osv import osv


class SomPolissaWebformsHelpers(osv.osv_memory):

    _name = "som.polissa.webforms.helpers"

    def www_get_iban(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (list, set, tuple)):
            polissa_id = ids[0]
        else:
            polissa_id = ids

        pol_obj = self.pool.get("giscedata.polissa")
        bank = pol_obj.read(cursor, uid, polissa_id, ["bank"], context=context)
        iban = ""
        if bank.get("bank"):
            iban_suffix = bank["bank"][1][-4:]
            iban = "**** **** **** **** **** {}".format(iban_suffix)
        return iban

    def www_check_iban(self, cursor, uid, iban, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get("giscedata.polissa")
        result = pol_obj.www_check_iban(cursor, uid, iban, context=context)

        return result

    def _update_payment_lines(self, cursor, uid, polissa_id, context):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")
        line_obj = self.pool.get("payment.line")

        search_vals = [
            ("polissa_id", "=", polissa_id),
            ("type", "in", ["out_invoice", "out_refund"]),
            ("state", "in", ["draft", "open"]),
        ]
        factura_ids = fact_obj.search(cursor, uid, search_vals, context=context)
        factures = fact_obj.browse(cursor, uid, factura_ids)

        draft_order_ids = []
        for factura in factures:
            if factura.payment_order_id and factura.payment_order_id.state == "draft":
                draft_order_ids.append(factura.payment_order_id.id)
            else:
                continue

        if draft_order_ids:
            bank_id = pol_obj.read(cursor, uid, polissa_id, ["bank"], context=context)["bank"][0]
            partner_id = pol_obj.read(cursor, uid, polissa_id, ["titular"], context=context)[
                "titular"
            ][0]
            line_ids = line_obj.search(
                cursor,
                uid,
                [
                    ("order_id", "in", draft_order_ids),
                    ("partner_id", "=", partner_id),
                ],
            )
            line_obj.write(cursor, uid, line_ids, {"bank_id": bank_id})

    def www_set_iban(self, cursor, uid, ids, iban, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (list, set, tuple)):
            polissa_id = ids[0]
        else:
            polissa_id = ids

        wiz_obj = self.pool.get("wizard.bank.account.change")

        vals = {
            "account_iban": iban,
            "update_fact_no_pagades": True,
            "print_mandate": False,
            "state": "end",
        }

        context = {"active_id": polissa_id}

        wiz_id = wiz_obj.create(cursor, uid, vals, context=context)
        wizard_result = wiz_obj.action_bank_account_change_confirm(
            cursor, uid, [wiz_id], context=context
        )

        result = False
        if wizard_result == {}:
            self._update_payment_lines(cursor, uid, polissa_id, context=context)
            result = True
        return result


SomPolissaWebformsHelpers()
