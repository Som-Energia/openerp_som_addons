# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from mako.template import Template


class ReportBackendInvoiceEmail(ReportBackend):
    _source_model = 'giscedata.facturacio.factura'
    _name = 'report.backend.invoice.email'

    @report_browsify
    def get_data(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}

        report_factura_obj = self.pool.get('giscedata.facturacio.factura.report.v2')

        data = {
            'comerci': self.get_comerci(cursor, uid, fra, context=context),
            'polissa': self.get_polissa(cursor, uid, fra, context=context),
            'factura': report_factura_obj.get_factura(cursor, uid, fra, context=context),
            'socia': self.get_socia(cursor, uid, fra, context=context),
            'text_correu': self.get_text_correu(cursor, uid, fra, context=context),
            'lang': fra.partner_id.lang,
        }
        return data

    def get_comerci(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}
        energetica = self.get_socia(cursor, uid, fra, context=context)['energetica']

        data = {}

        if energetica:
            data['logo'] = "https://blog.somenergia.coop/wp-content/uploads/2018/10/som-energia-energetica-logos.jpg"
        else:
            data['logo'] = "http://www.somenergia.coop/wp-content/uploads/2014/07/logo.png"

        return data


    def get_socia(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}
        data = {
            'socia': fra.polissa_id.soci.id,
            'energetica': fra.polissa_id.soci.id == 38039
        }

        return data

    def get_polissa(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}

        report_o = self.pool.get('giscedata.facturacio.factura.report.v2')
        data = report_o.get_polissa(cursor, uid, fra, context=context)

        polissa_retrocedida = False
        de_lot = fra.lot_facturacio and fra.lot_facturacio.id != False
        if de_lot:
            clot_obj = fra.pool.get('giscedata.facturacio.contracte_lot')
            clot_id = clot_obj.search(fra._cr, fra._uid, [('polissa_id', '=', fra.polissa_id.id), ('lot_id', '=', fra.lot_facturacio.id)])
            if clot_id:
                n_retrocedir_lot = clot_obj.read(fra._cr, fra._uid, clot_id[0], ['n_retrocedir_lot'])['n_retrocedir_lot']
                polissa_retrocedida = n_retrocedir_lot > 0

        data['polissa_retrocedida'] = polissa_retrocedida

        return data

    def get_text_correu(self, cursor, uid, fra, context=None):
        def render(text_to_render, object_):
            templ = Template(text_to_render)
            return templ.render_unicode(
                object=object_,
                format_exceptions=True
            )

        if context is None:
            context = {}

        data = {}

        t_obj = self.pool.get('poweremail.templates')
        md_obj = self.pool.get('ir.model.data')

        template_id = md_obj.get_object_reference(
            cursor, uid,  'som_poweremail_common_templates', 'common_template_legal_footer'
        )[1]
        data['text_legal'] = render(t_obj.read(
            cursor, uid, [template_id], ['def_body_text'])[0]['def_body_text'], fra
        )

        return data


ReportBackendInvoiceEmail()
