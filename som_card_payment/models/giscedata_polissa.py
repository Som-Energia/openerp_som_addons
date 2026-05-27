# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataPolissa(osv.osv):
    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def onchange_tipo_pago(self, cursor, uid, ids, tipo_pago, pagador, context=None):
        res = super(GiscedataPolissa, self).onchange_tipo_pago(
            cursor, uid, ids, tipo_pago, pagador, context=context
        )
        res.setdefault("value", {})
        if not tipo_pago:
            res["value"].update({"creditcard": False})
            return res

        payment_type = self.pool.get("payment.type").browse(cursor, uid, tipo_pago, context=context)
        if payment_type.code != "COBRAMENT_RECURRENT_TARGETA":
            res["value"].update({"creditcard": False})
            return res

        if not pagador:
            res.setdefault("value", {}).update({"creditcard": False})
            return res

        card_obj = self.pool.get("res.partner.creditcard")
        card_ids = card_obj.search(cursor, uid, [("partner_id", "=", pagador)], context=context)
        res["value"].update({"creditcard": card_ids[0] if len(card_ids) == 1 else False})
        return res

    def _check_card_payment_data(self, cursor, uid, ids, context=None):
        for polissa in self.browse(cursor, uid, ids, context=context):
            if not polissa.tipo_pago or polissa.tipo_pago.code != "COBRAMENT_RECURRENT_TARGETA":
                continue
            if not polissa.creditcard:
                return False
            if polissa.pagador and polissa.creditcard.partner_id.id != polissa.pagador.id:
                return False
        return True

    _columns = {
        "creditcard": fields.many2one(
            "res.partner.creditcard",
            "Targeta",
            ondelete="restrict",
            readonly=True,
            states={
                "esborrany": [("readonly", False)],
                "validar": [("readonly", False)],
                "modcontractual": [("readonly", False)],
            },
        ),
    }

    _constraints = [
        (
            _check_card_payment_data,
            "Cal indicar una targeta del pagador quan el tipus de pagament "
            "es cobrament recurrent per targeta.",
            ["tipo_pago", "creditcard", "pagador"],
        )
    ]


GiscedataPolissa()


class GiscedataPolissaModcontractual(osv.osv):
    _name = "giscedata.polissa.modcontractual"
    _inherit = "giscedata.polissa.modcontractual"

    def _check_card_payment_data(self, cursor, uid, ids, context=None):
        for modcontractual in self.browse(cursor, uid, ids, context=context):
            payment_type = getattr(modcontractual, "tipo_pago", False)
            if not payment_type or payment_type.code != "COBRAMENT_RECURRENT_TARGETA":
                continue

            creditcard = getattr(modcontractual, "creditcard", False)
            if not creditcard:
                return False

            pagador = getattr(modcontractual, "pagador", False)
            if not pagador and getattr(modcontractual, "polissa_id", False):
                pagador = modcontractual.polissa_id.pagador

            if pagador and creditcard.partner_id.id != pagador.id:
                return False
        return True

    _columns = {
        "creditcard": fields.many2one("res.partner.creditcard", "Targeta", ondelete="restrict"),
    }

    _constraints = [
        (
            _check_card_payment_data,
            "Cal indicar una targeta del pagador quan el tipus de pagament "
            "es cobrament recurrent per targeta.",
            ["tipo_pago", "creditcard", "pagador"],
        )
    ]


GiscedataPolissaModcontractual()
