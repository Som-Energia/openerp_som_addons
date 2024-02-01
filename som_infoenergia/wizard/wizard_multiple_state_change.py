# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from som_infoenergia.som_infoenergia_enviament import ESTAT_ENVIAT

STATES = [("init", "Estat Inicial"), ("finished", "Estat Final")]
ENV_STATES = [("esborrany", "Esborrany"), ("obert", "Obert"), ("cancellat", "Cancel·lat")]


class WizardMultipleStateChange(osv.osv_memory):
    _name = "wizard.infoenergia.multiple.state.change"

    def multiple_state_change(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context=context)
        env_obj = self.pool.get("som.infoenergia.enviament")

        env_ids = context.get("active_ids", [])
        states_dict = dict(ESTAT_ENVIAT)
        message = wiz.message or " "
        for _id in env_ids:
            old_state = env_obj.read(cursor, uid, _id, ["estat"])["estat"]
            env_obj.write(cursor, uid, _id, {"estat": wiz.new_state})
            env_obj.add_info_line(
                cursor,
                uid,
                _id,
                message
                + " (Estat: {} -> {})".format(states_dict[old_state], states_dict[wiz.new_state]),
            )
        wiz.write({"state": "finished"})
        return True

    _columns = {
        "state": fields.selection(STATES, _(u"Estat del wizard de baixada de CSV")),
        "new_state": fields.selection(ENV_STATES, ("Nou estat dels enviaments")),
        "message": fields.text(_("Comentari"), size=256),
    }

    _defaults = {
        "state": "init",
        "message": " ",
    }


WizardMultipleStateChange()
