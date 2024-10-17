# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import date, timedelta


class WizardChangeToIndexadaAuvidiMulti(osv.osv_memory):

    _name = "wizard.change.to.indexada.auvidi.multi"

    def change_to_indexada_auvidi_multi(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz_og = self.browse(cursor, uid, ids[0], context=context)

        pol_ids = context.get("active_ids")
        faileds = []
        from_wainting_periodes = []
        from_periodes = []
        from_waiting_indexed = []
        from_already_there = []
        from_indexed = []
        from_auvidi = []
        msg = []

        for pol_id in pol_ids:

            mode = self.get_current_mode(cursor, uid, pol_id)
            md = self.get_last_pending_modcon(cursor, uid, pol_id)

            if mode == 'atr':  # in periods
                if not md:
                    # Periods withe MODCON pending to indexed --> modcon pending Indexed + auvidi
                    # Create the MODCON to indexed
                    if not self.change_to_indexada(cursor, uid, pol_id):
                        faileds.append(pol_id)
                    else:
                        md = self.get_last_pending_modcon(cursor, uid, pol_id)
                        self.set_auvidi(cursor, uid, md.id)
                        from_periodes.append(pol_id)
                else:
                    if md.te_auvidi:
                        # Periods with MODCON pending to indexed and auvidi --> don't do anything
                        from_already_there.append(pol_id)
                    else:
                        # Periods with MODCON pending to indexed --> modify the MODCON to add auvdi
                        self.set_auvidi(cursor, uid, md.id)
                        from_waiting_indexed.append(pol_id)
            else:  # in indexed
                if not md:
                    if self.get_current_auvidi(cursor, uid, pol_id):
                        # Indexed and auvidiwith out MODCON to periods --> don't do anything
                        from_auvidi.append(pol_id)
                    else:
                        # Indexed with out MODCON to periods --> create MODCON to auvidi
                        if not self.create_auvidi_pending_modcon(cursor, uid, pol_id):
                            faileds.append(pol_id)
                        else:
                            from_indexed.append(pol_id)
                else:
                    # Indexed with MODCON to periods --> error, cannot be done!
                    from_wainting_periodes.append(pol_id)

        if from_periodes:
            pols = self.get_list_polissa_names(cursor, uid, from_periodes)
            msg.append("Pòlisses que estan a periodes:")
            msg.append(" - Creada modcon a indexada + auvidi: {}".format(pols))

        if from_waiting_indexed:
            pols = self.get_list_polissa_names(cursor, uid, from_waiting_indexed)
            msg.append("Pòlisses que estan a periodes i tenen modcon a indexada:")
            msg.append(" - Modcon modificada, afegit auvidi: {}".format(pols))

        if from_already_there:
            pols = self.get_list_polissa_names(cursor, uid, from_already_there)
            msg.append("Pòlisses que estan a periodes i tenen modcon a indexada amb auvidi:")
            msg.append(" - No fem res: {}".format(pols))

        if from_indexed:
            pols = self.get_list_polissa_names(cursor, uid, from_indexed)
            msg.append("Pòlisses que estan a indexada:")
            msg.append(" - Creada modcon a auvidi: {}".format(pols))

        if from_auvidi:
            pols = self.get_list_polissa_names(cursor, uid, from_auvidi)
            msg.append("Pòlisses que estan a indexada amb auvidi:")
            msg.append(" - No fem res: {}".format(pols))

        if from_wainting_periodes:
            pols = self.get_list_polissa_names(cursor, uid, from_wainting_periodes)
            msg.append("ERROR Pòlisses que estan a indexada amb modcon pendent a periodes:")
            msg.append(" - {}".format(pols))

        if faileds:
            pols = self.get_list_polissa_names(cursor, uid, faileds)
            msg.append("ERROR Pòlisses que han fallat al crear modcon:")
            msg.append(" - {}".format(pols))

        if not faileds and not from_wainting_periodes:
            msg.append("Procés acabat correctament!")

        wiz_og.write({"state": "end", "info": "\n".join(msg)})

    def quit_auvidi_multi(self, cursor, uid, ids, context=None):
        pass

    def get_last_pending_modcon(self, cursor, uid, pol_id):
        pol_obj = self.pool.get("giscedata.polissa")
        pol = pol_obj.browse(cursor, uid, pol_id)
        if pol.modcontractuals_ids[0].state == "pendent":
            if (pol.mode_facturacio != pol.modcontractuals_ids[0].mode_facturacio
                    or pol.mode_facturacio == 'index'):
                if pol.modcontractuals_ids[0].mode_facturacio:
                    return pol.modcontractuals_ids[0]
        return None

    def get_current_mode(self, cursor, uid, pol_id):
        pol_obj = self.pool.get("giscedata.polissa")
        data = pol_obj.read(cursor, uid, pol_id, ['mode_facturacio'])
        return data['mode_facturacio']

    def get_current_auvidi(self, cursor, uid, pol_id):
        pol_obj = self.pool.get("giscedata.polissa")
        data = pol_obj.read(cursor, uid, pol_id, ['te_auvidi'])
        return data['te_auvidi']

    def set_auvidi(self, cursor, uid, modcon_id, value=True):
        mod_obj = self.pool.get("giscedata.polissa.modcontractual")
        mod_obj.write(cursor, uid, modcon_id, {'te_auvidi': value})

    def get_list_polissa_names(self, cursor, uid, pol_ids):
        pol_obj = self.pool.get("giscedata.polissa")
        pol_data = pol_obj.read(cursor, uid, pol_ids, ["name"])
        return ', '.join([pol['name'] for pol in pol_data])

    def change_to_indexada(self, cursor, uid, pol_id):
        wz_chng_to_indx_obj = self.pool.get("wizard.change.to.indexada")
        ctx = {"active_id": pol_id}
        params = {"change_type": "from_period_to_index"}
        wiz_id = wz_chng_to_indx_obj.create(cursor, uid, params, context=ctx)
        wiz = wz_chng_to_indx_obj.browse(cursor, uid, [wiz_id])[0]
        try:
            wz_chng_to_indx_obj.change_to_indexada(cursor, uid, [wiz.id], context=ctx)
            return True
        except Exception:
            return False

    def create_auvidi_pending_modcon(self, cursor, uid, pol_id):
        pol_obj = self.pool.get("giscedata.polissa")
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        auvidi_flag = {
            'te_auvidi': True,
        }
        try:
            pol_obj.create_contracte(cursor, uid, pol_id, tomorrow, auvidi_flag)
            return True
        except Exception:
            return False

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "info": fields.text("Description"),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


WizardChangeToIndexadaAuvidiMulti()
