# -*- coding: utf-8 -*-
from osv import osv, fields


class WizardChangeToIndexadaAuvidiMulti(osv.osv_memory):

    _name = "wizard.change.to.indexada.auvidi.multi"

    def change_to_indexada_auvidi_multi(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz_og = self.browse(cursor, uid, ids[0], context=context)

        pol_ids = context.get("active_ids")
        wz_chng_to_indx_obj = self.pool.get("wizard.change.to.indexada")
        pol_obj = self.pool.get("giscedata.polissa")
        failed_polisses = []
        for pol_id in pol_ids:
            ctx = {
                "active_id": pol_id,
                "business_pricelist": wiz_og.pricelist.id,
                "coeficient_k": wiz_og.coeficient_k,
            }
            params = {"change_type": "from_period_to_index"}
            wiz_id = wz_chng_to_indx_obj.create(cursor, uid, params, context=ctx)
            wiz = wz_chng_to_indx_obj.browse(cursor, uid, [wiz_id])[0]
            try:
                wz_chng_to_indx_obj.change_to_indexada(cursor, uid, [wiz.id], context=ctx)
            except Exception:
                pol_name = pol_obj.read(cursor, uid, pol_id, ["name"])
                failed_polisses.append(pol_name["name"])

        info = ""
        if failed_polisses:
            info += "\nLes pòlisses següents han fallat: {}".format(str(failed_polisses))
        if not failed_polisses:
            info = "Procés acabat correctament!"

        wiz_og.write({"state": "end", "info": info})

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "info": fields.text("Description"),
        "pricelist": fields.many2one("product.pricelist", "Tarifa"),
        "coeficient_k": fields.float("Coeficient K", digits=(9, 3)),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


WizardChangeToIndexadaAuvidiMulti()
