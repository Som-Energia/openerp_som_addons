# -*- coding: utf-8 -*-
import datetime
import os
import base64

from autoworker import AutoWorker
from oorq.decorators import job, create_jobs_group
from osv import fields, osv
from tools.translate import _

import unicodedata

ESTAT_ENVIAT = [
    ("obert", "Obert"),
    ("encuat", "Encuat per enviar"),
    ("enviat", "Enviat"),
    ("cancellat", "Cancel·lat"),
]


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


class SomEnviamentMassiu(osv.osv):
    _name = "som.enviament.massiu"

    def attach_pdf(self, cursor, uid, ids, filepath, filename):
        if isinstance(ids, (tuple, list)):
            ids = ids[0]
        enviament = self.browse(cursor, uid, ids)
        attachment_obj = self.pool.get("ir.attachment")
        attachment_to_delete = attachment_obj.search(
            cursor,
            uid,
            [("res_id", "=", ids), ("res_model", "=", "som.enviament.massiu")],
        )

        with open(filepath, "r") as pdf_file:
            data = pdf_file.read()
            values = {
                "name": "Lot {}, contracte {}".format(
                    enviament.lot_enviament.name, enviament.polissa_id.name
                ),
                "datas_fname": filename,
                "datas": base64.b64encode(data),
                "res_model": "som.enviament.massiu",
                "res_id": ids,
            }
            attachment_obj.create(cursor, uid, values)

        attachment_obj.unlink(cursor, uid, attachment_to_delete)

        if os.path.isfile(filepath) or os.path.islink(filepath):
            os.unlink(filepath)

    def create(self, cursor, uid, vals=None, context=None):
        if "polissa_id" in vals:
            pol_obj = self.pool.get("giscedata.polissa")
            titular_id = pol_obj.read(cursor, uid, vals["polissa_id"], ["titular"])["titular"][0]
            vals["partner_id"] = titular_id
        elif "invoice_id" in vals:
            inv_obj = self.pool.get("account.invoice")
            partner_id = inv_obj.read(cursor, uid, vals["invoice_id"], ["partner_id"])[
                "partner_id"
            ][0]
            vals["partner_id"] = partner_id

        return super(SomEnviamentMassiu, self).create(cursor, uid, vals, context)

    def add_info_line(self, cursor, uid, ids, new_info, context=None):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        for env_id in ids:
            env = self.browse(cursor, uid, env_id)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info = env.info if env.info else ""
            env.write({"info": str(now) + ": " + new_info + "\n" + info})

    def send_reports(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        if not ids:
            return
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        lot_name = self.read(cursor, uid, ids[0], ["lot_enviament"])["lot_enviament"][1]
        job_ids = []
        for _id in ids:
            j = self.send_single_report_async(cursor, uid, _id, context)
            job_ids.append(j.id)
        create_jobs_group(
            cursor.dbname,
            uid,
            _("Enviament Massiu Lot {} - {} enviaments").format(lot_name, len(ids)),
            "infoenergia.infoenergia_send",
            job_ids,
        )
        aw = AutoWorker(queue="infoenergia_send", default_result_ttl=24 * 3600)
        aw.work()

    def send_single_report(self, cursor, uid, _id, context=None):
        if context is None:
            context = {}
        if isinstance(_id, (tuple, list)):
            _id = _id[0]

        attach_obj = self.pool.get("ir.attachment")
        pe_send_obj = self.pool.get("poweremail.send.wizard")
        enviament = self.browse(cursor, uid, _id, context=context)
        allowed_states = ["obert"]
        if context.get("allow_reenviar", False):
            allowed_states.append("enviat")
        if enviament.estat not in allowed_states:
            return

        template_id = enviament.lot_enviament.email_template.id
        tmpl = enviament.lot_enviament.email_template

        ctx = context.copy()
        ctx.update(
            {
                "src_rec_ids": [_id],
                "src_model": "som.enviament.massiu",
                "template_id": template_id,
                "active_id": _id,
            }
        )
        send_id = pe_send_obj.create(cursor, uid, {}, context=ctx)
        vals = {"from": tmpl.enforce_from_account.id}
        if context.get("email_to", False):
            vals.update({"to": context.get("email_to")})
            vals.update({"bcc": ""})
        if context.get("email_subject", False):
            vals.update({"subject": context.get("email_subject")})
        attachment_id = attach_obj.search(
            cursor,
            uid,
            [("res_id", "=", _id), ("res_model", "=", "som.enviament.massiu")],
        )
        if attachment_id:
            vals.update({"attachment_ids": [(6, 0, [attachment_id[0]])]})
        pe_send_obj.write(cursor, uid, [send_id], vals, context=ctx)
        sender = pe_send_obj.browse(cursor, uid, send_id, context=ctx)
        sender.send_mail(context=ctx)

    @job(queue="infoenergia_send")
    def send_single_report_async(self, cursor, uid, id, context=None):
        self.send_single_report(cursor, uid, id, context)

    def poweremail_create_callback(self, cursor, uid, ids, vals, context=None):
        """Hook que cridarà el poweremail quan es creei un email
        a partir d'un enviament.
        """
        origin_ids = context.get("pe_callback_origin_ids", {})
        for _id in ids:
            self.write(cursor, uid, _id, {"estat": "encuat", "mail_id": origin_ids.get(_id, False)})
            self.add_info_line(cursor, uid, _id, "Correu encuat per enviar", context)
        return True

    def poweremail_write_callback(self, cursor, uid, ids, vals, context=None):
        """Hook que cridarà el poweremail quan es modifiqui un email."""
        if context is None:
            context = {}
        if "date_mail" in vals and "folder" in vals:
            vals_w = {"date_sent": vals["date_mail"], "folder": vals["folder"]}
            if vals_w["folder"] == "sent":
                for _id in ids:
                    if not self.browse(cursor, uid, _id).lot_enviament.is_test:
                        self.write(
                            cursor,
                            uid,
                            _id,
                            {"estat": "enviat", "data_enviament": vals_w["date_sent"]},
                        )
                        self.add_info_line(cursor, uid, _id, "Correu enviat", context)
                    else:
                        self.add_info_line(cursor, uid, _id, "Correu de test enviat", context)
                        self.write(cursor, uid, _id, {"estat": "obert"})
        return True

    def poweremail_unlink_callback(self, cursor, uid, ids, vals, context=None):
        """Hook que cridarà el poweremail quan s'esborra un email
        d'un enviament.
        """
        for _id in ids:
            self.write(cursor, uid, _id, {"estat": "obert"})
            self.add_info_line(cursor, uid, _id, "Correu eliminat de la bústia", context)
        return True

    _columns = {
        "polissa_id": fields.many2one(
            "giscedata.polissa", _("Contracte"), ondelete="restrict", select=True, pol_rel="no"
        ),
        "partner_id": fields.many2one(
            "res.partner", _("Contacte"), ondelete="restrict", select=True
        ),
        "invoice_id": fields.many2one(
            "account.invoice", _("Factura"), ondelete="restrict", select=True, pol_rel="no"
        ),
        "lang": fields.related(
            "partner_id",
            "lang",
            type="char",
            help=_("Idioma del partner"),
            string=_("Idioma"),
            readonly=True,
        ),
        "name": fields.related("partner_id", "name", type="char", string=_("Nom"), readonly=True),
        "estat": fields.selection(ESTAT_ENVIAT, _("Estat"), required=True),
        "lot_enviament": fields.many2one(
            "som.infoenergia.lot.enviament",
            _("Lot Enviament"),
            required=True,
            ondelete="restrict",
            select=True,
        ),
        "mail_id": fields.many2one("poweremail.mailbox", "Mail", ondelete="set null"),
        "data_enviament": fields.date(_("Data enviament"), allow_none=True),
        "info": fields.text(
            _(u"Informació Adicional"),
            help=_(u"Inclou qualsevol informació adicional, com els errors del Shera"),
        ),
        "extra_text": fields.text(
            _(u"Informació Extra"), help=_("Missatge que es vol afegir al correu")
        ),
    }

    _defaults = {
        "estat": lambda *a: "obert",
    }


SomEnviamentMassiu()
