# -*- coding: utf-8 -*-
from datetime import datetime
from gestionatr.defs import *
from gestionatr.input.messages.R1 import get_minimum_fields
from osv import osv, fields, orm
from tools.translate import _
import xml.etree.ElementTree as ET


class GiscedataSwitchingWizardR101(osv.osv_memory):

    _name = "giscedata.switching.r101.wizard"
    _inherit = "giscedata.switching.r101.wizard"

    def _default_facturacio_suspesa(self, cursor, uid, context=None):
        return True

    def _default_refacturacio_pendent(self, cursor, uid, context=None):
        return True

    def action_create_atr_case(self, cursor, uid, ids, context=None):
        winfo = self.read(
            cursor,
            uid,
            ids,
            ["facturacio_suspesa", "refacturacio_pendent", "invoice", "doc_add", "doc_ids"],
        )[0]
        context.update({"r1_doc_add": {"doc_add": winfo["doc_add"], "doc_ids": winfo["doc_ids"]}})

        res = super(GiscedataSwitchingWizardR101, self).action_create_atr_case(
            cursor, uid, ids, context=context
        )
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")
        factinfo = fact_obj.read(cursor, uid, winfo["invoice"], ["polissa_id"])
        if winfo["facturacio_suspesa"]:
            pol_obj.write(
                cursor,
                uid,
                factinfo["polissa_id"][0],
                {
                    "facturacio_suspesa": winfo["facturacio_suspesa"],
                    "observacio_suspesa": res[0].replace("\n", ""),
                },
            )
        if winfo["refacturacio_pendent"]:
            pol_obj.write(
                cursor,
                uid,
                factinfo["polissa_id"][0],
                {"refacturacio_pendent": winfo["refacturacio_pendent"]},
            )
        return res

    _columns = {
        "facturacio_suspesa": fields.boolean("Marcar contracte amb facturació suspesa"),
        "refacturacio_pendent": fields.boolean("Marcar contracte amb refacturacio pendent"),
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

    _defaults = {
        "facturacio_suspesa": _default_facturacio_suspesa,
        "refacturacio_pendent": _default_refacturacio_pendent,
    }


GiscedataSwitchingWizardR101()
