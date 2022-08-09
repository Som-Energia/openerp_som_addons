# -*- coding: utf-8 -*-
from osv import osv
from tools import cache
from datetime import datetime, timedelta
import logging

class GiscedataFacturacioImportacioLinia(osv.osv):
    _name = 'giscedata.facturacio.importacio.linia'
    _inherit = 'giscedata.facturacio.importacio.linia'

    @cache(timeout=5 * 60)
    def exact_origin_search(self, cursor, uid, context=None):
        if context is None:
            context = {}
        exact = int(self.pool.get('res.config').get(
            cursor, uid, 'invoice_origin_cerca_exacte', '0')
        )
        return exact

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        """Funció per fer cerques per origin (invoice_number_text) exacte, enlloc d'amb 'ilike'.
        """
        exact_origin = self.exact_origin_search(cr, user, context=context)
        if exact_origin:
            for idx, arg in enumerate(args):
                if len(arg) == 3:
                    field, operator, match = arg
                    if exact_origin and field == 'invoice_number_text' and isinstance(match,(unicode,str)):
                        if not '%' in match:
                            operator = '='
                        args[idx] = (field, operator, match)
        return super(GiscedataFacturacioImportacioLinia, self).search(cr, user, args, offset, limit, order, context, count)

    def reimport_f1_by_cups(self, cursor, uid, ids, context=None):
        f1_info = self.read(cursor, uid, ids, ['cups_id', 'fecha_factura_desde'])
        f1_dict = {}
        for f1 in f1_info:
            cups_id = f1['cups_id'][0]
            if cups_id not in f1_dict:
                f1_dict[cups_id] = []
            f1_dict[cups_id].append(f1)

        for _, f1ns in f1_dict.items():
            sorted_list = sorted(f1ns, key=lambda x: x['fecha_factura_desde'])
            line_ids = [x['id'] for x in sorted_list]
            self.process_line(cursor, uid, line_ids, context=context)


    def do_reimport_f1(self, cursor, uid, data=None, context=None):
        if not context:
            context = {}
        if not data:
            return True

        logger = logging.getLogger(
            'openerp.{}.reimport_f1'.format(__name__)
        )

        f1_ids = []
        days_to_check = data.get('days_to_check', 30)
        date_to_check = (datetime.today() - timedelta(days_to_check)).strftime('%Y-%m-%d')
        for error_code in data['error_codes']:
            code = error_code.get('code', '')
            text = error_code.get('text', '')
            _ids = self.search(cursor, uid, [
                ('state','=','erroni'), ('info', 'ilike','%[{}]%{}%'.format(code, text)),('fecha_factura','>=',date_to_check)
            ])
            f1_ids += _ids

        if f1_ids:
            self.reimport_f1_by_cups(cursor, uid, f1_ids, context=context)
        logger.info('Iniciada la reimportació de {} fitxers, amb data factura entre {} i avui ({})'.format(
            len(f1_ids), date_to_check, datetime.today().strftime('%Y-%m-%d')
        ))

GiscedataFacturacioImportacioLinia()