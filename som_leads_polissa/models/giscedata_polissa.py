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

        if res[2]:
            sw_id = res[2]
            sw = sw_o.browse(cursor, uid, sw_id, context=context)
            pas_model = sw.get_pas_model_name()
            if pas_model == 'giscedata.switching.c2.01':
                pas = sw.get_pas()
                c201_obj = self.pool.get(pas_model)
                c201_obj.write(cursor, uid, pas.id, {'contratacion_incondicional_bs': 'S'})

        return res


GiscedataPolissa()
