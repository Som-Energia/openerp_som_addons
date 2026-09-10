# -*- coding: utf-8 -*-
from __future__ import absolute_import

import re

from osv import osv, fields
from tools.translate import _


class ResPartnerCreditCard(osv.osv):
    _name = "res.partner.creditcard"
    _description = "Targetes de partner"
    _rec_name = "masked_number"

    _resolution_fields = ("token", "masked_number", "expiry_date", "cof_txnid")

    def resolve_for_payer(self, cursor, uid, partner_id, card_data, context=None):
        context = (context or {}).copy()
        values = dict(
            (field_name, card_data.get(field_name))
            for field_name in self._resolution_fields
        )
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise osv.except_osv(
                _("Invalid card data"),
                _("Missing required card fields: %s") % ", ".join(sorted(missing)),
            )

        self.check_perm(cursor, uid, "read", context=context)
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))",
            (values["token"],),
        )
        lookup_context = context.copy()
        lookup_context["active_test"] = False
        card_ids = self.search(
            cursor,
            uid,
            [("token", "=", values["token"])],
            context=lookup_context,
        )
        if card_ids:
            cards = self.read(
                cursor,
                uid,
                card_ids,
                ["partner_id", "active"] + list(self._resolution_fields),
                context=lookup_context,
            )
            compatible = [
                card
                for card in cards
                if card["active"]
                and card["partner_id"][0] == partner_id
                and all(card[name] == values[name] for name in self._resolution_fields)
            ]
            if len(cards) == 1 and compatible:
                return {"id": compatible[0]["id"], "disposition": "reused"}
            raise osv.except_osv(
                _("Card token conflict"),
                _("The stored card token has different payer or metadata."),
            )

        self.check_perm(cursor, uid, "create", context=context)
        values["partner_id"] = partner_id
        card_id = self.create(cursor, uid, values, context=context)
        return {"id": card_id, "disposition": "created"}

    _columns = {
        "active": fields.boolean("Activa"),
        "partner_id": fields.many2one(
            "res.partner", "Empresa", required=True, ondelete="cascade", select=True
        ),
        "token": fields.char("Token", size=128, required=True, select=True),
        "cof_txnid": fields.char("COF TxnId", size=128, select=True),
        "expiry_date": fields.char("Data caducitat", size=5),
        "masked_number": fields.char("Numero targeta", size=32, select=True),
    }

    def _check_expiry_date(self, cursor, uid, ids, context=None):
        pattern = re.compile(r"^(0[1-9]|1[0-2])/[0-9]{2}$")
        for card in self.browse(cursor, uid, ids, context=context):
            if not card.expiry_date:
                continue
            if not pattern.match(card.expiry_date):
                return False
        return True

    _constraints = [
        (
            _check_expiry_date,
            _("La data de caducitat ha de tenir format MM/YY."),
            ["expiry_date"],
        ),
    ]

    _defaults = {
        "active": lambda *a: True,
    }


ResPartnerCreditCard()
