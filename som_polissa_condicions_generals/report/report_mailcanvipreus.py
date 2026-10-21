from __future__ import absolute_import
import os
import json
import base64
import pooler
import subprocess
from report.interface import report_int

from mako.template import Template as MakoTemplate
from mako.lookup import TemplateLookup
from tools import config
from report_backend.report_parser import ReportParser


class MailCanviPreusReport(report_int):

    def _render_record(self, cursor, uid, pool, pol, context):
        templates = pool.get('poweremail.templates')
        model_data = pool.get('ir.model.data')
        legacy_id = model_data.get_object_reference(
            cursor, uid, 'som_polissa_condicions_generals', 'canviPreusBackend')[1]
        env_id = context.get('price_change_enviament_id')
        if not env_id:
            legacy = templates.browse(cursor, uid, legacy_id, context=context)
            if legacy.model_int_name == 'giscedata.polissa':
                return pol, legacy
            campaign_id = model_data.get_object_reference(
                cursor, uid, 'som_polissa_condicions_generals',
                'price_change_campaign_template')[1]
            candidates = pool.get('som.enviament.massiu').search(cursor, uid, [
                ('polissa_id', '=', pol.id),
                ('lot_enviament.email_template', 'in', [legacy_id, campaign_id]),
            ], limit=2, context=context)
            if len(candidates) != 1:
                raise ValueError(
                    'Select the original sending with price_change_enviament_id '
                    'to preview this policy: no unique price-change sending exists')
            env_id = candidates[0]
        env = pool.get('som.enviament.massiu').browse(cursor, uid, env_id, context=context)
        if env.polissa_id.id != pol.id:
            raise ValueError('The PDF sending must belong to the requested policy')
        template = env.lot_enviament.email_template
        if template.model_int_name != 'som.enviament.massiu':
            raise ValueError('The PDF sending requires a mass-mail template')
        return env, template

    def create(self, cursor, uid, ids, datas, context=None):
        context = dict(context or {})
        if context.get('price_change_enviament_id') and len(ids) != 1:
            raise ValueError('An explicit sending can preview only its own policy')
        pool = pooler.get_pool(cursor.dbname)
        pol_o = pool.get('giscedata.polissa')
        lookup = TemplateLookup(directories=[config['addons_path']], input_encoding='utf-8')
        result = []
        for pol_id in ids:
            pol = pol_o.browse(cursor, uid, pol_id, context=context)
            record, template = self._render_record(cursor, uid, pool, pol, context)
            templ = MakoTemplate(template.def_body_html, input_encoding='utf-8', lookup=lookup)
            reply = templ.render_unicode(
                pool=pool, cursor=cursor, uid=uid, object=record, peobject=record,
                env={}, format_exceptions=True, template=template, lang=context.get('lang'))
            pdf_path = ReportParser.get_temporal_file_path('pdf')
            html_path = None
            try:
                html_path = ReportParser.write_temporal_file(reply, 'html')
                params = {
                    'path': {'html': html_path, 'pdf': pdf_path},
                    'options': {'landscape': False},
                }
                subprocess.check_call([
                    os.environ.get('NODE_BIN_PATH') or 'node',
                    os.path.join(config['addons_path'], 'report_puppeteer', 'js', 'get_pdf.js'),
                    json.dumps(params),
                ])
                with open(pdf_path, 'rb') as pdf_file:
                    pdf = pdf_file.read()
                if not pdf.startswith(b'%PDF'):
                    raise ValueError('The PDF renderer did not produce a PDF document')
                result.append(base64.b64encode(pdf))
            finally:
                for path in (html_path, pdf_path):
                    if path and os.path.exists(path):
                        os.remove(path)
        return result, 'pdf'


MailCanviPreusReport('report.report_mailcanvipreus')
