# -*- coding: utf-8 -*-
from __future__ import absolute_import

import re

from osv import osv, fields


class ResPartnerCreditCard(osv.osv):
    _name = "res.partner.creditcard"
    _description = "Targetes de partner"
    _rec_name = "masked_number"

    def get_joins_order(self, order, tables):
        joins, order_clauses = super(ResPartnerCreditCard, self).get_joins_order(order, tables)
        expiry_field = '"{0}"."expiry_date"'.format(self._table)
        chronological_order = []
        for clause in order_clauses:
            field, direction = clause.rsplit(" ", 1)
            if field == expiry_field:
                # MM/YY is kept as text; sort by YY and then MM instead.
                for position in (4, 1):
                    chronological_order.append(
                        "substring(NULLIF({0}, '') from {1} for 2) {2}".format(
                            expiry_field, position, direction
                        )
                    )
            else:
                chronological_order.append(clause)
        return joins, chronological_order

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
        ),
    ]

    _defaults = {
        "active": lambda *a: True,
    }


ResPartnerCreditCard()
