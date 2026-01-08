# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import datetime, date, timedelta


class GiscedataPolissa(osv.osv):

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def som_autoreclama_add_to_info_gestio_endarrerida(self, cursor, uid, pol_id, params, context=None):  # noqa: E501
        data = self.read(cursor, uid, pol_id, ['info_gestio_endarrerida'])
        if 'info_gestio_endarrerida' in data and data['info_gestio_endarrerida']:
            text = "\n" + data['info_gestio_endarrerida']
        else:
            text = ""

        head = params.get("message", "")
        timestamp = datetime.today().strftime("%Y-%m-%d_%H:%M:%S")
        line = u"{} {}".format(timestamp, head)

        self.write(cursor, uid, pol_id, {'info_gestio_endarrerida': line + text})

    def get_autoreclama_data(self, cursor, uid, id, namespace, context=None):
        vals = self._get_autoreclama_data_common(cursor, uid, id, context=context)
        if namespace == "polissa":
            vals.update(self._get_autoreclama_data_006(cursor, uid, id, context=context))
        if namespace == "polissa009":
            vals.update(self._get_autoreclama_data_009(cursor, uid, id, context=context))
        return vals

    def _get_autoreclama_data_common(self, cursor, uid, id, context=None):
        data = self.read(
            cursor,
            uid,
            id,
            ["data_ultima_lectura_f1", "data_baixa", "state"],
            context,
        )

        baixa = data['state'] == 'baixa'
        if data["data_ultima_lectura_f1"] and data["data_baixa"]:
            facturada = data["data_baixa"] <= data["data_ultima_lectura_f1"]
        else:
            facturada = False

        if data["data_baixa"]:
            baixa_dt = datetime.strptime(data["data_baixa"], "%Y-%m-%d")
            days_baixa = (datetime.today() - baixa_dt).days
        else:
            days_baixa = 0

        return {
            'days_since_baixa': days_baixa,
            'baixa_facturada': baixa and facturada,
        }

    def _get_autoreclama_data_006(self, cursor, uid, id, context=None):
        atc_obj = self.pool.get("giscedata.atc")
        data_obj = self.pool.get("ir.model.data")

        data = self.read(
            cursor,
            uid,
            id,
            ["data_ultima_lectura_f1", "data_alta", "state"],
            context,
        )

        if data['data_ultima_lectura_f1']:
            last_date = data['data_ultima_lectura_f1']
        else:
            last_date = data['data_alta']

        if last_date and data['state'] in ['activa', 'baixa']:
            last_date_dt = datetime.strptime(last_date, "%Y-%m-%d")
            days_since_last_f1 = (datetime.today() - last_date_dt).days
        else:
            days_since_last_f1 = 0

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

        atc_006_ids = []
        if 'days_ago_R1006' in context:
            days_ago = context.get('days_ago_R1006', 0)
            str_date_limit = (date.today() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            id_r1_006 = data_obj.get_object_reference(
                cursor, uid, "giscedata_subtipus_reclamacio", "subtipus_reclamacio_006"
            )[1]
            review_state_id = data_obj.get_object_reference(
                cursor, uid, "som_autoreclama", "review_state_workflow_polissa"
            )[1]
            h_ids = history_obj.search(cursor, uid, [
                ("polissa_id", "=", id),
                ("state_id", "=", review_state_id),
            ])
            if h_ids:
                last_date_review = history_obj.read(
                    cursor, uid, h_ids[0], ['change_date']
                )['change_date']
                if last_date_review and last_date_review > str_date_limit:
                    str_date_limit = last_date_review

            atc_006_ids = atc_obj.search(
                cursor, uid,
                [
                    ('polissa_id', '=', id),
                    ('subtipus_id', '=', id_r1_006),
                    ('date', '>', str_date_limit),
                ],
                context={'active_test': False}
            )

        return {
            'days_without_F1': days_since_last_f1,
            'days_since_current_CACR1006_closed': days_since_current_cacr1006,
            'CACR1006s_in_last_conf_days': len(atc_006_ids),
        }

    def _get_autoreclama_data_009(self, cursor, uid, id, context=None):
        atc_obj = self.pool.get("giscedata.atc")
        data_obj = self.pool.get("ir.model.data")
        l_obj = self.pool.get("giscedata.lectures.lectura.pool")
        per_obj = self.pool.get("giscedata.polissa.tarifa.periodes")
        origins_obj = self.pool.get("giscedata.lectures.origen")

        real_origins_ids = origins_obj.search(cursor, uid, [
            ('codi', 'in', ['10', '20', '30', '60', 'LC']),
        ], context=context)
        meter_ids = self.read(cursor, uid, id, ["comptadors"], context)['comptadors']
        last_real_reading_ids = l_obj.search(cursor, uid, [
            ('comptador_id', 'in', meter_ids),
            ('origen_id', 'in', real_origins_ids),
        ], order='name DESC', limit=1, context=context)

        p1_ids = per_obj.search(cursor, uid, [
            ('name', '=', 'P1'),
        ])
        params = [
            ('comptador_id', 'in', meter_ids),
            ('periode', 'in', p1_ids),
        ]
        if last_real_reading_ids:
            last_real_reading_date = l_obj.read(cursor, uid, last_real_reading_ids[0], [
                                                'name'], context=context)['name']
            params.append(('name', '<', last_real_reading_date))

        reading_ids = l_obj.search(cursor, uid, params, context=context)
        invoicing_cyles_with_estimate_readings = len(reading_ids)

        history_obj = self.pool.get("som.autoreclama.state.history.polissa009")
        h_ids = history_obj.search(cursor, uid, [("polissa_id", "=", id)])

        days_since_current_cacr1009 = 0
        if h_ids:
            cacr1009_closed = None
            values = history_obj.read(
                cursor, uid,
                h_ids[0],
                ["generated_atc_id", "change_date"],
                context=context
            )
            if values['generated_atc_id']:
                atc_data = atc_obj.read(
                    cursor, uid,
                    values['generated_atc_id'][0],
                    ["state", "date_closed"],
                    context=context
                )
                if atc_data["state"] == 'done' and atc_data["date_closed"]:
                    cacr1009_closed = atc_data["date_closed"][:10]

            elif values['change_date']:  # no cac, change_state created manually
                cacr1009_closed = values['change_date']

            if cacr1009_closed:
                cacr1009_closed_dt = datetime.strptime(cacr1009_closed, "%Y-%m-%d")
                days_since_current_cacr1009 = (datetime.today() - cacr1009_closed_dt).days

        atc_009_ids = []
        if 'days_ago_R1009' in context:
            days_ago = context.get('days_ago_R1009', 0)
            str_date_limit = (date.today() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            id_r1_009 = data_obj.get_object_reference(
                cursor, uid, "giscedata_subtipus_reclamacio", "subtipus_reclamacio_009"
            )[1]
            review_state_id = data_obj.get_object_reference(
                cursor, uid, "som_autoreclama", "review_state_workflow_polissa009"
            )[1]
            h_ids = history_obj.search(cursor, uid, [
                ("polissa_id", "=", id),
                ("state_id", "=", review_state_id),
            ])
            if h_ids:
                last_date_review = history_obj.read(
                    cursor, uid, h_ids[0], ['change_date']
                )['change_date']
                if last_date_review and last_date_review > str_date_limit:
                    str_date_limit = last_date_review

            atc_009_ids = atc_obj.search(
                cursor, uid,
                [
                    ('polissa_id', '=', id),
                    ('subtipus_id', '=', id_r1_009),
                    ('date', '>', str_date_limit),
                ],
                context={'active_test': False}
            )

        return {
            'invoicing_cyles_with_estimate_readings': invoicing_cyles_with_estimate_readings,
            'days_since_current_CACR1009_closed': days_since_current_cacr1009,
            'CACR1009s_in_last_conf_days': len(atc_009_ids),
        }

    # Create and setup autoreclama history to the new created polissa object

    def create(self, cursor, uid, vals, context=None):
        polissa_id = super(GiscedataPolissa, self).create(cursor, uid, vals, context=context)
        self._create_autoreclama_history_006(cursor, uid, polissa_id, context=context)
        self._create_autoreclama_history_009(cursor, uid, polissa_id, context=context)
        return polissa_id

    def _create_autoreclama_history_006(self, cursor, uid, polissa_id, context=None):
        if not context:
            context = {}

        initial_state_id = None
        if "autoreclama_history_initial_state_id" in context:
            initial_state_id = context["autoreclama_history_initial_state_id"]
        else:

            imd_obj = self.pool.get("ir.model.data")
            initial_state_id = imd_obj.get_object_reference(
                cursor, uid, "som_autoreclama", "correct_state_workflow_polissa"
            )[1]

        self._create_autoreclama_history_gen(cursor, uid,
                                             polissa_id,
                                             initial_state_id,
                                             "som.autoreclama.state.history.polissa",
                                             context=context)

    def _create_autoreclama_history_009(self, cursor, uid, polissa_id, context=None):
        if not context:
            context = {}

        initial_state_id = None
        if "autoreclama_009_history_initial_state_id" in context:
            initial_state_id = context["autoreclama_009_history_initial_state_id"]
        else:
            imd_obj = self.pool.get("ir.model.data")
            initial_state_id = imd_obj.get_object_reference(
                cursor, uid, "som_autoreclama", "correct_state_workflow_polissa009"
            )[1]

        self._create_autoreclama_history_gen(cursor, uid,
                                             polissa_id,
                                             initial_state_id,
                                             "som.autoreclama.state.history.polissa009",
                                             context=context)

    def _create_autoreclama_history_gen(self, cursor, uid, polissa_id, initial_state_id, model, context=None):  # noqa: E501
        if not context:
            context = {}

        initial_date = context.get(
            "autoreclama_history_initial_date", date.today().strftime("%Y-%m-%d")
        )

        polh_obj = self.pool.get(model)
        polh_obj.create(
            cursor,
            uid,
            {
                "polissa_id": polissa_id,
                "state_id": initial_state_id,
                "change_date": initial_date,
            },
        )

    # Autoreclama history management functions

    def get_current_autoreclama_state_info(self, cursor, uid, ids, model, context=None):
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
        history_obj = self.pool.get(model)
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
    def _get_last_autoreclama006_state_from_history(
        self, cursor, uid, ids, field_name, arg, context=None
    ):
        return self._get_last_autoreclama_state_from_history(
            cursor, uid, ids, field_name, arg,
            "som.autoreclama.state.history.polissa",
            {
                'state': 'autoreclama_state',
                'date': 'autoreclama_state_date',
            },
            context)

    def _get_last_autoreclama009_state_from_history(
        self, cursor, uid, ids, field_name, arg, context=None
    ):
        return self._get_last_autoreclama_state_from_history(
            cursor, uid, ids, field_name, arg,
            "som.autoreclama.state.history.polissa009",
            {
                'state': 'autoreclama009_state',
                'date': 'autoreclama009_state_date',
            },
            context)

    def _get_last_autoreclama_state_from_history(
        self, cursor, uid, ids, field_name, arg, model, fields_dict, context=None
    ):
        result = {k: {} for k in ids}
        last_lines = self.get_current_autoreclama_state_info(cursor, uid, ids, model, context)
        for id in ids:
            if last_lines[id]:
                result[id][fields_dict["state"]] = last_lines[id]["state_id"]
                result[id][fields_dict["date"]] = last_lines[id]["change_date"]
            else:
                result[id][fields_dict["state"]] = False
                result[id][fields_dict["date"]] = False
        return result

    # Autoreclama history management functions

    def change_state(self, cursor, uid, ids, context):
        values = self.read(cursor, uid, ids, ["polissa_id"])
        return [value["polissa_id"][0] for value in values]

    _STORE_STATE_006 = {
        "som.autoreclama.state.history.polissa": (change_state, ["change_date"], 10)
    }
    _STORE_STATE_009 = {
        "som.autoreclama.state.history.polissa009": (change_state, ["change_date"], 10)
    }

    _columns = {
        "autoreclama_state": fields.function(
            _get_last_autoreclama006_state_from_history,
            method=True,
            type="many2one",
            obj="som.autoreclama.state",
            string=_(u"Estat autoreclama 006"),
            required=False,
            readonly=True,
            store=_STORE_STATE_006,
            multi="autoreclama",
        ),
        "autoreclama_state_date": fields.function(
            _get_last_autoreclama006_state_from_history,
            method=True,
            type="date",
            string=_(u"última data d'autoreclama 006"),
            required=False,
            readonly=True,
            store=_STORE_STATE_006,
            multi="autoreclama",
        ),
        "autoreclama_history_ids": fields.one2many(
            "som.autoreclama.state.history.polissa",
            "polissa_id",
            _(u"Historic d'autoreclama 006"),
            readonly=True,
        ),
        "autoreclama009_state": fields.function(
            _get_last_autoreclama009_state_from_history,
            method=True,
            type="many2one",
            obj="som.autoreclama.state",
            string=_(u"Estat autoreclama 009"),
            required=False,
            readonly=True,
            store=_STORE_STATE_009,
            multi="autoreclama",
        ),
        "autoreclama009_state_date": fields.function(
            _get_last_autoreclama009_state_from_history,
            method=True,
            type="date",
            string=_(u"última data d'autoreclama 009"),
            required=False,
            readonly=True,
            store=_STORE_STATE_009,
            multi="autoreclama",
        ),
        "autoreclama009_history_ids": fields.one2many(
            "som.autoreclama.state.history.polissa009",
            "polissa_id",
            _(u"Historic d'autoreclama 009"),
            readonly=True,
        ),
    }


GiscedataPolissa()
