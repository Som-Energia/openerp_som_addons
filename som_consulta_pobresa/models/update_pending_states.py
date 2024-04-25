# -*- coding: utf-8 -*-
from osv import osv


class UpdatePendingStates(osv.osv_memory):
    _name = "update.pending.states"
    _inherit = "update.pending.states"

    def consulta_pobresa_pendent(self, cursor, uid, polissa):
        return polissa.consulta_pobresa_pendent

    def update_pending_ask_poverty_invoices(self, cursor, uid, factura_id, context=None):
        super(UpdatePendingStates, self).update_pending_ask_poverty_invoices(
            cursor, uid, factura_id, context=context)
        scp_obj = self.pool.get("som.consulta.pobresa")
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")
        pobresa_certificada = self.get_object_id(
            cursor, uid, "som_account_invoice_pending",
            "probresa_energetica_certificada_pending_state"
        )
        warning_cut_off_state = self.get_object_id(
            cursor, uid, "giscedata_facturacio_comer_bono_social", "avis_tall_pending_state"
        )
        invoice = fact_obj.read(cursor, uid, factura_id)
        polissa_id = invoice["polissa_id"][0]
        polissa_state = pol_obj.read(cursor, uid, [polissa_id], ["state"])[0]["state"]
        if polissa_state != "baixa":
            scp_activa = scp_obj.consulta_pobresa_activa(
                cursor, uid, [], partner_id=invoice['partner_id'], polissa_id=polissa_id)

            if scp_activa and scp_activa.resolucio:
                fact_obj.set_pending(cursor, uid, [factura_id], pobresa_certificada)
                return True

            if self.poverty_eligible(cursor, uid, polissa_id) and not scp_activa:
                wiz_obj = self.pool.get("wizard.crear.consulta.pobresa")
                context = {"active_ids": [factura_id], "active_id": factura_id}
                wiz_id = wiz_obj.create(cursor, uid, {}, context=context)
                wiz_obj.crear_consulta_pobresa(cursor, uid, wiz_id, context=context)

            fact_obj.set_pending(cursor, uid, [factura_id], warning_cut_off_state)


UpdatePendingStates()
