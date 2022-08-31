# -*- coding: utf-8 -*-
"""Classes pel mòdul giscedata_cups (General)."""
from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta


class GiscedataCupsPs(osv.osv):
    """Classe d'un CUPS (Punt de servei)."""

    _name = 'giscedata.cups.ps'
    _inherit = 'giscedata.cups.ps'

    _NEW_ORIGENS_CONANY = [('estadistic', _(u"Estadística SOM")),
                           ('usuari', _(u'usuari (webforms)'))]

    def __init__(self, pool, cursor):
        ''' Afegim els nous origens'''
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
        ''' Afegeix el consum anual estadístic i el de webforms'''
        llista = super(GiscedataCupsPs, self).get_fonts_consums_anuals(
            cursor, uid, context=context)
        # webforms
        vals = {'priority': 100,
                'model': 'giscedata.polissa',
                'func': 'get_consum_anual_webforms',
                'origen': 'usuari'}
        llista.append(vals)
        # estadístic
        vals = {'priority': '1000',
                'model': 'giscedata.polissa',
                'func': 'get_consum_anual_estadistic_som',
                'origen': 'estadistic'}
        llista.append(vals)

        return llista

GiscedataCupsPs()