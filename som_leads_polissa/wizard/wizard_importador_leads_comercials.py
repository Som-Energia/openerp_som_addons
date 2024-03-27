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

        write_vals = {
            "llista_preu": wiz.llista_preus,
            "condicions_generals_id": wiz.condicions_generals_id,
            "atr_proces_name": wiz.atr_proces_name
        }

        lead_o.write(cursor, uid, leads_ids, write_vals, context=context)

    _columns = {
        "llista_preus": fields.many2one("product.pricelist", "Tarifa", required=True),
        "condicions_generals_id": fields.many2one(
            "giscedata.polissa.condicions.generals", "Condicions Generals", required=True),
        'atr_proces_name': fields.selection(
            [('A3', 'A3'), ('C1', 'C1'), ('C2', 'C2')], "Procés d'alta", required=True),
    }


WizardImportarLeadsComercials()
