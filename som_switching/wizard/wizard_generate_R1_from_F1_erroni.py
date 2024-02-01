# -*- coding: utf-8 -*-
from datetime import datetime
from gestionatr.defs import *
from gestionatr.input.messages.R1 import get_minimum_fields
from osv import osv, fields, orm
from tools.translate import _
import xml.etree.ElementTree as ET


class WizardGenerateR1FromF1Erroni(osv.osv_memory):
    """Wizard to generate R1 Cases from contracts."""

    _name = "wizard.r1.from.f1.erroni"
    _inherit = "wizard.r1.from.f1.erroni"

    def create_atr_case(self, cursor, uid, ids, line_id, context=None):
        if context is None:
            context = {}
        winfo = self.read(cursor, uid, ids, ["doc_add", "doc_ids"])[0]
        context.update({"r1_doc_add": {"doc_add": winfo["doc_add"], "doc_ids": winfo["doc_ids"]}})
        res = super(WizardGenerateR1FromF1Erroni, self).create_atr_case(
            cursor, uid, ids, line_id, context=context
        )
        if not isinstance(res[-1], long):
            return res

        pol_obj = self.pool.get("giscedata.polissa")
        cups_obj = self.pool.get("giscedata.cups.ps")
        user_obj = self.pool.get("res.users")
        sw_obj = self.pool.get("giscedata.switching")

        line_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        line_info = line_obj.read(cursor, uid, line_id, ["cups_id", "cups_text"], context=context)
        cups_id = line_info["cups_id"]
        polissa_id = False
        if not cups_id:
            cups_id = cups_obj.search(cursor, uid, [("name", "=", line_info["cups_text"])])
        if cups_id:
            cups_id = cups_id[0]
            ctx = context.copy()
            ctx["search_non_active"] = True
            polissa_id = sw_obj.trobar_polissa_w_cups(cursor, uid, cups_id, context=ctx)

        if not polissa_id:
            return res

        subtipus_info = {"type": "02", "name": "037"}

        pinf = pol_obj.read(cursor, uid, polissa_id, ["observacions", "category_id"])

        # Escriure al contracte el comentari:
        # "Data_Usuari_Reclamació (codi Cas) SUBTIPUS. Generat el pas R1-01”
        subtipus_info_str = "{0}-{1}".format(subtipus_info["type"], subtipus_info["name"])
        user_name = user_obj.read(cursor, uid, uid, ["name"])["name"]
        sw_code = sw_obj.read(cursor, uid, res[-1], ["codi_sollicitud"])["codi_sollicitud"]
        new_text = _(u"{0}, {1}, Reclamació {2}: SUBTIPUS {3}. Generat el pas R1-01\n\n").format(
            datetime.today().strftime("%d-%m-%Y"), user_name, sw_code, subtipus_info_str
        )

        # Activar categoria “Reclamacions lectura / en curs”
        imd_obj = self.pool.get("ir.model.data")
        categoria_id = imd_obj.get_object_reference(
            cursor, uid, "som_polissa_soci", "som_sw_reclamacions_lectura_en_curs"
        )[1]
        category_ids = pinf["category_id"]

        # Asignar al responsable genèric
        responsable = user_obj.search(cursor, uid, [("login", "=", "r1manager")])
        if len(responsable):
            sw_obj.write(cursor, uid, res[-1], {"user_id": responsable[0]})

        pol_vals = {
            "observacions": new_text + (pinf["observacions"] or ""),
            "category_id": [(6, 0, category_ids + [categoria_id])],
        }

        pol_obj.write(cursor, uid, polissa_id, pol_vals)

        return res

    _columns = {
        # Document fields
        "doc_add": fields.boolean(u"Documents adjunts"),
        "doc_ids": fields.many2many(
            "giscedata.switching.document",
            "sw_wiz_r1_doc_ref",
            "wiz_r1_id",
            "document_id",
            string="Documents",
            domain=[("type", "=", "whatever")],
        ),
    }


WizardGenerateR1FromF1Erroni()
