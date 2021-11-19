# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

class GiscedataCupsPs(osv.osv):
    """Classe d'un CUPS (Punt de servei)."""

    _name = 'giscedata.cups.ps'
    _inherit = 'giscedata.cups.ps'

    def get_fonts_consums_anuals(self, cursor, uid, context=None):
        ''' Afegim consum_anual_consum_lectures com a font de consum anual
        '''
        llista = super(GiscedataCupsPs, self).get_fonts_consums_anuals(
            cursor, uid, context=context)

        vals = {'priority': 5,
                'model': 'giscedata.polissa',
                'func': 'get_consum_anual_consum_lectures',
                'origen': 'lectures'}
        llista.append(vals)

        return llista

GiscedataCupsPs()