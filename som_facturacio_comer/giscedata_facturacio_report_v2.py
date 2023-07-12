# -*- coding: utf-8 -*-
from osv import osv
from report_backend.report_backend import report_browsify

class GiscedataFacturacioFacturaReportV2(osv.osv):
    _inherit = 'giscedata.facturacio.factura.report.v2'

    def get_parametres_energia(self, data):
        parametres_energia = super(GiscedataFacturacioFacturaReportV2, self).get_parametres_energia(data)
        parametres_energia_sense_gwkh = []
        for parametre in parametres_energia:
            if parametre[0] != 'prEh':
                parametres_energia_sense_gwkh.append(parametre)
        return parametres_energia_sense_gwkh

    def get_tc(self, data):
        tc = super(GiscedataFacturacioFacturaReportV2, self).get_tc(data)

        if data['factura']['te_gkwh']:
            tc = 'I0'

        return tc

    @report_browsify
    def get_factura(self, cursor, uid, fra, context=None):
        res = super(GiscedataFacturacioFacturaReportV2, self).get_factura(cursor, uid, fra, context=context)
        res['te_gkwh'] = fra.is_gkwh
        return res

    def get_impsa(self, data, linies_importe_otros):
        res = super(GiscedataFacturacioFacturaReportV2, self).get_impsa(data, linies_importe_otros)

        for linia in data['linies']['altres']:
            if linia['metadata']['code'] in ['DN01', 'DN02', 'DONATIU']:
                donatiu_sense_iva = linia['import'].val / 1.21
                res += float(format(donatiu_sense_iva, '.2f'))
        return res

    # Posem total_preu_linies_sense_iva perquè els conceptes de linia sense iva estan a impsa / 1.21.
    # Ens ho ha comunicat la CNMC que s'ha de fer així
    def get_linies_importe_otros(self, data):
        linies_importe_otros, total_preu_linies_sense_iva = super(GiscedataFacturacioFacturaReportV2, self).get_linies_importe_otros(data)
        return linies_importe_otros, 0

GiscedataFacturacioFacturaReportV2()
