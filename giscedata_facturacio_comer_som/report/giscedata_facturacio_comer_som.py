# -*- coding: utf-8 -*-

from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
import pooler


class report_webkit_html(report_sxw.rml_parse):
    def __init__(self, cursor, uid, name, context):
        super(report_webkit_html, self).__init__(cursor, uid, name,
                                                 context=context)
        self.localcontext.update({
            'cursor': cursor,
            'uid': uid,
            'addons_path': config['addons_path'],
        })



class FacturaReportSomWebkitParserHTML(webkit_report.WebKitParser):

    def __init__(
            self, name='report.giscedata.facturacio.factura',
            table='giscedata.facturacio.factura', rml=None,
            parser=report_webkit_html, header=True, store=False,
    ):

        super(FacturaReportSomWebkitParserHTML, self).__init__(
            name, table, rml, parser, header, store
        )

    def create(self, cursor, uid, ids, data, context=None):
        """
        To sign PDF of certain factures
        :param cursor:
        :param uid:
        :param ids:
        :param data:
        :param context:
        :return:
        """

        if context is None:
            context = {}
        pool = pooler.get_pool(cursor.dbname)
        factura_o = pool.get('giscedata.facturacio.factura')
        to_join = []

        factura_f = ['tarifa_acces_id.name']
        dmn = [('id', 'in', ids)]
        factura_vs = factura_o.q(cursor, uid).read(factura_f).where(dmn)

        file_type = 'pdf'

        for factura_v in factura_vs:
            # TODO s'ha de validar aquest IF
            if 'TD' in factura_v['tarifa_acces_id.name']:
                ctx = context.copy()
                ctx['webkit_signed_pdf'] = True
                res = super(FacturaReportSomWebkitParserHTML, self).create(
                    cursor, uid, [factura_v['id']], data, context=ctx
                )
            else:
                res = super(FacturaReportSomWebkitParserHTML, self).create(
                    cursor, uid, [factura_v['id']], data, context=context
                )

        return res


FacturaReportSomWebkitParserHTML(
    'report.giscedata.facturacio.factura',
    'giscedata.facturacio.factura',
    'giscedata_facturacio_comer_som/report/report_giscedata_facturacio_factura_comer.mako',
    parser=report_webkit_html
)