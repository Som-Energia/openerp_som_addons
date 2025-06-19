# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import date


class GiscedataAtc(osv.osv):

    _name = "giscedata.atc"
    _inherit = "giscedata.atc"
    _order = "id desc"

    def get_autoreclama_data(self, cursor, uid, id, context=None):
        data = self.read(
            cursor,
            uid,
            id,
            ["business_days_with_same_agent", "subtipus_id", "agent_actual", "state"],
            context,
        )
        # agent_actual = '10' is ditri
        return {
            "distri_days": data["business_days_with_same_agent"]
            if data["agent_actual"] == "10"
            else 0,
            "subtipus_id": data["subtipus_id"][0],
            "agent_actual": data["agent_actual"],
            "state": data["state"],
        }

    # Automatic ATC + R1-029 from existing ATC / Entry point
    def create_ATC_R1_029_from_atc_via_wizard(self, cursor, uid, atc_id, context=None):
        channel_obj = self.pool.get("res.partner.canal")
        canal_id = channel_obj.search(
            cursor, uid, [("name", "ilike", "intercambi")], context=context
        )[0]

        subtr_obj = self.pool.get("giscedata.subtipus.reclamacio")
        subtr_id = subtr_obj.search(cursor, uid, [("name", "=", "029")], context=context)[0]

        imd_obj = self.pool.get("ir.model.data")
        initial_state_id = imd_obj.get_object_reference(
            cursor, uid, "som_autoreclama", "automated_state_workflow_atc"
        )[1]

        atc = self.browse(cursor, uid, atc_id, context)
        if atc.ref and atc.ref.split(",")[0] == u"giscedata.switching":
            original_sw_id = int(atc.ref.split(",")[1])

            sw_obj = self.pool.get("giscedata.switching")
            original_sw = sw_obj.browse(cursor, uid, original_sw_id, context)
            if original_sw.state != "open":
                raise Exception(
                    _(
                        u"S'ha intentat generar un cas ATC amb R1 029 a partir del cas ATR {} amb R1 {} no oberta!"  # noqa: E501
                    ).format(atc_id, original_sw_id)
                )
        else:
            raise Exception(
                _(
                    u"S'ha intentat generar un cas ATC amb R1 029 a partir del cas ATR {} sense R1 associada!"  # noqa: E501
                ).format(atc_id)
            )

        new_case_data = {
            "polissa_id": atc.polissa_id.id,
            "descripcio": u"Reclamació per retràs automàtica",
            "canal_id": canal_id,
            "section_id": atc.section_id.id,
            "subtipus_reclamacio_id": subtr_id,
            "comentaris": u"",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": True,
            "crear_cas_r1": True,
            "autoreclama_history_initial_state_id": initial_state_id,
            "orginal_sw_id": original_sw_id,
        }
        return self.create_general_atc_r1_case_via_wizard(cursor, uid, new_case_data, context)

    # Automatic ATC + R1-006 from existing polissa / Entry point

    def create_ATC_R1_006_from_polissa_via_wizard(self, cursor, uid, polissa_id, context=None):
        subtr_obj = self.pool.get("giscedata.subtipus.reclamacio")
        subtr_id = subtr_obj.search(cursor, uid, [("name", "=", "006")], context=context)[0]

        # Do not create a 006 if there is an active one yet
        params = [
            ("polissa_id", "=", polissa_id),
            ("state", "in", ["open", "pending"]),
            ("subtipus_id", "=", subtr_id),
        ]
        atc_ids = self.search(cursor, uid, params, context=context)
        if atc_ids:
            raise Exception(
                _(
                    u"Error en la creació del CAC amb R1 006, ja n'hi ha un en estat obert o pendent amb id {}!!!"  # noqa: E501
                ).format(",".join([str(atc_id) for atc_id in atc_ids]))
            )

        channel_obj = self.pool.get("res.partner.canal")
        canal_id = channel_obj.search(
            cursor, uid, [("name", "ilike", "intercambi")], context=context
        )[0]

        imd_obj = self.pool.get("ir.model.data")
        initial_state_id = imd_obj.get_object_reference(
            cursor, uid, "som_autoreclama", "correct_state_workflow_atc"
        )[1]

        section_id = imd_obj.get_object_reference(
            cursor, uid, "som_switching", "atc_section_factura"
        )[1]

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"AUTOCAC 006",
            "canal_id": canal_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtr_id,
            "comentaris": u"",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": True,
            "crear_cas_r1": True,
            "autoreclama_history_initial_state_id": initial_state_id,
        }

        tag_obj = self.pool.get("giscedata.atc.tag")
        tag_ids = tag_obj.search(
            cursor, uid, [('name', '=', 'AUTOCAC 006')], context=context
        )
        if tag_ids:
            new_case_data['atc_tag_id'] = tag_ids[0]

        return self.create_general_atc_r1_case_via_wizard(cursor, uid, new_case_data, context)

    # Automatic ATC + R1-010 from existing F1 / Entry point
    def has_previous_R1_010(self, cursor, uid, cups_name, factura_number):
        subtipus_id = self.pool.get('ir.model.data').get_object_reference(
            cursor, uid, 'giscedata_subtipus_reclamacio', 'subtipus_reclamacio_010')[1]

        rec_obj = self.pool.get("giscedata.switching.reclamacio")
        rec_ids = rec_obj.search(cursor, uid, [("num_factura", "=", factura_number)])
        if not rec_ids:
            return False

        sw_obj = self.pool.get("giscedata.switching")
        sw_ids = sw_obj.search(cursor, uid, [
            ("cups_input", "=", cups_name),
            ("state", "=", "open"),
            ("proces_id.name", "=", "R1"),
        ])
        if not sw_ids:
            return False

        sw_r101_obj = self.pool.get("giscedata.switching.r1.01")
        sw_r101_ids = sw_r101_obj.search(cursor, uid, [
            ("subtipus_id", "in", [subtipus_id]),
            ("reclamacio_ids", "in", rec_ids),
            ("sw_id", "in", sw_ids),
        ])
        return len(sw_r101_ids) > 0

    def create_ATC_R1_010_from_f1_via_wizard(self, cursor, uid, f1_id, context=None):
        subtr_obj = self.pool.get("giscedata.subtipus.reclamacio")
        subtr_id = subtr_obj.search(cursor, uid, [("name", "=", "010")], context=context)[0]

        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        f1 = f1_obj.browse(cursor, uid, f1_id, context=context)

        if self.has_previous_R1_010(cursor, uid, f1.cups_id.name, f1.invoice_number_text):
            raise Exception(
                _(
                    u"Error en la creació del CAC amb R1 010, ja existeix un R1 obert vinculat a la mateixa factura f1 {}!!!"  # noqa: E501
                ).format(f1_id)
            )
        # TODO: verify there is no other cac

        channel_obj = self.pool.get("res.partner.canal")
        canal_id = channel_obj.search(
            cursor, uid, [("name", "ilike", "intercambi")], context=context
        )[0]

        imd_obj = self.pool.get("ir.model.data")
        initial_state_id = imd_obj.get_object_reference(
            cursor, uid, "som_autoreclama", "correct_state_workflow_atc"
        )[1]

        section_id = imd_obj.get_object_reference(
            cursor, uid, "som_switching", "atc_section_factura"
        )[1]

        if f1.type_factura != 'C':
            raise Exception(
                _(
                    u"Error en la creació del CAC amb R1 010, F1 no es tipus C id_f1 {}!!!"  # noqa: E501
                ).format(f1_id)
            )

        if len(f1.liniafactura_id) == 0:
            raise Exception(
                _(
                    u"Error en la creació del CAC amb R1 010, F1 sense linies id_f1 {}!!!"  # noqa: E501
                ).format(f1_id)
            )

        if f1.liniafactura_id[0].tipo_factura == '06':
            tag_name = "[GET] Expedient ANOMALIA"
        elif f1.liniafactura_id[0].tipo_factura == '11':
            tag_name = "[GET] Expedient FRAU"
        else:
            raise Exception(
                _(
                    u"Error en la creació del CAC amb R1 010, F1 no es tipus anomalia o frau id_f1 {}!!!"  # noqa: E501
                ).format(f1_id)
            )

        tag_obj = self.pool.get("giscedata.atc.tag")
        tag_ids = tag_obj.search(
            cursor, uid, [('name', '=', tag_name)], context=context
        )

        new_case_data = {
            "polissa_id": f1.id,
            "atc_tag_id": tag_ids[0],
            "canal_id": canal_id,
            "descripcio": u"R per defecte expedient",
            "section_id": section_id,
            "subtipus_reclamacio_id": subtr_id,
            "comentaris": u"",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": False,
            "crear_cas_r1": True,
            "autoreclama_history_initial_state_id": initial_state_id,
            "from_model": "giscedata.facturacio.importacio.linia",
            "polissa_field": "cups_id.polissa_id",
        }
        atc_id = self.create_general_atc_r1_case_via_wizard(cursor, uid, new_case_data, context)

        atc_obj = self.pool.get("giscedata.atc")
        ref = atc_obj.read(cursor, uid, atc_id, ['ref'], context=context)['ref'].split(',')

        sw_obj = self.pool.get(ref[0])
        sw = sw_obj.browse(cursor, uid, int(ref[1]), context=context)
        ref2 = sw.step_ids[0].pas_id.split(',')

        r101_obj = self.pool.get(ref2[0])
        r101 = r101_obj.browse(cursor, uid, int(ref2[1]), context=context)

        rec_obj = self.pool.get("giscedata.switching.reclamacio")
        rec_obj.write(cursor, uid, r101.reclamacio_ids[0].id, {
                      'num_factura': f1.invoice_number_text}, context=context)
        return atc_id

    # Automatic ATC + [R1] from dictonary / Entry poiut

    def create_general_atc_r1_case_via_wizard(self, cursor, uid, case_data, context=None):
        if not context:
            ctx = {}
        else:
            ctx = context.copy()
        ctx["from_model"] = case_data.get(
            "from_model", "giscedata.polissa")  # model gas o electricitat
        ctx["polissa_field"] = case_data.get("polissa_field", "id")  # camp per llegir
        ctx["active_ids"] = [case_data["polissa_id"]]  # id del model origen
        ctx["active_id"] = case_data["polissa_id"]  # id del model origen
        if case_data.get("autoreclama_history_initial_state_id", False):
            ctx["autoreclama_history_initial_state_id"] = case_data[
                "autoreclama_history_initial_state_id"
            ]
        if case_data.get("autoreclama_history_initial_date", False):
            ctx["autoreclama_history_initial_date"] = case_data["autoreclama_history_initial_date"]

        params = {
            "canal_id": case_data["canal_id"],
            "subtipus_id": case_data["subtipus_reclamacio_id"],
            "comments": case_data["comentaris"],
            "multi": False,
            "name": case_data["descripcio"],
            "section_id": case_data["section_id"],
            "open_case": True,
            "no_responsible": case_data.get("sense_responsable", False),
            "tancar_cac_al_finalitzar_r1": case_data.get("tanca_al_finalitzar_r1", False),
            "tag": case_data.get("atc_tag_id", False),
        }

        atcw_obj = self.pool.get("wizard.create.atc.from.polissa")
        wiz_id = atcw_obj.create(cursor, uid, params, ctx)
        atcw_obj.create_atc_case_from_view(cursor, uid, [wiz_id], ctx)  # creates the ATC case

        gen_cases = atcw_obj.read(cursor, uid, wiz_id, ["generated_cases"], ctx)[0]
        atc_id = gen_cases["generated_cases"][0]  # gets the new ATC case id

        if case_data["section_id"]:
            self.write(cursor, uid, atc_id, {"section_id": case_data["section_id"]})

        if case_data.get("crear_cas_r1", False):
            open_r1_wiz = atcw_obj.open_r1_wizard(cursor, uid, [wiz_id], ctx)

            r1atcw_ctx = open_r1_wiz["context"]

            if "from_model" in case_data:
                r1atcw_ctx["from_model"] = case_data["from_model"]
            if "polissa_field" in case_data:
                r1atcw_ctx["polissa_field"] = case_data["polissa_field"]

            r1atcw_obj = self.pool.get(open_r1_wiz["res_model"])  # wizard.generate.r1.from.atc.case
            r1atcw_id = r1atcw_obj.create(cursor, uid, {}, r1atcw_ctx)
            generate_r1_wiz = r1atcw_obj.generate_r1(
                cursor, uid, [r1atcw_id], r1atcw_ctx
            )  # Generates the R1 for the ATC case
            if type(generate_r1_wiz["context"]) == dict:
                r1w_ctx = generate_r1_wiz["context"]
            else:
                r1w_ctx = eval(generate_r1_wiz["context"])

            if generate_r1_wiz["res_model"] == 'wizard.create.r1':
                r1w_obj = self.pool.get(generate_r1_wiz["res_model"])  # "wizard.create.r1"
                r1w_id = r1w_obj.create(cursor, uid, {}, r1w_ctx)
                subtype_r1_wiz = r1w_obj.action_subtype_fields_view(
                    cursor, uid, [r1w_id], r1w_ctx
                )  # obtain subtype wizard R1

                sr1w_obj = self.pool.get(subtype_r1_wiz["res_model"])  # "wizard.subtype.r1"
                if "orginal_sw_id" in case_data:
                    r1w_ctx["from_sw_id"] = case_data["orginal_sw_id"]
                sr1w_id = sr1w_obj.create(cursor, uid, {}, r1w_ctx)
                sr1w_obj.action_create_r1_case(
                    cursor, uid, [sr1w_id], r1w_ctx
                )  # create subtype R1 for example:029  # USE OLD CONTEXT!
            elif generate_r1_wiz["res_model"] == 'wizard.r101.from.contract':
                r1w_obj = self.pool.get(generate_r1_wiz["res_model"])  # "wizard.r101.from.contract"
                r1w_id = r1w_obj.create(cursor, uid, {}, r1w_ctx)
                r1w_obj.action_create_atr_case(
                    cursor, uid, [r1w_id], r1w_ctx
                )
            elif generate_r1_wiz["res_model"] == 'wizard.r1.from.f1.erroni':
                r1w_obj = self.pool.get(generate_r1_wiz["res_model"])  # "wizard.r1.from.f1.erroni"
                r1w_id = r1w_obj.create(cursor, uid, {}, r1w_ctx)
                generate_r1_wiz = r1w_obj.create_cases_from_invoice_contracts(
                    cursor, uid, [r1w_id], r1w_ctx
                )

                r1w_obj = self.pool.get(generate_r1_wiz["res_model"])  # "wizard.create.r1"
                r1w_id = r1w_obj.create(cursor, uid, {}, generate_r1_wiz['context'])
                subtype_r1_wiz = r1w_obj.action_subtype_fields_view(
                    cursor, uid, [r1w_id], r1w_ctx
                )  # obtain subtype wizard R1

                sr1w_obj = self.pool.get(subtype_r1_wiz["res_model"])  # "wizard.subtype.r1"
                sr1w_id = sr1w_obj.create(cursor, uid, {}, eval(subtype_r1_wiz["context"]))
                sr1w_obj.action_create_r1_case(
                    cursor, uid, [sr1w_id], r1w_ctx
                )  # create subtype R1 for example:029  # USE OLD CONTEXT!

            else:
                raise Exception(_("Error en la creació del R1, aquest cas no està suportat"))

        return atc_id

    # Create and setup autoreclama history to the new created ATC object
    def create(self, cursor, uid, vals, context=None):
        atc_id = super(GiscedataAtc, self).create(cursor, uid, vals, context=context)

        if not context:
            context = {}

        imd_obj = self.pool.get("ir.model.data")
        initial_state_id = imd_obj.get_object_reference(
            cursor, uid, "som_autoreclama", "correct_state_workflow_atc"
        )[1]

        initial_state_id = context.get("autoreclama_history_initial_state_id", initial_state_id)
        initial_date = context.get(
            "autoreclama_history_initial_date", date.today().strftime("%Y-%m-%d")
        )

        atch_obj = self.pool.get("som.autoreclama.state.history.atc")
        atch_obj.create(
            cursor,
            uid,
            {
                "atc_id": atc_id,
                "state_id": initial_state_id,
                "change_date": initial_date,
            },
        )
        return atc_id

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
        history_obj = self.pool.get("som.autoreclama.state.history.atc")
        result = dict.fromkeys(ids, False)
        fields_to_read = ["state_id", "change_date", "atc_id"]
        for id in ids:
            res = history_obj.search(cursor, uid, [("atc_id", "=", id)])
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
        values = self.read(cursor, uid, ids, ["atc_id"])
        return [value["atc_id"][0] for value in values]

    _STORE_STATE = {"som.autoreclama.state.history.atc": (change_state, ["change_date"], 10)}

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
            "som.autoreclama.state.history.atc",
            "atc_id",
            _(u"Historic d'autoreclama"),
            readonly=True,
        ),
    }


GiscedataAtc()
