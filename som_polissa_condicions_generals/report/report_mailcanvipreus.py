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

    def create(self, cursor, uid, ids, datas, context=None):
        if context is None:
            context = {}

        pool = pooler.get_pool(cursor.dbname)
        pol_o = pool.get("giscedata.polissa")
        template_o = pool.get("poweremail.templates")

        ir_model_data = self.pool.get("ir.model.data")
        template_id = ir_model_data.get_object_reference(
            cursor, uid,
            "som_polissa_condicions_generals",
            "canviPreusBackend"
        )[1]

        for pol_id in ids:
            pol_br = pol_o.browse(cursor, uid, pol_id, context=context)

            addons_lookup = TemplateLookup(
                directories=[config['addons_path']], input_encoding='utf-8'
            )
            template = template_o.browse(cursor, uid, template_id, context=context)
            message = template.def_body_html
            templ = MakoTemplate(message, input_encoding='utf-8', lookup=addons_lookup)

            values = {
                'pool': pool,
                'cursor': cursor,
                'uid': uid,
                'object': pol_br,
                'peobject': pol_br,
                'env': {},
                'format_exceptions': True,
                'template': template,
                'lang': context.get('lang'),
            }
            reply = templ.render_unicode(**values)

            pdf_file_path = ReportParser.get_temporal_file_path('pdf')
            html_file_path = ReportParser.write_temporal_file(reply, 'html')

            puppeteer_script_path = 'get_pdf'

            node_bin_path = os.environ.get('NODE_BIN_PATH', 'node')
            if not node_bin_path:
                node_bin_path = 'node'

            node_modules_path = os.environ.get('NODE_PATH', False)
            if node_modules_path:
                node_bin_path = 'NODE_PATH={} {}'.format(
                    node_modules_path, node_bin_path
                )

            try:
                params = {
                    'path': {
                        'html': html_file_path,
                        'pdf': pdf_file_path
                    },
                    'options': {
                        'landscape': False,
                    }
                }
                command = [
                    node_bin_path,
                    '{}/report_puppeteer/js/{}.js'.format(
                        config['addons_path'], puppeteer_script_path),
                    "'{}'".format(json.dumps(params))
                ]
                generate_command = ' '.join(command)
                subprocess.call(generate_command, shell=True)
            except Exception:
                raise
            finally:
                os.remove(html_file_path)

            with open(pdf_file_path, "rb") as pdf_file:
                result = base64.b64encode(pdf_file.read())

            return result, 'pdf'


MailCanviPreusReport('report.report_mailcanvipreus')
