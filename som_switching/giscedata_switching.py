# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime
from tools.translate import _
import pooler

from giscedata_switching_comer.giscedata_switching import POTENCIES_TRIFASIQUES


class GiscedataSwitchingAparell(osv.osv):

    _name = "giscedata.switching.aparell"
    _inherit = "giscedata.switching.aparell"

    def calcula_lloguer_comptador(
        self, cursor, uid, ids, tarifaatr=None, potencia=None, context=None
    ):
        """En funció del tipus d'aparell, calcula el lloguer del comptador"""
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        irdata_obj = self.pool.get("ir.model.data")
        uom_obj = self.pool.get("product.uom")
        pm_obj = self.pool.get("giscedata.switching.pm")
        product_obj = self.pool.get("product.product")
        pricelist_obj = self.pool.get("product.pricelist")
        tarifa_obj = self.pool.get("giscedata.polissa.tarifa")

        # Tarifes electricitat
        tar_elec_data = irdata_obj._get_id(
            cursor, uid, "giscedata_facturacio", "pricelist_tarifas_electricidad"
        )

        tar_elec_id = irdata_obj.read(cursor, uid, tar_elec_data, ["res_id"])["res_id"]

        # TODO: es podria tenir en compte any de traspas
        # Unitats de mesura ALQ/mes i ALQ/dia
        data_names = ["uom_aql_elec_dia", "uom_aql_elec_mes"]
        uom_alq_datas = irdata_obj.search(
            cursor, uid, [("model", "=", "product.uom"), ("name", "in", data_names)]
        )

        uom_alq_ids = [p["res_id"] for p in irdata_obj.read(cursor, uid, uom_alq_datas, ["res_id"])]

        uom_alq_vals = uom_obj.read(cursor, uid, uom_alq_ids, ["name"])

        uoms = dict([(u["name"], u["id"]) for u in uom_alq_vals])

        # Productes de lloguer
        data_names = [
            "alq_cont_st_ea_mono_resto",
            "alq_cont_st_ea_tri",
            "alq_cont_dh_mono",
            "alq_cont_dh_tri_doble",
            "alq_conta_tele",
            "alq_conta_tele_tri",
            # 30 and AT fixed price (ALQ30)
            "alq_cont_30_default",
        ]

        alq_datas = irdata_obj.search(
            cursor, uid, [("model", "=", "product.product"), ("name", "in", data_names)]
        )

        alq_ids = [p["res_id"] for p in irdata_obj.read(cursor, uid, alq_datas, ["res_id"])]

        alq_vals = product_obj.read(cursor, uid, alq_ids, ["list_price", "code", "uom_id"])

        preus = dict(
            [
                (a["code"], {"preu": a["list_price"], "uom": uoms["ALQ/mes"], "id": a["id"]})
                for a in alq_vals
            ]
        )

        # Dades de l'aparell
        aparell_vals = self.read(cursor, uid, ids, ["tipus_em", "propietat", "pm_id"])

        pm_vals = pm_obj.read(cursor, uid, aparell_vals["pm_id"][0], ["mode_lectura", "tensio_pm"])

        # DH segons Tarifa
        es_dh = False
        es_30 = False
        if tarifaatr:
            # 3.0 fare, fixed price
            if tarifaatr == "003":
                es_30 = True

            tar_id = tarifa_obj.get_tarifa_from_ocsum(cursor, uid, tarifaatr)

            if tar_id:
                es_dh = tarifa_obj.get_num_periodes(cursor, uid, [tar_id]) > 1
            tar_vals = tarifa_obj.read(cursor, uid, tar_id, ["tipus"])
            if tar_vals["tipus"] == "AT":
                es_30 = True

        # Telegestió?
        es_tg = pm_vals["mode_lectura"] == "4"

        # Trifàsic segons potència
        es_trifasic = potencia and potencia in POTENCIES_TRIFASIQUES or False
        es_trifasic = es_trifasic or pm_vals["tensio_pm"] == 400

        # Escullim el producte de lloguer
        if es_30:
            alq = "ALQ30"
        elif es_tg:
            # Telegestió
            alq = es_trifasic and "ALQ20" or "ALQ19"
        elif es_dh:
            # DH
            alq = es_trifasic and "ALQ07" or "ALQ06"
        else:
            # Resta
            alq = es_trifasic and "ALQ03" or "ALQ02"

        # Calculem el preu per dia
        ctx = {"date": datetime.today().strftime("%Y-%m-%d")}
        preu_mes = pricelist_obj.price_get(
            cursor, uid, [tar_elec_id], preus[alq]["id"], 1.0, context=ctx
        )[tar_elec_id]

        preu = uom_obj._compute_price(cursor, uid, uoms["ALQ/mes"], preu_mes, uoms["ALQ/dia"])

        txt = (
            (
                " ".join(
                    [
                        pm_vals["mode_lectura"],
                        str(tarifaatr),
                        str(potencia),
                        str(pm_vals["tensio_pm"]),
                    ]
                )
            )
            + "->"
            + alq
        )

        vals = {
            "preu_lloguer": round(preu, 6),
            "lloguer": True,
            "uom_id": uoms["ALQ/dia"],
            "txt": txt,
        }

        return vals


GiscedataSwitchingAparell()


class GiscedataSwitching(osv.osv):
    """Classe per gestionar el canvi de comercialitzador"""

    _name = "giscedata.switching"
    _inherit = "giscedata.switching"

    def activa_cas_atr(self, cursor, uid, sw, context=None):
        if context is None:
            context = {}
        act_obj = self.pool.get("giscedata.switching.activation.config")
        helperdist_obj = self.pool.get("giscedata.switching.helpers.distri")
        helpercomer_obj = self.pool.get("giscedata.switching.helpers")
        if sw.whereiam == "distri":
            helper_obj = helperdist_obj
            whereiam = _(u"Distribuidora")
        else:
            helper_obj = helpercomer_obj
            whereiam = _(u"Comercializadora")

        method_names = act_obj.get_activation_method(cursor, uid, sw.get_pas(), context=context)
        if not method_names:
            return [
                _(u"Atenció"),
                _(
                    u"Activació cas %s-%s no implementada/activada a %s.\n\n"
                    u"Pots consultar les activacions disponibles a:\n"
                    u"* Gestió ATR -> Configuració -> Activacions de Casos ATR"
                )
                % (sw.proces_id.name, sw.step_id.name, whereiam),
            ]
        else:
            all_res = []
            all_res_description = []
            for method_name in method_names:
                method_caller = getattr(helper_obj, method_name, False)
                if not method_caller and helper_obj != helpercomer_obj:
                    # Els metodes comuns estan al de comer, busquem allà
                    method_caller = getattr(helpercomer_obj, method_name, False)
                if not method_caller:
                    raise osv.except_osv(
                        _("Error"),
                        _(
                            "No s'ha pogut activar el cas {0} perqué no es troba el "
                            "métode d'activació {1}."
                        ).format(sw.name, method_name),
                    )
                init_str = _(u"Resultat Activacio:\n")
                db = pooler.get_db(cursor.dbname)
                tmp_cursor = db.cursor()
                msg_h = ""
                try:
                    res = method_caller(tmp_cursor, uid, sw.id, context=context)
                    if len(res) == 2:
                        msg = res[0] + ": " + res[1]
                        all_res.append(res[0].upper())
                        all_res_description.append(res[1])
                    elif len(res) == 1:
                        msg = res[0]
                        all_res.append("INFO.")
                        all_res_description.append(res[0])
                    elif not res:
                        continue
                    else:
                        raise Exception(
                            "ERROR", _(u"La activacio no ha retornat la informacio esperada")
                        )
                    msg_h = init_str + msg
                    tmp_cursor.commit()
                except Exception as e:
                    msg_h = init_str + str(e)
                    tmp_cursor.rollback()
                    return ("ERROR", str(e))
                finally:
                    tmp_cursor.close()
                    db = pooler.get_db(cursor.dbname)
                    tmp_cursor = db.cursor()
                    self.update_deadline(tmp_cursor, uid, sw.id)
                    self.historize_msg(tmp_cursor, uid, sw.id, msg_h, context=context)
                    tmp_cursor.commit()
                    tmp_cursor.close()
            if "ERROR" in all_res:
                final_res = ["ERROR"]
            elif "OK" in all_res:
                final_res = ["OK"]
            else:
                final_res = [all_res[0]]

            n_msg = ""
            try:
                init_str = _(u"Resultat Notificacio:\n")
                notificate_on_activate = int(
                    self.pool.get("res.config").get(cursor, 1, "sw_notificate_on_activate", "0")
                )
                if notificate_on_activate and final_res[0] != "ERROR":
                    pas = sw.get_pas()
                    if pas.notificacio_pendent:
                        ctx = context.copy()
                        ctx["check_cas_tancat_on_activate"] = True
                        ares = sw.notifica_a_client(context=ctx)
                        n_msg = init_str + ares[1]
                        self.historize_msg(cursor, uid, sw.id, n_msg, context=context)
            except Exception as e:
                n_msg = init_str + str(e)
                self.historize_msg(cursor, uid, sw.id, n_msg, context=context)

            final_res.append("\n\n".join(all_res_description + [n_msg]))
            return final_res

    def _get_last_history_line(self, cr, uid, ids, name, arg, context=None):
        """Nom de la situació de la instal·lació"""
        res = dict([(i, "") for i in ids])

        for sw_obs in self.read(cr, uid, ids, ["user_observations"], context=context):
            if sw_obs["user_observations"]:
                usr_obs = sw_obs["user_observations"].split("\n")

                if len(usr_obs) > 1:
                    usr_obs = [o for o in usr_obs if o]
                last_line = usr_obs[0] if usr_obs else ""

                res[sw_obs["id"]] = last_line[:100]

        return res

    def _ff_get_data_accio(self, cursor, uid, ids, field_name, args, context=None):
        """Find the value of field data_accio in step '01'.
        Only search for process which are in ['a3', 'b1', 'm1', 'c1', 'c2']
        :param cursor: Database cursor
        :param uid: User id
        :param ids: cas atr id list
        :param context: Application context
        :returns data_accio
        """
        result = dict.fromkeys(ids, None)
        for sw_obs in self.read(cursor, uid, ids, ["proces_id"], context=context):
            if sw_obs["proces_id"][1].lower() in ["a3", "b1", "m1", "c1", "c2"]:
                pas_obj = self.pool.get(
                    "giscedata.switching.{}.01".format(sw_obs["proces_id"][1].lower())
                )
                pas_id = pas_obj.search(cursor, uid, [("sw_id", "=", sw_obs["id"])])
                if pas_id:
                    result[sw_obs["id"]] = pas_obj.read(cursor, uid, pas_id[0], ["data_accio"])[
                        "data_accio"
                    ]

        return result

    def _get_pas_id(self, cr, uid, ids, context=None):
        res = []
        for sw_obs in self.read(cr, uid, ids, ["sw_id"]):
            res.append(sw_obs["sw_id"][0])

        return res

    def escull_tarifa_comer(self, cursor, uid, ids, tarifa_atr, context=None):
        if context is None:
            context = {}
        context["tarifa_atr"] = tarifa_atr
        return super(GiscedataSwitching, self).escull_tarifa_comer(
            cursor, uid, ids, tarifa_atr, context=context
        )

    def unlink(self, cursor, uid, ids, context=None):
        return self.case_and_cacs_cancel(cursor, uid, ids, context)

    def case_and_cacs_cancel(self, cursor, uid, ids, *args):
        cac_obj = self.pool.get("giscedata.atc")
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        self.case_cancel(cursor, uid, ids, *args)

        cacs_to_cancel = []
        for switching in self.browse(cursor, uid, ids):
            ref = switching.ref or switching.ref2
            if ref and 'giscedata.atc,' in ref:
                cacs_to_cancel.append(int(ref.split(',')[1]))

        if cacs_to_cancel:
            cac_obj.case_cancel(cursor, uid, cacs_to_cancel, *args)
        return True

    def case_cancel(self, cursor, uid, ids, *args):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for switching in self.browse(cursor, uid, ids):
            step = switching.step_id and switching.step_id.name
            if not switching.enviament_pendent or step not in [None, '01']:
                raise osv.except_osv(
                    _(u"Warning"),
                    _(
                        "No es poden cancel·lar casos ATR en marxa, "
                        "revisa els protocols o demana ajuda."
                    ).format(switching.id),
                )
        return super(GiscedataSwitching, self).case_cancel(cursor, uid, ids, *args)

    _columns = {
        "user_observations": fields.text("Observaciones del usuario"),
        "last_observation_line": fields.function(
            _get_last_history_line,
            method=True,
            type="char",
            size=100,
            string="Última línia de les observacions",
            store={
                "giscedata.switching": (
                    lambda self, cr, uid, ids, c=None: ids,
                    ["user_observations"],
                    20,
                ),
            },
        ),
        "data_accio": fields.function(
            _ff_get_data_accio,
            method=True,
            type="date",
            string="Data acció del pas 01",
            store={
                "giscedata.switching.a3.01": (_get_pas_id, ["data_accio"], 20),
                "giscedata.switching.b1.01": (_get_pas_id, ["data_accio"], 20),
                "giscedata.switching.c1.01": (_get_pas_id, ["data_accio"], 20),
                "giscedata.switching.c2.01": (_get_pas_id, ["data_accio"], 20),
                "giscedata.switching.m1.01": (_get_pas_id, ["data_accio"], 20),
            },
        ),
        "collectiu": fields.related(
            "cups_polissa_id",
            "is_autoconsum_collectiu",
            type="boolean",
            string="Col·lectiu",
            readonly=True,
        ),
    }

    _defaults = {"user_observations": lambda *a: ""}


GiscedataSwitching()


class GiscedataFacturacioImportacioLinia(osv.osv):
    """Agrupació d'importacions"""

    _name = "giscedata.facturacio.importacio.linia"
    _inherit = "giscedata.facturacio.importacio.linia"

    def _get_last_history_line(self, cr, uid, ids, name, arg, context=None):
        """Nom de la situació de la instal·lació"""
        res = dict([(i, "") for i in ids])

        for f1 in self.read(cr, uid, ids, ["user_observations"], context=context):
            if f1["user_observations"]:
                usr_obs = f1["user_observations"].split("\n")

                if len(usr_obs) > 1:
                    usr_obs = [o for o in usr_obs if o]
                last_line = usr_obs[0] if usr_obs else ""

                res[f1["id"]] = last_line[:100]

        return res

    _columns = {
        "user_observations": fields.text("Observacions de l'usuari"),
        "last_observation_line": fields.function(
            _get_last_history_line,
            method=True,
            type="char",
            size=100,
            string="Última línia de les observacions",
            store={
                "giscedata.facturacio.importacio.linia": (
                    lambda self, cr, uid, ids, c=None: ids,
                    ["user_observations"],
                    20,
                ),
            },
        ),
    }


GiscedataFacturacioImportacioLinia()
