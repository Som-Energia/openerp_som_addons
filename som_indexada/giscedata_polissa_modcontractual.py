# -*- coding: utf-8 -*-
from osv import osv


class GiscedataPolissaModcontractual(osv.osv):

    _name = "giscedata.polissa.modcontractual"
    _inherit = "giscedata.polissa.modcontractual"

    def send_indexada_modcon_activated_email(self, cursor, uid, polissa_id):
        ir_model_data = self.pool.get("ir.model.data")
        account_obj = self.pool.get("poweremail.core_accounts")
        power_email_tmpl_obj = self.pool.get("poweremail.templates")

        template_id = ir_model_data.get_object_reference(
            cursor, uid, "som_indexada", "email_activacio_tarifa_indexada"
        )[1]
        template = power_email_tmpl_obj.read(cursor, uid, template_id)

        email_from = False
        email_account_id = "info@somenergia.coop"
        if template.get("enforce_from_account", False):
            email_from = template.get("enforce_from_account")[0]
        if not email_from:
            email_from = account_obj.search(cursor, uid, [("email_id", "=", email_account_id)])[0]

        try:
            wiz_send_obj = self.pool.get("poweremail.send.wizard")
            ctx = {
                "active_ids": [polissa_id],
                "active_id": polissa_id,
                "template_id": template_id,
                "src_model": "giscedata.polissa",
                "src_rec_ids": [polissa_id],
                "from": email_from,
                "state": "single",
                "priority": "0",
            }

            params = {"state": "single", "priority": "0", "from": ctx["from"]}
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)
            return wiz_send_obj.send_mail(cursor, uid, [wiz_id], ctx)

        except Exception as e:
            raise e

    def _do_previous_actions_on_activation(self, cursor, uid, mc_id, context=None):
        res = super(GiscedataPolissaModcontractual, self)._do_previous_actions_on_activation(
            cursor, uid, mc_id, context
        )
        modcon_obj = self.pool.get("giscedata.polissa.modcontractual")
        modcon = modcon_obj.browse(cursor, uid, mc_id, context={"prefetch": False})

        if (
            res == "OK"
            and modcon.state == "pendent"
            and (modcon.mode_facturacio != modcon.modcontractual_ant.mode_facturacio)
        ):
            self.send_indexada_modcon_activated_email(cursor, uid, modcon.polissa_id.id)

        coeficient_k_ant = modcon.coeficient_k
        coeficient_k_new = modcon.modcontractual_ant.coeficient_k
        if (
            modcon.modcontractual_ant.mode_facturacio == "index"
            and modcon.mode_facturacio == "index"
            and coeficient_k_ant != coeficient_k_new
        ):
            if not self._apply_modcon_date_last_f1_plus_1(cursor, uid, mc_id, context):
                return "error"

        return res


GiscedataPolissaModcontractual()
