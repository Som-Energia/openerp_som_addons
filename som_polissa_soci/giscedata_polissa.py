# -*- coding: utf-8 -*-
from osv import osv, fields
import re


class GiscedataPolissa(osv.osv):
    """Pòlissa per afegir el camp de soci.
    """
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def get_consum_anual_webforms(self, cursor, uid, polissa_id, context=None):
        """ Busca el consum anual introduït en el formulari de alta
            * consum: xxx a observacions de la pólissa"""
        res = False

        if isinstance(polissa_id, (tuple, list)):
            polissa_id = polissa_id[0]

        polissa_vals = self.read(cursor, uid, polissa_id, ['observacions',
                                                           'name'])

        if (polissa_vals and polissa_vals['observacions']
                and '* consum: ' in polissa_vals['observacions']):
            observacions = polissa_vals['observacions']
            cadena = '* consum: '
            linia = [l for l in observacions.split('\n') if cadena in l][0]

            val = re.findall('[0-9]+', linia.split(':')[1])
            try:
                consum = val and int(val[0]) or False
            except:
                consum = False

            res = consum

        return res

    def get_consum_anual_estadistic_som(self, cursor, uid, polissa_id,
                                        context=None):
        """ Consum anual segons estadística de SOM"""
        res = 0

        if isinstance(polissa_id, (tuple, list)):
            polissa_id = polissa_id[0]

        polissa_vals = self.read(cursor, uid, polissa_id, ['potencia'])
        if polissa_vals['potencia'] < 1.5:
            res = 840
        elif 1.5 <= polissa_vals['potencia'] < 3.5:
            res = 1800
        elif 3.5 <= polissa_vals['potencia'] < 5.5:
            res = 2400
        elif 5.5 <= polissa_vals['potencia'] < 6.5:
            res = 2880
        elif 6.5 <= polissa_vals['potencia'] < 7.5:
            res = 3840
        elif 7.5 <= polissa_vals['potencia'] < 9.5:
            res = 5280
        elif 9.5 <= polissa_vals['potencia'] < 15:
            res = 9480
        elif 15 <= polissa_vals['potencia']:
            res = 14400

        return res

    _columns = {
        'soci': fields.many2one('res.partner', 'Soci',
                                states={'validar': [('required', True)]}
                                ),
        'soci_nif': fields.related('soci', 'vat', type='char',
                                   string='NIF soci', readonly=True),
        'donatiu': fields.boolean('Donatiu voluntari',
                                  readonly=True,
                                  states={'esborrany': [('readonly', False)],
                                          'validar': [('readonly', False)],
                                          'modcontractual': [('readonly',
                                                              False)],
                                          },
                                  help="Incloure a la factura 0.01€/kWh"
                                       " consumit"),
        'active': fields.boolean('Activa', required=True, readonly=True,
                                 states={'esborrany': [('readonly', False)]}),
    }

    _defaults = {
        'donatiu': lambda *a: False,
    }


GiscedataPolissa()
