# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class GiscedataPolissaInfoenergia(osv.osv):
    """
    Pòlissa per afegir els camps relacionats amb infoenergia
    """

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    MINIM_DIES_CONSUM = 122

    def write(self, cursor, uid, ids, vals, context=None):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        if "emp_allow_recieve_mail_infoenergia" in vals:
            profile_obj = self.pool.get("empowering.customize.profile")
            profile_id = None
            if vals["emp_allow_recieve_mail_infoenergia"]:
                profile_id = profile_obj.search(
                    cursor, uid, [("name", "=", "Default profile")]
                )[0]
            vals["empowering_profile_id"] = profile_id

        if "emp_allow_send_data" in vals:
            if not vals["emp_allow_send_data"]:
                vals["emp_allow_recieve_mail_infoenergia"] = False

        res = super(GiscedataPolissaInfoenergia, self).write(
            cursor, uid, ids, vals, context
        )
        return res

    def get_consum_anual_consum_lectures(self, cursor, uid, polissa_id, context=None):
        """Calculem el consum anual a partir del consum de les lectures"""

        if isinstance(polissa_id, (tuple, list)):
            polissa_id = polissa_id[0]

        lectures_obj = self.pool.get("giscedata.lectures.lectura")
        limit_date = (datetime.today() - timedelta(self.MINIM_DIES_CONSUM)).strftime(
            "%Y-%m-%d"
        )

        from_date = (datetime.today() - relativedelta(months=14)).strftime("%Y-%m-%d")
        data_ultima_lectura = self.read(cursor, uid, polissa_id, ["data_ultima_lectura"])[
            "data_ultima_lectura"
        ]
        search_params = [
            ("comptador.polissa", "=", polissa_id),
            ("name", ">", from_date),
            ("name", "<=", data_ultima_lectura),
            ("tipus", "=", "A"),
            ("consum", "<", 989999),
        ]
        lect_ids = lectures_obj.search(
            cursor, uid, search_params, context={"active_test": False}
        )

        lect_info = lectures_obj.read(cursor, uid, lect_ids, ["consum", "name"])
        lect_info.sort(key=lambda x: x["name"])
        if (
            not lect_ids
            or lect_info[0]["name"] > limit_date
            or lect_info[-1]["name"] < limit_date
        ):
            return False

        consum = sum([x["consum"] for x in lect_info])
        n_dies = datetime.strptime(lect_info[-1]["name"], "%Y-%m-%d") - datetime.strptime(
            lect_info[0]["name"], "%Y-%m-%d"
        )
        n_dies = n_dies.days
        if n_dies < self.MINIM_DIES_CONSUM:
            return False

        consum_anual = consum * 365 / n_dies
        if consum_anual < 0 or consum_anual > 10000000:
            return False

        return consum_anual

    def get_consum_anual_factures(self, cursor, uid, polissa_id, context=None):
        """Calculem el consum anual a partir del consum de les lectures"""

        if isinstance(polissa_id, (tuple, list)):
            polissa_id = polissa_id[0]

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        from_date = (datetime.today() - relativedelta(months=14)).strftime("%Y-%m-%d")

        search_params = [
            ("polissa_id", "=", polissa_id),
            ("state", "!=", "draft"),
            ("data_inici", ">=", from_date),
            ("type", "in", ["out_invoice", "out_refund"]),
        ]
        fact_ids = fact_obj.search(cursor, uid, search_params)
        if not fact_ids:
            return False

        fact_infos = fact_obj.read(
            cursor, uid, fact_ids, ["energia_kwh", "type", "data_inici", "data_final"]
        )
        fact_infos.sort(key=lambda x: x["data_inici"])
        n_dies = datetime.strptime(
            fact_infos[-1]["data_final"], "%Y-%m-%d"
        ) - datetime.strptime(fact_infos[0]["data_inici"], "%Y-%m-%d")
        n_dies = n_dies.days
        if n_dies < self.MINIM_DIES_CONSUM:
            return False

        consum_anual = 0
        for fact_info in fact_infos:
            if fact_info["type"] == "out_invoice":
                consum_anual += fact_info["energia_kwh"]
            else:
                consum_anual -= fact_info["energia_kwh"]

        if consum_anual < 0 or consum_anual > 10000000:
            return False

        return consum_anual * 365 / n_dies

    _columns = {
        "emp_allow_send_data": fields.boolean(
            "Permetre compartir dades amb BeeData",
            help="Compartir dades a través de l'API amb BeeData",
        ),
        "emp_allow_recieve_mail_infoenergia": fields.boolean(
            "Permetre rebre informes",
            help="Indica si es vol rebre informes per email del servei" "d'infoenergia",
        ),
    }
    _defaults = {
        "emp_allow_send_data": lambda *a: True,
        "emp_allow_recieve_mail_infoenergia": lambda *a: True,
    }


GiscedataPolissaInfoenergia()
