# -*- coding: utf-8 -*-
from osv import osv, fields
import re
from tools.translate import _
from gestionatr.defs import TABLA_113, TABLA_17
from datetime import datetime, timedelta
from tools import cache
import logging

TIPO_AUTOCONSUMO_SEL = [(ac[0], '[{}] - {}'.format(ac[0], ac[1])) for ac in TABLA_113]
IMPORT_PHASE_1 = 10  # 10 = Fase de càrrega XML

class GiscedataFacturacioImportacioLinia(osv.osv):
    _name = 'giscedata.facturacio.importacio.linia'
    _inherit = 'giscedata.facturacio.importacio.linia'

    def unlink_facturacio_extra(self, cursor, uid, lid, context=None):
        """Eliminiar les línies de giscedata.facturacio.extra associades a
           la línia a través de giscedata.facturacio.importacio.linia.extra
        """
        if not context:
            context = {}
        lin_ext = self.pool.get(
                    'giscedata.facturacio.importacio.linia.extra')
        ext = self.pool.get('giscedata.facturacio.extra')
        lin_ext_id = lin_ext.search(cursor, uid, [('linia_id', '=', lid)])
        if lin_ext_id:
            lin_ext_obj = lin_ext.read(cursor, uid, lin_ext_id, ['extra_id'])
            ext_ids = [x['extra_id'][0] for x in lin_ext_obj]
            ext_info = ext.read(cursor, uid, ext_ids, ['amount_invoiced', 'total_amount_invoiced'])
            if any([x for x in ext_info if x.get('amount_invoiced', 0.0) != 0.0]) or \
               any([x for x in ext_info if x.get('total_amount_invoiced', 0.0) != 0.0]):
                raise osv.except_osv('Error', _('No es pot eliminar el Fitxer importat per que hi ha almenys '
                                                'una línia extra amb import ja facturat'))
            ext.unlink(cursor, uid, ext_ids, context)


    def get_header_dict(self, xml_data):
        vals = super(GiscedataFacturacioImportacioLinia, self).get_header_dict(xml_data)

        tipus_autoconsum = re.findall(
            '<TipoAutoconsumo>(.*)</TipoAutoconsumo>', xml_data
        )
        if tipus_autoconsum:
            vals['tipus_autoconsum'] = tipus_autoconsum[0]

        tarifaATR = re.findall(
            '<TarifaATRFact>(.*)</TarifaATRFact>', xml_data
        )
        if tarifaATR:
            vals['tarifa_atr'] = tarifaATR[0]

        if vals['type_factura'] == 'C':
            expedient = re.findall(
                '<NumeroExpediente>(.*)</NumeroExpediente>', xml_data
            )
            if expedient:
                vals['num_expedient'] = expedient[0]

            comentario = re.findall(
                '<Comentarios>(.*)</Comentarios>', xml_data
            )
            if comentario:
                comentario = comentario[0]
                try:
                    comentario = comentario.encode('utf-8')
                except:
                    try:
                        comentario = comentario.decode('latin-1').encode('utf-8')
                    except:
                        comentario = ''

                vals['comentari'] = comentario
        return vals

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
            for line in line_ids:
                self.process_line(cursor, uid, line, context=context)


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

        _ids = self.search(cursor, uid, [
            ('state', '=', False),
            ('import_phase', '=', IMPORT_PHASE_1),
            ('fecha_factura', '>=', date_to_check),
        ])
        f1_ids += _ids

        if f1_ids:
            self.reimport_f1_by_cups(cursor, uid, f1_ids, context=context)
        logger.info('Iniciada la reimportació de {} fitxers, amb data factura entre {} i avui ({})'.format(
            len(f1_ids), date_to_check, datetime.today().strftime('%Y-%m-%d')
        ))

    def _ff_get_polissa(self, cursor, uid, ids, field_name, arg, context):
        """Pòlissa a la que fa referència l'F1."""
        cups_obj = self.pool.get('giscedata.cups.ps')

        res = dict.fromkeys(ids, False)
        for f1_info in self.read(cursor, uid, ids, ['cups_id', 'fecha_factura_desde']):
            if f1_info['cups_id'] and f1_info['fecha_factura_desde']:
                data_inici_factura = datetime.strftime(
                    datetime.strptime(f1_info['fecha_factura_desde'], '%Y-%m-%d') + timedelta(days=1),
                '%Y-%m-%d')
                pol_id = cups_obj.find_most_recent_polissa(cursor, uid, f1_info['cups_id'][0], data_inici_factura)
                res[f1_info['id']] = pol_id[f1_info['cups_id'][0]]
        return res

    def _get_importacio_linia_polissa(self, cr, uid, ids, context={}):

        f1_obj = self.pool.get('giscedata.facturacio.importacio.linia')

        cups_ids = [x['cups'][0] for x in self.read(cr, uid, ids, ['cups']) if x['cups']]
        return f1_obj.search(cr, uid, [('cups_id', 'in', cups_ids)])

    _store_polissa_id = {
        'giscedata.facturacio.importacio.linia': (lambda self, cr, uid, ids, c={}: ids, None, 20),
        'giscedata.polissa': (_get_importacio_linia_polissa, ['name', 'data_alta', 'data_baixa', 'state', 'cups'], 20),
    }

    _columns = {
        'tipus_autoconsum': fields.selection(
            TIPO_AUTOCONSUMO_SEL, u"Autoconsum", readonly=True,
            help=u'Tipus de autoconsum informat a l\'F1'
        ),
        'tarifa_atr': fields.selection(TABLA_17, u'Tarifa', readonly=True),
        'num_expedient': fields.char(_(u'Núm. Expedient'), size=16, readonly=True),
        'comentari': fields.text(_(u'Comentari de l\'F1'), readonly=True),
        'polissa_id': fields.function(
            _ff_get_polissa, method=True, type='many2one',
            relation='giscedata.polissa', store=_store_polissa_id, string='Polissa'
        ),
        'data_ultima_lectura_polissa': fields.related(
            'polissa_id', 'data_ultima_lectura', type="date", string="Data ultima lect. facturada pòlissa", readonly=True
        )
    }
GiscedataFacturacioImportacioLinia()