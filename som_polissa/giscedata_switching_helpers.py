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


GiscedataSwitchingHelpers()
