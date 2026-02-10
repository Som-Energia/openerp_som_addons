# -*- coding: utf-8 -*-
from osv import osv
from report_backend.report_backend import report_browsify
from copy import deepcopy


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
            'components_som': self._get_data_factura_som(cursor, uid, fra.id, context=context),
        })
        return data

    def _get_data_factura_som(self, cursor, uid, fra_id, context=None):
        sr_obj = self.pool.get("giscedata.facturacio.factura.report")

        legacy_components = [
            'amount_destination',
            'contract_data',
            'emergency_complaints',
            'energy_consumption_graphic',
            'invoice_details_comments',
            'invoice_details_energy',
            'invoice_details_generation',
            'invoice_details_other_concepts',
            'invoice_details_power',
            'invoice_details_reactive',
            'invoice_details_tec271',
            'invoice_summary',
            'maximeter_readings_table',
            'meters',
            'reactive_readings_table',
            'readings_6x',
            'readings_g_table',
            'readings_table',
            'readings_text',
        ]
        ctx = deepcopy(context) or {}
        ctx.update({'deny_list': legacy_components + [
            'cnmc_comparator_qr_link',  # data also present under 'cnmc' key
        ]})
        return sr_obj.get_components_data_dict(cursor, uid, fra_id, context=ctx)


GiscedataFacturacioFacturaReportV2()
