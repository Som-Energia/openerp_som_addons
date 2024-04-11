# -*- coding: utf-8 -*-
from osv import osv, fields

RESOLUTION_STATES = [
    ('positiva', 'Positiva'),
    ('negaviva', 'Negativa'),
]


class SomConsultaPobresa(osv.OsvInherits):
    _name = 'som.consulta.pobresa'
    _inherits = {"crm.case": "crm_id"}
    _description = 'Model per gestionar les consultes de pobresa energètica'

    def case_close(self, cr, uid, ids, *args):
        casos = self.browse(cr, uid, ids)
        for cas in casos:
            if not cas.resolucio:
                raise osv.except_osv(
                    "Falta resolució",
                    "Per poder tancar la consulta s'ha d'informar el camp resolució.")

        return super(SomConsultaPobresa, self).case_close(cr, uid, ids, args)

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

    def _ff_get_municipi(self, cr, uid, ids, field, arg, context=None):
        """ Anem a buscar el municipi del cups de la pólissa assignada (si en té) """
        res = {}
        if not context:
            context = {}
        scp_obj = self.pool.get('som.consulta.pobresa')
        consultes = scp_obj.browse(cr, uid, ids)
        for c in consultes:
            res[c.id] = (c.polissa_id and c.polissa_id.cups.id_municipi.name
                         or False)
        return res

    def _ff_get_direccio_cups(self, cr, uid, ids, field, arg, context=None):
        """ Anem a buscar el municipi del cups de la pólissa assignada (si en té) """
        res = {}
        if not context:
            context = {}
        scp_obj = self.pool.get('som.consulta.pobresa')
        consultes = scp_obj.browse(cr, uid, ids)
        for c in consultes:
            res[c.id] = (c.polissa_id and c.polissa_id.cups.direccio
                         or False)
        return res

    def _ff_get_email_titular(self, cr, uid, ids, field, arg, context=None):
        """ Anem a buscar el titular de la pólissa assignada (si en té) """
        res = {}
        if not context:
            context = {}
        scp_obj = self.pool.get('som.consulta.pobresa')
        consultes = scp_obj.browse(cr, uid, ids)
        for c in consultes:
            res[c.id] = (c.polissa_id and c.polissa_id.titular.www_email
                         or False)
        return res

    _columns = {
        'crm_id': fields.many2one('crm.case', required=True),
        'polissa_id': fields.many2one('giscedata.polissa',
                                      'Contracte', required=True),
        'titular_id': fields.function(
            _ff_get_titular, method=True,
            string='Titular', type='text', stored=True),
        'municipi': fields.function(
            _ff_get_municipi, method=True,
            string="Municipi", type='text', stored=True),
        'numero_registre': fields.char("Número de registre", size=128),
        'agrupacio_supramunicipal': fields.many2one('agrupacio.supramunicipal',
                                                    'Agrupació supramunicipal'),
        'direccio_cups': fields.function(
            _ff_get_direccio_cups, method=True,
            string="Direcció CUPS", type='text', stored=True),
        'email_partner': fields.function(
            _ff_get_email_titular, method=True,
            string="Email titular", type='text', stored=True),
        'resolucio': fields.selection(RESOLUTION_STATES, 'Resolució', size=16),
    }

    _order = "id desc"


SomConsultaPobresa()
