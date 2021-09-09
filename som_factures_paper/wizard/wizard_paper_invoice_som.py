# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import datetime
import json
import netsvc
import tempfile
import os
import tools
from cStringIO import StringIO
from zipfile import PyZipFile, ZIP_DEFLATED
import base64


STATES = [
    ('init', 'Estat Inicial'),
    ('info', 'Informació de factures impresses'),
    ('done', 'Estat Final'),
]


class WizardPaperInvoiceSom(osv.osv_memory):
    _name = 'wizard.paper.invoice.som'

    _columns = {
        'state': fields.selection(STATES, _(u'Estat del wizard de imprimir report')),
        'date_from': fields.date('Data desde'),
        'date_to': fields.date('Data fins'),
        'info': fields.text('Informació', readonly=True),
        'invoice_ids': fields.text('Factures'),
        'file': fields.binary('Fitxer generat'),
        'file_name': fields.text('Nom del fitxer'),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'file_name': lambda *a: 'factures.zip',
        'date_to': lambda *a: datetime.today().strftime("%Y-%m-%d")
    }

    def search_invoices(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')
        fact_obj = self.pool.get('giscedata.facturacio.factura')

        wiz = self.browse(cursor, uid, ids[0], context=context)

        pol_ids = pol_obj.search(cursor, uid, [('enviament', '!=', 'email')], context=context)
        fact_ids = []
        for pol_id in pol_ids:
            p_f_ids = fact_obj.search(cursor, uid, [
                ('polissa_id', '=', pol_id),
                ('date_invoice', '>=', wiz.date_from),
                ('date_invoice', '<=', wiz.date_to),
                ('state', 'in', ('open', 'paid')),
                ('type', 'in', ('out_refund', 'out_invoice')),
                ], context=context)
            fact_ids.extend(p_f_ids)

        fact_datas = fact_obj.read(cursor, uid, fact_ids, ['number'])
        fact_names = ', '.join([f['number'] for f in fact_datas])
        wiz.write({
            'state': 'info',
            'invoice_ids': json.dumps(fact_ids),
            'info': "Trobades {} polisses amb enviament postal.\nEs generanan {} pdf's de les seguents factures:\n{}".format(
                len(pol_ids),
                len(fact_ids),
                fact_names),
        })

    def generate_invoices(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        fact_obj = self.pool.get('giscedata.facturacio.factura')

        wiz = self.browse(cursor, uid, ids[0], context=context)
        fact_ids = json.loads(wiz.invoice_ids)
        report = 'report.giscedata.facturacio.factura'
        tmp_dir = tempfile.mkdtemp()

        for fact_id in fact_ids:
            fact = fact_obj.browse(cursor, uid, fact_id, context=context)
            file_name = "{}-{}.pdf".format(fact.polissa_id.direccio_notificacio.name, fact.number)
            self.render_to_file(cursor, uid, [fact_id], report, tmp_dir, file_name, context)

        wiz.write({
            'state': 'done',
            'file': self.get_zip_from_directory(tmp_dir, True),
        })

    def render_to_file(self, cursor, uid, fids, report, dirname, file_name, context=None):
        """Return a tuple of status (0: OK, 1: Failed) and the invoice path.
        """
        if context is None:
            context = {}
        try:
            report = netsvc.service_exist(report)
            values = {
                'model': 'giscedata.facturacio.factura',
                'id': fids,
                'report_type': 'pdf'
            }
            content = report.create(cursor, uid, fids, values, context)[0]
            # Escriure report a "fitxer"
            fitxer_name = '{}/{}'.format(dirname, file_name)
            with open(fitxer_name, 'wb') as f:
                f.write(content)
            return 0, fitxer_name
        except Exception:
            import traceback
            traceback.print_exc()
            sentry = self.pool.get('sentry.setup')
            if sentry is not None:
                sentry.client.captureException()
            return 1, fids

    def get_zip_from_directory(self, directory, b64enc=True):

        def _zippy(archive, path):
            path = os.path.abspath(path)
            base = os.path.basename(path)
            for f in tools.osutil.listdir(path, True):
                archive.write(os.path.join(path, f), os.path.join(base, f))

        archname = StringIO()
        archive = PyZipFile(archname, "w", ZIP_DEFLATED)
        archive.writepy(directory)
        _zippy(archive, directory)
        archive.close()
        val = archname.getvalue()
        archname.close()

        if b64enc:
            val = base64.encodestring(val)

        return val


WizardPaperInvoiceSom()
