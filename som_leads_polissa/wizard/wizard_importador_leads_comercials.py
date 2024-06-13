# -*- coding: utf-8 -*-
from osv import fields, osv
import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("import.crm.leads")


class WizardImportarLeadsComercials(osv.osv):
    _inherit = "wizard.importador.leads.comercials"

    def import_file(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if type(ids) not in (list, tuple):
            ids = [ids]

        res = super(WizardImportarLeadsComercials, self).import_file(
            cursor, uid, ids, context
        )
        self.add_values_from_wizard(cursor, uid, ids[0], res, context)
        return res

    def add_values_from_wizard(self, cursor, uid, wiz_id, leads_ids, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, wiz_id, context=context)
        lead_o = self.pool.get("giscedata.crm.lead")

        wiz_vals = {
            "llista_preu": wiz.llista_preus.id,
            "atr_proces_name": wiz.atr_proces_name,
            "coeficient_k": wiz.coeficient_k
        }

        for lead_id in leads_ids:
            lead_vals = lead_o.read(
                cursor, uid, lead_id, list(wiz_vals.keys()), context=context
            )

            write_vals = {}
            for val in lead_vals:
                if not lead_vals[val]:
                    write_vals[val] = wiz_vals[val]

            lead_o.write(cursor, uid, lead_id, write_vals, context=context)

    _columns = {
        "llista_preus": fields.many2one("product.pricelist", "Tarifa", required=False),
        "atr_proces_name": fields.selection(
            [("A3", "A3"), ("C1", "C1")], "Procés d'alta", required=False),
        "coeficient_k": fields.float("Coeficient K €/MWh", digits=(5, 3)),
    }


WizardImportarLeadsComercials()
