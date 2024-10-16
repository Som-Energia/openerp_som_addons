# -*- coding: utf-8 -*-
from osv import osv, fields


class WizardChangeToIndexadaAuvidiMulti(osv.osv_memory):

    _name = "wizard.change.to.indexada.auvidi.multi"

    def change_to_indexada_auvidi_multi(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz_og = self.browse(cursor, uid, ids[0], context=context)

        pol_ids = context.get("active_ids")
        failed_polisses = []
        error_polisses = []
        for pol_id in pol_ids:

            mode = self.get_current_mode(cursor, uid, pol_id)
            md = self.get_last_pending_modcon(cursor, uid, pol_id)

            if mode == 'atr':  # in periods
                if not md:
                    # Periods withe MODCON pending to indexed --> modcon pending Indexed + auvidi
                    # Create the MODCON to indexed
                    if not self.change_to_indexada_auvidi(
                        cursor, uid, pol_id, wiz_og.pricelist.id, wiz_og.coeficient_k
                    ):
                        self.add_to_list(cursor, uid, pol_id, failed_polisses)
                        break

                md = self.get_last_pending_modcon(cursor, uid, pol_id)
                # Periods with MODCON pending to indexed and auvidi --> don't do anything
                # Periods with MODCON pending to indexed --> modify the MODCON to add the auvdi
                md.te_auvidi = True

            else:  # in indexed
                if not md:
                    # Indexed with out MODCON to periods --> create MODCON to auvidi
                    pass
                else:
                    # Indexed with MODCON to periods --> error, cannot be done!
                    self.add_to_list(cursor, uid, pol_id, error_polisses)

        info = ""
        if failed_polisses:
            info += "\nLes pòlisses següents han fallat: {}".format(str(failed_polisses))
        if error_polisses:
            info += "\nLes pòlisses següents no es pot fer el canvi: {}".format(str(error_polisses))
        if not failed_polisses and not error_polisses:
            info = "Procés acabat correctament!"

        wiz_og.write({"state": "end", "info": info})

    def get_last_pending_modcon(self, cursor, uid, pol_id):
        pol_obj = self.pool.get("giscedata.polissa")
        pol = pol_obj.browse(cursor, uid, pol_id)
        if (pol.modcontractuals_ids[0].state == "pendent"
            and pol.mode_facturacio != pol.modcontractuals_ids[0].mode_facturacio
                and pol.modcontractuals_ids[0].mode_facturacio):
            return pol.modcontractuals_ids[0]
        else:
            return None

    def get_current_mode(self, cursor, uid, pol_id):
        pol_obj = self.pool.get("giscedata.polissa")
        data = pol_obj.read(cursor, uid, pol_id, ['mode_facturacio'])
        return data['mode_facturacio']

    def add_to_list(self, cursor, uid, pol_id, list_to_add):
        pol_obj = self.pool.get("giscedata.polissa")
        pol_name = pol_obj.read(cursor, uid, pol_id, ["name"])
        list_to_add.append(pol_name["name"])

    def change_to_indexada_auvidi(self, cursor, uid, pol_id, pricelist_id, coeficient_k):
        wz_chng_to_indx_obj = self.pool.get("wizard.change.to.indexada")
        ctx = {
            "active_id": pol_id,
            "business_pricelist": pricelist_id,
            "coeficient_k": coeficient_k,
        }
        params = {"change_type": "from_period_to_index"}
        wiz_id = wz_chng_to_indx_obj.create(cursor, uid, params, context=ctx)
        wiz = wz_chng_to_indx_obj.browse(cursor, uid, [wiz_id])[0]
        try:
            wz_chng_to_indx_obj.change_to_indexada(cursor, uid, [wiz.id], context=ctx)
            return True
        except Exception:
            return False

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
