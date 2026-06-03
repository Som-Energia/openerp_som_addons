# -*- coding: utf-8 -*-
import re

from osv import osv, fields


class ResPartnerCreditCard(osv.osv):
    _name = "res.partner.creditcard"
    _description = "Targetes de partner"
    _rec_name = "masked_number"

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
            "La data de caducitat ha de tenir format MM/YY.",
            ["expiry_date"],
        )
    ]

    _sql_constraints = [
        (
            "res_partner_creditcard_token_unique",
            "unique(token)",
            "Ja existeix una targeta amb aquest token.",
        )
    ]

    _defaults = {
        "active": lambda *a: True,
    }


ResPartnerCreditCard()
