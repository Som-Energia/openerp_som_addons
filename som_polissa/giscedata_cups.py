# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _


class GiscedataCupsPs(osv.osv):
    """Classe d'un CUPS (Punt de servei)."""

    _name = 'giscedata.cups.ps'
    _inherit = 'giscedata.cups.ps'

    _NEW_ORIGENS_CONANY = [
        ('consums', _(u'Historic consums')),
        ('factures', _(u'Historic factures')),
        ('pdf', _(u'Pdf última factura')),
        ('consums_periods', _(u'Historic consums periodes')),
        ('estadistic', _(u"Estadística SOM")),
        ('usuari', _(u'usuari (webforms)'))
    ]

    def __init__(self, pool, cursor):
        ''' Afegim els nou orígen'''
        super(GiscedataCupsPs, self).__init__(pool, cursor)
        origens = self.get_fonts_consums_anuals(cursor, 1)
        for origen in origens:
            current_sel = dict(self._columns['conany_origen'].selection).keys()
            if origen['origen'] not in current_sel:
                new_sel = (origen['origen'],
                           dict(self._NEW_ORIGENS_CONANY).get(
                               origen['origen'], origen['origen']))
                self._columns['conany_origen'].selection.append(new_sel)

    def get_consum_anual_backend_gisce(self, cursor, uid, polissa_id, context=None):
        """ Consum anual segons query de del backend de la factura de GISCE """
        if context is None:
            context = {}
        if isinstance(polissa_id, (tuple, list)):
            polissa_id = polissa_id[0]

        factura_obj = self.pool.get('giscedata.facturacio.factura')
        factura_backend_obj = self.pool.get('giscedata.facturacio.factura.report.v2')

        search_params = [('polissa_id', '=', polissa_id)]

        last_inv = factura_obj.search(
            cursor, uid, search_params, order="data_inici desc", context=context
        )[0]

        historic = factura_backend_obj.get_grafica_historic_consum_14_mesos(
            cursor, uid, last_inv, context=context)

        consums = historic['historic_js']
        if len(consums) < 12:
            return False

        consum_periodes = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0, 'P5': 0, 'P6': 0}
        for invoice in consums:
            for k, _ in invoice.items():
                if k in consum_periodes:
                    consum_periodes[k] += float(invoice[k].replace(',', '.'))

        days_of_consume = int(historic['historic']['days'])
        for k, _ in consum_periodes.items():
            consum_periodes[k] = int(consum_periodes[k] * 365 / days_of_consume)
        return consum_periodes

    def get_fonts_consums_anuals(self, cursor, uid, context=None):
        ''' Afegim consum_anual_consum_lectures com a font de consum anual
        '''
        llista = super(GiscedataCupsPs, self).get_fonts_consums_anuals(
            cursor, uid, context=context)

        for i in range(len(llista)):
            if llista[i]['func'] == 'get_consum_anual_lectures':
                del llista[i]
                break

        vals = [
            {'priority': 500,
             'model': 'giscedata.polissa',
             'func': 'get_consum_anual_sips',
             'origen': 'consums',
             'periods': True},
            {'priority': 3,
             'model': 'giscedata.polissa',
             'func': 'get_consum_anual_backend_gisce',
             'origen': 'consums',
             'periods': True},
            {'priority': 5,
             'model': 'giscedata.polissa',
             'func': 'get_consum_anual_consum_lectures',
             'origen': 'consums'},
            {'priority': 4,
             'model': 'giscedata.polissa',
             'func': 'get_consum_anual_factures',
             'origen': 'factures'},
            {'priority': 3,
             'model': 'giscedata.polissa',
             'func': 'get_consum_anual_pdf',
             'origen': 'pdf'},
            {'priority': 100,
             'model': 'giscedata.polissa',
             'func': 'get_consum_anual_webforms',
             'origen': 'usuari'},
            {'priority': '1000',
             'model': 'giscedata.polissa',
             'func': 'get_consum_anual_estadistic_som',
             'origen': 'estadistic'}
        ]

        llista += vals

        return llista


GiscedataCupsPs()
