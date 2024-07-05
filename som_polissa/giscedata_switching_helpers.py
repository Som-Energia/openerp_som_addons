# -*- coding: utf-8 -*-
# Funcions compartides per diferents processos de switching
from osv import osv


class GiscedataSwitchingHelpers(osv.osv):

    _name = "giscedata.switching.helpers"
    _inherit = "giscedata.switching.helpers"
    _auto = False

    def move_bateria_virtual_from_old_to_new_post_hook(
        self, cursor, uid, old_pol_id, new_pol_id, context=None
    ):
        if context is None:
            context = {}

        polissa_obj = self.pool.get("giscedata.polissa")
        bat_obj = self.pool.get("giscedata.bateria.virtual")

        super(GiscedataSwitchingHelpers, self).move_bateria_virtual_from_old_to_new_post_hook(
            cursor, uid, old_pol_id, new_pol_id, context=context
        )

        if polissa_obj.te_bateria_virtual(cursor, uid, old_pol_id, context=context):
            ctx = context.copy()
            ctx["prefech"] = False
            old_polissa = polissa_obj.browse(cursor, uid, old_pol_id, context=ctx)
            new_pol_vals = polissa_obj.read(
                cursor, uid, new_pol_id, ["data_alta", "name"], context=context
            )
            for old_pol_bat in old_polissa.bateria_ids:
                # Canviem el nom de la bateria (BV -> FS)
                write_vals = {"name": "FS{}".format(new_pol_vals["name"])}
                bat_obj.write(cursor, uid, [old_pol_bat.bateria_id.id], write_vals)

        return True

    def activar_polissa_from_m1_canvi_titular_subrogacio(self, cursor, uid, sw_id, old_polissa=None, context=None):  # noqa: E501
        res = super(
            GiscedataSwitchingHelpers, self
        ).activar_polissa_from_m1_canvi_titular_subrogacio(
            cursor, uid, sw_id, old_polissa=old_polissa, context=context)

        imd_obj = self.pool.get("ir.model.data")
        sw_obj = self.pool.get("giscedata.switching")
        sw = sw_obj.browse(cursor, uid, sw_id, context=context)
        if sw.cups_polissa_id._is_enterprise():
            default_process = imd_obj.get_object_reference(
                cursor, uid, "account_invoice_pending", "default_pending_state_process"
            )[1]
            sw.cups_polissa_id.write({"process_id": default_process})
        else:
            bo_social_process = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_comer_bono_social',
                'bono_social_pending_state_process'
            )[1]
            sw.cups_polissa_id.write({"process_id": bo_social_process})

        return res


GiscedataSwitchingHelpers()
