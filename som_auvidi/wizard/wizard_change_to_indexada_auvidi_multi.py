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
                    # Periods without MODCON pending to indexed --> modcon pending Indexed + auvidi
                    # Create the MODCON to indexed
                    if not self.change_to_indexada(cursor, uid, pol_id, {'te_auvidi': True}):
                        faileds.append(pol_id)
                    else:
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
                        if not self.create_auvidi_pending_modcon(cursor, uid, pol_id, True):
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

    def quit_auvidi_multi(self, cursor, uid, ids, context=None):  # noqa: C901
        if context is None:
            context = {}

        wiz_og = self.browse(cursor, uid, ids[0], context=context)

        pol_ids = context.get("active_ids")
        faileds = []
        from_already_there = []
        msg = []

        for pol_id in pol_ids:

            mode = self.get_current_mode(cursor, uid, pol_id)
            auvidi = self.get_current_auvidi(cursor, uid, pol_id)
            md = self.get_last_pending_modcon(cursor, uid, pol_id)

            faileds = []
            from_indexed_auvidi = []
            from_indexed_waiting_auvidi = []
            from_indexed_waiting_no_auvidi = []
            from_indexed_no_auvidi = []
            from_periods_auvidi = []
            from_periods_waiting_indexada_auvidi = []
            from_periods_waiting_no_auvidi = []
            from_already_there = []

            if mode == 'index':  # in indexed
                if auvidi:  # has auvidi
                    if not md:  # does not have any pending modcon
                        # Indexed + auvidi --> create MODCON to quit auvidi
                        if not self.create_auvidi_pending_modcon(cursor, uid, pol_id, False):
                            faileds.append(pol_id)
                        else:
                            from_indexed_auvidi.append(pol_id)
                    else:  # has a pending MODCON
                        # Indexed + auvidi + MODCON --> modify the MODCON to quit auvidi
                        if md.te_auvidi:
                            self.set_auvidi(cursor, uid, md.id, False)
                            from_indexed_waiting_auvidi.append(pol_id)
                        else:
                            from_indexed_waiting_no_auvidi.append(pol_id)
                else:  # does not has auvidi
                    if md and md.te_auvidi:
                        # Indexed + MODCON auvidi --> modify the MODCON to quit auvidi
                        self.set_auvidi(cursor, uid, md.id, False)
                        from_indexed_waiting_auvidi.append(pol_id)
                    else:
                        from_indexed_no_auvidi.append(pol_id)

            else:  # in periods
                if auvidi:  # periods and auvidi --> Error!!
                    if not md:  # does not have any pending modcon
                        if not self.create_auvidi_pending_modcon(cursor, uid, pol_id, False):
                            faileds.append(pol_id)
                        else:
                            from_periods_auvidi.append(pol_id)
                    else:
                        # periods + auvidi + MODCON --> modify the MODCON to quit auvidi
                        if md.te_auvidi:
                            self.set_auvidi(cursor, uid, md.id, False)
                            from_periods_waiting_indexada_auvidi.append(pol_id)
                        else:
                            from_periods_waiting_no_auvidi.append(pol_id)
                else:  # periods and not auvidi
                    if not md:  # does not have any pending modcon
                        # Periods no auvidi and no modcon --> don't do anything
                        from_already_there.append(pol_id)
                    else:
                        if md.te_auvidi:
                            self.set_auvidi(cursor, uid, md.id, False)
                            from_periods_waiting_indexada_auvidi.append(pol_id)
                        else:
                            from_periods_waiting_no_auvidi.append(pol_id)

        if from_indexed_auvidi:
            pols = self.get_list_polissa_names(cursor, uid, from_indexed_auvidi)
            msg.append("Pòlisses que estan a indexada amb auvidi:")
            msg.append(" - Creada modcon per treure auvidi: {}".format(pols))

        if from_indexed_waiting_auvidi:
            pols = self.get_list_polissa_names(cursor, uid, from_indexed_waiting_auvidi)
            msg.append("Pòlisses que estan a indexada amb modcon pendent per activar auvidi:")
            msg.append(" - Modcon modificada, tret auvidi: {}".format(pols))

        if from_indexed_waiting_no_auvidi:
            pols = self.get_list_polissa_names(cursor, uid, from_indexed_waiting_no_auvidi)
            msg.append("Pòlisses que ja estan a indexada amb modcon pendent per treure auvidi:")
            msg.append(" - no fem res: {}".format(pols))

        if from_indexed_no_auvidi:
            pols = self.get_list_polissa_names(cursor, uid, from_indexed_no_auvidi)
            msg.append("Pòlisses que estan a indexada sense auvidi i sense modcon pendent:")
            msg.append(" - no fem res: {}".format(pols))

        if from_periods_auvidi:
            pols = self.get_list_polissa_names(cursor, uid, from_periods_auvidi)
            msg.append("Pòlisses que estan a periodes amb auvidi!!!:")
            msg.append(" - Creada modcon per treure auvidi: {}".format(pols))

        if from_periods_waiting_indexada_auvidi:
            pols = self.get_list_polissa_names(cursor, uid, from_periods_waiting_indexada_auvidi)
            msg.append("Pòlisses que estan a periodes amb modcon per passar a indexada + auvidi:")
            msg.append(" - Modcon modificada, tret auvidi: {}".format(pols))

        if from_periods_waiting_no_auvidi:
            pols = self.get_list_polissa_names(cursor, uid, from_periods_waiting_no_auvidi)
            msg.append("Pòlisses que estan a periodes amb modcon per passar a indexada SENSE auvidi:")  # noqa: E501
            msg.append(" - no fem res: {}".format(pols))

        if from_already_there:
            pols = self.get_list_polissa_names(cursor, uid, from_already_there)
            msg.append("Pòlisses que estan a periodes i no tenen modcon a indexada ni auvidi:")
            msg.append(" - No fem res: {}".format(pols))

        if faileds:
            pols = self.get_list_polissa_names(cursor, uid, faileds)
            msg.append("ERROR Pòlisses que han fallat al crear modcon:")
            msg.append(" - {}".format(pols))

        if not faileds:
            msg.append("Procés acabat correctament!")

        wiz_og.write({"state": "end", "info": "\n".join(msg)})

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
        if not value:
            mod_obj.write(cursor, uid, modcon_id, {'te_auvidi': value})
        pol_id = mod_obj.read(cursor, uid, modcon_id, ['polissa_id'])['polissa_id'][0]
        self.create_auvidi_pending_modcon(cursor, uid, pol_id, value)

    def get_list_polissa_names(self, cursor, uid, pol_ids):
        pol_obj = self.pool.get("giscedata.polissa")
        pol_data = pol_obj.read(cursor, uid, pol_ids, ["name"])
        return ', '.join([pol['name'] for pol in pol_data])

    def change_to_indexada(self, cursor, uid, pol_id):
        pol_obj = self.pool.get("giscedata.polissa")
        pol = pol_obj.browse(cursor, uid, pol_id)
        last_modcon_date = pol.modcontractuals_ids[0].data_final
        today = date.today().strftime("%Y-%m-%d")
        if last_modcon_date < today:
            return False

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

    def create_auvidi_pending_modcon(self, cursor, uid, pol_id, auvidi_value):
        pol_obj = self.pool.get("giscedata.polissa")
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        auvidi_flag = {
            'te_auvidi': auvidi_value,
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
