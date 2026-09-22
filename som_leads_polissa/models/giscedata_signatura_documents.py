# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv


class GiscedataSignaturaDocuments(osv.osv):
    _name = 'giscedata.signatura.documents'
    _inherit = 'giscedata.signatura.documents'

    _SIGNATURIT_DOCUMENT_NAMES = {
        'ca': {
            'contract': u'Contracte',
            'mandate': u'Autorització bancària',
            'summary': u'Resum de contractació',
        },
        'es': {
            'contract': u'Contrato',
            'mandate': u'Autorización Bancaria',
            'summary': u'Resumen de Contratación',
        },
    }

    def _get_signaturit_document_name(
        self, report_name, lang, filename, report_title=''
    ):
        names = self._SIGNATURIT_DOCUMENT_NAMES.get(lang)
        if not names:
            return filename

        report_key = '{} {}'.format(report_name, report_title).lower()
        if 'mandate' in report_key or 'mandato' in report_key:
            document_name = names['mandate']
        elif 'summary' in report_key or 'resum' in report_key:
            document_name = names['summary']
        elif 'contract' in report_key:
            document_name = names['contract']
        else:
            return filename

        return document_name

    def generate_report(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        generated_documents = super(
            GiscedataSignaturaDocuments, self
        ).generate_report(cursor, uid, ids, context=context) or {}

        lang = (context.get('lang') or '').split('_')[0]
        for document in self.browse(cursor, uid, ids, context=context):
            generated = generated_documents.get(document.id)
            if not generated and document.report_id:
                generated = self.read(
                    cursor, uid, document.id, ['filename', 'doc_file'],
                    context=context
                )
                generated_documents[document.id] = generated
            if not generated or not document.report_id:
                continue

            filename = self._get_signaturit_document_name(
                document.report_id.report_name,
                lang,
                generated['filename'],
                document.report_id.name
            )
            if filename == generated['filename']:
                continue

            self.write(cursor, uid, document.id, {'filename': filename}, context=context)
            generated['filename'] = filename

        return generated_documents


GiscedataSignaturaDocuments()
