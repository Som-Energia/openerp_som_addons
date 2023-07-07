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

GiscedataFacturacioFacturaReportV2()
