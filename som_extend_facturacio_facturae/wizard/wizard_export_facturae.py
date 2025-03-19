# -*- coding: utf-8 -*-

from osv import osv


class WizardExportFacturae(osv.osv_memory):

    _name = "wizard.export.facturae"
    _inherit = "wizard.export.facturae"

    def oncreated_facturae(self, cursor, uid, model, model_id, context=None):

        if model == "giscedata.facturacio.factura":
            fact_obj = self.pool.get("giscedata.facturacio.factura")
            vals = {"has_facturae": True}
            fact_obj.write(cursor, uid, model_id, vals, context=context)

        super(WizardExportFacturae, self).oncreated_facturae(cursor, uid, model, model_id, context)


WizardExportFacturae()
