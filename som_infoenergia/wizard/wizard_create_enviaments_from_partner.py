# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

STATES = [("init", "Estat Inicial"), ("finished", "Estat Final")]


class WizardAddPartnersLot(osv.osv_memory):
    _name = "wizard.add.partners.lot"

    def add_partners_lot(self, cursor, uid, ids, context=None):

        if not context.get("active_id", False) or len(context.get("active_ids", False)) > 1:
            raise osv.except_osv(_("Error!"), _("S'ha de seleccionar un lot"))

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        lot_obj = self.pool.get("som.infoenergia.lot.enviament")
        partner_obj = self.pool.get("res.partner")

        wiz = self.browse(cursor, uid, ids[0])

        search_params = []
        search_params_relation = {
            "category": [("category_id", "=", wiz.category.id)],
            "active": [("active", "=", wiz.active)],
            "baixa": [("baixa", "=", wiz.baixa)],
            "init_date": [("data_baixa_soci", ">=", wiz.init_date)],
            "end_date": [("data_baixa_soci", "<=", wiz.end_date)],
            "vat": [("vat", "ilike", "%{}%".format(wiz.vat))],
        }
        for field in search_params_relation.keys():
            if getattr(wiz, field):
                search_params += search_params_relation[field]

        partner_ids = []
        soci_obj = self.pool.get("somenergia.soci")

        if wiz.te_aportacions:
            inv_obj = self.pool.get("generationkwh.investment")
            inv_ids = inv_obj.search(cursor, uid, [("emission_id.type", "=", "apo")])
            member_ids = [
                x["member_id"][0] for x in inv_obj.read(cursor, uid, inv_ids, ["member_id"])
            ]
            partner_ids += [
                x["partner_id"][0] for x in soci_obj.read(cursor, uid, member_ids, ["partner_id"])
            ]

        if wiz.es_soci:
            soci_ids = soci_obj.search(cursor, uid, [("data_baixa_soci", "=", False)])
            partner_ids += [
                x["partner_id"][0] for x in soci_obj.read(cursor, uid, soci_ids, ["partner_id"])
            ]

        if wiz.has_gkwh:
            soci_ids = soci_obj.search(
                cursor, uid, [("data_baixa_soci", "=", False), ("has_gkwh", "=", True)]
            )
            partner_ids += [
                x["partner_id"][0] for x in soci_obj.read(cursor, uid, soci_ids, ["partner_id"])
            ]

        partner_ids = list(set(partner_ids))
        search_params += [("id", "in", partner_ids)] if partner_ids else ""

        res_ids = partner_obj.search(cursor, uid, search_params)

        self.write(
            cursor,
            uid,
            ids,
            {
                "state": "finished",
                "len_result": "La cerca ha trobat {} resultats".format(len(res_ids)),
            },
        )
        ctx = {"from_model": "partner_id"}
        lot_obj.create_enviaments_from_object_list(
            cursor, uid, context.get("active_id"), res_ids, ctx
        )

    _columns = {
        "category": fields.many2one(
            "res.partner.category", "Categoria", help=_(u"Categoria de Partner")
        ),
        "active": fields.boolean("Actiu"),
        "baixa": fields.boolean("Baixa"),
        "init_date": fields.date("Data Baixa (Inici)"),
        "end_date": fields.date("Data Baixa (Fi)"),
        "has_gkwh": fields.boolean(u"Té GKwh"),
        "vat": fields.char("NIF", size=12),
        "state": fields.selection(STATES, _(u"Estat del wizard")),
        "len_result": fields.text("Resultat de la cerca", readonly=True),
        "te_aportacions": fields.boolean(u"Té Aportacions al Capital Social"),
        "es_soci": fields.boolean(u"És sòcia"),
    }

    _defaults = {
        "state": "init",
    }


WizardAddPartnersLot()
