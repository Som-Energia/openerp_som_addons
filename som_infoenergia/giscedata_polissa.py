# -*- coding: utf-8 -*-
from osv import osv, fields
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tools.translate import _
from tools import email_send


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
                profile_id = profile_obj.search(cursor, uid, [("name", "=", "Default profile")])[0]
            vals["empowering_profile_id"] = profile_id

        if "emp_allow_send_data" in vals:
            if not vals["emp_allow_send_data"]:
                vals["emp_allow_recieve_mail_infoenergia"] = False

        res = super(GiscedataPolissaInfoenergia, self).write(cursor, uid, ids, vals, context)
        return res

    def get_consum_anual_consum_lectures(self, cursor, uid, polissa_id, context=None):
        """Calculem el consum anual a partir del consum de les lectures"""

        if isinstance(polissa_id, (tuple, list)):
            polissa_id = polissa_id[0]

        lectures_obj = self.pool.get("giscedata.lectures.lectura")
        limit_date = (datetime.today() - timedelta(self.MINIM_DIES_CONSUM)).strftime("%Y-%m-%d")

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
        lect_ids = lectures_obj.search(cursor, uid, search_params, context={"active_test": False})

        lect_info = lectures_obj.read(cursor, uid, lect_ids, ["consum", "name"])
        lect_info.sort(key=lambda x: x["name"])
        if not lect_ids or lect_info[0]["name"] > limit_date or lect_info[-1]["name"] < limit_date:
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
        search_params = [
            ("polissa_id", "=", polissa_id),
            ("state", "!=", "draft"),
            ("type", "in", ["out_invoice", "out_refund"]),
        ]
        f_id = fact_obj.search(cursor, uid, search_params, limit=1, order="id desc")
        if not f_id:
            return False

        data_final = fact_obj.read(cursor, uid, f_id[0], ["data_final"])["data_final"]
        today = datetime.strptime(data_final, "%Y-%m-%d")
        from_date = (today - relativedelta(months=12, days=15)).strftime("%Y-%m-%d")

        search_params = [
            ("polissa_id", "=", polissa_id),
            ("state", "!=", "draft"),
            ("data_inici", ">=", from_date),
            ("type", "in", ["out_invoice", "out_refund"]),
        ]
        fact_ids = fact_obj.search(cursor, uid, search_params)
        if not fact_ids:
            return False

        fact_infos = fact_obj.read(cursor, uid, fact_ids, ["energia_kwh", "type"])
        consum_anual = 0
        for fact_info in fact_infos:
            if fact_info["type"] == "out_invoice":
                consum_anual += fact_info["energia_kwh"]
            else:
                consum_anual -= fact_info["energia_kwh"]

        if consum_anual < 0 or consum_anual > 10000000:
            return False

        return consum_anual

    def get_consum_anual_pdf(self, cursor, uid, polissa_id, context=None):
        """Calculem el consum anual a partir del consum de la factura en pdf"""

        if isinstance(polissa_id, (tuple, list)):
            polissa_id = polissa_id[0]

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        rprt_obj = self.pool.get("giscedata.facturacio.factura.report")

        ids = fact_obj.search(
            cursor,
            uid,
            [
                ("polissa_id", "=", polissa_id),
                ("state", "!=", "draft"),
                ("type", "in", ["out_refund", "out_invoice"]),
            ],
            limit=1,
            order="id DESC",
        )

        if not ids:
            return False

        conany = False
        try:
            data = rprt_obj.get_components_data(cursor, uid, [ids[0]])
            conany = data[data.keys()[0]].energy_consumption_graphic_td.total_any
        except Exception:
            pass

        return conany

    def _conany_updater(self, cursor, uid, context=None):
        cups_obj = self.pool.get("giscedata.cups.ps")
        msg = []
        msg.append(str(datetime.today()))
        msg.append("Cercant polisses a updatar")
        domain = [("state", "=", "activa"), ("tarifa_codi", "like", "2%")]
        contracts2_ids = self.search(cursor, uid, domain)
        msg.append("Trobades {} polisses 2.X".format(len(contracts2_ids)))
        domain = [("state", "=", "activa"), ("tarifa_codi", "like", "3%")]
        contracts3_ids = self.search(cursor, uid, domain)
        msg.append("Trobades {} polisses 3.X".format(len(contracts3_ids)))
        domain = [("state", "=", "activa"), ("tarifa_codi", "like", "6%")]
        contracts6_ids = self.search(cursor, uid, domain)
        msg.append("Trobades {} polisses 6.X".format(len(contracts6_ids)))

        contracts_ids = contracts3_ids + contracts6_ids
        msg.append("Trobades {} polisses candidates".format(len(contracts_ids)))

        failed = []
        company_contracts_cups_id = []
        for contract in self.read(cursor, uid, contracts_ids, ["id", "cups"]):
            try:
                company_contracts_cups_id.append(contract["cups"][0])
            except Exception as e:
                failed.append(("contract read", contract["id"], str(e)))
        cups_search = [
            ("id", "in", company_contracts_cups_id),
            "|",
            ("conany_origen", "!=", "manual"),
            ("conany_origen", "=", False),
        ]
        toupdate_cups_id = cups_obj.search(cursor, uid, cups_search)

        domestic_contracts_cups_id = []
        for contract in self.read(cursor, uid, contracts2_ids, ["id", "cups"]):
            try:
                domestic_contracts_cups_id.append(contract["cups"][0])
            except Exception as e:
                failed.append(("contract read", contract["id"], str(e)))

        thirtyfive_days_ago = (datetime.now() - timedelta(days=35)).strftime("%Y-%m-%d")
        cups_search = [
            ("id", "in", domestic_contracts_cups_id),
            "|",
            ("conany_data", "=", False),
            ("conany_data", "<", thirtyfive_days_ago),
            "|",
            ("conany_origen", "=", False),
            ("conany_origen", "!=", "manual"),
        ]
        toupdate_cups_id = toupdate_cups_id + cups_obj.search(cursor, uid, cups_search)
        msg.append("Trobats {} cups a updatar".format(len(toupdate_cups_id)))

        cups_updated = 0
        for cups_id in toupdate_cups_id:
            try:
                cups_obj.omple_consum_anual_periods(cursor, uid, cups_id, periods=True)
                cups_updated += 1
            except Exception as e:
                failed.append(("cups update", cups_id, str(e)))

        msg.append("Updatats {} cups".format(cups_updated))
        msg.append(str(datetime.today()))
        msg = "\n".join(msg)
        if failed:
            msg += "\n\nErrors\n"
            for fail in failed:
                msg += "{} {} {}\n".format(fail[0], fail[1], fail[2])

        return msg

    def _cronjob_conany_updater_mail_text(self, cursor, uid, data=None, context=None):
        if not data:
            data = {}
        if not context:
            context = {}

        subject = _(u"Resultat accions update de consum anual")
        msg = self._conany_updater(cursor, uid, context)
        emails_to = filter(lambda a: bool(a), map(str.strip, data.get("emails_to", "").split(",")))
        if emails_to:
            user_obj = self.pool.get("res.users")
            email_from = user_obj.browse(cursor, uid, uid).address_id.email
            email_send(email_from, emails_to, subject, msg)

        return True

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
