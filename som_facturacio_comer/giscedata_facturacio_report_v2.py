from osv import osv

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

GiscedataFacturacioFacturaReportV2()
