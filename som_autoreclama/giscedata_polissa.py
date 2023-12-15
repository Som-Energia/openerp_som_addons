# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class GiscedataPolissa(osv.osv):

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"


    def get_autoreclama_data(self, cursor, uid, id, context=None):
        data = self.read(
            cursor,
            uid,
            id,
            ["data_ultima_lectura_f1"],
            context,
        )
        return {'days_without_F1': 1234}


    # Autoreclama history management functions
    def get_current_autoreclama_state_info(self, cursor, uid, ids, context=None):
        """
            Get the info of the last history line by atc id.
        :return: a dict containing the info of the last history line of the
                 atc indexed by its id.
                 ==== Fields of the dict for each atc ===
                 'id': if of the last som.autoreclama.state.history.atc
                 'state_id': id of its state
                 'change_date': date of change (also, date of the creation of
                                the line)
        """
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        history_obj = self.pool.get("som.autoreclama.state.history.polissa")
        result = dict.fromkeys(ids, False)
        fields_to_read = ["state_id", "change_date", "polissa_id"]
        for id in ids:
            res = history_obj.search(cursor, uid, [("polissa_id", "=", id)])
            if res:
                # We consider the last record the first one due to order
                # statement in the model definition.
                values = history_obj.read(cursor, uid, res[0], fields_to_read)
                result[id] = {
                    "id": values["id"],
                    "state_id": values["state_id"][0],
                    "change_date": values["change_date"],
                }
            else:
                result[id] = False
        return result


    # Autoreclama history management functions
    def _get_last_autoreclama_state_from_history(
        self, cursor, uid, ids, field_name, arg, context=None
    ):
        result = {k: {} for k in ids}
        last_lines = self.get_current_autoreclama_state_info(cursor, uid, ids)
        for id in ids:
            if last_lines[id]:
                result[id]["autoreclama_state"] = last_lines[id]["state_id"]
                result[id]["autoreclama_state_date"] = last_lines[id]["change_date"]
            else:
                result[id]["autoreclama_state"] = False
                result[id]["autoreclama_state_date"] = False
        return result


    # Autoreclama history management functions
    def change_state(self, cursor, uid, ids, context):
        values = self.read(cursor, uid, ids, ["polissa_id"])
        return [value["polissa_id"][0] for value in values]


    _STORE_STATE = {"som.autoreclama.state.history.polissa": (change_state, ["change_date"], 10)}

    _columns = {
        "autoreclama_state": fields.function(
            _get_last_autoreclama_state_from_history,
            method=True,
            type="many2one",
            obj="som.autoreclama.state",
            string=_(u"Estat autoreclama"),
            required=False,
            readonly=True,
            store=_STORE_STATE,
            multi="autoreclama",
        ),
        "autoreclama_state_date": fields.function(
            _get_last_autoreclama_state_from_history,
            method=True,
            type="date",
            string=_(u"última data d'autoreclama"),
            required=False,
            readonly=True,
            store=_STORE_STATE,
            multi="autoreclama",
        ),
        "autoreclama_history_ids": fields.one2many(
            "som.autoreclama.state.history.polissa",
            "polissa_id",
            _(u"Historic d'autoreclama"),
            readonly=True,
        ),
    }


GiscedataPolissa()
