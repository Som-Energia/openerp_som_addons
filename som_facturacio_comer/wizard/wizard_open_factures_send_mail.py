# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
import logging


class WizardOpenFacturesSendMail(osv.osv_memory):
    """"""

    _name = "wizard.open.factures.send.mail"

    def open_factures_send_mail(self, cursor, uid, ids, context=None):
        import pooler

        logger = logging.getLogger("openerp" + __name__)
        if context is None:
            context = {}

        clot_obj = self.pool.get("giscedata.facturacio.contracte_lot")
        fact_obj = self.pool.get("giscedata.facturacio.factura")

        clot_ids = context.get("active_ids", [])

        open_facts = []
        for _id in clot_ids:
            clot_info = clot_obj.read(cursor, uid, _id, ["polissa_id", "lot_id", "state"])
            lot_id = clot_info["lot_id"][0]
            pol_id = clot_info["polissa_id"][0]
            f_ids = fact_obj.search(
                cursor,
                uid,
                [
                    ("polissa_id", "=", pol_id),
                    ("lot_facturacio", "=", lot_id),
                    ("state", "=", "draft"),
                    ("type", "=", "out_invoice"),
                ],
            )
            db = pooler.get_db_only(cursor.dbname)
            tmp_cr = db.cursor()
            try:
                if clot_info["state"] == "facturat_incident":
                    clot_obj.facturar_incident(cursor, uid, [_id])

                fact_infos = fact_obj.read(cursor, uid, f_ids, ["id", "date_invoice"])
                sorted_factures = sorted(fact_infos, key=lambda f: f["date_invoice"])
                for factura in sorted_factures:
                    factura_id = factura["id"]
                    fact_obj.invoice_open(cursor, uid, [factura_id], context=context)
                tmp_cr.commit()
                open_facts += f_ids
            except Exception as exc:
                logger.error("Error obrint la factura %s: %s ", factura["id"], exc)
                tmp_cr.rollback()
            finally:
                tmp_cr.close()

        if not open_facts:
            raise osv.except_osv(_("Error!"), ("No s'ha pogut obrir cap factura!"))

        src_obj = "giscedata.facturacio.factura"
        imd_obj = self.pool.get("ir.model.data")
        fact_template_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio_comer", "env_fact_via_email"
        )[1]
        ctx = {
            "src_model": src_obj,
            "template_id": fact_template_id,
            "src_rec_id": open_facts[0],
            "src_rec_ids": open_facts,
        }

        res = {
            "name": _("%s Mail Form"),
            "type": "ir.actions.act_window",
            "res_model": "poweremail.send.wizard",
            "src_model": src_obj,
            "view_type": "form",
            "context": str(ctx),
            "view_mode": "form,tree",
            "view_id": self.pool.get("ir.ui.view").search(
                cursor, uid, [("name", "=", "poweremail.send.wizard.form")], context=context
            ),
            "target": "new",
        }

        return res

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
    }

    _defaults = {"state": lambda *a: "init"}


WizardOpenFacturesSendMail()
