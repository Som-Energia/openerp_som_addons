from osv import osv


class GiscedataPolissa(osv.osv):
    _inherit = "giscedata.polissa"

    def crear_cas_atr(self, cursor, uid, polissa_id, proces=None, config_vals=None, context=None):
        if context is None:
            context = {}

        sw_o = self.pool.get("giscedata.switching")

        res = super(GiscedataPolissa, self).crear_cas_atr(
            cursor, uid, polissa_id, proces, config_vals, context
        )

        if res[2] and context.get("create_draft_atr"):
            sw_o.write(cursor, uid, res[2], {'state': 'draft'})

        return res


GiscedataPolissa()
