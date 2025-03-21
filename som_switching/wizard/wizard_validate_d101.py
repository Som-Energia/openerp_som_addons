# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

from gestionatr.defs import TABLA_64, TABLA_17, TARIFES_SEMPRE_MAX


class GiscedataSwitchingWizardValidateD101(osv.osv_memory):

    """Classe per gestionar el canvi de comercialitzador"""

    _name = "wizard.validate.d101"

    _change_reason = ""

    def _get_change_reason(self, cursor, uid, ids):
        sw_obj = self.pool.get("giscedata.switching")
        wizard_vals = self.read(cursor, uid, ids)[0]
        sw_id = wizard_vals["sw_id"]
        sw = sw_obj.browse(cursor, uid, sw_id)

        pas_id = sw.step_ids[0].pas_id
        d101_obj = self.pool.get("giscedata.switching.d1.01")
        id_pas = int(pas_id.split(",")[1])
        self._change_reason = d101_obj.read(cursor, uid, id_pas, ["motiu_canvi"])["motiu_canvi"]

    def isAutoconsum(self, cursor, uid):
        """
        Pending CNMC
        """
        return False

    def mod_con_wizard_default_values(self, cursor, uid, ids, context=None):
        """
        Method prepared to add default values
        """
        res = {"tipus_mod_cau": 'alta'}

        isAutoconsum = self.isAutoconsum(cursor, uid)

        if isAutoconsum and self._change_reason == "06":
            values = {
                "generate_new_contract": "exists",
                "change_adm": 1,
                "change_atr": 0,
                "owner_change_type": "R",
            }
            res.update(values)
        return res

    def validate_d101_autoconsum(self, cursor, uid, ids, context=None):
        """
        Creates a step D102 from a D1 case (sw_id).
        If it's not a rejections, a M1 case is created to change self-consumption
        for the related contract.
        Returns a tuple with 2 values:
            - If the D102 is a rejection step , returns (D102_ID, False)
            - If the D101 is accepted, returns (False, M1_ID)
        """
        if not context:
            context = {}

        if isinstance(ids, list) or isinstance(ids, tuple):
            ids = ids[0]

        self._get_change_reason(cursor, uid, ids)

        sw_obj = self.pool.get("giscedata.switching")

        wizard_vals = self.read(
            cursor, uid, ids, ["sw_id", "set_pending", "is_rejected", "rejection_comment"]
        )[0]

        sw_id = wizard_vals["sw_id"]

        is_rejected = wizard_vals["is_rejected"]
        rejection_comment = wizard_vals["rejection_comment"]
        set_pending = wizard_vals["set_pending"]

        # només pels de rebuig
        if is_rejected:
            d102_id = self._create_step_d1_02_autoconsum(
                cursor, uid, ids, sw_id, is_rejected, rejection_comment, set_pending, context
            )
            self.write(cursor, uid, [ids], {"generated_d102": d102_id})

        cups_id, cups_name = sw_obj.read(cursor, uid, sw_id, ["cups_id"])["cups_id"]
        # cups_id = sw_obj.read(cursor, uid, sw_id, ["cups_id"])["cups_id"][0]

        if not is_rejected:
            pol_obj = self.pool.get("giscedata.polissa")
            pol_id = pol_obj.search(cursor, uid, [('cups', '=', cups_id)])[0]
            # pol_id = sw_obj.read(cursor, uid, sw_id, ["polissa_ref_id"])["polissa_ref_id"][0]

            try:
                m1_id = self._create_case_m1_01_autoconsum(cursor, uid, ids, pol_id, context)
                self.write(cursor, uid, [ids], {"generated_m1": m1_id})

            except Exception as e:
                # set validacio_pendent to True
                sw_obj.write(cursor, uid, sw_id, {"validacio_pendent": True})

                raise osv.except_osv(
                    "Error",
                    _(
                        u"No s'ha pogut crear el cas M1 pel contracte amb id {}: {}".format(
                            pol_id, e.message
                        )
                    ),
                )
            sw = sw_obj.browse(cursor, uid, sw_id)
            sw.case_close()

            message = "M1-01 creat per al CUPS {}".format(cups_name)
            self.write(cursor, uid, [ids], {"state": "end", "results": message})

            return False, m1_id

        message = "Pas D1-02 de rebuig creat per al CUPS {}".format(cups_name)

        self.write(cursor, uid, [ids], {"state": "end", "results": message})

        return d102_id, False

    def _create_step_d1_02_autoconsum(
        self,
        cursor,
        uid,
        ids,
        sw_id,
        is_rejected,
        rejection_comment="",
        set_pending=True,
        context=None,
    ):
        """Creates a step D102 (rejected or accepted, depending on is_rejection parameter)
        from a D1 case (sw_id)"""
        if not context:
            context = {}
        wiz_step_obj = self.pool.get("wizard.create.step")
        sw_obj = self.pool.get("giscedata.switching")

        context.update({"active_ids": [sw_id]})

        params = {
            "step": "02",
            "option": "R" if is_rejected else "A",
            "step_is_rejectable": True,
            "check_repeated": True,
        }

        if is_rejected:
            self.pool.get("giscedata.switching.motiu.rebuig")
            imd_obj = self.pool.get("ir.model.data")
            motiu_rebuig_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_switching", "sw_motiu_rebuig_F1"
            )[1]
            params["motiu_rebuig"] = motiu_rebuig_id

        wiz_step_id = wiz_step_obj.create(cursor, uid, params, context=context)
        wiz_step = wiz_step_obj.browse(cursor, uid, wiz_step_id)
        wiz_step.action_create_steps(context=context)
        wiz_step = wiz_step.browse()[0]

        if len(eval(wiz_step.sw_ids)) == 0:
            raise osv.except_osv(_("Error"), wiz_step.info)

        d1 = sw_obj.browse(cursor, uid, sw_id)
        d102 = sw_obj.get_pas(cursor, uid, d1)

        if is_rejected:
            rebuig_obj = self.pool.get("giscedata.switching.rebuig")
            history_msg = (
                "D1-01 Rebutjat des de l'assistent de validació de D1-01:\n" + rejection_comment
            )
            rebuig_obj.write(
                cursor,
                uid,
                [d102.rebuig_ids[-1].id],
                {"desc_rebuig": d102.rebuig_ids[-1].desc_rebuig + ": {}".format(rejection_comment)},
            )

            d1.write({"state": "draft"})

            if set_pending:
                d1.write({"validacio_pendent": True})
                d102.write({"validacio_pendent": True})
        else:
            history_msg = "D1-01 Acceptat des de l'assistent de validació de D1-01"

        d1.historize_msg(history_msg)
        return d102.id

    def add_tension_to_additional_info(self, cursor, uid, cas_id, tension):
        sw_obj = self.pool.get("giscedata.switching")
        sw_vals = sw_obj.read(cursor, uid, cas_id, ["additional_info"])

        taula_cnmc = dict(TABLA_64)
        tension_name = taula_cnmc.get(tension, False)

        sw_obj.write(
            cursor,
            uid,
            cas_id,
            {
                "additional_info": "(N) Tensio: {tensio}; {old_info}".format(
                    tensio="M -> T" if tension_name.lower().startswith("3x") else "T -> M",
                    old_info=sw_vals["additional_info"][3:],
                )
            },
        )

    def specify_lack_of_tension(self, cursor, uid, cas_id):
        sw_obj = self.pool.get("giscedata.switching")
        step_info_obj = self.pool.get("giscedata.switching.step.info")
        m101_obj = self.pool.get("giscedata.switching.m1.01")

        sw_vals = sw_obj.read(cursor, uid, cas_id, ["step_ids"])
        step_info_vals = step_info_obj.read(cursor, uid, sw_vals["step_ids"][0])
        m101_id = int(step_info_vals["pas_id"].split(",")[1])

        m101_obj.write(cursor, uid, m101_id, {"solicitud_tensio": "N"})

    def _create_case_m1_01_autoconsum(self, cursor, uid, ids, pol_id, context=None):
        """Creates case M1 to change self-consumption for the given contract"""
        if not context:
            context = {}

        sw_obj = self.pool.get("giscedata.switching")
        wiz_obj = self.pool.get("giscedata.switching.mod.con.wizard")
        # self.pool.get("giscedata.polissa")

        wiz_id = wiz_obj.create(cursor, uid, {}, context={"cas": "M1", "pol_id": pol_id})
        # cups_name = pol_obj.read(cursor, uid, pol_id, ["cups"])["cups"][1]

        # deprecated
        # # validate autoconsum data
        # res_auto = wiz_obj.onchange_mod_autoconsum(
        #     cursor, uid, wiz_id, True, cups_name, context=None
        # )
        # hem de saber quin cau hem de fer
        # if res_auto["warning"]:
        #     raise osv.except_osv(_("Error"), res_auto["warning"])

        # validate tarpot changes
        self_vals = self.read(cursor, uid, ids)[0]
        if not self_vals['autoconsum_id']:
            raise osv.except_osv(
                "Error",
                _(u"No s'ha pogut crear el cas M1 per la pòlissa {}"
                  " al no haver-hi un autoconsum".format(pol_id))
            )
        wiz_obj_vals = wiz_obj.read(cursor, uid, wiz_id)[0]
        wiz_modcon_args = {
            "tariff": self_vals["tariff"]
            if self_vals.get("tariff", False)
            else wiz_obj_vals["tariff"],
            "power_p1": self_vals["power_p1"]
            if self_vals.get("power_p1", False)
            else wiz_obj_vals["power_p1"],
            "power_p2": self_vals["power_p2"]
            if self_vals.get("power_p2", False)
            else wiz_obj_vals["power_p2"],
            "power_p3": self_vals["power_p3"]
            if self_vals.get("power_p3", False)
            else wiz_obj_vals["power_p3"],
            "power_p4": self_vals["power_p4"]
            if self_vals.get("power_p4", False)
            else wiz_obj_vals["power_p4"],
            "power_p5": self_vals["power_p5"]
            if self_vals.get("power_p5", False)
            else wiz_obj_vals["power_p5"],
            "power_p6": self_vals["power_p6"]
            if self_vals.get("power_p6", False)
            else wiz_obj_vals["power_p6"],
        }
        useMaximeter = wiz_obj_vals["power_invoicing"] == "2" or (
            wiz_modcon_args["tariff"] in TARIFES_SEMPRE_MAX
        )
        wiz_modcon_args["power_invoicing"] = "2" if useMaximeter else "1"
        res_tarpot = wiz_obj.onchange_atr(
            cursor, uid, wiz_id, contract_id=pol_id, context={"pol_id": pol_id}, **wiz_modcon_args
        )
        if res_tarpot["warning"] and res_tarpot["warning"]["title"] != u"Potència incorrecte":
            raise osv.except_osv(_("Error"), res_tarpot["warning"])

        # include tension, if requested
        tension = self_vals.get("solicitud_tensio", False)
        if tension:
            wiz_modcon_args["solicitud_tensio"] = self_vals["solicitud_tensio"]

        # update wizard and create cases
        wiz_modcon_args.update(
            {
                "autoconsum_id": self_vals['autoconsum_id'],
                "retail_tariff": res_tarpot["value"].get("retail_tariff", False),
            }
        )

        wiz_default_values = self.mod_con_wizard_default_values(cursor, uid, ids)
        wiz_modcon_args.update(wiz_default_values)

        for field_name in ["con_name", "con_sur1", "con_sur2", "phone_num", "phone_pre"]:
            if field_name in self_vals and self_vals[field_name]:
                wiz_modcon_args[field_name] = self_vals[field_name]
        wiz_obj.write(cursor, uid, [wiz_id], wiz_modcon_args)

        wiz_obj.afegir_cau(cursor, uid, [wiz_id], context={"pol_id": pol_id})

        wiz_obj.genera_casos_atr(cursor, uid, [wiz_id], context={"pol_id": pol_id})

        casos_generats = wiz_obj.read(cursor, uid, wiz_id, ["casos_generats"])[0]["casos_generats"]
        cas_ids = eval(casos_generats)
        if not cas_ids:
            raise osv.except_osv(
                "Error", _(u"No s'ha pogut crear el cas M1 per la pòlissa {}".format(pol_id))
            )

        if tension:
            self.add_tension_to_additional_info(cursor, uid, cas_ids[0], tension)
        else:
            self.specify_lack_of_tension(cursor, uid, cas_ids[0])

        sw_obj.write(cursor, uid, cas_ids, {"state": "draft", "validacio_pendent": False})

        return cas_ids[0]

    def open_generated_cases(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        if isinstance(ids, list) or isinstance(ids, tuple):
            ids = ids[0]

        casos_ids = []

        d102_id = self.read(cursor, uid, ids, ["generated_d102"])["generated_d102"]
        if d102_id:
            d102_obj = self.pool.get("giscedata.switching.d1.02")
            d1_id = d102_obj.read(cursor, uid, d102_id, ["sw_id"])["sw_id"][0]
            casos_ids.append(d1_id)

        m1_id = self.read(cursor, uid, ids, ["generated_m1"])["generated_m1"]
        if m1_id:
            casos_ids.append(m1_id)

        return {
            "domain": "[('id','in', %s)]" % str(casos_ids),
            "name": _("Casos Creats"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "giscedata.switching",
            "type": "ir.actions.act_window",
        }

    _columns = {
        'autoconsum_id': fields.many2one('giscedata.autoconsum', 'Autoconsum', size=64),
        "is_rejected": fields.boolean(
            "Rebutjar", help="Si s'activa es generarà un D1-02 serà de rebuig"
        ),
        "rejection_comment": fields.text(
            "Motiu de rebuig", help="Comentari de rebuig del pas D1-02"
        ),
        "set_pending": fields.boolean(
            "D1-02 de rebuig pendent de validar",
            help="Si s'activa, es crearà el D1-02 marcat com a pendent de validar",
        ),
        "sw_id": fields.many2one(
            "giscedata.switching",
            "Pas D1 a validar",
            required=True,
            domain=[
                ("proces_id.name", "=", "D1"),
                ("step_id.name", "=", "01"),
                "|",
                ("additional_info", "ilike", "(04)%"),
                ("additional_info", "ilike", "(05)%"),
            ],
        ),
        "generated_d102": fields.integer(string="ID del pas D102 generat per l'assitent"),
        "generated_m1": fields.integer(string="ID del cas M1 generat per l'assitent"),
        "state": fields.selection(
            selection=[("init", "Init"), ("end", "End")], string="Estat", required=True
        ),
        "results": fields.text("Resultats", read_only=True),
        "solicitud_tensio": fields.selection([("", "")] + TABLA_64, u"Tensió Sol.licitada"),
        "power_p1": fields.integer("P1"),
        "power_p2": fields.integer("P2"),
        "power_p3": fields.integer("P3"),
        "power_p4": fields.integer("P4"),
        "power_p5": fields.integer("P5"),
        "power_p6": fields.integer("P6"),
        "tariff": fields.selection(sorted(TABLA_17, key=lambda t: t[1]), string="Tarifa ATR"),
        "con_name": fields.char("Nom", size=256),
        "con_sur1": fields.char("Cognom 1", size=256),
        "con_sur2": fields.char("Cognom 2", size=256),
        "phone_num": fields.char("Telèfon", size=9),
        "phone_pre": fields.char("Prefix", size=2),
    }

    _defaults = {
        "state": lambda *a: "init",
        "is_rejected": lambda *a: False,
        "set_pending": lambda *a: True,
    }


GiscedataSwitchingWizardValidateD101()
