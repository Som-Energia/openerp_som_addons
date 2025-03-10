# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from tools.translate import _


class ReportBackendNotaCarrec(ReportBackend):
    _inherit = 'report.backend.account.invoice.nota.carrec'

    def get_lang(self, cursor, uid, record_id, context=None):
        """
        Get the language of the report, depending on the partner

        :param cursor: Database cursor
        :param uid: User ID
        :param record_id: ID of the record to print
        :param context: Context dictionary

        :return: Return the language of the RECIPIENT partner, defaulting to 'ca_ES'
        """
        if context is None:
            context = {}

        nota_carrec_brw = self.pool.get('account.invoice.nota.carrec').browse(cursor, uid, record_id, context=context)
        lang = nota_carrec_brw.partner_id.lang or 'ca_ES'

        return lang

    @report_browsify
    def get_data(self, cursor, uid, nota, context=None):
        res = super(ReportBackendNotaCarrec, self).get_data(cursor, uid, nota, context=context)
        res.update({
            'lang': self.get_lang(cursor, uid, nota.id, context=context),
        })

        return res

ReportBackendNotaCarrec()