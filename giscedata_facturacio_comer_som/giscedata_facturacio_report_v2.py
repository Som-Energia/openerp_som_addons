# -*- coding: utf-8 -*-
from osv import osv
from report_backend.report_backend import report_browsify


class GiscedataFacturacioFacturaReportV2(osv.osv):
    _inherit = "giscedata.facturacio.factura.report.v2"

    @report_browsify
    def get_data(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}
        data = super(GiscedataFacturacioFacturaReportV2, self).get_data(
            cursor, uid, fra, context=context
        )

        data.update({
            'factura_som': self._get_data_factura_som(cursor, uid, fra.id, context=context),
        })
        return data

    def _get_data_factura_som(self, cursor, uid, fra_id, context=None):
        sr_obj = self.pool.get("giscedata.facturacio.factura.report")
        return sr_obj.get_components_data_dict(cursor, uid, fra_id, context=context)


GiscedataFacturacioFacturaReportV2()
