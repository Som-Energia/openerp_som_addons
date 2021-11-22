# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _

class GiscedataCupsPs(osv.osv):
    """Classe d'un CUPS (Punt de servei)."""

    _name = 'giscedata.cups.ps'
    _inherit = 'giscedata.cups.ps'

    _NEW_ORIGENS_CONANY = [
        ('consums', _(u'Historic consums')),
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

    def get_fonts_consums_anuals(self, cursor, uid, context=None):
        ''' Afegim consum_anual_consum_lectures com a font de consum anual
        '''
        llista = super(GiscedataCupsPs, self).get_fonts_consums_anuals(
            cursor, uid, context=context)

        vals = {'priority': 5,
                'model': 'giscedata.polissa',
                'func': 'get_consum_anual_consum_lectures',
                'origen': 'consums'}
        llista.append(vals)

        return llista

GiscedataCupsPs()