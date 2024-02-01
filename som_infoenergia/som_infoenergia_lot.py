# -*- coding: utf-8 -*-
import os, datetime, csv
from dateutil.relativedelta import relativedelta
from paramiko import SSHClient, AutoAddPolicy
import tempfile, shutil
import base64
from scp import SCPClient
import shutil
from StringIO import StringIO

from autoworker import AutoWorker
from oorq.decorators import job, create_jobs_group
from osv import fields, osv
from tools.translate import _
from tools import config
from som_infoenergia.pdf_tools import topdf

TIPUS_LOT = [
    ("infoenergia", "Infoenergia"),
    ("altres", "Altres"),
]

ESTAT_LOT = [
    ("esborrany", "Esborrany"),
    ("obert", "Obert"),
    ("realitzat", "Realitzat"),
]

TIPUS_INFORME = [
    ("m1", "M1 terciari"),
    ("m2", "M2 domèstic"),
    ("m5", "M5 domèstic"),
    ("m6_domestic", "M6 domèstic"),
    ("m6_terciari", "M6 terciari"),
    ("m10", "M10 terciari"),
    ("m11", "M11 domèstic"),
    ("fv", "FV (fotovoltaic)"),
    ("altres", "Altres"),
]


def get_ssh_connection():
    beedata_user = config.get("beedata_ssh_user", "")
    beedata_password = config.get("beedata_ssh_password", "")
    beedata_host = config.get("beedata_ssh_host", "")
    beedata_port = config.get("beedata_ssh_port", "22")

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(AutoAddPolicy)

    ssh.connect(
        hostname=beedata_host,
        port=int(beedata_port),
        username=beedata_user,
        password=beedata_password,
    )
    return ssh


class SomInfoenergiaLotEnviament(osv.osv):
    _name = "som.infoenergia.lot.enviament"

    def _attach_csv(self, cursor, uid, ids, filepath):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]
        attachment_obj = self.pool.get("ir.attachment")
        attachment_to_delete = attachment_obj.search(
            cursor, uid, [("res_id", "=", ids), ("res_model", "=", "som.infoenergia.lot.enviament")]
        )

        with open(filepath, "r") as pdf_file:
            data = pdf_file.read()
            values = {
                "name": "Enviaments.csv",
                "datas": base64.b64encode(data),
                "res_model": "som.infoenergia.lot.enviament",
                "res_id": ids,
            }
            attachment_id = attachment_obj.create(cursor, uid, values)

        attachment_obj.unlink(cursor, uid, attachment_to_delete)

        if os.path.isfile(filepath) or os.path.islink(filepath):
            os.unlink(filepath)
        return attachment_id

    def create_enviaments_from_csv_file(self, cursor, uid, ids, filename, context=None):
        with open(filename, "rb") as csv_file:
            headers = [h.lower() for h in csv.reader(csv_file, delimiter=";", quotechar='"').next()]

            csv_dictReader = csv.DictReader(
                csv_file, delimiter=";", quotechar='"', fieldnames=headers, restkey="wrong_row"
            )
            csv_data = list(csv_dictReader)

            self.create_enviaments_from_csv(cursor, uid, ids, csv_data, context)

    def create_enviaments_from_object_list(self, cursor, uid, ids, object_ids, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        lot_info = self.read(cursor, uid, ids, ["name", "tipus"])
        context["tipus"] = lot_info["tipus"]
        job_ids = []

        contexte = context.copy()
        for obj_id in object_ids:
            if context.get("extra_text", False):
                pol_obj = self.pool.get("giscedata.polissa")
                pol_data = pol_obj.read(cursor, uid, obj_id, ["name"])
                contexte["extra_text"] = context["extra_text"][pol_data["name"]]

            job = self.create_single_enviament_from_object_async(
                cursor, uid, ids, obj_id, context=contexte
            )
            job_ids.append(job.id)

        if not job_ids:
            return False

        # Create a jobs_group to see the status of the operation
        create_jobs_group(
            cursor.dbname,
            uid,
            _("Crear Enviaments al lot {0} a partir de {1} {2}.").format(
                lot_info["name"], len(job_ids), context["from_model"]
            ),
            "infoenergia.create_enviaments",
            job_ids,
        )
        amax_proc = int(
            self.pool.get("res.config").get(
                cursor, uid, "infoenergia_create_enviaments_tasks_max_procs", "0"
            )
        )
        if not amax_proc:
            amax_proc = None
        aw = AutoWorker(
            queue="infoenergia_create_enviament", default_result_ttl=24 * 3600, max_procs=amax_proc
        )
        aw.work()

        return True

    @job(queue="infoenergia_create_enviament")
    def create_single_enviament_from_object_async(self, cursor, uid, ids, object_id, context=None):
        self.create_single_enviament_from_object(cursor, uid, ids, object_id, context)

    def create_single_enviament_from_object(self, cursor, uid, ids, object_id, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        env_values = {
            "lot_enviament": ids,
            "estat": "preesborrany" if context["tipus"] == "infoenergia" else "obert",
        }
        if context["tipus"] == "infoenergia":
            env_obj = self.pool.get("som.infoenergia.enviament")
            context["from_model"] = "polissa_id"
            env_values.update({"found_in_search": True})
        elif context["tipus"] == "altres":
            env_obj = self.pool.get("som.enviament.massiu")

        env_values.update({context["from_model"]: object_id})
        if "extra_text" in context:
            env_values.update({"extra_text": context["extra_text"]})

        env_id = env_obj.search(
            cursor, uid, [("lot_enviament", "=", ids), (context["from_model"], "=", object_id)]
        )
        if not env_id:
            env_id = env_obj.create(cursor, uid, env_values, context)
            env_obj.add_info_line(
                cursor, uid, env_id, u"Enviament creat des de " + context["from_model"]
            )
        elif context["tipus"] == "infoenergia":
            env_obj.write(cursor, uid, env_id, {"found_in_search": True})

    def create_enviaments_from_csv(self, cursor, uid, ids, csv_data, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        for idx, env in enumerate(csv_data):
            self.create_single_enviament_async(cursor, uid, ids, env, context)

        return idx

    @job(queue="infoenergia_download")
    def create_single_enviament_async(self, cursor, uid, ids, env_data, context=None):
        self.create_single_enviament(cursor, uid, ids, env_data, context)

    def create_single_enviament(self, cursor, uid, ids, env_data, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        pol_obj = self.pool.get("giscedata.polissa")
        env_obj = self.pool.get("som.infoenergia.enviament")

        pol_ids = (
            pol_obj.search(cursor, uid, [("name", "=", env_data["contractid"])])
            if env_data["contractid"] != "True"
            else None
        )
        msg = ""
        env_values = {
            "polissa_id": pol_ids[0] if pol_ids else None,
            "pdf_filename": context.get("path_pdf", "") + "/" + env_data["report"],
            "num_polissa_csv": env_data["contractid"],
            "body_text": env_data["text"],
            "lot_enviament": ids,
            "estat": "esborrany",
        }
        if not pol_ids:
            pol_inactive_ids = (
                pol_obj.search(
                    cursor, uid, [("name", "=", env_data["contractid"]), ("active", "=", False)]
                )
                if env_data["contractid"] != "True"
                else None
            )
            if pol_inactive_ids:
                env_values["polissa_id"] = pol_inactive_ids[0]
                env_values["estat"] = "baixa"
                msg += "La pòlissa {} està donada de baixa. ".format(env_values["num_polissa_csv"])
            else:
                env_values["estat"] = "error"
                msg += "No s'ha trobat la pòlissa {}. ".format(env_values["num_polissa_csv"])

        env_id = env_obj.search(
            cursor,
            uid,
            [("lot_enviament", "=", ids), ("polissa_id", "=", env_values["polissa_id"])],
        )
        if "wrong_row" in env_data:
            env_values["estat"] = "error"
            msg += "La línia del csv té un format incorrecte: {}. ".format(env_data)
        if not env_data["valid"]:
            env_values["estat"] = "error"
            msg += 'Informe marcat "no vàlid" al csv. '

        if env_id:
            msg += "Dades actualitzades. "
            env_obj.write(cursor, uid, env_id[0], env_values, context)
        else:
            env_id = env_obj.create(cursor, uid, env_values, context)

        if msg:
            env_obj.add_info_line(cursor, uid, env_id, msg)

        return True

    def add_info_line(self, cursor, uid, ids, new_info, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]
        lot = self.browse(cursor, uid, ids)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info = lot.info if lot.info else ""
        lot.write({"info": str(now) + ": " + new_info + "\n" + info})

    def get_csv(self, cursor, uid, ids, context=None):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        lot_obj = self.pool.get("som.infoenergia.lot.enviament")
        lot = lot_obj.browse(cursor, uid, ids)

        try:
            ssh = get_ssh_connection()
            output_dir = config.get("infoenergia_report_download_dir", "/tmp/test_shera/reports")

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            csv_path_file = context.get("path_csv", "")
            output_filepath = os.path.join(output_dir, "Enviaments.csv")

            scp = SCPClient(ssh.get_transport())
            scp.get(csv_path_file, output_filepath)

            lot.create_enviaments_from_csv_file(output_filepath, context)
            self._attach_csv(cursor, uid, ids, output_filepath)

            self.add_info_line(cursor, uid, ids, "CSV descarregat correctament")
        except Exception as e:
            message = "ERROR " + str(e)
            self.add_info_line(cursor, uid, ids, message)

    def get_enviament_object(self, cursor, uid, id, context=None):
        if isinstance(id, (tuple, list)):
            id = id[0]
        tipus = self.read(cursor, uid, id, ["tipus"])["tipus"]

        if tipus == "infoenergia":
            env_obj = self.pool.get("som.infoenergia.enviament")
        elif tipus == "altres":
            env_obj = self.pool.get("som.enviament.massiu")

        return env_obj

    def cancel_enviaments_from_polissa_names(
        self, cursor, uid, ids, polissa_name_list, context=None
    ):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        tipus = self.read(cursor, uid, ids, ["tipus"])["tipus"]
        if tipus == "infoenergia":
            env_obj = self.pool.get("som.infoenergia.enviament")
            context["from_model"] = "polissa_id"
        elif tipus == "altres":
            env_obj = self.pool.get("som.enviament.massiu")

        env_ids = env_obj.search(
            cursor,
            uid,
            [("lot_enviament", "=", ids), ("polissa_id.name", "in", polissa_name_list)],
            context={"active_test": False},
        )
        env_obj.write(cursor, uid, env_ids, {"estat": "cancellat"})
        env_obj.add_info_line(
            cursor, uid, env_ids, u"Enviament cancel·lat per " + context["reason"]
        )

    def _ff_totals(self, cursor, uid, ids, field_name, arg, context=None):
        res = {}
        estats = {
            "total_preesborrany": "preesborrany",
            "total_esborrany": "esborrany",
            "total_oberts": "obert",
            "total_enviats": "enviat",
            "total_cancelats": "cancellat",
            "total_baixa": "baixa",
            "total_errors": "error",
            "total_encuats": "encuat",
        }

        if field_name == "total_enviaments":
            for _id in ids:
                env_obj = self.get_enviament_object(cursor, uid, _id)
                res[_id] = env_obj.search_count(cursor, uid, [("lot_enviament.id", "=", _id)])
        elif field_name == "total_enviaments_in_search":
            for _id in ids:
                env_obj = self.get_enviament_object(cursor, uid, _id)
                res[_id] = env_obj.search_count(
                    cursor, uid, [("lot_enviament.id", "=", _id), ("found_in_search", "=", True)]
                )
        elif field_name == "total_env_csv":
            for _id in ids:
                tipus = self.read(cursor, uid, _id, ["tipus"])["tipus"]
                if tipus == "infoenergia":
                    env_obj = self.pool.get("som.infoenergia.enviament")
                    res[_id] = env_obj.search_count(
                        cursor, uid, [("lot_enviament.id", "=", _id), ("pdf_filename", "!=", "")]
                    )
                else:
                    res[_id] = 0
        elif field_name == "total_env_csv_in_search":
            for _id in ids:
                tipus = self.read(cursor, uid, _id, ["tipus"])["tipus"]
                if tipus == "infoenergia":
                    env_obj = self.pool.get("som.infoenergia.enviament")
                    res[_id] = env_obj.search_count(
                        cursor,
                        uid,
                        [
                            ("lot_enviament.id", "=", _id),
                            ("pdf_filename", "!=", ""),
                            ("found_in_search", "=", True),
                        ],
                    )
                else:
                    res[_id] = 0
        elif "_in_search" in field_name:
            for _id in ids:
                tipus = self.read(cursor, uid, _id, ["tipus"])["tipus"]
                if tipus == "infoenergia":
                    field_name = field_name.replace("_in_search", "")
                    env_obj = self.pool.get("som.infoenergia.enviament")
                    res[_id] = env_obj.search_count(
                        cursor,
                        uid,
                        [
                            ("lot_enviament.id", "=", _id),
                            ("found_in_search", "=", True),
                            ("estat", "=", estats[field_name]),
                        ],
                    )
                else:
                    res[_id] = 0
        else:
            for _id in ids:
                env_obj = self.get_enviament_object(cursor, uid, _id)
                res[_id] = env_obj.search_count(
                    cursor,
                    uid,
                    [("lot_enviament.id", "=", _id), ("estat", "=", estats[field_name])],
                )
        return res

    def _ff_progress(self, cursor, uid, ids, field_name, arg, context=None):
        res = {}
        for _id in ids:
            env_obj = self.get_enviament_object(cursor, uid, _id)
            total_enviaments = float(
                self.read(cursor, uid, _id, ["total_enviaments"])["total_enviaments"]
            )
            tipus = self.read(cursor, uid, _id, ["tipus"])["tipus"]
            if not total_enviaments:
                res[_id] = 0
            elif field_name == "env_sending_progress":
                total_env_enviats = env_obj.search_count(
                    cursor, uid, [("lot_enviament.id", "=", _id), ("data_enviament", "!=", False)]
                )
                res[_id] = (total_env_enviats / total_enviaments) * 100
            elif tipus == "infoenergia" and field_name == "env_csv_progress":
                total_env_csv = self.read(cursor, uid, _id, ["total_env_csv"])["total_env_csv"]
                res[_id] = (total_env_csv / total_enviaments) * 100
            elif tipus == "infoenergia" and field_name == "pdf_download_progress":
                total_env_amb_pdf = env_obj.search_count(
                    cursor, uid, [("lot_enviament.id", "=", _id), ("data_informe", "!=", False)]
                )
                res[_id] = (total_env_amb_pdf / total_enviaments) * 100
            else:
                res[_id] = 0

        return res

    _columns = {
        "name": fields.char(_("Nom del lot"), size=256, required=True),
        "estat": fields.selection(ESTAT_LOT, _("Estat"), required=True),
        "tipus": fields.selection(TIPUS_LOT, _("Tipus de lot"), required=True),
        "is_test": fields.boolean("Test", help=_(u"És un enviament de prova?")),
        "tipus_informe": fields.selection(
            TIPUS_INFORME,
            _("Tipus d'informe"),
        ),
        "info": fields.text(
            _(u"Informació Adicional"),
            help=_(u"Inclou qualsevol informació adicional, com els errors del Shera"),
        ),
        "email_template": fields.many2one(
            "poweremail.templates",
            "Plantilla del correu del lot",
            required=True,
            domain="[('object_name.model', 'in', ['som.enviament.massiu','som.infoenergia.enviament'])]",
        ),
        "total_env_csv": fields.function(
            _ff_totals,
            string="Enviaments presents en CSVs",
            help="Enviaments que han estat informats en algun CSV descarregat de Beedata",
            readonly=True,
            type="integer",
            method=True,
        ),
        "total_enviaments": fields.function(
            _ff_totals, string="Enviaments totals", readonly=True, type="integer", method=True
        ),
        "total_enviats": fields.function(
            _ff_totals, string="Enviaments enviats", readonly=True, type="integer", method=True
        ),
        "total_encuats": fields.function(
            _ff_totals,
            string="Enviaments encuats per enviar",
            readonly=True,
            type="integer",
            method=True,
            help="S'ha realitzat l'acció d'enviar i el procés en segon pla té la tasca pendent",
        ),
        "total_oberts": fields.function(
            _ff_totals,
            string="Enviaments oberts",
            readonly=True,
            type="integer",
            method=True,
            help="Enviaments que tenen el PDF adjunt i encara no s'han enviat",
        ),
        "total_esborrany": fields.function(
            _ff_totals, string="Enviaments en esborrany", readonly=True, type="integer", method=True
        ),
        "total_preesborrany": fields.function(
            _ff_totals,
            string="Enviaments en pre-esborrany",
            help="Enviaments que s'han creat des d'una pòlissa i no s'han descarregat en cap CSV",
            readonly=True,
            type="integer",
            method=True,
        ),
        "total_cancelats": fields.function(
            _ff_totals,
            string="Enviaments cancel·lats",
            readonly=True,
            type="integer",
            method=True,
            help="Ja sigui perquè la pòlissa té l'enviament deshabilitat, s'ha cancel·lat a través d'una acció...",
        ),
        "total_baixa": fields.function(
            _ff_totals,
            string="Enviaments de baixa",
            readonly=True,
            type="integer",
            method=True,
            help="Enviaments que tenen associat una pòlissa de baixa o amb data de baixa",
        ),
        "total_errors": fields.function(
            _ff_totals, string="Enviaments amb error", readonly=True, type="integer", method=True
        ),
        "env_csv_progress": fields.function(
            _ff_progress,
            string="Enviaments informats en algun CSV descarregat",
            readonly=True,
            type="float",
            method=True,
            help="Indica quants enviaments s'han trobat en algun CSV descarregat de Beedata",
        ),
        "pdf_download_progress": fields.function(
            _ff_progress,
            string="Enviaments amb PDF descarregat",
            readonly=True,
            type="float",
            method=True,
            help="Indica quants PDFs s'han descarregat del total d'enviaments del Lot",
        ),
        "env_sending_progress": fields.function(
            _ff_progress,
            string="Enviaments enviats",
            readonly=True,
            type="float",
            method=True,
            help="Indica quants enviaments s'han enviat del total d'enviaments del Lot",
        ),
        "total_esborrany_in_search": fields.function(
            _ff_totals,
            string="Enviaments en esborrany trobats en cerca",
            readonly=True,
            type="integer",
            method=True,
        ),
        "total_oberts_in_search": fields.function(
            _ff_totals,
            string="Enviaments oberts trobats en cerca",
            readonly=True,
            type="integer",
            method=True,
        ),
        "total_enviats_in_search": fields.function(
            _ff_totals,
            string="Enviaments enviats trobats en cerca",
            readonly=True,
            type="integer",
            method=True,
        ),
        "total_baixa_in_search": fields.function(
            _ff_totals,
            string="Enviaments de baixa trobats en cerca",
            readonly=True,
            type="integer",
            method=True,
        ),
        "total_encuats_in_search": fields.function(
            _ff_totals,
            string="Enviaments encuats per enviar trobats en cerca",
            readonly=True,
            type="integer",
            method=True,
        ),
        "total_cancelats_in_search": fields.function(
            _ff_totals,
            string="Enviaments cancel·lats trobats en cerca",
            readonly=True,
            type="integer",
            method=True,
        ),
        "total_errors_in_search": fields.function(
            _ff_totals,
            string="Enviaments amb error trobats en cerca",
            readonly=True,
            type="integer",
            method=True,
        ),
        "total_enviaments_in_search": fields.function(
            _ff_totals,
            string="Enviaments totals trobats en cerca",
            readonly=True,
            type="integer",
            method=True,
        ),
        "total_env_csv_in_search": fields.function(
            _ff_totals,
            string="Enviaments totals informats en algun CSV descarregat de Beedata trobats en cerca",
            readonly=True,
            type="integer",
            method=True,
        ),
    }

    _defaults = {
        "estat": lambda *a: "obert",
        "tipus": lambda *a: "infoenergia",
        "is_test": lambda *a: False,
        "env_csv_progress": lambda *a: 0,
        "pdf_download_progress": lambda *a: 0,
        "env_sending_progress": lambda *a: 0,
    }


SomInfoenergiaLotEnviament()
