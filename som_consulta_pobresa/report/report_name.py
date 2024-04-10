# -*- coding: utf-8 -*-
from report_backend.report_backend import ReportBackend, report_browsify
from tools import config
import pooler


class ReportBackendTemplate(ReportBackend):
    _name = 'report.backend.som.template'
    _source_model = 'som.template'

    def get_lang(self, cursor, uid, invoice_id, context=None):
        return config.get('lang', config.get('default_lang', 'en_US'))

    @report_browsify
    def get_data(self, cursor, uid, invoice, context=None):
        res = super(ReportBackendTemplate, self).get_data(
            cursor, uid, invoice, context=context
        )
        res.update({
            'companyia': self.get_company(cursor, uid, 1, context=context),
        })
        return res

    def get_company(self, cr, uid, context=None):
        if context is None:
            context = {}
        user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
            company_id = user.company_id.id
        else:
            company_id = pooler.get_pool(cr.dbname).get(
                'res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        return company_id


ReportBackendTemplate()
