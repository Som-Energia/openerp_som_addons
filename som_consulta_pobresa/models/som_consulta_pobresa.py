# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

RESOLUTION_STATES = [
    ('positiva', 'Positiva'),
    ('negaviva', 'Negativa'),
]


class SomConsultaPobresa(osv.osv):
    _name = 'som.consulta.pobresa'
    _inherits = {"crm.case": "crm_id"}
    _description = 'Model per gestionar les consultes de pobresa energètica'

    def _ff_get_titular(self, cr, uid, ids, field, arg, context=None):
        """ Anem a buscar el titular de la pólissa assignada (si en té) """
        res = {}
        if not context:
            context = {}
        scp_obj = self.pool.get('som.consulta.pobresa')
        consultes = scp_obj.browse(cr, uid, ids)
        for c in consultes:
            res[c.id] = (c.polissa_id and c.polissa_id.titular.name
                         or False)
        return res

    _columns = {
        'crm_id': fields.many2one('crm.case', required=True),
        'polissa_id': fields.many2one('giscedata.polissa',
                                      _('Contracte'), required=True),
        'titular_id': fields.function(
            _ff_get_titular, method=True,
            string='Titular', type='text', stored=True),
        'municipi': fields.char("Número de registre", size=128),  # _ff ?
        'numero_registre': fields.char("Número de registre", size=128),
        'agrupacio_supramunicipal': fields.char("Número de registre", size=128),
        'direccio_cups': fields.char("Direcció CUPS", size=128),  # _ff ?
        'email_partner': fields.char("Email titular", size=128),  # _ff ?
        'resolucio': fields.selection(RESOLUTION_STATES, 'Resolució', size=16),
    }
    _order = "id desc"


SomConsultaPobresa()
