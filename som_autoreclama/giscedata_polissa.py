# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import datetime, date


class GiscedataPolissa(osv.osv):

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def get_autoreclama_data(self, cursor, uid, id, context=None):
        data = self.read(
            cursor,
            uid,
            id,
            ["data_ultima_lectura_f1", "data_alta"],
            context,
        )

        if data['data_ultima_lectura_f1']:
            last_date = data['data_ultima_lectura_f1']
        else:
            last_date = data['data_alta']

        last_date_dt = datetime.strptime(last_date, "%Y-%m-%d")
        days_since_last_f1 = (datetime.today() - last_date_dt).days

        history_obj = self.pool.get("som.autoreclama.state.history.polissa")
        h_ids = history_obj.search(cursor, uid, [("polissa_id", "=", id)])

        days_since_current_cacr1006 = 0
        if h_ids:
            cacr1006_closed = None
            values = history_obj.read(
                cursor, uid,
                h_ids[0],
                ["generated_atc_id", "change_date"],
                context=context
            )
            if values['generated_atc_id']:
                atc_obj = self.pool.get("giscedata.atc")
                atc_data = atc_obj.read(
                    cursor, uid,
                    values['generated_atc_id'][0],
                    ["state", "date_closed"],
                    context=context
                )
                if atc_data["state"] == 'done' and atc_data["date_closed"]:
                    cacr1006_closed = atc_data["date_closed"][:10]

            elif values['change_date']:  # no cac, change_state created manually
                cacr1006_closed = values['change_date']

            if cacr1006_closed:
                cacr1006_closed_dt = datetime.strptime(cacr1006_closed, "%Y-%m-%d")
                days_since_current_cacr1006 = (datetime.today() - cacr1006_closed_dt).days

        return {
            'days_without_F1': days_since_last_f1,
            'days_since_current_CACR1006_closed': days_since_current_cacr1006,
        }

    # Create and setup autoreclama history to the new created polissa object

    def create(self, cursor, uid, vals, context=None):
        polissa_id = super(GiscedataPolissa, self).create(cursor, uid, vals, context=context)

        if not context:
            context = {}

        imd_obj = self.pool.get("ir.model.data")
        initial_state_id = imd_obj.get_object_reference(
            cursor, uid, "som_autoreclama", "correct_state_workflow_polissa"
        )[1]

        initial_state_id = context.get("autoreclama_history_initial_state_id", initial_state_id)
        initial_date = context.get(
            "autoreclama_history_initial_date", date.today().strftime("%Y-%m-%d")
        )

        polh_obj = self.pool.get("som.autoreclama.state.history.polissa")
        polh_obj.create(
            cursor,
            uid,
            {
                "polissa_id": polissa_id,
                "state_id": initial_state_id,
                "change_date": initial_date,
            },
        )
        return polissa_id

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
