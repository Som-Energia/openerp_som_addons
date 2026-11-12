# -*- coding: utf-8 -*-

from osv import osv, fields


class FacturacioExtra(osv.osv):

    _name = "giscedata.facturacio.extra"
    _inherit = "giscedata.facturacio.extra"

    _columns = {
        "polissa_state": fields.related(
            "polissa_id", "state", type="char", string="Estat pòlissa", readonly=True
        ),
    }


FacturacioExtra()


class GiscedataFacturacioFacturaSendEmail(osv.osv):
    """Classe temporal per enviar els mails de les factures F010 (Canvi tarifes)"""

    _name = "giscedata.facturacio.factura.send.email"

    _columns = {
        "factura_id": fields.many2one("giscedata.facturacio.factura", "Factura"),
        "enviat": fields.boolean("Enviat"),
    }


GiscedataFacturacioFacturaSendEmail()


class GiscedataPolissa(osv.osv):

    _inherit = "giscedata.polissa"

    def do_extra_actions_fix_facturacurta_fc01(self, cursor, uid, fact_ids, context=None):
        if not isinstance(fact_ids, list):
            fact_ids = [fact_ids]
        eo = self.pool.get("giscedata.facturacio.factura.send.email")
        for fact_id in fact_ids:
            if not eo.search(cursor, uid, [("factura_id", "=", fact_id)]):
                eo.create(cursor, uid, {"factura_id": fact_id, "enviat": False})

        return super(GiscedataPolissa, self).do_extra_actions_fix_facturacurta_fc01(
            cursor, uid, fact_ids, context=context
        )


GiscedataPolissa()


class WizardFacturesPerEmail(osv.osv_memory):

    _name = "wizard.factures.per.email"
    _inherit = "wizard.factures.per.email"

    def action_enviar_lot_per_mail(self, cursor, uid, ids, context=None):
        if not context:
            context = {}
        ctx = context.copy()
        eo = self.pool.get("giscedata.facturacio.factura.send.email")
        eids = eo.search(cursor, uid, [("enviat", "=", False)])
        if eids:
            ctx["extra_factura_ids"] = [
                x["factura_id"][0] for x in eo.read(cursor, uid, eids, ["factura_id"])
            ]
        res = super(WizardFacturesPerEmail, self).action_enviar_lot_per_mail(
            cursor, uid, ids, context=ctx
        )
        if eids:
            eo.write(cursor, uid, eids, {"enviat": True})
        return res


WizardFacturesPerEmail()
